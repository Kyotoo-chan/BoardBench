"""Source-bounded implementation of Bohnanza, 4--5 player condition.

The model uses explicit proposals for the rulebook's free-form negotiation.  A
fixed shuffle seed makes ``initial_state`` reproducible while retaining a
hidden, ordered draw pile in the state.
"""
from dataclasses import dataclass, field
import copy
import json
import random
from typing import Any


BEANS = (
    "Blaue Bohne", "Feuerbohne", "Saubohne", "Brechbohne",
    "Sojabohne", "Augenbohne", "Rote Bohne", "Gartenbohne",
    "Weinbrandbohne", "Ackerbohne",
)
COUNTS = dict(zip(BEANS, (20, 18, 16, 14, 12, 10, 8, 6, 22, 3)))
METERS = {
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


@dataclass
class GameState:
    players: int
    active: int
    controller: int
    phase: str
    hands: list[list[str]]
    fields: list[list[list[str]]]
    coins: list[int]
    deck: list[str]
    discard: list[str] = field(default_factory=list)
    face_up: list[str] = field(default_factory=list)
    planting: list[tuple[int, str]] = field(default_factory=list)
    proposal: tuple | None = None
    empty_count: int = 0
    end_pending: bool = False
    terminal: bool = False


class Game:
    def __init__(self, players: int = 4, seed: int = 1):
        if players not in (4, 5):
            raise ValueError("the assigned source condition supports 4 or 5 players")
        self.players, self.seed = players, seed

    def initial_state(self) -> GameState:
        deck = [b for b in BEANS for _ in range(COUNTS[b])]
        random.Random(self.seed).shuffle(deck)
        hands = [[] for _ in range(self.players)]
        for p in range(self.players):
            for _ in range(5):
                hands[p].append(deck.pop())
        return GameState(self.players, 0, 0, "plant_first", hands,
                         [[[], []] for _ in range(self.players)],
                         [0] * self.players, deck)

    def current_player(self, state: GameState) -> int:
        return state.controller

    @staticmethod
    def _protected(fields: list[list[str]], i: int) -> bool:
        return len(fields[i]) == 1 and any(len(f) > 1 for f in fields)

    @staticmethod
    def _can_plant(fields: list[list[str]], bean: str, i: int) -> bool:
        return 0 <= i < len(fields) and (not fields[i] or fields[i][0] == bean)

    def _harvest_actions(self, s: GameState, p: int) -> list[tuple]:
        return [("harvest", i) for i, f in enumerate(s.fields[p])
                if f and not self._protected(s.fields[p], i)]

    def legal_actions(self, s: GameState) -> list[tuple]:
        if s.terminal:
            return []
        p, out = s.controller, []
        if s.phase in ("plant_first", "plant_second"):
            if s.hands[p]:
                bean = s.hands[p][0]
                out += [("plant_hand", i) for i in range(len(s.fields[p]))
                        if self._can_plant(s.fields[p], bean, i)]
                out += self._harvest_actions(s, p)
            elif s.phase == "plant_first":
                out.append(("advance",))
            if s.phase == "plant_second":
                out.append(("skip_second",))
        elif s.phase == "reveal":
            out.append(("reveal_two",))
        elif s.phase == "trade":
            # Active player can offer a hand card or either untraded face-up card.
            for target in range(s.players):
                if target == s.active:
                    continue
                for si in range(len(s.hands[s.active])):
                    out.append(("propose_gift", "hand", si, target))
                    for ti in range(len(s.hands[target])):
                        out.append(("propose_trade", "hand", si, target, ti))
                for si in range(len(s.face_up)):
                    out.append(("propose_gift", "face", si, target))
                    for ti in range(len(s.hands[target])):
                        out.append(("propose_trade", "face", si, target, ti))
            out.append(("finish_trading",))
        elif s.phase == "respond":
            out += [("accept",), ("reject",)]
        elif s.phase == "plant_trades":
            if not s.planting:
                out.append(("finish_planting",))
            else:
                owner, bean = s.planting[0]
                out += [("plant_trade", i) for i in range(len(s.fields[owner]))
                        if self._can_plant(s.fields[owner], bean, i)]
                out += self._harvest_actions(s, owner)
        elif s.phase == "draw":
            out.append(("draw_three",))
        return out

    def _draw(self, s: GameState) -> str | None:
        if not s.deck:
            s.empty_count += 1
            if s.empty_count >= 3:
                s.end_pending = True
                return None
            s.deck, s.discard = s.discard, []
            random.Random(self.seed + s.empty_count).shuffle(s.deck)
            if not s.deck:
                s.end_pending = True
                return None
        return s.deck.pop()

    def _harvest(self, s: GameState, p: int, i: int) -> None:
        cards = s.fields[p][i]
        bean, n = cards[0], len(cards)
        if bean == "Ackerbohne":
            gain = 3 if n >= 3 else 0
            if n == 2 and len(s.fields[p]) == 2:
                s.fields[p].append([])
        else:
            gain = max((gold for need, gold in METERS[bean] if n >= need), default=0)
        s.coins[p] += gain
        s.discard.extend(cards[gain:])
        s.fields[p][i] = []

    def apply_action(self, state: GameState, action: tuple) -> GameState:
        s = copy.deepcopy(state)
        if action not in self.legal_actions(s):
            raise ValueError("illegal action")
        kind, p = action[0], s.controller
        if kind == "harvest":
            self._harvest(s, p, action[1])
        elif kind == "plant_hand":
            s.fields[p][action[1]].append(s.hands[p].pop(0))
            s.phase = "plant_second" if s.phase == "plant_first" else "reveal"
        elif kind in ("advance", "skip_second"):
            s.phase = "reveal"
        elif kind == "reveal_two":
            for _ in range(2):
                card = self._draw(s)
                if card is not None:
                    s.face_up.append(card)
            s.phase = "trade"
        elif kind.startswith("propose_"):
            s.proposal = action
            s.controller = action[3]
            s.phase = "respond"
        elif kind == "reject":
            s.proposal = None; s.controller = s.active; s.phase = "trade"
        elif kind == "accept":
            q = s.proposal; assert q is not None
            _, source, si, target, *rest = q
            offered = (s.hands[s.active] if source == "hand" else s.face_up).pop(si)
            s.planting.append((target, offered))
            if q[0] == "propose_trade":
                received = s.hands[target].pop(rest[0])
                s.planting.append((s.active, received))
            s.proposal = None; s.controller = s.active; s.phase = "trade"
        elif kind == "finish_trading":
            s.planting.extend((s.active, b) for b in s.face_up)
            s.face_up = []
            s.phase = "plant_trades"
            s.controller = s.planting[0][0] if s.planting else s.active
        elif kind == "plant_trade":
            owner, bean = s.planting.pop(0)
            s.fields[owner][action[1]].append(bean)
            s.controller = s.planting[0][0] if s.planting else s.active
        elif kind == "finish_planting":
            s.phase = "draw"; s.controller = s.active
        elif kind == "draw_three":
            for _ in range(3):
                card = self._draw(s)
                if card is not None:
                    s.hands[s.active].append(card)
            if s.end_pending:
                s.terminal = True; s.phase = "terminal"
            else:
                s.active = (s.active + 1) % s.players
                s.controller = s.active; s.phase = "plant_first"
        return s

    def is_terminal(self, state: GameState) -> bool:
        return state.terminal

    def returns(self, state: GameState) -> tuple[int, ...]:
        if not state.terminal:
            return tuple(0 for _ in range(state.players))
        scores = [state.coins[p] + len(state.hands[p]) for p in range(state.players)]
        best = max(scores)
        winners = [p for p, x in enumerate(scores) if x == best]
        if len(winners) > 1:
            # Clockwise nearest to the start player wins the stated tie-break.
            winners = [max(winners)]
        return tuple(1 if p in winners else -1 for p in range(state.players))

    def render(self, s: GameState) -> str:
        return (f"phase={s.phase} active={s.active} controller={s.controller} "
                f"coins={s.coins} hand_sizes={[len(h) for h in s.hands]} "
                f"fields={s.fields} face_up={s.face_up}")

    def action_to_name(self, action: tuple) -> str:
        return json.dumps(action, ensure_ascii=False, separators=(",", ":"))

    def name_to_action(self, name: str) -> tuple:
        def freeze(x: Any) -> Any:
            return tuple(freeze(v) for v in x) if isinstance(x, list) else x
        return freeze(json.loads(name))
