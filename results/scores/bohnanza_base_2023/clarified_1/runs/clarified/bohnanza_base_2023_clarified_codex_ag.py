"""Bohnanza base game, transcribed from the supplied German rulebook."""
from __future__ import annotations

import copy
import itertools
import json
import random
from typing import NamedTuple

BEANS = ("gartenbohne", "rote_bohne", "augenbohne", "sojabohne",
         "brechbohne", "saubohne", "feuerbohne", "blaue_bohne")
COUNTS = dict(zip(BEANS, (6, 8, 10, 12, 14, 16, 18, 20)))
THRESHOLDS = {
    "gartenbohne": ((2, 2), (3, 3)),
    "rote_bohne": ((2, 1), (3, 2), (4, 3), (5, 4)),
    "augenbohne": ((2, 1), (4, 2), (5, 3), (6, 4)),
    "sojabohne": ((2, 1), (4, 2), (6, 3), (7, 4)),
    "brechbohne": ((3, 1), (5, 2), (6, 3), (7, 4)),
    "saubohne": ((3, 1), (5, 2), (7, 3), (8, 4)),
    "feuerbohne": ((3, 1), (6, 2), (8, 3), (9, 4)),
    "blaue_bohne": ((4, 1), (6, 2), (8, 3), (10, 4)),
}
PHASES = {"plant_first", "plant_second", "reveal", "trade",
          "trade_response", "plant_received", "draw", "terminal"}
STATE_SCHEMA = "boardbench/bohnanza-base-2023/state/1"
ACTION_SCHEMA = "boardbench/bohnanza-base-2023/action/1"
OBS_SCHEMA = "boardbench/bohnanza-base-2023/observation/1"


class Action(NamedTuple):
    type: str
    actor: int
    args: tuple = ()


class GameState:
    def __init__(self, configuration, current_player, active_player, start_player,
                 phase, terminal, players, zones, depletions=0, pending=None,
                 chance=None):
        self.configuration = configuration
        self.current_player = current_player
        self.active_player = active_player
        self.start_player = start_player
        self.phase = phase
        self.terminal = terminal
        self.players = players
        self.zones = zones
        self.depletions = depletions
        self.pending = pending
        self.chance = chance or {"seed": configuration["seed"], "draw_index": 0}


def _argdict(action):
    return dict(action.args)


def _card_ref(owner, zone, index, bean):
    return (("owner", owner), ("zone", zone), ("index", index), ("bean", bean))


def _refdict(ref):
    return dict(ref)


class Game:
    def __init__(self, num_players=None, seed=None):
        self.num_players = 3 if num_players is None else num_players
        if type(self.num_players) is not int or not 3 <= self.num_players <= 5:
            raise ValueError("num_players must be 3, 4, or 5")
        if seed is not None and type(seed) is not int:
            raise TypeError("seed must be int or None")
        self.seed = seed

    def initial_state(self):
        deck = [bean for bean in BEANS for _ in range(COUNTS[bean])]
        random.Random(self.seed).shuffle(deck)
        field_count = 3 if self.num_players == 3 else 2
        players = [{"id": p, "hand": [],
                    "fields": [[] for _ in range(field_count)], "coins": 0}
                   for p in range(self.num_players)]
        for _ in range(5):
            for player in players:
                player["hand"].append(deck.pop())
        return GameState(
            {"players": self.num_players, "seed": self.seed}, 0, 0, 0,
            "plant_first", False, players,
            {"deck": deck, "discard": [], "revealed": [],
             "pending_received": [[] for _ in players], "reserve": []},
            chance={"seed": self.seed, "draw_index": 0})

    def current_player(self, state):
        return state.current_player

    @staticmethod
    def _can_harvest(state, player, field):
        fields = state.players[player]["fields"]
        if not 0 <= field < len(fields) or not fields[field]:
            return False
        return len(fields[field]) > 1 or not any(len(other) > 1 for other in fields)

    def _harvest_actions(self, state):
        return [Action("harvest", p, (("player", p), ("field", f)))
                for p, player in enumerate(state.players)
                for f in range(len(player["fields"]))
                if self._can_harvest(state, p, f)]

    @staticmethod
    def _plant_actions(state, actor, source, cards):
        result = []
        indices = [0] if source == "hand" and cards else range(len(cards))
        for index in indices:
            bean = cards[index]
            for field, planted in enumerate(state.players[actor]["fields"]):
                if not planted or planted[0] == bean:
                    result.append(Action("plant", actor, (
                        ("field", field), ("source", source),
                        ("index", index), ("bean", bean))))
        return result

    @staticmethod
    def _refs(owner, zone, cards):
        return [_card_ref(owner, zone, i, bean) for i, bean in enumerate(cards)]

    @staticmethod
    def _nonempty_subsets(items):
        for size in range(1, len(items) + 1):
            yield from itertools.combinations(items, size)

    def _trade_actions(self, state):
        actor = state.active_player
        offered_pool = self._refs(actor, "hand", state.players[actor]["hand"])
        offered_pool += self._refs(actor, "revealed", state.zones["revealed"])
        actions = []
        for partner in range(len(state.players)):
            if partner == actor:
                continue
            requested_pool = self._refs(
                partner, "hand", state.players[partner]["hand"])
            for offered in self._nonempty_subsets(offered_pool):
                actions.append(Action("trade_propose", actor, (
                    ("partner", partner), ("offered", offered),
                    ("requested", ()), ("gift", True))))
                for requested in self._nonempty_subsets(requested_pool):
                    actions.append(Action("trade_propose", actor, (
                        ("partner", partner), ("offered", offered),
                        ("requested", requested), ("gift", False))))
        return actions

    def legal_actions(self, state):
        if state.terminal:
            return []
        actions = self._harvest_actions(state)
        p = state.current_player
        if state.phase == "plant_first":
            hand = state.players[state.active_player]["hand"]
            actions += self._plant_actions(state, state.active_player, "hand", hand)
            if not hand:
                actions.append(Action("pass", state.active_player))
        elif state.phase == "plant_second":
            actions += self._plant_actions(
                state, state.active_player, "hand",
                state.players[state.active_player]["hand"])
            actions.append(Action("pass", state.active_player))
        elif state.phase == "reveal":
            actions.append(Action("reveal", state.active_player))
        elif state.phase == "trade":
            actions += self._trade_actions(state)
            actions.append(Action("end_trade", state.active_player))
        elif state.phase == "trade_response":
            actions += [Action("trade_accept", p), Action("trade_reject", p)]
        elif state.phase == "plant_received":
            cards = state.zones["pending_received"][p]
            source = "received"
            if p == state.active_player and not cards and state.zones["revealed"]:
                cards, source = state.zones["revealed"], "revealed"
            actions += self._plant_actions(state, p, source, cards)
            if not cards:
                actions.append(Action("pass", p))
        elif state.phase == "draw":
            actions.append(Action("draw", state.active_player))
        return actions

    def _empty_deck(self, state, phase):
        state.depletions += 1
        if state.depletions >= 3:
            if phase not in {"reveal", "trade", "trade_response", "plant_received"}:
                state.terminal, state.phase = True, "terminal"
            return
        state.zones["deck"] = state.zones["discard"]
        state.zones["discard"] = []
        salt = 0 if state.chance["seed"] is None else state.chance["seed"]
        random.Random(salt + 1000003 * state.chance["draw_index"]).shuffle(
            state.zones["deck"])

    def _draw_one(self, state, destination, phase):
        if not state.zones["deck"]:
            return False
        destination.append(state.zones["deck"].pop())
        state.chance["draw_index"] += 1
        if not state.zones["deck"]:
            self._empty_deck(state, phase)
        return True

    @staticmethod
    def _coins_for(bean, count):
        value = 0
        for threshold, coins in THRESHOLDS[bean]:
            if count >= threshold:
                value = coins
        return value

    def _apply_harvest(self, state, action):
        args = _argdict(action)
        p, f = args["player"], args["field"]
        if action.actor != p or not self._can_harvest(state, p, f):
            raise ValueError("illegal harvest")
        cards = state.players[p]["fields"][f]
        coins = self._coins_for(cards[0], len(cards))
        state.players[p]["coins"] += coins
        state.zones["discard"].extend(cards[:len(cards) - coins])
        state.players[p]["fields"][f] = []

    @staticmethod
    def _remove_refs(state, refs):
        resolved, seen = [], set()
        for ref in refs:
            r = _refdict(ref)
            key = (r["owner"], r["zone"], r["index"])
            if key in seen:
                raise ValueError("duplicate card reference")
            seen.add(key)
            cards = (state.players[r["owner"]]["hand"] if r["zone"] == "hand"
                     else state.zones["revealed"])
            if not 0 <= r["index"] < len(cards) or cards[r["index"]] != r["bean"]:
                raise ValueError("stale card reference")
            resolved.append((r, cards))
        for r, cards in sorted(resolved, key=lambda x: x[0]["index"], reverse=True):
            cards.pop(r["index"])
        return [r["bean"] for r, _ in resolved]

    def _next_received_player(self, state):
        for offset in range(len(state.players)):
            p = (state.active_player + offset) % len(state.players)
            if state.zones["pending_received"][p]:
                state.current_player = p
                return
        if state.zones["revealed"]:
            state.current_player = state.active_player
            return
        if state.depletions >= 3:
            state.terminal, state.phase = True, "terminal"
        else:
            state.phase, state.current_player = "draw", state.active_player

    def apply_action(self, state, action):
        if action not in self.legal_actions(state):
            raise ValueError("illegal action")
        state = copy.deepcopy(state)
        args = _argdict(action)
        if action.type == "harvest":
            self._apply_harvest(state, action)
            return state
        if action.type == "plant":
            p, source, index, bean = (
                action.actor, args["source"], args["index"], args["bean"])
            cards = (state.players[p]["hand"] if source == "hand"
                     else state.zones["revealed"] if source == "revealed"
                     else state.zones["pending_received"][p])
            cards.pop(index)
            state.players[p]["fields"][args["field"]].append(bean)
            if state.phase == "plant_first":
                state.phase = "plant_second"
            elif state.phase == "plant_received" and not cards:
                self._next_received_player(state)
            return state
        if action.type == "pass":
            if state.phase in {"plant_first", "plant_second"}:
                state.phase = "reveal"
            else:
                self._next_received_player(state)
            return state
        if action.type == "reveal":
            for _ in range(2):
                if not self._draw_one(state, state.zones["revealed"], "reveal"):
                    break
                if state.depletions >= 3:
                    break
            state.phase = "trade"
            return state
        if action.type == "trade_propose":
            state.pending = {
                "type": "gift" if args["gift"] else "trade",
                "actor": action.actor, "partner": args["partner"],
                "offered": [dict(r) for r in args["offered"]],
                "requested": [dict(r) for r in args["requested"]],
                "awaiting_player": args["partner"]}
            state.phase, state.current_player = "trade_response", args["partner"]
            return state
        if action.type == "trade_reject":
            state.pending = None
            state.phase, state.current_player = "trade", state.active_player
            return state
        if action.type == "trade_accept":
            pending = state.pending
            offered = self._remove_refs(
                state, [tuple(r.items()) for r in pending["offered"]])
            requested = self._remove_refs(
                state, [tuple(r.items()) for r in pending["requested"]])
            state.zones["pending_received"][pending["partner"]].extend(offered)
            state.zones["pending_received"][pending["actor"]].extend(requested)
            state.pending = None
            state.phase, state.current_player = "trade", state.active_player
            return state
        if action.type == "end_trade":
            state.phase, state.current_player = "plant_received", state.active_player
            self._next_received_player(state)
            return state
        if action.type == "draw":
            for _ in range(3):
                if not self._draw_one(
                        state, state.players[state.active_player]["hand"], "draw"):
                    break
                if state.terminal:
                    return state
            state.active_player = (state.active_player + 1) % len(state.players)
            state.current_player, state.phase = state.active_player, "plant_first"
            return state
        raise ValueError("unknown action")

    def is_terminal(self, state):
        return state.terminal

    def returns(self, state):
        if not state.terminal:
            return [0 for _ in state.players]
        totals = [
            p["coins"] + sum(
                self._coins_for(field[0], len(field)) if field else 0
                for field in p["fields"])
            for p in state.players
        ]
        best = max(totals)
        winners = [p for p, total in enumerate(totals) if total == best]
        winner = (max(winners, key=lambda p: (p - state.start_player) %
                      len(state.players)) if len(winners) > 1 else winners[0])
        return [1 if p == winner else 0 for p in range(len(state.players))]

    def render(self, state):
        lines = [f"Phase: {state.phase}; active/current: "
                 f"{state.active_player}/{state.current_player}; deck: "
                 f"{len(state.zones['deck'])}; depletions: {state.depletions}"]
        for p in state.players:
            lines.append(f"P{p['id']} coins={p['coins']} hand={p['hand']} "
                         f"fields={p['fields']}")
        if state.zones["revealed"]:
            lines.append(f"Revealed: {state.zones['revealed']}")
        return "\n".join(lines)

    def action_to_data(self, action):
        args = _argdict(action)
        if action.type == "trade_propose":
            args = dict(args)
            args["offered"] = [dict(r) for r in args["offered"]]
            args["requested"] = [dict(r) for r in args["requested"]]
        return {"schema": ACTION_SCHEMA, "data": {
            "type": action.type, "actor": action.actor, "args": copy.deepcopy(args)}}

    def action_from_data(self, payload):
        self._check_envelope(payload, ACTION_SCHEMA)
        data = payload["data"]
        if set(data) != {"type", "actor", "args"}:
            raise ValueError("invalid action fields")
        typ, actor, args = data["type"], data["actor"], data["args"]
        types = {"plant", "harvest", "reveal", "trade_propose", "trade_accept",
                 "trade_reject", "end_trade", "draw", "pass"}
        if typ not in types or type(actor) is not int or not isinstance(args, dict):
            raise ValueError("invalid action")
        expected = {
            "plant": {"field", "source", "index", "bean"},
            "harvest": {"player", "field"}, "reveal": set(),
            "trade_propose": {"partner", "offered", "requested", "gift"},
            "trade_accept": set(), "trade_reject": set(), "end_trade": set(),
            "draw": set(), "pass": set()}[typ]
        if set(args) != expected:
            raise ValueError("invalid action arguments")
        if typ == "trade_propose":
            args = dict(args)
            for key in ("offered", "requested"):
                if not isinstance(args[key], list):
                    raise TypeError("card references must be lists")
                args[key] = tuple(self._parse_ref(r) for r in args[key])
        self._validate_action_args(typ, args)
        order = {
            "plant": ("field", "source", "index", "bean"),
            "harvest": ("player", "field"),
            "trade_propose": ("partner", "offered", "requested", "gift"),
        }.get(typ, ())
        return Action(typ, actor, tuple((key, args[key]) for key in order))

    def _validate_action_args(self, typ, args):
        if typ == "plant":
            if (type(args["field"]) is not int or type(args["index"]) is not int
                    or args["source"] not in {"hand", "revealed", "received"}
                    or args["bean"] not in BEANS):
                raise ValueError("invalid plant arguments")
        elif typ == "harvest":
            if type(args["player"]) is not int or type(args["field"]) is not int:
                raise TypeError("invalid harvest arguments")
        elif typ == "trade_propose":
            if (type(args["partner"]) is not int or type(args["gift"]) is not bool
                    or not args["offered"] or (args["gift"] and args["requested"])
                    or (not args["gift"] and not args["requested"])):
                raise ValueError("invalid trade proposal")

    def action_to_name(self, action):
        data = self.action_to_data(action)["data"]
        return data["type"].replace("_", " ").title() + " | " + json.dumps(
            data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    def name_to_action(self, name):
        if not isinstance(name, str) or " | " not in name:
            raise ValueError("invalid action name")
        label, raw = name.split(" | ", 1)
        data = json.loads(raw)
        if label != data.get("type", "").replace("_", " ").title():
            raise ValueError("action label mismatch")
        return self.action_from_data({"schema": ACTION_SCHEMA, "data": data})

    @staticmethod
    def _check_envelope(payload, schema):
        if (not isinstance(payload, dict) or set(payload) != {"schema", "data"}
                or payload.get("schema") != schema
                or not isinstance(payload.get("data"), dict)):
            raise ValueError("invalid envelope")

    @staticmethod
    def _parse_ref(ref):
        if not isinstance(ref, dict) or set(ref) != {"owner", "zone", "index", "bean"}:
            raise ValueError("invalid card reference")
        if (type(ref["owner"]) is not int or type(ref["index"]) is not int
                or ref["zone"] not in {"hand", "revealed"}
                or ref["bean"] not in BEANS):
            raise ValueError("invalid card reference")
        return tuple((key, ref[key]) for key in ("owner", "zone", "index", "bean"))

    def state_to_data(self, state):
        return {"schema": STATE_SCHEMA, "data": copy.deepcopy({
            "configuration": state.configuration,
            "current_player": state.current_player,
            "active_player": state.active_player,
            "start_player": state.start_player, "phase": state.phase,
            "terminal": state.terminal, "players": state.players,
            "zones": state.zones, "depletions": state.depletions,
            "pending": state.pending, "chance": state.chance})}

    def state_from_data(self, payload):
        self._check_envelope(payload, STATE_SCHEMA)
        d = copy.deepcopy(payload["data"])
        required = {"configuration", "current_player", "active_player", "start_player",
                    "phase", "terminal", "players", "zones", "depletions",
                    "pending", "chance"}
        if set(d) != required:
            raise ValueError("invalid state fields")
        self._validate_state(d)
        return GameState(**d)

    def _validate_state(self, d):
        cfg = d["configuration"]
        if (not isinstance(cfg, dict) or set(cfg) != {"players", "seed"}
                or type(cfg["players"]) is not int
                or (cfg["seed"] is not None and type(cfg["seed"]) is not int)):
            raise ValueError("invalid configuration")
        n = cfg["players"]
        for key in ("current_player", "active_player", "start_player"):
            if type(d[key]) is not int or not 0 <= d[key] < n:
                raise ValueError("invalid player index")
        if type(d["depletions"]) is not int or d["depletions"] < 0:
            raise ValueError("invalid depletions")
        if d["phase"] not in PHASES or type(d["terminal"]) is not bool:
            raise ValueError("invalid phase")
        if not isinstance(d["players"], list) or len(d["players"]) != n:
            raise ValueError("invalid players")
        for i, p in enumerate(d["players"]):
            if (not isinstance(p, dict) or set(p) != {"id", "hand", "fields", "coins"}
                    or p["id"] != i or type(p["coins"]) is not int
                    or p["coins"] < 0 or not isinstance(p["fields"], list)):
                raise ValueError("invalid player")
            self._beans(p["hand"])
            for field in p["fields"]:
                self._beans(field)
                if field and len(set(field)) != 1:
                    raise ValueError("mixed bean field")
        z = d["zones"]
        if (not isinstance(z, dict) or set(z) !=
                {"deck", "discard", "revealed", "pending_received", "reserve"}
                or not isinstance(z["pending_received"], list)
                or len(z["pending_received"]) != n):
            raise ValueError("invalid zones")
        for key in ("deck", "discard", "revealed", "reserve"):
            self._beans(z[key])
        for cards in z["pending_received"]:
            self._beans(cards)
        chance = d["chance"]
        if (not isinstance(chance, dict) or set(chance) != {"seed", "draw_index"}
                or (chance["seed"] is not None and type(chance["seed"]) is not int)
                or type(chance["draw_index"]) is not int):
            raise ValueError("invalid chance")
        if d["pending"] is not None:
            self._validate_pending(d["pending"], n)

    @staticmethod
    def _beans(cards):
        if not isinstance(cards, list) or any(bean not in BEANS for bean in cards):
            raise ValueError("invalid bean list")

    def _validate_pending(self, pending, n):
        keys = {"type", "actor", "partner", "offered", "requested", "awaiting_player"}
        if (not isinstance(pending, dict) or set(pending) != keys
                or pending["type"] not in {"trade", "gift"}):
            raise ValueError("invalid pending decision")
        for key in ("actor", "partner", "awaiting_player"):
            if type(pending[key]) is not int or not 0 <= pending[key] < n:
                raise ValueError("invalid pending player")
        for key in ("offered", "requested"):
            if not isinstance(pending[key], list):
                raise ValueError("invalid pending references")
            for ref in pending[key]:
                self._parse_ref(ref)

    def observation_to_data(self, state, player):
        if type(player) is not int or not 0 <= player < len(state.players):
            raise ValueError("invalid observing player")
        pending = copy.deepcopy(state.pending)
        if pending is not None and player not in {pending["actor"], pending["partner"]}:
            pending = {"type": pending["type"], "actor": pending["actor"],
                       "partner": pending["partner"],
                       "offered_count": len(pending["offered"]),
                       "requested_count": len(pending["requested"]),
                       "awaiting_player": pending["awaiting_player"]}
        return {"schema": OBS_SCHEMA, "data": copy.deepcopy({
            "player": player, "current_player": state.current_player,
            "active_player": state.active_player, "phase": state.phase,
            "terminal": state.terminal, "own_hand": state.players[player]["hand"],
            "opponents": [{"id": p["id"], "hand_size": len(p["hand"])}
                          for p in state.players if p["id"] != player],
            "fields": [p["fields"] for p in state.players],
            "coins": [p["coins"] for p in state.players],
            "revealed": state.zones["revealed"],
            "deck_size": len(state.zones["deck"]),
            "discard_size": len(state.zones["discard"]), "pending": pending})}
