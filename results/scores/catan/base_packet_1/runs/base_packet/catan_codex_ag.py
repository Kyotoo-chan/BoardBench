"""CATAN (2022 beginner layout), implemented from the supplied German rules."""
from __future__ import annotations

import copy
import json
import math

RESOURCES = ("wood", "brick", "wool", "grain", "ore")
DEVELOPMENT = ("knight", "road_building", "year_of_plenty", "monopoly",
               "library", "marketplace", "city_hall", "chapel", "university")
PHASES = ("roll", "discard", "robber_move", "robber_steal", "trade",
          "trade_offer", "build", "road_building", "terminal")
ACTION_TYPES = ("roll_dice", "discard_resource", "move_robber", "steal_resource",
 "begin_domestic_trade", "add_trade_item", "cancel_domestic_trade",
 "commit_domestic_trade", "maritime_trade", "end_trade", "build_road",
 "build_settlement", "build_city", "buy_development", "play_knight",
 "play_road_building", "place_free_road", "play_year_of_plenty",
 "play_monopoly", "end_turn")
COLORS = ("red", "blue", "orange", "white")
HEXES = [
 ("h00","ore",10),("h01","wool",2),("h02","wood",9),("h03","grain",12),
 ("h04","brick",6),("h05","wool",4),("h06","brick",10),("h07","grain",9),
 ("h08","wood",11),("h09","desert",None),("h10","wood",3),("h11","ore",8),
 ("h12","wood",8),("h13","ore",3),("h14","grain",4),("h15","wool",5),
 ("h16","brick",5),("h17","grain",6),("h18","wool",11)]
HARBORS = [
 ("p00",2,"grain",("v01","v05")),("p01",2,"wood",("v10","v15")),
 ("p02",3,None,("v26","v32")),("p03",2,"wool",("v46","v50")),
 ("p04",3,None,("v49","v52")),("p05",3,None,("v47","v51")),
 ("p06",2,"brick",("v27","v33")),("p07",2,"ore",("v11","v16")),
 ("p08",3,None,("v00","v03"))]
SETTLEMENTS = [(0,"v08"),(0,"v28"),(1,"v39"),(1,"v41"),
               (2,"v14"),(2,"v40"),(3,"v17"),(3,"v31")]
ROADS = [(0,"e_v08_v13"),(0,"e_v28_v34"),(1,"e_v39_v44"),
         (1,"e_v36_v41"),(2,"e_v09_v14"),(2,"e_v40_v45"),
         (3,"e_v17_v22"),(3,"e_v25_v31")]
START = [
 {"wood":2,"brick":0,"wool":0,"grain":1,"ore":0},
 {"wood":1,"brick":1,"wool":0,"grain":0,"ore":1},
 {"wood":0,"brick":0,"wool":0,"grain":2,"ore":1},
 {"wood":1,"brick":0,"wool":1,"grain":0,"ore":1}]
COSTS = {"build_road":{"wood":1,"brick":1},
 "build_settlement":{"wood":1,"brick":1,"wool":1,"grain":1},
 "build_city":{"ore":3,"grain":2},
 "buy_development":{"ore":1,"wool":1,"grain":1}}
VP_CARDS = {"library","marketplace","city_hall","chapel","university"}


class Action(tuple):
    def __new__(cls, kind, actor, args=None):
        return tuple.__new__(cls, (kind, actor, tuple(sorted((args or {}).items()))))
    @property
    def kind(self): return self[0]
    @property
    def actor(self): return self[1]
    @property
    def args(self): return dict(self[2])
    def __reduce__(self):
        return (Action, (self.kind, self.actor, self.args))


class GameState:
    def __init__(self, data):
        self.data = data
    def __deepcopy__(self, memo):
        return GameState(copy.deepcopy(self.data, memo))


def _topology():
    rows = (3,4,5,4,3)
    corners, hex_corners = {}, {}
    for r,n in enumerate(rows):
        for c in range(n):
            hid = f"h{sum(rows[:r])+c:02d}"
            x=(c+abs(2-r)/2)*math.sqrt(3); y=1.5*r
            pts=[]
            for angle in (30,90,150,210,270,330):
                a=math.radians(angle)
                p=(round((x+math.cos(a))*1000),round((y+math.sin(a))*1000))
                corners[p]=None; pts.append(p)
            hex_corners[hid]=pts
    for i,p in enumerate(sorted(corners,key=lambda p:(p[1],p[0]))):
        corners[p]=f"v{i:02d}"
    edge_set=set()
    for pts in hex_corners.values():
        vs=[corners[p] for p in pts]
        for i in range(6):
            edge_set.add(tuple(sorted((vs[i],vs[(i+1)%6]))))
    return corners, hex_corners, sorted(edge_set)


_CORNERS, _HEX_CORNERS, _EDGE_PAIRS = _topology()
VERTICES = tuple(f"v{i:02d}" for i in range(54))
EDGES = tuple("e_"+a+"_"+b for a,b in _EDGE_PAIRS)
EDGE_VERTICES = dict(zip(EDGES, _EDGE_PAIRS))
ADJ = {v:set() for v in VERTICES}
for a,b in _EDGE_PAIRS: ADJ[a].add(b); ADJ[b].add(a)
VERTEX_HEXES = {v:[] for v in VERTICES}
for h,pts in _HEX_CORNERS.items():
    for p in pts: VERTEX_HEXES[_CORNERS[p]].append(h)


class Game:
    def __init__(self, num_players=None, seed=None):
        if num_players not in (None,4):
            raise ValueError("the supplied beginner setup defines exactly four players")
        if seed is not None and (type(seed) is not int):
            raise TypeError("seed must be an integer or None")
        self.seed = seed

    def initial_state(self):
        vertices=[{"id":v,"building":None,"harbor_ids":[]} for v in VERTICES]
        vm={x["id"]:x for x in vertices}
        harbors=[]
        for hid,ratio,res,vs in HARBORS:
            harbors.append({"id":hid,"ratio":ratio,"resource":res,"vertices":list(vs)})
            for v in vs: vm[v]["harbor_ids"].append(hid)
        for p,v in SETTLEMENTS: vm[v]["building"]={"owner":p,"type":"settlement"}
        edges=[{"id":e,"vertices":list(EDGE_VERTICES[e]),"road_owner":None} for e in EDGES]
        em={x["id"]:x for x in edges}
        for p,e in ROADS: em[e]["road_owner"]=p
        inv=(["knight"]*14+["road_building"]*2+["year_of_plenty"]*2+
             ["monopoly"]*2+["library","marketplace","city_hall","chapel","university"])
        rng = (self.seed if self.seed is not None else 0xC0A7A) & 0x7fffffff
        for i in range(len(inv)-1,0,-1):
            rng=(1103515245*rng+12345)&0x7fffffff
            j=rng%(i+1); inv[i],inv[j]=inv[j],inv[i]
        players=[]
        for p in range(4):
            players.append({"id":p,"color":COLORS[p],"resources":copy.deepcopy(START[p]),
              "development_hand":[],"played_knights":0,
              "pieces":{"roads":13,"settlements":3,"cities":4}})
        used={r:sum(x["resources"][r] for x in players) for r in RESOURCES}
        d={"configuration":{"players":4,"seed":self.seed,"oldest_player":0,"setup":"beginner_4p"},
           "current_player":0,"active_player":0,"phase":"roll",
           "turn":{"number":1,"development_played":False,"last_roll":None},
           "terminal":False,"winner":None,"players":players,
           "board":{"hexes":[{"id":h,"terrain":t,"number":n,"robber":h=="h09"} for h,t,n in HEXES],
                    "vertices":vertices,"edges":edges,"harbors":harbors},
           "bank":{"resources":{r:19-used[r] for r in RESOURCES},
                   "development_deck":inv,"played_development":[]},
           "special_cards":{"longest_road_owner":None,"longest_road_length":0,
                            "largest_army_owner":None},
           "pending":None,"chance":{"rng_state":rng,"scripted_rolls":[],"scripted_steals":[]},
           "zones":{"reserve":{"resources":{r:0 for r in RESOURCES},"development_cards":[]}}}
        return GameState(d)

    def current_player(self,state): return state.data["current_player"]
    def is_terminal(self,state): return bool(state.data["terminal"])
    def returns(self,state):
        n=len(state.data["players"])
        if not self.is_terminal(state): return [0.0]*n
        return [1.0 if i==state.data["winner"] else -1.0 for i in range(n)]

    def _score(self,d,p,include_hidden=True):
        s=0
        for v in d["board"]["vertices"]:
            b=v["building"]
            if b and b["owner"]==p: s += 1 if b["type"]=="settlement" else 2
        if d["special_cards"]["longest_road_owner"]==p: s+=2
        if d["special_cards"]["largest_army_owner"]==p: s+=2
        if include_hidden: s+=sum(c["id"] in VP_CARDS for c in d["players"][p]["development_hand"])
        return s

    def _can_pay(self,p,cost): return all(p["resources"][r]>=n for r,n in cost.items())
    def _road_legal(self,d,p,e):
        edge=next((x for x in d["board"]["edges"] if x["id"]==e),None)
        if not edge or edge["road_owner"] is not None: return False
        vm={v["id"]:v["building"] for v in d["board"]["vertices"]}
        em={x["id"]:x["road_owner"] for x in d["board"]["edges"]}
        for v in edge["vertices"]:
            b=vm[v]
            if b and b["owner"]==p: return True
            if b and b["owner"]!=p: continue
            if any(em["e_"+min(v,w)+"_"+max(v,w)]==p for w in ADJ[v]): return True
        return False
    def _settlement_legal(self,d,p,v):
        vm={x["id"]:x["building"] for x in d["board"]["vertices"]}
        if v not in vm or vm[v] is not None or any(vm[w] for w in ADJ[v]): return False
        em={x["id"]:x["road_owner"] for x in d["board"]["edges"]}
        return any(em["e_"+min(v,w)+"_"+max(v,w)]==p for w in ADJ[v])
    def _dev_actions(self,d,p):
        if d["turn"]["development_played"]: return []
        ids={c["id"] for c in d["players"][p]["development_hand"] if c["bought_turn"]<d["turn"]["number"]}
        out=[]
        if "knight" in ids: out.append(Action("play_knight",p,{"card":"knight"}))
        if "road_building" in ids and d["players"][p]["pieces"]["roads"]>0:
            out.append(Action("play_road_building",p,{"card":"road_building"}))
        if "year_of_plenty" in ids:
            for a in RESOURCES:
                for b in RESOURCES:
                    need=2 if a==b else 1
                    if d["bank"]["resources"][a]>=need and (a==b or d["bank"]["resources"][b]>=1):
                        out.append(Action("play_year_of_plenty",p,{"card":"year_of_plenty","resources":(a,b)}))
        if "monopoly" in ids:
            out += [Action("play_monopoly",p,{"card":"monopoly","resource":r}) for r in RESOURCES]
        return out

    def legal_actions(self,state):
        d=state.data
        if d["terminal"]: return []
        p=d["current_player"]; phase=d["phase"]; out=[]
        if phase=="discard":
            pend=d["pending"]; submitted=pend["submitted"].get(str(p),{r:0 for r in RESOURCES})
            if sum(submitted.values()) < pend["required"][str(p)]:
                out=[Action("discard_resource",p,{"resource":r}) for r in RESOURCES
                     if d["players"][p]["resources"][r]>submitted[r]]
        elif phase=="robber_move":
            out=[Action("move_robber",p,{"hex":h["id"]}) for h in d["board"]["hexes"] if not h["robber"]]
        elif phase=="robber_steal":
            out=[Action("steal_resource",p,{"victim":v}) for v in d["pending"]["victims"]]
        elif phase=="road_building":
            out=[Action("place_free_road",p,{"edge":e}) for e in EDGES if self._road_legal(d,p,e)]
            if not out: self._finish_road_building(d); return self.legal_actions(state)
        elif phase=="trade_offer":
            out=[Action("cancel_domestic_trade",p)]
            pend=d["pending"]
            if self._trade_committable(d):
                out.append(Action("commit_domestic_trade",p))
            for q in range(len(d["players"])):
                if q==p: continue
                leg=next((x for x in pend["legs"] if x["partner"]==q),None)
                give=leg["give"] if leg else {r:0 for r in RESOURCES}
                take=leg["take"] if leg else {r:0 for r in RESOURCES}
                for r in RESOURCES:
                    if give[r]<d["players"][p]["resources"][r]:
                        out.append(Action("add_trade_item",p,{"partner":q,"direction":"give","resource":r}))
                    if take[r]<d["players"][q]["resources"][r]:
                        out.append(Action("add_trade_item",p,{"partner":q,"direction":"take","resource":r}))
        elif phase=="roll":
            out=[Action("roll_dice",p)]+self._dev_actions(d,p)
        elif phase=="trade":
            out=[Action("begin_domestic_trade",p),Action("end_trade",p)]+self._dev_actions(d,p)
            for give in RESOURCES:
                ratio=self._ratio(d,p,give)
                if d["players"][p]["resources"][give]>=ratio:
                    out += [Action("maritime_trade",p,{"give":give,"receive":r}) for r in RESOURCES
                            if r!=give and d["bank"]["resources"][r]>0]
        elif phase=="build":
            pl=d["players"][p]
            if pl["pieces"]["roads"] and self._can_pay(pl,COSTS["build_road"]):
                out += [Action("build_road",p,{"edge":e}) for e in EDGES if self._road_legal(d,p,e)]
            if pl["pieces"]["settlements"] and self._can_pay(pl,COSTS["build_settlement"]):
                out += [Action("build_settlement",p,{"vertex":v}) for v in VERTICES if self._settlement_legal(d,p,v)]
            if pl["pieces"]["cities"] and self._can_pay(pl,COSTS["build_city"]):
                out += [Action("build_city",p,{"vertex":v["id"]}) for v in d["board"]["vertices"]
                        if v["building"]=={"owner":p,"type":"settlement"}]
            if d["bank"]["development_deck"] and self._can_pay(pl,COSTS["buy_development"]):
                out.append(Action("buy_development",p))
            out += self._dev_actions(d,p)+[Action("end_turn",p)]
        return out

    def _ratio(self,d,p,r):
        owned={v["id"] for v in d["board"]["vertices"] if v["building"] and v["building"]["owner"]==p}
        ratio=4
        for h in d["board"]["harbors"]:
            if owned.intersection(h["vertices"]) and (h["resource"] is None or h["resource"]==r):
                ratio=min(ratio,h["ratio"])
        return ratio
    def _rand(self,d,n):
        d["chance"]["rng_state"]=(1103515245*d["chance"]["rng_state"]+12345)&0x7fffffff
        return d["chance"]["rng_state"]%n
    def _pay(self,d,p,cost):
        for r,n in cost.items():
            d["players"][p]["resources"][r]-=n; d["bank"]["resources"][r]+=n
    def _remove_dev(self,d,p,card):
        hand=d["players"][p]["development_hand"]
        i=next(i for i,c in enumerate(hand) if c["id"]==card and c["bought_turn"]<d["turn"]["number"])
        hand.pop(i); d["bank"]["played_development"].append({"owner":p,"id":card})
        d["turn"]["development_played"]=True

    def apply_action(self,state,action):
        legal=self.legal_actions(state)
        if action not in legal: raise ValueError("illegal action")
        s=copy.deepcopy(state); d=s.data; p=action.actor; a=action.args; k=action.kind
        if k=="roll_dice":
            if d["chance"]["scripted_rolls"]: dice=d["chance"]["scripted_rolls"].pop(0)
            else: dice=[self._rand(d,6)+1,self._rand(d,6)+1]
            d["turn"]["last_roll"]=dice
            if sum(dice)==7: self._begin_seven(d)
            else: self._produce(d,sum(dice)); d["phase"]="trade"
        elif k=="discard_resource":
            pend=d["pending"]; sub=pend["submitted"].setdefault(str(p),{r:0 for r in RESOURCES})
            sub[a["resource"]]+=1
            if sum(sub.values())==pend["required"][str(p)]: self._advance_discard(d)
        elif k=="move_robber": self._move_robber(d,a["hex"])
        elif k=="steal_resource": self._steal(d,a["victim"]); self._resume(d)
        elif k=="begin_domestic_trade":
            d["phase"]="trade_offer"; d["pending"]={"type":"domestic_trade","legs":[],"resume_phase":"trade"}
        elif k=="add_trade_item": self._add_trade(d,a)
        elif k=="cancel_domestic_trade": d["pending"]=None; d["phase"]="trade"
        elif k=="commit_domestic_trade": self._commit_trade(d)
        elif k=="maritime_trade":
            ratio=self._ratio(d,p,a["give"]); d["players"][p]["resources"][a["give"]]-=ratio
            d["bank"]["resources"][a["give"]]+=ratio; d["bank"]["resources"][a["receive"]]-=1
            d["players"][p]["resources"][a["receive"]]+=1
        elif k=="end_trade": d["phase"]="build"
        elif k=="build_road": self._pay(d,p,COSTS[k]); self._place_road(d,p,a["edge"])
        elif k=="build_settlement":
            self._pay(d,p,COSTS[k]); self._place_settlement(d,p,a["vertex"]); self._victory(d,p)
        elif k=="build_city":
            self._pay(d,p,COSTS[k]); v=next(x for x in d["board"]["vertices"] if x["id"]==a["vertex"])
            v["building"]["type"]="city"; d["players"][p]["pieces"]["cities"]-=1
            d["players"][p]["pieces"]["settlements"]+=1; self._victory(d,p)
        elif k=="buy_development":
            self._pay(d,p,COSTS[k]); card=d["bank"]["development_deck"].pop(0)
            d["players"][p]["development_hand"].append({"id":card,"bought_turn":d["turn"]["number"]})
            self._victory(d,p)
        elif k=="play_knight":
            self._remove_dev(d,p,"knight"); d["players"][p]["played_knights"]+=1
            self._largest_army(d); resume=d["phase"]; d["phase"]="robber_move"
            d["pending"]={"type":"robber_move","resume_phase":resume,"source":"knight"}; self._victory(d,p)
        elif k=="play_road_building":
            self._remove_dev(d,p,"road_building"); resume=d["phase"]; d["phase"]="road_building"
            d["pending"]={"type":"road_building","resume_phase":resume,"remaining":2}
        elif k=="place_free_road":
            self._place_road(d,p,a["edge"]); d["pending"]["remaining"]-=1
            if d["pending"]["remaining"]==0: self._finish_road_building(d)
        elif k=="play_year_of_plenty":
            self._remove_dev(d,p,"year_of_plenty")
            for r in a["resources"]: d["bank"]["resources"][r]-=1; d["players"][p]["resources"][r]+=1
        elif k=="play_monopoly":
            self._remove_dev(d,p,"monopoly"); r=a["resource"]
            for q in range(len(d["players"])):
                if q!=p:
                    n=d["players"][q]["resources"][r]; d["players"][q]["resources"][r]=0
                    d["players"][p]["resources"][r]+=n
        elif k=="end_turn":
            q=(p+1)%len(d["players"]); d["active_player"]=q; d["current_player"]=q
            d["phase"]="roll"; d["turn"]={"number":d["turn"]["number"]+1,
                "development_played":False,"last_roll":None}
        return s

    def _produce(self,d,total):
        demand={r:[0]*len(d["players"]) for r in RESOURCES}
        hexmap={h["id"]:h for h in d["board"]["hexes"]}
        for v in d["board"]["vertices"]:
            if not v["building"]: continue
            n=1 if v["building"]["type"]=="settlement" else 2
            for hid in VERTEX_HEXES[v["id"]]:
                h=hexmap[hid]
                if h["number"]==total and not h["robber"] and h["terrain"]!="desert":
                    demand[h["terrain"]][v["building"]["owner"]]+=n
        for r,needs in demand.items():
            if sum(needs)<=d["bank"]["resources"][r]:
                for p,n in enumerate(needs): d["players"][p]["resources"][r]+=n
                d["bank"]["resources"][r]-=sum(needs)
    def _begin_seven(self,d):
        req={str(p["id"]):sum(p["resources"].values())//2 for p in d["players"] if sum(p["resources"].values())>7}
        if req:
            d["phase"]="discard"; d["current_player"]=min(map(int,req))
            d["pending"]={"type":"discard","required":req,"submitted":{},"resume":"robber_move"}
        else:
            d["phase"]="robber_move"; d["pending"]={"type":"robber_move","resume_phase":"trade","source":"seven"}
    def _advance_discard(self,d):
        pend=d["pending"]; undone=[int(p) for p in pend["required"] if sum(pend["submitted"].get(p,{}).values())<pend["required"][p]]
        if undone: d["current_player"]=min(undone); return
        for ps,counts in pend["submitted"].items():
            p=int(ps)
            for r,n in counts.items(): d["players"][p]["resources"][r]-=n; d["bank"]["resources"][r]+=n
        d["current_player"]=d["active_player"]; d["phase"]="robber_move"
        d["pending"]={"type":"robber_move","resume_phase":"trade","source":"seven"}
    def _move_robber(self,d,hid):
        for h in d["board"]["hexes"]: h["robber"]=h["id"]==hid
        victims=sorted({v["building"]["owner"] for v in d["board"]["vertices"]
            if v["building"] and hid in VERTEX_HEXES[v["id"]]
            and v["building"]["owner"]!=d["active_player"]
            and sum(d["players"][v["building"]["owner"]]["resources"].values())>0})
        old=d["pending"]
        if victims:
            d["phase"]="robber_steal"; d["pending"]={"type":"robber_steal",
              "resume_phase":old["resume_phase"],"victims":victims,"source":old["source"]}
        else: self._resume(d)
    def _resume(self,d):
        phase=d["pending"]["resume_phase"]; d["pending"]=None; d["phase"]=phase
        d["current_player"]=d["active_player"]
    def _steal(self,d,victim):
        pool=[]
        for r in RESOURCES: pool += [r]*d["players"][victim]["resources"][r]
        scripted=d["chance"]["scripted_steals"]
        r=scripted.pop(0) if scripted else pool[self._rand(d,len(pool))]
        if r not in pool: raise ValueError("scripted stolen resource unavailable")
        d["players"][victim]["resources"][r]-=1; d["players"][d["active_player"]]["resources"][r]+=1
    def _add_trade(self,d,a):
        legs=d["pending"]["legs"]; leg=next((x for x in legs if x["partner"]==a["partner"]),None)
        if leg is None:
            leg={"partner":a["partner"],"give":{r:0 for r in RESOURCES},"take":{r:0 for r in RESOURCES}}; legs.append(leg)
        leg[a["direction"]][a["resource"]]+=1
    def _commit_trade(self,d):
        legs=d["pending"]["legs"]
        if not legs or any(sum(x["give"].values())==0 or sum(x["take"].values())==0 for x in legs):
            raise ValueError("gifts and empty trades are forbidden")
        p=d["active_player"]
        total={r:sum(x["give"][r] for x in legs) for r in RESOURCES}
        if any(total[r]>d["players"][p]["resources"][r] for r in RESOURCES): raise ValueError("trade unavailable")
        for x in legs:
            q=x["partner"]
            if any(x["take"][r]>d["players"][q]["resources"][r] for r in RESOURCES): raise ValueError("trade unavailable")
        for x in legs:
            q=x["partner"]
            for r in RESOURCES:
                d["players"][p]["resources"][r] += x["take"][r]-x["give"][r]
                d["players"][q]["resources"][r] += x["give"][r]-x["take"][r]
        d["pending"]=None; d["phase"]="trade"
    def _trade_committable(self,d):
        legs=d["pending"]["legs"]; p=d["active_player"]
        if not legs or any(sum(x["give"].values())==0 or sum(x["take"].values())==0 for x in legs):
            return False
        if any(sum(x["give"][r] for x in legs)>d["players"][p]["resources"][r] for r in RESOURCES):
            return False
        return all(all(x["take"][r]<=d["players"][x["partner"]]["resources"][r]
                       for r in RESOURCES) for x in legs)
    def _place_road(self,d,p,e):
        next(x for x in d["board"]["edges"] if x["id"]==e)["road_owner"]=p
        d["players"][p]["pieces"]["roads"]-=1; self._longest_road(d); self._victory(d,p)
    def _place_settlement(self,d,p,v):
        next(x for x in d["board"]["vertices"] if x["id"]==v)["building"]={"owner":p,"type":"settlement"}
        d["players"][p]["pieces"]["settlements"]-=1; self._longest_road(d)
    def _road_length(self,d,p):
        owned={tuple(x["vertices"]) for x in d["board"]["edges"] if x["road_owner"]==p}
        blocked={v["id"] for v in d["board"]["vertices"] if v["building"] and v["building"]["owner"]!=p}
        def walk(v,used):
            best=len(used)
            if v in blocked and used: return best
            for e in owned:
                if e not in used and v in e:
                    best=max(best,walk(e[1] if e[0]==v else e[0],used|{e}))
            return best
        return max([0]+[walk(v,set()) for e in owned for v in e])
    def _longest_road(self,d):
        lengths=[self._road_length(d,p) for p in range(len(d["players"]))]
        old=d["special_cards"]["longest_road_owner"]; m=max(lengths)
        leaders=[p for p,x in enumerate(lengths) if x==m and x>=5]
        owner=old if old in leaders else (leaders[0] if len(leaders)==1 else None)
        d["special_cards"]["longest_road_owner"]=owner
        d["special_cards"]["longest_road_length"]=m
    def _largest_army(self,d):
        vals=[p["played_knights"] for p in d["players"]]; old=d["special_cards"]["largest_army_owner"]; m=max(vals)
        leaders=[i for i,x in enumerate(vals) if x==m and x>=3]
        d["special_cards"]["largest_army_owner"]=old if old in leaders else (leaders[0] if len(leaders)==1 else None)
    def _victory(self,d,p):
        if p==d["active_player"] and self._score(d,p)>=10:
            d["terminal"]=True; d["winner"]=p; d["phase"]="terminal"; d["pending"]=None; d["current_player"]=p
    def _finish_road_building(self,d):
        phase=d["pending"]["resume_phase"]; d["pending"]=None; d["phase"]=phase

    def action_to_data(self,a):
        args=a.args
        if "resources" in args: args["resources"]=list(args["resources"])
        return {"schema":"boardbench/catan/action/1","data":{"type":a.kind,"actor":a.actor,"args":args}}
    def action_from_data(self,payload):
        if type(payload) is not dict or set(payload)!={"schema","data"} or payload["schema"]!="boardbench/catan/action/1":
            raise ValueError("invalid action envelope")
        d=payload["data"]
        if type(d) is not dict or set(d)!={"type","actor","args"} or d["type"] not in ACTION_TYPES or type(d["actor"]) is not int or type(d["args"]) is not dict:
            raise ValueError("invalid action")
        expected={"discard_resource":{"resource"},"move_robber":{"hex"},"steal_resource":{"victim"},
          "add_trade_item":{"partner","direction","resource"},"maritime_trade":{"give","receive"},
          "build_road":{"edge"},"build_settlement":{"vertex"},"build_city":{"vertex"},
          "play_knight":{"card"},"play_road_building":{"card"},"place_free_road":{"edge"},
          "play_year_of_plenty":{"card","resources"},"play_monopoly":{"card","resource"}}.get(d["type"],set())
        if set(d["args"])!=expected: raise ValueError("invalid action arguments")
        args=copy.deepcopy(d["args"])
        if "resources" in args:
            if type(args["resources"]) is not list or len(args["resources"])!=2: raise ValueError("invalid resources")
            args["resources"]=tuple(args["resources"])
        return Action(d["type"],d["actor"],args)
    def action_to_name(self,a):
        args=a.args
        tail=", ".join(f"{k}={('/'.join(v) if isinstance(v,tuple) else v)}" for k,v in sorted(args.items()))
        return a.kind.replace("_"," ").title()+f" [player {a.actor}]"+(f": {tail}" if tail else "")
    def name_to_action(self,name):
        # Names are parsed through their deliberately simple, stable grammar.
        for kind in ACTION_TYPES:
            prefix=kind.replace("_"," ").title()+" [player "
            if name.startswith(prefix):
                rest=name[len(prefix):]; actor_s,sep,tail=rest.partition("]")
                if not sep: break
                args={}
                if tail:
                    if not tail.startswith(": "): break
                    for item in tail[2:].split(", "):
                        k,v=item.split("=",1)
                        if k in ("partner","victim"): v=int(v)
                        elif k=="resources": v=tuple(v.split("/"))
                        args[k]=v
                return Action(kind,int(actor_s),args)
        raise ValueError("unknown action name")

    def state_to_data(self,state):
        return {"schema":"boardbench/catan/state/1","data":copy.deepcopy(state.data)}
    def state_from_data(self,payload):
        if type(payload) is not dict or set(payload)!={"schema","data"} or payload["schema"]!="boardbench/catan/state/1":
            raise ValueError("invalid state envelope")
        required={"configuration","current_player","active_player","phase","turn","terminal","winner",
                  "players","board","bank","special_cards","pending","chance","zones"}
        d=payload["data"]
        if type(d) is not dict or set(d)!=required: raise ValueError("invalid state fields")
        if d["phase"] not in PHASES or type(d["players"]) is not list: raise ValueError("invalid state values")
        return GameState(copy.deepcopy(d))
    def observation_to_data(self,state,player):
        d=state.data
        if type(player) is not int or not 0<=player<len(d["players"]): raise ValueError("invalid player")
        pend=copy.deepcopy(d["pending"])
        if pend and pend["type"]=="discard":
            pend={"type":"discard","required":copy.deepcopy(pend["required"]),
                  "submitted_players":sorted(int(x) for x in pend["submitted"]
                    if sum(pend["submitted"][x].values())==pend["required"][x])}
        elif pend and pend["type"]=="domestic_trade": pend={"type":"domestic_trade","legs":pend["legs"]}
        elif pend and pend["type"] in ("robber_move","robber_steal"):
            pend={k:pend[k] for k in (("type","victims","source") if pend["type"]=="robber_steal" else ("type","source"))}
        elif pend and pend["type"]=="road_building": pend={"type":"road_building","remaining":pend["remaining"]}
        obs={"player":player,"current_player":d["current_player"],"active_player":d["active_player"],
          "phase":d["phase"],"turn":copy.deepcopy(d["turn"]),"terminal":d["terminal"],"winner":d["winner"],
          "own_resources":copy.deepcopy(d["players"][player]["resources"]),
          "own_development":copy.deepcopy(d["players"][player]["development_hand"]),
          "opponents":[{"id":p["id"],"resource_count":sum(p["resources"].values()),
             "development_count":len(p["development_hand"]),"played_knights":p["played_knights"]}
             for p in d["players"] if p["id"]!=player],
          "board":copy.deepcopy(d["board"]),
          "bank":{"resources":copy.deepcopy(d["bank"]["resources"]),
             "development_deck_size":len(d["bank"]["development_deck"]),
             "played_development":copy.deepcopy(d["bank"]["played_development"])},
          "public_scores":[self._score(d,p["id"],False) for p in d["players"]],
          "special_cards":copy.deepcopy(d["special_cards"]),"pending":pend}
        return {"schema":"boardbench/catan/observation/1","data":obs}
    def render(self,state):
        d=state.data
        scores=", ".join(f"{p['color']}={self._score(d,p['id'])}" for p in d["players"])
        return f"CATAN turn {d['turn']['number']} | {d['phase']} | player {d['current_player']} | {scores}"
