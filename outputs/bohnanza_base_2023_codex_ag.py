"""Self-contained Bohnanza base-game environment (German rules, version 5.4)."""
from __future__ import annotations

import copy
import json
import random
from collections import Counter

BEANS = ("gartenbohne", "rote_bohne", "augenbohne", "sojabohne",
         "brechbohne", "saubohne", "feuerbohne", "blaue_bohne")
COUNTS = dict(zip(BEANS, (6, 8, 10, 12, 14, 16, 18, 20)))
METERS = {
    "gartenbohne": ((2, 2), (3, 3)), "rote_bohne": ((2, 1), (3, 2), (4, 3), (5, 4)),
    "augenbohne": ((2, 1), (4, 2), (5, 3), (6, 4)),
    "sojabohne": ((2, 1), (4, 2), (6, 3), (7, 4)),
    "brechbohne": ((3, 1), (5, 2), (6, 3), (7, 4)),
    "saubohne": ((3, 1), (5, 2), (7, 3), (8, 4)),
    "feuerbohne": ((3, 1), (6, 2), (8, 3), (9, 4)),
    "blaue_bohne": ((4, 1), (6, 2), (8, 3), (10, 4)),
}
PHASES = {"plant_first", "plant_second", "reveal", "trade", "trade_response",
          "plant_received", "draw", "terminal"}
STATE_SCHEMA = "boardbench/bohnanza-base-2023/state/2"
ACTION_SCHEMA = "boardbench/bohnanza-base-2023/action/2"
OBS_SCHEMA = "boardbench/bohnanza-base-2023/observation/2"


class Action:
    def __init__(self, typ, actor, args=None):
        self.type, self.actor, self.args = typ, actor, copy.deepcopy(args or {})
    def __eq__(self, other):
        return isinstance(other, Action) and (self.type, self.actor, self.args) == (other.type, other.actor, other.args)
    def __hash__(self):
        return hash((self.type, self.actor, json.dumps(self.args, sort_keys=True)))


class GameState:
    def __init__(self, data):
        self.data = copy.deepcopy(data)
    def __eq__(self, other):
        return isinstance(other, GameState) and self.data == other.data


class Game:
    def __init__(self, num_players=None, seed=None):
        self.num_players = 3 if num_players is None else num_players
        if type(self.num_players) is not int or self.num_players not in (3, 4, 5):
            raise ValueError("Bohnanza supports 3, 4, or 5 players")
        if seed is not None and type(seed) is not int:
            raise ValueError("seed must be an integer or None")
        self.seed = seed

    def initial_state(self):
        rng = random.Random(self.seed)
        deck = [bean for bean in BEANS for _ in range(COUNTS[bean])]
        rng.shuffle(deck)
        start = rng.randrange(self.num_players)
        players = [{"id": i, "hand": [], "fields": [[] for _ in range(3 if self.num_players == 3 else 2)], "coins": 0}
                   for i in range(self.num_players)]
        for p in players:
            for _ in range(5):
                p["hand"].append(deck.pop())
        data = {
            "configuration": {"players": self.num_players, "seed": self.seed, "variant": "base_2023"},
            "current_player": start, "active_player": start, "start_player": start,
            "phase": "plant_first", "terminal": False, "winner": None, "players": players,
            "zones": {"deck": deck, "discard": [], "revealed": [],
                      "pending_received": [[] for _ in players], "reserve": []},
            "depletions": 0, "pending": None, "turn_number": 0,
            "chance": {"seed": self.seed, "counter": 0},
        }
        return GameState(data)

    def current_player(self, state):
        return state.data["current_player"]

    @staticmethod
    def _fits(field, bean):
        return not field or field[0] == bean

    @staticmethod
    def _harvestable(player, fi):
        field = player["fields"][fi]
        return bool(field) and (len(field) > 1 or not any(len(x) > 1 for x in player["fields"]))

    def _plant_actions(self, d, actor, source, bean, index):
        return [Action("plant", actor, {"field": fi, "source": source, "index": index, "bean": bean})
                for fi, field in enumerate(d["players"][actor]["fields"]) if self._fits(field, bean)]

    def legal_actions(self, state):
        d = state.data
        if d["terminal"]:
            return []
        actions = []
        # The rules permit every player to harvest at any time.
        for p in d["players"]:
            for fi in range(len(p["fields"])):
                if self._harvestable(p, fi):
                    actions.append(Action("harvest", p["id"], {"player": p["id"], "field": fi}))
        phase, active = d["phase"], d["active_player"]
        if phase in ("plant_first", "plant_second"):
            hand = d["players"][active]["hand"]
            if not hand:
                actions.append(Action("pass", active))
            elif phase == "plant_first":
                actions += self._plant_actions(d, active, "hand", hand[0], 0)
            else:
                actions.append(Action("pass", active))
                actions += self._plant_actions(d, active, "hand", hand[0], 0)
        elif phase == "reveal":
            actions.append(Action("reveal", active))
        elif phase == "trade":
            actions.append(Action("end_trade", active))
            # All nonempty offered/requested bundles are representable. Generate
            # singleton and full-zone choices; apply_action also validates arbitrary bundles.
            offered = [{"owner": active, "zone": "revealed", "index": i, "bean": b}
                       for i, b in enumerate(d["zones"]["revealed"])]
            offered += [{"owner": active, "zone": "hand", "index": i, "bean": b}
                        for i, b in enumerate(d["players"][active]["hand"])]
            for partner in range(len(d["players"])):
                if partner == active:
                    continue
                requested = [{"owner": partner, "zone": "hand", "index": i, "bean": b}
                             for i, b in enumerate(d["players"][partner]["hand"])]
                for ref in offered:
                    actions.append(Action("trade_propose", active, {"partner": partner, "offered": [ref],
                                                                   "requested": [], "gift": True}))
                    for req in requested:
                        actions.append(Action("trade_propose", active, {"partner": partner, "offered": [ref],
                                                                       "requested": [req], "gift": False}))
                for req in requested:
                    actions.append(Action("trade_propose", active, {"partner": partner, "offered": [],
                                                                   "requested": [req], "gift": True}))
        elif phase == "trade_response":
            who = d["pending"]["awaiting_player"]
            actions += [Action("trade_accept", who), Action("trade_reject", who)]
        elif phase == "plant_received":
            for owner, cards in enumerate(d["zones"]["pending_received"]):
                if cards:
                    actions += self._plant_actions(d, owner, "received", cards[0], 0)
            if d["zones"]["revealed"]:
                actions += self._plant_actions(d, active, "revealed", d["zones"]["revealed"][0], 0)
            if not d["zones"]["revealed"] and not any(d["zones"]["pending_received"]):
                actions.append(Action("pass", active))
        elif phase == "draw":
            actions.append(Action("draw", active))
        return actions

    def _draw_one(self, d, context):
        if not d["zones"]["deck"]:
            return None
        card = d["zones"]["deck"].pop()
        if not d["zones"]["deck"]:
            d["depletions"] += 1
            if d["depletions"] < 3 and d["zones"]["discard"]:
                seed = d["chance"]["seed"]
                rng = random.Random((0 if seed is None else seed) + d["chance"]["counter"] + 1)
                d["chance"]["counter"] += 1
                new = d["zones"]["discard"][:]
                rng.shuffle(new)
                d["zones"]["discard"] = []
                d["zones"]["deck"] = new
        return card

    def _finish(self, d):
        for p in d["players"]:
            for fi in range(len(p["fields"])):
                if p["fields"][fi]:
                    self._do_harvest(d, p["id"], fi)
        best = max(p["coins"] for p in d["players"])
        tied = {p["id"] for p in d["players"] if p["coins"] == best}
        winner = None
        for step in range(len(d["players"])):
            candidate = (d["start_player"] + step) % len(d["players"])
            if candidate in tied:
                winner = candidate
        d.update({"phase": "terminal", "terminal": True, "winner": winner,
                  "current_player": winner, "pending": None})

    def _do_harvest(self, d, pi, fi):
        field = d["players"][pi]["fields"][fi]
        n, bean = len(field), field[0]
        coins = 0
        for threshold, payout in METERS[bean]:
            if n >= threshold:
                coins = payout
        d["players"][pi]["coins"] += coins
        d["zones"]["discard"].extend(field[coins:])
        d["players"][pi]["fields"][fi] = []

    @staticmethod
    def _remove_refs(d, refs):
        removed = []
        by_zone = {}
        for ref in refs:
            key = (ref["owner"], ref["zone"])
            by_zone.setdefault(key, []).append(ref)
        for (owner, zone), group in by_zone.items():
            target = d["zones"]["revealed"] if zone == "revealed" else d["players"][owner]["hand"]
            for ref in sorted(group, key=lambda r: r["index"], reverse=True):
                if ref["index"] >= len(target) or target[ref["index"]] != ref["bean"]:
                    raise ValueError("stale card reference")
                removed.append((ref, target.pop(ref["index"])))
        return removed

    def apply_action(self, state, action):
        legal_data = [self.action_to_data(a) for a in self.legal_actions(state)]
        encoded = self.action_to_data(action)
        # Arbitrary valid trade bundles are accepted even though enumerating their
        # exponential action space would make the environment unusable.
        if encoded not in legal_data and action.type != "trade_propose":
            raise ValueError("illegal action")
        d = copy.deepcopy(state.data)
        typ, active = action.type, d["active_player"]
        if typ == "harvest":
            self._do_harvest(d, action.args["player"], action.args["field"])
        elif typ == "plant":
            source, idx = action.args["source"], action.args["index"]
            if source == "hand":
                card = d["players"][action.actor]["hand"].pop(idx)
            elif source == "revealed":
                card = d["zones"]["revealed"].pop(idx)
            else:
                card = d["zones"]["pending_received"][action.actor].pop(idx)
            d["players"][action.actor]["fields"][action.args["field"]].append(card)
            if d["phase"] == "plant_first":
                d["phase"] = "plant_second"
            elif d["phase"] == "plant_received" and not d["zones"]["revealed"] and not any(d["zones"]["pending_received"]):
                if d["depletions"] >= 3:
                    self._finish(d)
                else:
                    d["current_player"] = active
        elif typ == "pass":
            if d["phase"] in ("plant_first", "plant_second"):
                d["phase"] = "reveal"
            elif d["phase"] == "plant_received":
                if d["depletions"] >= 3:
                    self._finish(d)
                else:
                    d["phase"] = "draw"
        elif typ == "reveal":
            for _ in range(2):
                card = self._draw_one(d, "reveal")
                if card is not None:
                    d["zones"]["revealed"].append(card)
                if d["depletions"] >= 3:
                    break
            d["phase"] = "trade"
        elif typ == "trade_propose":
            self._validate_proposal(d, action)
            d["pending"] = {"type": "gift" if action.args["gift"] else "trade", "actor": active,
                            "partner": action.args["partner"], "offered": copy.deepcopy(action.args["offered"]),
                            "requested": copy.deepcopy(action.args["requested"]),
                            "awaiting_player": action.args["partner"]}
            d["phase"], d["current_player"] = "trade_response", action.args["partner"]
        elif typ == "trade_reject":
            d["pending"] = None
            d["phase"], d["current_player"] = "trade", active
        elif typ == "trade_accept":
            pending = d["pending"]
            offered = self._remove_refs(d, pending["offered"])
            requested = self._remove_refs(d, pending["requested"])
            d["zones"]["pending_received"][pending["partner"]].extend(card for _, card in offered)
            d["zones"]["pending_received"][active].extend(card for _, card in requested)
            d["pending"] = None
            d["phase"], d["current_player"] = "trade", active
        elif typ == "end_trade":
            d["phase"], d["current_player"] = "plant_received", active
        elif typ == "draw":
            for _ in range(3):
                card = self._draw_one(d, "draw")
                if card is None:
                    self._finish(d)
                    break
                d["players"][active]["hand"].append(card)
            if not d["terminal"] and d["depletions"] >= 3:
                self._finish(d)
            if not d["terminal"]:
                nxt = (active + 1) % len(d["players"])
                d["active_player"] = d["current_player"] = nxt
                d["phase"] = "plant_first"
                d["turn_number"] += 1
        return GameState(d)

    def _validate_proposal(self, d, action):
        if d["phase"] != "trade" or action.actor != d["active_player"]:
            raise ValueError("trade may only be proposed by active player")
        a = action.args
        if a["partner"] == action.actor or not (a["offered"] or a["requested"]):
            raise ValueError("invalid trade participants or empty proposal")
        if bool(a["gift"]) != (not a["offered"] or not a["requested"]):
            raise ValueError("gift flag mismatch")
        seen = set()
        for ref in a["offered"] + a["requested"]:
            key = (ref["owner"], ref["zone"], ref["index"])
            if key in seen:
                raise ValueError("duplicate reference")
            seen.add(key)
            expected = action.actor if ref in a["offered"] else a["partner"]
            if ref["owner"] != expected or ref["zone"] not in (("hand", "revealed") if expected == action.actor else ("hand",)):
                raise ValueError("invalid card owner or zone")
            target = d["zones"]["revealed"] if ref["zone"] == "revealed" else d["players"][ref["owner"]]["hand"]
            if type(ref["index"]) is not int or not 0 <= ref["index"] < len(target) or target[ref["index"]] != ref["bean"]:
                raise ValueError("invalid card reference")

    def is_terminal(self, state):
        return state.data["terminal"]

    def returns(self, state):
        if not state.data["terminal"]:
            return [0] * len(state.data["players"])
        return [1 if p["id"] == state.data["winner"] else 0 for p in state.data["players"]]

    def render(self, state):
        d = state.data
        return f"Bohnanza turn={d['turn_number']} phase={d['phase']} active=P{d['active_player']} " + \
               " ".join(f"P{p['id']} coins={p['coins']} hand={len(p['hand'])} fields={p['fields']}" for p in d["players"])

    def action_to_name(self, action):
        return f"{action.type} P{action.actor} {json.dumps(action.args, ensure_ascii=False, sort_keys=True, separators=(',', ':'))}"

    def name_to_action(self, name):
        typ, actor, raw = name.split(" ", 2)
        return Action(typ, int(actor[1:]), json.loads(raw))

    def action_to_data(self, action):
        if not isinstance(action, Action):
            raise ValueError("expected Action")
        return {"schema": ACTION_SCHEMA, "data": {"type": action.type, "actor": action.actor, "args": copy.deepcopy(action.args)}}

    def action_from_data(self, payload):
        self._envelope(payload, ACTION_SCHEMA)
        d = payload["data"]
        if set(d) != {"type", "actor", "args"} or d["type"] not in {"plant", "harvest", "reveal", "trade_propose",
                "trade_accept", "trade_reject", "end_trade", "draw", "pass"} or type(d["actor"]) is not int or not isinstance(d["args"], dict):
            raise ValueError("invalid action payload")
        return Action(d["type"], d["actor"], d["args"])

    @staticmethod
    def _envelope(payload, schema):
        if not isinstance(payload, dict) or set(payload) != {"schema", "data"} or payload["schema"] != schema or not isinstance(payload["data"], dict):
            raise ValueError("invalid canonical envelope")

    def state_to_data(self, state):
        return {"schema": STATE_SCHEMA, "data": copy.deepcopy(state.data)}

    def state_from_data(self, payload):
        self._envelope(payload, STATE_SCHEMA)
        d = payload["data"]
        required = {"configuration", "current_player", "active_player", "start_player", "phase", "terminal",
                    "winner", "players", "zones", "depletions", "pending", "turn_number", "chance"}
        if set(d) != required:
            raise ValueError("invalid state fields")
        n = d["configuration"].get("players") if isinstance(d["configuration"], dict) else None
        if n not in (3, 4, 5) or len(d["players"]) != n or d["phase"] not in PHASES:
            raise ValueError("invalid state configuration")
        if set(d["zones"]) != {"deck", "discard", "revealed", "pending_received", "reserve"}:
            raise ValueError("invalid zones")
        all_cards = []
        for p in d["players"]:
            all_cards += p["hand"]
            for f in p["fields"]: all_cards += f
        for z in ("deck", "discard", "revealed", "reserve"): all_cards += d["zones"][z]
        for z in d["zones"]["pending_received"]: all_cards += z
        if any(x not in BEANS for x in all_cards) or len(all_cards) + sum(p["coins"] for p in d["players"]) != 104:
            raise ValueError("invalid physical inventory")
        return GameState(d)

    def observation_to_data(self, state, player):
        d = state.data
        if type(player) is not int or not 0 <= player < len(d["players"]):
            raise ValueError("invalid player")
        data = {
            "player": player, "current_player": d["current_player"], "active_player": d["active_player"],
            "start_player": d["start_player"], "phase": d["phase"], "terminal": d["terminal"],
            "winner": d["winner"], "own_hand": copy.deepcopy(d["players"][player]["hand"]),
            "opponents": [{"id": p["id"], "hand_size": len(p["hand"]), "front_card": p["hand"][0] if p["hand"] else None}
                          for p in d["players"] if p["id"] != player],
            "fields": copy.deepcopy([p["fields"] for p in d["players"]]),
            "coins": [p["coins"] for p in d["players"]], "revealed": copy.deepcopy(d["zones"]["revealed"]),
            "deck_size": len(d["zones"]["deck"]), "discard_size": len(d["zones"]["discard"]),
            "pending_received_counts": [len(x) for x in d["zones"]["pending_received"]],
            "pending": copy.deepcopy(d["pending"]), "turn_number": d["turn_number"],
        }
        return {"schema": OBS_SCHEMA, "data": data}
