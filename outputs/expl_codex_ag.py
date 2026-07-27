"""Source-faithful, self-contained model of Exploding Kittens (German NSFW 2018)."""
from __future__ import annotations

import copy
import json
import random
from typing import Any, Optional

STATE_SCHEMA = "boardbench/exploding-kittens/state/1"
ACTION_SCHEMA = "boardbench/exploding-kittens/action/1"
OBS_SCHEMA = "boardbench/exploding-kittens/observation/1"
CARDS = (
    "exploding_kitten", "defuse", "attack", "nope", "skip", "favor", "shuffle",
    "see_future", "cat_beard", "cat_cattermelon", "cat_hairy_potato",
    "cat_rainbow", "cat_tacocat",
)
COUNTS = dict(zip(CARDS, (4, 6, 4, 5, 4, 4, 4, 5, 4, 4, 4, 4, 4)))
CAT_CARDS = set(CARDS[8:])
PLAYABLE = set(CARDS[2:])
PHASES = {"play", "reaction", "favor_give", "defuse_reinsert", "terminal"}
ACTION_TYPES = {
    "draw", "play_card", "play_pair", "play_triple", "play_five",
    "give_card", "reinsert", "play_nope", "pass_nope",
}


class Action:
    __slots__ = ("type", "actor", "args")

    def __init__(self, type: str, actor: int, args: tuple[tuple[str, Any], ...] = ()):
        self.type, self.actor, self.args = type, actor, args

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, Action) and
                (self.type, self.actor, self.args) == (other.type, other.actor, other.args))

    def __hash__(self) -> int:
        return hash((self.type, self.actor, self.args))

    def arguments(self) -> dict[str, Any]:
        return {k: list(v) if isinstance(v, tuple) else v for k, v in self.args}


class GameState:
    def __init__(self, configuration: dict, players: list[dict], zones: dict,
                 current_player: int, turns_owed: int, phase: str,
                 pending: Optional[dict], terminal: bool, winner: Optional[int],
                 turn_number: int, chance: dict):
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


def _action(kind: str, actor: int, **args: Any) -> Action:
    return Action(kind, actor, tuple((k, tuple(v) if isinstance(v, list) else v)
                                     for k, v in sorted(args.items())))


class Game:
    def __init__(self, num_players: Optional[int] = None, seed: Optional[int] = None):
        self.num_players = 2 if num_players is None else num_players
        if type(self.num_players) is not int or self.num_players not in (2, 3, 4, 5):
            raise ValueError("num_players must be one of 2, 3, 4, 5")
        if seed is not None and type(seed) is not int:
            raise ValueError("seed must be an integer or None")
        self.seed = seed

    @staticmethod
    def _rng(state: GameState) -> random.Random:
        seed = state.chance["seed"]
        counter = state.chance["counter"]
        state.chance["counter"] += 1
        return random.Random(f"{seed!r}:{counter}")

    def initial_state(self) -> GameState:
        state = GameState(
            {"players": self.num_players, "seed": self.seed, "variant": "base"},
            [{"id": i, "alive": True, "hand": [], "preview": []}
             for i in range(self.num_players)],
            {"deck": [], "discard": [], "box": []}, 0, 1, "play", None,
            False, None, 0, {"seed": self.seed, "counter": 0},
        )
        pool = [c for c in CARDS if c not in ("exploding_kitten", "defuse")
                for _ in range(COUNTS[c])]
        self._rng(state).shuffle(pool)
        for player in state.players:
            player["hand"] = [pool.pop() for _ in range(7)] + ["defuse"]
        defuses = 2 if self.num_players == 2 else COUNTS["defuse"] - self.num_players
        state.zones["box"] = (
            ["exploding_kitten"] * (COUNTS["exploding_kitten"] - self.num_players + 1)
            + ["defuse"] * (COUNTS["defuse"] - self.num_players - defuses)
        )
        state.zones["deck"] = pool + ["exploding_kitten"] * (self.num_players - 1) + ["defuse"] * defuses
        self._rng(state).shuffle(state.zones["deck"])
        return state

    def current_player(self, state: GameState) -> int:
        return state.current_player

    @staticmethod
    def _alive_after(state: GameState, player: int) -> int:
        for step in range(1, len(state.players) + 1):
            candidate = (player + step) % len(state.players)
            if state.players[candidate]["alive"]:
                return candidate
        return player

    def legal_actions(self, state: GameState) -> list[Action]:
        if state.terminal or state.phase == "terminal":
            return []
        p = state.current_player
        if state.phase == "reaction":
            pending = state.pending or {}
            p = pending["responder"]
            result = [_action("pass_nope", p)]
            if "nope" in state.players[p]["hand"]:
                result.append(_action("play_nope", p))
            return result
        if state.phase == "favor_give":
            target = state.pending["target"]
            return [_action("give_card", target, card=c)
                    for c in sorted(set(state.players[target]["hand"]))]
        if state.phase == "defuse_reinsert":
            actor = state.pending["actor"]
            return [_action("reinsert", actor, position=i)
                    for i in range(len(state.zones["deck"]) + 1)]

        hand = state.players[p]["hand"]
        result = [_action("draw", p)]
        for card in sorted(set(hand) & PLAYABLE):
            if card == "favor":
                for target in self._opponents(state, p):
                    result.append(_action("play_card", p, card=card, target=target))
            else:
                result.append(_action("play_card", p, card=card, target=None))
        for card in sorted(set(hand)):
            if hand.count(card) >= 2:
                for target in self._opponents(state, p):
                    result.append(_action("play_pair", p, card=card, target=target))
            if hand.count(card) >= 3:
                for target in self._opponents(state, p):
                    for requested in CARDS:
                        result.append(_action("play_triple", p, card=card, target=target,
                                              requested=requested))
        distinct = sorted(set(hand))
        if len(distinct) >= 5:
            from itertools import combinations
            for cards in combinations(distinct, 5):
                for retrieve in sorted(set(state.zones["discard"])):
                    result.append(_action("play_five", p, cards=list(cards), retrieve=retrieve))
        return result

    @staticmethod
    def _opponents(state: GameState, actor: int) -> list[int]:
        return [p["id"] for p in state.players if p["alive"] and p["id"] != actor]

    def apply_action(self, state: GameState, action: Action) -> GameState:
        legal = self.legal_actions(state)
        if action not in legal:
            raise ValueError("illegal action")
        state = copy.deepcopy(state)
        args = action.arguments()
        if action.type == "draw":
            self._draw(state, action.actor)
        elif action.type in ("play_card", "play_pair", "play_triple", "play_five"):
            self._propose(state, action)
        elif action.type == "play_nope":
            state.players[action.actor]["hand"].remove("nope")
            state.zones["discard"].append("nope")
            state.pending["nope_count"] += 1
            self._reset_responders(state, action.actor)
        elif action.type == "pass_nope":
            remaining = state.pending["remaining_responders"]
            if remaining:
                state.pending["responder"] = remaining.pop(0)
            else:
                self._finish_reaction(state)
        elif action.type == "give_card":
            card = args["card"]
            target, actor = state.pending["target"], state.pending["actor"]
            state.players[target]["hand"].remove(card)
            state.players[actor]["hand"].append(card)
            state.phase, state.pending = "play", None
        elif action.type == "reinsert":
            state.zones["deck"].insert(args["position"], "exploding_kitten")
            state.phase, state.pending = "play", None
            self._finish_turn(state)
        return state

    def _propose(self, state: GameState, action: Action) -> None:
        args = action.arguments()
        if action.type == "play_card":
            cards = [args["card"]]
        elif action.type in ("play_pair", "play_triple"):
            cards = [args["card"]] * (2 if action.type == "play_pair" else 3)
        else:
            cards = list(args["cards"])
        for card in cards:
            state.players[action.actor]["hand"].remove(card)
            state.zones["discard"].append(card)
        state.pending = {
            "type": "reaction", "proposed": self.action_to_data(action)["data"],
            "cards": cards, "nope_count": 0, "responder": action.actor,
            "remaining_responders": [],
        }
        self._reset_responders(state, action.actor)
        if state.pending["remaining_responders"]:
            state.pending["responder"] = state.pending["remaining_responders"].pop(0)
            state.phase = "reaction"
        else:
            self._finish_reaction(state)

    def _reset_responders(self, state: GameState, last: int) -> None:
        responders = []
        cursor = last
        for _ in range(len(state.players) - 1):
            cursor = self._alive_after(state, cursor)
            if cursor != last and cursor not in responders:
                responders.append(cursor)
        state.pending["remaining_responders"] = responders
        if responders:
            state.pending["responder"] = responders.pop(0)

    def _finish_reaction(self, state: GameState) -> None:
        pending = state.pending
        proposed = self.action_from_data({"schema": ACTION_SCHEMA, "data": pending["proposed"]})
        active = pending["nope_count"] % 2 == 0
        state.phase, state.pending = "play", None
        if active:
            self._resolve_proposed(state, proposed)

    def _resolve_proposed(self, state: GameState, action: Action) -> None:
        a = action.arguments()
        if action.type == "play_card":
            card = a["card"]
            if card == "attack":
                state.turns_owed = 1
                self._finish_turn(state)
                state.turns_owed = 2
            elif card == "skip":
                self._finish_turn(state)
            elif card == "favor":
                if state.players[a["target"]]["hand"]:
                    state.phase = "favor_give"
                    state.pending = {"type": "favor", "actor": action.actor, "target": a["target"]}
            elif card == "shuffle":
                self._rng(state).shuffle(state.zones["deck"])
            elif card == "see_future":
                state.players[action.actor]["preview"] = list(reversed(state.zones["deck"][-3:]))
            # Individual cat cards are explicitly powerless.
        elif action.type == "play_pair":
            target = a["target"]
            if state.players[target]["hand"]:
                index = self._rng(state).randrange(len(state.players[target]["hand"]))
                state.players[action.actor]["hand"].append(state.players[target]["hand"].pop(index))
        elif action.type == "play_triple":
            target, requested = a["target"], a["requested"]
            if requested in state.players[target]["hand"]:
                state.players[target]["hand"].remove(requested)
                state.players[action.actor]["hand"].append(requested)
        elif action.type == "play_five":
            state.zones["discard"].remove(a["retrieve"])
            state.players[action.actor]["hand"].append(a["retrieve"])

    def _draw(self, state: GameState, actor: int) -> None:
        state.players[actor]["preview"] = []
        card = state.zones["deck"].pop()
        if card != "exploding_kitten":
            state.players[actor]["hand"].append(card)
            self._finish_turn(state)
        elif "defuse" in state.players[actor]["hand"]:
            state.players[actor]["hand"].remove("defuse")
            state.zones["discard"].append("defuse")
            state.phase = "defuse_reinsert"
            state.pending = {"type": "defuse", "actor": actor, "kitten": "exploding_kitten"}
        else:
            state.players[actor]["alive"] = False
            state.zones["discard"].append("exploding_kitten")
            state.zones["discard"].extend(state.players[actor]["hand"])
            state.players[actor]["hand"] = []
            alive = [p["id"] for p in state.players if p["alive"]]
            if len(alive) == 1:
                state.terminal, state.winner, state.phase = True, alive[0], "terminal"
                state.pending = None
            else:
                state.turns_owed = 1
                state.current_player = self._alive_after(state, actor)
                state.turn_number += 1

    def _finish_turn(self, state: GameState) -> None:
        state.turns_owed -= 1
        state.turn_number += 1
        if state.turns_owed <= 0:
            state.current_player = self._alive_after(state, state.current_player)
            state.turns_owed = 1

    def is_terminal(self, state: GameState) -> bool:
        return state.terminal

    def returns(self, state: GameState) -> list[int]:
        if not state.terminal:
            return [0] * len(state.players)
        return [1 if i == state.winner else -1 for i in range(len(state.players))]

    def render(self, state: GameState) -> str:
        hands = ", ".join(f"P{p['id']}:{len(p['hand'])}{'' if p['alive'] else ' eliminated'}"
                          for p in state.players)
        return (f"phase={state.phase} current=P{state.current_player} "
                f"turns_owed={state.turns_owed} deck={len(state.zones['deck'])} {hands}")

    def action_to_name(self, action: Action) -> str:
        labels = {
            "draw": "Ziehen", "play_card": "Spielen", "play_pair": "Pärchen",
            "play_triple": "Drilling", "play_five": "Fünfling", "give_card": "Karte geben",
            "reinsert": "Exploding Kitten zurücklegen", "play_nope": "NÖ! spielen",
            "pass_nope": "NÖ!-Gelegenheit passen",
        }
        details = json.dumps(action.arguments(), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return f"P{action.actor} {labels[action.type]} {details}"

    def name_to_action(self, name: str) -> Action:
        for kind in sorted(ACTION_TYPES):
            marker = {
                "draw": "Ziehen", "play_card": "Spielen", "play_pair": "Pärchen",
                "play_triple": "Drilling", "play_five": "Fünfling", "give_card": "Karte geben",
                "reinsert": "Exploding Kitten zurücklegen", "play_nope": "NÖ! spielen",
                "pass_nope": "NÖ!-Gelegenheit passen",
            }[kind]
            if name.startswith("P") and f" {marker} " in name:
                prefix, raw = name.split(f" {marker} ", 1)
                actor = int(prefix[1:])
                args = json.loads(raw)
                return _action(kind, actor, **args)
        raise ValueError("invalid action name")

    def action_to_data(self, action: Action) -> dict:
        if not isinstance(action, Action) or action.type not in ACTION_TYPES:
            raise ValueError("invalid action")
        args = action.arguments()
        self._validate_action_fields(action.type, action.actor, args)
        return {"schema": ACTION_SCHEMA,
                "data": {"type": action.type, "actor": action.actor, "args": copy.deepcopy(args)}}

    def action_from_data(self, payload: dict) -> Action:
        root = self._envelope(payload, ACTION_SCHEMA)
        if set(root) != {"type", "actor", "args"}:
            raise ValueError("invalid action fields")
        self._validate_action_fields(root["type"], root["actor"], root["args"])
        return _action(root["type"], root["actor"], **root["args"])

    @staticmethod
    def _validate_action_fields(kind: Any, actor: Any, args: Any) -> None:
        if kind not in ACTION_TYPES or type(actor) is not int or actor < 0 or not isinstance(args, dict):
            raise ValueError("invalid action")
        expected = {
            "draw": {}, "play_card": {"card", "target"}, "play_pair": {"card", "target"},
            "play_triple": {"card", "target", "requested"},
            "play_five": {"cards", "retrieve"}, "give_card": {"card"},
            "reinsert": {"position"}, "play_nope": {}, "pass_nope": {},
        }[kind]
        if set(args) != (expected if isinstance(expected, set) else set()):
            raise ValueError("invalid action arguments")
        for key in ("card", "requested", "retrieve"):
            if key in args and args[key] not in CARDS:
                raise ValueError("invalid card")
        if "target" in args and args["target"] is not None and type(args["target"]) is not int:
            raise ValueError("invalid target")
        if "position" in args and (type(args["position"]) is not int or args["position"] < 0):
            raise ValueError("invalid position")
        if "cards" in args and (not isinstance(args["cards"], list) or len(args["cards"]) != 5
                                or len(set(args["cards"])) != 5 or any(c not in CARDS for c in args["cards"])):
            raise ValueError("invalid five-card combination")

    def state_to_data(self, state: GameState) -> dict:
        data = {field: copy.deepcopy(getattr(state, field)) for field in (
            "configuration", "players", "zones", "current_player", "turns_owed", "phase",
            "pending", "terminal", "winner", "turn_number", "chance")}
        return {"schema": STATE_SCHEMA, "data": data}

    def state_from_data(self, payload: dict) -> GameState:
        data = self._envelope(payload, STATE_SCHEMA)
        required = {"configuration", "players", "zones", "current_player", "turns_owed",
                    "phase", "pending", "terminal", "winner", "turn_number", "chance"}
        if set(data) != required:
            raise ValueError("invalid state fields")
        self._validate_state(data)
        return GameState(**copy.deepcopy(data))

    def _validate_state(self, d: dict) -> None:
        cfg = d["configuration"]
        if not isinstance(cfg, dict) or set(cfg) != {"players", "seed", "variant"}:
            raise ValueError("invalid configuration")
        n = cfg["players"]
        if type(n) is not int or n not in (2, 3, 4, 5) or cfg["variant"] != "base":
            raise ValueError("invalid configuration")
        if cfg["seed"] is not None and type(cfg["seed"]) is not int:
            raise ValueError("invalid seed")
        if not isinstance(d["players"], list) or len(d["players"]) != n:
            raise ValueError("invalid players")
        for i, p in enumerate(d["players"]):
            if (not isinstance(p, dict) or set(p) != {"id", "alive", "hand", "preview"}
                    or p["id"] != i or type(p["alive"]) is not bool):
                raise ValueError("invalid player")
            self._cards(p["hand"]); self._cards(p["preview"])
        z = d["zones"]
        if not isinstance(z, dict) or set(z) != {"deck", "discard", "box"}:
            raise ValueError("invalid zones")
        for value in z.values(): self._cards(value)
        if type(d["current_player"]) is not int or not 0 <= d["current_player"] < n:
            raise ValueError("invalid current player")
        if type(d["turns_owed"]) is not int or d["turns_owed"] < 0 or d["phase"] not in PHASES:
            raise ValueError("invalid phase")
        if type(d["terminal"]) is not bool or (d["winner"] is not None and
                (type(d["winner"]) is not int or not 0 <= d["winner"] < n)):
            raise ValueError("invalid terminal data")
        if type(d["turn_number"]) is not int or d["turn_number"] < 0:
            raise ValueError("invalid turn number")
        chance = d["chance"]
        if (not isinstance(chance, dict) or set(chance) != {"seed", "counter"}
                or chance["seed"] != cfg["seed"] or type(chance["counter"]) is not int
                or chance["counter"] < 0):
            raise ValueError("invalid chance")
        self._validate_pending(d["pending"], n)

    def _validate_pending(self, pending: Any, n: int) -> None:
        if pending is None:
            return
        if not isinstance(pending, dict) or pending.get("type") not in {"reaction", "favor", "defuse"}:
            raise ValueError("invalid pending")
        kind = pending["type"]
        expected = {"reaction": {"type", "proposed", "cards", "nope_count", "responder", "remaining_responders"},
                    "favor": {"type", "actor", "target"},
                    "defuse": {"type", "actor", "kitten"}}[kind]
        if set(pending) != expected:
            raise ValueError("invalid pending fields")
        for key in ("actor", "target", "responder"):
            if key in pending and (type(pending[key]) is not int or not 0 <= pending[key] < n):
                raise ValueError("invalid pending player")
        if kind == "reaction":
            self._cards(pending["cards"])
            if type(pending["nope_count"]) is not int or pending["nope_count"] < 0:
                raise ValueError("invalid nope count")
            if (not isinstance(pending["remaining_responders"], list)
                    or any(type(x) is not int or not 0 <= x < n for x in pending["remaining_responders"])):
                raise ValueError("invalid responders")
            self.action_from_data({"schema": ACTION_SCHEMA, "data": pending["proposed"]})
        if kind == "defuse" and pending["kitten"] != "exploding_kitten":
            raise ValueError("invalid kitten")

    @staticmethod
    def _cards(value: Any) -> None:
        if not isinstance(value, list) or any(c not in CARDS for c in value):
            raise ValueError("invalid cards")

    @staticmethod
    def _envelope(payload: Any, schema: str) -> dict:
        if not isinstance(payload, dict) or set(payload) != {"schema", "data"}:
            raise ValueError("invalid envelope")
        if payload["schema"] != schema or not isinstance(payload["data"], dict):
            raise ValueError("invalid envelope")
        return copy.deepcopy(payload["data"])

    def observation_to_data(self, state: GameState, player: int) -> dict:
        if type(player) is not int or not 0 <= player < len(state.players):
            raise ValueError("invalid player")
        p = state.players[player]
        pending = copy.deepcopy(state.pending)
        data = {
            "player": player, "own_hand": copy.deepcopy(p["hand"]),
            "opponent_hand_sizes": {str(x["id"]): len(x["hand"]) for x in state.players if x["id"] != player},
            "deck_size": len(state.zones["deck"]), "discard": copy.deepcopy(state.zones["discard"]),
            "alive": [x["alive"] for x in state.players], "current_player": state.current_player,
            "turns_owed": state.turns_owed, "phase": state.phase, "pending": pending,
            "preview": copy.deepcopy(p["preview"]), "terminal": state.terminal,
            "winner": state.winner, "turn_number": state.turn_number,
        }
        return {"schema": OBS_SCHEMA, "data": data}
