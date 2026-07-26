"""Wizard (German rules, version 1.0) as a small deterministic game engine."""
from dataclasses import dataclass
import copy
import random
from typing import Any

SUITS = ("menschen_blau", "elfen_gruen", "zwerge_rot", "riesen_gelb")
SPECIALS = ("zauberer", "narr")
STATE_SCHEMA = "boardbench/wizard/state/1"
ACTION_SCHEMA = "boardbench/wizard/action/1"
OBS_SCHEMA = "boardbench/wizard/observation/1"


def _cards() -> list[str]:
    return [f"{s}:{r}" for s in SUITS for r in range(1, 14)] + ["zauberer"] * 4 + ["narr"] * 4


def _suit(card: str) -> str | None:
    return card.split(":", 1)[0] if ":" in card else None


def _rank(card: str) -> int:
    return int(card.split(":", 1)[1])


def _next(player: int, count: int) -> int:
    return (player + 1) % count


@dataclass(frozen=True)
class Action:
    type: str
    actor: int
    args: tuple[tuple[str, Any], ...]

    def value(self, key: str) -> Any:
        return dict(self.args)[key]


@dataclass
class GameState:
    configuration: dict
    round_number: int
    max_round: int
    dealer: int
    leader: int
    current_player: int
    phase: str
    terminal: bool
    trump_suit: str | None
    led_suit: str | None
    players: list[dict]
    zones: dict
    pending: dict | None
    chance: dict


class Game:
    def __init__(self, num_players: int | None = None, seed: int | None = None):
        self.num_players = 4 if num_players is None else num_players
        if self.num_players not in (3, 4, 5, 6):
            raise ValueError("num_players must be one of 3, 4, 5, 6")
        if seed is not None and (not isinstance(seed, int) or isinstance(seed, bool)):
            raise ValueError("seed must be an integer or None")
        self.seed = seed

    def _rng(self, index: int) -> random.Random:
        # Each shuffle is independently reproducible from canonical chance state.
        return random.Random(f"{self.seed!r}:{index}")

    def _deal_round(self, state: GameState) -> None:
        deck = _cards()
        self._rng(state.chance["shuffle_index"]).shuffle(deck)
        state.chance["shuffle_index"] += 1
        for p in state.players:
            p["hand"] = []
            p["prediction"] = None
            p["tricks_won"] = 0
        for _ in range(state.round_number):
            for p in state.players:
                p["hand"].append(deck.pop())
        state.zones = {
            "deck": deck, "revealed_trump": None, "trick": [],
            "completed_tricks": [], "reserve": [],
        }
        state.trump_suit = None
        state.led_suit = None
        state.leader = _next(state.dealer, self.num_players)
        if state.round_number < state.max_round:
            card = state.zones["deck"].pop()
            state.zones["revealed_trump"] = card
            if card == "zauberer":
                state.phase = "choose_trump"
                state.current_player = state.dealer
                state.pending = {"type": "trump_choice", "player": state.dealer}
                return
            if card != "narr":
                state.trump_suit = _suit(card)
        state.phase = "predict"
        state.current_player = _next(state.dealer, self.num_players)
        state.pending = None

    def initial_state(self) -> GameState:
        rng = self._rng(-1)
        dealer = rng.randrange(self.num_players)
        state = GameState(
            {"players": self.num_players, "seed": self.seed, "variant": "base"},
            1, 60 // self.num_players, dealer, _next(dealer, self.num_players),
            _next(dealer, self.num_players), "predict", False, None, None,
            [{"id": i, "hand": [], "prediction": None, "tricks_won": 0, "score": 0}
             for i in range(self.num_players)],
            {}, None, {"seed": self.seed, "shuffle_index": 0},
        )
        self._deal_round(state)
        return state

    def current_player(self, state: GameState) -> int:
        return state.current_player

    def legal_actions(self, state: GameState) -> list[Action]:
        if state.terminal or state.phase == "terminal":
            return []
        actor = state.current_player
        if state.phase == "choose_trump":
            return [Action("choose_trump", actor, (("suit", s),)) for s in SUITS]
        if state.phase == "predict":
            return [Action("predict", actor, (("tricks", n),))
                    for n in range(state.round_number + 1)]
        if state.phase != "play":
            return []
        hand = state.players[actor]["hand"]
        if not state.zones["trick"] or state.led_suit is None:
            legal = hand
        else:
            matching = [c for c in hand if _suit(c) == state.led_suit]
            legal = [c for c in hand if c in SPECIALS or not matching or _suit(c) == state.led_suit]
        # Identical special copies produce the same game transition.
        return [Action("play_card", actor, (("card", card),)) for card in dict.fromkeys(legal)]

    def apply_action(self, state: GameState, action: Action) -> GameState:
        if action not in self.legal_actions(state):
            raise ValueError("illegal action")
        state = copy.deepcopy(state)
        actor = action.actor
        if action.type == "choose_trump":
            state.trump_suit = action.value("suit")
            state.pending = None
            state.phase = "predict"
            state.current_player = _next(state.dealer, self.num_players)
        elif action.type == "predict":
            state.players[actor]["prediction"] = action.value("tricks")
            nxt = _next(actor, self.num_players)
            if nxt == _next(state.dealer, self.num_players):
                state.phase = "play"
                state.current_player = state.leader
            else:
                state.current_player = nxt
        else:
            card = action.value("card")
            state.players[actor]["hand"].remove(card)
            state.zones["trick"].append({"player": actor, "card": card})
            if state.led_suit is None and _suit(card) is not None:
                state.led_suit = _suit(card)
            if len(state.zones["trick"]) < self.num_players:
                state.current_player = _next(actor, self.num_players)
            else:
                self._finish_trick(state)
        return state

    def _finish_trick(self, state: GameState) -> None:
        trick = state.zones["trick"]
        wizard = next((e for e in trick if e["card"] == "zauberer"), None)
        if wizard:
            winner = wizard["player"]
        else:
            ordinary = [e for e in trick if _suit(e["card"]) is not None]
            trumps = [e for e in ordinary if _suit(e["card"]) == state.trump_suit]
            candidates = trumps or [e for e in ordinary if _suit(e["card"]) == state.led_suit]
            winner = max(candidates, key=lambda e: _rank(e["card"]))["player"] if candidates else trick[0]["player"]
        state.players[winner]["tricks_won"] += 1
        state.zones["completed_tricks"].append(
            {"winner": winner, "cards": [e["card"] for e in trick]})
        state.zones["trick"] = []
        state.led_suit = None
        state.leader = winner
        state.current_player = winner
        if not any(p["hand"] for p in state.players):
            for p in state.players:
                prediction, won = p["prediction"], p["tricks_won"]
                p["score"] += 20 + 10 * won if prediction == won else -10 * abs(prediction - won)
            if state.round_number == state.max_round:
                state.phase, state.terminal, state.pending = "terminal", True, None
            else:
                state.round_number += 1
                state.dealer = _next(state.dealer, self.num_players)
                self._deal_round(state)

    def is_terminal(self, state: GameState) -> bool:
        return state.terminal

    def returns(self, state: GameState) -> list[int]:
        return [p["score"] for p in state.players] if state.terminal else [0] * len(state.players)

    def render(self, state: GameState) -> str:
        scores = ", ".join(f"P{p['id']}={p['score']}" for p in state.players)
        return f"Wizard round {state.round_number}/{state.max_round}, {state.phase}, current P{state.current_player}; {scores}"

    def action_to_name(self, action: Action) -> str:
        if action.type == "choose_trump":
            return f"Trumpffarbe wählen: {action.value('suit')} (P{action.actor})"
        if action.type == "predict":
            return f"Vorhersage: {action.value('tricks')} Stiche (P{action.actor})"
        return f"Karte spielen: {action.value('card')} (P{action.actor})"

    def name_to_action(self, name: str) -> Action:
        if name.startswith("Trumpffarbe wählen: ") and " (P" in name:
            body, actor = name[20:].rsplit(" (P", 1)
            return Action("choose_trump", int(actor[:-1]), (("suit", body),))
        if name.startswith("Vorhersage: ") and " Stiche (P" in name:
            n, actor = name[12:].split(" Stiche (P", 1)
            return Action("predict", int(actor[:-1]), (("tricks", int(n)),))
        if name.startswith("Karte spielen: ") and " (P" in name:
            card, actor = name[15:].rsplit(" (P", 1)
            return Action("play_card", int(actor[:-1]), (("card", card),))
        raise ValueError("invalid action name")

    def state_to_data(self, state: GameState) -> dict:
        return {"schema": STATE_SCHEMA, "data": copy.deepcopy(state.__dict__)}

    def state_from_data(self, payload: dict) -> GameState:
        data = self._validate_envelope(payload, STATE_SCHEMA)
        required = set(GameState.__dataclass_fields__)
        if set(data) != required:
            raise ValueError("invalid state fields")
        self._validate_state(data)
        return GameState(**copy.deepcopy(data))

    def action_to_data(self, action: Action) -> dict:
        args = dict(action.args)
        return {"schema": ACTION_SCHEMA, "data":
                {"type": action.type, "actor": action.actor, "args": copy.deepcopy(args)}}

    def action_from_data(self, payload: dict) -> Action:
        data = self._validate_envelope(payload, ACTION_SCHEMA)
        if set(data) != {"type", "actor", "args"} or type(data["actor"]) is not int or not isinstance(data["args"], dict):
            raise ValueError("invalid action fields")
        typ, args = data["type"], data["args"]
        expected = {"choose_trump": {"suit"}, "predict": {"tricks"},
                    "play_card": {"card"}}
        if typ not in expected or set(args) != expected[typ]:
            raise ValueError("invalid action type or arguments")
        if typ == "choose_trump" and args["suit"] not in SUITS:
            raise ValueError("invalid suit")
        if typ == "predict" and (type(args["tricks"]) is not int or args["tricks"] < 0):
            raise ValueError("invalid prediction")
        if typ == "play_card" and not self._valid_card(args["card"]):
            raise ValueError("invalid card")
        return Action(typ, data["actor"], tuple(args.items()))

    def observation_to_data(self, state: GameState, player: int) -> dict:
        if type(player) is not int or not 0 <= player < len(state.players):
            raise ValueError("invalid player")
        d = {
            "player": player, "round_number": state.round_number, "max_round": state.max_round,
            "dealer": state.dealer, "leader": state.leader, "current_player": state.current_player,
            "phase": state.phase, "terminal": state.terminal, "trump_suit": state.trump_suit,
            "led_suit": state.led_suit, "own_hand": copy.deepcopy(state.players[player]["hand"]),
            "players": [{"id": p["id"], "hand_size": len(p["hand"]), "prediction": p["prediction"],
                         "tricks_won": p["tricks_won"], "score": p["score"]} for p in state.players],
            "revealed_trump": state.zones["revealed_trump"],
            "trick": copy.deepcopy(state.zones["trick"]),
            "completed_trick_count": len(state.zones["completed_tricks"]),
            "deck_size": len(state.zones["deck"]),
        }
        return {"schema": OBS_SCHEMA, "data": d}

    @staticmethod
    def _validate_envelope(payload: dict, schema: str) -> dict:
        if not isinstance(payload, dict) or set(payload) != {"schema", "data"} or payload["schema"] != schema or not isinstance(payload["data"], dict):
            raise ValueError("invalid canonical envelope")
        return payload["data"]

    @staticmethod
    def _valid_card(card: Any) -> bool:
        if card in SPECIALS:
            return True
        if not isinstance(card, str) or ":" not in card:
            return False
        suit, rank = card.split(":", 1)
        return suit in SUITS and rank.isdigit() and 1 <= int(rank) <= 13

    def _validate_state(self, d: dict) -> None:
        cfg = d["configuration"]
        if not isinstance(cfg, dict) or set(cfg) != {"players", "seed", "variant"} or cfg["players"] not in (3, 4, 5, 6) or cfg["variant"] != "base":
            raise ValueError("invalid configuration")
        if cfg["seed"] is not None and type(cfg["seed"]) is not int:
            raise ValueError("invalid seed")
        ints = ("round_number", "max_round", "dealer", "leader", "current_player")
        if any(type(d[k]) is not int for k in ints) or type(d["terminal"]) is not bool:
            raise ValueError("invalid state scalar")
        if d["phase"] not in ("choose_trump", "predict", "play", "terminal"):
            raise ValueError("invalid phase")
        if d["trump_suit"] not in SUITS + (None,) or d["led_suit"] not in SUITS + (None,):
            raise ValueError("invalid suit")
        if not isinstance(d["players"], list) or len(d["players"]) != cfg["players"]:
            raise ValueError("invalid players")
        for p in d["players"]:
            if not isinstance(p, dict) or set(p) != {"id", "hand", "prediction", "tricks_won", "score"}:
                raise ValueError("invalid player")
            if any(type(p[k]) is not int for k in ("id", "tricks_won", "score")) or (p["prediction"] is not None and type(p["prediction"]) is not int):
                raise ValueError("invalid player scalar")
            if not isinstance(p["hand"], list) or not all(self._valid_card(c) for c in p["hand"]):
                raise ValueError("invalid hand")
        z = d["zones"]
        if not isinstance(z, dict) or set(z) != {"deck", "revealed_trump", "trick", "completed_tricks", "reserve"}:
            raise ValueError("invalid zones")
        for key in ("deck", "reserve"):
            if not isinstance(z[key], list) or not all(self._valid_card(c) for c in z[key]):
                raise ValueError("invalid card zone")
        if z["revealed_trump"] is not None and not self._valid_card(z["revealed_trump"]):
            raise ValueError("invalid revealed card")
        if not isinstance(z["trick"], list) or any(not isinstance(e, dict) or set(e) != {"player", "card"} or type(e["player"]) is not int or not self._valid_card(e["card"]) for e in z["trick"]):
            raise ValueError("invalid trick")
        if not isinstance(z["completed_tricks"], list) or any(not isinstance(e, dict) or set(e) != {"winner", "cards"} or type(e["winner"]) is not int or not isinstance(e["cards"], list) or not all(self._valid_card(c) for c in e["cards"]) for e in z["completed_tricks"]):
            raise ValueError("invalid completed tricks")
        pending = d["pending"]
        if pending is not None and (not isinstance(pending, dict) or set(pending) != {"type", "player"} or pending["type"] != "trump_choice" or type(pending["player"]) is not int):
            raise ValueError("invalid pending")
        chance = d["chance"]
        if not isinstance(chance, dict) or set(chance) != {"seed", "shuffle_index"} or (chance["seed"] is not None and type(chance["seed"]) is not int) or type(chance["shuffle_index"]) is not int:
            raise ValueError("invalid chance")
