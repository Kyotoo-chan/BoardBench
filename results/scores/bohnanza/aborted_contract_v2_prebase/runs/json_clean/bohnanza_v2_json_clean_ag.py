"""Source-faithful Bohnanza Variant 2 (Ackerbohnen), for four or five players."""
from dataclasses import dataclass, field
import copy, json, random

BEANS = ("blaue_bohne","feuerbohne","saubohne","brechbohne","sojabohne","augenbohne","rote_bohne","gartenbohne","weinbrandbohne","ackerbohne")
COUNTS = {"blaue_bohne":20,"feuerbohne":18,"saubohne":16,"brechbohne":14,"sojabohne":12,"augenbohne":10,"rote_bohne":8,"gartenbohne":6,"weinbrandbohne":22,"ackerbohne":3}
METERS = {
 "blaue_bohne":((4,1),(6,2),(8,3),(10,4)), "feuerbohne":((3,1),(6,2),(8,3),(9,4)),
 "saubohne":((3,1),(5,2),(7,3),(8,4)), "brechbohne":((3,1),(5,2),(6,3),(7,4)),
 "sojabohne":((2,1),(4,2),(6,3),(7,4)), "augenbohne":((2,1),(4,2),(5,3),(6,4)),
 "rote_bohne":((2,1),(3,2),(4,3),(5,4)), "gartenbohne":((2,2),(3,3)),
 "weinbrandbohne":((4,1),(7,2),(9,3),(11,4)), "ackerbohne":((3,3),)}
PHASES = ("plant_first","plant_second","reveal","trade","trade_response","plant_received","draw","terminal")
ACTION_TYPES = {"plant","harvest","reveal","trade_start","trade_add_offer_card","trade_add_request_card","trade_submit","trade_accept","trade_reject","gift_propose","gift_accept","gift_reject","end_trade","draw","pass","reorder_hand"}

@dataclass(eq=True)
class Action:
    type: str
    actor: int
    args: dict = field(default_factory=dict)

@dataclass(eq=True)
class GameState:
    configuration: dict; current_player: int; active_player: int; start_player: int
    phase: str; terminal: bool; players: list; zones: dict; depletions: int
    pending: dict|None; chance: dict

class Game:
    def __init__(self, num_players=None, seed=None):
        self.num_players = 4 if num_players is None else num_players
        if type(self.num_players) is not int or self.num_players not in (4,5): raise ValueError("Variant 2 requires 4 or 5 players")
        if seed is not None and type(seed) is not int: raise ValueError("seed must be int or None")
        self.seed = seed

    def initial_state(self):
        deck=[b for b in BEANS for _ in range(COUNTS[b])]; random.Random(self.seed).shuffle(deck)
        ps=[]
        for i in range(self.num_players):
            hand=[deck.pop() for _ in range(5)]
            ps.append({"id":i,"hand":hand,"fields":[[],[]],"coins":0,"third_field":False,"alive":True})
        return GameState({"players":self.num_players,"seed":self.seed},0,0,0,"plant_first",False,ps,
            {"deck":deck,"discard":[],"revealed":[],"pending_received":[[] for _ in ps],"reserve":[]},0,None,{"seed":self.seed,"draw_index":5*self.num_players})

    def current_player(self,s): return s.current_player
    def is_terminal(self,s): return s.terminal
    def returns(self,s):
        if not s.terminal:return [0]*len(s.players)
        scores=[p["coins"] for p in s.players]; best=max(scores)
        # tie: clockwise farthest from start player
        winner=max((i for i,x in enumerate(scores) if x==best),key=lambda i:(i-s.start_player)%len(scores))
        return [1 if i==winner else -1 for i in range(len(scores))]

    def _harvestable(self,s,p):
        nonempty=[i for i,f in enumerate(s.players[p]["fields"]) if f]
        multi=any(len(s.players[p]["fields"][i])>1 for i in nonempty)
        return [i for i in nonempty if not (len(s.players[p]["fields"][i])==1 and multi)]
    def _can_plant(self,s,p,bean):
        return [i for i,f in enumerate(s.players[p]["fields"]) if not f or f[0]==bean]
    def legal_actions(self,s):
        if s.terminal:return []
        a=[]; cp=s.current_player; p=s.players[cp]
        for fi in self._harvestable(s,cp): a.append(Action("harvest",cp,{"field":fi}))
        if s.phase in ("plant_first","plant_second"):
            if not p["hand"]: a.append(Action("pass",cp,{}))
            else:
                for fi in self._can_plant(s,cp,p["hand"][0]): a.append(Action("plant",cp,{"source":"hand","index":0,"field":fi}))
            if s.phase=="plant_second" and p["hand"]: a.append(Action("pass",cp,{}))
        elif s.phase=="reveal": a.append(Action("reveal",cp,{}))
        elif s.phase=="trade":
            a.append(Action("end_trade",cp,{}))
            # one-card proposals cover every card; repeated trades are allowed
            for ri,b in enumerate(s.zones["revealed"]):
                for q in range(len(s.players)):
                    if q!=cp:
                        a.append(Action("gift_propose",cp,{"partner":q,"source":"revealed","index":ri,"bean":b}))
                        for hi,hb in enumerate(s.players[q]["hand"]):
                            a.append(Action("trade_start",cp,{"partner":q,"offer_source":"revealed","offer_index":ri,"offer_bean":b,"request_index":hi,"request_bean":hb}))
            for hi,b in enumerate(p["hand"]):
                for q in range(len(s.players)):
                    if q!=cp:
                        a.append(Action("gift_propose",cp,{"partner":q,"source":"hand","index":hi,"bean":b}))
                        for qi,qb in enumerate(s.players[q]["hand"]): a.append(Action("trade_start",cp,{"partner":q,"offer_source":"hand","offer_index":hi,"offer_bean":b,"request_index":qi,"request_bean":qb}))
        elif s.phase=="trade_response":
            typ=s.pending["type"]; a += [Action("gift_accept" if typ=="gift" else "trade_accept",cp,{}),Action("gift_reject" if typ=="gift" else "trade_reject",cp,{})]
        elif s.phase=="plant_received":
            cards=s.zones["pending_received"][cp]
            if not cards and cp==s.active_player: cards=s.zones["revealed"]
            if cards:
                for fi in self._can_plant(s,cp,cards[0]): a.append(Action("plant",cp,{"source":"received","index":0,"field":fi}))
            else:a.append(Action("pass",cp,{}))
        elif s.phase=="draw": a.append(Action("draw",cp,{}))
        return a

    def _draw_one(self,s):
        if not s.zones["deck"]:
            s.depletions+=1
            if s.depletions>=3:return None
            s.zones["deck"]=s.zones["discard"][:]; s.zones["discard"].clear()
            random.Random((s.chance["seed"] or 0)+s.chance["draw_index"]+s.depletions*100003).shuffle(s.zones["deck"])
        if not s.zones["deck"]: return None
        s.chance["draw_index"]+=1; return s.zones["deck"].pop()
    def _finish(self,s):
        for i,p in enumerate(s.players):
            for fi in range(len(p["fields"])):
                if p["fields"][fi]: self._do_harvest(s,i,fi,False)
        s.terminal=True;s.phase="terminal";s.current_player=s.active_player
    def _do_harvest(self,s,pi,fi,protected=True):
        f=s.players[pi]["fields"][fi]
        if protected and fi not in self._harvestable(s,pi): raise ValueError("protected single bean")
        bean=f[0]; n=len(f)
        if bean=="ackerbohne" and n==2:
            if not s.players[pi]["third_field"]: s.players[pi]["third_field"]=True;s.players[pi]["fields"].append([])
            reward=0
        else:
            reward=max((v for threshold,v in METERS[bean] if n>=threshold),default=0)
        s.players[pi]["coins"]+=reward
        s.zones["reserve"].extend(f[:reward]);s.zones["discard"].extend(f[reward:]);s.players[pi]["fields"][fi]=[]

    def apply_action(self,state,action):
        s=copy.deepcopy(state)
        if action not in self.legal_actions(s): raise ValueError("illegal action")
        t=action.type; cp=s.current_player
        if t=="harvest": self._do_harvest(s,cp,action.args["field"]); return s
        if t=="plant":
            if action.args["source"]=="hand": bean=s.players[cp]["hand"].pop(0)
            else:
                cards=s.zones["pending_received"][cp]
                if not cards and cp==s.active_player: cards=s.zones["revealed"]
                bean=cards.pop(0)
            s.players[cp]["fields"][action.args["field"]].append(bean)
            if s.phase=="plant_first": s.phase="plant_second"
            elif s.phase=="plant_second": s.phase="reveal"
            return s
        if t=="pass":
            if s.phase in ("plant_first","plant_second"): s.phase="reveal"
            else:self._advance_planter(s)
        elif t=="reveal":
            for _ in range(2):
                b=self._draw_one(s)
                if b is None: break
                s.zones["revealed"].append(b)
            s.phase="trade"
        elif t in ("gift_propose","trade_start"):
            q=action.args["partner"]
            offered=[{"owner":cp,"zone":action.args.get("source",action.args.get("offer_source")),"index":action.args.get("index",action.args.get("offer_index")),"bean":action.args.get("bean",action.args.get("offer_bean"))}]
            req=[] if t=="gift_propose" else [{"owner":q,"zone":"hand","index":action.args["request_index"],"bean":action.args["request_bean"]}]
            s.pending={"type":"gift" if t=="gift_propose" else "trade","actor":cp,"partner":q,"offered":offered,"requested":req,"awaiting_player":q};s.phase="trade_response";s.current_player=q
        elif t in ("gift_reject","trade_reject"):
            s.current_player=s.active_player;s.pending=None;s.phase="trade"
        elif t in ("gift_accept","trade_accept"):
            pend=s.pending; actor=pend["actor"]; partner=pend["partner"]
            def take(c):
                zone=s.players[c["owner"]]["hand"] if c["zone"]=="hand" else s.zones["revealed"]
                return zone.pop(c["index"])
            # take descending indices per zone (current model has one each)
            ob=[take(c) for c in pend["offered"]]; rb=[take(c) for c in pend["requested"]]
            s.zones["pending_received"][partner].extend(ob);s.zones["pending_received"][actor].extend(rb)
            s.current_player=actor;s.pending=None;s.phase="trade"
        elif t=="end_trade": s.phase="plant_received";s.current_player=s.active_player
        elif t=="draw":
            # each player draws one, active player first clockwise
            for k in range(len(s.players)):
                pi=(s.active_player+k)%len(s.players); b=self._draw_one(s)
                if b is None: self._finish(s); return s
                s.players[pi]["hand"].append(b)
            s.active_player=(s.active_player+1)%len(s.players);s.current_player=s.active_player;s.phase="plant_first"
        return s
    def _advance_planter(self,s):
        n=len(s.players)
        for k in range(1,n+1):
            q=(s.current_player+k)%n
            if s.zones["pending_received"][q] or (q==s.active_player and s.zones["revealed"]): s.current_player=q;return
        s.current_player=s.active_player;s.phase="draw"

    def action_to_name(self,a): return a.type+":"+str(a.actor)+":"+json.dumps(a.args,ensure_ascii=False,sort_keys=True,separators=(",",":"))
    def name_to_action(self,n):
        t,actor,args=n.split(":",2);return Action(t,int(actor),json.loads(args))
    def action_to_data(self,a): return {"schema":"boardbench/bohnanza/action/1","data":{"type":a.type,"actor":a.actor,"args":copy.deepcopy(a.args)}}
    def action_from_data(self,p):
        self._envelope(p,"boardbench/bohnanza/action/1");d=p["data"]
        if set(d)!={"type","actor","args"} or d["type"] not in ACTION_TYPES or type(d["actor"]) is not int or not isinstance(d["args"],dict):raise ValueError("invalid action")
        return Action(d["type"],d["actor"],copy.deepcopy(d["args"]))
    def state_to_data(self,s):
        return {"schema":"boardbench/bohnanza/state/1","data":copy.deepcopy(s.__dict__)}
    def state_from_data(self,p):
        self._envelope(p,"boardbench/bohnanza/state/1");d=p["data"]
        required={"configuration","current_player","active_player","start_player","phase","terminal","players","zones","depletions","pending","chance"}
        if set(d)!=required or d["phase"] not in PHASES:raise ValueError("invalid state")
        return GameState(**copy.deepcopy(d))
    def observation_to_data(self,s,player):
        if type(player) is not int or not 0<=player<len(s.players):raise ValueError("invalid player")
        pending=copy.deepcopy(s.pending)
        d={"player":player,"current_player":s.current_player,"active_player":s.active_player,"phase":s.phase,"terminal":s.terminal,
           "own_hand":copy.deepcopy(s.players[player]["hand"]),"opponents":[{"id":p["id"],"hand_size":len(p["hand"])} for p in s.players if p["id"]!=player],
           "fields":[copy.deepcopy(p["fields"]) for p in s.players],"coins":[p["coins"] for p in s.players],"revealed":copy.deepcopy(s.zones["revealed"]),
           "deck_size":len(s.zones["deck"]),"discard_size":len(s.zones["discard"]),"pending":pending}
        return {"schema":"boardbench/bohnanza/observation/1","data":d}
    def _envelope(self,p,schema):
        if not isinstance(p,dict) or set(p)!={"schema","data"} or p["schema"]!=schema or not isinstance(p["data"],dict):raise ValueError("invalid envelope")
    def render(self,s): return f"phase={s.phase} active={s.active_player} current={s.current_player} deck={len(s.zones['deck'])} coins={[p['coins'] for p in s.players]}"
