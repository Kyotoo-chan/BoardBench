"""Wizard (German rulebook, version 1.0), as a small deterministic game engine."""

from __future__ import annotations

import copy
import random
from typing import NamedTuple


SUITS = ("menschen_blau", "elfen_gruen", "zwerge_rot", "riesen_gelb")
SPECIALS = ("zauberer", "narr")
PHASES = ("choose_trump", "predict", "play", "terminal")
STATE_SCHEMA = "boardbench/wizard/state/1"
ACTION_SCHEMA = "boardbench/wizard/action/1"
OBS_SCHEMA = "boardbench/wizard/observation/1"


class Action(NamedTuple):
    type: str
    actor: int
    arg: object


class GameState:
    def __init__(self, configuration, round_number, max_round, dealer, leader,
                 current_player, phase, terminal, trump_suit, led_suit, players,
                 zones, pending, chance):
        self.configuration = configuration
        self.round_number = round_number
        self.max_round = max_round
        self.dealer = dealer
        self.leader = leader
        self.current_player = current_player
        self.phase = phase
        self.terminal = terminal
        self.trump_suit = trump_suit
        self.led_suit = led_suit
        self.players = players
        self.zones = zones
        self.pending = pending
        self.chance = chance


def _deck():
    return [f"{s}:{r}" for s in SUITS for r in range(1, 14)] + ["zauberer"] * 4 + ["narr"] * 4


def _card(card):
    if card in SPECIALS:
        return card, None
    suit, sep, rank = card.rpartition(":")
    if not sep or suit not in SUITS:
        raise ValueError("invalid card id")
    try:
        value = int(rank)
    except (TypeError, ValueError):
        raise ValueError("invalid card id") from None
    if not 1 <= value <= 13 or str(value) != rank:
        raise ValueError("invalid card id")
    return suit, value


def _strict_int(value, label="value"):
    if type(value) is not int:
        raise ValueError(f"{label} must be an integer")
    return value


class Game:
    def __init__(self, num_players=None, seed=None):
        count = 4 if num_players is None else _strict_int(num_players, "num_players")
        if count not in (3, 4, 5, 6):
            raise ValueError("num_players must be 3, 4, 5, or 6")
        if seed is not None:
            _strict_int(seed, "seed")
        self.num_players = count
        self.seed = seed

    def _shuffle(self, index):
        # Recreate shuffle n from the two canonical chance fields.
        rng = random.Random(0 if self.seed is None else self.seed)
        cards = None
        for _ in range(index + 1):
            cards = _deck()
            rng.shuffle(cards)
        return cards

    def _start_round(self, state):
        n, rnd = self.num_players, state.round_number
        cards = self._shuffle(state.chance["shuffle_index"])
        state.chance["shuffle_index"] += 1
        state.players = [
            {"id": i, "hand": [], "prediction": None, "tricks_won": 0,
             "score": state.players[i]["score"]}
            for i in range(n)
        ]
        cursor = (state.dealer + 1) % n
        for _ in range(rnd):
            for offset in range(n):
                state.players[(cursor + offset) % n]["hand"].append(cards.pop())
        revealed = cards.pop() if cards else None
        state.zones = {
            "deck": cards, "revealed_trump": revealed, "trick": [],
            "completed_tricks": [], "reserve": [],
        }
        state.leader = cursor
        state.led_suit = None
        state.pending = None
        if revealed == "zauberer":
            state.phase = "choose_trump"
            state.current_player = state.dealer
            state.trump_suit = None
            state.pending = {"type": "trump_choice", "player": state.dealer}
        else:
            state.phase = "predict"
            state.current_player = cursor
            state.trump_suit = None if revealed in (None, "narr") else _card(revealed)[0]

    def initial_state(self):
        players = [
            {"id": i, "hand": [], "prediction": None, "tricks_won": 0, "score": 0}
            for i in range(self.num_players)
        ]
        state = GameState(
            {"players": self.num_players, "seed": self.seed, "variant": "base"},
            1, 60 // self.num_players, 0, 1 % self.num_players, 1 % self.num_players,
            "predict", False, None, None, players,
            {"deck": [], "revealed_trump": None, "trick": [],
             "completed_tricks": [], "reserve": []},
            None, {"seed": self.seed, "shuffle_index": 0},
        )
        self._start_round(state)
        return state

    def current_player(self, state):
        return state.current_player

    def legal_actions(self, state):
        if state.terminal or state.phase == "terminal":
            return []
        actor = state.current_player
        if state.phase == "choose_trump":
            return [Action("choose_trump", actor, suit) for suit in SUITS]
        if state.phase == "predict":
            return [Action("predict", actor, n) for n in range(state.round_number + 1)]
        if state.phase != "play":
            return []
        hand = state.players[actor]["hand"]
        ordinary = [c for c in hand if c not in SPECIALS]
        matching = [c for c in ordinary if _card(c)[0] == state.led_suit]
        cards = matching + [c for c in hand if c in SPECIALS] if matching else list(hand)
        # Duplicate special cards are interchangeable and therefore one action each.
        return [Action("play_card", actor, c) for c in dict.fromkeys(cards)]

    def apply_action(self, state, action):
        if action not in self.legal_actions(state):
            raise ValueError("illegal action")
        state = copy.deepcopy(state)
        actor = action.actor
        if action.type == "choose_trump":
            state.trump_suit = action.arg
            state.pending = None
            state.phase = "predict"
            state.current_player = (state.dealer + 1) % self.num_players
        elif action.type == "predict":
            state.players[actor]["prediction"] = action.arg
            nxt = (actor + 1) % self.num_players
            if nxt == (state.dealer + 1) % self.num_players:
                state.phase = "play"
                state.current_player = state.leader
            else:
                state.current_player = nxt
        else:
            hand = state.players[actor]["hand"]
            hand.remove(action.arg)
            state.zones["trick"].append({"player": actor, "card": action.arg})
            if state.led_suit is None and action.arg not in SPECIALS:
                # A Wizard lead never establishes a suit; after Jesters, the first
                # ordinary card establishes the suit to be followed.
                state.led_suit = _card(action.arg)[0]
            if len(state.zones["trick"]) < self.num_players:
                state.current_player = (actor + 1) % self.num_players
            else:
                self._finish_trick(state)
        return state

    def _finish_trick(self, state):
        trick = state.zones["trick"]
        wizard = next((e for e in trick if e["card"] == "zauberer"), None)
        if wizard:
            winner = wizard["player"]
        else:
            candidates = [
                e for e in trick
                if e["card"] not in SPECIALS and _card(e["card"])[0] == state.trump_suit
            ]
            if not candidates:
                candidates = [
                    e for e in trick
                    if e["card"] not in SPECIALS and _card(e["card"])[0] == state.led_suit
                ]
            winner = (max(candidates, key=lambda e: _card(e["card"])[1])["player"]
                      if candidates else trick[0]["player"])
        state.players[winner]["tricks_won"] += 1
        state.zones["completed_tricks"].append(
            {"winner": winner, "cards": [e["card"] for e in trick]})
        state.zones["trick"] = []
        state.led_suit = None
        if all(not p["hand"] for p in state.players):
            self._finish_round(state)
        else:
            state.leader = winner
            state.current_player = winner

    def _finish_round(self, state):
        for player in state.players:
            bid, won = player["prediction"], player["tricks_won"]
            player["score"] += 20 + 10 * won if bid == won else -10 * abs(bid - won)
        if state.round_number == state.max_round:
            state.phase = "terminal"
            state.terminal = True
            state.current_player = -1
            return
        state.round_number += 1
        state.dealer = (state.dealer + 1) % self.num_players
        self._start_round(state)

    def is_terminal(self, state):
        return state.terminal

    def returns(self, state):
        return [p["score"] for p in state.players] if state.terminal else [0] * self.num_players

    def render(self, state):
        scores = ", ".join(f"P{p['id']}={p['score']}" for p in state.players)
        return (f"Wizard round {state.round_number}/{state.max_round}; "
                f"phase={state.phase}; current={state.current_player}; "
                f"trump={state.trump_suit}; scores: {scores}")

    def action_to_name(self, action):
        labels = {"menschen_blau": "Menschen (blau)", "elfen_gruen": "Elfen (grün)",
                  "zwerge_rot": "Zwerge (rot)", "riesen_gelb": "Riesen (gelb)",
                  "zauberer": "Zauberer", "narr": "Narr"}
        if action.type == "choose_trump":
            detail = labels[action.arg]
            return f"Spieler {action.actor}: Trumpf wählen – {detail}"
        if action.type == "predict":
            return f"Spieler {action.actor}: Vorhersage – {action.arg} Stiche"
        suit, rank = _card(action.arg)
        detail = labels[action.arg] if action.arg in SPECIALS else f"{labels[suit]} {rank}"
        return f"Spieler {action.actor}: Karte spielen – {detail}"

    def name_to_action(self, name):
        for actor in range(self.num_players):
            for suit in SUITS:
                action = Action("choose_trump", actor, suit)
                if self.action_to_name(action) == name:
                    return action
            for n in range(61):
                action = Action("predict", actor, n)
                if self.action_to_name(action) == name:
                    return action
            for card in _deck():
                action = Action("play_card", actor, card)
                if self.action_to_name(action) == name:
                    return action
        raise ValueError("unknown action name")

    def action_to_data(self, action):
        if not isinstance(action, Action):
            raise ValueError("invalid action")
        key = {"choose_trump": "suit", "predict": "tricks", "play_card": "card"}.get(action.type)
        if key is None:
            raise ValueError("invalid action type")
        return {"schema": ACTION_SCHEMA,
                "data": {"type": action.type, "actor": action.actor, "args": {key: action.arg}}}

    def action_from_data(self, payload):
        data = self._envelope(payload, ACTION_SCHEMA, {"type", "actor", "args"})
        typ, actor, args = data["type"], _strict_int(data["actor"], "actor"), data["args"]
        specs = {"choose_trump": ("suit", SUITS), "predict": ("tricks", None),
                 "play_card": ("card", None)}
        if typ not in specs or type(args) is not dict:
            raise ValueError("invalid action")
        key, allowed = specs[typ]
        if set(args) != {key}:
            raise ValueError("invalid action args")
        arg = args[key]
        if typ == "predict":
            _strict_int(arg, "tricks")
            if not 0 <= arg <= 60:
                raise ValueError("invalid prediction")
        elif typ == "play_card":
            _card(arg)
        elif arg not in allowed:
            raise ValueError("invalid suit")
        if not 0 <= actor < self.num_players:
            raise ValueError("invalid actor")
        return Action(typ, actor, arg)

    @staticmethod
    def _envelope(payload, schema, fields):
        if type(payload) is not dict or set(payload) != {"schema", "data"}:
            raise ValueError("invalid envelope")
        if payload["schema"] != schema or type(payload["data"]) is not dict:
            raise ValueError("invalid envelope")
        if set(payload["data"]) != fields:
            raise ValueError("invalid fields")
        return payload["data"]

    def state_to_data(self, state):
        return {"schema": STATE_SCHEMA, "data": copy.deepcopy(vars(state))}

    def state_from_data(self, payload):
        fields = {"configuration", "round_number", "max_round", "dealer", "leader",
                  "current_player", "phase", "terminal", "trump_suit", "led_suit",
                  "players", "zones", "pending", "chance"}
        data = copy.deepcopy(self._envelope(payload, STATE_SCHEMA, fields))
        self._validate_state(data)
        return GameState(**data)

    def _validate_state(self, d):
        cfg = d["configuration"]
        if type(cfg) is not dict or set(cfg) != {"players", "seed", "variant"}:
            raise ValueError("invalid configuration")
        if cfg != {"players": self.num_players, "seed": self.seed, "variant": "base"}:
            raise ValueError("state configuration does not match game")
        for key in ("round_number", "max_round", "dealer", "leader", "current_player"):
            _strict_int(d[key], key)
        if d["phase"] not in PHASES or type(d["terminal"]) is not bool:
            raise ValueError("invalid phase")
        for suit in (d["trump_suit"], d["led_suit"]):
            if suit is not None and suit not in SUITS:
                raise ValueError("invalid suit")
        if type(d["players"]) is not list or len(d["players"]) != self.num_players:
            raise ValueError("invalid players")
        for i, p in enumerate(d["players"]):
            if type(p) is not dict or set(p) != {"id", "hand", "prediction", "tricks_won", "score"}:
                raise ValueError("invalid player")
            if p["id"] != i or type(p["hand"]) is not list:
                raise ValueError("invalid player")
            for c in p["hand"]:
                _card(c)
            if p["prediction"] is not None:
                _strict_int(p["prediction"], "prediction")
            _strict_int(p["tricks_won"], "tricks_won")
            _strict_int(p["score"], "score")
        z = d["zones"]
        if type(z) is not dict or set(z) != {"deck", "revealed_trump", "trick", "completed_tricks", "reserve"}:
            raise ValueError("invalid zones")
        for key in ("deck", "reserve"):
            if type(z[key]) is not list:
                raise ValueError("invalid zone")
            for c in z[key]:
                _card(c)
        if z["revealed_trump"] is not None:
            _card(z["revealed_trump"])
        if type(z["trick"]) is not list or type(z["completed_tricks"]) is not list:
            raise ValueError("invalid tricks")
        for e in z["trick"]:
            if type(e) is not dict or set(e) != {"player", "card"}:
                raise ValueError("invalid trick")
            _strict_int(e["player"]); _card(e["card"])
        for e in z["completed_tricks"]:
            if type(e) is not dict or set(e) != {"winner", "cards"} or type(e["cards"]) is not list:
                raise ValueError("invalid completed trick")
            _strict_int(e["winner"])
            for c in e["cards"]:
                _card(c)
        pending = d["pending"]
        if pending is not None and (
            type(pending) is not dict or set(pending) != {"type", "player"}
            or pending["type"] != "trump_choice" or type(pending["player"]) is not int
        ):
            raise ValueError("invalid pending decision")
        chance = d["chance"]
        if type(chance) is not dict or set(chance) != {"seed", "shuffle_index"}:
            raise ValueError("invalid chance")
        if chance["seed"] != self.seed:
            raise ValueError("chance seed mismatch")
        _strict_int(chance["shuffle_index"], "shuffle_index")

    def observation_to_data(self, state, player):
        _strict_int(player, "player")
        if not 0 <= player < self.num_players:
            raise ValueError("invalid player")
        data = {
            "player": player, "round_number": state.round_number, "max_round": state.max_round,
            "dealer": state.dealer, "leader": state.leader,
            "current_player": state.current_player, "phase": state.phase,
            "terminal": state.terminal, "trump_suit": state.trump_suit,
            "led_suit": state.led_suit, "own_hand": copy.deepcopy(state.players[player]["hand"]),
            "players": [
                {"id": p["id"], "hand_size": len(p["hand"]), "prediction": p["prediction"],
                 "tricks_won": p["tricks_won"], "score": p["score"]}
                for p in state.players
            ],
            "revealed_trump": state.zones["revealed_trump"],
            "trick": copy.deepcopy(state.zones["trick"]),
            "completed_trick_count": len(state.zones["completed_tricks"]),
            "deck_size": len(state.zones["deck"]),
        }
        return {"schema": OBS_SCHEMA, "data": data}
