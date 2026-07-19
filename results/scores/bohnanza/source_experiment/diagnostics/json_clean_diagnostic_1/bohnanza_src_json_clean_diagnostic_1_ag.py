"""Source-bounded implementation of Bohnanza, Ackerbohnen variant (4 players).

The public state contains hands for inspectability, but only their owners may choose
hand cards.  Card order is always significant and is never changed.
"""
from dataclasses import dataclass, field
import random

BEANS = {
    "Blaue Bohne": (20, ((4,1),(6,2),(8,3),(10,4))),
    "Feuerbohne": (18, ((3,1),(6,2),(8,3),(9,4))),
    "Saubohne": (16, ((3,1),(5,2),(7,3),(8,4))),
    "Brechbohne": (14, ((3,1),(5,2),(6,3),(7,4))),
    "Sojabohne": (12, ((2,1),(4,2),(6,3),(7,4))),
    "Augenbohne": (10, ((2,1),(4,2),(5,3),(6,4))),
    "Rote Bohne": (8, ((2,1),(3,2),(4,3),(5,4))),
    "Gartenbohne": (6, ((2,2),(3,3))),
    "Weinbrandbohne": (22, ((4,1),(7,2),(9,3),(11,4))),
    "Ackerbohne": (3, ()),
}

@dataclass
class GameState:
    players: int = 4
    active: int = 0
    actor: int = 0
    phase: str = "plant_first"
    hands: list[list[str]] = field(default_factory=list)
    fields: list[list[list[str]]] = field(default_factory=list)
    coins: list[int] = field(default_factory=list)
    third_field: list[bool] = field(default_factory=list)
    deck: list[str] = field(default_factory=list)
    discard: list[str] = field(default_factory=list)
    table: list[str] = field(default_factory=list)
    traded: list[list[str]] = field(default_factory=list)
    empty_count: int = 0
    draw_left: int = 0
    terminal: bool = False

class Game:
    def initial_state(self):
        n = 4
        deck = [b for b,(count,_) in BEANS.items() for _ in range(count)]
        random.Random(0).shuffle(deck)
        hands = [[] for _ in range(n)]
        for p in range(n):
            for _ in range(5): hands[p].append(deck.pop())
        return GameState(hands=hands, fields=[[[],[]] for _ in range(n)],
                         coins=[0]*n, third_field=[False]*n, deck=deck,
                         traded=[[] for _ in range(n)])

    def current_player(self, s): return s.actor
    def is_terminal(self, s): return s.terminal
    def returns(self, s):
        if not s.terminal: return [0]*s.players
        m=max(s.coins); winners=[i for i,x in enumerate(s.coins) if x==m]
        # tie: clockwise furthest from start player (player 0), i.e. greatest index
        w=max(winners)
        return [1 if i==w else -1 for i in range(s.players)]

    def _harvestable(self,s,p,i):
        f=s.fields[p][i]
        if not f: return False
        if len(f)>1: return True
        return not any(len(x)>1 for x in s.fields[p])

    def legal_actions(self,s):
        if s.terminal: return []
        a=[]; p=s.actor
        # Harvesting is expressly allowed at any time, including when inactive.
        for hp in range(s.players):
            for i in range(len(s.fields[hp])):
                if self._harvestable(s,hp,i): a.append(("harvest",hp,i))
        if s.phase in ("plant_first","plant_second"):
            if s.hands[p]:
                b=s.hands[p][0]
                for i,f in enumerate(s.fields[p]):
                    if not f or f[0]==b: a.append(("plant_hand",p,i))
            elif s.phase=="plant_first": a.append(("skip_empty_hand",))
            if s.phase=="plant_second": a.append(("skip_second",))
        elif s.phase=="flip": a.append(("flip_two",))
        elif s.phase=="trade":
            # Atomic, mutually agreed exchanges: active may use table/top-level hand;
            # the partner may offer any hand card (order is not changed).
            for ti,b in enumerate(s.table):
                for q in range(s.players):
                    if q!=s.active:
                        a.append(("give_table",ti,q))
                        for hi,c in enumerate(s.hands[q]):
                            a.append(("trade_table_for_hand",ti,q,hi))
            # Active can trade any hand card; source says hand position is irrelevant.
            for hi,b in enumerate(s.hands[s.active]):
                for q in range(s.players):
                    if q!=s.active:
                        for hj,c in enumerate(s.hands[q]):
                            a.append(("trade_hands",hi,q,hj))
            a.append(("end_trade",))
        elif s.phase=="plant_traded":
            if s.traded[p]:
                for ti,b in enumerate(s.traded[p]):
                    for i,f in enumerate(s.fields[p]):
                        if not f or f[0]==b: a.append(("plant_traded",p,ti,i))
            else: a.append(("done_traded",))
        elif s.phase=="draw": a.append(("draw_one",p))
        return a

    def _draw(self,s):
        if s.empty_count>=3: return None
        if not s.deck:
            s.empty_count += 1
            if s.empty_count>=3: return None
            s.deck=s.discard; s.discard=[]
            random.Random(s.empty_count).shuffle(s.deck)
        return s.deck.pop() if s.deck else None

    def _plant(self,s,p,i,b):
        f=s.fields[p][i]
        if f and f[0]!=b: raise ValueError("wrong bean field")
        f.append(b)

    def _do_harvest(self,s,p,i):
        f=s.fields[p][i]; b=f[0]; count=len(f)
        if b=="Ackerbohne":
            if count==2:
                if not s.third_field[p]:
                    s.third_field[p]=True; s.fields[p].append([])
                s.discard.extend(f)
            elif count>=3:
                s.coins[p]+=3
                # three cards are the coins; any excess is discarded
                s.discard.extend(f[3:])
            else: s.discard.extend(f)
        else:
            gold=0
            for threshold,value in BEANS[b][1]:
                if count>=threshold: gold=value
            s.coins[p]+=gold
            s.discard.extend(f[gold:])
        s.fields[p][i]=[]

    def apply_action(self,s,a):
        if a not in self.legal_actions(s): raise ValueError("illegal action")
        k=a[0]
        if k=="harvest": self._do_harvest(s,a[1],a[2]); return s
        if k=="plant_hand":
            _,p,i=a; self._plant(s,p,i,s.hands[p].pop(0))
            s.phase="plant_second" if s.phase=="plant_first" else "flip"
        elif k=="skip_second": s.phase="flip"
        elif k=="skip_empty_hand": s.phase="flip"
        elif k=="flip_two":
            for _ in range(2):
                c=self._draw(s)
                if c is None: break
                s.table.append(c)
            s.phase="trade"
        elif k=="give_table":
            _,ti,q=a; s.traded[q].append(s.table.pop(ti))
        elif k=="trade_table_for_hand":
            _,ti,q,hi=a; s.traded[q].append(s.table.pop(ti)); s.traded[s.active].append(s.hands[q].pop(hi))
        elif k=="trade_hands":
            _,hi,q,hj=a
            x=s.hands[s.active].pop(hi); y=s.hands[q].pop(hj)
            s.traded[q].append(x); s.traded[s.active].append(y)
        elif k=="end_trade":
            s.traded[s.active].extend(s.table); s.table=[]; s.actor=s.active; s.phase="plant_traded"
        elif k=="plant_traded":
            _,p,ti,i=a; self._plant(s,p,i,s.traded[p].pop(ti))
        elif k=="done_traded":
            q=(s.actor+1)%s.players
            if q==s.active: s.phase="draw"; s.actor=s.active; s.draw_left=s.players
            else: s.actor=q
        elif k=="draw_one":
            c=self._draw(s)
            if c is not None: s.hands[s.actor].append(c)
            s.draw_left-=1
            if s.draw_left:
                s.actor=(s.actor+1)%s.players
            else:
                if s.empty_count>=3: self._finish(s)
                else:
                    s.active=(s.active+1)%s.players; s.actor=s.active; s.phase="plant_first"
        return s

    def _finish(self,s):
        for p in range(s.players):
            for i in range(len(s.fields[p])):
                if s.fields[p][i]: self._do_harvest(s,p,i)
        s.terminal=True; s.phase="terminal"

    def action_to_name(self,a): return " | ".join(map(str,a))
    def name_to_action(self,name):
        parts=name.split(" | "); out=[parts[0]]
        for x in parts[1:]:
            try: out.append(int(x))
            except ValueError: out.append(x)
        return tuple(out)
    def render(self,s):
        return f"phase={s.phase} active={s.active} actor={s.actor} coins={s.coins} hands={[len(h) for h in s.hands]} fields={s.fields} deck={len(s.deck)} empty={s.empty_count}"
