"""Self-contained model of the supplied 4-5 player Ackerbohnen variant."""
from __future__ import annotations

import copy
import random


COUNTS = {
    "Blaue Bohne": 20, "Feuerbohne": 18, "Saubohne": 16,
    "Brechbohne": 14, "Sojabohne": 12, "Augenbohne": 10,
    "Rote Bohne": 8, "Gartenbohne": 6, "Weinbrandbohne": 22,
    "Ackerbohne": 3,
}
BOHNOMETER = {
    "Blaue Bohne": ((4, 1), (6, 2), (8, 3), (10, 4)),
    "Feuerbohne": ((3, 1), (6, 2), (8, 3), (9, 4)),
    "Saubohne": ((3, 1), (5, 2), (7, 3), (8, 4)),
    "Brechbohne": ((3, 1), (5, 2), (6, 3), (7, 4)),
    "Sojabohne": ((2, 1), (4, 2), (6, 3), (7, 4)),
    "Augenbohne": ((2, 1), (4, 2), (5, 3), (6, 4)),
    "Rote Bohne": ((2, 1), (3, 2), (4, 3), (5, 4)),
    "Gartenbohne": ((2, 2), (3, 3)),
    "Weinbrandbohne": ((2, 1), (4, 2), (6, 3), (8, 4)),
}


class GameState:
    def __init__(self):
        self.num_players = 0
        self.active = 0
        self.actor = 0
        self.start_player = 0
        self.hands = []
        self.fields = []
        self.coins = []
        self.deck = []
        self.discard = []
        self.empty_count = 0
        self.stage = "plant_first"
        self.table = []              # [owner, bean], traded cards are removed/re-added
        self.proposal = None
        self.pending_order = []
        self.draw_order = []
        self.end_triggered = False
        self.terminal = False


class Game:
    """A deterministic-seed game engine; hands are ordered and private by convention."""

    def __init__(self, num_players=4, seed=0):
        if num_players not in (4, 5):
            raise ValueError("the assigned variant permits 4 or 5 players")
        self.num_players = num_players
        self.seed = seed

    def initial_state(self):
        s = GameState()
        s.num_players = self.num_players
        cards = [bean for bean, count in COUNTS.items() for _ in range(count)]
        random.Random(self.seed).shuffle(cards)
        s.hands = [[] for _ in range(self.num_players)]
        for _ in range(5):
            for p in range(self.num_players):
                s.hands[p].append(cards.pop())
        s.fields = [[[] for _ in range(2)] for _ in range(self.num_players)]
        s.coins = [0] * self.num_players
        s.deck = cards
        return s

    def current_player(self, state):
        return state.actor

    @staticmethod
    def _can_harvest(s, p, field):
        if not (0 <= field < len(s.fields[p])) or not s.fields[p][field]:
            return False
        if len(s.fields[p][field]) == 1 and any(len(f) > 1 for f in s.fields[p]):
            return False
        return True

    @staticmethod
    def _plantable_fields(s, p, bean):
        return [i for i, f in enumerate(s.fields[p]) if not f or f[0] == bean]

    def legal_actions(self, s):
        if s.terminal:
            return []
        a = []
        p = s.actor
        # Harvesting is available at every decision point to the player whose
        # decision is currently represented.
        for i in range(len(s.fields[p])):
            if self._can_harvest(s, p, i):
                a.append(("harvest", p, i))

        if s.stage in ("plant_first", "plant_second"):
            if not s.hands[p]:
                a.append(("advance_plant",))
            else:
                bean = s.hands[p][0]
                for i in self._plantable_fields(s, p, bean):
                    a.append(("plant_hand", p, i))
                if s.stage == "plant_second":
                    a.append(("skip_second",))
        elif s.stage == "reveal":
            a.append(("reveal_two",))
        elif s.stage == "trade":
            a.append(("finish_trading",))
            sources = [("table", i, card[1]) for i, card in enumerate(s.table)
                       if card[0] == s.active]
            sources += [("hand", i, b) for i, b in enumerate(s.hands[s.active])]
            for kind, idx, bean in sources:
                for target in range(s.num_players):
                    if target == s.active:
                        continue
                    a.append(("offer_gift", kind, idx, bean, target))
                    for j, wanted in enumerate(s.hands[target]):
                        a.append(("offer_trade", kind, idx, bean, target, j, wanted))
        elif s.stage == "respond":
            a.extend((("accept_offer",), ("decline_offer",)))
        elif s.stage == "plant_table":
            owned = [(i, c[1]) for i, c in enumerate(s.table) if c[0] == p]
            if not owned:
                a.append(("finish_table_player",))
            else:
                idx, bean = owned[0]
                for field in self._plantable_fields(s, p, bean):
                    a.append(("plant_table", idx, p, field, bean))
        elif s.stage == "draw":
            a.append(("draw_one", p))
        return a

    def _harvest(self, s, p, i):
        field = s.fields[p][i]
        bean, n = field[0], len(field)
        if bean == "Ackerbohne":
            if n == 2 and len(s.fields[p]) == 2:
                s.fields[p].append([])
                gain = 0
            elif n == 2:
                gain = 0
            else:
                gain = 3 if n >= 3 else 0
            s.discard.extend([bean] * n)
        else:
            gain = 0
            for threshold, value in BOHNOMETER[bean]:
                if n >= threshold:
                    gain = value
            # Coin cards leave play; all other harvested cards go to discard.
            s.discard.extend([bean] * (n - gain))
        s.coins[p] += gain
        s.fields[p][i] = []

    def _take_card(self, s):
        if not s.deck:
            s.empty_count += 1
            if s.empty_count >= 3:
                s.end_triggered = True
                return None
            s.deck = list(s.discard)
            s.discard = []
            random.Random(self.seed + s.empty_count * 7919).shuffle(s.deck)
        return s.deck.pop() if s.deck else None

    def _finish_game(self, s):
        # The end rule has every player harvest every field; hand cards do not
        # score.  This is mandatory scoring, not an optional final action.
        for p in range(s.num_players):
            for i in range(len(s.fields[p])):
                if s.fields[p][i]:
                    self._harvest(s, p, i)
        s.terminal = True
        s.stage = "terminal"

    def apply_action(self, state, action):
        if action not in self.legal_actions(state):
            raise ValueError("illegal action: " + repr(action))
        s = copy.deepcopy(state)
        tag = action[0]
        if tag == "harvest":
            self._harvest(s, action[1], action[2]); return s
        if tag == "plant_hand":
            _, p, f = action
            s.fields[p][f].append(s.hands[p].pop(0))
            if s.stage == "plant_first": s.stage = "plant_second"
            else: s.stage = "reveal"
            return s
        if tag == "advance_plant":
            s.stage = "plant_second" if s.stage == "plant_first" else "reveal"; return s
        if tag == "skip_second":
            s.stage = "reveal"; return s
        if tag == "reveal_two":
            for _ in range(2):
                card = self._take_card(s)
                if card is not None: s.table.append([s.active, card])
            s.stage = "trade"; return s
        if tag in ("offer_gift", "offer_trade"):
            kind, idx, bean, target = action[1:5]
            s.proposal = {"kind": tag, "source_kind": kind, "source_index": idx,
                          "source_bean": bean, "target": target}
            if tag == "offer_trade":
                s.proposal.update({"target_index": action[5], "target_bean": action[6]})
            s.stage, s.actor = "respond", target
            return s
        if tag == "decline_offer":
            s.proposal = None; s.stage, s.actor = "trade", s.active; return s
        if tag == "accept_offer":
            q = s.proposal
            if q["source_kind"] == "hand":
                # Proposal indices remain valid because no intervening mutation occurs.
                given = s.hands[s.active].pop(q["source_index"])
            else:
                given = s.table.pop(q["source_index"])[1]
            s.table.append([q["target"], given])
            if q["kind"] == "offer_trade":
                wanted = s.hands[q["target"]].pop(q["target_index"])
                s.table.append([s.active, wanted])
            s.proposal = None; s.stage, s.actor = "trade", s.active; return s
        if tag == "finish_trading":
            s.pending_order = [((s.active + k) % s.num_players) for k in range(s.num_players)]
            s.stage = "plant_table"; s.actor = s.pending_order.pop(0); return s
        if tag == "plant_table":
            _, idx, p, field, _ = action
            bean = s.table.pop(idx)[1]; s.fields[p][field].append(bean); return s
        if tag == "finish_table_player":
            if s.pending_order:
                s.actor = s.pending_order.pop(0)
            elif s.end_triggered:
                self._finish_game(s)
            else:
                s.draw_order = [((s.active + k) % s.num_players) for k in range(s.num_players)]
                s.stage = "draw"; s.actor = s.draw_order.pop(0)
            return s
        if tag == "draw_one":
            card = self._take_card(s)
            if card is not None: s.hands[s.actor].append(card)
            if s.draw_order and not s.end_triggered:
                s.actor = s.draw_order.pop(0)
            elif s.end_triggered:
                self._finish_game(s)
            else:
                s.active = (s.active + 1) % s.num_players
                s.actor = s.active; s.stage = "plant_first"
            return s
        raise AssertionError(tag)

    def is_terminal(self, state):
        return state.terminal

    def returns(self, state):
        if not state.terminal:
            return [0] * state.num_players
        best = max(state.coins)
        tied = [p for p, score in enumerate(state.coins) if score == best]
        # Clockwise furthest from the start player wins the tie.
        winner = max(tied, key=lambda p: (p - state.start_player) % state.num_players)
        return [1 if p == winner else -1 for p in range(state.num_players)]

    def render(self, s):
        fields = [[(f[0], len(f)) if f else None for f in fs] for fs in s.fields]
        return (f"stage={s.stage} active={s.active} actor={s.actor} coins={s.coins} "
                f"hands={[len(h) for h in s.hands]} fields={fields} "
                f"deck={len(s.deck)} discard={len(s.discard)} table={s.table}")

    def action_to_name(self, action):
        return " | ".join(str(x) for x in action)

    def name_to_action(self, name):
        parts = name.split(" | ")
        return tuple(int(x) if x.lstrip("-").isdigit() else x for x in parts)
