"""Source-grounded model of Bohnanza, Ackerbohnen variant (4 players).

The interface intentionally uses small, serialisable tuples for actions.  Trading is
resolved as explicit offers which the named recipient may accept or reject.
"""
from dataclasses import dataclass, field
import random
from typing import Optional

BEANS = ("Blaue Bohne", "Feuerbohne", "Saubohne", "Brechbohne",
         "Sojabohne", "Augenbohne", "Rote Bohne", "Gartenbohne",
         "Weinbrandbohne", "Ackerbohne")
COUNTS = dict(zip(BEANS, (20, 18, 16, 14, 12, 10, 8, 6, 22, 3)))
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

Action = tuple

@dataclass
class GameState:
    hands: list[list[str]]
    fields: list[list[list[str]]]
    coins: list[int]
    deck: list[str]
    discard: list[str] = field(default_factory=list)
    active: int = 0
    actor: int = 0
    phase: str = "plant_first"
    revealed: list[str] = field(default_factory=list)
    acquired: list[list[str]] = field(default_factory=list)
    pending: Optional[tuple[int, int, str, Optional[str]]] = None
    empty_count: int = 0
    terminal: bool = False
    last_event: str = "Spielbeginn"

class Game:
    def __init__(self, players: int = 4, seed: Optional[int] = None):
        if players not in (4, 5):
            raise ValueError("Ackerbohnen variant is for 4-5 players")
        self.players, self.seed = players, seed

    def initial_state(self) -> GameState:
        deck = [b for b in BEANS for _ in range(COUNTS[b])]
        random.Random(self.seed).shuffle(deck)
        hands = [[] for _ in range(self.players)]
        # Dealing singly preserves the immutable front-to-back order.
        for _ in range(5):
            for h in hands: h.append(deck.pop())
        return GameState(hands, [[[], []] for _ in hands], [0]*self.players,
                         deck, acquired=[[] for _ in hands])

    def current_player(self, s): return None if s.terminal else s.actor
    def is_terminal(self, s): return s.terminal
    def returns(self, s):
        return tuple(s.coins) if s.terminal else tuple(0 for _ in s.coins)

    @staticmethod
    def _protected(s, p, f):
        nonempty = [x for x in s.fields[p] if x]
        return len(s.fields[p][f]) == 1 and any(len(x) > 1 for x in nonempty)

    @staticmethod
    def _coin_value(bean, n):
        return max((v for k,v in METER.get(bean, ()) if n >= k), default=0)

    def _can_plant(self, s, p, bean):
        return any(not f or f[0] == bean for f in s.fields[p])

    def legal_actions(self, s):
        if s.terminal: return []
        p, out = s.actor, []
        # Harvest is always permitted, subject to the bean-protection rule.
        for i,f in enumerate(s.fields[p]):
            if f and not self._protected(s,p,i): out.append(("harvest",p,i))
        if s.phase in ("plant_first", "plant_second"):
            if not s.hands[p]: return [("finish_plant",)]
            bean=s.hands[p][0]
            for i,f in enumerate(s.fields[p]):
                if not f or f[0]==bean: out.append(("plant_hand",i))
            if s.phase=="plant_second": out.append(("finish_plant",))
        elif s.phase=="trade":
            # Offers may use either an active player's hand card or a face-up card.
            offered=[]
            for i,b in enumerate(s.hands[s.active]): offered.append(("hand",i,b))
            for i,b in enumerate(s.revealed): offered.append(("revealed",i,b))
            for target in range(self.players):
                if target==s.active: continue
                for src,i,b in offered:
                    out.append(("offer_gift",target,src,i,b))
                    for j,w in enumerate(s.hands[target]):
                        out.append(("offer_trade",target,src,i,b,j,w))
            out.append(("finish_trade",))
        elif s.phase=="respond": out.extend((("accept",),("reject",)))
        elif s.phase=="plant_acquired":
            cards=s.acquired[p]
            if not cards: return [("finish_acquired",)]
            bean=cards[0]
            for i,f in enumerate(s.fields[p]):
                if not f or f[0]==bean: out.append(("plant_acquired",i))
        return out

    def apply_action(self, s, a):
        if a not in self.legal_actions(s): raise ValueError("illegal action")
        kind=a[0]; p=s.actor
        if kind=="harvest":
            _,p,i=a; f=s.fields[p][i]; bean,n=f[0],len(f)
            if bean=="Ackerbohne":
                if n>=3: s.coins[p]+=3
                elif n==2 and len(s.fields[p])==2: s.fields[p].append([])
                s.discard.extend(f)
            else:
                value=self._coin_value(bean,n); s.coins[p]+=value
                s.discard.extend(f[value:])
            s.fields[p][i]=[]; s.last_event=f"{p} erntet {bean}"
            return s
        if kind=="plant_hand":
            bean=s.hands[p].pop(0); s.fields[p][a[1]].append(bean)
            s.phase="plant_second"; s.last_event=f"{p} baut {bean} an"; return s
        if kind=="finish_plant":
            s.revealed=[]
            for _ in range(2):
                card=self._draw(s)
                if card is not None: s.revealed.append(card)
            s.phase="trade"; s.actor=s.active; return s
        if kind in ("offer_gift","offer_trade"):
            target,src,i,b=a[1:5]; wanted=None if kind=="offer_gift" else a[6]
            s.pending=(s.active,target,b,wanted); s.phase="respond"; s.actor=target
            return s
        if kind=="reject": s.pending=None; s.phase="trade"; s.actor=s.active; return s
        if kind=="accept":
            giver,target,offered,wanted=s.pending
            if offered in s.revealed: s.revealed.remove(offered)
            else: s.hands[giver].remove(offered)
            s.acquired[target].append(offered)
            if wanted is not None:
                s.hands[target].remove(wanted); s.acquired[giver].append(wanted)
            s.pending=None; s.phase="trade"; s.actor=s.active; return s
        if kind=="finish_trade":
            s.acquired[s.active].extend(s.revealed); s.revealed=[]
            s.phase="plant_acquired"; s.actor=0
            return self._advance_acquired(s)
        if kind=="plant_acquired":
            bean=s.acquired[p].pop(0); s.fields[p][a[1]].append(bean)
            return self._advance_acquired(s)
        if kind=="finish_acquired": return self._finish_turn(s)
        raise ValueError(kind)

    def _advance_acquired(self,s):
        while s.actor < self.players and not s.acquired[s.actor]: s.actor += 1
        if s.actor >= self.players: return self._finish_turn(s)
        return s

    def _draw(self,s):
        if not s.deck:
            s.empty_count += 1
            if s.empty_count >= 3: return None
            s.deck=s.discard; s.discard=[]; random.Random(self.seed).shuffle(s.deck)
        return s.deck.pop() if s.deck else None

    def _finish_turn(self,s):
        if s.empty_count>=3:
            for p in range(self.players):
                for f in s.fields[p]:
                    if f: s.coins[p]+=self._coin_value(f[0],len(f)) if f[0]!="Ackerbohne" else (3 if len(f)>=3 else 0)
            s.terminal=True; s.phase="terminal"; s.actor=s.active; return s
        for offset in range(self.players):
            p=(s.active+offset)%self.players
            card=self._draw(s)
            if card is not None: s.hands[p].append(card)
        s.active=(s.active+1)%self.players; s.actor=s.active; s.phase="plant_first"
        return s

    def action_to_name(self,a): return " | ".join(map(str,a))
    def name_to_action(self,name):
        parts=name.split(" | "); ints={"harvest":(1,2),"plant_hand":(1,),"plant_acquired":(1,),
            "offer_gift":(1,3),"offer_trade":(1,3,5)}
        for i in ints.get(parts[0],()): parts[i]=int(parts[i])
        return tuple(parts)

    def render(self,s):
        hands=[s.hands[i] if i==s.actor else ["?" for _ in s.hands[i]] for i in range(self.players)]
        return f"Phase={s.phase} active={s.active} actor={s.actor} coins={s.coins} fields={s.fields} hands={hands} revealed={s.revealed} draw={len(s.deck)}"
