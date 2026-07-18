"""Source-faithful, self-contained Bohnanza base game for 4 or 5 players.

The default is four players.  Hidden hands are represented in full in GameState so
the engine can adjudicate them; render() only exposes each hand's size except for
the current decision maker.
"""
from dataclasses import dataclass, replace
import random
from typing import Optional


BEANS = (
    ("Blaue Bohne", 20, ((4, 1), (6, 2), (8, 3), (10, 4))),
    ("Feuerbohne", 18, ((3, 1), (6, 2), (8, 3), (9, 4))),
    ("Saubohne", 16, ((3, 1), (5, 2), (7, 3), (8, 4))),
    ("Brechbohne", 14, ((3, 1), (5, 2), (6, 3), (7, 4))),
    ("Sojabohne", 12, ((2, 1), (4, 2), (6, 3), (7, 4))),
    ("Augenbohne", 10, ((2, 1), (4, 2), (5, 3), (6, 4))),
    ("Rote Bohne", 8, ((2, 1), (3, 2), (4, 3), (5, 4))),
    ("Gartenbohne", 6, ((2, 2), (3, 3))),
)
METER = {name: thresholds for name, _, thresholds in BEANS}
Action = tuple


@dataclass(frozen=True)
class GameState:
    players: int
    active: int
    actor: int
    phase: str
    deck: tuple[str, ...]
    discard: tuple[str, ...]
    hands: tuple[tuple[str, ...], ...]
    fields: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...]
    coins: tuple[int, ...]
    revealed: tuple[str, ...] = ()
    acquired: tuple[tuple[str, ...], ...] = ()
    planted_extra: bool = False
    empty_count: int = 0
    pending_end: bool = False
    proposal: Optional[tuple[int, str, str, Optional[str]]] = None
    terminal: bool = False


class Game:
    def __init__(self, players: int = 4, seed: int = 1):
        if players not in (4, 5):
            raise ValueError("the assigned base condition supports 4 or 5 players")
        self.players, self.seed = players, seed

    def initial_state(self) -> GameState:
        cards = [name for name, count, _ in BEANS for _ in range(count)]
        random.Random(self.seed).shuffle(cards)
        hands = [[] for _ in range(self.players)]
        # Deal singly; append preserves the immutable hand order.
        for _ in range(5):
            for p in range(self.players):
                hands[p].append(cards.pop())
        fields = tuple(((), ()) for _ in range(self.players))
        return GameState(self.players, 0, 0, "plant_first", tuple(cards), (),
                         tuple(map(tuple, hands)), fields, (0,) * self.players,
                         acquired=tuple(() for _ in range(self.players)))

    def current_player(self, state: GameState) -> int:
        return state.actor

    @staticmethod
    def _replace_seq(seq, index, value):
        out = list(seq); out[index] = value; return tuple(out)

    @staticmethod
    def _harvest_allowed(state, p, f):
        field = state.fields[p][f]
        if not field:
            return False
        return len(field) > 1 or not any(len(x) > 1 for x in state.fields[p])

    @staticmethod
    def _can_plant(state, p, bean, f):
        field = state.fields[p][f]
        return not field or field[0] == bean or Game._harvest_allowed(state, p, f)

    def _harvest_actions(self, state):
        return [("harvest", state.actor, f) for f in range(2)
                if self._harvest_allowed(state, state.actor, f)]

    def legal_actions(self, state: GameState):
        if state.terminal:
            return []
        p = state.actor
        harvest = self._harvest_actions(state)
        if state.proposal:
            _, target, _, _ = state.proposal
            return [("accept_trade", target), ("reject_trade", target)] if p == target else []
        if state.phase in ("plant_first", "plant_second"):
            if not state.hands[p]:
                return [("advance", state.phase)] + harvest
            bean = state.hands[p][0]
            plants = [("plant_hand", p, f, bean) for f in range(2)
                      if self._can_plant(state, p, bean, f)]
            if state.phase == "plant_second":
                plants.append(("skip_second", p))
            return plants + harvest
        if state.phase == "trade":
            actions = [("end_trade", p)] + harvest
            available = list(dict.fromkeys(state.hands[p] + state.revealed))
            for target in range(state.players):
                if target == p:
                    continue
                for give in available:
                    actions.append(("propose_gift", p, target, give))
                    for receive in dict.fromkeys(state.hands[target]):
                        actions.append(("propose_trade", p, target, give, receive))
            return actions
        if state.phase == "plant_acquired":
            pool = state.acquired[p]
            if not pool:
                return [("finish_acquired", p)] + harvest
            actions = harvest[:]
            for bean in dict.fromkeys(pool):
                actions += [("plant_acquired", p, f, bean) for f in range(2)
                            if self._can_plant(state, p, bean, f)]
            return actions
        if state.phase == "draw_three":
            return [("draw_three", p)] + harvest
        raise ValueError("unknown phase")

    def _draw_one(self, state):
        if state.terminal:
            return state, None
        deck, discard, empties = list(state.deck), list(state.discard), state.empty_count
        pending, terminal = state.pending_end, state.terminal
        if not deck:
            empties += 1
            if empties >= 3:
                if state.phase == "trade": pending = True
                else: terminal = True
                return replace(state, empty_count=empties, pending_end=pending,
                               terminal=terminal), None
            deck = discard; discard = []
            random.Random(self.seed + empties).shuffle(deck)
        card = deck.pop()
        return replace(state, deck=tuple(deck), discard=tuple(discard),
                       empty_count=empties), card

    def _do_harvest(self, state, p, f):
        field = state.fields[p][f]
        if not self._harvest_allowed(state, p, f):
            raise ValueError("Bohnenschutzregel forbids this harvest")
        reward = 0
        for threshold, value in METER[field[0]]:
            if len(field) >= threshold: reward = value
        fields_p = self._replace_seq(state.fields[p], f, ())
        fields = self._replace_seq(state.fields, p, fields_p)
        coins = self._replace_seq(state.coins, p, state.coins[p] + reward)
        # reward cards become the player's coin pile; remaining cards are discarded.
        return replace(state, fields=fields, coins=coins,
                       discard=state.discard + field[reward:])

    def _plant(self, state, p, f, bean):
        field = state.fields[p][f]
        if field and field[0] != bean:
            state = self._do_harvest(state, p, f); field = ()
        fields_p = self._replace_seq(state.fields[p], f, field + (bean,))
        return replace(state, fields=self._replace_seq(state.fields, p, fields_p))

    def apply_action(self, state: GameState, action: Action):
        if action not in self.legal_actions(state):
            raise ValueError("illegal action")
        kind = action[0]; p = state.actor
        if kind == "harvest": return self._do_harvest(state, action[1], action[2])
        if kind == "advance":
            return replace(state, phase="reveal", actor=state.active) if False else self._reveal_two(replace(state, phase="trade"))
        if kind == "plant_hand":
            _, _, f, bean = action
            hands = self._replace_seq(state.hands, p, state.hands[p][1:])
            state = self._plant(replace(state, hands=hands), p, f, bean)
            if state.phase == "plant_first": return replace(state, phase="plant_second")
            return self._reveal_two(replace(state, phase="trade"))
        if kind == "skip_second": return self._reveal_two(replace(state, phase="trade"))
        if kind in ("propose_trade", "propose_gift"):
            target, give = action[2], action[3]
            receive = action[4] if kind == "propose_trade" else None
            return replace(state, actor=target, proposal=(state.active, target, give, receive))
        if kind == "reject_trade": return replace(state, actor=state.active, proposal=None)
        if kind == "accept_trade": return self._accept(state)
        if kind == "end_trade":
            acquired = list(state.acquired)
            acquired[state.active] += state.revealed
            return replace(state, phase="plant_acquired", actor=0, revealed=(),
                           acquired=tuple(acquired))
        if kind == "plant_acquired":
            _, _, f, bean = action
            pool = list(state.acquired[p]); pool.remove(bean)
            acquired = self._replace_seq(state.acquired, p, tuple(pool))
            return self._plant(replace(state, acquired=acquired), p, f, bean)
        if kind == "finish_acquired":
            nxt = p + 1
            if nxt < state.players: return replace(state, actor=nxt)
            if state.pending_end: return replace(state, terminal=True)
            return replace(state, phase="draw_three", actor=state.active)
        if kind == "draw_three":
            for _ in range(3):
                state, card = self._draw_one(state)
                if card is None: break
                hands = self._replace_seq(state.hands, p, state.hands[p] + (card,))
                state = replace(state, hands=hands)
            if state.terminal: return state
            active = (state.active + 1) % state.players
            return replace(state, active=active, actor=active, phase="plant_first")
        raise ValueError("unknown action")

    def _reveal_two(self, state):
        cards = []
        for _ in range(2):
            state, card = self._draw_one(state)
            if card is not None: cards.append(card)
            if state.terminal: break
        # A third emptying during phase 2 still completes phases 2 and 3.
        if state.terminal:
            state = replace(state, terminal=False, pending_end=True)
        return replace(state, revealed=tuple(cards), actor=state.active)

    def _remove_active_card(self, state, bean):
        p = state.active
        if bean in state.revealed:
            r = list(state.revealed); r.remove(bean); return replace(state, revealed=tuple(r))
        h = list(state.hands[p]); h.remove(bean)
        return replace(state, hands=self._replace_seq(state.hands, p, tuple(h)))

    def _accept(self, state):
        active, target, give, receive = state.proposal
        state = self._remove_active_card(state, give)
        acq = list(state.acquired); acq[target] += (give,)
        hands = state.hands
        if receive is not None:
            h = list(hands[target]); h.remove(receive)
            hands = self._replace_seq(hands, target, tuple(h)); acq[active] += (receive,)
        return replace(state, hands=hands, acquired=tuple(acq), actor=active, proposal=None)

    def is_terminal(self, state): return state.terminal

    def returns(self, state):
        if not state.terminal: return (0,) * state.players
        scores = list(state.coins)
        # At game end everybody harvests both fields; hand cards do not count.
        for p in range(state.players):
            for field in state.fields[p]:
                if field:
                    reward = 0
                    for threshold, value in METER[field[0]]:
                        if len(field) >= threshold: reward = value
                    scores[p] += reward
        best = max(scores)
        winners = [p for p, score in enumerate(scores) if score == best]
        # Tie: clockwise after the starting player (player 0), so the highest index.
        winner = max(winners)
        return tuple(1 if p == winner else -1 for p in range(state.players))

    def render(self, state):
        hands = [list(h) if p == state.actor else f"{len(h)} hidden cards"
                 for p, h in enumerate(state.hands)]
        return str({"active": state.active, "actor": state.actor, "phase": state.phase,
                    "hands": hands, "fields": state.fields, "coins": state.coins,
                    "revealed": state.revealed, "deck": len(state.deck),
                    "discard": len(state.discard), "emptyings": state.empty_count})

    def action_to_name(self, action):
        return " | ".join(map(str, action))

    def name_to_action(self, name):
        parts = name.split(" | ")
        numeric = {"harvest": (1, 2), "plant_hand": (1, 2), "skip_second": (1,),
                   "propose_gift": (1, 2), "propose_trade": (1, 2),
                   "accept_trade": (1,), "reject_trade": (1,), "plant_acquired": (1, 2),
                   "end_trade": (1,), "finish_acquired": (1,), "draw_three": (1,)}
        for i in numeric.get(parts[0], ()):
            parts[i] = int(parts[i])
        return tuple(parts)
