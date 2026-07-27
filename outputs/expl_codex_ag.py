"""Exploding Kittens (German NSFW Edition 2018), from the supplied rulebook."""
from __future__ import annotations

import copy
import hashlib
import random
from typing import Any

CARDS = (
    "exploding_kitten", "defuse", "attack", "nope", "skip", "favor", "shuffle",
    "see_future", "cat_beard", "cat_cattermelon", "cat_hairy_potato",
    "cat_rainbow", "cat_tacocat",
)
CAT_CARDS = CARDS[8:]
PLAYABLE = ("attack", "nope", "skip", "favor", "shuffle", "see_future") + CAT_CARDS
LABEL = {
    "exploding_kitten": "Exploding Kitten", "defuse": "Entschärfung",
    "attack": "Angriff", "nope": "Nö!", "skip": "Hops!", "favor": "Wunsch",
    "shuffle": "Mischen", "see_future": "Blick in die Zukunft",
    "cat_beard": "Katzen-Karte: Bart", "cat_cattermelon": "Katzen-Karte: Melone",
    "cat_hairy_potato": "Katzen-Karte: Haarige Kartoffel",
    "cat_rainbow": "Katzen-Karte: Regenbogen", "cat_tacocat": "Katzen-Karte: Tacocat",
}
STATE_SCHEMA = "boardbench/exploding-kittens/state/1"
ACTION_SCHEMA = "boardbench/exploding-kittens/action/1"
OBS_SCHEMA = "boardbench/exploding-kittens/observation/1"


class Action:
    def __init__(self, type: str, actor: int, args: dict[str, Any]):
        self.type, self.actor, self.args = type, actor, args

    def __eq__(self, other):
        return isinstance(other, Action) and self.__dict__ == other.__dict__


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

    def __eq__(self, other):
        return isinstance(other, GameState) and self.__dict__ == other.__dict__


class Game:
    def __init__(self, num_players=None, seed=None):
        self.num_players = 2 if num_players is None else num_players
        if self.num_players not in (2, 3, 4, 5):
            raise ValueError("num_players must be one of 2, 3, 4, 5")
        if seed is not None and (not isinstance(seed, int) or isinstance(seed, bool)):
            raise ValueError("seed must be an int or None")
        self.seed = seed

    def _rng(self, state):
        material = f"{state.chance['seed']}:{state.chance['counter']}".encode()
        state.chance["counter"] += 1
        return random.Random(int.from_bytes(hashlib.sha256(material).digest(), "big"))

    def _shuffle(self, state, cards):
        self._rng(state).shuffle(cards)

    def initial_state(self):
        players = [{"id": i, "alive": True, "hand": [], "preview": []}
                   for i in range(self.num_players)]
        s = GameState({"players": self.num_players, "seed": self.seed, "variant": "base"},
                      players, {"deck": [], "discard": [], "box": []}, 0, 1, "play",
                      None, False, None, 0, {"seed": self.seed, "counter": 0})
        ordinary = (["attack"] * 4 + ["nope"] * 5 + ["skip"] * 4 +
                    ["favor"] * 4 + ["shuffle"] * 4 + ["see_future"] * 5 +
                    sum(([c] * 4 for c in CAT_CARDS), []))
        self._shuffle(s, ordinary)
        for p in players:
            p["hand"] = [ordinary.pop() for _ in range(7)] + ["defuse"]
        kittens = ["exploding_kitten"] * (self.num_players - 1)
        s.zones["box"] = (["exploding_kitten"] * (5 - self.num_players) +
                          (["defuse"] * 2 if self.num_players == 2 else []))
        remaining_defuses = 2 if self.num_players == 2 else 6 - self.num_players
        s.zones["deck"] = ordinary + ["defuse"] * remaining_defuses + kittens
        self._shuffle(s, s.zones["deck"])
        return s

    def current_player(self, state):
        return state.current_player

    def _alive_after(self, s, player):
        for n in range(1, len(s.players) + 1):
            q = (player + n) % len(s.players)
            if s.players[q]["alive"]:
                return q
        return player

    def _a(self, typ, actor, **args):
        return Action(typ, actor, args)

    def legal_actions(self, s):
        if s.terminal:
            return []
        p = s.current_player
        if s.phase == "reaction":
            r = s.pending["responder"]
            out = [self._a("pass_nope", r)]
            if "nope" in s.players[r]["hand"]:
                out.append(self._a("play_nope", r))
            return out
        if s.phase == "favor_give":
            actor = s.pending["target"]
            return [self._a("give_card", actor, card=c)
                    for c in sorted(set(s.players[actor]["hand"]))]
        if s.phase == "defuse_reinsert":
            return [self._a("reinsert", p, position=i)
                    for i in range(len(s.zones["deck"]) + 1)]
        hand = s.players[p]["hand"]
        out = [self._a("draw", p)]
        for card in sorted(set(hand)):
            if card in ("attack", "skip", "shuffle", "see_future"):
                out.append(self._a("play_card", p, card=card, target=None))
            elif card == "favor":
                out += [self._a("play_card", p, card=card, target=q)
                        for q in range(len(s.players)) if q != p and s.players[q]["alive"]]
        for card in sorted(set(hand)):
            if hand.count(card) >= 2:
                out += [self._a("play_pair", p, card=card, target=q)
                        for q in range(len(s.players)) if q != p and s.players[q]["alive"]
                        and s.players[q]["hand"]]
            if hand.count(card) >= 3:
                out += [self._a("play_triple", p, card=card, target=q, requested=req)
                        for q in range(len(s.players)) if q != p and s.players[q]["alive"]
                        for req in CARDS]
        if len(set(hand)) >= 5 and s.zones["discard"]:
            from itertools import combinations
            for cards in combinations(sorted(set(hand)), 5):
                for retrieve in sorted(set(s.zones["discard"])):
                    out.append(self._a("play_five", p, cards=list(cards), retrieve=retrieve))
        return out

    def _finish_turn(self, s, consume=True):
        s.players[s.current_player]["preview"] = []
        if consume:
            s.turns_owed -= 1
        if s.turns_owed <= 0:
            s.current_player = self._alive_after(s, s.current_player)
            s.turns_owed = 1
        s.turn_number += 1

    def _start_reaction(self, s, action, cards):
        actor = action.actor
        responders = [((actor + n) % len(s.players)) for n in range(1, len(s.players))
                      if s.players[(actor + n) % len(s.players)]["alive"]]
        proposed = self.action_to_data(action)["data"]
        s.pending = {"type": "reaction", "proposed": proposed, "cards": cards,
                     "nope_count": 0, "responder": responders[0],
                     "remaining_responders": responders[1:]}
        s.phase = "reaction"

    def _resolve(self, s, action):
        p, a = action.actor, action.args
        if action.type == "play_card":
            card = a["card"]
            if card == "attack":
                s.turns_owed = 0
                s.current_player = self._alive_after(s, p)
                s.turns_owed = 2
                s.turn_number += 1
            elif card == "skip":
                self._finish_turn(s)
            elif card == "favor":
                s.phase = "favor_give"
                s.pending = {"type": "favor", "actor": p, "target": a["target"]}
            elif card == "shuffle":
                self._shuffle(s, s.zones["deck"])
            elif card == "see_future":
                s.players[p]["preview"] = s.zones["deck"][:3]
        elif action.type == "play_pair":
            target = a["target"]
            if s.players[target]["hand"]:
                i = self._rng(s).randrange(len(s.players[target]["hand"]))
                s.players[p]["hand"].append(s.players[target]["hand"].pop(i))
        elif action.type == "play_triple":
            target, requested = a["target"], a["requested"]
            if requested in s.players[target]["hand"]:
                s.players[target]["hand"].remove(requested)
                s.players[p]["hand"].append(requested)
        elif action.type == "play_five":
            s.zones["discard"].remove(a["retrieve"])
            s.players[p]["hand"].append(a["retrieve"])

    def apply_action(self, state, action):
        s = copy.deepcopy(state)
        if action not in self.legal_actions(s):
            raise ValueError("illegal action")
        p = action.actor
        if action.type == "draw":
            card = s.zones["deck"].pop(0)
            s.players[p]["preview"] = []
            if card == "exploding_kitten":
                if "defuse" in s.players[p]["hand"]:
                    s.players[p]["hand"].remove("defuse")
                    s.zones["discard"].append("defuse")
                    s.phase, s.pending = "defuse_reinsert", {
                        "type": "defuse", "actor": p, "kitten": "exploding_kitten"}
                else:
                    s.players[p]["alive"] = False
                    s.zones["discard"].extend(s.players[p]["hand"] + [card])
                    s.players[p]["hand"] = []
                    alive = [q["id"] for q in s.players if q["alive"]]
                    if len(alive) == 1:
                        s.terminal, s.winner, s.phase, s.pending = True, alive[0], "terminal", None
                    else:
                        s.current_player, s.turns_owed = self._alive_after(s, p), 1
                        s.turn_number += 1
            else:
                s.players[p]["hand"].append(card)
                self._finish_turn(s)
        elif action.type == "reinsert":
            s.zones["deck"].insert(action.args["position"], "exploding_kitten")
            s.phase, s.pending = "play", None
            self._finish_turn(s)
        elif action.type == "give_card":
            card = action.args["card"]
            s.players[p]["hand"].remove(card)
            actor = s.pending["actor"]
            s.players[actor]["hand"].append(card)
            s.phase, s.pending = "play", None
        elif action.type in ("play_nope", "pass_nope"):
            pending = s.pending
            if action.type == "play_nope":
                s.players[p]["hand"].remove("nope")
                s.zones["discard"].append("nope")
                pending["nope_count"] += 1
                order = [((p + n) % len(s.players)) for n in range(1, len(s.players))
                         if s.players[(p + n) % len(s.players)]["alive"]]
                pending["responder"], pending["remaining_responders"] = order[0], order[1:]
            elif pending["remaining_responders"]:
                pending["responder"] = pending["remaining_responders"].pop(0)
            else:
                proposed = self.action_from_data({"schema": ACTION_SCHEMA, "data": pending["proposed"]})
                negated = pending["nope_count"] % 2 == 1
                s.phase, s.pending = "play", None
                if not negated:
                    self._resolve(s, proposed)
        else:
            if action.type == "play_card":
                cards = [action.args["card"]]
            elif action.type in ("play_pair", "play_triple"):
                cards = [action.args["card"]] * (2 if action.type == "play_pair" else 3)
            else:
                cards = list(action.args["cards"])
            for c in cards:
                s.players[p]["hand"].remove(c)
            s.zones["discard"].extend(cards)
            self._start_reaction(s, action, cards)
        return s

    def is_terminal(self, state):
        return state.terminal

    def returns(self, state):
        if not state.terminal:
            return [0.0] * len(state.players)
        return [1.0 if p["id"] == state.winner else -1.0 for p in state.players]

    def action_to_name(self, a):
        x = a.args
        if a.type == "draw": return f"{a.actor}: Karte ziehen"
        if a.type == "play_card": return f"{a.actor}: {LABEL[x['card']]} spielen -> {x['target']}"
        if a.type == "play_pair": return f"{a.actor}: Pärchen {LABEL[x['card']]} -> {x['target']}"
        if a.type == "play_triple": return f"{a.actor}: Drilling {LABEL[x['card']]} -> {x['target']}, wünsche {LABEL[x['requested']]}"
        if a.type == "play_five": return f"{a.actor}: Fünfling {','.join(x['cards'])} -> {LABEL[x['retrieve']]}"
        if a.type == "give_card": return f"{a.actor}: {LABEL[x['card']]} geben"
        if a.type == "reinsert": return f"{a.actor}: Exploding Kitten einfügen Position {x['position']}"
        if a.type == "play_nope": return f"{a.actor}: Nö! spielen"
        return f"{a.actor}: Nö!-Fenster passen"

    def name_to_action(self, name):
        # Names are deliberately canonical JSON-backed through exhaustive parsing.
        import re
        for typ in ("draw", "play_card", "play_pair", "play_triple", "play_five",
                    "give_card", "reinsert", "play_nope", "pass_nope"):
            pass
        m = re.match(r"^(\d+): ", name)
        if not m: raise ValueError("invalid action name")
        actor = int(m.group(1))
        # Candidate generation is finite and independent of state.
        candidates = [self._a("draw", actor), self._a("play_nope", actor),
                      self._a("pass_nope", actor)]
        candidates += [self._a("play_card", actor, card=c, target=t)
                       for c in ("attack", "skip", "shuffle", "see_future", "favor")
                       for t in ([None] if c != "favor" else range(5))]
        candidates += [self._a("give_card", actor, card=c) for c in CARDS]
        candidates += [self._a("reinsert", actor, position=i) for i in range(60)]
        candidates += [self._a("play_pair", actor, card=c, target=t) for c in CARDS for t in range(5)]
        candidates += [self._a("play_triple", actor, card=c, target=t, requested=r)
                       for c in CARDS for t in range(5) for r in CARDS]
        # Five-card names are parsed directly because combinations are numerous.
        for c in candidates:
            if self.action_to_name(c) == name: return c
        mf = re.match(r"^\d+: Fünfling (.+) -> (.+)$", name)
        if mf:
            cards = mf.group(1).split(",")
            reverse = {v: k for k, v in LABEL.items()}
            if len(cards) == 5 and mf.group(2) in reverse:
                return self._a("play_five", actor, cards=cards, retrieve=reverse[mf.group(2)])
        raise ValueError("invalid action name")

    def action_to_data(self, a):
        return {"schema": ACTION_SCHEMA, "data": {
            "type": a.type, "actor": a.actor, "args": copy.deepcopy(a.args)}}

    def action_from_data(self, payload):
        self._envelope(payload, ACTION_SCHEMA)
        d = payload["data"]
        if set(d) != {"type", "actor", "args"} or type(d["actor"]) is not int or not isinstance(d["args"], dict):
            raise ValueError("invalid action fields")
        typ, a = d["type"], d["args"]
        shapes = {"draw": set(), "play_card": {"card", "target"}, "play_pair": {"card", "target"},
                  "play_triple": {"card", "target", "requested"}, "play_five": {"cards", "retrieve"},
                  "give_card": {"card"}, "reinsert": {"position"}, "play_nope": set(), "pass_nope": set()}
        if typ not in shapes or set(a) != shapes[typ]: raise ValueError("invalid action")
        if d["actor"] < 0:
            raise ValueError("invalid actor")
        if typ == "play_card":
            if a["card"] not in ("attack", "skip", "favor", "shuffle", "see_future"):
                raise ValueError("invalid card")
            if a["card"] == "favor":
                if type(a["target"]) is not int or a["target"] < 0:
                    raise ValueError("invalid target")
            elif a["target"] is not None:
                raise ValueError("invalid target")
        elif typ in ("play_pair", "play_triple"):
            if a["card"] not in CARDS or type(a["target"]) is not int or a["target"] < 0:
                raise ValueError("invalid combination")
            if typ == "play_triple" and a["requested"] not in CARDS:
                raise ValueError("invalid requested card")
        elif typ == "play_five":
            if (not isinstance(a["cards"], list) or len(a["cards"]) != 5
                    or any(card not in CARDS for card in a["cards"])
                    or len(set(a["cards"])) != 5 or a["retrieve"] not in CARDS):
                raise ValueError("invalid five-card combination")
        elif typ == "give_card" and a["card"] not in CARDS:
            raise ValueError("invalid card")
        elif typ == "reinsert" and (type(a["position"]) is not int or a["position"] < 0):
            raise ValueError("invalid position")
        return Action(typ, d["actor"], copy.deepcopy(a))

    def state_to_data(self, s):
        return {"schema": STATE_SCHEMA, "data": copy.deepcopy(s.__dict__)}

    def state_from_data(self, payload):
        self._envelope(payload, STATE_SCHEMA)
        d = payload["data"]
        required = {"configuration", "players", "zones", "current_player", "turns_owed",
                    "phase", "pending", "terminal", "winner", "turn_number", "chance"}
        if set(d) != required:
            raise ValueError("invalid state fields")
        configuration = d["configuration"]
        if (not isinstance(configuration, dict)
                or set(configuration) != {"players", "seed", "variant"}
                or type(configuration["players"]) is not int
                or configuration["players"] not in (2, 3, 4, 5)
                or (configuration["seed"] is not None and type(configuration["seed"]) is not int)
                or configuration["variant"] != "base"):
            raise ValueError("invalid configuration")
        n = configuration["players"]
        if not isinstance(d["players"], list) or len(d["players"]) != n:
            raise ValueError("invalid players")
        for index, player in enumerate(d["players"]):
            if (not isinstance(player, dict)
                    or set(player) != {"id", "alive", "hand", "preview"}
                    or player["id"] != index or type(player["alive"]) is not bool):
                raise ValueError("invalid player")
            self._card_list(player["hand"])
            self._card_list(player["preview"])
        if not isinstance(d["zones"], dict) or set(d["zones"]) != {"deck", "discard", "box"}:
            raise ValueError("invalid zones")
        for zone in d["zones"].values():
            self._card_list(zone)
        if type(d["current_player"]) is not int or not 0 <= d["current_player"] < n:
            raise ValueError("invalid current player")
        if type(d["turns_owed"]) is not int or d["turns_owed"] < 0:
            raise ValueError("invalid turns owed")
        if d["phase"] not in ("play", "reaction", "favor_give", "defuse_reinsert", "terminal"):
            raise ValueError("invalid phase")
        if type(d["terminal"]) is not bool:
            raise ValueError("invalid terminal flag")
        if d["winner"] is not None and (type(d["winner"]) is not int or not 0 <= d["winner"] < n):
            raise ValueError("invalid winner")
        if type(d["turn_number"]) is not int or d["turn_number"] < 0:
            raise ValueError("invalid turn number")
        chance = d["chance"]
        if (not isinstance(chance, dict) or set(chance) != {"seed", "counter"}
                or (chance["seed"] is not None and type(chance["seed"]) is not int)
                or type(chance["counter"]) is not int or chance["counter"] < 0):
            raise ValueError("invalid chance")
        self._validate_pending(d["pending"], d["phase"], n)
        return GameState(**copy.deepcopy(d))

    def _card_list(self, value):
        if not isinstance(value, list) or any(card not in CARDS for card in value):
            raise ValueError("invalid card list")

    def _validate_pending(self, pending, phase, n):
        expected = {
            "play": None, "terminal": None, "reaction": "reaction",
            "favor_give": "favor", "defuse_reinsert": "defuse",
        }[phase]
        if expected is None:
            if pending is not None:
                raise ValueError("invalid pending decision")
            return
        if not isinstance(pending, dict) or pending.get("type") != expected:
            raise ValueError("invalid pending decision")
        if expected == "favor":
            if set(pending) != {"type", "actor", "target"}:
                raise ValueError("invalid favor decision")
            for key in ("actor", "target"):
                if type(pending[key]) is not int or not 0 <= pending[key] < n:
                    raise ValueError("invalid favor player")
        elif expected == "defuse":
            if (set(pending) != {"type", "actor", "kitten"}
                    or type(pending["actor"]) is not int or not 0 <= pending["actor"] < n
                    or pending["kitten"] != "exploding_kitten"):
                raise ValueError("invalid defuse decision")
        else:
            required = {"type", "proposed", "cards", "nope_count", "responder",
                        "remaining_responders"}
            if set(pending) != required:
                raise ValueError("invalid reaction decision")
            self.action_from_data({"schema": ACTION_SCHEMA, "data": pending["proposed"]})
            self._card_list(pending["cards"])
            if (type(pending["nope_count"]) is not int or pending["nope_count"] < 0
                    or type(pending["responder"]) is not int
                    or not 0 <= pending["responder"] < n
                    or not isinstance(pending["remaining_responders"], list)
                    or any(type(p) is not int or not 0 <= p < n
                           for p in pending["remaining_responders"])):
                raise ValueError("invalid reaction fields")

    def observation_to_data(self, s, player):
        if type(player) is not int or not 0 <= player < len(s.players): raise ValueError("invalid player")
        pending = copy.deepcopy(s.pending)
        if pending and pending["type"] == "reaction":
            pending.pop("cards", None)
        data = {"player": player, "own_hand": copy.deepcopy(s.players[player]["hand"]),
                "opponent_hand_sizes": {str(p["id"]): len(p["hand"]) for p in s.players if p["id"] != player},
                "deck_size": len(s.zones["deck"]), "discard": copy.deepcopy(s.zones["discard"]),
                "alive": [p["alive"] for p in s.players], "current_player": s.current_player,
                "turns_owed": s.turns_owed, "phase": s.phase, "pending": pending,
                "preview": copy.deepcopy(s.players[player]["preview"]), "terminal": s.terminal,
                "winner": s.winner, "turn_number": s.turn_number}
        return {"schema": OBS_SCHEMA, "data": data}

    def _envelope(self, payload, schema):
        if not isinstance(payload, dict) or set(payload) != {"schema", "data"} or payload["schema"] != schema or not isinstance(payload["data"], dict):
            raise ValueError("invalid envelope")

    def render(self, s):
        hands = ", ".join(f"P{p['id']}:{len(p['hand'])}{'' if p['alive'] else ' ausgeschieden'}" for p in s.players)
        return f"Phase={s.phase} Spieler={s.current_player} Züge={s.turns_owed} Stapel={len(s.zones['deck'])} | {hands}"
