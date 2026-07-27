"""Exploding Kittens (German NSFW Edition 2018), from the supplied rulebook."""
from dataclasses import dataclass
import copy
import random
from typing import Any

CARDS = (
    "exploding_kitten", "defuse", "attack", "nope", "skip", "favor",
    "shuffle", "see_future", "cat_beard", "cat_cattermelon",
    "cat_hairy_potato", "cat_rainbow", "cat_tacocat",
)
CAT_CARDS = set(CARDS[8:])
PLAYABLE = set(CARDS[2:])
STATE_SCHEMA = "boardbench/exploding-kittens/state/2"
ACTION_SCHEMA = "boardbench/exploding-kittens/action/2"
OBS_SCHEMA = "boardbench/exploding-kittens/observation/2"
PHASES = {"play", "reaction", "favor_give", "defuse_reinsert", "terminal"}
ACTION_TYPES = {
    "draw", "play_card", "play_pair", "play_triple", "play_five",
    "give_card", "reinsert", "play_nope", "pass_nope",
}


@dataclass(frozen=True)
class Action:
    type: str
    actor: int
    args: tuple[tuple[str, Any], ...] = ()

    def get(self, key: str, default: Any = None) -> Any:
        return dict(self.args).get(key, default)


@dataclass
class GameState:
    configuration: dict
    players: list[dict]
    zones: dict
    current_player: int
    turns_owed: int
    phase: str
    pending: dict | None
    terminal: bool
    winner: int | None
    turn_number: int
    chance: dict


def _action(kind: str, actor: int, **args: Any) -> Action:
    return Action(kind, actor, tuple((k, args[k]) for k in sorted(args)))


class Game:
    def __init__(self, num_players: int | None = None, seed: int | None = None):
        self.num_players = 2 if num_players is None else num_players
        if self.num_players not in (2, 3, 4, 5):
            raise ValueError("num_players must be one of 2, 3, 4, 5")
        if seed is not None and (type(seed) is not int):
            raise ValueError("seed must be an integer or None")
        self.seed = seed

    def _shuffle(self, state: GameState, cards: list[str]) -> None:
        # Each chance operation is a pure function of the serialized seed/counter.
        rng = random.Random(f"{state.chance['seed']}:{state.chance['counter']}")
        rng.shuffle(cards)
        state.chance["counter"] += 1

    def initial_state(self) -> GameState:
        n = self.num_players
        # Rulebook material counts: EK 4, Defuse 6, action counts 4/4/4/4/5,
        # cat cards 4 of each kind.
        rest = (
            ["attack"] * 4 + ["skip"] * 4 + ["favor"] * 4 +
            ["shuffle"] * 4 + ["see_future"] * 5 + ["nope"] * 5 +
            sum(([c] * 4 for c in CARDS[8:]), [])
        )
        state = GameState(
            {"players": n, "seed": self.seed, "variant": "base"},
            [{"id": i, "alive": True, "hand": [], "preview": []} for i in range(n)],
            {"deck": [], "discard": [],
             "box": ["exploding_kitten"] * (5 - n) + (["defuse"] * 2 if n == 2 else [])},
            0, 1, "play", None, False, None, 0,
            {"seed": self.seed, "counter": 0},
        )
        self._shuffle(state, rest)
        for i in range(n):
            state.players[i]["hand"] = [rest.pop() for _ in range(7)] + ["defuse"]
        rest += ["exploding_kitten"] * (n - 1)
        rest += ["defuse"] * (2 if n == 2 else 6 - n)
        self._shuffle(state, rest)
        # Internal and canonical order is bottom to top.
        state.zones["deck"] = rest
        return state

    def current_player(self, state: GameState) -> int:
        return state.current_player

    def is_terminal(self, state: GameState) -> bool:
        return state.terminal

    def returns(self, state: GameState) -> list[int]:
        if not state.terminal:
            return [0] * len(state.players)
        return [1 if i == state.winner else -1 for i in range(len(state.players))]

    def _alive_after(self, state: GameState, player: int) -> int:
        n = len(state.players)
        for d in range(1, n + 1):
            candidate = (player + d) % n
            if state.players[candidate]["alive"]:
                return candidate
        return player

    def _counts(self, hand: list[str]) -> dict[str, int]:
        return {c: hand.count(c) for c in CARDS}

    def legal_actions(self, state: GameState) -> list[Action]:
        if state.terminal:
            return []
        p = state.current_player
        hand = state.players[p]["hand"]
        counts = self._counts(hand)
        if state.phase == "favor_give":
            return [_action("give_card", p, card=c) for c in CARDS if counts[c]]
        if state.phase == "defuse_reinsert":
            return [_action("reinsert", p, position=i)
                    for i in range(len(state.zones["deck"]) + 1)]
        if state.phase == "reaction":
            out = [_action("pass_nope", p)]
            if counts["nope"]:
                out.insert(0, _action("play_nope", p))
            return out
        out = [_action("draw", p)]
        opponents = [x["id"] for x in state.players if x["alive"] and x["id"] != p]
        for card in CARDS:
            if not counts[card] or card not in PLAYABLE or card == "nope" or card in CAT_CARDS:
                continue
            targets = opponents if card == "favor" else [None]
            for target in targets:
                out.append(_action("play_card", p, card=card, target=target))
        for card in CARDS:
            if counts[card] >= 2:
                out.extend(_action("play_pair", p, card=card, target=t) for t in opponents)
            if counts[card] >= 3:
                for t in opponents:
                    out.extend(_action("play_triple", p, card=card, target=t, requested=r)
                               for r in CARDS)
        distinct = [c for c in CARDS if counts[c]]
        if len(distinct) >= 5 and state.zones["discard"]:
            from itertools import combinations
            for cards in combinations(distinct, 5):
                for retrieve in CARDS:
                    if retrieve in state.zones["discard"]:
                        out.append(_action("play_five", p, cards=cards, retrieve=retrieve))
        return out

    def _start_reaction(self, state: GameState, action: Action, cards: list[str]) -> None:
        actor = action.actor
        responders = []
        x = self._alive_after(state, actor)
        while x != actor:
            responders.append(x)
            x = self._alive_after(state, x)
        if not responders:
            self._resolve(state, action, cards)
            return
        state.phase = "reaction"
        state.pending = {
            "type": "reaction", "proposed": self.action_to_data(action)["data"],
            "cards": cards, "nope_count": 0, "responder": responders[0],
            "remaining_responders": responders[1:],
        }
        state.current_player = responders[0]

    def _advance_reaction(self, state: GameState) -> None:
        pending = state.pending
        assert pending is not None
        if pending["remaining_responders"]:
            nxt = pending["remaining_responders"].pop(0)
            pending["responder"] = nxt
            state.current_player = nxt
            return
        proposed = self.action_from_data({"schema": ACTION_SCHEMA,
                                          "data": pending["proposed"]})
        cards, count = list(pending["cards"]), pending["nope_count"]
        state.pending = None
        if count % 2:
            # Noped cards remain discarded; their effect does not occur.
            state.phase = "play"
            state.current_player = proposed.actor
        else:
            self._resolve(state, proposed, cards)

    def _finish_turn(self, state: GameState) -> None:
        actor = state.current_player
        state.players[actor]["preview"] = []
        state.turns_owed -= 1
        state.turn_number += 1
        if state.turns_owed <= 0:
            state.current_player = self._alive_after(state, actor)
            state.turns_owed = 1
        state.phase = "play"
        state.pending = None

    def _draw(self, state: GameState) -> None:
        p = state.current_player
        card = state.zones["deck"].pop()
        state.players[p]["preview"] = []
        if card != "exploding_kitten":
            state.players[p]["hand"].append(card)
            self._finish_turn(state)
            return
        hand = state.players[p]["hand"]
        if "defuse" in hand:
            hand.remove("defuse")
            state.zones["discard"].append("defuse")
            state.phase = "defuse_reinsert"
            state.pending = {"type": "defuse", "actor": p, "kitten": card}
            return
        state.zones["discard"].append(card)
        state.players[p]["alive"] = False
        alive = [x["id"] for x in state.players if x["alive"]]
        if len(alive) == 1:
            state.terminal = True
            state.winner = alive[0]
            state.phase = "terminal"
            state.pending = None
            state.current_player = alive[0]
        else:
            state.turn_number += 1
            state.current_player = self._alive_after(state, p)
            state.turns_owed = 1
            state.phase = "play"

    def _resolve(self, state: GameState, action: Action, cards: list[str]) -> None:
        p, kind = action.actor, action.type
        state.current_player = p
        state.phase = "play"
        state.pending = None
        if kind == "play_card":
            card = action.get("card")
            if card == "attack":
                state.players[p]["preview"] = []
                state.current_player = self._alive_after(state, p)
                state.turns_owed = 2
                state.turn_number += 1
            elif card == "skip":
                self._finish_turn(state)
            elif card == "favor":
                state.phase = "favor_give"
                state.pending = {"type": "favor", "actor": p, "target": action.get("target")}
                state.current_player = action.get("target")
            elif card == "shuffle":
                self._shuffle(state, state.zones["deck"])
            elif card == "see_future":
                state.players[p]["preview"] = list(reversed(state.zones["deck"][-3:]))
        elif kind == "play_pair":
            target = action.get("target")
            if state.players[target]["hand"]:
                rng = random.Random(f"{state.chance['seed']}:{state.chance['counter']}")
                state.chance["counter"] += 1
                i = rng.randrange(len(state.players[target]["hand"]))
                state.players[p]["hand"].append(state.players[target]["hand"].pop(i))
        elif kind == "play_triple":
            target, wanted = action.get("target"), action.get("requested")
            hand = state.players[target]["hand"]
            if wanted in hand:
                hand.remove(wanted)
                state.players[p]["hand"].append(wanted)
        elif kind == "play_five":
            wanted = action.get("retrieve")
            i = len(state.zones["discard"]) - 1 - state.zones["discard"][::-1].index(wanted)
            state.players[p]["hand"].append(state.zones["discard"].pop(i))

    def apply_action(self, state: GameState, action: Action) -> GameState:
        if action not in self.legal_actions(state):
            raise ValueError("illegal action")
        s = copy.deepcopy(state)
        p = action.actor
        if action.type == "draw":
            self._draw(s)
        elif action.type == "give_card":
            card = action.get("card")
            s.players[p]["hand"].remove(card)
            actor = s.pending["actor"]
            s.players[actor]["hand"].append(card)
            s.current_player = actor
            s.phase, s.pending = "play", None
        elif action.type == "reinsert":
            s.zones["deck"].insert(action.get("position"), "exploding_kitten")
            self._finish_turn(s)
        elif action.type == "play_nope":
            s.players[p]["hand"].remove("nope")
            s.zones["discard"].append("nope")
            s.pending["nope_count"] += 1
            # A NOPE can itself be NOPED: restart a full response circuit after it.
            responders = []
            x = self._alive_after(s, p)
            while x != p:
                responders.append(x)
                x = self._alive_after(s, x)
            s.pending["responder"] = responders[0]
            s.pending["remaining_responders"] = responders[1:]
            s.current_player = responders[0]
        elif action.type == "pass_nope":
            self._advance_reaction(s)
        else:
            cards = ([action.get("card")] if action.type == "play_card"
                     else list(action.get("cards")) if action.type == "play_five"
                     else [action.get("card")] * (2 if action.type == "play_pair" else 3))
            for card in cards:
                s.players[p]["hand"].remove(card)
                s.zones["discard"].append(card)
            self._start_reaction(s, action, cards)
        return s

    def action_to_name(self, action: Action) -> str:
        labels = {
            "draw": "Ziehen", "play_card": "Spielen", "play_pair": "Pärchen",
            "play_triple": "Drilling", "play_five": "Fünfling",
            "give_card": "Wunsch: Karte geben", "reinsert": "Entschärfung: wiedereinsetzen",
            "play_nope": "NÖ!", "pass_nope": "NÖ! passen",
        }
        bits = [labels[action.type], f"Spieler {action.actor}"]
        for k, v in action.args:
            bits.append(f"{k}={','.join(v) if isinstance(v, tuple) else v}")
        return " | ".join(map(str, bits))

    def name_to_action(self, name: str) -> Action:
        if type(name) is not str:
            raise ValueError("action name must be a string")
        parts = name.split(" | ")
        reverse = {
            "Ziehen": "draw", "Spielen": "play_card", "Pärchen": "play_pair",
            "Drilling": "play_triple", "Fünfling": "play_five",
            "Wunsch: Karte geben": "give_card",
            "Entschärfung: wiedereinsetzen": "reinsert",
            "NÖ!": "play_nope", "NÖ! passen": "pass_nope",
        }
        if len(parts) < 2 or parts[0] not in reverse or not parts[1].startswith("Spieler "):
            raise ValueError("invalid action name")
        actor = int(parts[1][8:])
        args = {}
        for part in parts[2:]:
            k, v = part.split("=", 1)
            if k == "target":
                args[k] = None if v == "None" else int(v)
            elif k == "position":
                args[k] = int(v)
            elif k == "cards":
                args[k] = tuple(v.split(","))
            else:
                args[k] = None if v == "None" else v
        return _action(reverse[parts[0]], actor, **args)

    def action_to_data(self, action: Action) -> dict:
        if not isinstance(action, Action) or action.type not in ACTION_TYPES:
            raise ValueError("invalid action")
        args = dict(action.args)
        if isinstance(args.get("cards"), tuple):
            args["cards"] = list(args["cards"])
        return {"schema": ACTION_SCHEMA,
                "data": {"type": action.type, "actor": action.actor, "args": args}}

    def action_from_data(self, payload: dict) -> Action:
        self._envelope(payload, ACTION_SCHEMA)
        data = payload["data"]
        if set(data) != {"type", "actor", "args"} or data["type"] not in ACTION_TYPES:
            raise ValueError("invalid action fields")
        if type(data["actor"]) is not int or type(data["args"]) is not dict:
            raise ValueError("invalid action types")
        specs = {
            "draw": set(), "play_card": {"card", "target"}, "play_pair": {"card", "target"},
            "play_triple": {"card", "target", "requested"},
            "play_five": {"cards", "retrieve"}, "give_card": {"card"},
            "reinsert": {"position"}, "play_nope": set(), "pass_nope": set(),
        }
        args = data["args"]
        if set(args) != specs[data["type"]]:
            raise ValueError("invalid action arguments")
        for k in ("card", "requested", "retrieve"):
            if k in args and args[k] not in CARDS:
                raise ValueError("invalid card")
        if "target" in args and args["target"] is not None and type(args["target"]) is not int:
            raise ValueError("invalid target")
        if "position" in args and (type(args["position"]) is not int or args["position"] < 0):
            raise ValueError("invalid position")
        if "cards" in args:
            if (type(args["cards"]) is not list or len(args["cards"]) != 5 or
                    len(set(args["cards"])) != 5 or any(c not in CARDS for c in args["cards"])):
                raise ValueError("invalid five-card combination")
            args = dict(args)
            args["cards"] = tuple(args["cards"])
        return _action(data["type"], data["actor"], **args)

    @staticmethod
    def _envelope(payload: Any, schema: str) -> None:
        if type(payload) is not dict or set(payload) != {"schema", "data"}:
            raise ValueError("invalid envelope")
        if payload["schema"] != schema or type(payload["data"]) is not dict:
            raise ValueError("invalid schema or data")

    def state_to_data(self, state: GameState) -> dict:
        data = {k: copy.deepcopy(getattr(state, k)) for k in (
            "configuration", "players", "zones", "current_player", "turns_owed",
            "phase", "pending", "terminal", "winner", "turn_number", "chance")}
        return {"schema": STATE_SCHEMA, "data": data}

    def state_from_data(self, payload: dict) -> GameState:
        self._envelope(payload, STATE_SCHEMA)
        d = copy.deepcopy(payload["data"])
        required = {"configuration", "players", "zones", "current_player", "turns_owed",
                    "phase", "pending", "terminal", "winner", "turn_number", "chance"}
        if set(d) != required:
            raise ValueError("invalid state fields")
        cfg = d["configuration"]
        if (type(cfg) is not dict or set(cfg) != {"players", "seed", "variant"} or
                type(cfg["players"]) is not int or cfg["players"] not in (2, 3, 4, 5) or
                (cfg["seed"] is not None and type(cfg["seed"]) is not int) or
                cfg["variant"] != "base"):
            raise ValueError("invalid configuration")
        if type(d["players"]) is not list or len(d["players"]) != cfg["players"]:
            raise ValueError("invalid players")
        for i, p in enumerate(d["players"]):
            if (type(p) is not dict or set(p) != {"id", "alive", "hand", "preview"} or
                    p["id"] != i or type(p["alive"]) is not bool):
                raise ValueError("invalid player")
            self._cards(p["hand"]); self._cards(p["preview"])
        z = d["zones"]
        if type(z) is not dict or set(z) != {"deck", "discard", "box"}:
            raise ValueError("invalid zones")
        for v in z.values():
            self._cards(v)
        ints = ("current_player", "turns_owed", "turn_number")
        if any(type(d[k]) is not int for k in ints) or not 0 <= d["current_player"] < cfg["players"]:
            raise ValueError("invalid state integer")
        if d["phase"] not in PHASES or type(d["terminal"]) is not bool:
            raise ValueError("invalid phase/terminal")
        if d["winner"] is not None and (type(d["winner"]) is not int or not 0 <= d["winner"] < cfg["players"]):
            raise ValueError("invalid winner")
        ch = d["chance"]
        if (type(ch) is not dict or set(ch) != {"seed", "counter"} or
                (ch["seed"] is not None and type(ch["seed"]) is not int) or
                type(ch["counter"]) is not int or ch["counter"] < 0):
            raise ValueError("invalid chance")
        self._validate_pending(d["pending"], cfg["players"])
        return GameState(**d)

    @staticmethod
    def _cards(value: Any) -> None:
        if type(value) is not list or any(c not in CARDS for c in value):
            raise ValueError("invalid card list")

    def _validate_pending(self, p: Any, n: int) -> None:
        if p is None:
            return
        if type(p) is not dict or p.get("type") not in {"reaction", "favor", "defuse"}:
            raise ValueError("invalid pending")
        if p["type"] == "favor":
            if set(p) != {"type", "actor", "target"}:
                raise ValueError("invalid favor pending")
        elif p["type"] == "defuse":
            if set(p) != {"type", "actor", "kitten"} or p["kitten"] != "exploding_kitten":
                raise ValueError("invalid defuse pending")
        else:
            if set(p) != {"type", "proposed", "cards", "nope_count", "responder", "remaining_responders"}:
                raise ValueError("invalid reaction pending")
            self.action_from_data({"schema": ACTION_SCHEMA, "data": p["proposed"]})
            self._cards(p["cards"])
            if type(p["nope_count"]) is not int or type(p["remaining_responders"]) is not list:
                raise ValueError("invalid reaction pending")
        for k in ("actor", "target", "responder"):
            if k in p and (type(p[k]) is not int or not 0 <= p[k] < n):
                raise ValueError("invalid pending player")
        if "remaining_responders" in p and any(type(x) is not int or not 0 <= x < n
                                               for x in p["remaining_responders"]):
            raise ValueError("invalid responders")

    def observation_to_data(self, state: GameState, player: int) -> dict:
        if type(player) is not int or not 0 <= player < len(state.players):
            raise ValueError("invalid player")
        pending = copy.deepcopy(state.pending)
        # Pending data contains public choices/cards already played, never hands/deck.
        data = {
            "player": player,
            "own_hand": list(state.players[player]["hand"]),
            "opponent_hand_sizes": {str(p["id"]): len(p["hand"]) for p in state.players
                                    if p["id"] != player},
            "deck_size": len(state.zones["deck"]),
            "discard": list(state.zones["discard"]),
            "alive": [p["alive"] for p in state.players],
            "current_player": state.current_player, "turns_owed": state.turns_owed,
            "phase": state.phase, "pending": pending,
            "preview": list(state.players[player]["preview"]),
            "terminal": state.terminal, "winner": state.winner,
            "turn_number": state.turn_number,
        }
        return {"schema": OBS_SCHEMA, "data": data}

    def render(self, state: GameState) -> str:
        status = "terminal" if state.terminal else f"{state.phase}, Spieler {state.current_player}"
        hands = ", ".join(f"P{p['id']}:{len(p['hand'])}{'' if p['alive'] else ' (explodiert)'}"
                          for p in state.players)
        return f"Exploding Kittens — {status}; Stapel:{len(state.zones['deck'])}; Hände {hands}"
