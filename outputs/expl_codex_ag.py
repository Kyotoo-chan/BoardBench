"""Self-contained implementation of the supplied German Exploding Kittens rules."""
from __future__ import annotations

from typing import Any
import copy
import json
import random

CARDS = ("exploding_kitten", "defuse", "attack", "nope", "skip", "favor",
         "shuffle", "see_future", "cat_beard", "cat_cattermelon",
         "cat_hairy_potato", "cat_rainbow", "cat_tacocat")
COUNTS = dict(zip(CARDS, (4, 6, 4, 5, 4, 4, 4, 5, 4, 4, 4, 4, 4)))
CAT_CARDS = set(CARDS[8:])
PHASES = {"play", "reaction", "favor_give", "defuse_reinsert", "terminal"}
ACTION_TYPES = {"draw", "play_card", "play_pair", "play_triple", "play_five",
                "give_card", "reinsert", "play_nope", "pass_nope"}
STATE_SCHEMA = "boardbench/exploding-kittens/state/2"
ACTION_SCHEMA = "boardbench/exploding-kittens/action/2"
OBS_SCHEMA = "boardbench/exploding-kittens/observation/2"


class GameState:
    def __init__(self, configuration, players, zones, current_player, turns_owed,
                 phase, pending, terminal, winner, turn_number, chance):
        self.configuration = configuration
        self.players = players
        self.zones = zones
        self.current_player = current_player
        self.turns_owed = turns_owed
        self.phase = phase
        self.pending = pending
        self.terminal = terminal
        self.winner = winner
        self.turn_number = turn_number
        self.chance = chance


class Action:
    __slots__ = ("type", "actor", "args_json")

    def __init__(self, type, actor, args_json="{}"):
        self.type, self.actor, self.args_json = type, actor, args_json

    def __eq__(self, other):
        return (isinstance(other, Action) and
                (self.type, self.actor, self.args_json) ==
                (other.type, other.actor, other.args_json))

    def __hash__(self):
        return hash((self.type, self.actor, self.args_json))

    def __deepcopy__(self, memo):
        return self

    @property
    def args(self):
        return json.loads(self.args_json)


def _action(kind, actor, **args):
    return Action(kind, actor, json.dumps(args, sort_keys=True, separators=(",", ":")))


class Game:
    def __init__(self, num_players=None, seed=None):
        self.num_players = 2 if num_players is None else num_players
        if type(self.num_players) is not int or self.num_players not in (2, 3, 4, 5):
            raise ValueError("num_players must be one of 2, 3, 4, 5")
        if seed is not None and type(seed) is not int:
            raise ValueError("seed must be an integer or None")
        self.seed = seed

    def _shuffle(self, state, values):
        seed = state.chance["seed"]
        counter = state.chance["counter"]
        random.Random(f"{seed!r}:{counter}").shuffle(values)
        state.chance["counter"] += 1

    def _choice(self, state, values):
        seed = state.chance["seed"]
        counter = state.chance["counter"]
        value = random.Random(f"{seed!r}:{counter}").choice(values)
        state.chance["counter"] += 1
        return value

    def initial_state(self):
        n = self.num_players
        state = GameState(
            {"players": n, "seed": self.seed, "variant": "base"},
            [{"id": i, "alive": True, "hand": [], "preview": []} for i in range(n)],
            {"deck": [], "discard": [], "box": []}, 0, 1, "play", None,
            False, None, 0, {"seed": self.seed, "counter": 0})
        pool = []
        for card, count in COUNTS.items():
            if card not in ("exploding_kitten", "defuse"):
                pool += [card] * count
        self._shuffle(state, pool)
        for player in state.players:
            player["hand"] = [pool.pop() for _ in range(7)] + ["defuse"]
        extra_defuses = 2 if n == 2 else 6 - n
        pool += ["defuse"] * extra_defuses
        pool += ["exploding_kitten"] * (n - 1)
        state.zones["box"] = (["defuse"] * (6 - n - extra_defuses) +
                              ["exploding_kitten"] * (5 - n))
        self._shuffle(state, pool)
        state.zones["deck"] = pool
        return state

    def current_player(self, state):
        return state.current_player

    def _opponents_with_cards(self, s, actor):
        return [p["id"] for p in s.players
                if p["alive"] and p["id"] != actor and p["hand"]]

    def legal_actions(self, s):
        if s.terminal or s.phase == "terminal":
            return []
        actor = s.current_player
        if not (0 <= actor < len(s.players)) or not s.players[actor]["alive"]:
            return []
        if s.phase == "reaction":
            actions = [_action("pass_nope", actor)]
            if "nope" in s.players[actor]["hand"]:
                actions.append(_action("play_nope", actor))
            return actions
        if s.phase == "favor_give":
            if not s.players[actor]["hand"]:
                return []
            return [_action("give_card", actor, card=c)
                    for c in sorted(set(s.players[actor]["hand"]))]
        if s.phase == "defuse_reinsert":
            return [_action("reinsert", actor, position=i)
                    for i in range(len(s.zones["deck"]) + 1)]
        hand = s.players[actor]["hand"]
        actions = [_action("draw", actor)]
        targets = self._opponents_with_cards(s, actor)
        for card in sorted(set(hand)):
            if card in ("exploding_kitten", "defuse", "nope") or card in CAT_CARDS:
                continue
            if card == "favor":
                actions += [_action("play_card", actor, card=card, target=t) for t in targets]
            else:
                actions.append(_action("play_card", actor, card=card, target=None))
        for card in sorted(set(hand)):
            count = hand.count(card)
            if count >= 2:
                actions += [_action("play_pair", actor, card=card, target=t) for t in targets]
            if count >= 3:
                for target in targets:
                    for requested in CARDS:
                        actions.append(_action("play_triple", actor, card=card,
                                               target=target, requested=requested))
        if len(set(hand)) >= 5 and s.zones["discard"]:
            import itertools
            for cards in itertools.combinations(sorted(set(hand)), 5):
                for retrieve in sorted(set(s.zones["discard"])):
                    actions.append(_action("play_five", actor, cards=list(cards),
                                           retrieve=retrieve))
        return actions

    def _next_alive(self, s, actor):
        for offset in range(1, len(s.players) + 1):
            p = (actor + offset) % len(s.players)
            if s.players[p]["alive"]:
                return p
        return actor

    def _advance(self, s, consume=1):
        s.turns_owed -= consume
        s.turn_number += 1
        if s.turns_owed <= 0:
            s.current_player = self._next_alive(s, s.current_player)
            s.turns_owed = 1
        s.phase, s.pending = "play", None

    def _begin_reaction(self, s, proposed, cards):
        actor = proposed.actor
        responders = [p["id"] for p in s.players if p["alive"] and p["id"] != actor]
        if not responders:
            self._resolve_proposed(s, proposed)
            return
        s.phase = "reaction"
        s.current_player = responders[0]
        s.pending = {"type": "reaction", "proposed": self.action_to_data(proposed)["data"],
                     "cards": list(cards), "nope_count": 0,
                     "responder": responders[0], "remaining_responders": responders}

    def _resolve_proposed(self, s, a):
        actor, args = a.actor, a.args
        s.current_player = actor
        if a.type == "play_card":
            card = args["card"]
            if card == "attack":
                nxt = self._next_alive(s, actor)
                s.current_player, s.turns_owed = nxt, s.turns_owed + 1
                s.turn_number += 1
                s.phase, s.pending = "play", None
            elif card == "skip":
                self._advance(s)
            elif card == "favor":
                s.current_player = args["target"]
                s.phase = "favor_give"
                s.pending = {"type": "favor", "actor": actor, "target": args["target"]}
            elif card == "shuffle":
                self._shuffle(s, s.zones["deck"])
                s.phase, s.pending = "play", None
            elif card == "see_future":
                s.players[actor]["preview"] = list(reversed(s.zones["deck"][-3:]))
                s.phase, s.pending = "play", None
        elif a.type == "play_pair":
            target = args["target"]
            if s.players[target]["hand"]:
                stolen = self._choice(s, s.players[target]["hand"])
                s.players[target]["hand"].remove(stolen)
                s.players[actor]["hand"].append(stolen)
            s.phase, s.pending = "play", None
        elif a.type == "play_triple":
            target, requested = args["target"], args["requested"]
            if requested in s.players[target]["hand"]:
                s.players[target]["hand"].remove(requested)
                s.players[actor]["hand"].append(requested)
            s.phase, s.pending = "play", None
        elif a.type == "play_five":
            retrieve = args["retrieve"]
            if retrieve in s.zones["discard"]:
                s.zones["discard"].remove(retrieve)
                s.players[actor]["hand"].append(retrieve)
            s.phase, s.pending = "play", None

    def _eliminate(self, s, actor, kitten):
        s.players[actor]["alive"] = False
        s.zones["discard"].extend(s.players[actor]["hand"])
        s.players[actor]["hand"] = []
        s.zones["discard"].append(kitten)
        alive = [p["id"] for p in s.players if p["alive"]]
        if len(alive) == 1:
            s.terminal, s.winner, s.phase, s.pending = True, alive[0], "terminal", None
            s.current_player = alive[0]
        else:
            s.current_player = self._next_alive(s, actor)
            s.turns_owed, s.phase, s.pending = 1, "play", None
            s.turn_number += 1

    def apply_action(self, state, action):
        s = copy.deepcopy(state)
        if action not in self.legal_actions(s):
            raise ValueError("illegal action")
        actor, args = action.actor, action.args
        if s.phase == "reaction":
            p = s.pending
            if action.type == "play_nope":
                s.players[actor]["hand"].remove("nope")
                s.zones["discard"].append("nope")
                p["nope_count"] += 1
            remaining = list(p["remaining_responders"])
            if actor in remaining:
                remaining.remove(actor)
            if action.type == "play_nope":
                proposer = p["proposed"]["actor"]
                remaining = [x["id"] for x in s.players if x["alive"] and x["id"] != actor]
                if proposer not in remaining and s.players[proposer]["alive"]:
                    remaining.append(proposer)
            p["remaining_responders"] = remaining
            if remaining:
                s.current_player = remaining[0]
                p["responder"] = remaining[0]
            else:
                proposed = self.action_from_data({"schema": ACTION_SCHEMA, "data": p["proposed"]})
                if p["nope_count"] % 2 == 0:
                    self._resolve_proposed(s, proposed)
                else:
                    s.current_player, s.phase, s.pending = proposed.actor, "play", None
            return s
        if s.phase == "favor_give":
            card = args["card"]
            receiver = s.pending["actor"]
            s.players[actor]["hand"].remove(card)
            s.players[receiver]["hand"].append(card)
            s.current_player, s.phase, s.pending = receiver, "play", None
            return s
        if s.phase == "defuse_reinsert":
            pos = args["position"]
            s.zones["deck"].insert(pos, s.pending["kitten"])
            self._advance(s)
            return s
        if action.type == "draw":
            if not s.zones["deck"]:
                raise ValueError("cannot draw from empty deck")
            card = s.zones["deck"].pop()
            s.players[actor]["preview"] = []
            if card == "exploding_kitten":
                if "defuse" in s.players[actor]["hand"]:
                    s.players[actor]["hand"].remove("defuse")
                    s.zones["discard"].append("defuse")
                    s.phase = "defuse_reinsert"
                    s.pending = {"type": "defuse", "actor": actor,
                                 "kitten": "exploding_kitten"}
                else:
                    self._eliminate(s, actor, card)
            else:
                s.players[actor]["hand"].append(card)
                self._advance(s)
            return s
        cards = []
        if action.type == "play_card":
            cards = [args["card"]]
        elif action.type in ("play_pair", "play_triple"):
            cards = [args["card"]] * (2 if action.type == "play_pair" else 3)
        elif action.type == "play_five":
            cards = args["cards"]
        for card in cards:
            s.players[actor]["hand"].remove(card)
            s.zones["discard"].append(card)
        self._begin_reaction(s, action, cards)
        return s

    def is_terminal(self, state):
        return state.terminal

    def returns(self, state):
        if not state.terminal:
            return [0] * len(state.players)
        return [1 if p["id"] == state.winner else -1 for p in state.players]

    def render(self, s):
        return (f"phase={s.phase} player={s.current_player} owed={s.turns_owed} "
                f"deck={len(s.zones['deck'])} hands="
                f"{[len(p['hand']) for p in s.players]} winner={s.winner}")

    def action_to_name(self, a):
        if not isinstance(a, Action):
            raise ValueError("expected Action")
        details = ",".join(f"{k}={json.dumps(v, ensure_ascii=False, separators=(',', ':'))}"
                           for k, v in sorted(a.args.items()))
        return f"{a.type}[actor={a.actor}{',' if details else ''}{details}]"

    def name_to_action(self, name):
        if not isinstance(name, str):
            raise ValueError("invalid action name")
        for kind in ACTION_TYPES:
            prefix = kind + "[actor="
            if name.startswith(prefix) and name.endswith("]"):
                body = name[len(prefix):-1]
                decoder = json.JSONDecoder()
                comma = body.find(",")
                actor_text = body if comma < 0 else body[:comma]
                args, rest = {}, ("" if comma < 0 else body[comma + 1:])
                while rest:
                    eq = rest.find("=")
                    if eq <= 0:
                        raise ValueError("invalid action name")
                    key = rest[:eq]
                    value, used = decoder.raw_decode(rest[eq + 1:])
                    args[key] = value
                    rest = rest[eq + 1 + used:]
                    if rest.startswith(","):
                        rest = rest[1:]
                    elif rest:
                        raise ValueError("invalid action name")
                return self.action_from_data({"schema": ACTION_SCHEMA,
                                              "data": {"type": kind, "actor": int(actor_text),
                                                       "args": args}})
        raise ValueError("invalid action name")

    def state_to_data(self, s):
        data = {k: copy.deepcopy(getattr(s, k)) for k in
                ("configuration", "players", "zones", "current_player", "turns_owed",
                 "phase", "pending", "terminal", "winner", "turn_number", "chance")}
        return {"schema": STATE_SCHEMA, "data": data}

    def _exact(self, value, keys, label):
        if type(value) is not dict or set(value) != set(keys):
            raise ValueError(f"invalid {label}")

    def state_from_data(self, payload):
        self._exact(payload, ("schema", "data"), "state envelope")
        if payload["schema"] != STATE_SCHEMA:
            raise ValueError("invalid state schema")
        d = payload["data"]
        fields = ("configuration", "players", "zones", "current_player", "turns_owed",
                  "phase", "pending", "terminal", "winner", "turn_number", "chance")
        self._exact(d, fields, "state fields")
        self._validate_state(d)
        return GameState(**copy.deepcopy(d))

    def _validate_state(self, d):
        self._exact(d["configuration"], ("players", "seed", "variant"), "configuration")
        n = d["configuration"]["players"]
        if type(n) is not int or n not in (2, 3, 4, 5) or d["configuration"]["variant"] != "base":
            raise ValueError("invalid configuration")
        if d["configuration"]["seed"] is not None and type(d["configuration"]["seed"]) is not int:
            raise ValueError("invalid seed")
        if type(d["players"]) is not list or len(d["players"]) != n:
            raise ValueError("invalid players")
        for i, p in enumerate(d["players"]):
            self._exact(p, ("id", "alive", "hand", "preview"), "player")
            if p["id"] != i or type(p["alive"]) is not bool:
                raise ValueError("invalid player")
            self._cards(p["hand"]); self._cards(p["preview"])
        self._exact(d["zones"], ("deck", "discard", "box"), "zones")
        for z in d["zones"].values(): self._cards(z)
        for key in ("current_player", "turns_owed", "turn_number"):
            if type(d[key]) is not int:
                raise ValueError(f"invalid {key}")
        if not 0 <= d["current_player"] < n or d["turns_owed"] < 0 or d["turn_number"] < 0:
            raise ValueError("invalid counters")
        if d["phase"] not in PHASES or type(d["terminal"]) is not bool:
            raise ValueError("invalid phase")
        if d["winner"] is not None and (type(d["winner"]) is not int or not 0 <= d["winner"] < n):
            raise ValueError("invalid winner")
        self._exact(d["chance"], ("seed", "counter"), "chance")
        if d["chance"]["seed"] is not None and type(d["chance"]["seed"]) is not int:
            raise ValueError("invalid chance seed")
        if type(d["chance"]["counter"]) is not int or d["chance"]["counter"] < 0:
            raise ValueError("invalid chance counter")
        self._validate_pending(d["pending"], n)

    def _cards(self, cards):
        if type(cards) is not list or any(type(c) is not str or c not in CARDS for c in cards):
            raise ValueError("invalid cards")

    def _validate_pending(self, p, n):
        if p is None: return
        if type(p) is not dict or p.get("type") not in ("reaction", "favor", "defuse"):
            raise ValueError("invalid pending")
        if p["type"] == "favor":
            self._exact(p, ("type", "actor", "target"), "favor pending")
        elif p["type"] == "defuse":
            self._exact(p, ("type", "actor", "kitten"), "defuse pending")
            if p["kitten"] != "exploding_kitten": raise ValueError("invalid kitten")
        else:
            self._exact(p, ("type", "proposed", "cards", "nope_count", "responder",
                            "remaining_responders"), "reaction pending")
            self._cards(p["cards"])
            self.action_from_data({"schema": ACTION_SCHEMA, "data": p["proposed"]})
        ints = [v for k, v in p.items() if k in ("actor", "target", "responder", "nope_count")]
        if any(type(v) is not int for v in ints): raise ValueError("invalid pending integer")
        if "remaining_responders" in p and (type(p["remaining_responders"]) is not list or
            any(type(v) is not int for v in p["remaining_responders"])):
            raise ValueError("invalid responders")

    def action_to_data(self, a):
        if not isinstance(a, Action):
            raise ValueError("expected Action")
        return {"schema": ACTION_SCHEMA,
                "data": {"type": a.type, "actor": a.actor, "args": copy.deepcopy(a.args)}}

    def action_from_data(self, payload):
        self._exact(payload, ("schema", "data"), "action envelope")
        if payload["schema"] != ACTION_SCHEMA: raise ValueError("invalid action schema")
        d = payload["data"]; self._exact(d, ("type", "actor", "args"), "action fields")
        if d["type"] not in ACTION_TYPES or type(d["actor"]) is not int or type(d["args"]) is not dict:
            raise ValueError("invalid action")
        expected = {"draw": (), "play_card": ("card", "target"),
                    "play_pair": ("card", "target"),
                    "play_triple": ("card", "target", "requested"),
                    "play_five": ("cards", "retrieve"), "give_card": ("card",),
                    "reinsert": ("position",), "play_nope": (), "pass_nope": ()}[d["type"]]
        self._exact(d["args"], expected, "action args")
        a = d["args"]
        for k in ("card", "requested", "retrieve"):
            if k in a and (type(a[k]) is not str or a[k] not in CARDS): raise ValueError("invalid card")
        if "cards" in a: self._cards(a["cards"])
        if "target" in a and a["target"] is not None and type(a["target"]) is not int:
            raise ValueError("invalid target")
        if "position" in a and (type(a["position"]) is not int or a["position"] < 0):
            raise ValueError("invalid position")
        return _action(d["type"], d["actor"], **copy.deepcopy(a))

    def observation_to_data(self, s, player):
        if type(player) is not int or not 0 <= player < len(s.players):
            raise ValueError("invalid player")
        pending = copy.deepcopy(s.pending)
        if isinstance(pending, dict) and pending.get("type") == "reaction":
            pending.pop("cards", None)
        data = {"player": player, "own_hand": copy.deepcopy(s.players[player]["hand"]),
                "opponent_hand_sizes": {str(p["id"]): len(p["hand"]) for p in s.players
                                        if p["id"] != player},
                "deck_size": len(s.zones["deck"]), "discard": copy.deepcopy(s.zones["discard"]),
                "alive": [p["alive"] for p in s.players],
                "current_player": s.current_player, "turns_owed": s.turns_owed,
                "phase": s.phase, "pending": pending,
                "preview": copy.deepcopy(s.players[player]["preview"]),
                "terminal": s.terminal, "winner": s.winner, "turn_number": s.turn_number}
        return {"schema": OBS_SCHEMA, "data": data}
