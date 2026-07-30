"""Self-contained CATAN (2022 German beginner setup), standard library only."""
from dataclasses import dataclass
import copy, json, random

RES = ("wood", "brick", "wool", "grain", "ore")
DEVS = ("knight","road_building","year_of_plenty","monopoly",
        "library","marketplace","city_hall","chapel","university")
VP = set(DEVS[4:])
PHASES = ("roll","discard","robber_move","robber_steal","trade","trade_offer",
          "build","road_building","terminal")
SS, AS, OS = ("boardbench/catan/state/2","boardbench/catan/action/2",
              "boardbench/catan/observation/2")
HEXES = [
 ("h00","ore",10),("h01","wool",2),("h02","wood",9),("h03","grain",12),
 ("h04","brick",6),("h05","wool",4),("h06","brick",10),("h07","grain",9),
 ("h08","wood",11),("h09","desert",None),("h10","wood",3),("h11","ore",8),
 ("h12","wood",8),("h13","ore",3),("h14","grain",4),("h15","wool",5),
 ("h16","brick",5),("h17","grain",6),("h18","wool",11)]
VHEX = {
"v00":["h00"],"v01":["h01"],"v02":["h02"],"v03":["h00"],"v04":["h00","h01"],"v05":["h01","h02"],"v06":["h02"],
"v07":["h00","h03"],"v08":["h00","h01","h04"],"v09":["h01","h02","h05"],"v10":["h02","h06"],"v11":["h03"],
"v12":["h00","h03","h04"],"v13":["h01","h04","h05"],"v14":["h02","h05","h06"],"v15":["h06"],"v16":["h03","h07"],
"v17":["h03","h04","h08"],"v18":["h04","h05","h09"],"v19":["h05","h06","h10"],"v20":["h06","h11"],"v21":["h07"],
"v22":["h03","h07","h08"],"v23":["h04","h08","h09"],"v24":["h05","h09","h10"],"v25":["h06","h10","h11"],"v26":["h11"],
"v27":["h07"],"v28":["h07","h08","h12"],"v29":["h08","h09","h13"],"v30":["h09","h10","h14"],"v31":["h10","h11","h15"],
"v32":["h11"],"v33":["h07","h12"],"v34":["h08","h12","h13"],"v35":["h09","h13","h14"],"v36":["h10","h14","h15"],
"v37":["h11","h15"],"v38":["h12"],"v39":["h12","h13","h16"],"v40":["h13","h14","h17"],"v41":["h14","h15","h18"],
"v42":["h15"],"v43":["h12","h16"],"v44":["h13","h16","h17"],"v45":["h14","h17","h18"],"v46":["h15","h18"],
"v47":["h16"],"v48":["h16","h17"],"v49":["h17","h18"],"v50":["h18"],"v51":["h16"],"v52":["h17"],"v53":["h18"]}
EDGE_NAMES = """00_03 00_04 01_04 01_05 02_05 02_06 03_07 04_08 05_09 06_10 07_11 07_12 08_12 08_13 09_13 09_14 10_14 10_15 11_16 12_17 13_18 14_19 15_20 16_21 16_22 17_22 17_23 18_23 18_24 19_24 19_25 20_25 20_26 21_27 22_28 23_29 24_30 25_31 26_32 27_33 28_33 28_34 29_34 29_35 30_35 30_36 31_36 31_37 32_37 33_38 34_39 35_40 36_41 37_42 38_43 39_43 39_44 40_44 40_45 41_45 41_46 42_46 43_47 44_48 45_49 46_50 47_51 48_51 48_52 49_52 49_53 50_53""".split()
EDGES = [(f"e_v{x}_v{y}",f"v{x}",f"v{y}") for x,y in (z.split("_") for z in EDGE_NAMES)]
HARBORS = [
("p00",2,"grain",["v01","v05"]),("p01",2,"wood",["v10","v15"]),("p02",3,None,["v26","v32"]),
("p03",2,"wool",["v46","v50"]),("p04",3,None,["v49","v52"]),("p05",3,None,["v47","v51"]),
("p06",2,"brick",["v27","v33"]),("p07",2,"ore",["v11","v16"]),("p08",3,None,["v00","v03"])]
SETUPS = {
3: (["blue","orange","white"],
 [(0,"v39"),(0,"v41"),(1,"v14"),(1,"v40"),(2,"v17"),(2,"v31")],
 [(0,"e_v39_v44"),(0,"e_v36_v41"),(1,"e_v09_v14"),(1,"e_v40_v45"),(2,"e_v17_v22"),(2,"e_v25_v31")],
 [{"wood":1,"brick":1,"wool":0,"grain":0,"ore":1},{"wood":0,"brick":0,"wool":0,"grain":2,"ore":1},{"wood":1,"brick":0,"wool":1,"grain":0,"ore":1}]),
4: (["red","blue","orange","white"],
 [(0,"v08"),(0,"v28"),(1,"v39"),(1,"v41"),(2,"v14"),(2,"v40"),(3,"v17"),(3,"v31")],
 [(0,"e_v08_v13"),(0,"e_v28_v34"),(1,"e_v39_v44"),(1,"e_v36_v41"),(2,"e_v09_v14"),(2,"e_v40_v45"),(3,"e_v17_v22"),(3,"e_v25_v31")],
 [{"wood":2,"brick":0,"wool":0,"grain":1,"ore":0},{"wood":1,"brick":1,"wool":0,"grain":0,"ore":1},{"wood":0,"brick":0,"wool":0,"grain":2,"ore":1},{"wood":1,"brick":0,"wool":1,"grain":0,"ore":1}])
}
COST = {"road":{"wood":1,"brick":1},"settlement":{"wood":1,"brick":1,"wool":1,"grain":1},
        "city":{"ore":3,"grain":2},"development":{"ore":1,"wool":1,"grain":1}}

@dataclass(eq=True)
class GameState:
    data: dict

@dataclass(frozen=True)
class Action:
    type: str
    actor: int
    args: tuple = ()

def _zero(): return {r:0 for r in RES}
def _args(a): return dict(a.args)
def _edge_vertices(eid):
    e = next(e for e in EDGES if e[0] == eid); return e[1],e[2]

class Game:
    def __init__(self, num_players=None, seed=None):
        self.num_players = 4 if num_players is None else num_players
        if self.num_players not in (3,4): raise ValueError("CATAN source supports 3 or 4 players")
        self.seed = seed

    def initial_state(self):
        n=self.num_players; colors, settlements, roads, hands=SETUPS[n]
        rng=random.Random(self.seed)
        deck=sum(([d]*({"knight":14,"road_building":2,"year_of_plenty":2,"monopoly":2}.get(d,1)) for d in DEVS),[])
        rng.shuffle(deck)
        vertices=[{"id":v,"building":None,"harbor_ids":[p[0] for p in HARBORS if v in p[3]]} for v in VHEX]
        edges=[{"id":e,"vertices":[a,b],"road_owner":None} for e,a,b in EDGES]
        for p,v in settlements: vertices[int(v[1:])]["building"]={"owner":p,"type":"settlement"}
        em={e["id"]:e for e in edges}
        for p,e in roads: em[e]["road_owner"]=p
        players=[]
        for p in range(n):
            players.append({"id":p,"color":colors[p],"resources":copy.deepcopy(hands[p]),
             "development_hand":[],"played_knights":0,
             "pieces":{"roads":13,"settlements":3,"cities":4}})
        bank={r:19-sum(x[r] for x in hands) for r in RES}
        d={"configuration":{"players":n,"seed":self.seed,"oldest_player":0,"setup":"beginner_illustrated"},
           "current_player":0,"active_player":0,"phase":"roll","turn":{"number":1,"development_played":False,"last_roll":None},
           "terminal":False,"winner":None,"players":players,
           "board":{"hexes":[{"id":i,"terrain":t,"number":num,"robber":i=="h09"} for i,t,num in HEXES],
                    "vertices":vertices,"edges":edges,
                    "harbors":[{"id":i,"ratio":q,"resource":r,"vertices":vs} for i,q,r,vs in HARBORS]},
           "bank":{"resources":bank,"development_deck":deck,"played_development":[]},
           "special_cards":{"longest_road_owner":None,"longest_road_length":0,"largest_army_owner":None},
           "pending":[],"chance":{"rng_state":rng.getrandbits(63),"scripted_rolls":[],"scripted_steals":[]},
           "zones":{"reserve":{"resources":_zero(),"development_cards":[],"removed_colors":["red"] if n==3 else []}}}
        return GameState(d)

    def current_player(self,s): return s.data["current_player"]
    def is_terminal(self,s): return s.data["terminal"]
    def returns(self,s):
        if not s.data["terminal"]: return [0]*len(s.data["players"])
        return [1 if i==s.data["winner"] else -1 for i in range(len(s.data["players"]))]

    def _act(self,t,p,**kw): return Action(t,p,tuple(sorted(kw.items())))
    def _can_pay(self,p,c): return all(p["resources"][r]>=v for r,v in c.items())
    def _connected_edge(self,d,p,eid):
        a,b=_edge_vertices(eid)
        for v in (a,b):
            bld=d["board"]["vertices"][int(v[1:])]["building"]
            if bld and bld["owner"]==p:return True
            if bld and bld["owner"]!=p:continue
            if any(e["road_owner"]==p and v in e["vertices"] for e in d["board"]["edges"]):return True
        return False
    def _road_actions(self,d,p,free=False):
        if not free and (d["players"][p]["pieces"]["roads"]<=0 or not self._can_pay(d["players"][p],COST["road"])):return []
        return [self._act("place_free_road" if free else "build_road",p,edge=e["id"])
                for e in d["board"]["edges"] if e["road_owner"] is None and self._connected_edge(d,p,e["id"])]
    def _settlement_actions(self,d,p):
        pl=d["players"][p]
        if pl["pieces"]["settlements"]<=0 or not self._can_pay(pl,COST["settlement"]):return []
        occupied={v["id"] for v in d["board"]["vertices"] if v["building"]}
        adjacent={x for e,a,b in EDGES if a in occupied or b in occupied for x in (a,b)}
        roadverts={x for e,a,b in EDGES if next(z for z in d["board"]["edges"] if z["id"]==e)["road_owner"]==p for x in (a,b)}
        return [self._act("build_settlement",p,vertex=v) for v in VHEX if v not in occupied and v not in adjacent and v in roadverts]
    def _dev_actions(self,d,p):
        if d["turn"]["development_played"]:return []
        ids={c["id"] for c in d["players"][p]["development_hand"] if not c["revealed"] and c["bought_turn"]<d["turn"]["number"] and c["id"] not in VP}
        out=[]
        if "knight" in ids:out.append(self._act("play_knight",p,card="knight"))
        if "road_building" in ids:out.append(self._act("play_road_building",p,card="road_building"))
        if "year_of_plenty" in ids:
            out += [self._act("play_year_of_plenty",p,card="year_of_plenty",resources=[a,b])
                    for a in RES for b in RES if d["bank"]["resources"][a]>=1+(a==b)]
        if "monopoly" in ids:out += [self._act("play_monopoly",p,card="monopoly",resource=r) for r in RES]
        return out

    def legal_actions(self,s):
        d=s.data
        if d["terminal"]:return []
        p=d["current_player"]; ph=d["phase"]; out=[]
        if ph=="roll": out=[self._act("roll_dice",p)]
        elif ph=="discard":
            f=d["pending"][-1]; sel=f["selected"].get(str(p),_zero()); hand=d["players"][p]["resources"]
            out=[self._act("choose_discard_resource",p,resource=r) for r in RES if hand[r]-sel[r]>0 and sum(sel.values())<f["required"].get(str(p),0)]
            out += [self._act("undo_discard_resource",p,resource=r) for r in RES if sel[r]>0]
            if sum(sel.values())==f["required"].get(str(p),0):out.append(self._act("submit_discard",p))
        elif ph=="robber_move":
            old=next(h["id"] for h in d["board"]["hexes"] if h["robber"])
            out=[self._act("move_robber",p,hex=h["id"]) for h in d["board"]["hexes"] if h["id"]!=old]
        elif ph=="robber_steal":
            out=[self._act("steal_resource",p,victim=v) for v in d["pending"][-1]["victims"]]
        elif ph=="trade":
            out=[self._act("begin_domestic_trade",p,partner=q) for q in range(len(d["players"])) if q!=p]
            ratios={r:4 for r in RES}
            verts=[v for v in d["board"]["vertices"] if v["building"] and v["building"]["owner"]==p]
            for v in verts:
                for hid in v["harbor_ids"]:
                    h=next(x for x in d["board"]["harbors"] if x["id"]==hid)
                    if h["resource"] is None:
                        for r in RES:ratios[r]=min(ratios[r],3)
                    else:ratios[h["resource"]]=2
            for give in RES:
                if d["players"][p]["resources"][give]>=ratios[give]:
                    out += [self._act("maritime_trade",p,give=give,receive=r) for r in RES if r!=give and d["bank"]["resources"][r]>0]
            out.append(self._act("end_trade",p))
        elif ph=="trade_offer":
            f=d["pending"][-1]
            if f["status"]=="building":
                out=[self._act("add_trade_item",p,direction=x,resource=r) for x in ("give","take") for r in RES]
                if sum(f["give"].values()) and sum(f["take"].values()):out.append(self._act("propose_domestic_trade",p))
                out.append(self._act("cancel_domestic_trade",p))
            else:
                a0=f["resume_current_player"]; partner=f["partner"]
                out=[self._act("reject_domestic_trade",p)]
                if self._can_pay(d["players"][a0],f["give"]) and self._can_pay(d["players"][partner],f["take"]):
                    out.insert(0,self._act("accept_domestic_trade",p))
        elif ph=="build":
            out=self._road_actions(d,p)+self._settlement_actions(d,p)
            pl=d["players"][p]
            if pl["pieces"]["cities"]>0 and self._can_pay(pl,COST["city"]):
                out += [self._act("build_city",p,vertex=v["id"]) for v in d["board"]["vertices"] if v["building"]=={"owner":p,"type":"settlement"}]
            if d["bank"]["development_deck"] and self._can_pay(pl,COST["development"]):out.append(self._act("buy_development",p))
            out.append(self._act("end_turn",p))
        elif ph=="road_building":
            out=self._road_actions(d,p,True)
            if not out: out=[self._act("end_turn",p)]
        # The active player may play a development card before rolling or during source-approved interrupts.
        if p==d["active_player"] or ph in ("discard","trade_offer"):
            out += self._dev_actions(d,d["active_player"])
        # canonical de-duplication
        seen=set(); unique=[]
        for a in out:
            key=self.action_to_name(a)
            if key not in seen: seen.add(key);unique.append(a)
        return unique

    def _pay(self,d,p,c):
        for r,n in c.items():d["players"][p]["resources"][r]-=n;d["bank"]["resources"][r]+=n
    def _resume(self,d):
        if not d["pending"]:return
        f=d["pending"].pop();d["phase"]=f["resume_phase"];d["current_player"]=f["resume_current_player"]
    def _next_discard(self,d,f):
        needed=[int(x) for x in f["required"] if int(x) not in f["submitted_players"]]
        if needed:d["current_player"]=needed[0]
        else:
            for ps,sel in f["selected"].items():
                p=int(ps)
                for r,n in sel.items():d["players"][p]["resources"][r]-=n;d["bank"]["resources"][r]+=n
            d["pending"].pop();self._push_robber(d,"seven","trade",d["active_player"])
    def _push_robber(self,d,source,resume_phase,resume_player):
        d["pending"].append({"type":"robber_move","resume_phase":resume_phase,"resume_current_player":resume_player,"source":source})
        d["phase"]="robber_move";d["current_player"]=d["active_player"]
    def _rng(self,d):
        x=d["chance"]["rng_state"] or 1;x=(6364136223846793005*x+1442695040888963407)&((1<<63)-1);d["chance"]["rng_state"]=x;return x
    def _score(self,d,p,hidden=True):
        buildings=sum(2 if v["building"]["type"]=="city" else 1 for v in d["board"]["vertices"] if v["building"] and v["building"]["owner"]==p)
        specials=2*(d["special_cards"]["longest_road_owner"]==p)+2*(d["special_cards"]["largest_army_owner"]==p)
        cards=sum(c["id"] in VP and (hidden or c["revealed"]) for c in d["players"][p]["development_hand"])
        return buildings+specials+cards
    def _victory(self,d):
        p=d["active_player"]
        if self._score(d,p)>=10:
            need=max(0,10-self._score(d,p,False))
            for c in d["players"][p]["development_hand"]:
                if need and c["id"] in VP and not c["revealed"]:c["revealed"]=True;need-=1
            d.update(terminal=True,winner=p,phase="terminal",current_player=p,pending=[])
    def _play_card(self,d,p,cid):
        c=next(c for c in d["players"][p]["development_hand"] if c["id"]==cid and not c["revealed"] and c["bought_turn"]<d["turn"]["number"])
        c["revealed"]=True;d["turn"]["development_played"]=True;d["bank"]["played_development"].append({"owner":p,"id":cid})

    def apply_action(self,s,a):
        if a not in self.legal_actions(s):raise ValueError("illegal action")
        ns=copy.deepcopy(s);d=ns.data;p=a.actor;k=_args(a);t=a.type
        if t=="roll_dice":
            if d["chance"]["scripted_rolls"]:roll=d["chance"]["scripted_rolls"].pop(0)
            else:roll=[self._rng(d)%6+1,self._rng(d)%6+1]
            d["turn"]["last_roll"]=roll
            if sum(roll)==7:
                req={str(q):sum(x["resources"].values())//2 for q,x in enumerate(d["players"]) if sum(x["resources"].values())>7}
                if req:
                    d["pending"].append({"type":"discard","required":req,"selected":{q:_zero() for q in req},"submitted_players":[],"resume_phase":"robber_move","resume_current_player":p})
                    d["phase"]="discard";d["current_player"]=int(next(iter(req)))
                else:self._push_robber(d,"seven","trade",p)
            else:
                claims={r:[] for r in RES}
                for h in d["board"]["hexes"]:
                    if h["number"]==sum(roll) and not h["robber"]:
                        for v in d["board"]["vertices"]:
                            if h["id"] in VHEX[v["id"]] and v["building"]:
                                claims[h["terrain"]].append((v["building"]["owner"],2 if v["building"]["type"]=="city" else 1))
                for r,cs in claims.items():
                    if sum(n for _,n in cs)<=d["bank"]["resources"][r]:
                        for q,n in cs:d["players"][q]["resources"][r]+=n;d["bank"]["resources"][r]-=n
                d["phase"]="trade"
        elif t in ("choose_discard_resource","undo_discard_resource"):
            f=d["pending"][-1];sel=f["selected"].setdefault(str(p),_zero());sel[k["resource"]]+=1 if t.startswith("choose") else -1
        elif t=="submit_discard":
            f=d["pending"][-1];f["submitted_players"].append(p);self._next_discard(d,f)
        elif t=="move_robber":
            for h in d["board"]["hexes"]:h["robber"]=h["id"]==k["hex"]
            owners=sorted({v["building"]["owner"] for v in d["board"]["vertices"] if k["hex"] in VHEX[v["id"]] and v["building"] and v["building"]["owner"]!=p})
            f=d["pending"].pop()
            if owners:
                d["pending"].append({"type":"robber_steal","resume_phase":f["resume_phase"],"resume_current_player":f["resume_current_player"],"victims":owners,"source":f["source"]})
                d["phase"]="robber_steal"
            else:d["phase"]=f["resume_phase"];d["current_player"]=f["resume_current_player"]
        elif t=="steal_resource":
            v=k["victim"];bag=[r for r in RES for _ in range(d["players"][v]["resources"][r])]
            if bag:
                scripted=d["chance"]["scripted_steals"]
                r=scripted.pop(0) if scripted and scripted[0] in bag else bag[self._rng(d)%len(bag)]
                d["players"][v]["resources"][r]-=1;d["players"][p]["resources"][r]+=1
            self._resume(d)
        elif t=="begin_domestic_trade":
            d["pending"].append({"type":"trade_offer","partner":k["partner"],"give":_zero(),"take":_zero(),"status":"building","resume_phase":"trade","resume_current_player":p});d["phase"]="trade_offer"
        elif t=="add_trade_item":d["pending"][-1][k["direction"]][k["resource"]]+=1
        elif t=="propose_domestic_trade":
            d["pending"][-1]["status"]="awaiting_response";d["current_player"]=d["pending"][-1]["partner"]
        elif t in ("accept_domestic_trade","reject_domestic_trade","cancel_domestic_trade"):
            f=d["pending"][-1]
            if t=="accept_domestic_trade":
                a0=f["resume_current_player"];b=f["partner"]
                if not self._can_pay(d["players"][a0],f["give"]) or not self._can_pay(d["players"][b],f["take"]):raise ValueError("trade resources unavailable")
                for r in RES:
                    d["players"][a0]["resources"][r]+=f["take"][r]-f["give"][r];d["players"][b]["resources"][r]+=f["give"][r]-f["take"][r]
            self._resume(d)
        elif t=="maritime_trade":
            give=k["give"];receive=k["receive"];ratio=4
            for v in d["board"]["vertices"]:
                if v["building"] and v["building"]["owner"]==p:
                    for hid in v["harbor_ids"]:
                        h=next(x for x in d["board"]["harbors"] if x["id"]==hid)
                        if h["resource"] is None or h["resource"]==give:ratio=min(ratio,h["ratio"])
            d["players"][p]["resources"][give]-=ratio;d["bank"]["resources"][give]+=ratio;d["bank"]["resources"][receive]-=1;d["players"][p]["resources"][receive]+=1
        elif t=="end_trade":d["phase"]="build"
        elif t in ("build_road","place_free_road"):
            e=next(e for e in d["board"]["edges"] if e["id"]==k["edge"]);e["road_owner"]=p;d["players"][p]["pieces"]["roads"]-=1
            if t=="build_road":self._pay(d,p,COST["road"])
            else:
                f=d["pending"][-1];f["remaining"]-=1
                if not f["remaining"] or not self._road_actions(d,p,True):self._resume(d)
        elif t=="build_settlement":
            v=d["board"]["vertices"][int(k["vertex"][1:])];v["building"]={"owner":p,"type":"settlement"};d["players"][p]["pieces"]["settlements"]-=1;self._pay(d,p,COST["settlement"])
        elif t=="build_city":
            v=d["board"]["vertices"][int(k["vertex"][1:])];v["building"]["type"]="city";d["players"][p]["pieces"]["settlements"]+=1;d["players"][p]["pieces"]["cities"]-=1;self._pay(d,p,COST["city"])
        elif t=="buy_development":
            self._pay(d,p,COST["development"]);cid=d["bank"]["development_deck"].pop();d["players"][p]["development_hand"].append({"id":cid,"bought_turn":d["turn"]["number"],"revealed":False})
        elif t=="play_knight":
            self._play_card(d,p,"knight");d["players"][p]["played_knights"]+=1
            owner=d["special_cards"]["largest_army_owner"];best=d["players"][p]["played_knights"]
            if best>=3 and (owner is None or best>d["players"][owner]["played_knights"]):d["special_cards"]["largest_army_owner"]=p
            self._push_robber(d,"knight",d["phase"],d["current_player"])
        elif t=="play_road_building":
            self._play_card(d,p,"road_building")
            frame={"type":"road_building","resume_phase":d["phase"],"resume_current_player":d["current_player"],"remaining":2}
            d["pending"].append(frame);d["phase"]="road_building";d["current_player"]=p
            if not self._road_actions(d,p,True):self._resume(d)
        elif t=="play_year_of_plenty":
            self._play_card(d,p,"year_of_plenty")
            for r in k["resources"]:d["bank"]["resources"][r]-=1;d["players"][p]["resources"][r]+=1
        elif t=="play_monopoly":
            self._play_card(d,p,"monopoly");r=k["resource"]
            for q in range(len(d["players"])):
                if q!=p:n=d["players"][q]["resources"][r];d["players"][q]["resources"][r]=0;d["players"][p]["resources"][r]+=n
        elif t=="end_turn":
            d["active_player"]=(d["active_player"]+1)%len(d["players"]);d["current_player"]=d["active_player"];d["phase"]="roll";d["turn"]={"number":d["turn"]["number"]+1,"development_played":False,"last_roll":None}
        self._victory(d)
        return ns

    def action_to_name(self,a):
        data={"actor":a.actor,**_args(a)}
        return a.type.replace("_"," ").title()+" | "+json.dumps(data,sort_keys=True,separators=(",",":"))
    def name_to_action(self,n):
        head,sep,tail=n.partition(" | ");t=head.lower().replace(" ","_");args=json.loads(tail) if sep else {}
        # actor is encoded in canonical names to make them globally reversible
        if "actor" in args: actor=args.pop("actor")
        else: actor=getattr(self,"_name_actor",0)
        return self._act(t,actor,**args)
    def action_to_data(self,a):return {"schema":AS,"data":{"type":a.type,"actor":a.actor,"args":copy.deepcopy(_args(a))}}
    def action_from_data(self,payload):
        if not isinstance(payload,dict) or set(payload)!={"schema","data"} or payload["schema"]!=AS:raise ValueError("invalid action envelope")
        d=payload["data"]
        if set(d)!={"type","actor","args"} or d["type"] not in ("roll_dice","choose_discard_resource","undo_discard_resource","submit_discard","move_robber","steal_resource","begin_domestic_trade","add_trade_item","propose_domestic_trade","accept_domestic_trade","reject_domestic_trade","cancel_domestic_trade","maritime_trade","end_trade","build_road","build_settlement","build_city","buy_development","play_knight","play_road_building","place_free_road","play_year_of_plenty","play_monopoly","end_turn") or not isinstance(d["actor"],int) or not isinstance(d["args"],dict):raise ValueError("invalid action")
        return self._act(d["type"],d["actor"],**copy.deepcopy(d["args"]))

    def state_to_data(self,s):return {"schema":SS,"data":copy.deepcopy(s.data)}
    def state_from_data(self,payload):
        if not isinstance(payload,dict) or set(payload)!={"schema","data"} or payload["schema"]!=SS or not isinstance(payload["data"],dict):raise ValueError("invalid state envelope")
        required={"configuration","current_player","active_player","phase","turn","terminal","winner","players","board","bank","special_cards","pending","chance","zones"}
        if set(payload["data"])!=required:raise ValueError("invalid state fields")
        return GameState(copy.deepcopy(payload["data"]))
    def observation_to_data(self,s,player):
        d=s.data
        if not isinstance(player,int) or not 0<=player<len(d["players"]):raise ValueError("invalid player")
        own=d["players"][player]
        pending=[]
        for f in d["pending"]:
            x=copy.deepcopy(f)
            if x["type"]=="discard":
                x.pop("selected",None)
            pending.append(x)
        od={"player":player,"current_player":d["current_player"],"active_player":d["active_player"],"phase":d["phase"],
            "turn":copy.deepcopy(d["turn"]),"terminal":d["terminal"],"winner":d["winner"],
            "own_resources":copy.deepcopy(own["resources"]),"own_development":copy.deepcopy(own["development_hand"]),
            "opponents":[{"id":p["id"],"resource_count":sum(p["resources"].values()),"development_count":sum(not c["revealed"] for c in p["development_hand"]),"played_knights":p["played_knights"]} for p in d["players"] if p["id"]!=player],
            "board":copy.deepcopy(d["board"]),"bank":{"resources":copy.deepcopy(d["bank"]["resources"]),"development_deck_size":len(d["bank"]["development_deck"]),"played_development":copy.deepcopy(d["bank"]["played_development"])},
            "visible_scores":[self._score(d,p["id"],False) for p in d["players"]],"special_cards":copy.deepcopy(d["special_cards"]),"pending":pending}
        return {"schema":OS,"data":od}
    def render(self,s):
        d=s.data;return f"CATAN turn {d['turn']['number']} phase={d['phase']} active=P{d['active_player']} scores={[self._score(d,p['id'],False) for p in d['players']]}"
