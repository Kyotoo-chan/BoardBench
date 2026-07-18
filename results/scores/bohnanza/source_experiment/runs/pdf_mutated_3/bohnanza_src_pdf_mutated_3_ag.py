"""Source-bounded model of Bohnanza, variant 2 (four or five players).

Actions are strings.  The model uses a reproducible shuffle so that chance is
inspectable, and keeps ordered hands in state (callers should treat other hands
as private information).  Trading is built card-by-card, then accepted or
rejected, which represents arbitrary unequal exchanges without enormous action
lists.
"""
from dataclasses import dataclass, replace
import random
from typing import Optional, Tuple

BEANS = ("Blaue Bohne", "Feuerbohne", "Saubohne", "Brechbohne", "Sojabohne",
         "Augenbohne", "Rote Bohne", "Gartenbohne", "Weinbrandbohne", "Ackerbohne")
COUNTS = (20, 18, 16, 14, 12, 10, 8, 6, 22, 3)
METER = {
    "Blaue Bohne": ((4,1),(6,2),(8,3),(10,4)),
    "Feuerbohne": ((3,1),(6,2),(8,3),(9,4)),
    "Saubohne": ((3,1),(5,2),(7,3),(8,4)),
    "Brechbohne": ((3,1),(5,2),(6,3),(7,4)),
    "Sojabohne": ((2,1),(4,2),(6,3),(7,4)),
    "Augenbohne": ((2,1),(4,2),(5,3),(6,4)),
    "Rote Bohne": ((2,1),(3,2),(4,3),(5,4)),
    "Gartenbohne": ((2,2),(3,3)),
    "Weinbrandbohne": ((4,1),(7,2),(9,3),(11,4)),
}

@dataclass(frozen=True)
class Offer:
    other: int
    give_hand: Tuple[int, ...] = ()
    give_face: Tuple[int, ...] = ()
    receive_hand: Tuple[int, ...] = ()

@dataclass(frozen=True)
class GameState:
    players: int
    active: int
    phase: str
    deck: Tuple[str, ...]
    discard: Tuple[str, ...]
    hands: Tuple[Tuple[str, ...], ...]
    fields: Tuple[Tuple[Tuple[str, ...], ...], ...]
    coins: Tuple[int, ...]
    third_field: Tuple[bool, ...]
    face_up: Tuple[str, ...] = ()
    pending: Tuple[Tuple[str, ...], ...] = ()
    planter: int = 0
    plants_left: int = 0
    offer: Optional[Offer] = None
    end_pending: bool = False
    winner_returns: Tuple[float, ...] = ()

class Game:
    def __init__(self, players: int = 4, seed: int = 0):
        if players not in (4, 5):
            raise ValueError("Variante 2 requires 4-5 Spieler")
        self.players, self.seed = players, seed

    def initial_state(self) -> GameState:
        cards = [b for b, n in zip(BEANS, COUNTS) for _ in range(n)]
        random.Random(self.seed).shuffle(cards)
        hands = tuple(tuple(cards[p*5:(p+1)*5]) for p in range(self.players))
        deck = tuple(cards[self.players*5:])
        fields = tuple(((), ()) for _ in range(self.players))
        return GameState(self.players, 0, "plant_hand", deck, (), hands, fields,
                         (0,)*self.players, (False,)*self.players,
                         pending=tuple(() for _ in range(self.players)), plants_left=2)

    def current_player(self, s: GameState) -> int:
        if s.phase == "respond" and s.offer is not None:
            return s.offer.other
        if s.phase == "plant_trades": return s.planter
        return s.active

    def is_terminal(self, s: GameState) -> bool: return s.phase == "terminal"
    def returns(self, s: GameState) -> Tuple[float, ...]:
        return s.winner_returns if self.is_terminal(s) else (0.0,)*s.players

    def legal_actions(self, s: GameState):
        if self.is_terminal(s): return ()
        a = s.active
        actions = []
        if s.phase == "plant_hand":
            if not s.hands[a]: actions.append("FINISH_HAND_PLANTING")
            else:
                actions += self._plant_actions(s, a, s.hands[a][0], "HAND")
                if s.plants_left == 1: actions.append("SKIP_SECOND_HAND_CARD")
        elif s.phase == "trade":
            actions.append("END_TRADING")
            for p in range(s.players):
                if p != a: actions.append(f"START_OFFER_TO:{p}")
            actions += self._voluntary_harvests(s, a)
        elif s.phase == "build_offer":
            o = s.offer; assert o
            actions.append("CANCEL_OFFER")
            selected_h = set(o.give_hand)
            selected_f = set(o.give_face)
            selected_r = set(o.receive_hand)
            for i, b in enumerate(s.hands[a]):
                if i not in selected_h: actions.append(f"OFFER_GIVE_HAND:{i}:{b}")
            for i, b in enumerate(s.face_up):
                if i not in selected_f: actions.append(f"OFFER_GIVE_FACEUP:{i}:{b}")
            for i, b in enumerate(s.hands[o.other]):
                if i not in selected_r: actions.append(f"OFFER_REQUEST_HAND:{i}:{b}")
            if o.give_hand or o.give_face or o.receive_hand:
                actions.append("SUBMIT_OFFER")
        elif s.phase == "respond": actions += ["ACCEPT_OFFER", "REJECT_OFFER"]
        elif s.phase == "plant_trades":
            p = s.planter
            if not s.pending[p]: actions.append("FINISH_TRADED_PLANTING")
            else:
                for i, b in enumerate(s.pending[p]):
                    actions += self._plant_actions(s, p, b, f"TRADED:{i}")
        elif s.phase == "draw": actions.append("DRAW_THREE_CARDS")
        return tuple(actions)

    def _voluntary_harvests(self, s, p):
        return [f"HARVEST:{i}" for i, f in enumerate(s.fields[p]) if f and self._harvest_allowed(s.fields[p], i)]

    @staticmethod
    def _harvest_allowed(fields, i):
        return len(fields[i]) > 1 or not any(len(f) > 1 for f in fields)

    def _plant_actions(self, s, p, bean, source):
        out = []
        for i, field in enumerate(s.fields[p]):
            if not field or field[0] == bean:
                out.append(f"PLANT_{source}:{i}:{bean}")
            elif self._harvest_allowed(s.fields[p], i):
                out.append(f"HARVEST_AND_PLANT_{source}:{i}:{bean}")
        return out

    def apply_action(self, s: GameState, action: str) -> GameState:
        if action not in self.legal_actions(s): raise ValueError(f"illegal action: {action}")
        a = s.active
        if action.startswith("HARVEST:"):
            return self._harvest(s, a, int(action.split(":")[1]))
        if action.startswith("PLANT_HAND:") or action.startswith("HARVEST_AND_PLANT_HAND:"):
            i = int(action.split(":")[1]); hs = list(s.hands); bean = hs[a][0]; hs[a] = hs[a][1:]
            if action.startswith("HARVEST_"): s = self._harvest(s, a, i)
            s = replace(s, hands=tuple(hs)); s = self._put_field(s, a, i, bean)
            left = s.plants_left - 1
            return replace(s, plants_left=left) if left else self._reveal(s)
        if action in ("SKIP_SECOND_HAND_CARD", "FINISH_HAND_PLANTING"): return self._reveal(s)
        if action.startswith("START_OFFER_TO:"):
            return replace(s, phase="build_offer", offer=Offer(int(action.split(":")[1])))
        if s.phase == "build_offer":
            if action == "CANCEL_OFFER": return replace(s, phase="trade", offer=None)
            if action == "SUBMIT_OFFER": return replace(s, phase="respond")
            kind, idx, _ = action.split(":", 2); i=int(idx); o=s.offer; assert o
            if kind == "OFFER_GIVE_HAND": o=replace(o, give_hand=o.give_hand+(i,))
            elif kind == "OFFER_GIVE_FACEUP": o=replace(o, give_face=o.give_face+(i,))
            else: o=replace(o, receive_hand=o.receive_hand+(i,))
            return replace(s, offer=o)
        if action == "REJECT_OFFER": return replace(s, phase="trade", offer=None)
        if action == "ACCEPT_OFFER": return self._accept(s)
        if action == "END_TRADING":
            pend = [list(x) for x in s.pending]
            pend[a].extend(s.face_up)
            return replace(s, phase="plant_trades", pending=tuple(tuple(x) for x in pend),
                           face_up=(), planter=a, offer=None)
        if action.startswith("PLANT_TRADED:") or action.startswith("HARVEST_AND_PLANT_TRADED:"):
            parts=action.split(":"); i=int(parts[-2]); bean=parts[-1]; p=s.planter
            field_i=int(parts[1]) if action.startswith("PLANT_") else int(parts[1])
            # format is PREFIX:field:bean for source containing TRADED:index -> actually four parts
            field_i=int(parts[-2]) if len(parts)==3 else int(parts[-2])
            # recover pending index from embedded TRADED token format
            prefix=parts[0]; pending_i=int(prefix.split("TRADED:")[-1]) if "TRADED:" in prefix else 0
            # normal parser below handles emitted PLANT_TRADED:<pending>:<field>:<bean>
            if len(parts)==4: pending_i=int(parts[1]); field_i=int(parts[2]); bean=parts[3]
            pend=[list(x) for x in s.pending]; pend[p].pop(pending_i)
            if action.startswith("HARVEST_"): s=self._harvest(s,p,field_i)
            s=replace(s,pending=tuple(tuple(x) for x in pend)); return self._put_field(s,p,field_i,bean)
        if action == "FINISH_TRADED_PLANTING":
            nxt=(s.planter+1)%s.players
            if nxt == a: return replace(s, phase="draw", planter=nxt)
            return replace(s, planter=nxt)
        if action == "DRAW_THREE_CARDS": return self._draw_and_advance(s)
        raise AssertionError(action)

    def _reveal(self, s):
        n=min(2,len(s.deck)); face=s.deck[:n]; deck=s.deck[n:]
        return replace(s, phase="trade", deck=deck, face_up=face,
                       end_pending=s.end_pending or not deck)

    def _put_field(self,s,p,i,bean):
        fs=[list(map(tuple,x)) for x in s.fields]; row=list(fs[p]); row[i]=row[i]+(bean,); fs[p]=row
        return replace(s,fields=tuple(tuple(x) for x in fs))

    def _harvest(self,s,p,i):
        field=s.fields[p][i]; bean=field[0]; n=len(field); coins=list(s.coins); third=list(s.third_field)
        if bean == "Ackerbohne":
            gain=3 if n>=3 else 0
            if n==2 and not third[p]: third[p]=True
        else: gain=max((g for threshold,g in METER[bean] if n>=threshold),default=0)
        coins[p]+=gain; gold=field[:gain]; rest=field[gain:]
        fs=[list(x) for x in s.fields]; fs[p][i]=()
        if third[p] and len(fs[p])==2: fs[p].append(())
        return replace(s,fields=tuple(tuple(x) for x in fs),coins=tuple(coins),third_field=tuple(third),
                       discard=s.discard+rest)

    def _accept(self,s):
        o=s.offer; assert o; a=s.active; hs=[list(x) for x in s.hands]; face=list(s.face_up); pend=[list(x) for x in s.pending]
        give=[hs[a][i] for i in o.give_hand]+[face[i] for i in o.give_face]
        receive=[hs[o.other][i] for i in o.receive_hand]
        for i in sorted(o.give_hand,reverse=True): hs[a].pop(i)
        for i in sorted(o.give_face,reverse=True): face.pop(i)
        for i in sorted(o.receive_hand,reverse=True): hs[o.other].pop(i)
        pend[o.other].extend(give); pend[a].extend(receive)
        return replace(s,phase="trade",hands=tuple(tuple(x) for x in hs),face_up=tuple(face),
                       pending=tuple(tuple(x) for x in pend),offer=None)

    def _draw_and_advance(self,s):
        hs=[list(x) for x in s.hands]; n=min(3,len(s.deck)); hs[s.active].extend(s.deck[:n]); deck=s.deck[n:]
        if s.end_pending or not deck: return self._finish(replace(s,hands=tuple(tuple(x) for x in hs),deck=deck))
        nxt=(s.active+1)%s.players
        return replace(s,active=nxt,phase="plant_hand",hands=tuple(tuple(x) for x in hs),deck=deck,
                       plants_left=2,planter=nxt,pending=tuple(() for _ in range(s.players)))

    def _finish(self,s):
        # All fields are harvested; hand cards do not score.
        for p in range(s.players):
            for i in range(len(s.fields[p])):
                if s.fields[p][i]: s=self._harvest(s,p,i)
        best=max(s.coins); winners=[p for p,c in enumerate(s.coins) if c==best]
        if len(winners)>1:
            order=[(s.active-k)%s.players for k in range(s.players)]
            winner=next(p for p in order if p in winners)
        else: winner=winners[0]
        ret=tuple(1.0 if p==winner else -1.0 for p in range(s.players))
        return replace(s,phase="terminal",winner_returns=ret)

    def action_to_name(self, action): return str(action)
    def name_to_action(self, name): return str(name)
    def render(self,s):
        return (f"phase={s.phase} active={s.active} deck={len(s.deck)} face_up={list(s.face_up)}\n"
                f"coins={s.coins} fields={s.fields} hand_sizes={tuple(map(len,s.hands))}")
