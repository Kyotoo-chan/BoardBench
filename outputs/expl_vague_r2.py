"""Small, self-contained implementation of the supplied German rule sheet.

Only labels and rules present in rulebook.txt are used.  The few places where
that sheet is deliberately vague are called out next to the relevant code.
"""

from copy import deepcopy
from dataclasses import dataclass, field
import random
from typing import Any, Optional


EXPLODING = "Exploding Kitten"
DEFUSE = "Entschärfung"
SKIP = "Hops!"
ATTACK = "Angriff"
SEE = "Blick in die Zukunft"
SHUFFLE = "Mischen"
FAVOR = "Wunsch"
NOPE = "Nö!"
ZOMBIE = "Zombiekatze"
EYE = "Augenmampfende"

# These are the only card quantities/titles legible in the supplied source.
CARD_COUNTS = {
    ATTACK: 4,
    SKIP: 4,
    ZOMBIE: 4,
    EYE: 4,
    FAVOR: 4,
    SHUFFLE: 4,
    SEE: 5,
    NOPE: 5,
}


@dataclass
class GameState:
    hands: list[list[str]]
    deck: list[str]                 # index 0 is the top
    discard: list[str]
    alive: list[bool]
    player: int = 0
    turns_due: int = 1
    phase: str = "turn"             # turn, reaction, donate, defuse, terminal
    pending: Optional[dict[str, Any]] = None
    responder: Optional[int] = None
    reaction_passes: int = 0
    known_top: list[list[str]] = field(default_factory=list)
    rng_state: object = None


class Game:
    """Exploding Kittens NSFW Edition, as described by the supplied sheet."""

    def __init__(self, num_players: int = 2, seed: Optional[int] = 0):
        # The source gives exact Exploding Kitten counts only for 2, 3 and 4.
        if num_players not in (2, 3, 4):
            raise ValueError("the supplied rules support exactly 2, 3, or 4 players")
        self.num_players = num_players
        self.seed = seed

    def initial_state(self) -> GameState:
        rng = random.Random(self.seed)
        pool = [card for card, count in CARD_COUNTS.items() for _ in range(count)]
        rng.shuffle(pool)
        hands = [[DEFUSE] for _ in range(self.num_players)]
        # "So starten alle mit 8 Karten": one Entschärfung plus seven dealt.
        for _ in range(7):
            for hand in hands:
                hand.append(pool.pop())
        # The general setup does not quantify deck Entschärfung; the only exact
        # instruction says to shuffle two in, so that is used for every supported
        # player count.  Two-player uses 2 kittens; 3/4 use players-1.
        kittens = 2 if self.num_players == 2 else self.num_players - 1
        deck = pool + [DEFUSE] * 2 + [EXPLODING] * kittens
        rng.shuffle(deck)
        return GameState(
            hands=hands,
            deck=deck,
            discard=[],
            alive=[True] * self.num_players,
            known_top=[[] for _ in range(self.num_players)],
            rng_state=rng.getstate(),
        )

    def current_player(self, state: GameState) -> int:
        if self.is_terminal(state):
            return -1
        if state.phase == "reaction":
            assert state.responder is not None
            return state.responder
        if state.phase == "donate":
            return int(state.pending["target"])
        return state.player

    def legal_actions(self, state: GameState) -> list[str]:
        if self.is_terminal(state):
            return []
        if state.phase == "reaction":
            p = state.responder
            actions = [f"reaction:pass:player-{p}"]
            # Nö! cancels a Mitspieler action. Once a Nö! exists, its owner is
            # the relevant actor, so the original player may answer with DOCH!.
            opposed_player = state.pending.get("nope_owner", state.pending["actor"])
            if NOPE in state.hands[p] and p != opposed_player:
                actions.append(f"reaction:{NOPE}:player-{p}")
            return actions
        if state.phase == "donate":
            target = int(state.pending["target"])
            return [f"{FAVOR}:give:{c}" for c in sorted(set(state.hands[target]))]
        if state.phase == "defuse":
            return [f"{DEFUSE}:insert-{EXPLODING}:position:{i}" for i in range(len(state.deck) + 1)]

        p = state.player
        hand = state.hands[p]
        actions = ["Passen/ziehen"]
        for card in (SKIP, ATTACK, SEE, SHUFFLE):
            if card in hand:
                actions.append(f"spielen:{card}")
        if FAVOR in hand:
            for target in self._other_alive(state, p):
                actions.append(f"spielen:{FAVOR}:target:player-{target}")

        counts = {c: hand.count(c) for c in set(hand)}
        for card in sorted(c for c, n in counts.items() if n >= 2):
            for target in self._other_alive(state, p):
                actions.append(f"Pärchen:{card}:target:player-{target}")
        for card in sorted(c for c, n in counts.items() if n >= 3):
            for target in self._other_alive(state, p):
                for requested in sorted(CARD_COUNTS.keys() | {DEFUSE}):
                    actions.append(f"Drilling:{card}:target:player-{target}:request:{requested}")

        # "hinreichend verschiedene" is not quantified.  The heading Fünfling
        # is taken to mean exactly five distinct titles. Exploding Kitten is not
        # retrievable: the sheet says it must immediately be shown when drawn.
        if len(counts) >= 5:
            distinct = sorted(counts)
            for chosen in self._combinations(distinct, 5):
                for retrieve in sorted(set(state.discard) - {EXPLODING}):
                    actions.append(f"Fünfling:{'+'.join(chosen)}:retrieve:{retrieve}")
        return actions

    def apply_action(self, state: GameState, action: str) -> GameState:
        if action not in self.legal_actions(state):
            raise ValueError(f"illegal action: {action}")
        s = deepcopy(state)
        if s.phase == "reaction":
            self._apply_reaction(s, action)
        elif s.phase == "donate":
            card = action.split(":give:", 1)[1]
            target = int(s.pending["target"])
            actor = int(s.pending["actor"])
            s.hands[target].remove(card)
            s.hands[actor].append(card)
            s.pending = None
            s.phase = "turn"
        elif s.phase == "defuse":
            pos = int(action.rsplit(":", 1)[1])
            s.hands[s.player].remove(DEFUSE)
            s.discard.append(DEFUSE)
            s.deck.insert(pos, EXPLODING)
            s.pending = None
            s.phase = "turn"
            self._finish_one_turn(s)
        elif action == "Passen/ziehen":
            self._draw(s)
        else:
            self._begin_play(s, action)
        if sum(s.alive) == 1:
            s.phase = "terminal"
            s.pending = None
            s.responder = None
        return s

    def is_terminal(self, state: GameState) -> bool:
        return sum(state.alive) <= 1

    def returns(self, state: GameState) -> list[int]:
        if not self.is_terminal(state):
            return [0] * self.num_players
        return [1 if alive else -1 for alive in state.alive]

    def action_to_name(self, action: str) -> str:
        if not isinstance(action, str):
            raise TypeError("actions are stable string names")
        return action

    def name_to_action(self, name: str) -> str:
        if not isinstance(name, str):
            raise TypeError("action names are strings")
        return name

    def render(self, state: GameState) -> str:
        lines = [
            f"phase={state.phase} current_player={self.current_player(state)}",
            f"deck={len(state.deck)} discard=[{', '.join(state.discard)}]",
        ]
        viewer = self.current_player(state)
        for p, hand in enumerate(state.hands):
            status = "alive" if state.alive[p] else "exploded"
            if p == viewer:
                lines.append(f"player-{p} ({status}) hand=[{', '.join(sorted(hand))}]")
            else:
                lines.append(f"player-{p} ({status}) hand=<hidden:{len(hand)} cards>")
            if p == viewer and state.known_top[p]:
                lines.append(f"player-{p} knows top=[{', '.join(state.known_top[p])}]")
        if state.phase == "turn":
            lines.append(f"turns_due={state.turns_due}")
        if state.pending:
            lines.append(f"pending={state.pending}")
        return "\n".join(lines)

    def _begin_play(self, s: GameState, action: str) -> None:
        p = s.player
        if action.startswith("spielen:"):
            rest = action[len("spielen:"):]
            card = rest.split(":target:", 1)[0]
            cards = [card]
            effect: dict[str, Any] = {"kind": card, "actor": p}
            if ":target:player-" in rest:
                effect["target"] = int(rest.rsplit("player-", 1)[1])
        elif action.startswith("Pärchen:"):
            middle, target_text = action[len("Pärchen:"):].split(":target:player-")
            cards = [middle, middle]
            effect = {"kind": "Pärchen", "actor": p, "target": int(target_text)}
        elif action.startswith("Drilling:"):
            middle, tail = action[len("Drilling:"):].split(":target:player-")
            target_text, requested = tail.split(":request:", 1)
            cards = [middle] * 3
            effect = {"kind": "Drilling", "actor": p, "target": int(target_text), "request": requested}
        else:
            body = action[len("Fünfling:"):]
            card_text, retrieve = body.split(":retrieve:", 1)
            cards = card_text.split("+")
            effect = {"kind": "Fünfling", "actor": p, "retrieve": retrieve}
        for card in cards:
            s.hands[p].remove(card)
            s.discard.append(card)
        effect["canceled"] = False
        s.pending = effect
        s.phase = "reaction"
        s.reaction_passes = 0
        # The sheet permits Nö! out of turn but supplies no simultaneous timing.
        # Use a clockwise response window, starting after the acting player; each
        # Nö! resets the window so another Nö! can make a DOCH!.
        s.responder = self._next_alive(s, p)

    def _apply_reaction(self, s: GameState, action: str) -> None:
        p = s.responder
        if action.startswith(f"reaction:{NOPE}:"):
            s.hands[p].remove(NOPE)
            s.discard.append(NOPE)
            s.pending["canceled"] = not s.pending["canceled"]
            s.pending["nope_owner"] = p
            s.reaction_passes = 0
        else:
            s.reaction_passes += 1
        s.responder = self._next_alive(s, p)
        if s.reaction_passes >= sum(s.alive):
            effect = s.pending
            s.pending = None
            s.responder = None
            s.phase = "turn"
            if not effect["canceled"]:
                self._resolve_effect(s, effect)

    def _resolve_effect(self, s: GameState, effect: dict[str, Any]) -> None:
        kind = effect["kind"]
        actor = effect["actor"]
        if kind == SKIP:
            self._finish_one_turn(s)
        elif kind == ATTACK:
            # "verlagert oder erweitert ... angemessen" is vague.  We transfer
            # unfinished attacked turns and add the stated two new turns.
            remaining = s.turns_due - 1
            target = self._next_alive(s, actor)
            s.player = target
            s.turns_due = remaining + 2
        elif kind == SEE:
            s.known_top[actor] = s.deck[:3]
        elif kind == SHUFFLE:
            rng = self._rng(s)
            rng.shuffle(s.deck)
            s.rng_state = rng.getstate()
            s.known_top = [[] for _ in s.known_top]
        elif kind == FAVOR:
            target = effect["target"]
            if s.hands[target]:
                s.pending = effect
                s.phase = "donate"
        elif kind == "Pärchen":
            target = effect["target"]
            if s.hands[target]:
                rng = self._rng(s)
                i = rng.randrange(len(s.hands[target]))
                s.hands[actor].append(s.hands[target].pop(i))
                s.rng_state = rng.getstate()
        elif kind == "Drilling":
            target, requested = effect["target"], effect["request"]
            if requested in s.hands[target]:
                s.hands[target].remove(requested)
                s.hands[actor].append(requested)
        elif kind == "Fünfling":
            card = effect["retrieve"]
            s.discard.remove(card)
            s.hands[actor].append(card)

    def _draw(self, s: GameState) -> None:
        if not s.deck:
            # The sheet asserts this cannot occur; retaining an explicit guard
            # makes malformed externally-created states fail clearly.
            raise RuntimeError("Spielstapel unexpectedly empty")
        card = s.deck.pop(0)
        s.known_top = [[] for _ in s.known_top]
        if card != EXPLODING:
            s.hands[s.player].append(card)
            self._finish_one_turn(s)
        elif DEFUSE in s.hands[s.player]:
            s.phase = "defuse"
            s.pending = {"kind": EXPLODING}
        else:
            s.discard.extend(s.hands[s.player])
            s.discard.append(EXPLODING)
            s.hands[s.player].clear()
            s.alive[s.player] = False
            if sum(s.alive) > 1:
                s.player = self._next_alive(s, s.player)
                s.turns_due = 1

    def _finish_one_turn(self, s: GameState) -> None:
        s.turns_due -= 1
        if s.turns_due <= 0:
            s.player = self._next_alive(s, s.player)
            s.turns_due = 1

    @staticmethod
    def _other_alive(s: GameState, p: int) -> list[int]:
        return [q for q, alive in enumerate(s.alive) if alive and q != p]

    @staticmethod
    def _next_alive(s: GameState, p: int) -> int:
        q = (p + 1) % len(s.alive)
        while not s.alive[q]:
            q = (q + 1) % len(s.alive)
        return q

    @staticmethod
    def _combinations(items: list[str], size: int) -> list[tuple[str, ...]]:
        if size == 0:
            return [()]
        if len(items) < size:
            return []
        return [(items[0],) + tail for tail in Game._combinations(items[1:], size - 1)] + Game._combinations(items[1:], size)

    @staticmethod
    def _rng(s: GameState) -> random.Random:
        rng = random.Random()
        rng.setstate(s.rng_state)
        return rng
