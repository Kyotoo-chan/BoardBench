"""Self-contained executable model of the supplied 4--5 player base game.

Cards in ``deck`` and opponents' ``hands`` are private information in a physical
game.  They are present in GameState so that one object can referee the game;
``render`` hides them.
"""
from dataclasses import dataclass, field
import json
import random
from typing import Optional


BEANS = {
    "Gartenbohne": (6, ((2, 2), (3, 3))),
    "Rote Bohne": (8, ((2, 1), (3, 2), (4, 3), (5, 4))),
    "Augenbohne": (10, ((2, 1), (4, 2), (5, 3), (6, 4))),
    "Sojabohne": (12, ((2, 1), (4, 2), (6, 3), (7, 4))),
    "Brechbohne": (14, ((3, 1), (5, 2), (6, 3), (7, 4))),
    "Saubohne": (16, ((3, 1), (5, 2), (7, 3), (8, 4))),
    "Feuerbohne": (18, ((3, 1), (6, 2), (8, 3), (9, 4))),
    "Blaue Bohne": (20, ((4, 1), (6, 2), (8, 3), (10, 4))),
}


@dataclass
class GameState:
    players: int
    hands: list[list[str]]
    fields: list[list[list[str]]]
    coins: list[int]
    deck: list[str]
    discard: list[str] = field(default_factory=list)
    active: int = 0
    phase: int = 1
    planted_from_hand: int = 0
    exposed: list[str] = field(default_factory=list)
    pending: list[list[str]] = field(default_factory=list)
    empty_count: int = 0
    end_after_phase3: bool = False
    terminal: bool = False
    winner: Optional[int] = None


class Game:
    """The 4--5 player Grundspiel. Default setup is four players."""

    def __init__(self, players: int = 4, seed: int = 0):
        if players not in (4, 5):
            raise ValueError("Grundspiel condition requires 4 or 5 players")
        self.players, self.seed = players, seed

    def initial_state(self) -> GameState:
        deck = [b for b, (n, _) in BEANS.items() for _ in range(n)]
        random.Random(self.seed).shuffle(deck)
        hands = [[] for _ in range(self.players)]
        for _ in range(5):
            for hand in hands:
                hand.append(deck.pop())
        return GameState(self.players, hands,
                         [[[], []] for _ in range(self.players)],
                         [0] * self.players, deck,
                         pending=[[] for _ in range(self.players)])

    def current_player(self, state: GameState) -> int:
        return state.active

    @staticmethod
    def _harvestable(s: GameState, p: int, f: int) -> bool:
        field = s.fields[p][f]
        if not field:
            return False
        return len(field) != 1 or not any(len(x) > 1 for x in s.fields[p])

    def legal_actions(self, s: GameState) -> list[tuple]:
        if s.terminal:
            return []
        a: list[tuple] = [("Ernten", p, f) for p in range(s.players)
                          for f in range(2) if self._harvestable(s, p, f)]
        p = s.active
        if s.phase == 1:
            if not s.hands[p] or s.planted_from_hand == 2:
                a.append(("Phase 1 beenden",))
            else:
                bean = s.hands[p][0]
                for f in range(2):
                    fld = s.fields[p][f]
                    if not fld or fld[0] == bean:
                        a.append(("Vorderste Handkarte anbauen", f))
                if s.planted_from_hand == 1:
                    a.append(("Phase 1 beenden",))
        elif s.phase == 2:
            if not s.exposed:
                a.append(("Zwei Bohnenkarten aufdecken",))
            else:
                # Atomic actions represent a proposal accepted by both players.
                # Single-card exchanges, gifts, and the sourced two-for-one form.
                for q in range(s.players):
                    if q == p:
                        continue
                    for src, cards in (("aufgedeckt", s.exposed), ("Hand", s.hands[p])):
                        for i, bean in enumerate(cards):
                            a.append(("Bohnenkarte schenken", q, src, i, bean))
                            for j, wanted in enumerate(s.hands[q]):
                                a.append(("Bohnenhandel", q, src, i, bean, j, wanted))
                    pool = [("aufgedeckt", i, b) for i, b in enumerate(s.exposed)] + [("Hand", i, b) for i, b in enumerate(s.hands[p])]
                    for x in range(len(pool)):
                        for y in range(x + 1, len(pool)):
                            for j, wanted in enumerate(s.hands[q]):
                                a.append(("Bohnenhandel 2 gegen 1", q, pool[x], pool[y], j, wanted))
                a.append(("Handel beenden",))
        elif s.phase == 3:
            owners = [q for q in range(s.players) if s.pending[q] or (q == p and s.exposed)]
            if not owners:
                a.append(("Phase 3 beenden",))
            else:
                q = owners[0]
                bean = s.pending[q][0] if s.pending[q] else s.exposed[0]
                for f in range(2):
                    fld = s.fields[q][f]
                    if not fld or fld[0] == bean:
                        a.append(("Neue Bohnenkarte anbauen", q, f, bean))
        else:
            a.append(("Drei Bohnenkarten nachziehen",))
        return a

    def _harvest(self, s: GameState, p: int, f: int) -> None:
        cards = s.fields[p][f]
        reward = 0
        for threshold, coins in BEANS[cards[0]][1]:
            if len(cards) >= threshold:
                reward = coins
        s.coins[p] += reward
        s.discard.extend(cards[reward:])
        s.fields[p][f] = []

    def _draw(self, s: GameState) -> Optional[str]:
        if not s.deck:
            return None
        card = s.deck.pop()
        if not s.deck:
            s.empty_count += 1
            if s.empty_count < 3:
                random.Random(self.seed + s.empty_count).shuffle(s.discard)
                s.deck, s.discard = s.discard, []
        return card

    def _finish(self, s: GameState) -> None:
        for p in range(s.players):
            for f in range(2):
                if s.fields[p][f]:
                    self._harvest(s, p, f)
        best = max(s.coins)
        tied = [p for p, c in enumerate(s.coins) if c == best]
        # clockwise farthest from start player 0
        s.winner = max(tied)
        s.terminal = True

    def apply_action(self, s: GameState, action: tuple) -> GameState:
        if action not in self.legal_actions(s):
            raise ValueError("illegal action")
        kind = action[0]
        if kind == "Ernten":
            self._harvest(s, action[1], action[2]); return s
        p = s.active
        if kind == "Vorderste Handkarte anbauen":
            s.fields[p][action[1]].append(s.hands[p].pop(0)); s.planted_from_hand += 1
        elif kind == "Phase 1 beenden":
            s.phase = 2; s.planted_from_hand = 0
        elif kind == "Zwei Bohnenkarten aufdecken":
            for _ in range(2):
                c = self._draw(s)
                if c is not None: s.exposed.append(c)
                if s.empty_count == 3:
                    s.end_after_phase3 = True; break
        elif kind == "Bohnenkarte schenken":
            _, q, src, i, _ = action
            card = (s.exposed if src == "aufgedeckt" else s.hands[p]).pop(i)
            s.pending[q].append(card)
        elif kind == "Bohnenhandel":
            _, q, src, i, _, j, _ = action
            offered = (s.exposed if src == "aufgedeckt" else s.hands[p]).pop(i)
            wanted = s.hands[q].pop(j)
            s.pending[q].append(offered); s.pending[p].append(wanted)
        elif kind == "Bohnenhandel 2 gegen 1":
            _, q, x, y, j, _ = action
            # Remove higher indexes first within each source.
            offered = []
            for src, i, _ in sorted((x, y), key=lambda z: (z[0], z[1]), reverse=True):
                offered.append((s.exposed if src == "aufgedeckt" else s.hands[p]).pop(i))
            wanted = s.hands[q].pop(j)
            s.pending[q].extend(offered); s.pending[p].append(wanted)
        elif kind == "Handel beenden":
            s.phase = 3
        elif kind == "Neue Bohnenkarte anbauen":
            _, q, f, _ = action
            card = s.pending[q].pop(0) if s.pending[q] else s.exposed.pop(0)
            s.fields[q][f].append(card)
        elif kind == "Phase 3 beenden":
            if s.end_after_phase3: self._finish(s)
            else: s.phase = 4
        elif kind == "Drei Bohnenkarten nachziehen":
            for _ in range(3):
                c = self._draw(s)
                if c is not None: s.hands[p].append(c)
                if s.empty_count == 3: break
            if s.empty_count == 3: self._finish(s)
            else:
                s.active = (p + 1) % s.players; s.phase = 1
        return s

    def is_terminal(self, s: GameState) -> bool:
        return s.terminal

    def returns(self, s: GameState) -> tuple[int, ...]:
        if not s.terminal: return (0,) * s.players
        return tuple(1 if p == s.winner else -1 for p in range(s.players))

    def render(self, s: GameState) -> str:
        rows = [f"Phase {s.phase}; aktiver Spieler {s.active}; Nachziehstapel {len(s.deck)}"]
        for p in range(s.players):
            hand = s.hands[p] if p == s.active else ["verdeckt"] * len(s.hands[p])
            rows.append(f"Spieler {p}: Hand {hand}; Felder {s.fields[p]}; Taler {s.coins[p]}")
        return "\n".join(rows)

    def action_to_name(self, action: tuple) -> str:
        return json.dumps(action, ensure_ascii=False, separators=(",", ":"))

    def name_to_action(self, name: str) -> tuple:
        def freeze(x): return tuple(freeze(y) for y in x) if isinstance(x, list) else x
        return freeze(json.loads(name))
