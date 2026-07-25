"""Wizard Version 1.0 base game, implemented from the supplied German rulebook."""
from __future__ import annotations

import copy
import hashlib
import json
import random

SUITS = ("menschen_blau", "elfen_gruen", "zwerge_rot", "riesen_gelb")
RANKS = tuple(range(1, 14))
SPECIALS = ("zauberer", "narr")
PHASES = ("choose_trump", "predict", "play", "terminal")
STATE_SCHEMA = "boardbench/wizard/state/1"
ACTION_SCHEMA = "boardbench/wizard/action/1"
OBS_SCHEMA = "boardbench/wizard/observation/1"
STATE_FIELDS = {"configuration", "round_number", "max_round", "dealer", "leader", "current_player", "phase", "terminal", "trump_suit", "led_suit", "players", "zones", "pending", "chance"}


def _deck():
    return [f"{s}:{r}" for s in SUITS for r in RANKS] + ["zauberer"] * 4 + ["narr"] * 4


def _card_ok(card):
    if card in SPECIALS:
        return True
    if not isinstance(card, str) or ":" not in card:
        return False
    suit, rank = card.rsplit(":", 1)
    return suit in SUITS and rank.isdigit() and int(rank) in RANKS and rank == str(int(rank))


def _suit(card):
    return card.rsplit(":", 1)[0] if card not in SPECIALS else None


class GameState:
    def __init__(self, data):
        self.data = data

    def __deepcopy__(self, memo):
        return GameState(copy.deepcopy(self.data, memo))


class Action(tuple):
    __slots__ = ()

    def __new__(cls, type_, actor, arg):
        return tuple.__new__(cls, (type_, actor, arg))

    @property
    def type(self): return self[0]
    @property
    def actor(self): return self[1]
    @property
    def arg(self): return self[2]

    def __reduce__(self):
        return (Action, tuple(self))


class Game:
    def __init__(self, num_players=None, seed=None):
        n = 4 if num_players is None else num_players
        if type(n) is not int or not 3 <= n <= 6:
            raise ValueError("num_players must be an integer from 3 through 6")
        if seed is not None and type(seed) is not int:
            raise TypeError("seed must be an integer or None")
        self.num_players, self.seed = n, seed

    def _shuffle(self, cards, index, basis=""):
        if index == 0:
            rng = random.Random(self.seed)
        else:
            material = json.dumps([self.seed, index, basis], ensure_ascii=False, sort_keys=True)
            rng = random.Random(int(hashlib.sha256(material.encode()).hexdigest(), 16))
        rng.shuffle(cards)

    def initial_state(self):
        d = {
            "configuration": {"players": self.num_players, "seed": self.seed, "variant": "base"},
            "round_number": 1, "max_round": 60 // self.num_players, "dealer": 0,
            "leader": 1 % self.num_players, "current_player": 1 % self.num_players,
            "phase": "predict", "terminal": False, "trump_suit": None, "led_suit": None,
            "players": [{"id": i, "hand": [], "prediction": None, "tricks_won": 0, "score": 0} for i in range(self.num_players)],
            "zones": {"deck": _deck(), "revealed_trump": None, "trick": [], "completed_tricks": [], "reserve": []},
            "pending": None, "chance": {"seed": self.seed, "shuffle_index": 0},
        }
        self._shuffle(d["zones"]["deck"], 0)
        self._deal(d)
        return GameState(d)

    def _deal(self, d):
        n, dealer, rnd = d["configuration"]["players"], d["dealer"], d["round_number"]
        for p in d["players"]:
            p["hand"], p["prediction"], p["tricks_won"] = [], None, 0
        deck = d["zones"]["deck"]
        for _ in range(rnd):
            for offset in range(1, n + 1):
                d["players"][(dealer + offset) % n]["hand"].append(deck.pop())
        d["zones"].update(revealed_trump=None, trick=[], completed_tricks=[])
        d["leader"] = d["current_player"] = (dealer + 1) % n
        d["led_suit"] = d["trump_suit"] = None
        if deck:
            card = deck.pop()
            d["zones"]["revealed_trump"] = card
            if card == "zauberer":
                d["phase"], d["current_player"] = "choose_trump", dealer
                d["pending"] = {"type": "trump_choice", "player": dealer}
            else:
                d["phase"] = "predict"
                d["trump_suit"] = _suit(card)
                d["pending"] = None
        else:
            d["phase"], d["pending"] = "predict", None

    def current_player(self, state):
        return None if state.data["terminal"] else state.data["current_player"]

    def legal_actions(self, state):
        d = state.data
        if d["terminal"] or d["phase"] == "terminal": return []
        actor = d["current_player"]
        if d["phase"] == "choose_trump": return [Action("choose_trump", actor, s) for s in SUITS]
        if d["phase"] == "predict": return [Action("predict", actor, i) for i in range(d["round_number"] + 1)]
        if d["phase"] != "play": return []
        hand = d["players"][actor]["hand"]
        led = d["led_suit"]
        if led and any(_suit(c) == led for c in hand):
            cards = [c for c in hand if c in SPECIALS or _suit(c) == led]
        else: cards = hand
        # Duplicate specials are mechanically identical; one canonical action is sufficient.
        return [Action("play_card", actor, c) for c in dict.fromkeys(cards)]

    def apply_action(self, state, action):
        if action not in self.legal_actions(state): raise ValueError("illegal action")
        s, d = copy.deepcopy(state), None
        d = s.data; n = d["configuration"]["players"]
        if action.type == "choose_trump":
            d["trump_suit"], d["phase"], d["pending"] = action.arg, "predict", None
            d["current_player"] = (d["dealer"] + 1) % n
        elif action.type == "predict":
            d["players"][action.actor]["prediction"] = action.arg
            nxt = (action.actor + 1) % n
            if all(p["prediction"] is not None for p in d["players"]):
                d["phase"], d["current_player"] = "play", d["leader"]
            else: d["current_player"] = nxt
        else:
            p = d["players"][action.actor]; p["hand"].remove(action.arg)
            d["zones"]["trick"].append({"player": action.actor, "card": action.arg})
            if d["led_suit"] is None and action.arg not in SPECIALS:
                d["led_suit"] = _suit(action.arg)
            if len(d["zones"]["trick"]) < n:
                d["current_player"] = (action.actor + 1) % n
            else: self._finish_trick(d)
        return s

    def _finish_trick(self, d):
        trick = d["zones"]["trick"]
        wizards = [x for x in trick if x["card"] == "zauberer"]
        if wizards: winner = wizards[0]["player"]
        else:
            ordinary = [x for x in trick if x["card"] != "narr"]
            if not ordinary: winner = trick[0]["player"]
            else:
                trumps = [x for x in ordinary if _suit(x["card"]) == d["trump_suit"]]
                candidates = trumps or [x for x in ordinary if _suit(x["card"]) == d["led_suit"]]
                winner = max(candidates, key=lambda x: int(x["card"].rsplit(":", 1)[1]))["player"]
        d["players"][winner]["tricks_won"] += 1
        d["zones"]["completed_tricks"].append({"winner": winner, "cards": [x["card"] for x in trick]})
        d["zones"]["trick"], d["led_suit"] = [], None
        d["leader"] = d["current_player"] = winner
        if all(not p["hand"] for p in d["players"]): self._finish_round(d)

    def _finish_round(self, d):
        for p in d["players"]:
            diff = abs(p["prediction"] - p["tricks_won"])
            p["score"] += 20 + 10 * p["tricks_won"] if diff == 0 else -10 * diff
        if d["round_number"] >= d["max_round"]:
            d["phase"], d["terminal"] = "terminal", True
            return
        inventory = []
        for p in d["players"]: inventory.extend(p["hand"])
        inventory.extend(d["zones"]["deck"])
        if d["zones"]["revealed_trump"] is not None: inventory.append(d["zones"]["revealed_trump"])
        for t in d["zones"]["completed_tricks"]: inventory.extend(t["cards"])
        inventory.extend(d["zones"]["reserve"])
        d["round_number"] += 1; d["dealer"] = (d["dealer"] + 1) % d["configuration"]["players"]
        d["chance"]["shuffle_index"] += 1
        self._shuffle(inventory, d["chance"]["shuffle_index"], json.dumps(d["players"], sort_keys=True))
        d["zones"]["deck"], d["zones"]["reserve"] = inventory, []
        self._deal(d)

    def is_terminal(self, state): return bool(state.data["terminal"])
    def returns(self, state): return [p["score"] for p in state.data["players"]]

    def action_to_name(self, action):
        labels = {"choose_trump": "Trumpf wählen", "predict": "Vorhersage", "play_card": "Karte spielen"}
        return f"{labels[action.type]} | Spieler {action.actor} | {action.arg}"

    def name_to_action(self, name):
        try:
            label, actor, arg = name.split(" | "); actor = int(actor.removeprefix("Spieler "))
            rev = {"Trumpf wählen": "choose_trump", "Vorhersage": "predict", "Karte spielen": "play_card"}
            typ = rev[label]; value = int(arg) if typ == "predict" else arg
            return Action(typ, actor, value)
        except Exception as exc: raise ValueError("invalid action name") from exc

    def action_to_data(self, action):
        args = {"suit": action.arg} if action.type == "choose_trump" else ({"tricks": action.arg} if action.type == "predict" else {"card": action.arg})
        return {"schema": ACTION_SCHEMA, "data": {"type": action.type, "actor": action.actor, "args": args}}

    def action_from_data(self, payload):
        if type(payload) is not dict or set(payload) != {"schema", "data"} or payload.get("schema") != ACTION_SCHEMA: raise ValueError("invalid action envelope")
        d = payload["data"]
        if type(d) is not dict or set(d) != {"type", "actor", "args"} or type(d.get("actor")) is not int or type(d.get("args")) is not dict: raise ValueError("invalid action")
        specs = {"choose_trump": ("suit", SUITS), "predict": ("tricks", None), "play_card": ("card", None)}
        if d.get("type") not in specs: raise ValueError("unknown action type")
        key, allowed = specs[d["type"]]
        if set(d["args"]) != {key}: raise ValueError("invalid action args")
        val = d["args"][key]
        if allowed and val not in allowed or d["type"] == "predict" and (type(val) is not int or val < 0) or d["type"] == "play_card" and not _card_ok(val): raise ValueError("invalid action parameter")
        return Action(d["type"], d["actor"], val)

    def state_to_data(self, state): return {"schema": STATE_SCHEMA, "data": copy.deepcopy(state.data)}

    def state_from_data(self, payload):
        if type(payload) is not dict or set(payload) != {"schema", "data"} or payload.get("schema") != STATE_SCHEMA: raise ValueError("invalid state envelope")
        d = payload["data"]
        if type(d) is not dict or set(d) != STATE_FIELDS: raise ValueError("invalid state fields")
        self._validate_state(d)
        return GameState(copy.deepcopy(d))

    def _validate_state(self, d):
        cfg = d["configuration"]
        if type(cfg) is not dict or set(cfg) != {"players", "seed", "variant"} or cfg["variant"] != "base" or type(cfg["players"]) is not int or not 3 <= cfg["players"] <= 6 or cfg["seed"] is not None and type(cfg["seed"]) is not int: raise ValueError("invalid configuration")
        ints = ("round_number", "max_round", "dealer", "leader", "current_player")
        if any(type(d[x]) is not int for x in ints) or type(d["terminal"]) is not bool or d["phase"] not in PHASES or d["trump_suit"] not in SUITS + (None,) or d["led_suit"] not in SUITS + (None,): raise ValueError("invalid state scalar")
        if type(d["players"]) is not list or len(d["players"]) != cfg["players"]: raise ValueError("invalid players")
        for i, p in enumerate(d["players"]):
            if type(p) is not dict or set(p) != {"id", "hand", "prediction", "tricks_won", "score"} or p["id"] != i or type(p["hand"]) is not list or not all(_card_ok(c) for c in p["hand"]) or p["prediction"] is not None and type(p["prediction"]) is not int or type(p["tricks_won"]) is not int or type(p["score"]) is not int: raise ValueError("invalid player")
        z = d["zones"]
        if type(z) is not dict or set(z) != {"deck", "revealed_trump", "trick", "completed_tricks", "reserve"}: raise ValueError("invalid zones")
        if any(type(z[x]) is not list for x in ("deck", "trick", "completed_tricks", "reserve")) or not all(_card_ok(c) for x in ("deck", "reserve") for c in z[x]) or z["revealed_trump"] is not None and not _card_ok(z["revealed_trump"]): raise ValueError("invalid cards")
        for x in z["trick"]:
            if type(x) is not dict or set(x) != {"player", "card"} or type(x["player"]) is not int or not _card_ok(x["card"]): raise ValueError("invalid trick")
        for x in z["completed_tricks"]:
            if type(x) is not dict or set(x) != {"winner", "cards"} or type(x["winner"]) is not int or type(x["cards"]) is not list or not all(_card_ok(c) for c in x["cards"]): raise ValueError("invalid completed trick")
        pending = d["pending"]
        if pending is not None and (type(pending) is not dict or set(pending) != {"type", "player"} or pending["type"] != "trump_choice" or type(pending["player"]) is not int): raise ValueError("invalid pending")
        chance = d["chance"]
        if type(chance) is not dict or set(chance) != {"seed", "shuffle_index"} or chance["seed"] is not None and type(chance["seed"]) is not int or type(chance["shuffle_index"]) is not int: raise ValueError("invalid chance")

    def observation_to_data(self, state, player):
        d = state.data; n = d["configuration"]["players"]
        if type(player) is not int or not 0 <= player < n: raise ValueError("invalid player")
        data = {k: copy.deepcopy(d[k]) for k in ("round_number", "max_round", "dealer", "leader", "current_player", "phase", "terminal", "trump_suit", "led_suit")}
        data.update(player=player, own_hand=copy.deepcopy(d["players"][player]["hand"]), players=[{"id": p["id"], "hand_size": len(p["hand"]), "prediction": p["prediction"], "tricks_won": p["tricks_won"], "score": p["score"]} for p in d["players"]], revealed_trump=d["zones"]["revealed_trump"], trick=copy.deepcopy(d["zones"]["trick"]), completed_trick_count=len(d["zones"]["completed_tricks"]), deck_size=len(d["zones"]["deck"]))
        return {"schema": OBS_SCHEMA, "data": data}

    def render(self, state):
        d = state.data
        return f"Wizard Runde {d['round_number']}/{d['max_round']} | Phase {d['phase']} | Trumpf {d['trump_suit'] or '-'} | Punkte " + ", ".join(f"S{p['id']}={p['score']}" for p in d["players"])
