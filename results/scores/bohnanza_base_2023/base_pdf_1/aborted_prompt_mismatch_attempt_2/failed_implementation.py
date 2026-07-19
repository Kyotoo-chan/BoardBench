"""BoardBench implementation of the supplied Bohnanza base-game rulebook.

Only the 4- and 5-player condition requested by the packet is implemented.
"""
from __future__ import annotations

import copy
import json
import random
from typing import Any, Optional


BEANS = ("gartenbohne", "rote_bohne", "augenbohne", "sojabohne",
         "brechbohne", "saubohne", "feuerbohne", "blaue_bohne")
COUNTS = dict(zip(BEANS, (6, 8, 10, 12, 14, 16, 18, 20)))
# Minimum field sizes paying 1, 2, 3 and 4 coins (a missing tier is None).
METERS = {
    "gartenbohne": (2, 3, None, None),
    "rote_bohne": (3, 4, 5, 6),
    "augenbohne": (2, 4, 5, 6),
    "sojabohne": (2, 4, 6, 7),
    "brechbohne": (3, 5, 6, 7),
    "saubohne": (3, 5, 7, 8),
    "feuerbohne": (3, 6, 8, 9),
    "blaue_bohne": (4, 6, 8, 10),
}
PHASES = ("plant_first", "plant_second", "reveal", "trade", "trade_response",
          "plant_received", "draw", "terminal")
ACTION_TYPES = ("plant", "harvest", "reveal", "trade_propose", "trade_accept",
                "trade_reject", "end_trade", "draw", "pass")
STATE_SCHEMA = "boardbench/bohnanza-base-2023/state/1"
ACTION_SCHEMA = "boardbench/bohnanza-base-2023/action/1"
OBS_SCHEMA = "boardbench/bohnanza-base-2023/observation/1"


class Action:
    def __init__(self, type: str, actor: int, args: dict[str, Any]):
        self.type, self.actor, self.args = type, actor, args

    def __eq__(self, other: Any) -> bool:
        return (isinstance(other, Action) and self.type == other.type and
                self.actor == other.actor and self.args == other.args)

    def __repr__(self) -> str:
        return f"Action({self.type!r}, {self.actor!r}, {self.args!r})"


class GameState:
    def __init__(self, configuration: dict[str, Any], current_player: int,
                 active_player: int, start_player: int, phase: str, terminal: bool,
                 players: list[dict[str, Any]], zones: dict[str, Any], depletions: int,
                 pending: Optional[dict[str, Any]], chance: dict[str, Any]):
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
        self.chance = chance


class Game:
    def __init__(self, num_players: Optional[int] = None, seed: Optional[int] = None):
        self.num_players = 4 if num_players is None else num_players
        if type(self.num_players) is not int or self.num_players not in (4, 5):
            raise ValueError("the assigned source condition supports 4 or 5 players")
        if seed is not None and type(seed) is not int:
            raise TypeError("seed must be an integer or None")
        self.seed = seed

    def initial_state(self) -> GameState:
        deck = [bean for bean in BEANS for _ in range(COUNTS[bean])]
        random.Random(self.seed).shuffle(deck)
        players = [{"id": p, "hand": [], "fields": [[], []], "coins": 0}
                   for p in range(self.num_players)]
        # Cards are dealt one at a time; newly dealt cards go behind earlier cards.
        for _ in range(5):
            for player in players:
                player["hand"].append(deck.pop())
        return GameState(
            {"players": self.num_players, "seed": self.seed}, 0, 0, 0,
            "plant_first", False, players,
            {"deck": deck, "discard": [], "revealed": [],
             "pending_received": [[] for _ in players], "reserve": []},
            0, None, {"seed": self.seed, "draw_index": 0})

    def current_player(self, state: GameState) -> int:
        return state.current_player

    @staticmethod
    def _can_harvest(player: dict[str, Any], field: int) -> bool:
        if field < 0 or field >= len(player["fields"]) or not player["fields"][field]:
            return False
        size = len(player["fields"][field])
        return size > 1 or not any(len(other) > 1 for other in player["fields"])

    @staticmethod
    def _plant_fields(player: dict[str, Any], bean: str) -> list[int]:
        return [i for i, field in enumerate(player["fields"])
                if not field or field[0] == bean]

    def _harvest_actions(self, state: GameState) -> list[Action]:
        result = []
        for p, player in enumerate(state.players):
            for f in range(len(player["fields"])):
                if self._can_harvest(player, f):
                    result.append(Action("harvest", p, {"player": p, "field": f}))
        return result

    def legal_actions(self, state: GameState) -> list[Action]:
        if state.terminal or state.phase == "terminal":
            return []
        actions = self._harvest_actions(state)
        p = state.current_player
        active = state.active_player
        phase = state.phase
        if phase in ("plant_first", "plant_second"):
            hand = state.players[active]["hand"]
            if hand:
                bean = hand[0]
                actions += [Action("plant", active, {"field": f, "source": "hand",
                                                       "index": 0, "bean": bean})
                            for f in self._plant_fields(state.players[active], bean)]
            if phase == "plant_second" or not hand:
                actions.append(Action("pass", active, {}))
        elif phase == "reveal":
            actions.append(Action("reveal", active, {}))
        elif phase == "trade":
            actions.append(Action("end_trade", active, {}))
            offered_refs = ([{"owner": active, "zone": "hand", "index": i, "bean": b}
                             for i, b in enumerate(state.players[active]["hand"])] +
                            [{"owner": active, "zone": "revealed", "index": i, "bean": b}
                             for i, b in enumerate(state.zones["revealed"])])
            # Canonical one-for-one and one-card gift choices keep the normal action
            # surface finite. apply_action also validates rulebook-legal unequal bundles.
            for partner in range(len(state.players)):
                if partner == active:
                    continue
                for offer in offered_refs:
                    actions.append(Action("trade_propose", active,
                                          {"partner": partner, "offered": [copy.deepcopy(offer)],
                                           "requested": [], "gift": True}))
                    for i, bean in enumerate(state.players[partner]["hand"]):
                        request = {"owner": partner, "zone": "hand", "index": i, "bean": bean}
                        actions.append(Action("trade_propose", active,
                                              {"partner": partner, "offered": [copy.deepcopy(offer)],
                                               "requested": [request], "gift": False}))
        elif phase == "trade_response":
            actions += [Action("trade_accept", p, {}), Action("trade_reject", p, {})]
        elif phase == "plant_received":
            cards = state.zones["pending_received"][p]
            source = "received"
            if not cards and p == active and state.zones["revealed"]:
                cards = state.zones["revealed"]
                source = "revealed"
            if cards:
                bean = cards[0]
                actions += [Action("plant", p, {"field": f, "source": source,
                                                 "index": 0, "bean": bean})
                            for f in self._plant_fields(state.players[p], bean)]
            else:
                actions.append(Action("pass", p, {}))
        elif phase == "draw":
            actions.append(Action("draw", active, {}))
        return self._dedupe(actions)

    def _dedupe(self, actions: list[Action]) -> list[Action]:
        seen, result = set(), []
        for action in actions:
            key = json.dumps(self.action_to_data(action), sort_keys=True)
            if key not in seen:
                seen.add(key)
                result.append(action)
        return result

    def _coin_value(self, field: list[str]) -> int:
        if not field:
            return 0
        result = 0
        for coins, minimum in enumerate(METERS[field[0]], 1):
            if minimum is not None and len(field) >= minimum:
                result = coins
        return result

    def _do_harvest(self, state: GameState, player: int, field_index: int,
                    final: bool = False) -> None:
        field = state.players[player]["fields"][field_index]
        if not field or (not final and not self._can_harvest(state.players[player], field_index)):
            raise ValueError("illegal harvest")
        coins = self._coin_value(field)
        state.players[player]["coins"] += coins
        state.zones["discard"].extend(field[coins:])
        state.players[player]["fields"][field_index] = []

    def _draw_one(self, state: GameState) -> Optional[str]:
        if not state.zones["deck"]:
            return None
        card = state.zones["deck"].pop()
        if not state.zones["deck"]:
            state.depletions += 1
            if state.depletions < 3 and state.zones["discard"]:
                new_deck = state.zones["discard"]
                state.zones["discard"] = []
                base = 0 if state.chance["seed"] is None else state.chance["seed"]
                random.Random(base + 1000003 * (state.chance["draw_index"] + 1)).shuffle(new_deck)
                state.chance["draw_index"] += 1
                state.zones["deck"] = new_deck
        return card

    def _finalize(self, state: GameState) -> None:
        for p, player in enumerate(state.players):
            for f in range(len(player["fields"])):
                if player["fields"][f]:
                    self._do_harvest(state, p, f, final=True)
        state.phase = "terminal"
        state.terminal = True
        state.current_player = state.active_player
        state.pending = None

    def _next_received_player(self, state: GameState) -> Optional[int]:
        n = len(state.players)
        # Active player first, then clockwise; order within each player's cards is chosen
        # by that player through the sequence of first-card plant actions.
        for offset in range(n):
            p = (state.active_player + offset) % n
            if state.zones["pending_received"][p] or (p == state.active_player and state.zones["revealed"]):
                return p
        return None

    def _advance_after_received(self, state: GameState) -> None:
        nxt = self._next_received_player(state)
        if nxt is not None:
            state.current_player = nxt
            state.phase = "plant_received"
        elif state.depletions >= 3:
            self._finalize(state)
        else:
            state.current_player = state.active_player
            state.phase = "draw"

    @staticmethod
    def _check_ref(state: GameState, ref: dict[str, Any], owner: int,
                   zones: tuple[str, ...]) -> None:
        if set(ref) != {"owner", "zone", "index", "bean"} or ref["owner"] != owner or ref["zone"] not in zones:
            raise ValueError("invalid card reference")
        seq = state.players[owner]["hand"] if ref["zone"] == "hand" else state.zones["revealed"]
        if type(ref["index"]) is not int or ref["index"] < 0 or ref["index"] >= len(seq) or seq[ref["index"]] != ref["bean"]:
            raise ValueError("stale card reference")

    def _validate_proposal(self, state: GameState, action: Action) -> None:
        a = action.args
        if set(a) != {"partner", "offered", "requested", "gift"}:
            raise ValueError("invalid proposal arguments")
        partner = a["partner"]
        if type(partner) is not int or partner < 0 or partner >= len(state.players) or partner == state.active_player:
            raise ValueError("invalid trade partner")
        if type(a["gift"]) is not bool or not isinstance(a["offered"], list) or not isinstance(a["requested"], list):
            raise ValueError("invalid proposal")
        if not a["offered"] and not a["requested"]:
            raise ValueError("empty trade")
        if a["gift"] and (not a["offered"] or a["requested"]):
            raise ValueError("a gift has offered cards only")
        if not a["gift"] and (not a["offered"] or not a["requested"]):
            raise ValueError("a trade exchanges cards in both directions")
        for ref in a["offered"]:
            self._check_ref(state, ref, state.active_player, ("hand", "revealed"))
        for ref in a["requested"]:
            self._check_ref(state, ref, partner, ("hand",))
        keys = [(r["owner"], r["zone"], r["index"]) for r in a["offered"] + a["requested"]]
        if len(keys) != len(set(keys)):
            raise ValueError("a card cannot occur twice in a proposal")

    def apply_action(self, state: GameState, action: Action) -> GameState:
        if not isinstance(state, GameState) or not isinstance(action, Action):
            raise TypeError("expected GameState and Action")
        if state.terminal:
            raise ValueError("game is over")
        state = copy.deepcopy(state)
        t, actor, a = action.type, action.actor, action.args
        if t == "harvest":
            if actor != a.get("player"):
                raise ValueError("harvest actor mismatch")
            self._do_harvest(state, actor, a.get("field", -1))
            return state
        if actor != state.current_player:
            raise ValueError("wrong acting player")
        if t == "plant" and state.phase in ("plant_first", "plant_second", "plant_received"):
            source, index, bean, field = a.get("source"), a.get("index"), a.get("bean"), a.get("field")
            if type(index) is not int or index != 0 or type(field) is not int:
                raise ValueError("cards must be planted from the front of their row")
            if source == "hand" and state.phase in ("plant_first", "plant_second"):
                seq = state.players[actor]["hand"]
            elif source == "received" and state.phase == "plant_received":
                seq = state.zones["pending_received"][actor]
            elif source == "revealed" and state.phase == "plant_received" and actor == state.active_player and not state.zones["pending_received"][actor]:
                seq = state.zones["revealed"]
            else:
                raise ValueError("invalid plant source")
            if not seq or seq[0] != bean or field not in self._plant_fields(state.players[actor], bean):
                raise ValueError("illegal plant")
            seq.pop(0)
            state.players[actor]["fields"][field].append(bean)
            if state.phase == "plant_first":
                state.phase = "plant_second"
            elif state.phase == "plant_received":
                self._advance_after_received(state)
            return state
        if t == "pass":
            if state.phase == "plant_first" and not state.players[actor]["hand"]:
                state.phase = "reveal"
            elif state.phase == "plant_second":
                state.phase = "reveal"
            elif state.phase == "plant_received" and not state.zones["pending_received"][actor] and not (actor == state.active_player and state.zones["revealed"]):
                self._advance_after_received(state)
            else:
                raise ValueError("illegal pass")
            state.current_player = state.active_player if state.phase == "reveal" else state.current_player
            return state
        if t == "reveal" and state.phase == "reveal":
            for _ in range(2):
                card = self._draw_one(state)
                if card is None:
                    break
                state.zones["revealed"].append(card)
                if state.depletions >= 3:
                    break
            state.phase = "trade"
            return state
        if t == "trade_propose" and state.phase == "trade" and actor == state.active_player:
            self._validate_proposal(state, action)
            state.pending = {"type": "gift" if a["gift"] else "trade", "actor": actor,
                             "partner": a["partner"], "offered": copy.deepcopy(a["offered"]),
                             "requested": copy.deepcopy(a["requested"]), "awaiting_player": a["partner"]}
            state.phase = "trade_response"
            state.current_player = a["partner"]
            return state
        if t in ("trade_accept", "trade_reject") and state.phase == "trade_response" and state.pending and actor == state.pending["awaiting_player"]:
            pending = state.pending
            if t == "trade_accept":
                moves = [(r, pending["partner"]) for r in pending["offered"]] + [(r, pending["actor"]) for r in pending["requested"]]
                removals: dict[tuple[int, str], list[tuple[int, str, int]]] = {}
                for ref, recipient in moves:
                    removals.setdefault((ref["owner"], ref["zone"]), []).append((ref["index"], ref["bean"], recipient))
                for (owner, zone), entries in removals.items():
                    seq = state.players[owner]["hand"] if zone == "hand" else state.zones["revealed"]
                    for index, bean, recipient in sorted(entries, reverse=True):
                        if index >= len(seq) or seq[index] != bean:
                            raise ValueError("stale accepted trade")
                        seq.pop(index)
                        # Insert at the front: recipients may choose their planting order.
                        state.zones["pending_received"][recipient].insert(0, bean)
            state.pending = None
            state.phase = "trade"
            state.current_player = state.active_player
            return state
        if t == "end_trade" and state.phase == "trade" and actor == state.active_player:
            self._advance_after_received(state)
            return state
        if t == "draw" and state.phase == "draw" and actor == state.active_player:
            for _ in range(3):
                card = self._draw_one(state)
                if card is None:
                    break
                state.players[actor]["hand"].append(card)
                if state.depletions >= 3:
                    break
            if state.depletions >= 3:
                self._finalize(state)
            else:
                nxt = (state.active_player + 1) % len(state.players)
                state.active_player = nxt
                state.current_player = nxt
                state.phase = "plant_first"
            return state
        raise ValueError("illegal action for current phase")

    def is_terminal(self, state: GameState) -> bool:
        return state.terminal

    def returns(self, state: GameState) -> list[float]:
        if not state.terminal:
            return [0.0] * len(state.players)
        best = max(p["coins"] for p in state.players)
        tied = [p["id"] for p in state.players if p["coins"] == best]
        winner = max(tied, key=lambda p: (p - state.start_player) % len(state.players))
        return [1.0 if p == winner else 0.0 for p in range(len(state.players))]

    def render(self, state: GameState) -> str:
        lines = [f"Bohnanza phase={state.phase} active=P{state.active_player + 1} deck={len(state.zones['deck'])} depletions={state.depletions}"]
        for p in state.players:
            fields = ", ".join("-" if not f else f"{f[0]} x{len(f)}" for f in p["fields"])
            lines.append(f"P{p['id'] + 1}: coins={p['coins']} hand={p['hand']} fields=[{fields}]")
        if state.zones["revealed"]:
            lines.append(f"revealed={state.zones['revealed']}")
        return "\n".join(lines)

    def action_to_name(self, action: Action) -> str:
        return json.dumps(self.action_to_data(action)["data"], ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    def name_to_action(self, name: str) -> Action:
        try:
            data = json.loads(name)
        except Exception as exc:
            raise ValueError("invalid action name") from exc
        return self.action_from_data({"schema": ACTION_SCHEMA, "data": data})

    def state_to_data(self, state: GameState) -> dict[str, Any]:
        if not isinstance(state, GameState):
            raise TypeError("expected GameState")
        return {"schema": STATE_SCHEMA, "data": copy.deepcopy({
            "configuration": state.configuration, "current_player": state.current_player,
            "active_player": state.active_player, "start_player": state.start_player,
            "phase": state.phase, "terminal": state.terminal, "players": state.players,
            "zones": state.zones, "depletions": state.depletions, "pending": state.pending,
            "chance": state.chance})}

    @staticmethod
    def _exact_dict(value: Any, keys: set[str], label: str) -> dict[str, Any]:
        if not isinstance(value, dict) or set(value) != keys:
            raise ValueError(f"invalid {label} fields")
        return value

    @staticmethod
    def _int(value: Any, label: str, minimum: Optional[int] = None) -> int:
        if type(value) is not int or (minimum is not None and value < minimum):
            raise ValueError(f"invalid {label}")
        return value

    @staticmethod
    def _bean_list(value: Any, label: str) -> list[str]:
        if not isinstance(value, list) or any(type(x) is not str or x not in BEANS for x in value):
            raise ValueError(f"invalid {label}")
        return value

    def state_from_data(self, payload: dict[str, Any]) -> GameState:
        self._exact_dict(payload, {"schema", "data"}, "state envelope")
        if payload["schema"] != STATE_SCHEMA:
            raise ValueError("wrong state schema")
        d = self._exact_dict(payload["data"], {"configuration", "current_player", "active_player", "start_player", "phase", "terminal", "players", "zones", "depletions", "pending", "chance"}, "state")
        c = self._exact_dict(d["configuration"], {"players", "seed"}, "configuration")
        n = self._int(c["players"], "player count")
        if n not in (4, 5) or (c["seed"] is not None and type(c["seed"]) is not int):
            raise ValueError("invalid configuration")
        if not isinstance(d["players"], list) or len(d["players"]) != n:
            raise ValueError("invalid players")
        players = []
        for i, raw in enumerate(d["players"]):
            p = self._exact_dict(raw, {"id", "hand", "fields", "coins"}, "player")
            if self._int(p["id"], "player id") != i or not isinstance(p["fields"], list) or len(p["fields"]) not in (2, 3):
                raise ValueError("invalid player record")
            players.append({"id": i, "hand": list(self._bean_list(p["hand"], "hand")),
                            "fields": [list(self._bean_list(f, "field")) for f in p["fields"]],
                            "coins": self._int(p["coins"], "coins", 0)})
            if any(f and any(bean != f[0] for bean in f) for f in players[-1]["fields"]):
                raise ValueError("mixed bean field")
        zones = self._exact_dict(d["zones"], {"deck", "discard", "revealed", "pending_received", "reserve"}, "zones")
        if not isinstance(zones["pending_received"], list) or len(zones["pending_received"]) != n:
            raise ValueError("invalid received zones")
        clean_zones = {k: list(self._bean_list(zones[k], k)) for k in ("deck", "discard", "revealed", "reserve")}
        clean_zones["pending_received"] = [list(self._bean_list(x, "received")) for x in zones["pending_received"]]
        phase = d["phase"]
        if type(phase) is not str or phase not in PHASES or type(d["terminal"]) is not bool:
            raise ValueError("invalid phase or terminal flag")
        indices = [self._int(d[k], k) for k in ("current_player", "active_player", "start_player")]
        if any(x >= n for x in indices):
            raise ValueError("player index out of range")
        chance = self._exact_dict(d["chance"], {"seed", "draw_index"}, "chance")
        if chance["seed"] is not None and type(chance["seed"]) is not int:
            raise ValueError("invalid chance seed")
        clean_chance = {"seed": chance["seed"], "draw_index": self._int(chance["draw_index"], "draw index", 0)}
        pending = self._validate_pending_payload(d["pending"], n)
        return GameState(copy.deepcopy(c), indices[0], indices[1], indices[2], phase,
                         d["terminal"], players, clean_zones,
                         self._int(d["depletions"], "depletions", 0), pending, clean_chance)

    def _validate_pending_payload(self, pending: Any, n: int) -> Optional[dict[str, Any]]:
        if pending is None:
            return None
        p = self._exact_dict(pending, {"type", "actor", "partner", "offered", "requested", "awaiting_player"}, "pending")
        if p["type"] not in ("trade", "gift"):
            raise ValueError("invalid pending type")
        result = {"type": p["type"]}
        for key in ("actor", "partner", "awaiting_player"):
            result[key] = self._int(p[key], key)
            if result[key] >= n:
                raise ValueError("pending player out of range")
        for key, allowed in (("offered", ("hand", "revealed")), ("requested", ("hand",))):
            if not isinstance(p[key], list):
                raise ValueError("invalid pending refs")
            result[key] = []
            for raw in p[key]:
                ref = self._exact_dict(raw, {"owner", "zone", "index", "bean"}, "card ref")
                if ref["zone"] not in allowed or ref["bean"] not in BEANS:
                    raise ValueError("invalid card ref")
                owner = self._int(ref["owner"], "ref owner")
                if owner >= n:
                    raise ValueError("ref owner out of range")
                result[key].append({"owner": owner, "zone": ref["zone"],
                                    "index": self._int(ref["index"], "ref index", 0), "bean": ref["bean"]})
        return result

    def action_to_data(self, action: Action) -> dict[str, Any]:
        if not isinstance(action, Action):
            raise TypeError("expected Action")
        return {"schema": ACTION_SCHEMA, "data": copy.deepcopy({"type": action.type, "actor": action.actor, "args": action.args})}

    def action_from_data(self, payload: dict[str, Any]) -> Action:
        self._exact_dict(payload, {"schema", "data"}, "action envelope")
        if payload["schema"] != ACTION_SCHEMA:
            raise ValueError("wrong action schema")
        d = self._exact_dict(payload["data"], {"type", "actor", "args"}, "action")
        if type(d["type"]) is not str or d["type"] not in ACTION_TYPES or type(d["actor"]) is not int or d["actor"] < 0 or not isinstance(d["args"], dict):
            raise ValueError("invalid action")
        expected = {"plant": {"field", "source", "index", "bean"}, "harvest": {"player", "field"},
                    "reveal": set(), "trade_propose": {"partner", "offered", "requested", "gift"},
                    "trade_accept": set(), "trade_reject": set(), "end_trade": set(),
                    "draw": set(), "pass": set()}[d["type"]]
        if set(d["args"]) != expected:
            raise ValueError("invalid action arguments")
        a = copy.deepcopy(d["args"])
        if d["type"] == "plant":
            if a["source"] not in ("hand", "revealed", "received") or a["bean"] not in BEANS:
                raise ValueError("invalid plant arguments")
            self._int(a["field"], "field", 0); self._int(a["index"], "index", 0)
        elif d["type"] == "harvest":
            self._int(a["player"], "player", 0); self._int(a["field"], "field", 0)
        elif d["type"] == "trade_propose":
            self._int(a["partner"], "partner", 0)
            if type(a["gift"]) is not bool or not isinstance(a["offered"], list) or not isinstance(a["requested"], list):
                raise ValueError("invalid proposal")
            for ref in a["offered"] + a["requested"]:
                self._exact_dict(ref, {"owner", "zone", "index", "bean"}, "card ref")
                self._int(ref["owner"], "owner", 0); self._int(ref["index"], "index", 0)
                if ref["zone"] not in ("hand", "revealed") or ref["bean"] not in BEANS:
                    raise ValueError("invalid card ref")
        return Action(d["type"], d["actor"], a)

    def observation_to_data(self, state: GameState, player: int) -> dict[str, Any]:
        if type(player) is not int or player < 0 or player >= len(state.players):
            raise ValueError("invalid observing player")
        pending = copy.deepcopy(state.pending)
        # A proposal is public between its participants; the references expose bean
        # identities that were explicitly named in the offer.
        data = {"player": player, "current_player": state.current_player,
                "active_player": state.active_player, "phase": state.phase,
                "terminal": state.terminal, "own_hand": copy.deepcopy(state.players[player]["hand"]),
                "opponents": [{"id": p["id"], "hand_size": len(p["hand"])} for p in state.players if p["id"] != player],
                "fields": copy.deepcopy([p["fields"] for p in state.players]),
                "coins": [p["coins"] for p in state.players],
                "revealed": copy.deepcopy(state.zones["revealed"]),
                "deck_size": len(state.zones["deck"]), "discard_size": len(state.zones["discard"]),
                "pending": pending}
        return {"schema": OBS_SCHEMA, "data": data}
