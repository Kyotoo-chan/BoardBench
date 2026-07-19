"""Source-faithful Bohnanza Ackerbohnen variant for four or five players."""
from dataclasses import dataclass, field
import copy, json, random

BEANS = ("blaue_bohne","feuerbohne","saubohne","brechbohne","sojabohne",
         "augenbohne","rote_bohne","gartenbohne","weinbrandbohne","ackerbohne")
COUNTS = dict(zip(BEANS, (20,18,16,14,12,10,8,6,22,3)))
METERS = {
 "blaue_bohne":((4,1),(6,2),(8,3),(10,4)), "feuerbohne":((3,1),(6,2),(8,3),(9,4)),
 "saubohne":((3,1),(5,2),(7,3),(8,4)), "brechbohne":((3,1),(5,2),(6,3),(7,4)),
 "sojabohne":((2,1),(4,2),(6,3),(7,4)), "augenbohne":((2,1),(4,2),(5,3),(6,4)),
 "rote_bohne":((2,1),(3,2),(4,3),(5,4)), "gartenbohne":((2,2),(3,3)),
 "weinbrandbohne":((4,1),(7,2),(9,3),(11,4)), "ackerbohne":((3,3),)}
PHASES={"plant_first","plant_second","reveal","trade","trade_response","plant_received","draw","terminal"}
TYPES={"plant","harvest","reveal","trade_start","trade_add_offer_card","trade_add_request_card",
       "trade_submit","trade_accept","trade_reject","gift_propose","gift_accept","gift_reject",
       "end_trade","draw","pass","reorder_hand"}

@dataclass(frozen=True)
class Action:
    type: str
    actor: int
    args: tuple = ()

def A(kind, actor, **kwargs): return Action(kind, actor, tuple(sorted(kwargs.items())))
def args(a): return dict(a.args)

@dataclass
class Player:
    id:int; hand:list=field(default_factory=list); fields:list=field(default_factory=lambda:[[],[]])
    coins:int=0; third_field:bool=False; alive:bool=True

@dataclass
class GameState:
    configuration:dict; current_player:int; active_player:int; start_player:int; phase:str
    terminal:bool; players:list; deck:list; discard:list=field(default_factory=list)
    revealed:list=field(default_factory=list); pending_received:list=field(default_factory=list)
    reserve:list=field(default_factory=list); depletions:int=0; pending:dict|None=None
    chance:dict=field(default_factory=dict); end_after_plant:bool=False

class Game:
    def __init__(self, num_players=None, seed=None):
        self.num_players = 4 if num_players is None else num_players
        if self.num_players not in (4,5): raise ValueError("Ackerbohnen variant requires 4 or 5 players")
        if seed is not None and (type(seed) is not int): raise TypeError("seed must be int or None")
        self.seed=seed

    def initial_state(self):
        deck=[b for b in BEANS for _ in range(COUNTS[b])]
        random.Random(self.seed).shuffle(deck)
        ps=[Player(i) for i in range(self.num_players)]
        for _ in range(5):
            for p in ps: p.hand.append(deck.pop())
        return GameState({"players":self.num_players,"seed":self.seed},0,0,0,"plant_first",False,ps,deck,
                         pending_received=[[] for _ in ps],chance={"seed":self.seed,"draw_index":5*self.num_players})

    def current_player(self,s): return s.current_player
    def is_terminal(self,s): return s.terminal
    def returns(self,s):
        if not s.terminal: return [0.0]*len(s.players)
        best=max(p.coins for p in s.players)
        # Farthest clockwise from start wins a tie.
        tied=[p.id for p in s.players if p.coins==best]
        winner=max(tied,key=lambda i:(i-s.start_player)%len(s.players))
        return [1.0 if p.id==winner else 0.0 for p in s.players]

    def _can_plant(self,p,b): return any(not f or f[0]==b for f in p.fields)
    def _plant_actions(self,s,actor,source):
        p=s.players[actor]; cards=p.hand if source=="hand" else s.pending_received[actor]
        indices=[0] if source=="hand" and cards else list(range(len(cards)))
        out=[]
        for i in indices:
            b=cards[i]
            for fi,f in enumerate(p.fields):
                if not f or f[0]==b: out.append(A("plant",actor,source=source,index=i,field=fi,bean=b))
        return out
    def _harvest_actions(self,s,actor,forced=False):
        if actor!=s.active_player and not forced: return []
        p=s.players[actor]; multi=any(len(f)>1 for f in p.fields)
        return [A("harvest",actor,field=i) for i,f in enumerate(p.fields) if f and not(len(f)==1 and multi)]

    def legal_actions(self,s):
        if s.terminal:return []
        a=s.current_player; p=s.players[a]
        if s.phase=="plant_first":
            if not p.hand:return [A("pass",a)]
            plants=self._plant_actions(s,a,"hand")
            return plants+self._harvest_actions(s,a) if not plants else plants+self._harvest_actions(s,a)
        if s.phase=="plant_second": return [A("pass",a)]+self._plant_actions(s,a,"hand")+self._harvest_actions(s,a)
        if s.phase=="reveal": return [A("reveal",a)]
        if s.phase=="trade":
            if s.pending and s.pending["type"]=="draft":
                q=s.pending; partner=q["partner"]; out=[A("trade_reject",a)]
                used={(x["owner"],x["zone"],x["index"]) for x in q["offered"]+q["requested"]}
                for zone,cards in (("hand",p.hand),("revealed",s.revealed)):
                    for i,b in enumerate(cards):
                        if (a,zone,i) not in used: out.append(A("trade_add_offer_card",a,owner=a,zone=zone,index=i,bean=b))
                for i,b in enumerate(s.players[partner].hand):
                    if (partner,"hand",i) not in used: out.append(A("trade_add_request_card",a,owner=partner,zone="hand",index=i,bean=b))
                if q["offered"] and q["requested"]:out.append(A("trade_submit",a))
                return out
            out=[A("end_trade",a)]
            for partner in range(len(s.players)):
                if partner==a:continue
                # Start a proposal; cards are added explicitly afterwards.
                out.append(A("trade_start",a,partner=partner))
                for zone,cards,owner in (("revealed",s.revealed,a),("hand",p.hand,a),("hand",s.players[partner].hand,partner)):
                    for i,b in enumerate(cards): out.append(A("gift_propose",a,partner=partner,owner=owner,zone=zone,index=i,bean=b))
            return out
        if s.phase=="trade_response":
            k="gift" if s.pending["type"]=="gift" else "trade"
            return [A(k+"_accept",a),A(k+"_reject",a)]
        if s.phase=="plant_received":
            cards=s.pending_received[a]
            if not cards:return [A("pass",a)]
            plants=self._plant_actions(s,a,"pending")
            return plants+(self._harvest_actions(s,a,forced=True) if not plants else self._harvest_actions(s,a))
        if s.phase=="draw": return [A("draw",a)]
        # proposal construction uses trade phase plus pending type draft
        return []

    def _draw_one(self,s,context):
        if not s.deck:
            s.depletions+=1
            if s.depletions>=3:
                if context=="reveal": s.end_after_plant=True
                else: self._finish(s)
                return None
            s.deck=s.discard; s.discard=[]
            random.Random((s.chance["seed"],s.chance["draw_index"]).__repr__()).shuffle(s.deck)
        if not s.deck:return None
        s.chance["draw_index"]+=1
        return s.deck.pop()

    def _harvest(self,s,p,fi):
        f=p.fields[fi]; b=f[0]; n=len(f)
        if b=="ackerbohne" and n==2:
            if not p.third_field: p.third_field=True; p.fields.append([])
            s.discard.extend(f)
        else:
            value=max((gold for need,gold in METERS[b] if n>=need),default=0)
            p.coins+=value; s.discard.extend(f[value:]) # coin cards leave circulation
        p.fields[fi]=[]

    def apply_action(self,state,action):
        s=copy.deepcopy(state)
        if action not in self.legal_actions(s): raise ValueError("illegal action")
        a=action.actor; d=args(action); p=s.players[a]
        if action.type=="harvest": self._harvest(s,p,d["field"]); return s
        if action.type=="plant":
            cards=p.hand if d["source"]=="hand" else s.pending_received[a]
            b=cards.pop(d["index"]); p.fields[d["field"]].append(b)
            if s.phase=="plant_first": s.phase="plant_second"
            elif s.phase=="plant_received" and not s.pending_received[a]: self._advance_planter(s)
            return s
        if action.type=="pass":
            if s.phase in ("plant_first","plant_second"): s.phase="reveal"
            else:self._advance_planter(s)
        elif action.type=="reveal":
            for _ in range(2):
                c=self._draw_one(s,"reveal")
                if c is not None:s.revealed.append(c)
            s.phase="trade"; s.current_player=s.active_player
        elif action.type=="trade_start":
            partner=d["partner"]; s.pending={"type":"draft","actor":a,"partner":partner,"offered":[],"requested":[],"awaiting_player":None}
            # Draft construction is encoded by subsequent add actions exposed below.
            s.phase="trade"; s.current_player=a
        elif action.type in ("trade_add_offer_card","trade_add_request_card"):
            desc={k:d[k] for k in ("owner","zone","index","bean")}
            s.pending["offered" if action.type.endswith("offer_card") else "requested"].append(desc)
        elif action.type=="trade_submit":
            s.pending["type"]="trade";s.pending["awaiting_player"]=s.pending["partner"]
            s.phase="trade_response";s.current_player=s.pending["partner"]
        elif action.type=="gift_propose":
            desc={k:d[k] for k in ("owner","zone","index","bean")}
            s.pending={"type":"gift","actor":a,"partner":d["partner"],"offered":[desc],"requested":[],"awaiting_player":d["partner"]}
            s.phase="trade_response";s.current_player=d["partner"]
        elif action.type in ("trade_reject","gift_reject"):
            s.pending=None;s.phase="trade";s.current_player=s.active_player
        elif action.type in ("trade_accept","gift_accept"):
            self._execute_exchange(s);s.pending=None;s.phase="trade";s.current_player=s.active_player
        elif action.type=="end_trade":
            s.pending_received[s.active_player].extend(s.revealed);s.revealed=[]
            s.phase="plant_received"; self._select_planter(s)
        elif action.type=="draw":
            for _ in range(3):
                c=self._draw_one(s,"draw")
                if s.terminal:break
                if c is not None:p.hand.append(c)
            if not s.terminal:
                nxt=(s.active_player+1)%len(s.players);s.active_player=nxt;s.current_player=nxt;s.phase="plant_first"
        return s

    def _execute_exchange(self,s):
        q=s.pending
        for group,recipient in ((q["offered"],q["partner"]),(q["requested"],q["actor"])):
            for x in sorted(group,key=lambda z:z["index"],reverse=True):
                cards=s.revealed if x["zone"]=="revealed" else s.players[x["owner"]].hand
                s.pending_received[recipient].append(cards.pop(x["index"]))
    def _select_planter(self,s):
        order=[(s.active_player+i)%len(s.players) for i in range(len(s.players))]
        found=next((i for i in order if s.pending_received[i]),None)
        if found is None:
            if s.end_after_plant:self._finish(s)
            else:s.phase="draw";s.current_player=s.active_player
        else:s.current_player=found
    def _advance_planter(self,s): self._select_planter(s)
    def _finish(self,s):
        for p in s.players:
            for i in range(len(p.fields)):
                if p.fields[i]:self._harvest(s,p,i)
        s.terminal=True;s.phase="terminal";s.current_player=s.active_player

    def action_to_data(self,a): return {"schema":"boardbench/bohnanza/action/1","data":{"type":a.type,"actor":a.actor,"args":copy.deepcopy(args(a))}}
    def action_from_data(self,payload):
        self._envelope(payload,"boardbench/bohnanza/action/1");d=payload["data"]
        if set(d)!={"type","actor","args"} or d["type"] not in TYPES or type(d["actor"]) is not int or not isinstance(d["args"],dict):raise ValueError("invalid action")
        return A(d["type"],d["actor"],**d["args"])
    def action_to_name(self,a): return a.type+":"+str(a.actor)+":"+json.dumps(args(a),sort_keys=True,separators=(",",":"),ensure_ascii=False)
    def name_to_action(self,n):
        kind,actor,data=n.split(":",2);return self.action_from_data({"schema":"boardbench/bohnanza/action/1","data":{"type":kind,"actor":int(actor),"args":json.loads(data)}})

    def state_to_data(self,s):
        players=[{"id":p.id,"hand":list(p.hand),"fields":copy.deepcopy(p.fields),"coins":p.coins,"third_field":p.third_field,"alive":p.alive} for p in s.players]
        pending=None if s.pending is None else copy.deepcopy(s.pending)
        # end_after_plant is encoded as a source-defined pending marker when needed.
        if s.end_after_plant and pending is None: pending={"type":"end_after_plant","actor":s.active_player,"partner":None,"offered":[],"requested":[],"awaiting_player":None}
        data={"configuration":copy.deepcopy(s.configuration),"current_player":s.current_player,"active_player":s.active_player,"start_player":s.start_player,
              "phase":s.phase,"terminal":s.terminal,"players":players,"zones":{"deck":list(s.deck),"discard":list(s.discard),"revealed":list(s.revealed),"pending_received":copy.deepcopy(s.pending_received),"reserve":list(s.reserve)},
              "depletions":s.depletions,"pending":pending,"chance":copy.deepcopy(s.chance)}
        return {"schema":"boardbench/bohnanza/state/1","data":data}
    def state_from_data(self,payload):
        self._envelope(payload,"boardbench/bohnanza/state/1");d=copy.deepcopy(payload["data"])
        req={"configuration","current_player","active_player","start_player","phase","terminal","players","zones","depletions","pending","chance"}
        if set(d)!=req or d["phase"] not in PHASES:raise ValueError("invalid state fields")
        ps=[Player(x["id"],x["hand"],x["fields"],x["coins"],x["third_field"],x["alive"]) for x in d["players"]]
        z=d["zones"]; pending=d["pending"]; end=bool(pending and pending.get("type")=="end_after_plant")
        if end:pending=None
        return GameState(d["configuration"],d["current_player"],d["active_player"],d["start_player"],d["phase"],d["terminal"],ps,z["deck"],z["discard"],z["revealed"],z["pending_received"],z["reserve"],d["depletions"],pending,d["chance"],end)
    def observation_to_data(self,s,player):
        if type(player) is not int or not 0<=player<len(s.players):raise ValueError("invalid player")
        pending=copy.deepcopy(s.pending)
        data={"player":player,"current_player":s.current_player,"active_player":s.active_player,"phase":s.phase,"terminal":s.terminal,"own_hand":list(s.players[player].hand),
              "opponents":[{"id":p.id,"hand_size":len(p.hand)} for p in s.players if p.id!=player],"fields":[copy.deepcopy(p.fields) for p in s.players],"coins":[p.coins for p in s.players],
              "revealed":list(s.revealed),"deck_size":len(s.deck),"discard_size":len(s.discard),"pending":pending}
        return {"schema":"boardbench/bohnanza/observation/1","data":data}
    def _envelope(self,p,schema):
        if not isinstance(p,dict) or set(p)!={"schema","data"} or p["schema"]!=schema or not isinstance(p["data"],dict):raise ValueError("invalid envelope")
    def render(self,s): return f"phase={s.phase} active={s.active_player} coins={[p.coins for p in s.players]} deck={len(s.deck)}"
