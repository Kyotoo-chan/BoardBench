"""Wizard (German rulebook, Version 1.0), base game."""
from dataclasses import dataclass
from copy import deepcopy
import random

SUITS = ("menschen_blau", "elfen_gruen", "zwerge_rot", "riesen_gelb")
PHASES = ("choose_trump", "predict", "play", "terminal")
ACTION_TYPES = ("choose_trump", "predict", "play_card")
STATE_SCHEMA = "boardbench/wizard/state/1"
ACTION_SCHEMA = "boardbench/wizard/action/1"
OBS_SCHEMA = "boardbench/wizard/observation/1"


def _cards():
    return [f"{s}:{r}" for s in SUITS for r in range(1, 14)] + ["zauberer"] * 4 + ["narr"] * 4


def _suit(card):
    return card.split(":", 1)[0] if ":" in card else None


def _valid_card(card):
    if card in ("zauberer", "narr"):
        return True
    if not isinstance(card, str) or ":" not in card:
        return False
    suit, rank = card.rsplit(":", 1)
    return suit in SUITS and rank.isdigit() and 1 <= int(rank) <= 13


@dataclass(frozen=True)
class Action:
    type: str
    actor: int
    args: dict


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
    players: list
    zones: dict
    pending: dict | None
    chance: dict


class Game:
    def __init__(self, num_players=None, seed=None):
        self.num_players = 4 if num_players is None else num_players
        if type(self.num_players) is not int or self.num_players not in (3, 4, 5, 6):
            raise ValueError("num_players must be one of 3, 4, 5, 6")
        if seed is not None and type(seed) is not int:
            raise ValueError("seed must be an integer or None")
        self.seed = seed

    def initial_state(self):
        n = self.num_players
        effective_seed = self.seed if self.seed is not None else random.SystemRandom().randrange(2**63)
        state = GameState(
            {"players": n, "seed": self.seed, "variant": "base"}, 1, 60 // n,
            0, 1 % n, 1 % n, "predict", False, None, None,
            [{"id": p, "hand": [], "prediction": None, "tricks_won": 0, "score": 0}
             for p in range(n)],
            {"deck": [], "revealed_trump": None, "trick": [], "completed_tricks": [], "reserve": []},
            None, {"seed": effective_seed, "shuffle_index": 0})
        self._deal_round(state)
        return state

    def _deal_round(self, state):
        rng = random.Random(f"{state.chance['seed']}:{state.chance['shuffle_index']}")
        deck = _cards()
        rng.shuffle(deck)
        state.chance["shuffle_index"] += 1
        for p in state.players:
            p["hand"] = []
            p["prediction"] = None
            p["tricks_won"] = 0
        for _ in range(state.round_number):
            for offset in range(1, len(state.players) + 1):
                state.players[(state.dealer + offset) % len(state.players)]["hand"].append(deck.pop())
        state.zones = {"deck": deck, "revealed_trump": None, "trick": [],
                       "completed_tricks": [], "reserve": []}
        state.leader = (state.dealer + 1) % len(state.players)
        state.current_player = state.leader
        state.led_suit = None
        state.trump_suit = None
        state.pending = None
        if deck:
            shown = deck.pop()
            state.zones["revealed_trump"] = shown
            if shown == "zauberer":
                state.phase = "choose_trump"
                state.current_player = state.dealer
                state.pending = {"type": "trump_choice", "player": state.dealer}
            else:
                state.phase = "predict"
                state.trump_suit = _suit(shown)  # Narr therefore means no trump.
        else:
            state.phase = "predict"

    def current_player(self, state):
        return -1 if state.terminal else state.current_player

    def legal_actions(self, state):
        if state.terminal:
            return []
        actor = state.current_player
        if state.phase == "choose_trump":
            return [Action("choose_trump", actor, {"suit": suit}) for suit in SUITS]
        if state.phase == "predict":
            return [Action("predict", actor, {"tricks": n}) for n in range(state.round_number + 1)]
        if state.phase != "play":
            return []
        hand = state.players[actor]["hand"]
        led = state.led_suit
        if led and any(_suit(c) == led for c in hand):
            legal = [c for c in hand if _suit(c) == led or c in ("zauberer", "narr")]
        else:
            legal = list(hand)
        return [Action("play_card", actor, {"card": c}) for c in dict.fromkeys(legal)]

    def apply_action(self, state, action):
        canonical = self.action_from_data(self.action_to_data(action))
        if self.action_to_data(canonical) not in [self.action_to_data(a) for a in self.legal_actions(state)]:
            raise ValueError("illegal action")
        s = deepcopy(state)
        a, n = canonical.actor, len(s.players)
        if canonical.type == "choose_trump":
            s.trump_suit = canonical.args["suit"]
            s.pending = None
            s.phase = "predict"
            s.current_player = (s.dealer + 1) % n
        elif canonical.type == "predict":
            s.players[a]["prediction"] = canonical.args["tricks"]
            nxt = (a + 1) % n
            if all(p["prediction"] is not None for p in s.players):
                s.phase = "play"
                s.current_player = s.leader
            else:
                s.current_player = nxt
        else:
            card = canonical.args["card"]
            s.players[a]["hand"].remove(card)
            s.zones["trick"].append({"player": a, "card": card})
            if len(s.zones["trick"]) == 1 and card not in ("zauberer", "narr"):
                s.led_suit = _suit(card)
            if len(s.zones["trick"]) < n:
                s.current_player = (a + 1) % n
            else:
                winner = self._trick_winner(s.zones["trick"], s.trump_suit)
                s.players[winner]["tricks_won"] += 1
                s.zones["completed_tricks"].append(
                    {"winner": winner, "cards": [x["card"] for x in s.zones["trick"]]})
                s.zones["trick"] = []
                s.led_suit = None
                s.leader = winner
                s.current_player = winner
                if not s.players[0]["hand"]:
                    self._finish_round(s)
        return s

    @staticmethod
    def _trick_winner(trick, trump):
        for play in trick:
            if play["card"] == "zauberer":
                return play["player"]
        ordinary = [p for p in trick if p["card"] != "narr"]
        if not ordinary:
            return trick[0]["player"]
        led = _suit(ordinary[0]["card"])
        trump_cards = [p for p in ordinary if _suit(p["card"]) == trump]
        pool = trump_cards or [p for p in ordinary if _suit(p["card"]) == led]
        return max(pool, key=lambda p: int(p["card"].rsplit(":", 1)[1]))["player"]

    def _finish_round(self, s):
        for p in s.players:
            difference = abs(p["prediction"] - p["tricks_won"])
            p["score"] += 20 + 10 * p["tricks_won"] if difference == 0 else -10 * difference
        if s.round_number == s.max_round:
            s.phase, s.terminal, s.current_player = "terminal", True, -1
            s.pending = None
            return
        s.round_number += 1
        s.dealer = (s.dealer + 1) % len(s.players)
        self._deal_round(s)

    def is_terminal(self, state):
        return state.terminal

    def returns(self, state):
        return [p["score"] for p in state.players] if state.terminal else [0] * len(state.players)

    def render(self, state):
        return (f"Wizard round {state.round_number}/{state.max_round}; phase={state.phase}; "
                f"player={state.current_player}; trump={state.trump_suit}; "
                f"scores={[p['score'] for p in state.players]}")

    def action_to_name(self, action):
        a = self.action_from_data(self.action_to_data(action))
        if a.type == "choose_trump":
            return f"Trumpffarbe wählen: {a.args['suit']} (Lehrling {a.actor})"
        if a.type == "predict":
            return f"Vorhersage: {a.args['tricks']} Stiche (Lehrling {a.actor})"
        return f"Karte spielen: {a.args['card']} (Lehrling {a.actor})"

    def name_to_action(self, name):
        if not isinstance(name, str):
            raise ValueError("invalid action name")
        import re
        patterns = [
            (r"Trumpffarbe wählen: (.+) \(Lehrling (\d+)\)", "choose_trump", "suit"),
            (r"Vorhersage: (\d+) Stiche \(Lehrling (\d+)\)", "predict", "tricks"),
            (r"Karte spielen: (.+) \(Lehrling (\d+)\)", "play_card", "card")]
        for pattern, typ, key in patterns:
            m = re.fullmatch(pattern, name)
            if m:
                value = int(m.group(1)) if key == "tricks" else m.group(1)
                return self.action_from_data({"schema": ACTION_SCHEMA,
                                              "data": {"type": typ, "actor": int(m.group(2)),
                                                       "args": {key: value}}})
        raise ValueError("invalid action name")

    def action_to_data(self, action):
        if not isinstance(action, Action):
            raise ValueError("action must be Action")
        payload = {"schema": ACTION_SCHEMA, "data": {
            "type": action.type, "actor": action.actor, "args": deepcopy(action.args)}}
        self.action_from_data(payload)
        return payload

    def action_from_data(self, payload):
        data = self._envelope(payload, ACTION_SCHEMA)
        if set(data) != {"type", "actor", "args"} or data["type"] not in ACTION_TYPES:
            raise ValueError("invalid action fields")
        if type(data["actor"]) is not int or data["actor"] < 0 or type(data["args"]) is not dict:
            raise ValueError("invalid actor or args")
        spec = {"choose_trump": ("suit",), "predict": ("tricks",), "play_card": ("card",)}[data["type"]]
        if set(data["args"]) != set(spec):
            raise ValueError("invalid action arguments")
        value = data["args"][spec[0]]
        if data["type"] == "choose_trump" and value not in SUITS:
            raise ValueError("invalid suit")
        if data["type"] == "predict" and (type(value) is not int or value < 0):
            raise ValueError("invalid prediction")
        if data["type"] == "play_card" and not _valid_card(value):
            raise ValueError("invalid card")
        return Action(data["type"], data["actor"], deepcopy(data["args"]))

    def state_to_data(self, state):
        if not isinstance(state, GameState):
            raise ValueError("state must be GameState")
        data = {name: deepcopy(getattr(state, name)) for name in GameState.__dataclass_fields__}
        payload = {"schema": STATE_SCHEMA, "data": data}
        self.state_from_data(payload)
        return payload

    def state_from_data(self, payload):
        d = self._envelope(payload, STATE_SCHEMA)
        required = set(GameState.__dataclass_fields__)
        if set(d) != required:
            raise ValueError("invalid state fields")
        self._validate_state(d)
        return GameState(**deepcopy(d))

    def _validate_state(self, d):
        ints = ("round_number", "max_round", "dealer", "leader", "current_player")
        if any(type(d[k]) is not int for k in ints) or type(d["terminal"]) is not bool:
            raise ValueError("invalid state scalar")
        c = d["configuration"]
        if (type(c) is not dict or set(c) != {"players", "seed", "variant"} or
                type(c["players"]) is not int or c["players"] not in (3, 4, 5, 6) or
                (c["seed"] is not None and type(c["seed"]) is not int) or c["variant"] != "base"):
            raise ValueError("invalid configuration")
        if d["phase"] not in PHASES or d["trump_suit"] not in (*SUITS, None) or d["led_suit"] not in (*SUITS, None):
            raise ValueError("invalid phase or suit")
        if type(d["players"]) is not list or len(d["players"]) != c["players"]:
            raise ValueError("invalid players")
        for p in d["players"]:
            if type(p) is not dict or set(p) != {"id", "hand", "prediction", "tricks_won", "score"}:
                raise ValueError("invalid player")
            if any(type(p[k]) is not int for k in ("id", "tricks_won", "score")):
                raise ValueError("invalid player scalar")
            if p["prediction"] is not None and type(p["prediction"]) is not int:
                raise ValueError("invalid prediction")
            self._card_list(p["hand"])
        z = d["zones"]
        if type(z) is not dict or set(z) != {"deck", "revealed_trump", "trick", "completed_tricks", "reserve"}:
            raise ValueError("invalid zones")
        self._card_list(z["deck"]); self._card_list(z["reserve"])
        if z["revealed_trump"] is not None and not _valid_card(z["revealed_trump"]):
            raise ValueError("invalid revealed card")
        if type(z["trick"]) is not list or any(type(x) is not dict or set(x) != {"player", "card"}
                or type(x["player"]) is not int or not _valid_card(x["card"]) for x in z["trick"]):
            raise ValueError("invalid trick")
        if type(z["completed_tricks"]) is not list:
            raise ValueError("invalid completed tricks")
        for x in z["completed_tricks"]:
            if type(x) is not dict or set(x) != {"winner", "cards"} or type(x["winner"]) is not int:
                raise ValueError("invalid completed trick")
            self._card_list(x["cards"])
        pending = d["pending"]
        if pending is not None and (type(pending) is not dict or set(pending) != {"type", "player"}
                or pending["type"] != "trump_choice" or type(pending["player"]) is not int):
            raise ValueError("invalid pending decision")
        chance = d["chance"]
        if (type(chance) is not dict or set(chance) != {"seed", "shuffle_index"} or
                (chance["seed"] is not None and type(chance["seed"]) is not int) or
                type(chance["shuffle_index"]) is not int):
            raise ValueError("invalid chance")

    @staticmethod
    def _card_list(value):
        if type(value) is not list or any(not _valid_card(c) for c in value):
            raise ValueError("invalid card list")

    def observation_to_data(self, state, player):
        if type(player) is not int or not 0 <= player < len(state.players):
            raise ValueError("invalid observing player")
        d = {"player": player, "round_number": state.round_number, "max_round": state.max_round,
             "dealer": state.dealer, "leader": state.leader, "current_player": state.current_player,
             "phase": state.phase, "terminal": state.terminal, "trump_suit": state.trump_suit,
             "led_suit": state.led_suit, "own_hand": deepcopy(state.players[player]["hand"]),
             "players": [{"id": p["id"], "hand_size": len(p["hand"]), "prediction": p["prediction"],
                          "tricks_won": p["tricks_won"], "score": p["score"]} for p in state.players],
             "revealed_trump": state.zones["revealed_trump"], "trick": deepcopy(state.zones["trick"]),
             "completed_trick_count": len(state.zones["completed_tricks"]),
             "deck_size": len(state.zones["deck"])}
        return {"schema": OBS_SCHEMA, "data": d}

    @staticmethod
    def _envelope(payload, schema):
        if type(payload) is not dict or set(payload) != {"schema", "data"}:
            raise ValueError("invalid envelope")
        if payload["schema"] != schema or type(payload["data"]) is not dict:
            raise ValueError("invalid schema or data")
        return payload["data"]
