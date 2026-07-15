"""Source-only BoardBench implementation of the supplied German rulebook."""

import copy
import random
from dataclasses import dataclass, field
from itertools import combinations
from typing import Optional
from urllib.parse import quote, unquote


Action = tuple[str, ...]

EXPLODING = "Exploding Kitten"
DEFUSE = "Entschärfung"
ATTACK = "Angriff"
SKIP = "Hops!"
FAVOR = "Wunsch"
SHUFFLE = "Mischen"
SEE = "Blick in die Zukunft"
NOPE = "NÖ!"
CAT_1 = "Zombiekatze"
CAT_2 = "Augenmampfende"
# The source says there are 56 cards and five four-card cat types, but names only
# these two in its text extraction. These explicit placeholders are the smallest
# setup-only assumption; no outside card titles or effects are supplied.
UNNAMED_CATS = tuple(f"Katzen-Karte (unbenannt {i})" for i in range(1, 4))
CAT_TITLES = (CAT_1, CAT_2) + UNNAMED_CATS
TITLES = (EXPLODING, DEFUSE, ATTACK, SKIP, FAVOR, SHUFFLE, SEE, NOPE) + CAT_TITLES


@dataclass
class Pending:
    actor: int
    kind: str
    args: tuple[str, ...]
    responder: int
    nope_count: int = 0
    passes: int = 0


@dataclass
class GameState:
    hands: list[list[str]]
    deck: list[str]
    discard: list[str]
    alive: list[bool]
    active: int = 0
    turns_owed: int = 1
    phase: str = "turn"  # turn, reaction, donate, retrieve, defuse
    pending: Optional[Pending] = None
    chooser: Optional[int] = None
    target: Optional[int] = None
    viewed_top: tuple[str, ...] = ()
    view_owner: Optional[int] = None
    rng: random.Random = field(default_factory=random.Random, repr=False)


class Game:
    def __init__(self, num_players: int = 2, seed: Optional[int] = None):
        if not 2 <= num_players <= 5:
            raise ValueError("num_players must be between 2 and 5")
        self.num_players = num_players
        self.seed = seed

    def initial_state(self) -> GameState:
        rng = random.Random(self.seed)
        # Four Exploding Kittens and all six Entschärfungen are set aside first.
        ordinary = ([ATTACK] * 4 + [SKIP] * 4 + [FAVOR] * 4 +
                    [SHUFFLE] * 4 + [SEE] * 5 + [NOPE] * 5)
        for title in CAT_TITLES:
            ordinary += [title] * 4
        rng.shuffle(ordinary)
        hands = [[] for _ in range(self.num_players)]
        for _ in range(7):
            for hand in hands:
                hand.append(ordinary.pop())
        for hand in hands:
            hand.append(DEFUSE)
        deck = ordinary + [EXPLODING] * (self.num_players - 1)
        extra_defuses = 2 if self.num_players == 2 else 6 - self.num_players
        deck += [DEFUSE] * extra_defuses
        rng.shuffle(deck)
        return GameState(hands, deck, [], [True] * self.num_players, rng=rng)

    def current_player(self, state: GameState) -> int:
        if self.is_terminal(state):
            return -1
        if state.phase == "reaction":
            assert state.pending is not None
            return state.pending.responder
        if state.phase == "donate":
            assert state.target is not None
            return state.target
        if state.phase == "retrieve":
            assert state.chooser is not None
            return state.chooser
        return state.active

    def _others(self, state: GameState, actor: int, need_card: bool = False) -> list[int]:
        return [p for p in range(self.num_players)
                if p != actor and state.alive[p] and (not need_card or state.hands[p])]

    def legal_actions(self, state: GameState) -> list[Action]:
        if self.is_terminal(state):
            return []
        if state.phase == "reaction":
            p = self.current_player(state)
            out = [("react", "pass")]
            if NOPE in state.hands[p]:
                out.append(("react", NOPE))
            return out
        if state.phase == "donate":
            assert state.target is not None
            return [("donate", c) for c in sorted(set(state.hands[state.target]))]
        if state.phase == "retrieve":
            return [("retrieve", c) for c in sorted(set(state.discard))]
        if state.phase == "defuse":
            return [("place", str(i)) for i in range(len(state.deck) + 1)]

        p, hand = state.active, state.hands[state.active]
        out: list[Action] = [("draw",)]
        targets_with_cards = self._others(state, p, True)
        for card in (ATTACK, SKIP, SHUFFLE, SEE):
            if card in hand:
                out.append(("play", card))
        if FAVOR in hand:
            out += [("play", FAVOR, str(t)) for t in targets_with_cards]

        counts = {c: hand.count(c) for c in set(hand)}
        for title in sorted(c for c, n in counts.items() if n >= 2):
            out += [("pair", title, str(t)) for t in targets_with_cards]
        triple_targets = self._others(state, p)
        for title in sorted(c for c, n in counts.items() if n >= 3):
            for t in triple_targets:
                out += [("triple", title, str(t), wanted) for wanted in TITLES]
        distinct = sorted(counts)
        if len(distinct) >= 5:
            out += [("five",) + combo for combo in combinations(distinct, 5)]
        return out

    def apply_action(self, state: GameState, action: Action) -> GameState:
        if action not in self.legal_actions(state):
            raise ValueError(f"illegal action: {action!r}")
        s = copy.deepcopy(state)
        kind = action[0]
        if s.phase == "reaction":
            self._react(s, action)
        elif s.phase == "donate":
            card = action[1]
            assert s.target is not None and s.chooser is not None
            s.hands[s.target].remove(card)
            s.hands[s.chooser].append(card)
            self._clear_choice(s)
        elif s.phase == "retrieve":
            card = action[1]
            s.discard.remove(card)
            assert s.chooser is not None
            s.hands[s.chooser].append(card)
            self._clear_choice(s)
        elif s.phase == "defuse":
            s.deck.insert(int(action[1]), EXPLODING)
            s.phase = "turn"
            self._end_single_turn(s)
        elif kind == "draw":
            self._draw(s)
        else:
            self._announce(s, action)
        return s

    def _next_alive(self, s: GameState, p: int) -> int:
        q = (p + 1) % self.num_players
        while not s.alive[q]:
            q = (q + 1) % self.num_players
        return q

    def _announce(self, s: GameState, action: Action) -> None:
        actor, kind = s.active, action[0]
        if kind == "play":
            cards, effect, args = [action[1]], action[1], action[2:]
        elif kind == "pair":
            cards, effect, args = [action[1]] * 2, "pair", action[1:]
        elif kind == "triple":
            cards, effect, args = [action[1]] * 3, "triple", action[1:]
        else:
            cards, effect, args = list(action[1:]), "five", action[1:]
        for card in cards:
            s.hands[actor].remove(card)
            s.discard.append(card)
        s.phase = "reaction"
        s.pending = Pending(actor, effect, tuple(args), self._next_alive(s, actor))

    def _react(self, s: GameState, action: Action) -> None:
        assert s.pending is not None
        p = s.pending.responder
        if action[1] == NOPE:
            s.hands[p].remove(NOPE)
            s.discard.append(NOPE)
            s.pending.nope_count += 1
            s.pending.passes = 0
        else:
            s.pending.passes += 1
        if s.pending.passes >= sum(s.alive):
            pending = s.pending
            s.pending = None
            s.phase = "turn"
            if pending.nope_count % 2 == 0:
                self._resolve(s, pending)
            return
        s.pending.responder = self._next_alive(s, p)

    def _resolve(self, s: GameState, pending: Pending) -> None:
        actor, effect, args = pending.actor, pending.kind, pending.args
        if effect == ATTACK:
            s.viewed_top, s.view_owner = (), None
            s.active = self._next_alive(s, actor)
            s.turns_owed = 2
        elif effect == SKIP:
            self._end_single_turn(s)
        elif effect == SHUFFLE:
            s.rng.shuffle(s.deck)
        elif effect == SEE:
            s.viewed_top = tuple(s.deck[:3])
            s.view_owner = actor
        elif effect == FAVOR:
            s.phase, s.chooser, s.target = "donate", actor, int(args[0])
        elif effect == "pair":
            target = int(args[1])
            card = s.rng.choice(s.hands[target])
            s.hands[target].remove(card)
            s.hands[actor].append(card)
        elif effect == "triple":
            target, wanted = int(args[1]), args[2]
            if wanted in s.hands[target]:
                s.hands[target].remove(wanted)
                s.hands[actor].append(wanted)
        elif effect == "five":
            s.phase, s.chooser = "retrieve", actor

    def _clear_choice(self, s: GameState) -> None:
        s.phase, s.chooser, s.target = "turn", None, None

    def _draw(self, s: GameState) -> None:
        card = s.deck.pop(0)
        p = s.active
        if card != EXPLODING:
            s.hands[p].append(card)
            self._end_single_turn(s)
        elif DEFUSE in s.hands[p]:
            s.hands[p].remove(DEFUSE)
            s.discard.append(DEFUSE)
            s.phase = "defuse"
        else:
            s.discard.append(EXPLODING)
            s.discard.extend(s.hands[p])
            s.hands[p].clear()
            s.alive[p] = False
            s.viewed_top, s.view_owner = (), None
            if not self.is_terminal(s):
                s.active = self._next_alive(s, p)
                s.turns_owed = 1

    def _end_single_turn(self, s: GameState) -> None:
        s.viewed_top, s.view_owner = (), None
        if s.turns_owed > 1:
            s.turns_owed -= 1
        else:
            s.active = self._next_alive(s, s.active)
            s.turns_owed = 1

    def is_terminal(self, state: GameState) -> bool:
        return sum(state.alive) == 1

    def returns(self, state: GameState) -> list[int]:
        if not self.is_terminal(state):
            return [0] * self.num_players
        return [1 if alive else -1 for alive in state.alive]

    def render(self, state: GameState) -> str:
        lines = [f"phase={state.phase} active=player:{state.active} owed={state.turns_owed}",
                 f"deck={len(state.deck)} discard={state.discard}"]
        viewer = self.current_player(state)
        for p, hand in enumerate(state.hands):
            shown = hand if p == viewer else ["?" for _ in hand]
            lines.append(f"player:{p} {'alive' if state.alive[p] else 'eliminated'} hand={shown}")
        if state.view_owner == viewer:
            lines.append(f"Blick in die Zukunft={list(state.viewed_top)}")
        return "\n".join(lines)

    def action_to_name(self, action: Action) -> str:
        safe = " !ÄÖÜäöüß"
        head = action[0]
        if len(action) == 1:
            return head
        return head + ":" + "|".join(quote(x, safe=safe) for x in action[1:])

    def name_to_action(self, name: str) -> Action:
        if ":" not in name:
            return (name,)
        head, rest = name.split(":", 1)
        return (head,) + tuple(unquote(x) for x in rest.split("|"))
