"""Source-bound implementation of Bohnanza, Ackerbohnen variant (4 players).

The module intentionally uses no runtime files.  Hands are ordered tuples: index 0
is always the source rulebook's "vorderste Karte".
"""
from dataclasses import dataclass, replace
import random
from typing import Optional

Bean = str
Action = tuple

BASE = (
    ("Gartenbohne", 6, ((2, 2), (3, 3))),
    ("Rote Bohne", 8, ((2, 1), (3, 2), (4, 3), (5, 4))),
    ("Augenbohne", 10, ((2, 1), (4, 2), (5, 3), (6, 4))),
    ("Sojabohne", 12, ((2, 1), (4, 2), (6, 3), (7, 4))),
    ("Brechbohne", 14, ((3, 1), (5, 2), (6, 3), (7, 4))),
    ("Saubohne", 16, ((3, 1), (5, 2), (7, 3), (8, 4))),
    ("Feuerbohne", 18, ((3, 1), (6, 2), (8, 3), (9, 4))),
    ("Blaue Bohne", 20, ((4, 1), (6, 2), (8, 3), (10, 4))),
)
EXTRA = (
    ("Weinbrandbohne", 22, ((4, 1), (7, 2), (9, 3), (11, 4))),
    ("Ackerbohne", 3, ()),
)
BEANS = BASE + EXTRA
PAY = {name: table for name, _, table in BEANS}


@dataclass(frozen=True)
class GameState:
    hands: tuple[tuple[Bean, ...], ...]
    fields: tuple[tuple[tuple[Bean, ...], ...], ...]
    coins: tuple[int, ...]
    deck: tuple[Bean, ...]
    discard: tuple[Bean, ...] = ()
    active: int = 0
    actor: int = 0
    phase: str = "plant1"
    face_up: tuple[Bean, ...] = ()
    pending: tuple[tuple[Bean, ...], ...] = ((), (), (), ())
    planted_second: bool = False
    recycle_count: int = 0
    ending: bool = False
    ended: bool = False
    turn: int = 0


class Game:
    """Four-player Ackerbohnen condition; seed controls the explicit shuffle chance."""

    def __init__(self, seed: int = 0):
        self.seed = seed

    def initial_state(self) -> GameState:
        cards = [b for b, n, _ in BEANS for _ in range(n)]
        random.Random(self.seed).shuffle(cards)
        hands = [[] for _ in range(4)]
        for _ in range(5):
            for p in range(4):
                hands[p].append(cards.pop())
        return GameState(tuple(tuple(h) for h in hands),
                         tuple(((), ()) for _ in range(4)), (0, 0, 0, 0),
                         tuple(cards), pending=((), (), (), ()))

    def current_player(self, state: GameState) -> Optional[int]:
        return None if state.ended else state.actor

    @staticmethod
    def _harvestable(state: GameState, p: int, i: int) -> bool:
        fs = state.fields[p]
        if not fs[i]: return False
        # Bohnenschutzregel: a singleton cannot be harvested while any field has >1.
        return len(fs[i]) > 1 or not any(len(f) > 1 for f in fs)

    @staticmethod
    def _plant_slots(state: GameState, p: int, bean: Bean) -> list[int]:
        return [i for i, f in enumerate(state.fields[p]) if not f or f[0] == bean]

    def legal_actions(self, s: GameState) -> list[Action]:
        if s.ended: return []
        p = s.actor
        harvests = [("harvest", p, i) for i in range(len(s.fields[p]))
                    if self._harvestable(s, p, i)]
        if s.phase in ("plant1", "plant2"):
            if not s.hands[p]: return [("advance",)]
            bean = s.hands[p][0]
            plants = [("plant_hand", i) for i in self._plant_slots(s, p, bean)]
            if s.phase == "plant2": plants.append(("skip_second",))
            return plants + harvests
        if s.phase == "trade":
            a = s.active
            out = []
            # Atomic, consensual exchanges: one offered card for one requested card.
            # The active player may offer a hand card or either face-up card.
            offers = [("hand", i, b) for i, b in enumerate(s.hands[a])]
            offers += [("face", i, b) for i, b in enumerate(s.face_up)]
            for q in range(4):
                if q == a: continue
                for src, oi, _ in offers:
                    for qi in range(len(s.hands[q])):
                        out.append(("trade", q, src, oi, qi))
                for src, oi, _ in offers:
                    out.append(("gift", q, src, oi))
                for qi in range(len(s.hands[q])):
                    out.append(("gift_to_active", q, qi))
            out.append(("end_trade",))
            return out + harvests
        if s.phase == "plant_pending":
            if not s.pending[p]: return [("done_planting",)]
            bean = s.pending[p][0]
            return [("plant_pending", i) for i in self._plant_slots(s, p, bean)] + harvests
        if s.phase == "draw": return [("draw_three",)]
        raise ValueError(s.phase)

    def _set_player(self, seq, p, value):
        x = list(seq); x[p] = value; return tuple(x)

    def _harvest(self, s: GameState, p: int, i: int) -> GameState:
        field = s.fields[p][i]; bean = field[0]; n = len(field)
        fs = list(s.fields[p]); fs[i] = ()
        fields = self._set_player(s.fields, p, tuple(fs))
        coins = list(s.coins); discard = list(s.discard)
        if bean == "Ackerbohne":
            if n == 2 and len(fs) == 2: fs.append(()); fields = self._set_player(fields, p, tuple(fs))
            elif n >= 3: coins[p] += 3
            discard.extend(field)
        else:
            earned = 0
            for threshold, gold in PAY[bean]:
                if n >= threshold: earned = gold
            coins[p] += earned
            # Coin cards come from the harvested cards; their bean faces form score pile.
            discard.extend(field[earned:])
        return replace(s, fields=fields, coins=tuple(coins), discard=tuple(discard))

    def apply_action(self, s: GameState, action: Action) -> GameState:
        if action not in self.legal_actions(s): raise ValueError("illegal action")
        k = action[0]; p = s.actor
        if k == "harvest": return self._harvest(s, action[1], action[2])
        if k == "advance": return replace(s, phase="draw")
        if k == "plant_hand":
            i = action[1]; hs = s.hands[p]; fs = list(s.fields[p]); fs[i] += (hs[0],)
            ns = replace(s, hands=self._set_player(s.hands, p, hs[1:]),
                         fields=self._set_player(s.fields, p, tuple(fs)))
            return replace(ns, phase="plant2") if s.phase == "plant1" else self._reveal(ns)
        if k == "skip_second": return self._reveal(s)
        if k == "trade":
            q, src, oi, qi = action[1:]; ah=list(s.hands[s.active]); qh=list(s.hands[q]); fu=list(s.face_up)
            offered = ah.pop(oi) if src == "hand" else fu.pop(oi); requested=qh.pop(qi)
            pend=list(s.pending); pend[q] += (offered,); pend[s.active] += (requested,)
            return replace(s,hands=self._set_player(self._set_player(s.hands,s.active,tuple(ah)),q,tuple(qh)),face_up=tuple(fu),pending=tuple(pend))
        if k in ("gift", "gift_to_active"):
            q=action[1]; pend=list(s.pending)
            if k=="gift":
                src,oi=action[2:]; ah=list(s.hands[s.active]); fu=list(s.face_up)
                bean=ah.pop(oi) if src=="hand" else fu.pop(oi); pend[q]+=(bean,)
                return replace(s,hands=self._set_player(s.hands,s.active,tuple(ah)),face_up=tuple(fu),pending=tuple(pend))
            qh=list(s.hands[q]); bean=qh.pop(action[2]); pend[s.active]+=(bean,)
            return replace(s,hands=self._set_player(s.hands,q,tuple(qh)),pending=tuple(pend))
        if k == "end_trade":
            pend=list(s.pending); pend[s.active] += s.face_up
            return replace(s, face_up=(), pending=tuple(pend), phase="plant_pending", actor=s.active)
        if k == "plant_pending":
            i=action[1]; bean=s.pending[p][0]; fs=list(s.fields[p]); fs[i]+=(bean,); pend=list(s.pending); pend[p]=pend[p][1:]
            return replace(s,fields=self._set_player(s.fields,p,tuple(fs)),pending=tuple(pend))
        if k == "done_planting":
            nxt = next((q for q in list(range(p+1,4))+list(range(0,p+1)) if s.pending[q]), None)
            if nxt is not None: return replace(s,actor=nxt)
            return self._finish(s) if s.ending else replace(s,phase="draw",actor=s.active)
        if k == "draw_three":
            ns=s
            for _ in range(3):
                ns, card = self._draw_one(ns)
                if card is None: break
                hs=ns.hands[ns.active]+(card,); ns=replace(ns,hands=self._set_player(ns.hands,ns.active,hs))
            if ns.ending: return self._finish(ns)
            a=(ns.active+1)%4
            return replace(ns,active=a,actor=a,phase="plant1",planted_second=False,turn=ns.turn+1)
        raise ValueError(action)

    def _reveal(self, s):
        ns=s; cards=[]
        for _ in range(2):
            ns,c=self._draw_one(ns)
            if c is None: break
            cards.append(c)
        return replace(ns,phase="trade",face_up=tuple(cards),actor=ns.active)

    def _draw_one(self, s):
        if s.deck: return replace(s,deck=s.deck[:-1]),s.deck[-1]
        count=s.recycle_count+1
        if count>=3 or not s.discard: return replace(s,recycle_count=count,ending=True),None
        cards=list(s.discard); random.Random(self.seed+count).shuffle(cards)
        ns=replace(s,deck=tuple(cards),discard=(),recycle_count=count)
        return replace(ns,deck=ns.deck[:-1]),ns.deck[-1]

    def _finish(self,s):
        # Finish immediately if exhaustion occurs during reveal; source says phases 2+3
        # continue, represented by scoring current fields without further choices.
        coins=list(s.coins)
        for p in range(4):
            for f in s.fields[p]:
                if not f: continue
                if f[0]=="Ackerbohne": coins[p] += 3 if len(f)>=3 else 0
                else:
                    earned = 0
                    for n,g in PAY[f[0]]:
                        if len(f)>=n: earned=g
                    coins[p] += earned
        return replace(s,coins=tuple(coins),ended=True,phase="terminal")

    def is_terminal(self,s): return s.ended
    def returns(self,s):
        if not s.ended: return (0,0,0,0)
        m=max(s.coins); winners=[p for p,c in enumerate(s.coins) if c==m]
        if len(winners)>1:
            # clockwise furthest from starting player = greatest player index
            winners=[max(winners)]
        return tuple(1 if p in winners else -1 for p in range(4))

    def render(self,s):
        return f"phase={s.phase} active={s.active} actor={s.actor} coins={s.coins} fields={s.fields} hand_sizes={tuple(map(len,s.hands))} deck={len(s.deck)}"

    def action_to_name(self,a): return "|".join(map(str,a))
    def name_to_action(self,name):
        parts=name.split("|"); vals=[]
        for x in parts: vals.append(int(x) if x.isdigit() else x)
        return tuple(vals)
