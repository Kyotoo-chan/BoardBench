"""Exploding Kittens (German NSFW 2018 rule sheet), standard-library only."""
from __future__ import annotations

import copy
import json
import random

CARDS = ("exploding_kitten", "defuse", "attack", "nope", "skip", "favor",
         "shuffle", "see_future", "cat_beard", "cat_cattermelon",
         "cat_hairy_potato", "cat_rainbow", "cat_tacocat")
COUNTS = dict(zip(CARDS, (4, 6, 4, 5, 4, 4, 4, 5, 4, 4, 4, 4, 4)))
CAT_CARDS = set(CARDS[8:])
STATE_SCHEMA = "boardbench/exploding-kittens/state/2"
ACTION_SCHEMA = "boardbench/exploding-kittens/action/2"
OBS_SCHEMA = "boardbench/exploding-kittens/observation/2"
PHASES = {"play", "reaction", "favor_give", "defuse_reinsert", "terminal"}
ACTION_TYPES = {"draw", "play_card", "play_pair", "play_triple", "play_five",
                "give_card", "reinsert", "play_nope", "pass_nope"}


class Action:
    def __init__(self, type, actor, args=None):
        self.type, self.actor, self.args = type, actor, dict(args or {})

    def __eq__(self, other):
        return isinstance(other, Action) and (self.type, self.actor, self.args) == (
            other.type, other.actor, other.args)

    def __repr__(self):
        return f"Action({self.type!r}, {self.actor!r}, {self.args!r})"


class GameState:
    def __init__(self, data):
        self.data = data

    def __deepcopy__(self, memo):
        return GameState(copy.deepcopy(self.data, memo))


def _is_int(x):
    return isinstance(x, int) and not isinstance(x, bool)


def _is_json_value(value):
    if value is None or isinstance(value, (bool, str)) or _is_int(value):
        return True
    if isinstance(value, float):
        return value == value and value not in (float("inf"), float("-inf"))
    if isinstance(value, list):
        return all(_is_json_value(item) for item in value)
    if isinstance(value, dict):
        return all(isinstance(key, str) and _is_json_value(item)
                   for key, item in value.items())
    return False


class Game:
    def __init__(self, num_players=None, seed=None):
        n = 2 if num_players is None else num_players
        if n not in (2, 3, 4, 5):
            raise ValueError("num_players must be one of 2, 3, 4, 5")
        if seed is not None and not _is_int(seed):
            raise ValueError("seed must be an integer or None")
        self.num_players, self.seed = n, seed

    def initial_state(self):
        rng = random.Random(self.seed)
        pool = []
        for card, count in COUNTS.items():
            if card not in ("exploding_kitten", "defuse"):
                pool += [card] * count
        rng.shuffle(pool)
        players = []
        for i in range(self.num_players):
            hand = [pool.pop() for _ in range(7)] + ["defuse"]
            rng.shuffle(hand)
            players.append({"id": i, "alive": True, "hand": hand, "preview": []})
        kittens = ["exploding_kitten"] * (self.num_players - 1)
        defuses = ["defuse"] * (2 if self.num_players == 2 else 6 - self.num_players)
        deck = pool + kittens + defuses
        rng.shuffle(deck)
        box = ["exploding_kitten"] * (5 - self.num_players)
        if self.num_players == 2:
            box += ["defuse"] * 2
        return GameState({
            "configuration": {"players": self.num_players, "seed": self.seed, "variant": "base"},
            "players": players, "zones": {"deck": deck, "discard": [], "box": box},
            "current_player": 0, "turns_owed": 1, "phase": "play", "pending": None,
            "terminal": False, "winner": None, "turn_number": 0,
            "chance": {"seed": self.seed, "counter": 0}})

    def current_player(self, state):
        return state.data["current_player"]

    def is_terminal(self, state):
        return state.data["terminal"]

    def returns(self, state):
        n = state.data["configuration"]["players"]
        if not state.data["terminal"]:
            return [0.0] * n
        return [1.0 if i == state.data["winner"] else -1.0 for i in range(n)]

    def _alive_targets(self, d, actor):
        return [p["id"] for p in d["players"] if p["alive"] and p["id"] != actor]

    def legal_actions(self, state):
        d = state.data
        if d["terminal"]:
            return []
        phase, actor = d["phase"], d["current_player"]
        if phase == "reaction":
            actor = d["pending"]["responder"]
            out = [Action("pass_nope", actor)]
            if "nope" in d["players"][actor]["hand"]:
                out.append(Action("play_nope", actor))
            return out
        if phase == "favor_give":
            actor = d["pending"]["target"]
            return [Action("give_card", actor, {"card": c}) for c in sorted(set(d["players"][actor]["hand"]))]
        if phase == "defuse_reinsert":
            return [Action("reinsert", actor, {"position": i})
                    for i in range(len(d["zones"]["deck"]) + 1)]
        hand = d["players"][actor]["hand"]
        out = [Action("draw", actor)] if d["zones"]["deck"] else []
        targets = self._alive_targets(d, actor)
        for card in sorted(set(hand)):
            if card in ("exploding_kitten", "defuse", "nope") or card in CAT_CARDS:
                continue
            if card == "favor":
                out += [Action("play_card", actor, {"card": card, "target": t}) for t in targets]
            else:
                out.append(Action("play_card", actor, {"card": card, "target": None}))
        for card in sorted(set(hand)):
            if hand.count(card) >= 2:
                out += [Action("play_pair", actor, {"card": card, "target": t}) for t in targets]
            if hand.count(card) >= 3:
                for t in targets:
                    out += [Action("play_triple", actor, {"card": card, "target": t, "requested": r})
                            for r in CARDS]
        distinct = sorted(set(hand))
        if len(distinct) >= 5 and d["zones"]["discard"]:
            import itertools
            retrieves = sorted(set(d["zones"]["discard"]))
            for chosen in itertools.combinations(distinct, 5):
                out += [Action("play_five", actor, {"cards": list(chosen), "retrieve": r})
                        for r in retrieves]
        return out

    def _next_alive(self, d, actor):
        n = len(d["players"])
        for k in range(1, n + 1):
            j = (actor + k) % n
            if d["players"][j]["alive"]:
                return j
        return actor

    def _responders(self, d, actor):
        result, p = [], self._next_alive(d, actor)
        while p != actor:
            result.append(p)
            p = self._next_alive(d, p)
        return result

    def _advance(self, d):
        if d["turns_owed"] > 1:
            d["turns_owed"] -= 1
        else:
            d["current_player"] = self._next_alive(d, d["current_player"])
            d["turns_owed"] = 1
        d["turn_number"] += 1
        d["phase"], d["pending"] = "play", None

    def _shuffle(self, d):
        chance = d["chance"]
        rng = random.Random(f"{chance['seed']}:{chance['counter']}")
        rng.shuffle(d["zones"]["deck"])
        chance["counter"] += 1

    def _propose(self, d, action, cards):
        responders = self._responders(d, action.actor)
        proposed = {"type": action.type, "actor": action.actor, "args": copy.deepcopy(action.args)}
        if not responders:
            self._resolve(d, proposed)
            return
        d["phase"] = "reaction"
        d["pending"] = {"type": "reaction", "proposed": proposed, "cards": list(cards),
                        "nope_count": 0, "responder": responders[0],
                        "remaining_responders": responders[1:]}

    def _resolve(self, d, a):
        typ, actor, args = a["type"], a["actor"], a["args"]
        if typ == "play_card":
            card = args["card"]
            if card == "attack":
                target = self._next_alive(d, actor)
                d["current_player"], d["turns_owed"] = target, 2
                d["turn_number"] += 1
            elif card == "skip":
                self._advance(d)
            elif card == "favor":
                d["phase"], d["current_player"] = "favor_give", args["target"]
                d["pending"] = {"type": "favor", "actor": actor, "target": args["target"]}
            elif card == "shuffle":
                self._shuffle(d); d["phase"], d["pending"] = "play", None
            elif card == "see_future":
                d["players"][actor]["preview"] = list(reversed(d["zones"]["deck"][-3:]))
                d["phase"], d["pending"] = "play", None
        elif typ == "play_pair":
            target = args["target"]
            hand = d["players"][target]["hand"]
            if hand:
                rng = random.Random(f"{d['chance']['seed']}:{d['chance']['counter']}")
                card = hand.pop(rng.randrange(len(hand))); d["chance"]["counter"] += 1
                d["players"][actor]["hand"].append(card)
            d["phase"], d["pending"] = "play", None
        elif typ == "play_triple":
            hand = d["players"][args["target"]]["hand"]
            if args["requested"] in hand:
                hand.remove(args["requested"]); d["players"][actor]["hand"].append(args["requested"])
            d["phase"], d["pending"] = "play", None
        elif typ == "play_five":
            d["zones"]["discard"].remove(args["retrieve"])
            d["players"][actor]["hand"].append(args["retrieve"])
            d["phase"], d["pending"] = "play", None

    def apply_action(self, state, action):
        legal = self.legal_actions(state)
        if action not in legal:
            raise ValueError("illegal action")
        s, d = copy.deepcopy(state), None
        d = s.data
        typ, actor, args = action.type, action.actor, action.args
        if typ == "draw":
            d["players"][actor]["preview"] = []
            card = d["zones"]["deck"].pop()
            if card == "exploding_kitten":
                hand = d["players"][actor]["hand"]
                if "defuse" in hand:
                    hand.remove("defuse"); d["zones"]["discard"].append("defuse")
                    d["phase"] = "defuse_reinsert"
                    d["pending"] = {"type": "defuse", "actor": actor, "kitten": card}
                else:
                    d["zones"]["discard"].append(card)
                    d["players"][actor]["alive"] = False
                    alive = [p["id"] for p in d["players"] if p["alive"]]
                    if len(alive) == 1:
                        d.update({"terminal": True, "winner": alive[0], "phase": "terminal", "pending": None})
                    else:
                        d["current_player"] = self._next_alive(d, actor)
                        d["turns_owed"] = 1; d["turn_number"] += 1
            else:
                d["players"][actor]["hand"].append(card); self._advance(d)
        elif typ in ("play_card", "play_pair", "play_triple", "play_five"):
            if typ == "play_card":
                cards = [args["card"]]
            elif typ in ("play_pair", "play_triple"):
                cards = [args["card"]] * (2 if typ == "play_pair" else 3)
            else:
                cards = list(args["cards"])
            for card in cards:
                d["players"][actor]["hand"].remove(card)
                d["zones"]["discard"].append(card)
            self._propose(d, action, cards)
        elif typ == "give_card":
            card = args["card"]; pending = d["pending"]
            d["players"][actor]["hand"].remove(card)
            d["players"][pending["actor"]]["hand"].append(card)
            d["current_player"], d["phase"], d["pending"] = pending["actor"], "play", None
        elif typ == "reinsert":
            d["zones"]["deck"].insert(args["position"], "exploding_kitten")
            self._advance(d)
        elif typ == "pass_nope":
            p = d["pending"]
            if p["remaining_responders"]:
                p["responder"] = p["remaining_responders"].pop(0)
            else:
                proposed, active = p["proposed"], p["nope_count"] % 2 == 0
                if active: self._resolve(d, proposed)
                else: d["phase"], d["pending"] = "play", None
        elif typ == "play_nope":
            d["players"][actor]["hand"].remove("nope"); d["zones"]["discard"].append("nope")
            p = d["pending"]; p["nope_count"] += 1
            responders = self._responders(d, actor)
            p["responder"] = responders[0]
            p["remaining_responders"] = responders[1:]
        return s

    def action_to_name(self, action):
        labels = {"draw": "Ziehen", "play_card": "Spielen", "play_pair": "Pärchen",
                  "play_triple": "Drilling", "play_five": "Fünfling",
                  "give_card": "Karte geben", "reinsert": "Wiedereinsetzen",
                  "play_nope": "NÖ!", "pass_nope": "NÖ! passen"}
        tail = json.dumps(action.args, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return f"{labels[action.type]} [player {action.actor}] {tail}"

    def name_to_action(self, name):
        for typ in ACTION_TYPES:
            label = self.action_to_name(Action(typ, 0)).split(" [", 1)[0]
            prefix = label + " [player "
            if name.startswith(prefix):
                rest = name[len(prefix):]
                actor_s, tail = rest.split("] ", 1)
                return Action(typ, int(actor_s), json.loads(tail))
        raise ValueError("unknown action name")

    def action_to_data(self, action):
        payload = {"schema": ACTION_SCHEMA, "data": {"type": action.type, "actor": action.actor,
                                                     "args": copy.deepcopy(action.args)}}
        self.action_from_data(payload)
        return payload

    def action_from_data(self, payload):
        self._envelope(payload, ACTION_SCHEMA)
        if not _is_json_value(payload):
            raise ValueError("action is not JSON-safe")
        d = payload["data"]
        if set(d) != {"type", "actor", "args"} or d.get("type") not in ACTION_TYPES:
            raise ValueError("invalid action fields")
        if not _is_int(d["actor"]) or not isinstance(d["args"], dict):
            raise ValueError("invalid action")
        expected = {"draw": set(), "play_card": {"card", "target"}, "play_pair": {"card", "target"},
                    "play_triple": {"card", "target", "requested"}, "play_five": {"cards", "retrieve"},
                    "give_card": {"card"}, "reinsert": {"position"}, "play_nope": set(), "pass_nope": set()}
        if set(d["args"]) != expected[d["type"]]:
            raise ValueError("invalid action arguments")
        args = d["args"]
        if not 0 <= d["actor"] < self.num_players:
            raise ValueError("invalid action actor")
        typ = d["type"]
        card_fields = {
            "play_card": ("card",), "play_pair": ("card",),
            "play_triple": ("card", "requested"), "give_card": ("card",),
            "play_five": ("retrieve",)}
        if any(not isinstance(args[key], str) or args[key] not in CARDS
               for key in card_fields.get(typ, ())):
            raise ValueError("invalid card")
        if typ in ("play_pair", "play_triple"):
            if not _is_int(args["target"]) or not 0 <= args["target"] < self.num_players:
                raise ValueError("invalid target")
        if typ == "play_card":
            target = args["target"]
            if target is not None and (not _is_int(target) or not 0 <= target < self.num_players):
                raise ValueError("invalid target")
        if typ == "play_five":
            cards = args["cards"]
            if (not isinstance(cards, list) or len(cards) != 5 or
                    any(not isinstance(c, str) for c in cards) or
                    len(set(cards)) != 5 or any(c not in CARDS for c in cards)):
                raise ValueError("invalid five-card combination")
        if typ == "reinsert" and (not _is_int(args["position"]) or args["position"] < 0):
            raise ValueError("invalid reinsert position")
        return Action(d["type"], d["actor"], copy.deepcopy(d["args"]))

    def state_to_data(self, state):
        return {"schema": STATE_SCHEMA, "data": copy.deepcopy(state.data)}

    def _envelope(self, payload, schema):
        if not isinstance(payload, dict) or set(payload) != {"schema", "data"}:
            raise ValueError("invalid envelope")
        if payload["schema"] != schema or not isinstance(payload["data"], dict):
            raise ValueError("invalid schema")

    def state_from_data(self, payload):
        self._envelope(payload, STATE_SCHEMA)
        d = payload["data"]
        required = {"configuration", "players", "zones", "current_player", "turns_owed",
                    "phase", "pending", "terminal", "winner", "turn_number", "chance"}
        if set(d) != required:
            raise ValueError("invalid state fields")
        if not _is_json_value(payload):
            raise ValueError("state is not JSON-safe")
        config = d.get("configuration")
        if (not isinstance(config, dict) or set(config) != {"players", "seed", "variant"} or
                not _is_int(config["players"]) or config["players"] not in (2, 3, 4, 5) or
                (config["seed"] is not None and not _is_int(config["seed"])) or
                config["variant"] != "base"):
            raise ValueError("invalid configuration")
        players = d.get("players")
        if not isinstance(players, list) or len(players) != config["players"]:
            raise ValueError("invalid players")
        for i, player in enumerate(players):
            if (not isinstance(player, dict) or set(player) != {"id", "alive", "hand", "preview"} or
                    player["id"] != i or not isinstance(player["alive"], bool) or
                    not isinstance(player["hand"], list) or not isinstance(player["preview"], list) or
                    any(c not in CARDS for c in player["hand"] + player["preview"])):
                raise ValueError("invalid player")
        zones = d.get("zones")
        if (not isinstance(zones, dict) or set(zones) != {"deck", "discard", "box"} or
                any(not isinstance(zones[z], list) for z in zones) or
                any(c not in CARDS for z in zones.values() for c in z)):
            raise ValueError("invalid zones")
        if (not _is_int(d.get("current_player")) or
                not 0 <= d["current_player"] < config["players"] or
                not _is_int(d.get("turns_owed")) or d["turns_owed"] < 0 or
                d.get("phase") not in PHASES or not isinstance(d.get("terminal"), bool) or
                (d.get("winner") is not None and
                 (not _is_int(d["winner"]) or not 0 <= d["winner"] < config["players"])) or
                not _is_int(d.get("turn_number")) or d["turn_number"] < 0):
            raise ValueError("invalid state scalar")
        chance = d.get("chance")
        if (not isinstance(chance, dict) or set(chance) != {"seed", "counter"} or
                (chance["seed"] is not None and not _is_int(chance["seed"])) or
                not _is_int(chance["counter"]) or chance["counter"] < 0):
            raise ValueError("invalid chance state")
        self._validate_pending(d["pending"], config["players"])
        return GameState(copy.deepcopy(d))

    def _validate_pending(self, pending, num_players):
        if pending is None:
            return
        if not isinstance(pending, dict) or pending.get("type") not in {
                "reaction", "favor", "defuse"}:
            raise ValueError("invalid pending decision")
        typ = pending["type"]
        if typ == "favor":
            if (set(pending) != {"type", "actor", "target"} or
                    any(not _is_int(pending[k]) or not 0 <= pending[k] < num_players
                        for k in ("actor", "target"))):
                raise ValueError("invalid pending favor")
        elif typ == "defuse":
            if (set(pending) != {"type", "actor", "kitten"} or
                    not _is_int(pending["actor"]) or not 0 <= pending["actor"] < num_players or
                    pending["kitten"] != "exploding_kitten"):
                raise ValueError("invalid pending defuse")
        else:
            required = {"type", "proposed", "cards", "nope_count", "responder",
                        "remaining_responders"}
            proposed = pending.get("proposed")
            if (set(pending) != required or not isinstance(proposed, dict) or
                    set(proposed) != {"type", "actor", "args"} or
                    proposed["type"] not in ACTION_TYPES or not _is_int(proposed["actor"]) or
                    not 0 <= proposed["actor"] < num_players or
                    not isinstance(proposed["args"], dict) or
                    not isinstance(pending["cards"], list) or
                    any(c not in CARDS for c in pending["cards"]) or
                    not _is_int(pending["nope_count"]) or pending["nope_count"] < 0 or
                    not _is_int(pending["responder"]) or
                    not 0 <= pending["responder"] < num_players or
                    not isinstance(pending["remaining_responders"], list) or
                    any(not _is_int(p) or not 0 <= p < num_players
                        for p in pending["remaining_responders"])):
                raise ValueError("invalid pending reaction")
            self.action_from_data({"schema": ACTION_SCHEMA, "data": proposed})

    def observation_to_data(self, state, player):
        d = state.data
        if not _is_int(player) or not 0 <= player < len(d["players"]):
            raise ValueError("invalid player")
        pending = copy.deepcopy(d["pending"])
        data = {"player": player, "own_hand": list(d["players"][player]["hand"]),
                "opponent_hand_sizes": {str(p["id"]): len(p["hand"]) for p in d["players"] if p["id"] != player},
                "deck_size": len(d["zones"]["deck"]), "discard": list(d["zones"]["discard"]),
                "alive": [p["alive"] for p in d["players"]], "current_player": d["current_player"],
                "turns_owed": d["turns_owed"], "phase": d["phase"], "pending": pending,
                "preview": list(d["players"][player]["preview"]), "terminal": d["terminal"],
                "winner": d["winner"], "turn_number": d["turn_number"]}
        return {"schema": OBS_SCHEMA, "data": data}

    def render(self, state):
        d = state.data
        if d["terminal"]:
            return f"Spielende — player {d['winner']} wins."
        sizes = ", ".join(f"P{p['id']}:{len(p['hand'])}{'' if p['alive'] else ' (out)'}" for p in d["players"])
        return f"Turn {d['turn_number']} | {d['phase']} | player {d['current_player']} | deck {len(d['zones']['deck'])} | {sizes}"
