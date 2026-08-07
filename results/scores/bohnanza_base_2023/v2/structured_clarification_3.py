from dataclasses import dataclass
import copy, json, random

BEANS=("gartenbohne","rote_bohne","augenbohne","sojabohne","brechbohne","saubohne","feuerbohne","blaue_bohne")
COUNTS=dict(zip(BEANS,(6,8,10,12,14,16,18,20)))
METERS={"gartenbohne":((1,0),(2,2),(3,3)),"rote_bohne":((2,1),(3,2),(4,3),(5,4)),"augenbohne":((2,1),(4,2),(5,3),(6,4)),"sojabohne":((2,1),(4,2),(6,3),(7,4)),"brechbohne":((3,1),(5,2),(6,3),(7,4)),"saubohne":((3,1),(5,2),(7,3),(8,4)),"feuerbohne":((3,1),(6,2),(8,3),(9,4)),"blaue_bohne":((4,1),(6,2),(8,3),(10,4))}
PHASES=("plant_first","plant_second","reveal","trade","trade_response","plant_received","draw","terminal")
SS="boardbench/bohnanza-base-2023/state/2"; AS="boardbench/bohnanza-base-2023/action/2"; OS="boardbench/bohnanza-base-2023/observation/2"

@dataclass(eq=True)
class GameState:
    data: dict

@dataclass(frozen=True)
class Action:
    type: str
    actor: int
    args_json: str="{}"
    @property
    def args(self): return json.loads(self.args_json)

def _act(t,a,**kw): return Action(t,a,json.dumps(kw,sort_keys=True,separators=(",",":")))

class Game:
    def __init__(self,num_players=None,seed=None):
        self.num_players=3 if num_players is None else num_players
        if type(self.num_players) is not int or self.num_players not in (3,4,5): raise ValueError("Bohnanza supports 3, 4, or 5 players")
        if seed is not None and type(seed) is not int: raise ValueError("seed must be int or None")
        self.seed=seed

    def initial_state(self):
        rng=random.Random(self.seed); deck=[b for b in BEANS for _ in range(COUNTS[b])]; rng.shuffle(deck)
        start=rng.randrange(self.num_players); hands=[[] for _ in range(self.num_players)]
        for _ in range(5):
            for h in hands: h.append(deck.pop())
        nf=3 if self.num_players==3 else 2
        ps=[{"id":i,"hand":hands[i],"fields":[[] for _ in range(nf)],"coins":0} for i in range(self.num_players)]
        d={"configuration":{"players":self.num_players,"seed":self.seed,"variant":"base_2023"},"current_player":start,"active_player":start,"start_player":start,"phase":"plant_first","terminal":False,"winner":None,"players":ps,"zones":{"deck":deck,"discard":[],"revealed":[],"pending_received":[[] for _ in ps],"reserve":[]},"depletions":0,"pending":None,"turn_number":0,"chance":{"seed":self.seed,"counter":0}}
        return GameState(d)

    def current_player(self,s): return s.data["current_player"]
    def is_terminal(self,s): return s.data["terminal"]
    def returns(self,s):
        n=s.data["configuration"]["players"]
        return [1 if s.data["terminal"] and i==s.data["winner"] else 0 for i in range(n)]

    def _fits(self,p,b,f): return not p["fields"][f] or p["fields"][f][0]==b
    def _harvests(self,d):
        out=[]
        for p in d["players"]:
            protected=any(len(f)>1 for f in p["fields"])
            for i,f in enumerate(p["fields"]):
                if f and (len(f)>1 or not protected): out.append(_act("harvest",p["id"],player=p["id"],field=i))
        return out
    def _plants(self,d,actor,source):
        p=d["players"][actor]
        if source=="hand":
            if not p["hand"]: return []
            idx=0;b=p["hand"][0]
        elif source=="revealed":
            if not d["zones"]["revealed"]: return []
            idx=0;b=d["zones"]["revealed"][0]
        else:
            if not d["zones"]["pending_received"][actor]: return []
            idx=0;b=d["zones"]["pending_received"][actor][0]
        return [_act("plant",actor,field=i,source=source,index=idx,bean=b) for i in range(len(p["fields"])) if self._fits(p,b,i)]

    def legal_actions(self,s):
        d=s.data
        if d["terminal"]: return []
        ph=d["phase"]; a=d["active_player"]; out=self._harvests(d)
        if ph=="plant_first":
            x=self._plants(d,a,"hand"); out+=x or ([_act("pass",a)] if not d["players"][a]["hand"] else [])
        elif ph=="plant_second": out+=self._plants(d,a,"hand")+[_act("pass",a)]
        elif ph=="reveal": out.append(_act("reveal",a))
        elif ph=="trade":
            # Each concrete proposal uses one or two offered cards and one requested card;
            # repeated proposals allow the source's unrestricted negotiation without hidden-card leakage.
            refs=[]
            for i,b in enumerate(d["players"][a]["hand"]): refs.append({"owner":a,"zone":"hand","index":i,"bean":b})
            for i,b in enumerate(d["zones"]["revealed"]): refs.append({"owner":a,"zone":"revealed","index":i,"bean":b})
            for partner in range(len(d["players"])):
                if partner==a: continue
                for off in refs:
                    out.append(_act("trade_propose",a,partner=partner,offered=[off],requested=[],gift=True))
                    for i,b in enumerate(d["players"][partner]["hand"]):
                        req={"owner":partner,"zone":"hand","index":i,"bean":b}
                        out.append(_act("trade_propose",a,partner=partner,offered=[off],requested=[req],gift=False))
            out.append(_act("end_trade",a))
        elif ph=="trade_response":
            cp=d["current_player"];out += [_act("trade_accept",cp),_act("trade_reject",cp)]
        elif ph=="plant_received":
            for i,g in enumerate(d["zones"]["pending_received"]): out+=self._plants(d,i,"received")
            out+=self._plants(d,a,"revealed")
            if not any(d["zones"]["pending_received"]) and not d["zones"]["revealed"]: out.append(_act("pass",a))
        elif ph=="draw": out.append(_act("draw",a))
        # canonical dedup (harvest may coincide only by identity)
        return list(dict.fromkeys(out))

    def _draw_one(self,d,during_reveal=False):
        if not d["zones"]["deck"]:
            d["depletions"]+=1
            if d["depletions"]>=3:
                if during_reveal: return None
                self._finish(d); return None
            cards=d["zones"]["discard"];d["zones"]["discard"]=[]
            rng=random.Random(f"{d['chance']['seed']}:{d['chance']['counter']}");rng.shuffle(cards);d["chance"]["counter"]+=1;d["zones"]["deck"]=cards
        return d["zones"]["deck"].pop() if d["zones"]["deck"] else None
    def _payout(self,d,p,fi):
        field=p["fields"][fi]; n=len(field); pay=0
        for threshold,value in METERS[field[0]]:
            if n>=threshold: pay=value
        p["coins"]+=pay; d["zones"]["discard"].extend(field[pay:]);p["fields"][fi]=[]
    def _finish(self,d):
        for p in d["players"]:
            for i in range(len(p["fields"])):
                if p["fields"][i]: self._payout(d,p,i)
        top=max(p["coins"] for p in d["players"]); tied={p["id"] for p in d["players"] if p["coins"]==top};n=len(d["players"]);start=d["start_player"]
        d["winner"]=max(tied,key=lambda i:(i-start)%n);d["terminal"]=True;d["phase"]="terminal";d["pending"]=None;d["current_player"]=d["winner"]

    def apply_action(self,s,action):
        if action not in self.legal_actions(s): raise ValueError("illegal action")
        ns=copy.deepcopy(s);d=ns.data;ph=d["phase"];a=action.actor;x=action.args
        if action.type=="harvest": self._payout(d,d["players"][x["player"]],x["field"]); return ns
        if action.type=="plant":
            src=x["source"]
            if src=="hand": b=d["players"][a]["hand"].pop(0)
            elif src=="revealed": b=d["zones"]["revealed"].pop(x["index"])
            else: b=d["zones"]["pending_received"][a].pop(x["index"])
            d["players"][a]["fields"][x["field"]].append(b)
            if ph=="plant_first": d["phase"]="plant_second"
            return ns
        if action.type=="pass":
            if ph in ("plant_first","plant_second"): d["phase"]="reveal"
            elif ph=="plant_received":
                if d["depletions"]>=3: self._finish(d)
                else: d["phase"]="draw"
            return ns
        if action.type=="reveal":
            for _ in range(2):
                b=self._draw_one(d,True)
                if b is not None:d["zones"]["revealed"].append(b)
            d["phase"]="trade";return ns
        if action.type=="trade_propose":
            d["pending"]={"type":"gift" if x["gift"] else "trade","actor":a,"partner":x["partner"],"offered":x["offered"],"requested":x["requested"],"awaiting_player":x["partner"]};d["phase"]="trade_response";d["current_player"]=x["partner"];return ns
        if action.type=="trade_reject": d["pending"]=None;d["phase"]="trade";d["current_player"]=d["active_player"];return ns
        if action.type=="trade_accept":
            q=d["pending"]
            for key,target in (("offered",q["partner"]),("requested",q["actor"])):
                for r in sorted(q[key],key=lambda z:z["index"],reverse=True):
                    zone=d["players"][r["owner"]]["hand"] if r["zone"]=="hand" else d["zones"]["revealed"]
                    b=zone.pop(r["index"]);d["zones"]["pending_received"][target].append(b)
            d["pending"]=None;d["phase"]="trade";d["current_player"]=d["active_player"];return ns
        if action.type=="end_trade": d["phase"]="plant_received";return ns
        if action.type=="draw":
            for _ in range(3):
                b=self._draw_one(d)
                if d["terminal"]: break
                if b is not None:d["players"][a]["hand"].append(b)
            if not d["terminal"]:
                na=(a+1)%len(d["players"]);d["active_player"]=d["current_player"]=na;d["phase"]="plant_first";d["turn_number"]+=1
            return ns
        raise ValueError("unknown action")

    def action_to_data(self,a): return {"schema":AS,"data":{"type":a.type,"actor":a.actor,"args":a.args}}
    def action_from_data(self,p):
        if type(p) is not dict or set(p)!={"schema","data"} or p["schema"]!=AS: raise ValueError("invalid action envelope")
        d=p["data"]
        if type(d) is not dict or set(d)!={"type","actor","args"} or d["type"] not in ("plant","harvest","reveal","trade_propose","trade_accept","trade_reject","end_trade","draw","pass") or type(d["actor"]) is not int or type(d["args"]) is not dict: raise ValueError("invalid action")
        return Action(d["type"],d["actor"],json.dumps(d["args"],sort_keys=True,separators=(",",":")))
    def action_to_name(self,a): return a.type.replace("_"," ")+" | actor "+str(a.actor)+" | "+json.dumps(a.args,ensure_ascii=False,sort_keys=True,separators=(",",":"))
    def name_to_action(self,n):
        try:
            label,actor,args=n.split(" | ",2);return Action(label.replace(" ","_"),int(actor[6:]),json.dumps(json.loads(args),sort_keys=True,separators=(",",":")))
        except Exception as e: raise ValueError("invalid action name") from e

    def state_to_data(self,s): return {"schema":SS,"data":copy.deepcopy(s.data)}
    def state_from_data(self,p):
        if type(p) is not dict or set(p)!={"schema","data"} or p["schema"]!=SS or type(p["data"]) is not dict: raise ValueError("invalid state envelope")
        req={"configuration","current_player","active_player","start_player","phase","terminal","winner","players","zones","depletions","pending","turn_number","chance"}
        if set(p["data"])!=req: raise ValueError("invalid state fields")
        d=copy.deepcopy(p["data"])
        if d["phase"] not in PHASES or type(d["players"]) is not list or type(d["zones"]) is not dict: raise ValueError("invalid state values")
        return GameState(d)
    def observation_to_data(self,s,player):
        d=s.data
        if type(player) is not int or not 0<=player<len(d["players"]): raise ValueError("invalid player")
        opp=[{"id":p["id"],"hand_size":len(p["hand"]),"front_card":p["hand"][0] if p["hand"] else None} for p in d["players"] if p["id"]!=player]
        od={"player":player,"current_player":d["current_player"],"active_player":d["active_player"],"start_player":d["start_player"],"phase":d["phase"],"terminal":d["terminal"],"winner":d["winner"],"own_hand":copy.deepcopy(d["players"][player]["hand"]),"opponents":opp,"fields":[copy.deepcopy(p["fields"]) for p in d["players"]],"coins":[p["coins"] for p in d["players"]],"revealed":copy.deepcopy(d["zones"]["revealed"]),"deck_size":len(d["zones"]["deck"]),"discard_size":len(d["zones"]["discard"]),"pending_received_counts":[len(g) for g in d["zones"]["pending_received"]],"pending":copy.deepcopy(d["pending"]),"turn_number":d["turn_number"]}
        return {"schema":OS,"data":od}
    def render(self,s):
        d=s.data;return f"Bohnanza turn={d['turn_number']} phase={d['phase']} active={d['active_player']} deck={len(d['zones']['deck'])} coins={[p['coins'] for p in d['players']]}"
