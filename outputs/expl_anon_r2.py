"""A compact, source-bound implementation of the supplied German rulebook.

The source names only ``Symbolkarte A`` and ``Symbolkarte B`` while its component
total and "4 jeder art" imply three further four-card arts.  The stable explicit
placeholders ``Symbolkarte (unbenannte Art 1..3)`` preserve that unresolved gap
without assigning invented effects.  Reaction timing is also unspecified; the
explicit reaction window below gives other living players clockwise chances to
play ``Widerspruch``.  A Widerspruch starts a fresh clockwise response round.
"""

from dataclasses import dataclass, field
import random
from typing import Dict, List, Optional


GEFAHR = "Gefahrenkarte"
SCHUTZ = "Schutzkarte"
CARDS = (
    GEFAHR, SCHUTZ, "Doppelzug", "Überspringen", "Auswahl", "Neuordnen",
    "Vorschau", "Widerspruch", "Symbolkarte A", "Symbolkarte B",
    "Symbolkarte (unbenannte Art 1)", "Symbolkarte (unbenannte Art 2)",
    "Symbolkarte (unbenannte Art 3)",
)
PLAYABLE = ("Doppelzug", "Überspringen", "Neuordnen", "Vorschau",
            "Symbolkarte A", "Symbolkarte B", "Symbolkarte (unbenannte Art 1)",
            "Symbolkarte (unbenannte Art 2)", "Symbolkarte (unbenannte Art 3)")


@dataclass
class Pending:
    kind: str
    actor: int
    payload: Dict[str, object] = field(default_factory=dict)
    cancelled: bool = False
    responders: List[int] = field(default_factory=list)


@dataclass
class GameState:
    hands: List[List[str]]
    deck: List[str]                 # index 0 is the top
    discard: List[str]
    alive: List[bool]
    player: int = 0
    turns_left: int = 1
    phase: str = "turn"            # turn, reaction, donate, danger
    pending: Optional[Pending] = None
    donate_actor: Optional[int] = None
    knowledge: List[List[str]] = field(default_factory=list)
    rng: random.Random = field(default_factory=random.Random, repr=False)


class Game:
    def __init__(self, num_players: int = 2, seed: Optional[int] = 0):
        if not 2 <= num_players <= 5:
            raise ValueError("the rulebook supports 2–5 players")
        self.num_players = num_players
        self.seed = seed

    def initial_state(self) -> GameState:
        rng = random.Random(self.seed)
        pool = (["Doppelzug"] * 4 + ["Überspringen"] * 4 + ["Auswahl"] * 4
                + ["Neuordnen"] * 4 + ["Vorschau"] * 5
                + ["Widerspruch"] * 5 + ["Symbolkarte A"] * 4
                + ["Symbolkarte B"] * 4
                + ["Symbolkarte (unbenannte Art 1)"] * 4
                + ["Symbolkarte (unbenannte Art 2)"] * 4
                + ["Symbolkarte (unbenannte Art 3)"] * 4)
        rng.shuffle(pool)
        hands = [[] for _ in range(self.num_players)]
        for _ in range(7):
            for p in range(self.num_players):
                if not pool:
                    raise ValueError("supplied card labels do not support this setup")
                hands[p].append(pool.pop(0))
        for hand in hands:
            hand.append(SCHUTZ)

        # For two players the source explicitly says to add only two of the
        # remaining Schutzkarte.  Otherwise all remaining ones are added.
        extra_schutz = 2 if self.num_players == 2 else 6 - self.num_players
        deck = pool + [SCHUTZ] * extra_schutz + [GEFAHR] * (self.num_players - 1)
        rng.shuffle(deck)
        return GameState(hands, deck, [], [True] * self.num_players,
                         knowledge=[[] for _ in range(self.num_players)], rng=rng)

    def current_player(self, state: GameState) -> int:
        if self.is_terminal(state):
            return -1
        if state.phase == "reaction" and state.pending and state.pending.responders:
            return state.pending.responders[0]
        return state.player

    @staticmethod
    def _counts(hand: List[str]) -> Dict[str, int]:
        return {c: hand.count(c) for c in set(hand)}

    def legal_actions(self, state: GameState) -> List[str]:
        if self.is_terminal(state):
            return []
        if state.phase == "reaction":
            p = self.current_player(state)
            actions = ["pass:Widerspruch"]
            if "Widerspruch" in state.hands[p]:
                actions.append("play:Widerspruch")
            return actions
        if state.phase == "danger":
            if SCHUTZ not in state.hands[state.player]:
                return []  # unreachable: an unprotected draw explodes immediately
            return [f"play:{SCHUTZ}:place:{i}" for i in range(len(state.deck) + 1)]
        if state.phase == "donate":
            # Card identity, rather than a silently selected physical copy, is
            # the meaningful choice when copies have identical titles/effects.
            return [f"donate:{c}" for c in sorted(set(state.hands[state.player]))]

        p, hand = state.player, state.hands[state.player]
        actions = ["draw"]
        counts = self._counts(hand)
        for card in PLAYABLE:
            if counts.get(card, 0):
                actions.append(f"play:{card}")
        for target in self._other_alive(state, p):
            if counts.get("Auswahl", 0):
                actions.append(f"play:Auswahl->player:{target}")
            for card in sorted(c for c, n in counts.items() if n >= 2):
                actions.append(f"pärchen:{card}->player:{target}")
            for card in sorted(c for c, n in counts.items() if n >= 3):
                for wanted in CARDS:
                    actions.append(f"drilling:{card}->player:{target}:request:{wanted}")

        distinct = sorted(counts)
        if len(distinct) >= 5:
            # Every five-title selection is explicit.  This small recursive
            # helper avoids importing a non-standard combinatorics dependency.
            from itertools import combinations
            for chosen in combinations(distinct, 5):
                chosen_text = "|".join(chosen)
                discard_choices = sorted(set(state.discard) | set(chosen))
                for wanted in discard_choices:
                    actions.append(f"fünfling:{chosen_text}:take:{wanted}")
        return actions

    def apply_action(self, state: GameState, action: str) -> GameState:
        if action not in self.legal_actions(state):
            raise ValueError(f"illegal action: {action}")
        if state.phase == "reaction":
            self._react(state, action)
        elif state.phase == "danger":
            pos = int(action.rsplit(":", 1)[1])
            state.hands[state.player].remove(SCHUTZ)
            state.discard.append(SCHUTZ)
            state.deck.insert(pos, GEFAHR)
            state.phase = "turn"
            self._finish_one_turn(state)
        elif state.phase == "donate":
            card = action[len("donate:"):]
            donor, receiver = state.player, state.donate_actor
            state.hands[donor].remove(card)
            state.hands[receiver].append(card)  # type: ignore[index]
            state.player = receiver  # type: ignore[assignment]
            state.donate_actor = None
            state.phase = "turn"
        elif action == "draw":
            self._draw(state)
        else:
            self._begin_play(state, action)
        return state

    def _begin_play(self, state: GameState, action: str) -> None:
        p = state.player
        payload: Dict[str, object] = {}
        if action.startswith("play:Auswahl->player:"):
            kind, cards = "Auswahl", ["Auswahl"]
            payload["target"] = int(action.rsplit(":", 1)[1])
        elif action.startswith("pärchen:"):
            left, target = action.split("->player:")
            card = left[len("pärchen:"):]
            kind, cards = "pärchen", [card, card]
            payload["target"] = int(target)
        elif action.startswith("drilling:"):
            left, rest = action.split("->player:")
            target, wanted = rest.split(":request:")
            card = left[len("drilling:"):]
            kind, cards = "drilling", [card] * 3
            payload.update(target=int(target), wanted=wanted)
        elif action.startswith("fünfling:"):
            chosen, wanted = action[len("fünfling:"):].split(":take:")
            kind, cards = "fünfling", chosen.split("|")
            payload["wanted"] = wanted
        else:
            kind = action[len("play:"):]
            cards = [kind]
        for card in cards:
            state.hands[p].remove(card)
            state.discard.append(card)
        pending = Pending(kind, p, payload)
        pending.responders = self._clockwise(state, p, include_start=False)
        state.pending = pending
        if pending.responders:
            state.phase = "reaction"
        else:
            self._resolve_pending(state)

    def _react(self, state: GameState, action: str) -> None:
        pending = state.pending
        assert pending is not None
        responder = pending.responders.pop(0)
        if action == "play:Widerspruch":
            state.hands[responder].remove("Widerspruch")
            state.discard.append("Widerspruch")
            pending.cancelled = not pending.cancelled
            pending.responders = self._clockwise(state, responder, include_start=False)
        if not pending.responders:
            self._resolve_pending(state)

    def _resolve_pending(self, state: GameState) -> None:
        pending = state.pending
        assert pending is not None
        state.pending = None
        state.phase = "turn"
        state.player = pending.actor
        if pending.cancelled:
            return
        kind, p, data = pending.kind, pending.actor, pending.payload
        if kind == "Doppelzug":
            state.player = self._next_alive(state, p)
            state.turns_left = 2
        elif kind == "Überspringen":
            self._finish_one_turn(state)
        elif kind == "Neuordnen":
            state.rng.shuffle(state.deck)
            state.knowledge = [[] for _ in state.knowledge]
        elif kind == "Vorschau":
            state.knowledge[p] = list(state.deck[:3])
        elif kind == "Auswahl":
            target = int(data["target"])
            if state.hands[target]:
                state.phase, state.player, state.donate_actor = "donate", target, p
        elif kind == "pärchen":
            target = int(data["target"])
            if state.hands[target]:
                card = state.rng.choice(state.hands[target])
                state.hands[target].remove(card)
                state.hands[p].append(card)
        elif kind == "drilling":
            target, wanted = int(data["target"]), str(data["wanted"])
            if wanted in state.hands[target]:
                state.hands[target].remove(wanted)
                state.hands[p].append(wanted)
        elif kind == "fünfling":
            wanted = str(data["wanted"])
            # Take the most recently discarded copy, which is explicit and
            # deterministic where physically identical copies exist.
            idx = len(state.discard) - 1 - state.discard[::-1].index(wanted)
            state.hands[p].append(state.discard.pop(idx))
        # Symbol cards have no individual effect.

    def _draw(self, state: GameState) -> None:
        if not state.deck:
            # The source asserts this cannot happen.  Keep the unresolved breach
            # explicit instead of inventing a reshuffle or winner rule.
            raise RuntimeError("rulebook-declared impossible empty Spielstapel")
        p = state.player
        card = state.deck.pop(0)
        state.knowledge = [[] for _ in state.knowledge]
        if card != GEFAHR:
            state.hands[p].append(card)
            self._finish_one_turn(state)
        elif SCHUTZ in state.hands[p]:
            state.phase = "danger"
        else:
            state.discard.extend(state.hands[p])
            state.hands[p].clear()
            state.discard.append(GEFAHR)
            state.alive[p] = False
            if not self.is_terminal(state):
                state.player = self._next_alive(state, p)
                state.turns_left = 1
                state.phase = "turn"

    def _finish_one_turn(self, state: GameState) -> None:
        if state.turns_left > 1:
            state.turns_left -= 1
        else:
            state.player = self._next_alive(state, state.player)
            state.turns_left = 1

    def _other_alive(self, state: GameState, p: int) -> List[int]:
        return [q for q in self._clockwise(state, p, False) if q != p]

    def _clockwise(self, state: GameState, start: int,
                   include_start: bool) -> List[int]:
        result = []
        first = 0 if include_start else 1
        for step in range(first, self.num_players + (0 if include_start else 0)):
            q = (start + step) % self.num_players
            if state.alive[q] and (include_start or q != start):
                result.append(q)
        return result

    def _next_alive(self, state: GameState, p: int) -> int:
        for step in range(1, self.num_players + 1):
            q = (p + step) % self.num_players
            if state.alive[q]:
                return q
        return p

    def is_terminal(self, state: GameState) -> bool:
        return sum(state.alive) == 1

    def returns(self, state: GameState) -> List[int]:
        if not self.is_terminal(state):
            return [0] * self.num_players
        return [1 if alive else -1 for alive in state.alive]

    def render(self, state: GameState) -> str:
        current = self.current_player(state)
        lines = [f"phase={state.phase} current_player={current}",
                 f"Spielstapel={len(state.deck)} Ablagestapel={state.discard}"]
        for p, hand in enumerate(state.hands):
            shown = sorted(hand) if p == current else [f"{len(hand)} cards"]
            lines.append(f"player {p} {'alive' if state.alive[p] else 'dead'}: {shown}")
        if current >= 0 and state.knowledge[current]:
            lines.append(f"Vorschau={state.knowledge[current]}")
        if state.turns_left > 1:
            lines.append(f"remaining turns={state.turns_left}")
        return "\n".join(lines)

    def action_to_name(self, action: str) -> str:
        return action

    def name_to_action(self, name: str) -> str:
        return name
