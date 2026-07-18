"""Source-faithful playable model of the 4--5 player Bohnanza base game."""
from dataclasses import dataclass, field
import random
from typing import Optional

BEANS = ("Gartenbohne", "Rote Bohne", "Augenbohne", "Sojabohne",
         "Brechbohne", "Saubohne", "Feuerbohne", "Blaue Bohne")
COUNTS = dict(zip(BEANS, (6, 8, 10, 12, 14, 16, 18, 20)))
# minimum field sizes paying 1, 2, 3, 4 talers; None means that award is absent
METERS = {
    "Gartenbohne": (2, 3, None, None), "Rote Bohne": (2, 3, 4, 5),
    "Augenbohne": (2, 4, 5, 6), "Sojabohne": (2, 4, 6, 7),
    "Brechbohne": (3, 5, 6, 7), "Saubohne": (3, 5, 7, 8),
    "Feuerbohne": (3, 6, 8, 9), "Blaue Bohne": (4, 6, 8, 10),
}

Action = tuple

@dataclass
class GameState:
    players: int
    hands: list[list[str]]
    fields: list[list[list[str]]]
    coins: list[int]
    deck: list[str]
    discard: list[str]
    active: int = 0
    phase: str = "plant_first"
    revealed: list[str] = field(default_factory=list)
    incoming: list[list[str]] = field(default_factory=list)
    pending: Optional[tuple[int, str, Optional[str]]] = None
    empty_deck_count: int = 0
    terminal: bool = False
    winner_order: list[int] = field(default_factory=list)

class Game:
    """The base condition is defined for 4 or 5 players (default: 4)."""
    def __init__(self, players: int = 4, seed: int = 1):
        if players not in (4, 5):
            raise ValueError("Grundspiel source condition requires 4 or 5 players")
        self.players, self.seed = players, seed

    def initial_state(self) -> GameState:
        deck = [b for b in BEANS for _ in range(COUNTS[b])]
        random.Random(self.seed).shuffle(deck)
        hands = [[] for _ in range(self.players)]
        # Deal singly; append preserves the immutable hand order, index zero foremost.
        for _ in range(5):
            for p in range(self.players): hands[p].append(deck.pop())
        return GameState(self.players, hands, [[[], []] for _ in hands],
                         [0] * self.players, deck, [], incoming=[[] for _ in hands])

    def current_player(self, s):
        if s.pending: return s.pending[0]
        if s.phase == "build":
            owner = next((q for q in range(s.players) if s.incoming[q]), None)
            if owner is not None: return owner
        return s.active

    def _harvestable(self, s, p, i):
        f = s.fields[p][i]
        if not f: return False
        return len(f) > 1 or not any(len(x) > 1 for x in s.fields[p])

    def _can_plant(self, s, p, bean):
        return [i for i, f in enumerate(s.fields[p]) if not f or f[0] == bean]

    def legal_actions(self, s):
        if s.terminal: return []
        p = self.current_player(s)
        acts = []
        # Harvesting is allowed at any time, subject to the bean-protection rule.
        for i in range(2):
            if self._harvestable(s, p, i): acts.append(("harvest", p, i))
        if s.pending:
            return acts + [("accept_trade",), ("reject_trade",)]
        if s.phase in ("plant_first", "plant_second"):
            if not s.hands[p]: return acts + [("skip_empty_hand",)]
            bean = s.hands[p][0]
            acts += [("plant_hand", i) for i in self._can_plant(s, p, bean)]
            if s.phase == "plant_second": acts.append(("plant_only_one",))
        elif s.phase == "trade":
            # An offer gives one active-player card (revealed or hand) and may request
            # one hand card. Accepted received cards are locked out of later trades.
            offered = [("revealed", i, b) for i, b in enumerate(s.revealed)]
            offered += [("hand", i, b) for i, b in enumerate(s.hands[s.active])]
            for target in range(s.players):
                if target == s.active: continue
                wants = [(None, None)] + [(i, b) for i, b in enumerate(s.hands[target])]
                for src, i, b in offered:
                    for wi, wb in wants: acts.append(("offer_trade", target, src, i, b, wi, wb))
            acts.append(("finish_trading",))
        elif s.phase == "build":
            owner = next((q for q in range(s.players) if s.incoming[q]), None)
            if owner is None: acts.append(("finish_building",))
            else:
                b = s.incoming[owner][0]
                acts += [("plant_incoming", owner, i) for i in self._can_plant(s, owner, b)]
        return acts

    def _draw(self, s):
        if not s.deck:
            s.empty_deck_count += 1
            if s.empty_deck_count >= 3: return None
            s.deck, s.discard = s.discard, []
            random.Random(self.seed + s.empty_deck_count).shuffle(s.deck)
        return s.deck.pop() if s.deck else None

    def _harvest(self, s, p, i):
        f = s.fields[p][i]; bean = f[0]
        award = 0
        for n, threshold in enumerate(METERS[bean], 1):
            if threshold is not None and len(f) >= threshold: award = n
        s.coins[p] += award
        # Awarded cards become coins; all other harvested cards are discarded.
        s.discard.extend(f[award:]); s.fields[p][i] = []

    def apply_action(self, s, a):
        if a not in self.legal_actions(s): raise ValueError("illegal action")
        kind = a[0]
        if kind == "harvest": self._harvest(s, a[1], a[2]); return s
        if kind == "plant_hand":
            b = s.hands[s.active].pop(0); s.fields[s.active][a[1]].append(b)
            s.phase = "plant_second" if s.phase == "plant_first" else "reveal"
            if s.phase == "reveal": self._reveal(s)
        elif kind == "skip_empty_hand": s.phase = "reveal"; self._reveal(s)
        elif kind == "plant_only_one": s.phase = "reveal"; self._reveal(s)
        elif kind == "offer_trade": s.pending = (a[1], a[4], a[6]); s._offer = a
        elif kind == "reject_trade": s.pending = None; del s._offer
        elif kind == "accept_trade":
            a = s._offer; target, src, idx, bean, wi, wanted = a[1:]
            (s.revealed if src == "revealed" else s.hands[s.active]).pop(idx)
            s.incoming[target].append(bean)
            if wi is not None:
                s.hands[target].pop(wi); s.incoming[s.active].append(wanted)
            s.pending = None; del s._offer
        elif kind == "finish_trading":
            s.incoming[s.active].extend(s.revealed); s.revealed = []; s.phase = "build"
        elif kind == "plant_incoming":
            b = s.incoming[a[1]].pop(0); s.fields[a[1]][a[2]].append(b)
        elif kind == "finish_building":
            if s.empty_deck_count >= 3:
                self._finalize(s)
                return s
            for _ in range(3):
                b = self._draw(s)
                if b is not None: s.hands[s.active].append(b)
            s.active = (s.active + 1) % s.players; s.phase = "plant_first"
        return s

    def _reveal(self, s):
        for _ in range(2):
            b = self._draw(s)
            if b is not None: s.revealed.append(b)
        s.phase = "trade"
        if s.empty_deck_count >= 3:
            # Complete phases 2 and 3; finish_trading/building leads to final scoring.
            s.phase = "trade"

    def _finalize(self, s):
        for p in range(s.players):
            for i in range(2):
                if s.fields[p][i]: self._harvest(s, p, i)
        s.terminal = True
        s.winner_order = sorted(range(s.players), key=lambda p: (-s.coins[p], (p - 0) % s.players))

    def is_terminal(self, s): return s.terminal
    def returns(self, s):
        if not s.terminal: return [0] * s.players
        best = max(s.coins); return [1 if c == best else 0 for c in s.coins]
    def render(self, s):
        return f"active={s.active} phase={s.phase} coins={s.coins} fields={s.fields} hands={s.hands} deck={len(s.deck)}"
    def action_to_name(self, a): return "|".join("-" if x is None else str(x) for x in a)
    def name_to_action(self, name):
        parts = name.split("|"); out = [parts[0]]
        for x in parts[1:]: out.append(None if x == "-" else int(x) if x.isdigit() else x)
        return tuple(out)
