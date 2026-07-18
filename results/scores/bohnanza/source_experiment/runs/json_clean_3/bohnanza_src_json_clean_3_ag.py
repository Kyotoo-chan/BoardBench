"""Source-faithful Bohnanza Variant 2 (Ackerbohnen), for 4--5 players.

The engine is deterministic for a seed, but the shuffled deck and opponents' hands
remain represented separately.  Cards in a hand are ordered tuples and are never
reordered.
"""
from dataclasses import dataclass, replace
import json
import random
from typing import Optional


BEANS = {
    "Blaue Bohne": (20, ((4, 1), (6, 2), (8, 3), (10, 4))),
    "Feuerbohne": (18, ((3, 1), (6, 2), (8, 3), (9, 4))),
    "Saubohne": (16, ((3, 1), (5, 2), (7, 3), (8, 4))),
    "Brechbohne": (14, ((3, 1), (5, 2), (6, 3), (7, 4))),
    "Sojabohne": (12, ((2, 1), (4, 2), (6, 3), (7, 4))),
    "Augenbohne": (10, ((2, 1), (4, 2), (5, 3), (6, 4))),
    "Rote Bohne": (8, ((2, 1), (3, 2), (4, 3), (5, 4))),
    "Gartenbohne": (6, ((2, 2), (3, 3))),
    "Weinbrandbohne": (22, ((4, 1), (7, 2), (9, 3), (11, 4))),
    "Ackerbohne": (3, ()),
}


@dataclass(frozen=True)
class Action:
    kind: str
    args: tuple = ()


@dataclass(frozen=True)
class GameState:
    players: int
    active: int
    actor: int
    phase: str
    hands: tuple[tuple[str, ...], ...]
    fields: tuple[tuple[tuple[str, ...], ...], ...]
    coins: tuple[int, ...]
    deck: tuple[str, ...]
    discard: tuple[str, ...]
    face_up: tuple[str, ...] = ()
    received: tuple[tuple[str, ...], ...] = ()
    empty_count: int = 0
    first_planted: int = 0
    draw_left: int = 0
    pending_offer: Optional[tuple] = None
    offer_give: tuple[str, ...] = ()
    offer_ask: tuple[str, ...] = ()
    offer_partner: int = -1
    field_counts: tuple[int, ...] = ()
    terminal: bool = False


class Game:
    def __init__(self, num_players: int = 4, seed: int = 1):
        if num_players not in (4, 5):
            raise ValueError("Variant 2 is for 4-5 players")
        self.num_players, self.seed = num_players, seed

    def initial_state(self) -> GameState:
        deck = [b for b, (n, _) in BEANS.items() for _ in range(n)]
        random.Random(self.seed).shuffle(deck)
        hands = [[] for _ in range(self.num_players)]
        # Deal singly; the first received card remains at the front.
        for _ in range(5):
            for p in range(self.num_players):
                hands[p].append(deck.pop())
        empty_received = tuple(() for _ in hands)
        empty_fields = tuple(((), ()) for _ in hands)
        return GameState(self.num_players, 0, 0, "plant_hand", tuple(map(tuple, hands)),
                         empty_fields, (0,) * self.num_players, tuple(deck), (),
                         received=empty_received, field_counts=(2,) * self.num_players)

    def current_player(self, state: GameState) -> int:
        return state.actor

    @staticmethod
    def _replace_at(seq, i, value):
        x = list(seq); x[i] = value; return tuple(x)

    def _harvestable(self, s, p, i):
        f = s.fields[p][i]
        return bool(f) and (len(f) > 1 or not any(len(x) > 1 for x in s.fields[p]))

    def legal_actions(self, s: GameState):
        if s.terminal:
            return ()
        a = []
        # Harvesting is permitted at any time, by any player, subject to protection.
        for p in range(s.players):
            for i in range(len(s.fields[p])):
                if self._harvestable(s, p, i): a.append(Action("harvest", (p, i)))
        p = s.actor
        if s.phase == "plant_hand":
            if not s.hands[p] or s.first_planted == 2:
                a.append(Action("finish_hand_planting"))
            else:
                bean = s.hands[p][0]
                for i, f in enumerate(s.fields[p]):
                    if not f or f[0] == bean: a.append(Action("plant_front", (i,)))
                if s.first_planted == 1: a.append(Action("finish_hand_planting"))
        elif s.phase == "trade":
            a.append(Action("finish_trading"))
            if s.offer_partner < 0:
                for q in range(s.players):
                    if q != s.active: a.append(Action("begin_offer", (q,)))
            else:
                pool = list(s.face_up) + list(s.hands[s.active])
                for b in sorted(set(pool)):
                    if pool.count(b) > s.offer_give.count(b): a.append(Action("add_give", (b,)))
                pool = list(s.hands[s.offer_partner])
                for b in sorted(set(pool)):
                    if pool.count(b) > s.offer_ask.count(b): a.append(Action("add_ask", (b,)))
                if s.offer_give: a.append(Action("propose_offer"))
                a.append(Action("cancel_offer"))
        elif s.phase == "respond":
            a += [Action("accept_offer"), Action("reject_offer")]
        elif s.phase == "plant_received":
            cards = s.received[p] + (s.face_up if p == s.active else ())
            if cards:
                for bean in sorted(set(cards)):
                    for i, f in enumerate(s.fields[p]):
                        if not f or f[0] == bean: a.append(Action("plant_received", (bean, i)))
            else:
                a.append(Action("finish_received"))
        elif s.phase == "draw_round":
            a.append(Action("draw_one"))
        return tuple(a)

    def _draw(self, s):
        if not s.deck:
            return s, None
        d = list(s.deck); card = d.pop(); count = s.empty_count
        discard = s.discard
        if not d:
            count += 1
            if count < 3 and discard:
                d = list(discard); random.Random(self.seed + count).shuffle(d); discard = ()
        return replace(s, deck=tuple(d), discard=discard, empty_count=count), card

    def _finish_game(self, s):
        # All fields are harvested; hands and unplanted cards do not score.
        for p in range(s.players):
            for i in range(len(s.fields[p])):
                if s.fields[p][i]: s = self._harvest(s, p, i, forced=True)
        return replace(s, terminal=True, phase="terminal")

    def _harvest(self, s, p, i, forced=False):
        if not forced and not self._harvestable(s, p, i): raise ValueError("protected field")
        field = s.fields[p][i]; n = len(field); bean = field[0]
        reward = 0; new_count = s.field_counts[p]
        if bean == "Ackerbohne":
            if n == 2 and new_count == 2: new_count = 3
            elif n >= 3: reward = 3
        else:
            for threshold, gold in BEANS[bean][1]:
                if n >= threshold: reward = gold
        fs = list(s.fields[p]); fs[i] = ()
        if new_count > len(fs): fs.append(())
        fields = self._replace_at(s.fields, p, tuple(fs))
        coins = self._replace_at(s.coins, p, s.coins[p] + reward)
        counts = self._replace_at(s.field_counts, p, new_count)
        # Reward cards become coins; all remaining beans are discarded.
        return replace(s, fields=fields, coins=coins, field_counts=counts,
                       discard=s.discard + field[reward:])

    @staticmethod
    def _remove_multiset(seq, items):
        x = list(seq)
        for item in items: x.remove(item)
        return tuple(x)

    def apply_action(self, s: GameState, action: Action):
        if action not in self.legal_actions(s): raise ValueError("illegal action")
        k, z = action.kind, action.args
        if k == "harvest": return self._harvest(s, *z)
        p = s.actor
        if k == "plant_front":
            i, = z; b = s.hands[p][0]; hs = self._replace_at(s.hands, p, s.hands[p][1:])
            fs = list(s.fields[p]); fs[i] += (b,)
            return replace(s, hands=hs, fields=self._replace_at(s.fields, p, tuple(fs)), first_planted=s.first_planted + 1)
        if k == "finish_hand_planting":
            x = replace(s, phase="trade", actor=s.active, first_planted=0)
            x, c1 = self._draw(x); x, c2 = self._draw(x)
            face = tuple(c for c in (c1, c2) if c is not None)
            if x.empty_count >= 3 and not face: return self._finish_game(x)
            return replace(x, face_up=face)
        if k == "begin_offer": return replace(s, offer_partner=z[0], offer_give=(), offer_ask=())
        if k == "add_give": return replace(s, offer_give=s.offer_give + (z[0],))
        if k == "add_ask": return replace(s, offer_ask=s.offer_ask + (z[0],))
        if k == "cancel_offer": return replace(s, offer_partner=-1, offer_give=(), offer_ask=())
        if k == "propose_offer":
            offer = (s.active, s.offer_partner, s.offer_give, s.offer_ask)
            return replace(s, phase="respond", actor=s.offer_partner, pending_offer=offer)
        if k == "reject_offer": return replace(s, phase="trade", actor=s.active, pending_offer=None, offer_partner=-1, offer_give=(), offer_ask=())
        if k == "accept_offer":
            active, q, give, ask = s.pending_offer
            hands = s.hands; face = s.face_up
            give_face = []
            active_hand_give = []
            temp_face = list(face)
            for b in give:
                if b in temp_face: temp_face.remove(b); give_face.append(b)
                else: active_hand_give.append(b)
            hands = self._replace_at(hands, active, self._remove_multiset(hands[active], active_hand_give))
            hands = self._replace_at(hands, q, self._remove_multiset(hands[q], ask))
            rec = s.received
            rec = self._replace_at(rec, q, rec[q] + give)
            rec = self._replace_at(rec, active, rec[active] + ask)
            return replace(s, hands=hands, face_up=tuple(temp_face), received=rec, phase="trade", actor=active,
                           pending_offer=None, offer_partner=-1, offer_give=(), offer_ask=())
        if k == "finish_trading": return replace(s, phase="plant_received", actor=s.active, offer_partner=-1)
        if k == "plant_received":
            b, i = z; rec = s.received; face = s.face_up
            if b in rec[p]: rec = self._replace_at(rec, p, self._remove_multiset(rec[p], (b,)))
            else: face = self._remove_multiset(face, (b,))
            fs = list(s.fields[p]); fs[i] += (b,)
            return replace(s, received=rec, face_up=face, fields=self._replace_at(s.fields, p, tuple(fs)))
        if k == "finish_received":
            q = (p + 1) % s.players
            if q != s.active: return replace(s, actor=q)
            return replace(s, phase="draw_round", actor=s.active, draw_left=s.players)
        if k == "draw_one":
            x, card = self._draw(s)
            if card is not None:
                hs = self._replace_at(x.hands, p, x.hands[p] + (card,)); x = replace(x, hands=hs)
            if x.empty_count >= 3: return self._finish_game(x)
            left = s.draw_left - 1
            if left:
                return replace(x, actor=(p + 1) % s.players, draw_left=left)
            active = (s.active + 1) % s.players
            return replace(x, active=active, actor=active, phase="plant_hand", draw_left=0)
        raise ValueError(k)

    def is_terminal(self, state): return state.terminal

    def returns(self, state):
        if not state.terminal: return (0,) * state.players
        best = max(state.coins)
        # Ties: clockwise farthest from the fixed starting player (player 0).
        winners = [p for p, c in enumerate(state.coins) if c == best]
        winner = max(winners)
        return tuple(1 if p == winner else -1 for p in range(state.players))

    def render(self, s):
        return json.dumps({"active": s.active, "actor": s.actor, "phase": s.phase,
                           "hands": [list(h) for h in s.hands], "fields": s.fields,
                           "coins": s.coins, "face_up": s.face_up,
                           "deck_count": len(s.deck), "empty_count": s.empty_count}, ensure_ascii=False, default=list)

    def action_to_name(self, action):
        return json.dumps([action.kind, list(action.args)], ensure_ascii=False, separators=(",", ":"))

    def name_to_action(self, name):
        kind, args = json.loads(name)
        return Action(kind, tuple(args))
