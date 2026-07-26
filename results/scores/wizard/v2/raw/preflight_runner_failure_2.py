"""Wizard (German rules, version 1.0), as a small deterministic game engine."""
from copy import deepcopy
from dataclasses import dataclass
import json
import random

SUITS = ("menschen_blau", "elfen_gruen", "zwerge_rot", "riesen_gelb")
RANKS = tuple(range(1, 14))
PHASES = ("choose_trump", "predict", "play", "terminal")
STATE_SCHEMA = "boardbench/wizard/state/1"
ACTION_SCHEMA = "boardbench/wizard/action/1"
OBS_SCHEMA = "boardbench/wizard/observation/1"


@dataclass(eq=True)
class GameState:
    data: dict


@dataclass(frozen=True)
class Action:
    type: str
    actor: int
    args: tuple


def _card_suit(card):
    return card.split(":", 1)[0] if ":" in card else None


def _card_rank(card):
    return int(card.split(":", 1)[1]) if ":" in card else None


class Game:
    def __init__(self, num_players=None, seed=None):
        self.num_players = 4 if num_players is None else num_players
        if type(self.num_players) is not int or self.num_players not in (3, 4, 5, 6):
            raise ValueError("num_players must be one of 3, 4, 5, 6")
        if seed is not None and type(seed) is not int:
            raise ValueError("seed must be an integer or None")
        self.seed = seed

    @staticmethod
    def _inventory():
        return [f"{s}:{r}" for s in SUITS for r in RANKS] + ["zauberer"] * 4 + ["narr"] * 4

    def _shuffled(self, index):
        cards = self._inventory()
        # A local generator makes the state, rather than process-global RNG, authoritative.
        rng = random.Random(f"wizard:{self.seed!r}:{index}")
        rng.shuffle(cards)
        return cards

    def initial_state(self):
        n = self.num_players
        data = {
            "configuration": {"players": n, "seed": self.seed, "variant": "base"},
            "round_number": 1, "max_round": 60 // n, "dealer": 0,
            "leader": 1 % n, "current_player": 1 % n, "phase": "predict",
            "terminal": False, "trump_suit": None, "led_suit": None,
            "players": [{"id": i, "hand": [], "prediction": None,
                         "tricks_won": 0, "score": 0} for i in range(n)],
            "zones": {"deck": [], "revealed_trump": None, "trick": [],
                      "completed_tricks": [], "reserve": []},
            "pending": None, "chance": {"seed": self.seed, "shuffle_index": 0},
        }
        self._deal_round(data)
        return GameState(data)

    def _deal_round(self, d):
        n, rnd = d["configuration"]["players"], d["round_number"]
        cards = self._shuffled(d["chance"]["shuffle_index"])
        d["chance"]["shuffle_index"] += 1
        for p in d["players"]:
            p["hand"] = []
            p["prediction"] = None
            p["tricks_won"] = 0
        # Dealing starts left of dealer, one card at a time.
        for _ in range(rnd):
            for off in range(1, n + 1):
                d["players"][(d["dealer"] + off) % n]["hand"].append(cards.pop())
        d["zones"] = {"deck": cards, "revealed_trump": None, "trick": [],
                      "completed_tricks": [], "reserve": []}
        d["leader"] = (d["dealer"] + 1) % n
        d["current_player"] = d["leader"]
        d["trump_suit"] = None
        d["led_suit"] = None
        d["pending"] = None
        if cards:
            shown = cards.pop()
            d["zones"]["revealed_trump"] = shown
            if shown == "zauberer":
                d["phase"] = "choose_trump"
                d["current_player"] = d["dealer"]
                d["pending"] = {"type": "trump_choice", "player": d["dealer"]}
            else:
                d["trump_suit"] = _card_suit(shown)  # Fool therefore means no trump.
                d["phase"] = "predict"
        else:
            d["phase"] = "predict"  # Last round has no revealed card and no trump.

    def current_player(self, state):
        return state.data["current_player"]

    def legal_actions(self, state):
        d = state.data
        if d["terminal"] or d["phase"] == "terminal":
            return []
        actor = d["current_player"]
        if d["phase"] == "choose_trump":
            return [Action("choose_trump", actor, (("suit", s),)) for s in SUITS]
        if d["phase"] == "predict":
            return [Action("predict", actor, (("tricks", i),))
                    for i in range(d["round_number"] + 1)]
        if d["phase"] != "play":
            return []
        hand = d["players"][actor]["hand"]
        led = d["led_suit"]
        has_led = led is not None and any(_card_suit(c) == led for c in hand)
        playable = [c for c in hand if c in ("zauberer", "narr") or
                    not has_led or _card_suit(c) == led]
        return [Action("play_card", actor, (("card", c),)) for c in dict.fromkeys(playable)]

    def apply_action(self, state, action):
        legal = self.legal_actions(state)
        if action not in legal:
            raise ValueError("illegal action")
        d = deepcopy(state.data)
        args = dict(action.args)
        n = d["configuration"]["players"]
        if action.type == "choose_trump":
            d["trump_suit"] = args["suit"]
            d["pending"] = None
            d["phase"] = "predict"
            d["current_player"] = (d["dealer"] + 1) % n
        elif action.type == "predict":
            d["players"][action.actor]["prediction"] = args["tricks"]
            nxt = (action.actor + 1) % n
            if nxt == (d["dealer"] + 1) % n:
                d["phase"] = "play"
                d["current_player"] = d["leader"]
            else:
                d["current_player"] = nxt
        else:
            card = args["card"]
            d["players"][action.actor]["hand"].remove(card)
            d["zones"]["trick"].append({"player": action.actor, "card": card})
            if d["led_suit"] is None and _card_suit(card) is not None:
                d["led_suit"] = _card_suit(card)
            if len(d["zones"]["trick"]) < n:
                d["current_player"] = (action.actor + 1) % n
            else:
                self._finish_trick(d)
        return GameState(d)

    def _finish_trick(self, d):
        trick = d["zones"]["trick"]
        wizard = next((e for e in trick if e["card"] == "zauberer"), None)
        if wizard:
            winner = wizard["player"]
        else:
            ordinary = [e for e in trick if e["card"] != "narr"]
            if not ordinary:
                winner = trick[0]["player"]
            else:
                trump = [e for e in ordinary if _card_suit(e["card"]) == d["trump_suit"]]
                candidates = trump or [e for e in ordinary
                                       if _card_suit(e["card"]) == d["led_suit"]]
                winner = max(candidates, key=lambda e: _card_rank(e["card"]))["player"]
        d["players"][winner]["tricks_won"] += 1
        d["zones"]["completed_tricks"].append(
            {"winner": winner, "cards": [e["card"] for e in trick]})
        d["zones"]["trick"] = []
        d["led_suit"] = None
        d["leader"] = winner
        d["current_player"] = winner
        if all(not p["hand"] for p in d["players"]):
            for p in d["players"]:
                delta = abs(p["tricks_won"] - p["prediction"])
                p["score"] += 20 + 10 * p["tricks_won"] if delta == 0 else -10 * delta
            if d["round_number"] == d["max_round"]:
                d["phase"], d["terminal"] = "terminal", True
            else:
                d["round_number"] += 1
                d["dealer"] = (d["dealer"] + 1) % d["configuration"]["players"]
                self._deal_round(d)

    def is_terminal(self, state):
        return bool(state.data["terminal"])

    def returns(self, state):
        if not self.is_terminal(state):
            return [0] * state.data["configuration"]["players"]
        return [p["score"] for p in state.data["players"]]

    def render(self, state):
        d = state.data
        scores = ", ".join(f"P{p['id']}={p['score']}" for p in d["players"])
        return (f"Wizard round {d['round_number']}/{d['max_round']} "
                f"phase={d['phase']} current=P{d['current_player']} "
                f"trump={d['trump_suit'] or 'none'} scores: {scores}")

    def action_to_name(self, action):
        value = dict(action.args)
        label = {"choose_trump": "Trumpf wählen", "predict": "Vorhersage",
                 "play_card": "Karte spielen"}[action.type]
        key = next(iter(value))
        return f"{label} | Spieler {action.actor} | {key}={value[key]}"

    def name_to_action(self, name):
        try:
            label, actor, assignment = name.split(" | ")
            types = {"Trumpf wählen": "choose_trump", "Vorhersage": "predict",
                     "Karte spielen": "play_card"}
            typ = types[label]
            actor_i = int(actor.removeprefix("Spieler "))
            key, raw = assignment.split("=", 1)
            value = int(raw) if typ == "predict" else raw
            action = Action(typ, actor_i, ((key, value),))
            if self.action_to_name(action) != name:
                raise ValueError
            return action
        except Exception as exc:
            raise ValueError("invalid action name") from exc

    def action_to_data(self, action):
        return {"schema": ACTION_SCHEMA, "data": {
            "type": action.type, "actor": action.actor, "args": dict(action.args)}}

    def action_from_data(self, payload):
        self._envelope(payload, ACTION_SCHEMA)
        d = payload["data"]
        if set(d) != {"type", "actor", "args"} or type(d["actor"]) is not int or not isinstance(d["args"], dict):
            raise ValueError("invalid action payload")
        expected = {"choose_trump": ("suit", SUITS), "predict": ("tricks", None),
                    "play_card": ("card", None)}
        if d["type"] not in expected:
            raise ValueError("invalid action type")
        key, choices = expected[d["type"]]
        if set(d["args"]) != {key}:
            raise ValueError("invalid action arguments")
        val = d["args"][key]
        if choices is not None and val not in choices:
            raise ValueError("invalid suit")
        if d["type"] == "predict" and (type(val) is not int or val < 0):
            raise ValueError("invalid prediction")
        if d["type"] == "play_card" and not self._valid_card(val):
            raise ValueError("invalid card")
        return Action(d["type"], d["actor"], ((key, val),))

    def state_to_data(self, state):
        return {"schema": STATE_SCHEMA, "data": deepcopy(state.data)}

    def state_from_data(self, payload):
        self._envelope(payload, STATE_SCHEMA)
        d = payload["data"]
        required = {"configuration", "round_number", "max_round", "dealer", "leader",
                    "current_player", "phase", "terminal", "trump_suit", "led_suit",
                    "players", "zones", "pending", "chance"}
        if set(d) != required:
            raise ValueError("invalid state fields")
        self._validate_state(d)
        return GameState(deepcopy(d))

    def observation_to_data(self, state, player):
        d = state.data
        if type(player) is not int or not 0 <= player < d["configuration"]["players"]:
            raise ValueError("invalid player")
        own = next(p for p in d["players"] if p["id"] == player)
        data = {
            "player": player, "round_number": d["round_number"], "max_round": d["max_round"],
            "dealer": d["dealer"], "leader": d["leader"],
            "current_player": d["current_player"], "phase": d["phase"],
            "terminal": d["terminal"], "trump_suit": d["trump_suit"],
            "led_suit": d["led_suit"], "own_hand": deepcopy(own["hand"]),
            "players": [{"id": p["id"], "hand_size": len(p["hand"]),
                         "prediction": p["prediction"], "tricks_won": p["tricks_won"],
                         "score": p["score"]} for p in d["players"]],
            "revealed_trump": d["zones"]["revealed_trump"],
            "trick": deepcopy(d["zones"]["trick"]),
            "completed_trick_count": len(d["zones"]["completed_tricks"]),
            "deck_size": len(d["zones"]["deck"]),
        }
        return {"schema": OBS_SCHEMA, "data": data}

    @staticmethod
    def _envelope(payload, schema):
        if not isinstance(payload, dict) or set(payload) != {"schema", "data"} or \
                payload.get("schema") != schema or not isinstance(payload.get("data"), dict):
            raise ValueError("invalid envelope")

    @staticmethod
    def _valid_card(c):
        if c in ("zauberer", "narr"):
            return True
        if not isinstance(c, str) or ":" not in c:
            return False
        s, r = c.rsplit(":", 1)
        return s in SUITS and r.isdigit() and int(r) in RANKS

    def _validate_state(self, d):
        cfg = d["configuration"]
        if not isinstance(cfg, dict) or set(cfg) != {"players", "seed", "variant"} or \
                type(cfg["players"]) is not int or cfg["players"] not in (3, 4, 5, 6) or \
                cfg["variant"] != "base" or (cfg["seed"] is not None and type(cfg["seed"]) is not int):
            raise ValueError("invalid configuration")
        n = cfg["players"]
        ints = ("round_number", "max_round", "dealer", "leader", "current_player")
        if any(type(d[k]) is not int for k in ints) or d["phase"] not in PHASES or \
                type(d["terminal"]) is not bool or d["trump_suit"] not in (*SUITS, None) or \
                d["led_suit"] not in (*SUITS, None):
            raise ValueError("invalid state scalar")
        if not isinstance(d["players"], list) or len(d["players"]) != n:
            raise ValueError("invalid players")
        for p in d["players"]:
            if set(p) != {"id", "hand", "prediction", "tricks_won", "score"} or \
                    any(type(p[k]) is not int for k in ("id", "tricks_won", "score")) or \
                    (p["prediction"] is not None and type(p["prediction"]) is not int) or \
                    not isinstance(p["hand"], list) or not all(self._valid_card(c) for c in p["hand"]):
                raise ValueError("invalid player")
        z = d["zones"]
        if not isinstance(z, dict) or set(z) != {"deck", "revealed_trump", "trick", "completed_tricks", "reserve"}:
            raise ValueError("invalid zones")
        all_lists = z["deck"] + z["reserve"]
        if not all(self._valid_card(c) for c in all_lists) or \
                (z["revealed_trump"] is not None and not self._valid_card(z["revealed_trump"])):
            raise ValueError("invalid cards")
        json.dumps(d, allow_nan=False)
