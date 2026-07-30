"""Self-contained CATAN (2022 German beginner game) environment.

Only the supplied Spielanleitung, Almanach, representation profile, and approved
digital clarifications are used.  State objects are immutable-by-convention:
``apply_action`` always returns a detached successor.
"""
from dataclasses import dataclass
import copy
import json
import math
import random

RES = ("wood", "brick", "wool", "grain", "ore")
DEVS = ("knight", "road_building", "year_of_plenty", "monopoly",
        "library", "marketplace", "city_hall", "chapel", "university")
VP_DEVS = set(DEVS[4:])
PHASES = ("roll", "discard", "robber_move", "robber_steal", "trade",
          "trade_offer", "build", "road_building", "terminal")
STATE_SCHEMA = "boardbench/catan/state/2"
ACTION_SCHEMA = "boardbench/catan/action/2"
OBS_SCHEMA = "boardbench/catan/observation/2"

HEXES = [
 ("h00","ore",10),("h01","wool",2),("h02","wood",9),
 ("h03","grain",12),("h04","brick",6),("h05","wool",4),("h06","brick",10),
 ("h07","grain",9),("h08","wood",11),("h09","desert",None),("h10","wood",3),("h11","ore",8),
 ("h12","wood",8),("h13","ore",3),("h14","grain",4),("h15","wool",5),
 ("h16","brick",5),("h17","grain",6),("h18","wool",11)]
ROWS = [["h00","h01","h02"],["h03","h04","h05","h06"],
        ["h07","h08","h09","h10","h11"],["h12","h13","h14","h15"],
        ["h16","h17","h18"]]
HARBORS = [
 ("p00",2,"grain",("v01","v05")),("p01",2,"wood",("v10","v15")),
 ("p02",3,None,("v26","v32")),("p03",2,"wool",("v46","v50")),
 ("p04",3,None,("v49","v52")),("p05",3,None,("v47","v51")),
 ("p06",2,"brick",("v27","v33")),("p07",2,"ore",("v11","v16")),
 ("p08",3,None,("v00","v03"))]
SETUP = {
 3: {
  "colors":["blue","orange","white"],
  "settlements":[(0,"v39"),(0,"v41"),(1,"v14"),(1,"v40"),(2,"v17"),(2,"v31")],
  "roads":[(0,"e_v39_v44"),(0,"e_v36_v41"),(1,"e_v09_v14"),(1,"e_v40_v45"),
           (2,"e_v17_v22"),(2,"e_v25_v31")],
  "resources":[[1,1,0,0,1],[0,0,0,2,1],[1,0,1,0,1]],
  "bank":[17,18,18,17,16]},
 4: {
  "colors":["red","blue","orange","white"],
  "settlements":[(0,"v08"),(0,"v28"),(1,"v39"),(1,"v41"),(2,"v14"),(2,"v40"),(3,"v17"),(3,"v31")],
  "roads":[(0,"e_v08_v13"),(0,"e_v28_v34"),(1,"e_v39_v44"),(1,"e_v36_v41"),
           (2,"e_v09_v14"),(2,"e_v40_v45"),(3,"e_v17_v22"),(3,"e_v25_v31")],
  "resources":[[2,0,0,1,0],[1,1,0,0,1],[0,0,0,2,1],[1,0,1,0,1]],
  "bank":[15,18,18,16,16]}}

def counts(values=(0,0,0,0,0)):
    return {r:int(v) for r,v in zip(RES, values)}

def _topology():
    corners = {}
    hex_corners = {}
    for row, ids in enumerate(ROWS):
        offset = abs(2-row)/2
        for col,h in enumerate(ids):
            x=(col+offset)*math.sqrt(3); y=1.5*row
            pts=[]
            for angle in (30,90,150,210,270,330):
                a=math.radians(angle)
                p=(round((x+math.cos(a))*1000),round((y+math.sin(a))*1000))
                corners[p]=None; pts.append(p)
            hex_corners[h]=pts
    ordered=sorted(corners,key=lambda p:(p[1],p[0]))
    ids={p:f"v{i:02d}" for i,p in enumerate(ordered)}
    vertex_hexes={v:[] for v in ids.values()}
    edge_pairs=set()
    for h,pts in hex_corners.items():
        for p in pts: vertex_hexes[ids[p]].append(h)
        for i in range(6):
            a,b=sorted((ids[pts[i]],ids[pts[(i+1)%6]]))
            edge_pairs.add((a,b))
    edges=sorted(edge_pairs, key=lambda x:(x[0],x[1]))
    return vertex_hexes, [(f"e_{a}_{b}",a,b) for a,b in edges]

VERTEX_HEXES, EDGE_DEF = _topology()
EDGE_VERTS={e:(a,b) for e,a,b in EDGE_DEF}
ADJ={v:set() for v in VERTEX_HEXES}
for _,a,b in EDGE_DEF: ADJ[a].add(b); ADJ[b].add(a)

@dataclass
class GameState:
    data: dict

@dataclass(frozen=True)
class Action:
    type: str
    actor: int
    args: tuple = ()

    def argdict(self): return dict(self.args)

def act(t, actor, **kwargs):
    return Action(t, actor, tuple(sorted(kwargs.items())))

class Game:
    def __init__(self, num_players=None, seed=None):
        self.num_players = 4 if num_players is None else num_players
        if self.num_players not in (3,4): raise ValueError("CATAN supports 3 or 4 players")
        if seed is not None and (type(seed) is not int): raise ValueError("seed must be int or null")
        self.seed=seed

    def initial_state(self):
        s=SETUP[self.num_players]; rng=random.Random(self.seed)
        deck=(["knight"]*14+["road_building"]*2+["year_of_plenty"]*2+
              ["monopoly"]*2+list(DEVS[4:]))
        rng.shuffle(deck)
        vertices=[{"id":v,"building":None,"harbor_ids":[] } for v in VERTEX_HEXES]
        vm={v["id"]:v for v in vertices}
        for p,v in s["settlements"]: vm[v]["building"]={"owner":p,"type":"settlement"}
        for hid,_,_,vs in HARBORS:
            for v in vs: vm[v]["harbor_ids"].append(hid)
        roads=dict((e,None) for e,_,_ in EDGE_DEF)
        for p,e in s["roads"]: roads[e]=p
        players=[]
        for p,color in enumerate(s["colors"]):
            players.append({"id":p,"color":color,"resources":counts(s["resources"][p]),
              "development_hand":[],"played_knights":0,
              "pieces":{"roads":13,"settlements":3,"cities":4}})
        d={"configuration":{"players":self.num_players,"seed":self.seed,"oldest_player":0,
             "setup":"beginner_illustrated"},"current_player":0,"active_player":0,
           "phase":"roll","turn":{"number":1,"development_played":False,"last_roll":None},
           "terminal":False,"winner":None,"players":players,
           "board":{"hexes":[{"id":h,"terrain":t,"number":n,"robber":h=="h09"} for h,t,n in HEXES],
             "vertices":vertices,
             "edges":[{"id":e,"vertices":[a,b],"road_owner":roads[e]} for e,a,b in EDGE_DEF],
             "harbors":[{"id":h,"ratio":r,"resource":q,"vertices":list(vs)} for h,r,q,vs in HARBORS]},
           "bank":{"resources":counts(s["bank"]),"development_deck":deck,"played_development":[]},
           "special_cards":{"longest_road_owner":None,"longest_road_length":0,"largest_army_owner":None},
           "pending":[],"chance":{"rng_state":rng.getrandbits(63),"scripted_rolls":[],"scripted_steals":[]},
           "zones":{"reserve":{"resources":counts(),"development_cards":[],"removed_colors":[] if self.num_players==4 else ["red"]}}}
        return GameState(d)

    def current_player(self,state): return state.data["current_player"]
    def is_terminal(self,state): return bool(state.data["terminal"])
    def returns(self,state):
        if not self.is_terminal(state): return [0]*len(state.data["players"])
        return [1 if i==state.data["winner"] else -1 for i in range(len(state.data["players"]))]

    def _available(self,d,p):
        out=d["players"][p]["resources"].copy()
        for f in d["pending"]:
            if f["type"]=="discard" and str(p) in f["selected"]:
                for r,n in f["selected"][str(p)].items(): out[r]-=n
        return out

    def _eligible_dev(self,d,p):
        if d["turn"]["development_played"]: return []
        return [c for c in d["players"][p]["development_hand"]
                if not c["revealed"] and c["bought_turn"]<d["turn"]["number"] and c["id"] not in VP_DEVS]

    def legal_actions(self,state):
        d=state.data
        if d["terminal"]: return []
        p=d["current_player"]; phase=d["phase"]; out=[]
        # Permitted active-player development interrupt.
        ap=d["active_player"]
        if phase in ("discard","robber_move","robber_steal","trade","trade_offer","build"):
            for c in self._eligible_dev(d,ap):
                if c["id"]=="knight": out.append(act("play_knight",ap,card="knight"))
                elif c["id"]=="road_building": out.append(act("play_road_building",ap,card="road_building"))
                elif c["id"]=="year_of_plenty":
                    for a in RES:
                        for b in RES:
                            need=2 if a==b else 1
                            if d["bank"]["resources"][a]>=need and d["bank"]["resources"][b]>=1:
                                out.append(act("play_year_of_plenty",ap,card="year_of_plenty",resources=(a,b)))
                elif c["id"]=="monopoly":
                    out += [act("play_monopoly",ap,card="monopoly",resource=r) for r in RES]
        if phase=="roll": out.append(act("roll_dice",p))
        elif phase=="discard":
            f=d["pending"][-1]; key=str(p); selected=f["selected"].get(key,counts())
            if p in f["submitted_players"]: return out
            for r,n in self._available(d,p).items():
                if n>0 and sum(selected.values())<f["required"][key]: out.append(act("choose_discard_resource",p,resource=r))
            for r,n in selected.items():
                if n>0: out.append(act("undo_discard_resource",p,resource=r))
            if sum(selected.values())==f["required"][key]: out.append(act("submit_discard",p))
        elif phase=="robber_move":
            current=next(h["id"] for h in d["board"]["hexes"] if h["robber"])
            out += [act("move_robber",p,hex=h["id"]) for h in d["board"]["hexes"] if h["id"]!=current]
        elif phase=="robber_steal":
            out += [act("steal_resource",p,victim=v) for v in d["pending"][-1]["victims"]]
        elif phase=="trade":
            out += [act("begin_domestic_trade",p,partner=q) for q in range(len(d["players"])) if q!=p]
            have=self._available(d,p)
            for give,n in have.items():
                ratio=self._ratio(d,p,give)
                if n>=ratio:
                    out += [act("maritime_trade",p,give=give,receive=r) for r in RES if r!=give and d["bank"]["resources"][r]>0]
            out.append(act("end_trade",p))
        elif phase=="trade_offer":
            f=d["pending"][-1]
            if f["status"]=="building":
                maxgive=sum(self._available(d,p).values()); maxtake=sum(self._available(d,f["partner"]).values())
                if sum(f["give"].values())<maxgive:
                    out += [act("add_trade_item",p,direction="give",resource=r) for r in RES]
                if sum(f["take"].values())<maxtake:
                    out += [act("add_trade_item",p,direction="take",resource=r) for r in RES]
                if sum(f["give"].values()) and sum(f["take"].values()): out.append(act("propose_domestic_trade",p))
                out.append(act("cancel_domestic_trade",p))
            else:
                q=f["partner"]
                if all(self._available(d,q)[r]>=n for r,n in f["take"].items()) and all(self._available(d,p)[r]>=n for r,n in f["give"].items()):
                    out.append(act("accept_domestic_trade",q))
                out += [act("reject_domestic_trade",q),act("cancel_domestic_trade",p)]
        elif phase=="build":
            out += self._build_actions(d,p,False)
            out.append(act("end_turn",p))
        elif phase=="road_building":
            roads=self._legal_roads(d,p)
            if roads: out += [act("place_free_road",p,edge=e) for e in roads]
            else: out += self._finish_free_roads_actions(d,p)
        return out

    def _ratio(self,d,p,r):
        buildings={v["id"] for v in d["board"]["vertices"] if v["building"] and v["building"]["owner"]==p}
        ratios=[h["ratio"] for h in d["board"]["harbors"] if buildings.intersection(h["vertices"]) and (h["resource"] is None or h["resource"]==r)]
        return min(ratios+[4])

    def _legal_roads(self,d,p):
        owned={e["id"] for e in d["board"]["edges"] if e["road_owner"]==p}
        endpoints=set()
        for e in owned: endpoints.update(EDGE_VERTS[e])
        endpoints.update(v["id"] for v in d["board"]["vertices"] if v["building"] and v["building"]["owner"]==p)
        blocked={v["id"] for v in d["board"]["vertices"] if v["building"] and v["building"]["owner"]!=p}
        return [e["id"] for e in d["board"]["edges"] if e["road_owner"] is None and
                any(v in endpoints and v not in blocked for v in e["vertices"])]

    def _legal_settlements(self,d,p):
        ownroad=set()
        for e in d["board"]["edges"]:
            if e["road_owner"]==p: ownroad.update(e["vertices"])
        occupied={v["id"] for v in d["board"]["vertices"] if v["building"]}
        return [v for v in ownroad if v not in occupied and not (ADJ[v]&occupied)]

    def _build_actions(self,d,p,free):
        pl=d["players"][p]; r=self._available(d,p); out=[]
        if pl["pieces"]["roads"] and r["wood"] and r["brick"]:
            out += [act("build_road",p,edge=e) for e in self._legal_roads(d,p)]
        if pl["pieces"]["settlements"] and all(r[x]>=1 for x in ("wood","brick","wool","grain")):
            out += [act("build_settlement",p,vertex=v) for v in self._legal_settlements(d,p)]
        if pl["pieces"]["cities"] and r["ore"]>=3 and r["grain"]>=2:
            out += [act("build_city",p,vertex=v["id"]) for v in d["board"]["vertices"]
                    if v["building"]=={"owner":p,"type":"settlement"}]
        if r["ore"] and r["wool"] and r["grain"] and d["bank"]["development_deck"]:
            out.append(act("buy_development",p))
        return out

    def _finish_free_roads_actions(self,d,p):
        return []

    def apply_action(self,state,action):
        legal=self.legal_actions(state)
        if action not in legal: raise ValueError("illegal action")
        d=copy.deepcopy(state.data); p=action.actor; a=action.argdict(); t=action.type
        if t=="roll_dice":
            if d["chance"]["scripted_rolls"]: dice=d["chance"]["scripted_rolls"].pop(0)
            else:
                rng=random.Random(d["chance"]["rng_state"]); dice=[rng.randint(1,6),rng.randint(1,6)]; d["chance"]["rng_state"]=rng.getrandbits(63)
            d["turn"]["last_roll"]=dice
            if sum(dice)==7:
                req={str(q):sum(d["players"][q]["resources"].values())//2 for q in range(len(d["players"])) if sum(d["players"][q]["resources"].values())>7}
                if req:
                    d["pending"].append({"type":"discard","required":req,"selected":{k:counts() for k in req},"submitted_players":[],"resume_phase":"robber_move","resume_current_player":p})
                    d["phase"]="discard"; d["current_player"]=min(map(int,req))
                else: self._push_robber(d,"seven","trade",p)
            else:
                self._produce(d,sum(dice)); d["phase"]="trade"
        elif t in ("choose_discard_resource","undo_discard_resource"):
            f=d["pending"][-1]; sel=f["selected"].setdefault(str(p),counts()); sel[a["resource"]]+=1 if t.startswith("choose") else -1
        elif t=="submit_discard":
            f=d["pending"][-1]; f["submitted_players"].append(p)
            remaining=[int(q) for q in f["required"] if int(q) not in f["submitted_players"]]
            if remaining: d["current_player"]=min(remaining)
            else:
                for q,s in f["selected"].items():
                    for r,n in s.items(): d["players"][int(q)]["resources"][r]-=n; d["bank"]["resources"][r]+=n
                d["pending"].pop(); self._push_robber(d,"seven","trade",f["resume_current_player"])
        elif t=="move_robber":
            for h in d["board"]["hexes"]: h["robber"]=h["id"]==a["hex"]
            f=d["pending"].pop(); victims=sorted({v["building"]["owner"] for v in d["board"]["vertices"]
                if v["building"] and a["hex"] in VERTEX_HEXES[v["id"]] and v["building"]["owner"]!=p})
            if victims:
                d["pending"].append({"type":"robber_steal","resume_phase":f["resume_phase"],"resume_current_player":f["resume_current_player"],"victims":victims,"source":f["source"]})
                d["phase"]="robber_steal"; d["current_player"]=p
            else: self._resume(d,f)
        elif t=="steal_resource":
            f=d["pending"].pop(); victim=a["victim"]; pool=[r for r,n in self._available(d,victim).items() for _ in range(n)]
            if pool:
                if d["chance"]["scripted_steals"]: r=d["chance"]["scripted_steals"].pop(0)
                else:
                    rng=random.Random(d["chance"]["rng_state"]); r=rng.choice(pool); d["chance"]["rng_state"]=rng.getrandbits(63)
                d["players"][victim]["resources"][r]-=1; d["players"][p]["resources"][r]+=1
            self._resume(d,f)
        elif t=="begin_domestic_trade":
            d["pending"].append({"type":"trade_offer","partner":a["partner"],"give":counts(),"take":counts(),"status":"building","resume_phase":"trade","resume_current_player":p}); d["phase"]="trade_offer"
        elif t=="add_trade_item": d["pending"][-1][a["direction"]][a["resource"]]+=1
        elif t=="propose_domestic_trade":
            d["pending"][-1]["status"]="awaiting_response"; d["current_player"]=d["pending"][-1]["partner"]
        elif t=="accept_domestic_trade":
            f=d["pending"].pop(); owner=f["resume_current_player"]; partner=f["partner"]
            for r in RES:
                d["players"][owner]["resources"][r]-=f["give"][r]; d["players"][partner]["resources"][r]+=f["give"][r]
                d["players"][partner]["resources"][r]-=f["take"][r]; d["players"][owner]["resources"][r]+=f["take"][r]
            d["phase"]="trade"; d["current_player"]=owner
        elif t in ("reject_domestic_trade","cancel_domestic_trade"):
            f=d["pending"].pop(); d["phase"]="trade"; d["current_player"]=f["resume_current_player"]
        elif t=="maritime_trade":
            ratio=self._ratio(d,p,a["give"]); d["players"][p]["resources"][a["give"]]-=ratio; d["bank"]["resources"][a["give"]]+=ratio
            d["bank"]["resources"][a["receive"]]-=1; d["players"][p]["resources"][a["receive"]]+=1
        elif t=="end_trade": d["phase"]="build"
        elif t in ("build_road","place_free_road"):
            e=a["edge"]; next(x for x in d["board"]["edges"] if x["id"]==e)["road_owner"]=p; d["players"][p]["pieces"]["roads"]-=1
            if t=="build_road": self._pay(d,p,wood=1,brick=1)
            else:
                f=d["pending"][-1]; f["remaining"]-=1
                if f["remaining"]==0 or not self._legal_roads(d,p): d["pending"].pop(); self._resume(d,f)
            self._update_longest(d)
        elif t=="build_settlement":
            next(v for v in d["board"]["vertices"] if v["id"]==a["vertex"])["building"]={"owner":p,"type":"settlement"}
            d["players"][p]["pieces"]["settlements"]-=1; self._pay(d,p,wood=1,brick=1,wool=1,grain=1)
        elif t=="build_city":
            next(v for v in d["board"]["vertices"] if v["id"]==a["vertex"])["building"]["type"]="city"
            d["players"][p]["pieces"]["settlements"]+=1; d["players"][p]["pieces"]["cities"]-=1; self._pay(d,p,ore=3,grain=2)
        elif t=="buy_development":
            self._pay(d,p,ore=1,wool=1,grain=1); c=d["bank"]["development_deck"].pop(0)
            d["players"][p]["development_hand"].append({"id":c,"bought_turn":d["turn"]["number"],"revealed":False})
        elif t.startswith("play_"):
            self._play_dev(d,p,t,a)
        elif t=="end_turn":
            p=(p+1)%len(d["players"]); d["active_player"]=p; d["current_player"]=p; d["phase"]="roll"
            d["turn"]={"number":d["turn"]["number"]+1,"development_played":False,"last_roll":None}
        self._victory(d)
        return GameState(d)

    def _produce(self,d,total):
        claims={r:[] for r in RES}
        for h in d["board"]["hexes"]:
            if h["number"]==total and not h["robber"]:
                for v in d["board"]["vertices"]:
                    if v["building"] and h["id"] in VERTEX_HEXES[v["id"]]:
                        claims[h["terrain"]].append((v["building"]["owner"],2 if v["building"]["type"]=="city" else 1))
        for r,items in claims.items():
            if sum(n for _,n in items)<=d["bank"]["resources"][r]:
                for p,n in items: d["players"][p]["resources"][r]+=n; d["bank"]["resources"][r]-=n

    def _pay(self,d,p,**cost):
        for r,n in cost.items(): d["players"][p]["resources"][r]-=n; d["bank"]["resources"][r]+=n

    def _push_robber(self,d,source,resume,p):
        d["pending"].append({"type":"robber_move","resume_phase":resume,"resume_current_player":p,"source":source})
        d["phase"]="robber_move"; d["current_player"]=p

    def _resume(self,d,f):
        d["phase"]=f["resume_phase"]; d["current_player"]=f["resume_current_player"]

    def _play_dev(self,d,p,t,a):
        ident={"play_knight":"knight","play_road_building":"road_building","play_year_of_plenty":"year_of_plenty","play_monopoly":"monopoly"}[t]
        card=next(c for c in d["players"][p]["development_hand"] if c["id"]==ident and not c["revealed"] and c["bought_turn"]<d["turn"]["number"])
        card["revealed"]=True; d["bank"]["played_development"].append({"owner":p,"id":ident}); d["turn"]["development_played"]=True
        resume_phase=d["phase"]; resume_player=d["current_player"]
        if t=="play_knight":
            d["players"][p]["played_knights"]+=1; self._update_army(d); self._push_robber(d,"knight",resume_phase,resume_player)
        elif t=="play_road_building":
            n=min(2,d["players"][p]["pieces"]["roads"])
            if n and self._legal_roads(d,p):
                d["pending"].append({"type":"road_building","resume_phase":resume_phase,"resume_current_player":resume_player,"remaining":n}); d["phase"]="road_building"; d["current_player"]=p
        elif t=="play_year_of_plenty":
            for r in a["resources"]: d["bank"]["resources"][r]-=1; d["players"][p]["resources"][r]+=1
        else:
            r=a["resource"]
            for q in range(len(d["players"])):
                if q!=p:
                    n=self._available(d,q)[r]; d["players"][q]["resources"][r]-=n; d["players"][p]["resources"][r]+=n

    def _road_length(self,d,p):
        owned={e["id"] for e in d["board"]["edges"] if e["road_owner"]==p}
        blocked={v["id"] for v in d["board"]["vertices"] if v["building"] and v["building"]["owner"]!=p}
        def walk(v,used):
            best=len(used)
            if v in blocked and used: return best
            for e in owned-used:
                a,b=EDGE_VERTS[e]
                if v==a or v==b: best=max(best,walk(b if v==a else a,used|{e}))
            return best
        return max([walk(v,set()) for v in VERTEX_HEXES]+[0])

    def _update_longest(self,d):
        lens=[self._road_length(d,p) for p in range(len(d["players"]))]; old=d["special_cards"]["longest_road_owner"]; m=max(lens)
        if m<5: owner=None
        elif lens.count(m)==1: owner=lens.index(m)
        else: owner=old if old is not None and lens[old]==m else None
        d["special_cards"]["longest_road_owner"]=owner; d["special_cards"]["longest_road_length"]=m

    def _update_army(self,d):
        ns=[p["played_knights"] for p in d["players"]]; old=d["special_cards"]["largest_army_owner"]; m=max(ns)
        if m<3: owner=None
        elif ns.count(m)==1: owner=ns.index(m)
        else: owner=old if old is not None and ns[old]==m else None
        d["special_cards"]["largest_army_owner"]=owner

    def _score(self,d,p,hidden=True):
        n=sum(2 if v["building"]["type"]=="city" else 1 for v in d["board"]["vertices"] if v["building"] and v["building"]["owner"]==p)
        n+=2*(d["special_cards"]["longest_road_owner"]==p)+2*(d["special_cards"]["largest_army_owner"]==p)
        if hidden: n+=sum(c["id"] in VP_DEVS for c in d["players"][p]["development_hand"])
        else: n+=sum(c["id"] in VP_DEVS and c["revealed"] for c in d["players"][p]["development_hand"])
        return n

    def _victory(self,d):
        p=d["active_player"]
        if self._score(d,p)>=10:
            need=10-self._score(d,p,False)
            for c in d["players"][p]["development_hand"]:
                if need<=0: break
                if c["id"] in VP_DEVS and not c["revealed"]: c["revealed"]=True; need-=1
            d["terminal"]=True; d["winner"]=p; d["phase"]="terminal"; d["current_player"]=p; d["pending"]=[]

    def state_to_data(self,state): return {"schema":STATE_SCHEMA,"data":copy.deepcopy(state.data)}
    def state_from_data(self,payload):
        self._envelope(payload,STATE_SCHEMA)
        req={"configuration","current_player","active_player","phase","turn","terminal","winner","players","board","bank","special_cards","pending","chance","zones"}
        if set(payload["data"])!=req: raise ValueError("invalid state fields")
        return GameState(copy.deepcopy(payload["data"]))

    def action_to_data(self,action):
        args=copy.deepcopy(action.argdict())
        if "resources" in args: args["resources"]=list(args["resources"])
        return {"schema":ACTION_SCHEMA,"data":{"type":action.type,"actor":action.actor,"args":args}}
    def action_from_data(self,payload):
        self._envelope(payload,ACTION_SCHEMA)
        d=payload["data"]
        if set(d)!={"type","actor","args"} or type(d["actor"]) is not int or not isinstance(d["args"],dict): raise ValueError("invalid action")
        if d["type"] not in ("roll_dice","choose_discard_resource","undo_discard_resource","submit_discard","move_robber","steal_resource","begin_domestic_trade","add_trade_item","propose_domestic_trade","accept_domestic_trade","reject_domestic_trade","cancel_domestic_trade","maritime_trade","end_trade","build_road","build_settlement","build_city","buy_development","play_knight","play_road_building","place_free_road","play_year_of_plenty","play_monopoly","end_turn"): raise ValueError("unknown action")
        args=copy.deepcopy(d["args"])
        if "resources" in args: args["resources"]=tuple(args["resources"])
        return act(d["type"],d["actor"],**args)

    def _envelope(self,p,schema):
        if not isinstance(p,dict) or set(p)!={"schema","data"} or p["schema"]!=schema or not isinstance(p["data"],dict): raise ValueError("invalid envelope")

    def action_to_name(self,action):
        a=action.argdict()
        for k,v in list(a.items()):
            if isinstance(v,tuple): a[k]=list(v)
        tail=json.dumps(a,ensure_ascii=False,sort_keys=True,separators=(",",":"))
        return f"{action.type} [actor {action.actor}] {tail}"
    def name_to_action(self,name):
        for p in range(self.num_players):
            prefix=f" [actor {p}] "
            if prefix in name:
                typ,tail=name.split(prefix,1)
                try: args=json.loads(tail)
                except (ValueError,TypeError) as exc: raise ValueError("invalid action name") from exc
                if "resources" in args: args["resources"]=tuple(args["resources"])
                return act(typ,p,**args)
        raise ValueError("invalid action name")

    def observation_to_data(self,state,player):
        d=state.data
        if type(player) is not int or not 0<=player<len(d["players"]): raise ValueError("invalid player")
        pending=[]
        for f in d["pending"]:
            g=copy.deepcopy(f)
            if g["type"]=="discard":
                own=g["selected"].get(str(player))
                g.pop("selected"); g["own_selected"]=own
            pending.append(g)
        obs={"player":player,"current_player":d["current_player"],"active_player":d["active_player"],
          "phase":d["phase"],"turn":copy.deepcopy(d["turn"]),"terminal":d["terminal"],"winner":d["winner"],
          "own_resources":copy.deepcopy(d["players"][player]["resources"]),
          "own_development":copy.deepcopy(d["players"][player]["development_hand"]),
          "opponents":[{"id":q["id"],"resource_count":sum(q["resources"].values()),"development_count":sum(not c["revealed"] for c in q["development_hand"]),"played_knights":q["played_knights"]} for q in d["players"] if q["id"]!=player],
          "board":copy.deepcopy(d["board"]),
          "bank":{"resources":copy.deepcopy(d["bank"]["resources"]),"development_deck_size":len(d["bank"]["development_deck"]),"played_development":copy.deepcopy(d["bank"]["played_development"])},
          "visible_scores":[self._score(d,p,False) for p in range(len(d["players"]))],
          "special_cards":copy.deepcopy(d["special_cards"]),"pending":pending}
        return {"schema":OBS_SCHEMA,"data":obs}

    def render(self,state):
        d=state.data
        scores=", ".join(f"{p['color']}={self._score(d,p['id'],False)} VP/{sum(p['resources'].values())} cards" for p in d["players"])
        return f"CATAN turn {d['turn']['number']} phase={d['phase']} actor={d['current_player']}; {scores}"
