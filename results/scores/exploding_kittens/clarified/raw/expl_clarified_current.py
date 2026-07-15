"""BoardBench implementation derived only from rulebook.txt."""

from dataclasses import dataclass, field
import copy
import random
from typing import Any, Optional


EXPLODING = "Exploding Kitten"
DEFUSE = "Entschärfung"
SKIP = "Hops!"
ATTACK = "Angriff"
SEE = "Blick in die Zukunft"
SHUFFLE = "Mischen"
FAVOR = "Wunsch"
NOPE = "NÖ!"
CATS = (
    "Zombiekatze", "Augenmampfende",
    "Katzen-Karte (unbenannte Art 3)",
    "Katzen-Karte (unbenannte Art 4)",
    "Katzen-Karte (unbenannte Art 5)",
)
ACTION_COUNTS = {
    ATTACK: 4, SKIP: 4, FAVOR: 4, SHUFFLE: 4, SEE: 5, NOPE: 5,
    **{cat: 4 for cat in CATS},
}
TITLES = (EXPLODING, DEFUSE, ATTACK, SKIP, FAVOR, SHUFFLE, SEE, NOPE) + CATS


@dataclass
class GameState:
    hands: list[list[str]]
    deck: list[str]
    discard: list[str]
    active: int = 0
    alive: list[bool] = field(default_factory=list)
    turns_left: int = 1
    phase: str = "main"              # main, reaction, donate, insert, terminal
    pending: Optional[dict[str, Any]] = None
    reactor: Optional[int] = None
    passes: int = 0
    nope_count: int = 0
    preview_owner: Optional[int] = None
    preview: tuple[str, ...] = ()
    rng: random.Random = field(default_factory=random.Random, repr=False)


class Game:
    def __init__(self, num_players: int = 2, seed: Optional[int] = None):
        if not 2 <= num_players <= 5:
            raise ValueError("num_players must be between 2 and 5")
        self.num_players = num_players
        self.seed = seed

    def initial_state(self) -> GameState:
        rng = random.Random(self.seed)
        ordinary = [c for c, n in ACTION_COUNTS.items() for _ in range(n)]
        rng.shuffle(ordinary)
        hands = [[] for _ in range(self.num_players)]
        for p in range(self.num_players):
            hands[p] = [ordinary.pop() for _ in range(7)] + [DEFUSE]
            rng.shuffle(hands[p])
        extra_defuses = 2 if self.num_players == 2 else 6 - self.num_players
        deck = ordinary + [DEFUSE] * extra_defuses + [EXPLODING] * (self.num_players - 1)
        rng.shuffle(deck)
        return GameState(hands, deck, [], alive=[True] * self.num_players, rng=rng)

    def current_player(self, state: GameState) -> int:
        if state.phase == "terminal":
            return -1
        if state.phase == "reaction":
            assert state.reactor is not None
            return state.reactor
        if state.phase == "donate":
            return state.pending["target"]
        return state.active

    def legal_actions(self, state: GameState) -> list[str]:
        if self.is_terminal(state):
            return []
        if state.phase == "reaction":
            actions = ["Reaktion: Passen"]
            if NOPE in state.hands[state.reactor]:
                actions.append("Reaktion: NÖ!")
            return actions
        if state.phase == "donate":
            target = state.pending["target"]
            return [f"Wunsch: Karte geben: {c}" for c in sorted(set(state.hands[target]))]
        if state.phase == "insert":
            return [f"Entschärfung: Exploding Kitten an Position {i} (0=oben) legen"
                    for i in range(len(state.deck) + 1)]

        p, hand = state.active, state.hands[state.active]
        actions = ["Ziehen"]
        for card in (SKIP, ATTACK, SEE, SHUFFLE):
            if card in hand:
                actions.append(f"Spielen: {card}")
        if FAVOR in hand:
            for target in self._targets_with_cards(state, p):
                actions.append(f"Spielen: Wunsch -> Spieler {target}")

        for title in sorted(set(hand)):
            count = hand.count(title)
            if count >= 2:
                for target in self._targets_with_cards(state, p):
                    actions.append(f"Pärchen: {title} -> Spieler {target}")
            if count >= 3:
                for target in self._living_others(state, p):
                    for wanted in TITLES:
                        actions.append(f"Drilling: {title} -> Spieler {target}; Wunsch: {wanted}")

        distinct = sorted(set(hand))
        if len(distinct) >= 5:
            import itertools
            for cards in itertools.combinations(distinct, 5):
                available = sorted(set(state.discard) | set(cards))
                joined = " + ".join(cards)
                for take in available:
                    actions.append(f"Fünfling: {joined}; nehmen: {take}")
        return actions

    def apply_action(self, state: GameState, action: str) -> GameState:
        if action not in self.legal_actions(state):
            raise ValueError(f"illegal action: {action}")
        s = copy.deepcopy(state)
        if s.phase == "reaction":
            self._react(s, action)
        elif s.phase == "donate":
            card = action.split(": ", 2)[2]
            target, origin = s.pending["target"], s.active
            s.hands[target].remove(card)
            s.hands[origin].append(card)
            s.pending = None
            s.phase = "main"
        elif s.phase == "insert":
            pos = int(action.split("Position ", 1)[1].split(" ", 1)[0])
            s.deck.insert(pos, EXPLODING)
            s.pending = None
            s.phase = "main"
            self._end_one_turn(s)
        elif action == "Ziehen":
            self._draw(s)
        else:
            self._announce(s, action)
        return s

    def is_terminal(self, state: GameState) -> bool:
        return state.phase == "terminal" or sum(state.alive) == 1

    def returns(self, state: GameState) -> list[int]:
        if not self.is_terminal(state):
            return [0] * len(state.hands)
        winner = state.alive.index(True)
        return [1 if p == winner else -1 for p in range(len(state.hands))]

    def render(self, state: GameState) -> str:
        viewer = self.current_player(state)
        lines = [f"Phase: {state.phase}", f"Aktiver Spieler: {state.active}",
                 f"Am Zug/bei der Wahl: {viewer}", f"Offene Einzelzüge: {state.turns_left}",
                 f"Spielstapel: {len(state.deck)} Karten", "Ablage: " + ", ".join(state.discard)]
        for p, hand in enumerate(state.hands):
            status = "lebt" if state.alive[p] else "ausgeschieden"
            shown = ", ".join(hand) if p == viewer else f"{len(hand)} verdeckte Karten"
            lines.append(f"Spieler {p} ({status}): {shown}")
        if state.preview_owner == viewer and state.preview:
            lines.append("Private Vorschau (oben zuerst): " + ", ".join(state.preview))
        if state.pending:
            lines.append("Angekündigt: " + state.pending["name"])
        return "\n".join(lines)

    def action_to_name(self, action: str) -> str:
        if not isinstance(action, str):
            raise TypeError("actions are strings")
        return action

    def name_to_action(self, name: str) -> str:
        if not isinstance(name, str):
            raise TypeError("action names are strings")
        return name

    @staticmethod
    def _living_others(s: GameState, p: int) -> list[int]:
        return [q for q, alive in enumerate(s.alive) if alive and q != p]

    def _targets_with_cards(self, s: GameState, p: int) -> list[int]:
        return [q for q in self._living_others(s, p) if s.hands[q]]

    @staticmethod
    def _next_alive(s: GameState, p: int) -> int:
        q = (p + 1) % len(s.hands)
        while not s.alive[q]:
            q = (q + 1) % len(s.hands)
        return q

    def _end_one_turn(self, s: GameState) -> None:
        s.preview_owner, s.preview = None, ()
        if s.turns_left > 1:
            s.turns_left -= 1
        else:
            s.active = self._next_alive(s, s.active)
            s.turns_left = 1

    def _draw(self, s: GameState) -> None:
        if not s.deck:
            raise RuntimeError("rulebook guarantees the deck will not be empty")
        card = s.deck.pop(0)
        s.preview_owner, s.preview = None, ()
        if card != EXPLODING:
            s.hands[s.active].append(card)
            self._end_one_turn(s)
            return
        if DEFUSE in s.hands[s.active]:
            s.hands[s.active].remove(DEFUSE)
            s.discard.append(DEFUSE)
            s.phase = "insert"
            s.pending = {"name": "Entschärfung", "kitten": EXPLODING}
            return
        p = s.active
        s.discard.extend(s.hands[p])
        s.discard.append(EXPLODING)
        s.hands[p].clear()
        s.alive[p] = False
        if sum(s.alive) == 1:
            s.phase = "terminal"
        else:
            s.active = self._next_alive(s, p)
            s.turns_left = 1

    def _announce(self, s: GameState, action: str) -> None:
        p = s.active
        pending: dict[str, Any] = {"name": action, "origin": p}
        cards: list[str]
        if action.startswith("Spielen: Wunsch"):
            cards = [FAVOR]
            pending.update(kind="favor", target=int(action.rsplit(" ", 1)[1]))
        elif action.startswith("Spielen: "):
            card = action[len("Spielen: "):]
            cards = [card]
            pending.update(kind="single", card=card)
        elif action.startswith("Pärchen: "):
            title, target = action[len("Pärchen: "):].split(" -> Spieler ")
            cards = [title, title]
            pending.update(kind="pair", target=int(target))
        elif action.startswith("Drilling: "):
            left, wanted = action[len("Drilling: "):].split("; Wunsch: ")
            title, target = left.split(" -> Spieler ")
            cards = [title] * 3
            pending.update(kind="triple", target=int(target), wanted=wanted)
        else:
            left, take = action[len("Fünfling: "):].split("; nehmen: ")
            cards = left.split(" + ")
            pending.update(kind="five", take=take)
        for card in cards:
            s.hands[p].remove(card)
            s.discard.append(card)
        pending["cards"] = cards
        s.pending = pending
        s.phase = "reaction"
        s.reactor = self._next_alive(s, p)
        s.passes = s.nope_count = 0

    def _react(self, s: GameState, action: str) -> None:
        r = s.reactor
        if action == "Reaktion: NÖ!":
            s.hands[r].remove(NOPE)
            s.discard.append(NOPE)
            s.nope_count += 1
            s.passes = 0
        else:
            s.passes += 1
        s.reactor = self._next_alive(s, r)
        if s.passes >= sum(s.alive):
            effective = s.nope_count % 2 == 0
            pending = s.pending
            s.phase, s.reactor, s.passes, s.nope_count = "main", None, 0, 0
            if effective:
                self._resolve(s, pending)
            else:
                s.pending = None

    def _resolve(self, s: GameState, p: dict[str, Any]) -> None:
        kind = p["kind"]
        if kind == "single":
            card = p["card"]
            s.pending = None
            if card == SEE:
                s.preview_owner, s.preview = s.active, tuple(s.deck[:3])
            elif card == SHUFFLE:
                s.rng.shuffle(s.deck)
                s.preview_owner, s.preview = None, ()
            elif card == SKIP:
                self._end_one_turn(s)
            elif card == ATTACK:
                s.active = self._next_alive(s, s.active)
                s.turns_left = 2
                s.preview_owner, s.preview = None, ()
        elif kind == "favor":
            target = p["target"]
            if s.hands[target]:
                s.phase = "donate"
            else:
                s.pending = None
        elif kind == "pair":
            target = p["target"]
            if s.hands[target]:
                card = s.rng.choice(s.hands[target])
                s.hands[target].remove(card)
                s.hands[s.active].append(card)
            s.pending = None
        elif kind == "triple":
            target, wanted = p["target"], p["wanted"]
            if wanted in s.hands[target]:
                s.hands[target].remove(wanted)
                s.hands[s.active].append(wanted)
            s.pending = None
        else:
            take = p["take"]
            s.discard.remove(take)
            s.hands[s.active].append(take)
            s.pending = None
