"""Small, self-contained implementation of the supplied German rule sheet.

The sheet explicitly omits parts of the rules for Angriff, Nö!, Entschärfung
placement, and the Fünfling.  The first three nevertheless have enough text in
the overview/examples to model the behaviour below.  Fünfling is not modelled.
See ``Game.ASSUMPTIONS`` for the deliberately small gap-filling choices.
"""

from collections import Counter
from copy import deepcopy
from dataclasses import dataclass, field
import random
import re
from typing import Optional


EXPLODING = "Exploding Kitten"
DEFUSE = "Entschärfung"
ATTACK = "Angriff"
SKIP = "Hops!"
FAVOR = "Wunsch"
SHUFFLE = "Mischen"
SEE = "Blick in die Zukunft"
NOPE = "Nö!"
CAT_1 = "Zombiekatze"
CAT_2 = "Augenmampfende"
# The inventory says 56 cards and four of every cat title, but this rendering
# supplies only two of the five mathematically required cat titles.  Visible
# placeholders keep the omission explicit rather than borrowing outside names.
CAT_3 = "[fehlender Katzenkarten-Titel 1]"
CAT_4 = "[fehlender Katzenkarten-Titel 2]"
CAT_5 = "[fehlender Katzenkarten-Titel 3]"

CARD_TITLES = (
    EXPLODING, DEFUSE, ATTACK, SKIP, FAVOR, SHUFFLE, SEE, NOPE,
    CAT_1, CAT_2, CAT_3, CAT_4, CAT_5,
)
REQUESTABLE = tuple(c for c in CARD_TITLES if c != EXPLODING)


@dataclass(frozen=True)
class Action:
    kind: str
    card: str = ""
    target: int = -1
    requested: str = ""
    position: int = -1


@dataclass
class GameState:
    hands: list[list[str]]
    deck: list[str]
    discard: list[str]
    alive: list[bool]
    player: int = 0
    phase: str = "turn"             # turn, reaction, donate, exploding, place
    turns_remaining: int = 1
    pending: Optional[tuple] = None
    pending_actor: int = -1
    reaction_last_actor: int = -1
    reaction_passes: int = 0
    reaction_canceled: bool = False
    drawn_exploding: bool = False
    peek: dict[int, tuple[str, ...]] = field(default_factory=dict)
    winner: Optional[int] = None
    rng: random.Random = field(default_factory=random.Random, repr=False)


class Game:
    """Rules engine.  Card order and random steals are reproducible by seed."""

    ASSUMPTIONS = (
        "The three absent cat-card titles use explicit missing-title placeholders.",
        "An Angriff ends all of its user's currently owed turns and gives the next "
        "living player two turns; an un-Nö!'d Hops! ends exactly one owed turn.",
        "Nö! may answer a card play or another Nö!; consecutive passes by every "
        "other living player close the reaction window, and odd Nö! parity cancels.",
        "A player with no cards targeted by Wunsch gives nothing.",
        "Fünfling is omitted because its rule and combination resolution are absent.",
    )

    def __init__(self, num_players: int = 2, seed: Optional[int] = 0):
        if not 2 <= num_players <= 5:
            raise ValueError("the supplied rules allow 2–5 players")
        self.num_players = num_players
        self.seed = seed

    def initial_state(self) -> GameState:
        rng = random.Random(self.seed)
        ordinary = (
            [ATTACK] * 4 + [SKIP] * 4 + [FAVOR] * 4 + [SHUFFLE] * 4
            + [SEE] * 5 + [NOPE] * 5
            + [CAT_1] * 4 + [CAT_2] * 4 + [CAT_3] * 4
            + [CAT_4] * 4 + [CAT_5] * 4
        )
        rng.shuffle(ordinary)
        hands = [[] for _ in range(self.num_players)]
        for _ in range(7):
            for player in range(self.num_players):
                hands[player].append(ordinary.pop())
        for hand in hands:
            hand.append(DEFUSE)
            hand.sort()

        extra_defuses = 2 if self.num_players == 2 else 6 - self.num_players
        deck = ordinary + [DEFUSE] * extra_defuses + [EXPLODING] * (self.num_players - 1)
        rng.shuffle(deck)
        return GameState(hands, deck, [], [True] * self.num_players, rng=rng)

    def current_player(self, state: GameState) -> int:
        return state.player

    def legal_actions(self, state: GameState) -> list[Action]:
        if self.is_terminal(state):
            return []
        p = state.player
        hand = state.hands[p]
        if state.phase == "reaction":
            actions = [Action("reaction_pass")]
            if NOPE in hand:
                actions.append(Action("nope"))
            return actions
        if state.phase == "donate":
            # Empty targets are resolved before this phase is entered.
            return [Action("donate", card=c) for c in sorted(set(hand))]
        if state.phase == "exploding":
            actions = [Action("explode")]
            if DEFUSE in hand:
                actions.insert(0, Action("defuse"))
            return actions
        if state.phase == "place":
            n = len(state.deck)
            return [Action("place", position=i) for i in range(n + 1)]

        actions = [Action("draw")]
        counts = Counter(hand)
        opponents = [q for q, alive in enumerate(state.alive) if alive and q != p]
        for card in (SEE, SHUFFLE, SKIP, ATTACK):
            if counts[card]:
                actions.append(Action("play", card=card))
        if counts[FAVOR]:
            actions.extend(Action("favor", card=FAVOR, target=q) for q in opponents)

        # Pärchen and Drilling apply to every equal title, as the sheet states.
        for card in sorted(counts):
            if counts[card] >= 2:
                actions.extend(Action("pair", card=card, target=q) for q in opponents)
            if counts[card] >= 3:
                for q in opponents:
                    actions.extend(
                        Action("triple", card=card, target=q, requested=req)
                        for req in REQUESTABLE
                    )
        return actions

    def apply_action(self, state: GameState, action: Action) -> GameState:
        if action not in self.legal_actions(state):
            raise ValueError(f"illegal action: {self.action_to_name(action)}")
        s = deepcopy(state)
        p = s.player

        if action.kind == "draw":
            card = s.deck.pop(0)
            if card == EXPLODING:
                s.phase = "exploding"
                s.drawn_exploding = True
            else:
                s.hands[p].append(card)
                s.hands[p].sort()
                self._finish_one_turn(s, p)
        elif action.kind in ("play", "favor", "pair", "triple"):
            amount = 2 if action.kind == "pair" else 3 if action.kind == "triple" else 1
            for _ in range(amount):
                s.hands[p].remove(action.card)
                s.discard.append(action.card)
            if action.kind == "play":
                effect = (action.card,)
            elif action.kind == "favor":
                effect = (FAVOR, action.target)
            elif action.kind == "pair":
                effect = ("Pärchen", action.target)
            else:
                effect = ("Drilling", action.target, action.requested)
            self._open_reaction(s, p, effect)
        elif action.kind == "reaction_pass":
            s.reaction_passes += 1
            if s.reaction_passes >= sum(s.alive) - 1:
                self._close_reaction(s)
            else:
                s.player = self._next_alive(s, p)
        elif action.kind == "nope":
            s.hands[p].remove(NOPE)
            s.discard.append(NOPE)
            s.reaction_canceled = not s.reaction_canceled
            s.reaction_last_actor = p
            s.reaction_passes = 0
            s.player = self._next_alive(s, p)
        elif action.kind == "donate":
            actor = s.pending_actor
            s.hands[p].remove(action.card)
            s.hands[actor].append(action.card)
            s.hands[actor].sort()
            s.pending = None
            s.phase = "turn"
            s.player = actor
        elif action.kind == "defuse":
            s.hands[p].remove(DEFUSE)
            s.discard.append(DEFUSE)
            s.phase = "place"
        elif action.kind == "explode":
            s.discard.append(EXPLODING)
            s.discard.extend(s.hands[p])
            s.hands[p].clear()
            s.alive[p] = False
            s.drawn_exploding = False
            if sum(s.alive) == 1:
                s.winner = s.alive.index(True)
            else:
                s.player = self._next_alive(s, p)
                s.phase = "turn"
                s.turns_remaining = 1
        elif action.kind == "place":
            s.deck.insert(action.position, EXPLODING)
            s.drawn_exploding = False
            self._finish_one_turn(s, p)
        return s

    def _open_reaction(self, s: GameState, actor: int, effect: tuple) -> None:
        s.pending = effect
        s.pending_actor = actor
        s.reaction_last_actor = actor
        s.reaction_passes = 0
        s.reaction_canceled = False
        s.phase = "reaction"
        s.player = self._next_alive(s, actor)

    def _close_reaction(self, s: GameState) -> None:
        effect, actor, canceled = s.pending, s.pending_actor, s.reaction_canceled
        s.pending = None
        s.phase = "turn"
        s.player = actor
        if canceled:
            return
        label = effect[0]
        if label == SEE:
            s.peek[actor] = tuple(s.deck[:3])
        elif label == SHUFFLE:
            s.rng.shuffle(s.deck)
            s.peek.clear()
        elif label == SKIP:
            self._finish_one_turn(s, actor)
        elif label == ATTACK:
            s.peek.pop(actor, None)
            s.player = self._next_alive(s, actor)
            s.turns_remaining = 2
        elif label == FAVOR:
            target = effect[1]
            if s.hands[target]:
                s.phase = "donate"
                s.player = target
                s.pending_actor = actor
            else:
                s.player = actor
        elif label == "Pärchen":
            target = effect[1]
            if s.hands[target]:
                card = s.rng.choice(s.hands[target])
                s.hands[target].remove(card)
                s.hands[actor].append(card)
                s.hands[actor].sort()
        elif label == "Drilling":
            target, requested = effect[1], effect[2]
            if requested in s.hands[target]:
                s.hands[target].remove(requested)
                s.hands[actor].append(requested)
                s.hands[actor].sort()

    def _finish_one_turn(self, s: GameState, actor: int) -> None:
        s.peek.pop(actor, None)
        s.turns_remaining -= 1
        s.phase = "turn"
        if s.turns_remaining <= 0:
            s.player = self._next_alive(s, actor)
            s.turns_remaining = 1
        else:
            s.player = actor

    @staticmethod
    def _next_alive(s: GameState, player: int) -> int:
        q = (player + 1) % len(s.alive)
        while not s.alive[q]:
            q = (q + 1) % len(s.alive)
        return q

    def is_terminal(self, state: GameState) -> bool:
        return state.winner is not None

    def returns(self, state: GameState) -> list[int]:
        if state.winner is None:
            return [0] * self.num_players
        return [1 if p == state.winner else -1 for p in range(self.num_players)]

    def render(self, state: GameState) -> str:
        if self.is_terminal(state):
            return f"Spielende — Gewinner: Spieler {state.winner}; returns={self.returns(state)}"
        p = state.player
        lines = [
            f"Phase: {state.phase}; Spieler: {p}; verbleibende Züge: {state.turns_remaining}",
            f"Spielstapel: {len(state.deck)} Karten; Ablagestapel: {', '.join(state.discard) or 'leer'}",
            "Lebend: " + ", ".join(str(i) for i, alive in enumerate(state.alive) if alive),
            f"Hand von Spieler {p}: {', '.join(state.hands[p]) or 'leer'}",
            "Andere Handgrößen: " + ", ".join(
                f"{i}={len(h)}" for i, h in enumerate(state.hands) if i != p
            ),
        ]
        if p in state.peek:
            lines.append("Blick in die Zukunft: " + ", ".join(state.peek[p]))
        if state.phase == "reaction":
            lines.append(f"Reaktion auf: {state.pending}; derzeit {'aufgehoben' if state.reaction_canceled else 'aktiv'}")
        return "\n".join(lines)

    def action_to_name(self, action: Action) -> str:
        k = action.kind
        if k == "draw": return "draw"
        if k == "play": return f"play:{action.card}"
        if k == "favor": return f"play:{FAVOR}->player:{action.target}"
        if k == "pair": return f"Pärchen:{action.card}->player:{action.target}"
        if k == "triple":
            return f"Drilling:{action.card}->player:{action.target}:request:{action.requested}"
        if k == "reaction_pass": return "reaction:pass"
        if k == "nope": return f"reaction:play:{NOPE}"
        if k == "donate": return f"donate:{action.card}"
        if k == "defuse": return f"exploding:play:{DEFUSE}"
        if k == "explode": return "exploding:explode"
        if k == "place":
            return "place:top" if action.position == 0 else f"place:position:{action.position}"
        raise ValueError(f"unknown action kind: {k}")

    def name_to_action(self, name: str) -> Action:
        if name == "draw": return Action("draw")
        if name == "reaction:pass": return Action("reaction_pass")
        if name == f"reaction:play:{NOPE}": return Action("nope")
        if name == f"exploding:play:{DEFUSE}": return Action("defuse")
        if name == "exploding:explode": return Action("explode")
        if name == "place:top": return Action("place", position=0)
        m = re.fullmatch(r"place:position:(\d+)", name)
        if m: return Action("place", position=int(m.group(1)))
        if name.startswith("donate:"):
            return Action("donate", card=name[len("donate:"):])
        m = re.fullmatch(r"play:Wunsch->player:(\d+)", name)
        if m: return Action("favor", card=FAVOR, target=int(m.group(1)))
        m = re.fullmatch(r"Pärchen:(.*)->player:(\d+)", name)
        if m: return Action("pair", card=m.group(1), target=int(m.group(2)))
        m = re.fullmatch(r"Drilling:(.*)->player:(\d+):request:(.*)", name)
        if m:
            return Action("triple", card=m.group(1), target=int(m.group(2)), requested=m.group(3))
        if name.startswith("play:"):
            return Action("play", card=name[len("play:"):])
        raise ValueError(f"unknown action name: {name}")
