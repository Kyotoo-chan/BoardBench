"""Source-bound implementation of Bohnanza, variant 2 (Ackerbohnen), 4-5 players."""
from __future__ import annotations

import copy
import json
import random

BEANS = ("blaue_bohne", "feuerbohne", "saubohne", "brechbohne", "sojabohne",
         "augenbohne", "rote_bohne", "gartenbohne", "weinbrandbohne", "ackerbohne")
COUNTS = dict(zip(BEANS, (20, 18, 16, 14, 12, 10, 8, 6, 22, 3)))
PAY = {
    "blaue_bohne": ((4,1),(6,2),(8,3),(10,4)), "feuerbohne": ((3,1),(6,2),(8,3),(9,4)),
    "saubohne": ((3,1),(5,2),(7,3),(8,4)), "brechbohne": ((3,1),(5,2),(6,3),(7,4)),
    "sojabohne": ((2,1),(4,2),(6,3),(7,4)), "augenbohne": ((2,1),(4,2),(5,3),(6,4)),
    "rote_bohne": ((2,1),(3,2),(4,3),(5,4)), "gartenbohne": ((2,2),(3,3)),
    "weinbrandbohne": ((2,1),(4,2),(6,3),(8,4)), "ackerbohne": ((2,2),(3,3)),
}
PHASES = {"plant_first","plant_second","reveal","trade","trade_response","plant_received","draw","terminal"}
TYPES = {"plant","harvest","reveal","trade_start","trade_add_offer_card","trade_add_request_card",
         "trade_submit","trade_accept","trade_reject","gift_propose","gift_accept","gift_reject",
         "end_trade","draw","pass","reorder_hand"}

class Action:
    __slots__ = ("type", "actor", "args")
    def __init__(self, type, actor, args=None):
        self.type, self.actor, self.args = type, actor, {} if args is None else args
    def __eq__(self, other):
        return isinstance(other, Action) and (self.type,self.actor,self.args)==(other.type,other.actor,other.args)
    def __hash__(self):
        return hash((self.type,self.actor,json.dumps(self.args,sort_keys=True,separators=(",",":"))))
    def __repr__(self): return f"Action({self.type!r}, {self.actor!r}, {self.args!r})"

class GameState:
    def __init__(self, configuration, current_player, active_player, start_player, phase, terminal,
                 players, zones, depletions, pending, chance):
        self.configuration=configuration; self.current_player=current_player; self.active_player=active_player
        self.start_player=start_player; self.phase=phase; self.terminal=terminal; self.players=players
        self.zones=zones; self.depletions=depletions; self.pending=pending; self.chance=chance

class Game:
    def __init__(self, num_players=None, seed=None):
        self.num_players = 4 if num_players is None else num_players
        if type(self.num_players) is not int or not 4 <= self.num_players <= 5:
            raise ValueError("variant 2 requires 4 or 5 players")
        if seed is not None and type(seed) is not int: raise TypeError("seed must be int or None")
        self.seed = seed

    def initial_state(self):
        deck = [b for b in BEANS for _ in range(COUNTS[b])]
        random.Random(self.seed).shuffle(deck)
        ps = [{"id":i,"hand":[],"fields":[[],[]],"coins":0,"third_field":False,"alive":True}
              for i in range(self.num_players)]
        # Deal singly; append preserves the source-mandated hand order.
        for _ in range(5):
            for p in ps: p["hand"].append(deck.pop())
        return GameState({"players":self.num_players,"seed":self.seed},0,0,0,"plant_first",False,ps,
                         {"deck":deck,"discard":[],"revealed":[],"pending_received":[[] for _ in ps],"reserve":[]},
                         0,None,{"seed":self.seed,"draw_index":5*self.num_players})

    def current_player(self,s): return s.current_player
    def is_terminal(self,s): return s.terminal
    def returns(self,s):
        if not s.terminal: return [0]*len(s.players)
        vals=[p["coins"] for p in s.players]; m=max(vals)
        # Clockwise furthest from start player wins a tie.
        winner=max((i for i,v in enumerate(vals) if v==m), key=lambda i:(i-s.start_player)%len(vals))
        return [1 if i==winner else -1 for i in range(len(vals))]

    def _a(self,t,actor,**args): return Action(t,actor,args)
    def _harvestable(self,s,pid):
        fs=s.players[pid]["fields"]
        out=[]
        for i,f in enumerate(fs):
            if not f: continue
            if len(f)>1 or not any(len(x)>1 for x in fs): out.append(i)
        return out
    def _plant_options(self,s,pid,bean,source="hand",index=0):
        p=s.players[pid]; out=[]
        for i,f in enumerate(p["fields"]):
            if not f or f[0]==bean: out.append(self._a("plant",pid,source=source,index=index,field=i))
        # Harvest actions expose the prerequisite when no compatible/empty field exists.
        if not out:
            out += [self._a("harvest",pid,field=i) for i in self._harvestable(s,pid)]
        return out

    def legal_actions(self,s):
        if s.terminal: return []
        p=s.current_player; ph=s.phase
        if ph in ("plant_first","plant_second"):
            hand=s.players[p]["hand"]
            if not hand: return [self._a("pass",p)]
            out=self._plant_options(s,p,hand[0])
            if ph=="plant_second": out.append(self._a("pass",p))
            return out
        if ph=="reveal": return [self._a("reveal",p)]
        if ph=="trade":
            if s.pending is not None:
                q=s.pending; partner=q["partner"]
                out=[self._a("trade_submit",p)]
                used_offer={(x["zone"],x["index"]) for x in q["offered"]}
                used_request={x["index"] for x in q["requested"]}
                for zone,seq in (("revealed",s.zones["revealed"]),("hand",s.players[p]["hand"])):
                    for i in range(len(seq)):
                        if (zone,i) not in used_offer: out.append(self._a("trade_add_offer_card",p,zone=zone,index=i))
                for i in range(len(s.players[partner]["hand"])):
                    if i not in used_request: out.append(self._a("trade_add_request_card",p,index=i))
                return out
            out=[self._a("end_trade",p)]
            # Start one-card exchanges (further cards may be added before submission).
            owned=[("revealed",i,b) for i,b in enumerate(s.zones["revealed"])] + [("hand",i,b) for i,b in enumerate(s.players[p]["hand"])]
            for partner in range(len(s.players)):
                if partner==p: continue
                for oz,oi,ob in owned:
                    for ri,rb in enumerate(s.players[partner]["hand"]):
                        out.append(self._a("trade_start",p,partner=partner,offer_zone=oz,offer_index=oi,request_index=ri))
                    out.append(self._a("gift_propose",p,partner=partner,zone=oz,index=oi))
            return out
        if ph=="trade_response":
            t=s.pending["type"]
            return [self._a("trade_accept" if t=="trade" else "gift_accept",p),
                    self._a("trade_reject" if t=="trade" else "gift_reject",p)]
        if ph=="plant_received":
            rec=s.zones["pending_received"][p]
            if not rec: return [self._a("pass",p)]
            return self._plant_options(s,p,rec[0],"received",0)
        if ph=="draw": return [self._a("draw",p)]
        return []

    def _take(self,s,owner,zone,index):
        seq=s.players[owner]["hand"] if zone=="hand" else s.zones[zone]
        return seq.pop(index)
    def _refill(self,s):
        if s.zones["deck"]: return True
        if not s.zones["discard"]: return False
        s.depletions += 1
        if s.depletions >= 3:
            s.terminal=True; s.phase="terminal"; return False
        s.zones["deck"]=s.zones["discard"][:]; s.zones["discard"].clear()
        seed=s.chance["seed"]
        random.Random((0 if seed is None else seed)+1000003*s.depletions).shuffle(s.zones["deck"])
        return True
    def _draw_one(self,s):
        if not self._refill(s): return None
        s.chance["draw_index"] += 1
        return s.zones["deck"].pop()
    def _harvest(self,s,pid,fi):
        f=s.players[pid]["fields"][fi]; bean=f[0]; n=len(f)
        if bean=="ackerbohne":
            if n<2: gold=0
            else: gold=2 if n==2 else 3
            # exactly three Ackerbohnen; surplus condition is retained for reconstructed states
        else:
            gold=max((g for threshold,g in PAY[bean] if n>=threshold),default=0)
        for _ in range(gold): f.pop(); s.players[pid]["coins"]+=1
        s.zones["discard"].extend(f); f.clear()

    def apply_action(self,state,action):
        s=copy.deepcopy(state)
        if action not in self.legal_actions(s): raise ValueError("illegal action")
        p=action.actor; a=action.args; ph=s.phase
        if action.type=="harvest": self._harvest(s,p,a["field"]); return s
        if action.type=="pass":
            if ph=="plant_first": s.phase="reveal"
            elif ph=="plant_second": s.phase="reveal"
            else: s.current_player=s.active_player; s.phase="draw"
            return s
        if action.type=="plant":
            bean=(s.players[p]["hand"].pop(0) if a["source"]=="hand" else s.zones["pending_received"][p].pop(0))
            s.players[p]["fields"][a["field"]].append(bean)
            if ph=="plant_first": s.phase="plant_second"
            elif ph=="plant_second": s.phase="reveal"
            elif not s.zones["pending_received"][p]:
                nxt=next((i for i,x in enumerate(s.zones["pending_received"]) if x),None)
                if nxt is None: s.current_player=s.active_player; s.phase="draw"
                else: s.current_player=nxt
            return s
        if action.type=="reveal":
            for _ in range(2):
                b=self._draw_one(s)
                if b is None: break
                s.zones["revealed"].append(b)
            if not s.terminal: s.phase="trade"
            return s
        if action.type in ("trade_start","gift_propose"):
            partner=a["partner"]
            offered={"owner":p,"zone":a.get("offer_zone",a.get("zone")),"index":a.get("offer_index",a.get("index")),"bean":""}
            seq=s.players[p]["hand"] if offered["zone"]=="hand" else s.zones[offered["zone"]]
            offered["bean"]=seq[offered["index"]]
            req=[]
            if action.type=="trade_start":
                ri=a["request_index"]; req=[{"owner":partner,"zone":"hand","index":ri,"bean":s.players[partner]["hand"][ri]}]
            s.pending={"type":"trade_draft" if action.type=="trade_start" else "gift","actor":p,"partner":partner,
                       "offered":[offered],"requested":req,"awaiting_player":partner}
            if action.type=="trade_start":
                s.current_player=p; s.phase="trade"
            else:
                s.current_player=partner; s.phase="trade_response"
            return s
        if action.type in ("trade_add_offer_card","trade_add_request_card"):
            q=s.pending
            if action.type=="trade_add_offer_card":
                zone=a["zone"]; i=a["index"]; seq=s.players[p]["hand"] if zone=="hand" else s.zones[zone]
                q["offered"].append({"owner":p,"zone":zone,"index":i,"bean":seq[i]})
            else:
                i=a["index"]; partner=q["partner"]
                q["requested"].append({"owner":partner,"zone":"hand","index":i,"bean":s.players[partner]["hand"][i]})
            return s
        if action.type=="trade_submit":
            s.pending["type"]="trade"; s.current_player=s.pending["partner"]; s.phase="trade_response"; return s
        if action.type.endswith("reject"):
            s.current_player=s.active_player; s.phase="trade"; s.pending=None; return s
        if action.type.endswith("accept"):
            q=s.pending; # remove high indexes first within each zone
            got=[]
            for ref in sorted(q["offered"],key=lambda x:x["index"],reverse=True): got.append(self._take(s,ref["owner"],ref["zone"],ref["index"]))
            s.zones["pending_received"][q["partner"]].extend(reversed(got))
            got=[]
            for ref in sorted(q["requested"],key=lambda x:x["index"],reverse=True): got.append(self._take(s,ref["owner"],ref["zone"],ref["index"]))
            s.zones["pending_received"][q["actor"]].extend(reversed(got))
            s.pending=None; s.current_player=s.active_player; s.phase="trade"; return s
        if action.type=="end_trade":
            # Untraded revealed cards belong to and must be planted by active player.
            s.zones["pending_received"][p].extend(s.zones["revealed"]); s.zones["revealed"].clear()
            nxt=next((i for i,x in enumerate(s.zones["pending_received"]) if x),None)
            if nxt is None: s.phase="draw"
            else: s.current_player=nxt; s.phase="plant_received"
            return s
        if action.type=="draw":
            # Variant 1 flow: active player first, then every player clockwise draws one.
            order=[(s.active_player+i)%len(s.players) for i in range(len(s.players))]
            for i in order:
                b=self._draw_one(s)
                if b is None: break
                s.players[i]["hand"].append(b)
            if not s.terminal:
                s.active_player=(s.active_player+1)%len(s.players); s.current_player=s.active_player; s.phase="plant_first"
            return s
        raise ValueError("unsupported action")

    def action_to_name(self,a):
        return a.type+":"+str(a.actor)+":"+json.dumps(a.args,ensure_ascii=False,sort_keys=True,separators=(",",":"))
    def name_to_action(self,name):
        try: t,actor,args=name.split(":",2); return self.action_from_data({"schema":"boardbench/bohnanza/action/1","data":{"type":t,"actor":int(actor),"args":json.loads(args)}})
        except Exception as e: raise ValueError("invalid action name") from e
    def action_to_data(self,a): return {"schema":"boardbench/bohnanza/action/1","data":{"type":a.type,"actor":a.actor,"args":copy.deepcopy(a.args)}}
    def action_from_data(self,x):
        self._envelope(x,"boardbench/bohnanza/action/1"); d=x["data"]
        if set(d)!={"type","actor","args"} or d["type"] not in TYPES or type(d["actor"]) is not int or not isinstance(d["args"],dict): raise ValueError("invalid action")
        return Action(d["type"],d["actor"],copy.deepcopy(d["args"]))
    def state_to_data(self,s):
        d={k:copy.deepcopy(getattr(s,k)) for k in ("configuration","current_player","active_player","start_player","phase","terminal","players","zones","depletions","pending","chance")}
        return {"schema":"boardbench/bohnanza/state/1","data":d}
    def _envelope(self,x,schema):
        if not isinstance(x,dict) or set(x)!={"schema","data"} or x["schema"]!=schema or not isinstance(x["data"],dict): raise ValueError("invalid envelope")
    def state_from_data(self,x):
        self._envelope(x,"boardbench/bohnanza/state/1"); d=copy.deepcopy(x["data"])
        keys=("configuration","current_player","active_player","start_player","phase","terminal","players","zones","depletions","pending","chance")
        if set(d)!=set(keys): raise ValueError("invalid state fields")
        self._validate_state(d)
        return GameState(**d)
    def _validate_state(self,d):
        n=d["configuration"].get("players") if isinstance(d["configuration"],dict) else None
        if type(n) is not int or n not in (4,5) or len(d["players"])!=n: raise ValueError("invalid players")
        if d["phase"] not in PHASES or type(d["terminal"]) is not bool: raise ValueError("invalid phase")
        if any(type(d[k]) is not int for k in ("current_player","active_player","start_player","depletions")): raise ValueError("invalid integer")
        if not all(0<=d[k]<n for k in ("current_player","active_player","start_player")): raise ValueError("invalid player index")
        if set(d["zones"])!={"deck","discard","revealed","pending_received","reserve"}: raise ValueError("invalid zones")
        for seq in (d["zones"][z] for z in ("deck","discard","revealed","reserve")):
            if not isinstance(seq,list) or any(b not in BEANS for b in seq): raise ValueError("invalid bean zone")
        if len(d["zones"]["pending_received"])!=n: raise ValueError("invalid received zones")
        for i,p in enumerate(d["players"]):
            if set(p)!={"id","hand","fields","coins","third_field","alive"} or p["id"]!=i or len(p["fields"]) not in (2,3): raise ValueError("invalid player")
            if any(b not in BEANS for b in p["hand"]+sum(p["fields"],[])): raise ValueError("invalid bean")
    def observation_to_data(self,s,player):
        if type(player) is not int or not 0<=player<len(s.players): raise ValueError("invalid player")
        pending=copy.deepcopy(s.pending)
        d={"player":player,"current_player":s.current_player,"active_player":s.active_player,"phase":s.phase,"terminal":s.terminal,
           "own_hand":copy.deepcopy(s.players[player]["hand"]),"opponents":[{"id":p["id"],"hand_size":len(p["hand"])} for p in s.players if p["id"]!=player],
           "fields":copy.deepcopy([p["fields"] for p in s.players]),"coins":[p["coins"] for p in s.players],"revealed":copy.deepcopy(s.zones["revealed"]),
           "deck_size":len(s.zones["deck"]),"discard_size":len(s.zones["discard"]),"pending":pending}
        return {"schema":"boardbench/bohnanza/observation/1","data":d}
    def render(self,s):
        return f"phase={s.phase} active={s.active_player} deck={len(s.zones['deck'])} coins={[p['coins'] for p in s.players]}"
