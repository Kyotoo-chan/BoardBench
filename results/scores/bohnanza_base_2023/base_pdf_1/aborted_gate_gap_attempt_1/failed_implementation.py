from __future__ import annotations

import copy
import itertools
import json
import math
import random
from typing import NamedTuple

BEANS = ("gartenbohne", "rote_bohne", "augenbohne", "sojabohne", "brechbohne", "saubohne", "feuerbohne", "blaue_bohne")
COUNTS = dict(zip(BEANS, (6, 8, 10, 12, 14, 16, 18, 20)))
METERS = {
    "gartenbohne": ((2, 2), (3, 3)),
    "rote_bohne": ((2, 1), (3, 2), (4, 3), (5, 4)),
    "augenbohne": ((2, 1), (4, 2), (5, 3), (6, 4)),
    "sojabohne": ((2, 1), (4, 2), (6, 3), (7, 4)),
    "brechbohne": ((3, 1), (5, 2), (6, 3), (7, 4)),
    "saubohne": ((3, 1), (5, 2), (7, 3), (8, 4)),
    "feuerbohne": ((3, 1), (6, 2), (8, 3), (9, 4)),
    "blaue_bohne": ((4, 1), (6, 2), (8, 3), (10, 4)),
}
PHASES = ("plant_first", "plant_second", "reveal", "trade", "trade_response", "plant_received", "draw", "terminal")
ACTION_TYPES = ("plant", "harvest", "reveal", "trade_propose", "trade_accept", "trade_reject", "end_trade", "draw", "pass")
STATE_SCHEMA = "boardbench/bohnanza-base-2023/state/1"
ACTION_SCHEMA = "boardbench/bohnanza-base-2023/action/1"
OBS_SCHEMA = "boardbench/bohnanza-base-2023/observation/1"


class Action(NamedTuple):
    type: str
    actor: int
    args_json: str = "{}"

    @property
    def args(self):
        return json.loads(self.args_json)


class GameState:
    def __init__(self, data):
        self.data = data

    def __deepcopy__(self, memo):
        return GameState(copy.deepcopy(self.data, memo))


def _action(kind, actor, args=None):
    return Action(kind, actor, json.dumps(args or {}, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


class Game:
    def __init__(self, num_players=None, seed=None):
        self.num_players = 4 if num_players is None else num_players
        if type(self.num_players) is not int or not 4 <= self.num_players <= 5:
            raise ValueError("this source condition supports 4 or 5 players")
        if seed is not None and type(seed) is not int:
            raise TypeError("seed must be int or null")
        self.seed = seed

    def initial_state(self):
        deck = [b for b in BEANS for _ in range(COUNTS[b])]
        random.Random(self.seed).shuffle(deck)
        players = [{"id": i, "hand": [], "fields": [[], []], "coins": 0} for i in range(self.num_players)]
        # Deal one card at a time; appending preserves the unchangeable hand order.
        for _ in range(5):
            for p in players:
                p["hand"].append(deck.pop(0))
        data = {
            "configuration": {"players": self.num_players, "seed": self.seed},
            "current_player": 0, "active_player": 0, "start_player": 0,
            "phase": "plant_first", "terminal": False, "players": players,
            "zones": {"deck": deck, "discard": [], "revealed": [], "pending_received": [[] for _ in players], "reserve": []},
            "depletions": 0, "pending": None,
            "chance": {"seed": self.seed, "draw_index": 0},
        }
        return GameState(data)

    def current_player(self, state):
        return state.data["current_player"]

    def _can_harvest(self, d, player, field):
        fs = d["players"][player]["fields"]
        if not (0 <= field < len(fs)) or not fs[field]:
            return False
        return len(fs[field]) > 1 or not any(len(x) > 1 for x in fs)

    def _harvest_actions(self, d):
        out = []
        for p in range(len(d["players"])):
            for f in range(len(d["players"][p]["fields"])):
                if self._can_harvest(d, p, f):
                    out.append(_action("harvest", p, {"player": p, "field": f}))
        return out

    def _plant_actions(self, d, actor, source, index, bean):
        out = []
        for f, cards in enumerate(d["players"][actor]["fields"]):
            if not cards or cards[0] == bean:
                out.append(_action("plant", actor, {"field": f, "source": source, "index": index, "bean": bean}))
        return out

    @staticmethod
    def _refs(owner, zone, cards):
        return [{"owner": owner, "zone": zone, "index": i, "bean": b} for i, b in enumerate(cards)]

    @staticmethod
    def _subsets(refs):
        # The source explicitly illustrates two-for-one; keep proposals finite enough
        # for a discrete legal-action interface while retaining every such offer.
        for n in range(1, min(2, len(refs)) + 1):
            yield from itertools.combinations(refs, n)

    def legal_actions(self, state):
        d = state.data
        if d["terminal"] or d["phase"] == "terminal":
            return []
        phase, actor = d["phase"], d["current_player"]
        out = self._harvest_actions(d)
        if phase == "plant_first":
            hand = d["players"][actor]["hand"]
            if hand:
                out += self._plant_actions(d, actor, "hand", 0, hand[0])
            else:
                out.append(_action("pass", actor))
        elif phase == "plant_second":
            hand = d["players"][actor]["hand"]
            if hand:
                out += self._plant_actions(d, actor, "hand", 0, hand[0])
            out.append(_action("pass", actor))
        elif phase == "reveal":
            out.append(_action("reveal", actor))
        elif phase == "trade":
            out.append(_action("end_trade", actor))
            active_refs = self._refs(actor, "hand", d["players"][actor]["hand"]) + self._refs(actor, "revealed", d["zones"]["revealed"])
            # All finite card subsets are representable, including unequal trades and one-way gifts.
            active_sets = list(self._subsets(active_refs))
            for partner in range(len(d["players"])):
                if partner == actor:
                    continue
                partner_refs = self._refs(partner, "hand", d["players"][partner]["hand"])
                partner_sets = list(self._subsets(partner_refs))
                for offered in active_sets:
                    out.append(_action("trade_propose", actor, {"partner": partner, "offered": list(offered), "requested": [], "gift": True}))
                for requested in partner_sets:
                    out.append(_action("trade_propose", actor, {"partner": partner, "offered": [], "requested": list(requested), "gift": True}))
                for offered in active_sets:
                    for requested in partner_sets:
                        if len(offered) + len(requested) > 3:
                            continue
                        out.append(_action("trade_propose", actor, {"partner": partner, "offered": list(offered), "requested": list(requested), "gift": False}))
        elif phase == "trade_response":
            out += [_action("trade_accept", actor), _action("trade_reject", actor)]
        elif phase == "plant_received":
            cards = d["zones"]["pending_received"][actor]
            if cards:
                for i, bean in enumerate(cards):
                    out += self._plant_actions(d, actor, "received", i, bean)
            else:
                out.append(_action("pass", actor))
        elif phase == "draw":
            out.append(_action("draw", actor))
        # Harvesting is an interruption, so duplicate harvest actions never arise above.
        return out

    def _rng_shuffle(self, d, cards):
        seed = d["chance"]["seed"]
        rng = random.Random((seed if seed is not None else 0) + 1000003 * (d["chance"]["draw_index"] + 1))
        rng.shuffle(cards)

    def _draw_one(self, d):
        if not d["zones"]["deck"]:
            return None
        card = d["zones"]["deck"].pop(0)
        d["chance"]["draw_index"] += 1
        if not d["zones"]["deck"]:
            d["depletions"] += 1
            if d["depletions"] < 3:
                cards = d["zones"]["discard"]
                d["zones"]["discard"] = []
                self._rng_shuffle(d, cards)
                d["zones"]["deck"] = cards
        return card

    @staticmethod
    def _payout(bean, count):
        value = 0
        for threshold, coins in METERS[bean]:
            if count >= threshold:
                value = coins
        return value

    def _do_harvest(self, d, player, field, final=False):
        cards = d["players"][player]["fields"][field]
        if not cards or (not final and not self._can_harvest(d, player, field)):
            raise ValueError("illegal harvest")
        coins = self._payout(cards[0], len(cards))
        d["players"][player]["coins"] += coins
        d["zones"]["discard"].extend(cards[coins:])
        d["players"][player]["fields"][field] = []

    def _finish(self, d):
        for p in range(len(d["players"])):
            for f in range(len(d["players"][p]["fields"])):
                if d["players"][p]["fields"][f]:
                    self._do_harvest(d, p, f, True)
        d["terminal"] = True
        d["phase"] = "terminal"
        d["pending"] = None

    def _next_pending_player(self, d):
        n, start = len(d["players"]), d["active_player"]
        for offset in range(n):
            p = (start + offset) % n
            if d["zones"]["pending_received"][p]:
                return p
        return None

    def apply_action(self, state, action):
        legal = set(self.legal_actions(state))
        if action not in legal:
            raise ValueError("illegal action")
        s = copy.deepcopy(state)
        d, a = s.data, action.args
        phase = d["phase"]
        if action.type == "harvest":
            self._do_harvest(d, a["player"], a["field"])
            return s
        if action.type == "plant":
            actor, src, idx = action.actor, a["source"], a["index"]
            if src == "hand":
                card = d["players"][actor]["hand"].pop(idx)
            elif src == "received":
                card = d["zones"]["pending_received"][actor].pop(idx)
            else:
                card = d["zones"]["revealed"].pop(idx)
            d["players"][actor]["fields"][a["field"]].append(card)
            if phase == "plant_first":
                d["phase"] = "plant_second"
            elif phase == "plant_second":
                d["phase"] = "reveal"
            elif phase == "plant_received" and not d["zones"]["pending_received"][actor]:
                nxt = self._next_pending_player(d)
                if nxt is None:
                    if d["depletions"] >= 3:
                        self._finish(d)
                    else:
                        d["phase"], d["current_player"] = "draw", d["active_player"]
                else:
                    d["current_player"] = nxt
        elif action.type == "pass":
            if phase in ("plant_first", "plant_second"):
                d["phase"] = "reveal"
            elif phase == "plant_received":
                nxt = self._next_pending_player(d)
                if nxt is None:
                    if d["depletions"] >= 3: self._finish(d)
                    else: d["phase"], d["current_player"] = "draw", d["active_player"]
                else: d["current_player"] = nxt
        elif action.type == "reveal":
            for _ in range(2):
                card = self._draw_one(d)
                if card is None: break
                d["zones"]["revealed"].append(card)
                if d["depletions"] >= 3: break
            d["phase"] = "trade"
        elif action.type == "trade_propose":
            d["pending"] = {"type": "gift" if a["gift"] else "trade", "actor": action.actor, "partner": a["partner"],
                            "offered": copy.deepcopy(a["offered"]), "requested": copy.deepcopy(a["requested"]), "awaiting_player": a["partner"]}
            d["phase"], d["current_player"] = "trade_response", a["partner"]
        elif action.type == "trade_reject":
            d["pending"] = None
            d["phase"], d["current_player"] = "trade", d["active_player"]
        elif action.type == "trade_accept":
            p = d["pending"]
            received = {p["actor"]: [], p["partner"]: []}
            for refs, recipient in ((p["offered"], p["partner"]), (p["requested"], p["actor"])):
                grouped = {}
                for ref in refs: grouped.setdefault((ref["owner"], ref["zone"]), []).append(ref)
                for (owner, zone), group in grouped.items():
                    target = d["players"][owner]["hand"] if zone == "hand" else d["zones"]["revealed"]
                    for ref in sorted(group, key=lambda x: x["index"], reverse=True):
                        received[recipient].append(target.pop(ref["index"]))
            for recipient, cards in received.items():
                d["zones"]["pending_received"][recipient].extend(reversed(cards))
            d["pending"] = None
            d["phase"], d["current_player"] = "trade", d["active_player"]
        elif action.type == "end_trade":
            d["zones"]["pending_received"][d["active_player"]].extend(d["zones"]["revealed"])
            d["zones"]["revealed"] = []
            d["phase"] = "plant_received"
            nxt = self._next_pending_player(d)
            if nxt is None:
                if d["depletions"] >= 3: self._finish(d)
                else: d["phase"], d["current_player"] = "draw", d["active_player"]
            else: d["current_player"] = nxt
        elif action.type == "draw":
            for _ in range(3):
                card = self._draw_one(d)
                if card is None: break
                d["players"][action.actor]["hand"].append(card)
                if d["depletions"] >= 3: break
            if d["depletions"] >= 3:
                self._finish(d)
            else:
                nxt = (d["active_player"] + 1) % len(d["players"])
                d["active_player"] = d["current_player"] = nxt
                d["phase"] = "plant_first"
        return s

    def is_terminal(self, state):
        return state.data["terminal"]

    def returns(self, state):
        d = state.data
        if not d["terminal"]:
            return [0] * len(d["players"])
        scores = [p["coins"] for p in d["players"]]
        best = max(scores)
        tied = [i for i, x in enumerate(scores) if x == best]
        # Farthest clockwise from the fixed start player wins the tie.
        winner = max(tied, key=lambda p: (p - d["start_player"]) % len(scores))
        return [1 if i == winner else -1 for i in range(len(scores))]

    def action_to_name(self, action):
        return action.type + ":" + str(action.actor) + ":" + action.args_json

    def name_to_action(self, name):
        kind, actor, args = name.split(":", 2)
        return Action(kind, int(actor), args)

    def action_to_data(self, action):
        return {"schema": ACTION_SCHEMA, "data": {"type": action.type, "actor": action.actor, "args": copy.deepcopy(action.args)}}

    def action_from_data(self, payload):
        self._envelope(payload, ACTION_SCHEMA)
        d = payload["data"]
        if set(d) != {"type", "actor", "args"} or d["type"] not in ACTION_TYPES or type(d["actor"]) is not int or not isinstance(d["args"], dict):
            raise ValueError("invalid action data")
        expected = {"plant": {"field", "source", "index", "bean"}, "harvest": {"player", "field"}, "reveal": set(),
                    "trade_propose": {"partner", "offered", "requested", "gift"}, "trade_accept": set(), "trade_reject": set(),
                    "end_trade": set(), "draw": set(), "pass": set()}[d["type"]]
        if set(d["args"]) != expected:
            raise ValueError("invalid action arguments")
        return _action(d["type"], d["actor"], d["args"])

    @staticmethod
    def _envelope(payload, schema):
        if not isinstance(payload, dict) or set(payload) != {"schema", "data"} or payload["schema"] != schema or not isinstance(payload["data"], dict):
            raise ValueError("invalid envelope")

    def state_to_data(self, state):
        return {"schema": STATE_SCHEMA, "data": copy.deepcopy(state.data)}

    def state_from_data(self, payload):
        self._envelope(payload, STATE_SCHEMA)
        d = copy.deepcopy(payload["data"])
        required = {"configuration", "current_player", "active_player", "start_player", "phase", "terminal", "players", "zones", "depletions", "pending", "chance"}
        if set(d) != required:
            raise ValueError("invalid state fields")
        self._validate_state(d)
        return GameState(d)

    def _validate_state(self, d):
        def integer(x): return type(x) is int
        cfg = d["configuration"]
        if not isinstance(cfg, dict) or set(cfg) != {"players", "seed"} or not integer(cfg["players"]) or cfg["players"] not in (4, 5) or (cfg["seed"] is not None and not integer(cfg["seed"])):
            raise ValueError("invalid configuration")
        n = cfg["players"]
        if not all(integer(d[x]) and 0 <= d[x] < n for x in ("current_player", "active_player", "start_player")) or d["phase"] not in PHASES or type(d["terminal"]) is not bool or not integer(d["depletions"]) or d["depletions"] < 0:
            raise ValueError("invalid state scalar")
        if not isinstance(d["players"], list) or len(d["players"]) != n:
            raise ValueError("invalid players")
        for i, p in enumerate(d["players"]):
            if not isinstance(p, dict) or set(p) != {"id", "hand", "fields", "coins"} or p["id"] != i or not integer(p["coins"]) or p["coins"] < 0 or not isinstance(p["fields"], list) or len(p["fields"]) not in (2, 3):
                raise ValueError("invalid player")
            self._bean_list(p["hand"])
            for f in p["fields"]: self._bean_list(f)
        z = d["zones"]
        if not isinstance(z, dict) or set(z) != {"deck", "discard", "revealed", "pending_received", "reserve"} or not isinstance(z["pending_received"], list) or len(z["pending_received"]) != n:
            raise ValueError("invalid zones")
        for key in ("deck", "discard", "revealed", "reserve"): self._bean_list(z[key])
        for cards in z["pending_received"]: self._bean_list(cards)
        chance = d["chance"]
        if not isinstance(chance, dict) or set(chance) != {"seed", "draw_index"} or (chance["seed"] is not None and not integer(chance["seed"])) or not integer(chance["draw_index"]) or chance["draw_index"] < 0:
            raise ValueError("invalid chance")
        if d["pending"] is not None:
            p = d["pending"]
            if not isinstance(p, dict) or set(p) != {"type", "actor", "partner", "offered", "requested", "awaiting_player"} or p["type"] not in ("trade", "gift"):
                raise ValueError("invalid pending")
            if not all(integer(p[x]) and 0 <= p[x] < n for x in ("actor", "partner", "awaiting_player")):
                raise ValueError("invalid pending player")
            for ref in p["offered"] + p["requested"]: self._validate_ref(ref, n)

    @staticmethod
    def _bean_list(value):
        if not isinstance(value, list) or any(not isinstance(x, str) or x not in BEANS for x in value):
            raise ValueError("invalid bean list")

    @staticmethod
    def _validate_ref(ref, n):
        if not isinstance(ref, dict) or set(ref) != {"owner", "zone", "index", "bean"} or type(ref["owner"]) is not int or not 0 <= ref["owner"] < n or ref["zone"] not in ("hand", "revealed") or type(ref["index"]) is not int or ref["index"] < 0 or ref["bean"] not in BEANS:
            raise ValueError("invalid card reference")

    def observation_to_data(self, state, player):
        d = state.data
        if type(player) is not int or not 0 <= player < len(d["players"]): raise ValueError("invalid observer")
        pending = copy.deepcopy(d["pending"])
        data = {"player": player, "current_player": d["current_player"], "active_player": d["active_player"], "phase": d["phase"], "terminal": d["terminal"],
                "own_hand": copy.deepcopy(d["players"][player]["hand"]),
                "opponents": [{"id": p["id"], "hand_size": len(p["hand"])} for p in d["players"] if p["id"] != player],
                "fields": copy.deepcopy([p["fields"] for p in d["players"]]), "coins": [p["coins"] for p in d["players"]],
                "revealed": copy.deepcopy(d["zones"]["revealed"]), "deck_size": len(d["zones"]["deck"]), "discard_size": len(d["zones"]["discard"]), "pending": pending}
        return {"schema": OBS_SCHEMA, "data": data}
