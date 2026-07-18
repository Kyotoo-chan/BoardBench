"""Source-faithful, self-contained model of the supplied 4--5 player rules."""
from dataclasses import dataclass, field
import random
from typing import Optional

BEANS = ("Blaue Bohne", "Feuerbohne", "Saubohne", "Brechbohne",
         "Sojabohne", "Augenbohne", "Rote Bohne", "Gartenbohne",
         "Weinbrandbohne", "Ackerbohne")
COUNTS = dict(zip(BEANS, (20, 18, 16, 14, 12, 10, 8, 6, 22, 3)))
BOHNOMETER = {
    "Blaue Bohne": ((4, 1), (6, 2), (8, 3), (10, 4)),
    "Feuerbohne": ((3, 1), (6, 2), (8, 3), (9, 4)),
    "Saubohne": ((3, 1), (5, 2), (7, 3), (8, 4)),
    "Brechbohne": ((3, 1), (5, 2), (6, 3), (7, 4)),
    "Sojabohne": ((2, 1), (4, 2), (6, 3), (7, 4)),
    "Augenbohne": ((2, 1), (4, 2), (5, 3), (6, 4)),
    "Rote Bohne": ((2, 1), (3, 2), (4, 3), (5, 4)),
    "Gartenbohne": ((2, 2), (3, 3)),
    "Weinbrandbohne": ((4, 1), (7, 2), (9, 3), (11, 4)),
}


@dataclass(frozen=True)
class Action:
    kind: str
    args: tuple = ()


@dataclass
class PlayerState:
    hand: list[str] = field(default_factory=list)
    fields: list[list[str]] = field(default_factory=lambda: [[], []])
    pending: list[str] = field(default_factory=list)
    coins: int = 0


@dataclass
class GameState:
    players: list[PlayerState]
    deck: list[str]
    discard: list[str] = field(default_factory=list)
    active: int = 0
    start_player: int = 0
    phase: str = "phase1_must_plant"
    face_up: list[str] = field(default_factory=list)
    phase1_planted: int = 0
    phase2_drawn: int = 0
    draw_remaining: int = 0
    exhaustions: int = 0
    ending_after_phase3: bool = False
    terminal: bool = False
    winners: tuple[int, ...] = ()


class Game:
    """Four-player by default; pass players=5 for the other assigned condition."""

    def __init__(self, players: int = 4, seed: int = 0):
        if players not in (4, 5):
            raise ValueError("this source condition supports exactly 4 or 5 players")
        self.player_count = players
        self.seed = seed

    def initial_state(self) -> GameState:
        deck = [b for b in BEANS for _ in range(COUNTS[b])]
        random.Random(self.seed).shuffle(deck)
        ps = [PlayerState() for _ in range(self.player_count)]
        # Individually deal five; append order is the immutable hand order.
        for _ in range(5):
            for p in ps:
                p.hand.append(deck.pop())
        return GameState(ps, deck)

    def current_player(self, state: GameState) -> int:
        if state.terminal:
            return -1
        if state.phase == "phase3":
            for i, p in enumerate(state.players):
                if p.pending:
                    return i
        return state.active

    @staticmethod
    def _can_harvest(p: PlayerState, i: int) -> bool:
        f = p.fields[i]
        if not f:
            return False
        return len(f) > 1 or not any(len(other) > 1 for other in p.fields)

    @staticmethod
    def _plant_destinations(p: PlayerState, bean: str) -> list[int]:
        return [i for i, f in enumerate(p.fields) if not f or f[0] == bean]

    def legal_actions(self, s: GameState) -> list[Action]:
        if s.terminal:
            return []
        p = s.players[s.active]
        if s.phase in ("phase1_must_plant", "phase1_optional"):
            if not p.hand:
                return [Action("advance_to_phase2")]
            bean = p.hand[0]
            dest = self._plant_destinations(p, bean)
            acts = [Action("plant_hand_front", (i, bean)) for i in dest]
            if not dest:
                acts += [Action("harvest", (s.active, i)) for i in range(len(p.fields)) if self._can_harvest(p, i)]
            if s.phase == "phase1_optional":
                acts.append(Action("advance_to_phase2"))
            return acts
        if s.phase == "phase2_draw":
            return [Action("draw_face_up")]
        if s.phase == "phase2_trade":
            acts = [Action("end_trading")]
            # Every listed action is an immediately consensual legal trade/gift.
            for other, q in enumerate(s.players):
                if other == s.active:
                    continue
                for i, b in enumerate(p.hand):
                    acts.append(Action("gift", (s.active, "hand", i, other, b)))
                for i, b in enumerate(s.face_up):
                    acts.append(Action("gift", (s.active, "face_up", i, other, b)))
                for j, rb in enumerate(q.hand):
                    acts.append(Action("gift", (other, "hand", j, s.active, rb)))
                    for i, b in enumerate(p.hand):
                        acts.append(Action("trade", (other, "hand", i, b, j, rb)))
                    for i, b in enumerate(s.face_up):
                        acts.append(Action("trade", (other, "face_up", i, b, j, rb)))
            return acts
        if s.phase == "phase3":
            who = next((i for i, q in enumerate(s.players) if q.pending), None)
            if who is None:
                return [Action("finish_phase3")]
            q = s.players[who]
            bean = q.pending[0]
            dest = self._plant_destinations(q, bean)
            if dest:
                return [Action("plant_pending", (who, i, bean)) for i in dest]
            return [Action("harvest", (who, i)) for i in range(len(q.fields)) if self._can_harvest(q, i)]
        if s.phase == "phase4":
            return [Action("draw_to_hand")]
        raise RuntimeError(f"unknown phase {s.phase}")

    def _draw_one(self, s: GameState) -> Optional[str]:
        if not s.deck:
            s.exhaustions += 1
            if s.exhaustions >= 3:
                return None
            s.deck = s.discard
            s.discard = []
            random.Random(self.seed + s.exhaustions).shuffle(s.deck)
            if not s.deck:
                return None
        return s.deck.pop()

    def _harvest(self, s: GameState, who: int, fi: int) -> None:
        p = s.players[who]
        cards = p.fields[fi]
        bean, n = cards[0], len(cards)
        if bean == "Ackerbohne" and n == 2:
            if len(p.fields) == 2:
                p.fields.append([])
            s.discard.extend(cards)
        else:
            reward = (3 if n >= 3 else 0) if bean == "Ackerbohne" else max(
                (gold for threshold, gold in BOHNOMETER[bean] if n >= threshold), default=0)
            p.coins += reward
            # Reward cards become coins; only the remainder reaches discard.
            s.discard.extend(cards[reward:])
        p.fields[fi] = []

    def _finish_game(self, s: GameState) -> None:
        for who, p in enumerate(s.players):
            for fi in range(len(p.fields)):
                if p.fields[fi]:
                    self._harvest(s, who, fi)
        scores = [p.coins for p in s.players]
        best = max(scores)
        tied = [i for i, x in enumerate(scores) if x == best]
        # Furthest clockwise from the fixed start player wins the tie.
        winner = max(tied, key=lambda i: (i - s.start_player) % len(s.players))
        s.winners = (winner,)
        s.terminal = True
        s.phase = "terminal"

    def apply_action(self, s: GameState, a: Action) -> GameState:
        if a not in self.legal_actions(s):
            raise ValueError("illegal action")
        k, x = a.kind, a.args
        if k == "plant_hand_front":
            fi, bean = x; p = s.players[s.active]
            p.fields[fi].append(p.hand.pop(0)); s.phase1_planted += 1
            s.phase = "phase1_optional" if s.phase1_planted == 1 and p.hand else "phase2_draw"
            if s.phase == "phase2_draw": s.phase2_drawn = 0
        elif k == "advance_to_phase2":
            s.phase = "phase2_draw"; s.phase2_drawn = 0
        elif k == "harvest":
            self._harvest(s, x[0], x[1])
        elif k == "draw_face_up":
            card = self._draw_one(s)
            if card is not None: s.face_up.append(card)
            elif s.exhaustions >= 3: s.ending_after_phase3 = True
            s.phase2_drawn += 1
            if s.phase2_drawn >= 2 or (card is None and not s.deck): s.phase = "phase2_trade"
        elif k == "gift":
            giver, source, idx, receiver, bean = x
            card = s.face_up.pop(idx) if source == "face_up" else s.players[giver].hand.pop(idx)
            s.players[receiver].pending.append(card)
        elif k == "trade":
            other, source, idx, bean, j, received = x
            offered = s.face_up.pop(idx) if source == "face_up" else s.players[s.active].hand.pop(idx)
            got = s.players[other].hand.pop(j)
            s.players[other].pending.append(offered)
            s.players[s.active].pending.append(got)
        elif k == "end_trading":
            s.players[s.active].pending.extend(s.face_up); s.face_up.clear(); s.phase = "phase3"
        elif k == "plant_pending":
            who, fi, bean = x; p = s.players[who]
            p.fields[fi].append(p.pending.pop(0))
        elif k == "finish_phase3":
            if s.ending_after_phase3: self._finish_game(s)
            else: s.phase = "phase4"; s.draw_remaining = 3
        elif k == "draw_to_hand":
            card = self._draw_one(s)
            if card is not None: s.players[s.active].hand.append(card)
            s.draw_remaining -= 1
            if s.exhaustions >= 3:
                self._finish_game(s)
            elif s.draw_remaining <= 0:
                s.active = (s.active + 1) % len(s.players)
                s.phase = "phase1_must_plant"; s.phase1_planted = 0
        return s

    def is_terminal(self, state: GameState) -> bool:
        return state.terminal

    def returns(self, state: GameState) -> tuple[float, ...]:
        if not state.terminal:
            return tuple(0.0 for _ in state.players)
        return tuple(1.0 if i in state.winners else -1.0 for i in range(len(state.players)))

    def render(self, s: GameState) -> str:
        rows = [f"phase={s.phase} active={s.active} deck={len(s.deck)} exhaustions={s.exhaustions}"]
        for i, p in enumerate(s.players):
            rows.append(f"P{i}: hand={p.hand} fields={p.fields} pending={p.pending} coins={p.coins}")
        return "\n".join(rows)

    def action_to_name(self, action: Action) -> str:
        return action.kind + (":" + "|".join(map(str, action.args)) if action.args else "")

    def name_to_action(self, name: str) -> Action:
        if ":" not in name:
            return Action(name)
        kind, raw = name.split(":", 1)
        vals = []
        for v in raw.split("|"):
            vals.append(int(v) if v.lstrip("-").isdigit() else v)
        return Action(kind, tuple(vals))
