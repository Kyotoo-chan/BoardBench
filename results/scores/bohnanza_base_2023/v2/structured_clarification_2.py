"""Self-contained Bohnanza Base Game 2023 environment."""
import copy
import itertools
import random
from dataclasses import dataclass
from typing import Any

BEANS = ("gartenbohne", "rote_bohne", "augenbohne", "sojabohne",
         "brechbohne", "saubohne", "feuerbohne", "blaue_bohne")
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
STATE_SCHEMA = "boardbench/bohnanza-base-2023/state/2"
ACTION_SCHEMA = "boardbench/bohnanza-base-2023/action/2"
OBS_SCHEMA = "boardbench/bohnanza-base-2023/observation/2"
PHASES = {"plant_first", "plant_second", "reveal", "trade", "trade_response",
          "plant_received", "draw", "terminal"}
ACTION_TYPES = {"plant", "harvest", "reveal", "trade_propose", "trade_accept",
                "trade_reject", "end_trade", "draw", "pass"}


@dataclass(frozen=True)
class Action:
    type: str
    actor: int
    args: tuple = ()                 # recursively frozen (key, value) pairs


@dataclass
class GameState:
    configuration: dict
    current_player: int
    active_player: int
    start_player: int
    phase: str
    terminal: bool
    winner: int | None
    players: list
    zones: dict
    depletions: int
    pending: dict | None
    turn_number: int
    chance: dict


def _freeze(value):
    if isinstance(value, dict):
        return tuple((k, _freeze(v)) for k, v in sorted(value.items()))
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    return value


def _thaw(value):
    if isinstance(value, tuple):
        if all(isinstance(x, tuple) and len(x) == 2 and isinstance(x[0], str) for x in value):
            return {k: _thaw(v) for k, v in value}
        return [_thaw(v) for v in value]
    return value


class Game:
    def __init__(self, *, num_players=None, seed=None):
        num_players = 3 if num_players is None else num_players
        if type(num_players) is not int or num_players not in (3, 4, 5):
            raise ValueError("num_players must be 3, 4, or 5")
        if seed is not None and type(seed) is not int:
            raise ValueError("seed must be an integer or None")
        self.num_players, self.seed = num_players, seed

    def _chance_rng(self, chance):
        seed = chance["seed"]
        r = random.Random(f"{seed!r}:{chance['counter']}")
        chance["counter"] += 1
        return r

    def initial_state(self):
        chance = {"seed": self.seed, "counter": 0}
        start = self._chance_rng(chance).randrange(self.num_players)
        deck = [b for b in BEANS for _ in range(COUNTS[b])]
        self._chance_rng(chance).shuffle(deck)
        hands = [[] for _ in range(self.num_players)]
        for _ in range(5):
            for hand in hands:
                hand.append(deck.pop())
        field_count = 3 if self.num_players == 3 else 2
        players = [{"id": p, "hand": hands[p], "fields": [[] for _ in range(field_count)], "coins": 0}
                   for p in range(self.num_players)]
        zones = {"deck": deck, "discard": [], "revealed": [],
                 "pending_received": [[] for _ in players], "reserve": []}
        return GameState({"players": self.num_players, "seed": self.seed, "variant": "base_2023"},
                         start, start, start, "plant_first", False, None, players,
                         zones, 0, None, 0, chance)

    def current_player(self, state):
        return state.current_player

    @staticmethod
    def _args(action):
        return _thaw(action.args)

    @staticmethod
    def _action(kind, actor, **args):
        return Action(kind, actor, _freeze(args))

    @staticmethod
    def _plantable(state, player, bean):
        return [i for i, crop in enumerate(state.players[player]["fields"])
                if not crop or crop[0] == bean]

    @staticmethod
    def _harvestable(state, player):
        fields = state.players[player]["fields"]
        has_multi = any(len(crop) > 1 for crop in fields)
        return [i for i, crop in enumerate(fields) if crop and (len(crop) > 1 or not has_multi)]

    def _harvest_actions(self, state):
        return [self._action("harvest", p, player=p, field=i)
                for p in range(state.configuration["players"])
                for i in self._harvestable(state, p)]

    @staticmethod
    def _refs(owner, zone, cards):
        return [{"owner": owner, "zone": zone, "index": i, "bean": b}
                for i, b in enumerate(cards)]

    @staticmethod
    def _nonempty_subsets(items):
        for size in range(1, len(items) + 1):
            for group in itertools.combinations(items, size):
                yield list(group)

    def legal_actions(self, state):
        if state.terminal:
            return []
        actions = self._harvest_actions(state)
        active = state.active_player
        if state.phase == "trade_response":
            q = state.pending["awaiting_player"] if state.pending else state.current_player
            return actions + [self._action("trade_accept", q), self._action("trade_reject", q)]
        if state.phase == "plant_first":
            hand = state.players[active]["hand"]
            if not hand:
                actions.append(self._action("pass", active))
            else:
                bean = hand[0]
                actions += [self._action("plant", active, field=i, source="hand", index=0, bean=bean)
                            for i in self._plantable(state, active, bean)]
        elif state.phase == "plant_second":
            hand = state.players[active]["hand"]
            if hand:
                bean = hand[0]
                actions += [self._action("plant", active, field=i, source="hand", index=0, bean=bean)
                            for i in self._plantable(state, active, bean)]
            actions.append(self._action("pass", active))
        elif state.phase == "reveal":
            actions.append(self._action("reveal", active))
        elif state.phase == "trade":
            offered_refs = self._refs(active, "hand", state.players[active]["hand"]) + self._refs(active, "revealed", state.zones["revealed"])
            for partner in range(state.configuration["players"]):
                if partner == active:
                    continue
                requested_refs = self._refs(partner, "hand", state.players[partner]["hand"])
                for offered in self._nonempty_subsets(offered_refs):
                    actions.append(self._action("trade_propose", active, partner=partner,
                                                offered=offered, requested=[], gift=True))
                    for requested in self._nonempty_subsets(requested_refs):
                        actions.append(self._action("trade_propose", active, partner=partner,
                                                    offered=offered, requested=requested, gift=False))
            actions.append(self._action("end_trade", active))
        elif state.phase == "plant_received":
            for owner, cards in enumerate(state.zones["pending_received"]):
                for index, bean in enumerate(cards):
                    actions += [self._action("plant", owner, field=i, source="received", index=index, bean=bean)
                                for i in self._plantable(state, owner, bean)]
            for index, bean in enumerate(state.zones["revealed"]):
                actions += [self._action("plant", active, field=i, source="revealed", index=index, bean=bean)
                            for i in self._plantable(state, active, bean)]
            if not state.zones["revealed"] and not any(state.zones["pending_received"]):
                if state.depletions >= 3:
                    actions.append(self._action("pass", active))
                else:
                    actions.append(self._action("draw", active))
        elif state.phase == "draw":
            actions.append(self._action("draw", active))
        return actions

    def _harvest(self, state, player, index):
        crop = state.players[player]["fields"][index]
        count = len(crop)
        payout = max((coins for threshold, coins in METERS[crop[0]] if count >= threshold), default=0)
        state.players[player]["coins"] += payout
        state.zones["discard"].extend(crop[:count - payout])
        state.players[player]["fields"][index] = []

    def _draw_one(self, state):
        if not state.zones["deck"]:
            state.depletions += 1
            if state.depletions >= 3:
                return None, True
            state.zones["deck"] = state.zones["discard"]
            state.zones["discard"] = []
            self._chance_rng(state.chance).shuffle(state.zones["deck"])
            if not state.zones["deck"]:
                return None, False
        return state.zones["deck"].pop(), False

    def _finish(self, state):
        for p in range(state.configuration["players"]):
            for i in range(len(state.players[p]["fields"])):
                if state.players[p]["fields"][i]:
                    self._harvest(state, p, i)
        best = max(player["coins"] for player in state.players)
        tied = [p for p, player in enumerate(state.players) if player["coins"] == best]
        state.winner = max(tied, key=lambda p: (p - state.start_player) % state.configuration["players"])
        state.phase, state.terminal, state.pending = "terminal", True, None
        state.current_player = state.winner

    def apply_action(self, state, action):
        if action not in self.legal_actions(state):
            raise ValueError("illegal action")
        state = copy.deepcopy(state)
        args, active = self._args(action), state.active_player
        if action.type == "harvest":
            self._harvest(state, args["player"], args["field"])
        elif action.type == "plant":
            owner, source, index = action.actor, args["source"], args["index"]
            if source == "hand":
                bean = state.players[owner]["hand"].pop(index)
            elif source == "revealed":
                bean = state.zones["revealed"].pop(index)
            else:
                bean = state.zones["pending_received"][owner].pop(index)
            state.players[owner]["fields"][args["field"]].append(bean)
            if state.phase == "plant_first":
                state.phase = "plant_second"
        elif action.type == "pass":
            if state.phase in ("plant_first", "plant_second"):
                state.phase = "reveal"
            elif state.phase == "plant_received":
                self._finish(state)
        elif action.type == "reveal":
            for _ in range(2):
                bean, ended = self._draw_one(state)
                if bean is not None:
                    state.zones["revealed"].append(bean)
                if ended:
                    break
            state.phase = "trade"
        elif action.type == "trade_propose":
            state.pending = {"type": "gift" if args["gift"] else "trade", "actor": active,
                             "partner": args["partner"], "offered": args["offered"],
                             "requested": args["requested"], "awaiting_player": args["partner"]}
            state.phase, state.current_player = "trade_response", args["partner"]
        elif action.type == "trade_reject":
            state.pending, state.phase, state.current_player = None, "trade", active
        elif action.type == "trade_accept":
            proposal = state.pending
            transfers = ((proposal["offered"], proposal["partner"]),
                         (proposal["requested"], proposal["actor"]))
            for refs, recipient in transfers:
                by_zone = {}
                for ref in refs:
                    by_zone.setdefault((ref["owner"], ref["zone"]), []).append(ref)
                for (owner, zone), refs2 in by_zone.items():
                    cards = state.players[owner]["hand"] if zone == "hand" else state.zones["revealed"]
                    moved = []
                    for ref in sorted(refs2, key=lambda x: x["index"], reverse=True):
                        moved.append((ref["index"], cards.pop(ref["index"])))
                    state.zones["pending_received"][recipient].extend(bean for _, bean in sorted(moved))
            state.pending, state.phase, state.current_player = None, "trade", active
        elif action.type == "end_trade":
            state.phase = "plant_received"
        elif action.type == "draw":
            for _ in range(3):
                bean, ended = self._draw_one(state)
                if bean is not None:
                    state.players[active]["hand"].append(bean)
                if ended:
                    self._finish(state)
                    break
            if not state.terminal:
                state.active_player = (active + 1) % state.configuration["players"]
                state.current_player = state.active_player
                state.phase = "plant_first"
                state.turn_number += 1
        return state

    def is_terminal(self, state):
        return state.terminal

    def returns(self, state):
        if not state.terminal:
            return [0.0] * state.configuration["players"]
        return [1.0 if p == state.winner else -1.0 for p in range(state.configuration["players"])]

    def render(self, state):
        lines = [f"phase={state.phase} active={state.active_player} current={state.current_player}"]
        lines += [f"P{p['id']}: coins={p['coins']} hand={p['hand']} fields={p['fields']}" for p in state.players]
        return "\n".join(lines)

    def action_to_name(self, action):
        data = self.action_to_data(action)["data"]
        return f"{data['type']} P{data['actor']} {data['args']}"

    def name_to_action(self, name):
        import ast
        kind, actor, args = name.split(" ", 2)
        if not actor.startswith("P"):
            raise ValueError("invalid action name")
        return self.action_from_data({"schema": ACTION_SCHEMA,
                                      "data": {"type": kind, "actor": int(actor[1:]), "args": ast.literal_eval(args)}})

    def action_to_data(self, action):
        if not isinstance(action, Action):
            raise ValueError("invalid action")
        return {"schema": ACTION_SCHEMA,
                "data": {"type": action.type, "actor": action.actor, "args": copy.deepcopy(_thaw(action.args))}}

    def action_from_data(self, payload):
        if not isinstance(payload, dict) or set(payload) != {"schema", "data"} or payload["schema"] != ACTION_SCHEMA:
            raise ValueError("invalid action envelope")
        data = payload["data"]
        if not isinstance(data, dict) or set(data) != {"type", "actor", "args"}:
            raise ValueError("invalid action data")
        if data["type"] not in ACTION_TYPES or type(data["actor"]) is not int or not isinstance(data["args"], dict):
            raise ValueError("invalid action fields")
        return Action(data["type"], data["actor"], _freeze(copy.deepcopy(data["args"])))

    def state_to_data(self, state):
        data = {name: copy.deepcopy(getattr(state, name)) for name in GameState.__dataclass_fields__}
        return {"schema": STATE_SCHEMA, "data": data}

    def state_from_data(self, payload):
        required = set(GameState.__dataclass_fields__)
        if not isinstance(payload, dict) or set(payload) != {"schema", "data"} or payload["schema"] != STATE_SCHEMA:
            raise ValueError("invalid state envelope")
        data = copy.deepcopy(payload["data"])
        if not isinstance(data, dict) or set(data) != required:
            raise ValueError("invalid state fields")
        if data.get("phase") not in PHASES or type(data.get("terminal")) is not bool:
            raise ValueError("invalid state values")
        return GameState(**data)

    def observation_to_data(self, state, player):
        count = state.configuration["players"]
        if type(player) is not int or not 0 <= player < count:
            raise ValueError("invalid player")
        opponents = [{"id": p, "hand_size": len(state.players[p]["hand"]),
                      "front_card": state.players[p]["hand"][0] if state.players[p]["hand"] else None}
                     for p in range(count) if p != player]
        data = {"player": player, "current_player": state.current_player,
                "active_player": state.active_player, "start_player": state.start_player,
                "phase": state.phase, "terminal": state.terminal, "winner": state.winner,
                "own_hand": copy.deepcopy(state.players[player]["hand"]), "opponents": opponents,
                "fields": copy.deepcopy([p["fields"] for p in state.players]),
                "coins": [p["coins"] for p in state.players],
                "revealed": copy.deepcopy(state.zones["revealed"]),
                "deck_size": len(state.zones["deck"]), "discard_size": len(state.zones["discard"]),
                "pending_received_counts": [len(x) for x in state.zones["pending_received"]],
                "pending": copy.deepcopy(state.pending), "turn_number": state.turn_number}
        return {"schema": OBS_SCHEMA, "data": data}
