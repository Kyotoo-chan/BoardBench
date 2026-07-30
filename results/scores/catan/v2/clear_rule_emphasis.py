"""Self-contained CATAN (2022 German beginner game) environment.

Only the supplied Spielanleitung and Almanach are rule authorities.  The
fixed identifiers and serialization shape follow the evaluator profile.
"""
from __future__ import annotations

import copy
import json
import math
import random
from typing import Any

RESOURCES = ("wood", "brick", "wool", "grain", "ore")
TERRAINS = RESOURCES + ("desert",)
DEVS = ("knight", "road_building", "year_of_plenty", "monopoly",
        "library", "marketplace", "city_hall", "chapel", "university")
VP_DEVS = set(DEVS[4:])
PHASES = ("roll", "discard", "robber_move", "robber_steal", "trade",
          "trade_offer", "build", "road_building", "terminal")
ACTION_TYPES = ("roll_dice", "choose_discard_resource",
 "undo_discard_resource", "submit_discard", "move_robber", "steal_resource",
 "begin_domestic_trade", "add_trade_item", "propose_domestic_trade",
 "accept_domestic_trade", "reject_domestic_trade", "cancel_domestic_trade",
 "maritime_trade", "end_trade", "build_road", "build_settlement",
 "build_city", "buy_development", "play_knight", "play_road_building",
 "place_free_road", "play_year_of_plenty", "play_monopoly", "end_turn")
STATE_SCHEMA = "boardbench/catan/state/2"
ACTION_SCHEMA = "boardbench/catan/action/2"
OBS_SCHEMA = "boardbench/catan/observation/2"
COLORS = {3: ("blue", "orange", "white"),
          4: ("red", "blue", "orange", "white")}

HEXES = (
 ("h00","ore",10),("h01","wool",2),("h02","wood",9),
 ("h03","grain",12),("h04","brick",6),("h05","wool",4),
 ("h06","brick",10),("h07","grain",9),("h08","wood",11),
 ("h09","desert",None),("h10","wood",3),("h11","ore",8),
 ("h12","wood",8),("h13","ore",3),("h14","grain",4),
 ("h15","wool",5),("h16","brick",5),("h17","grain",6),
 ("h18","wool",11))

VERTEX_HEXES = {
"v00":["h00"],"v01":["h01"],"v02":["h02"],"v03":["h00"],
"v04":["h00","h01"],"v05":["h01","h02"],"v06":["h02"],
"v07":["h00","h03"],"v08":["h00","h01","h04"],"v09":["h01","h02","h05"],
"v10":["h02","h06"],"v11":["h03"],"v12":["h00","h03","h04"],
"v13":["h01","h04","h05"],"v14":["h02","h05","h06"],"v15":["h06"],
"v16":["h03","h07"],"v17":["h03","h04","h08"],"v18":["h04","h05","h09"],
"v19":["h05","h06","h10"],"v20":["h06","h11"],"v21":["h07"],
"v22":["h03","h07","h08"],"v23":["h04","h08","h09"],
"v24":["h05","h09","h10"],"v25":["h06","h10","h11"],"v26":["h11"],
"v27":["h07"],"v28":["h07","h08","h12"],"v29":["h08","h09","h13"],
"v30":["h09","h10","h14"],"v31":["h10","h11","h15"],"v32":["h11"],
"v33":["h07","h12"],"v34":["h08","h12","h13"],"v35":["h09","h13","h14"],
"v36":["h10","h14","h15"],"v37":["h11","h15"],"v38":["h12"],
"v39":["h12","h13","h16"],"v40":["h13","h14","h17"],
"v41":["h14","h15","h18"],"v42":["h15"],"v43":["h12","h16"],
"v44":["h13","h16","h17"],"v45":["h14","h17","h18"],
"v46":["h15","h18"],"v47":["h16"],"v48":["h16","h17"],
"v49":["h17","h18"],"v50":["h18"],"v51":["h16"],"v52":["h17"],"v53":["h18"]}

EDGE_IDS = """e_v00_v03 e_v00_v04 e_v01_v04 e_v01_v05 e_v02_v05 e_v02_v06
e_v03_v07 e_v04_v08 e_v05_v09 e_v06_v10 e_v07_v11 e_v07_v12 e_v08_v12
e_v08_v13 e_v09_v13 e_v09_v14 e_v10_v14 e_v10_v15 e_v11_v16 e_v12_v17
e_v13_v18 e_v14_v19 e_v15_v20 e_v16_v21 e_v16_v22 e_v17_v22 e_v17_v23
e_v18_v23 e_v18_v24 e_v19_v24 e_v19_v25 e_v20_v25 e_v20_v26 e_v21_v27
e_v22_v28 e_v23_v29 e_v24_v30 e_v25_v31 e_v26_v32 e_v27_v33 e_v28_v33
e_v28_v34 e_v29_v34 e_v29_v35 e_v30_v35 e_v30_v36 e_v31_v36 e_v31_v37
e_v32_v37 e_v33_v38 e_v34_v39 e_v35_v40 e_v36_v41 e_v37_v42 e_v38_v43
e_v39_v43 e_v39_v44 e_v40_v44 e_v40_v45 e_v41_v45 e_v41_v46 e_v42_v46
e_v43_v47 e_v44_v48 e_v45_v49 e_v46_v50 e_v47_v51 e_v48_v51 e_v48_v52
e_v49_v52 e_v49_v53 e_v50_v53""".split()

HARBORS = (
 ("p00",2,"grain",("v01","v05")),("p01",2,"wood",("v10","v15")),
 ("p02",3,None,("v26","v32")),("p03",2,"wool",("v46","v50")),
 ("p04",3,None,("v49","v52")),("p05",3,None,("v47","v51")),
 ("p06",2,"brick",("v27","v33")),("p07",2,"ore",("v11","v16")),
 ("p08",3,None,("v00","v03")))

SETUP = {
3: {
"settlements":((0,"v39"),(0,"v41"),(1,"v14"),(1,"v40"),(2,"v17"),(2,"v31")),
"roads":((0,"e_v39_v44"),(0,"e_v36_v41"),(1,"e_v09_v14"),
 (1,"e_v40_v45"),(2,"e_v17_v22"),(2,"e_v25_v31")),
"resources":((1,1,0,0,1),(0,0,0,2,1),(1,0,1,0,1))},
4: {
"settlements":((0,"v08"),(0,"v28"),(1,"v39"),(1,"v41"),(2,"v14"),
 (2,"v40"),(3,"v17"),(3,"v31")),
"roads":((0,"e_v08_v13"),(0,"e_v28_v34"),(1,"e_v39_v44"),
 (1,"e_v36_v41"),(2,"e_v09_v14"),(2,"e_v40_v45"),
 (3,"e_v17_v22"),(3,"e_v25_v31")),
"resources":((2,0,0,1,0),(1,1,0,0,1),(0,0,0,2,1),(1,0,1,0,1))}
}

DEV_INVENTORY = (["knight"]*14 + ["road_building"]*2 +
 ["year_of_plenty"]*2 + ["monopoly"]*2 +
 ["library","marketplace","city_hall","chapel","university"])
COSTS = {"road":{"wood":1,"brick":1}, "settlement":{"wood":1,"brick":1,"wool":1,"grain":1},
         "city":{"ore":3,"grain":2}, "development":{"ore":1,"wool":1,"grain":1}}

def counts(values=None):
    d = {r: 0 for r in RESOURCES}
    if values:
        d.update(values)
    return d

def edge_vertices(e):
    p = e.split("_")
    return p[1], p[2]

def adjacent_vertices(v):
    out = set()
    for e in EDGE_IDS:
        a,b=edge_vertices(e)
        if a==v: out.add(b)
        elif b==v: out.add(a)
    return out

class Action:
    def __init__(self, type: str, actor: int, args: dict[str, Any]):
        self.type, self.actor, self.args = type, actor, args
    def __eq__(self, other):
        return isinstance(other, Action) and (self.type,self.actor,self.args)==(other.type,other.actor,other.args)
    def __repr__(self):
        return f"Action({self.type!r}, {self.actor!r}, {self.args!r})"

class GameState:
    def __init__(self, data: dict[str, Any]):
        self.data = data

class Game:
    def __init__(self, num_players=None, seed=None):
        self.num_players = 4 if num_players is None else num_players
        if self.num_players not in (3,4):
            raise ValueError("supplied rules support 3 or 4 players")
        if seed is not None and (not isinstance(seed,int) or isinstance(seed,bool)):
            raise ValueError("seed must be int or None")
        self.seed = seed

    def initial_state(self):
        n=self.num_players; cfg=SETUP[n]
        rng=random.Random(self.seed)
        deck=list(DEV_INVENTORY); rng.shuffle(deck)
        players=[]
        for i in range(n):
            players.append({"id":i,"color":COLORS[n][i],
              "resources":dict(zip(RESOURCES,cfg["resources"][i])),
              "development_hand":[],"played_knights":0,
              "pieces":{"roads":13,"settlements":3,"cities":4}})
        verts=[]
        harbor_at={v:[] for v in VERTEX_HEXES}
        for pid,_,_,vs in HARBORS:
            for v in vs: harbor_at[v].append(pid)
        buildings={v:{"owner":p,"type":"settlement"} for p,v in cfg["settlements"]}
        roadmap={e:p for p,e in cfg["roads"]}
        bank=counts({r:19-sum(p["resources"][r] for p in players) for r in RESOURCES})
        data={"configuration":{"players":n,"seed":self.seed,"oldest_player":0,
              "setup":"beginner_illustrated"},
          "current_player":0,"active_player":0,"phase":"roll",
          "turn":{"number":1,"development_played":False,"last_roll":None},
          "terminal":False,"winner":None,"players":players,
          "board":{"hexes":[{"id":h,"terrain":t,"number":num,"robber":h=="h09"}
                    for h,t,num in HEXES],
            "vertices":[{"id":v,"building":buildings.get(v),"harbor_ids":harbor_at[v]}
                        for v in VERTEX_HEXES],
            "edges":[{"id":e,"vertices":list(edge_vertices(e)),
                      "road_owner":roadmap.get(e)} for e in EDGE_IDS],
            "harbors":[{"id":p,"ratio":ratio,"resource":r,"vertices":list(vs)}
                       for p,ratio,r,vs in HARBORS]},
          "bank":{"resources":bank,"development_deck":deck,"played_development":[]},
          "special_cards":{"longest_road_owner":None,"longest_road_length":0,
                           "largest_army_owner":None},
          "pending":[],"chance":{"rng_state":self._seed_value(),
                                "scripted_rolls":[],"scripted_steals":[]},
          "zones":{"reserve":{"resources":counts(),"development_cards":[],
                             "removed_colors":[]}}}
        return GameState(data)

    def _seed_value(self):
        # Stable integer-only generator state, including for seed=None.
        return (self.seed if self.seed is not None else 0) & ((1<<63)-1)

    def _rand(self,s,limit):
        x=s.data["chance"]["rng_state"]
        x=(6364136223846793005*x+1442695040888963407)&((1<<64)-1)
        s.data["chance"]["rng_state"]=x
        return x%limit

    def current_player(self,state):
        return state.data["current_player"]

    def is_terminal(self,state):
        return state.data["terminal"]

    def _player(self,s,p=None):
        return s.data["players"][s.data["active_player"] if p is None else p]

    def _building(self,s,v):
        return next(x["building"] for x in s.data["board"]["vertices"] if x["id"]==v)

    def _road_owner(self,s,e):
        return next(x["road_owner"] for x in s.data["board"]["edges"] if x["id"]==e)

    def _can_pay(self,p,cost):
        return all(p["resources"][r]>=n for r,n in cost.items())

    def _pay(self,s,p,cost):
        for r,n in cost.items():
            p["resources"][r]-=n; s.data["bank"]["resources"][r]+=n

    def _connected_road(self,s,pid,e):
        a,b=edge_vertices(e)
        for v in (a,b):
            building=self._building(s,v)
            if building and building["owner"]==pid: return True
            if building and building["owner"]!=pid: continue
            for other in EDGE_IDS:
                if other!=e and v in edge_vertices(other) and self._road_owner(s,other)==pid:
                    return True
        return False

    def _legal_road_edges(self,s,pid):
        if self._player(s,pid)["pieces"]["roads"]<=0: return []
        return [e for e in EDGE_IDS if self._road_owner(s,e) is None
                and self._connected_road(s,pid,e)]

    def _legal_settlement_vertices(self,s,pid):
        if self._player(s,pid)["pieces"]["settlements"]<=0:return []
        own_edges={e for e in EDGE_IDS if self._road_owner(s,e)==pid}
        out=[]
        for v in VERTEX_HEXES:
            if self._building(s,v) is not None: continue
            if any(self._building(s,n) is not None for n in adjacent_vertices(v)):continue
            if any(v in edge_vertices(e) for e in own_edges):out.append(v)
        return out

    def _eligible_devs(self,s):
        p=self._player(s)
        if s.data["turn"]["development_played"]:return []
        return [c["id"] for c in p["development_hand"]
                if not c["revealed"] and c["bought_turn"]<s.data["turn"]["number"]
                and c["id"] not in VP_DEVS]

    def _dev_actions(self,s):
        pid=s.data["active_player"]; acts=[]
        for d in sorted(set(self._eligible_devs(s))):
            if d=="knight": acts.append(Action("play_knight",pid,{"card":"knight"}))
            elif d=="road_building":
                if self._player(s)["pieces"]["roads"] and self._legal_road_edges(s,pid):
                    acts.append(Action("play_road_building",pid,{"card":"road_building"}))
            elif d=="year_of_plenty":
                bank=s.data["bank"]["resources"]
                for a in RESOURCES:
                    for b in RESOURCES:
                        need=2 if a==b else 1
                        if bank[a]>=need and (a==b or bank[b]>=1):
                            acts.append(Action("play_year_of_plenty",pid,
                                               {"card":d,"resources":[a,b]}))
            elif d=="monopoly":
                acts += [Action("play_monopoly",pid,{"card":d,"resource":r})
                         for r in RESOURCES]
        return acts

    def legal_actions(self,state):
        s=state
        if s.data["terminal"]: return []
        phase=s.data["phase"]; actor=s.data["current_player"]; p=self._player(s,actor)
        acts=[]
        # Almanac permits the active player to play a development card at any
        # time in their turn, including before rolling; pending stack resumes.
        if actor==s.data["active_player"] or phase in ("discard","trade_offer"):
            acts += self._dev_actions(s)
        top=s.data["pending"][-1] if s.data["pending"] else None
        if phase=="roll": acts.append(Action("roll_dice",actor,{}))
        elif phase=="discard" and top:
            req=top["required"].get(str(actor),0); sel=top["selected"].get(str(actor),counts())
            for r in RESOURCES:
                if p["resources"][r]>sel[r]:acts.append(Action("choose_discard_resource",actor,{"resource":r}))
                if sel[r]>0:acts.append(Action("undo_discard_resource",actor,{"resource":r}))
            if sum(sel.values())==req:acts.append(Action("submit_discard",actor,{}))
        elif phase=="robber_move":
            current=next(h["id"] for h in s.data["board"]["hexes"] if h["robber"])
            acts += [Action("move_robber",actor,{"hex":h["id"]})
                     for h in s.data["board"]["hexes"] if h["id"]!=current]
        elif phase=="robber_steal" and top:
            acts += [Action("steal_resource",actor,{"victim":v}) for v in top["victims"]]
            if not acts:self._finish_pending(s)
        elif phase=="trade":
            for partner in range(len(s.data["players"])):
                if partner!=actor:acts.append(Action("begin_domestic_trade",actor,{"partner":partner}))
            ratios=self._trade_ratios(s,actor)
            for give in RESOURCES:
                if p["resources"][give]>=ratios[give]:
                    acts += [Action("maritime_trade",actor,{"give":give,"receive":r})
                             for r in RESOURCES if r!=give and s.data["bank"]["resources"][r]>0]
            acts.append(Action("end_trade",actor,{}))
        elif phase=="trade_offer" and top:
            if top["status"]=="building":
                for direction in ("give","take"):
                    owner=actor if direction=="give" else top["partner"]
                    bundle=top[direction]
                    for r in RESOURCES:
                        if self._player(s,owner)["resources"][r]>bundle[r]:
                            acts.append(Action("add_trade_item",actor,{"direction":direction,"resource":r}))
                if sum(top["give"].values()) and sum(top["take"].values()):
                    acts.append(Action("propose_domestic_trade",actor,{}))
                acts.append(Action("cancel_domestic_trade",actor,{}))
            else:
                acts += [Action("accept_domestic_trade",actor,{}),
                         Action("reject_domestic_trade",actor,{})]
        elif phase=="build":
            ap=self._player(s); pid=s.data["active_player"]
            if self._can_pay(ap,COSTS["road"]):
                acts += [Action("build_road",pid,{"edge":e}) for e in self._legal_road_edges(s,pid)]
            if self._can_pay(ap,COSTS["settlement"]):
                acts += [Action("build_settlement",pid,{"vertex":v})
                         for v in self._legal_settlement_vertices(s,pid)]
            if self._can_pay(ap,COSTS["city"]) and ap["pieces"]["cities"]>0:
                acts += [Action("build_city",pid,{"vertex":v["id"]})
                         for v in s.data["board"]["vertices"]
                         if v["building"]=={"owner":pid,"type":"settlement"}]
            if self._can_pay(ap,COSTS["development"]) and s.data["bank"]["development_deck"]:
                acts.append(Action("buy_development",pid,{}))
            acts.append(Action("end_turn",pid,{}))
        elif phase=="road_building":
            acts += [Action("place_free_road",actor,{"edge":e})
                     for e in self._legal_road_edges(s,actor)]
            if not acts:self._finish_pending(s)
        return acts

    def _trade_ratios(self,s,pid):
        ratios={r:4 for r in RESOURCES}
        owned={v["id"] for v in s.data["board"]["vertices"]
               if v["building"] and v["building"]["owner"]==pid}
        for h in s.data["board"]["harbors"]:
            if owned.intersection(h["vertices"]):
                if h["resource"] is None:
                    for r in RESOURCES:ratios[r]=min(ratios[r],3)
                else:ratios[h["resource"]]=2
        return ratios

    def apply_action(self,state,action):
        legal=self.legal_actions(state)
        if action not in legal: raise ValueError("illegal action")
        s=copy.deepcopy(state); a=action; d=s.data; p=self._player(s,a.actor)
        t=a.type
        if t=="roll_dice":
            if d["chance"]["scripted_rolls"]: dice=d["chance"]["scripted_rolls"].pop(0)
            else:dice=[self._rand(s,6)+1,self._rand(s,6)+1]
            d["turn"]["last_roll"]=dice
            if sum(dice)==7:self._start_seven(s)
            else:self._produce(s,sum(dice)); d["phase"]="trade"
        elif t in ("choose_discard_resource","undo_discard_resource"):
            top=d["pending"][-1]; sel=top["selected"].setdefault(str(a.actor),counts())
            sel[a.args["resource"]] += 1 if t.startswith("choose") else -1
        elif t=="submit_discard": self._submit_discard(s,a.actor)
        elif t=="move_robber": self._move_robber(s,a.args["hex"])
        elif t=="steal_resource": self._steal(s,a.args["victim"]); self._finish_pending(s)
        elif t=="begin_domestic_trade":
            frame={"type":"trade_offer","partner":a.args["partner"],"give":counts(),
                   "take":counts(),"status":"building","resume_phase":"trade",
                   "resume_current_player":a.actor}
            d["pending"].append(frame);d["phase"]="trade_offer"
        elif t=="add_trade_item":
            d["pending"][-1][a.args["direction"]][a.args["resource"]]+=1
        elif t=="propose_domestic_trade":
            d["pending"][-1]["status"]="awaiting_response"
            d["current_player"]=d["pending"][-1]["partner"]
        elif t=="accept_domestic_trade":
            f=d["pending"][-1]; ap=self._player(s,d["active_player"]); q=self._player(s,f["partner"])
            for r in RESOURCES:
                ap["resources"][r]+=f["take"][r]-f["give"][r]
                q["resources"][r]+=f["give"][r]-f["take"][r]
            self._finish_pending(s)
        elif t in ("reject_domestic_trade","cancel_domestic_trade"):self._finish_pending(s)
        elif t=="maritime_trade":
            ratios=self._trade_ratios(s,a.actor); g=a.args["give"];r=a.args["receive"]
            p["resources"][g]-=ratios[g];d["bank"]["resources"][g]+=ratios[g]
            d["bank"]["resources"][r]-=1;p["resources"][r]+=1
        elif t=="end_trade":d["phase"]="build"
        elif t=="build_road":self._pay(s,p,COSTS["road"]);self._place_road(s,a.actor,a.args["edge"])
        elif t=="build_settlement":
            self._pay(s,p,COSTS["settlement"]);self._place_building(s,a.actor,a.args["vertex"],"settlement")
        elif t=="build_city":
            self._pay(s,p,COSTS["city"]);p["pieces"]["settlements"]+=1;p["pieces"]["cities"]-=1
            self._set_building(s,a.args["vertex"],{"owner":a.actor,"type":"city"})
        elif t=="buy_development":
            self._pay(s,p,COSTS["development"]); card=d["bank"]["development_deck"].pop()
            p["development_hand"].append({"id":card,"bought_turn":d["turn"]["number"],"revealed":False})
        elif t.startswith("play_"):
            self._play_development(s,a)
        elif t=="place_free_road":
            self._place_road(s,a.actor,a.args["edge"]);f=d["pending"][-1];f["remaining"]-=1
            if f["remaining"]==0 or not self._legal_road_edges(s,a.actor):self._finish_pending(s)
        elif t=="end_turn":
            nxt=(d["active_player"]+1)%len(d["players"]);d["active_player"]=nxt
            d["current_player"]=nxt;d["phase"]="roll";d["turn"]={"number":d["turn"]["number"]+1,
             "development_played":False,"last_roll":None}
        self._recalculate_specials(s);self._check_victory(s)
        return s

    def _produce(self,s,total):
        claims={r:[0]*len(s.data["players"]) for r in RESOURCES}
        for h in s.data["board"]["hexes"]:
            if h["number"]!=total or h["robber"] or h["terrain"]=="desert":continue
            for v in s.data["board"]["vertices"]:
                if h["id"] in VERTEX_HEXES[v["id"]] and v["building"]:
                    claims[h["terrain"]][v["building"]["owner"]]+=1 if v["building"]["type"]=="settlement" else 2
        for r,amounts in claims.items():
            if sum(amounts)<=s.data["bank"]["resources"][r]:
                for i,n in enumerate(amounts):
                    s.data["players"][i]["resources"][r]+=n;s.data["bank"]["resources"][r]-=n

    def _start_seven(self,s):
        required={str(p["id"]):sum(p["resources"].values())//2 for p in s.data["players"]
                  if sum(p["resources"].values())>7}
        if required:
            f={"type":"discard","required":required,"selected":{},"submitted_players":[],
               "resume_phase":"robber_move","resume_current_player":s.data["active_player"]}
            s.data["pending"].append(f);s.data["phase"]="discard"
            s.data["current_player"]=min(map(int,required))
        else:self._push_robber(s,"seven","trade")

    def _submit_discard(self,s,pid):
        f=s.data["pending"][-1];f["submitted_players"].append(pid)
        remaining=[int(x) for x in f["required"] if int(x) not in f["submitted_players"]]
        if remaining:s.data["current_player"]=min(remaining);return
        for key,sel in f["selected"].items():
            p=self._player(s,int(key))
            for r,n in sel.items():p["resources"][r]-=n;s.data["bank"]["resources"][r]+=n
        s.data["pending"].pop();self._push_robber(s,"seven","trade")

    def _push_robber(self,s,source,resume):
        s.data["pending"].append({"type":"robber_move","resume_phase":resume,
          "resume_current_player":s.data["active_player"],"source":source})
        s.data["phase"]="robber_move";s.data["current_player"]=s.data["active_player"]

    def _move_robber(self,s,hid):
        for h in s.data["board"]["hexes"]:h["robber"]=h["id"]==hid
        f=s.data["pending"].pop(); victims=sorted({v["building"]["owner"]
          for v in s.data["board"]["vertices"] if hid in VERTEX_HEXES[v["id"]]
          and v["building"] and v["building"]["owner"]!=s.data["active_player"]})
        if victims:
            s.data["pending"].append({"type":"robber_steal","resume_phase":f["resume_phase"],
              "resume_current_player":f["resume_current_player"],"victims":victims,"source":f["source"]})
            s.data["phase"]="robber_steal"
        else:
            s.data["phase"]=f["resume_phase"];s.data["current_player"]=f["resume_current_player"]

    def _steal(self,s,victim):
        q=self._player(s,victim); pool=[r for r in RESOURCES for _ in range(q["resources"][r])]
        if not pool:return
        scripted=s.data["chance"]["scripted_steals"]
        r=scripted.pop(0) if scripted else pool[self._rand(s,len(pool))]
        if q["resources"][r]<=0:raise ValueError("scripted stolen resource unavailable")
        q["resources"][r]-=1;self._player(s)["resources"][r]+=1

    def _finish_pending(self,s):
        if not s.data["pending"]:return
        f=s.data["pending"].pop();s.data["phase"]=f["resume_phase"]
        s.data["current_player"]=f["resume_current_player"]

    def _place_road(self,s,pid,e):
        for x in s.data["board"]["edges"]:
            if x["id"]==e:x["road_owner"]=pid;break
        self._player(s,pid)["pieces"]["roads"]-=1

    def _set_building(self,s,v,b):
        for x in s.data["board"]["vertices"]:
            if x["id"]==v:x["building"]=b;return

    def _place_building(self,s,pid,v,kind):
        self._set_building(s,v,{"owner":pid,"type":kind})
        self._player(s,pid)["pieces"]["settlements"]-=1

    def _play_development(self,s,a):
        p=self._player(s); d=a.type.removeprefix("play_")
        card=next(c for c in p["development_hand"] if c["id"]==d and not c["revealed"]
                  and c["bought_turn"]<s.data["turn"]["number"])
        card["revealed"]=True;s.data["turn"]["development_played"]=True
        s.data["bank"]["played_development"].append({"owner":a.actor,"id":d})
        if d=="knight":
            p["played_knights"]+=1;self._push_robber(s,"knight",s.data["phase"])
        elif d=="road_building":
            s.data["pending"].append({"type":"road_building","resume_phase":s.data["phase"],
              "resume_current_player":s.data["current_player"],"remaining":min(2,p["pieces"]["roads"])})
            s.data["phase"]="road_building";s.data["current_player"]=a.actor
        elif d=="year_of_plenty":
            for r in a.args["resources"]:s.data["bank"]["resources"][r]-=1;p["resources"][r]+=1
        elif d=="monopoly":
            r=a.args["resource"]
            for q in s.data["players"]:
                if q["id"]!=a.actor:p["resources"][r]+=q["resources"][r];q["resources"][r]=0

    def _longest(self,s,pid):
        owned={e for e in EDGE_IDS if self._road_owner(s,e)==pid}
        blocked={v["id"] for v in s.data["board"]["vertices"] if v["building"]
                 and v["building"]["owner"]!=pid}
        best=0
        def walk(v,used):
            nonlocal best;best=max(best,len(used))
            if used and v in blocked:return
            for e in owned-used:
                a,b=edge_vertices(e)
                if v==a:walk(b,used|{e})
                elif v==b:walk(a,used|{e})
        for e in owned:
            a,b=edge_vertices(e);walk(a,set());walk(b,set())
        return best

    def _recalculate_specials(self,s):
        sc=s.data["special_cards"]; lengths=[self._longest(s,i) for i in range(len(s.data["players"]))]
        old=sc["longest_road_owner"]; m=max(lengths,default=0); leaders=[i for i,x in enumerate(lengths) if x==m]
        if m<5:new=None
        elif old in leaders:new=old
        elif len(leaders)==1:new=leaders[0]
        else:new=None
        sc["longest_road_owner"]=new;sc["longest_road_length"]=m
        armies=[p["played_knights"] for p in s.data["players"]];am=max(armies,default=0)
        leaders=[i for i,x in enumerate(armies) if x==am]
        old=sc["largest_army_owner"]
        if am<3:new=None
        elif old in leaders:new=old
        elif len(leaders)==1:new=leaders[0]
        else:new=None
        sc["largest_army_owner"]=new

    def _score(self,s,pid,hidden=True):
        score=0
        for v in s.data["board"]["vertices"]:
            if v["building"] and v["building"]["owner"]==pid:
                score+=1 if v["building"]["type"]=="settlement" else 2
        if s.data["special_cards"]["longest_road_owner"]==pid:score+=2
        if s.data["special_cards"]["largest_army_owner"]==pid:score+=2
        if hidden:score+=sum(c["id"] in VP_DEVS for c in self._player(s,pid)["development_hand"])
        else:score+=sum(c["id"] in VP_DEVS and c["revealed"] for c in self._player(s,pid)["development_hand"])
        return score

    def _check_victory(self,s):
        pid=s.data["active_player"]
        if self._score(s,pid)>=10:
            need=10-self._score(s,pid,False)
            for c in self._player(s,pid)["development_hand"]:
                if need<=0:break
                if c["id"] in VP_DEVS and not c["revealed"]:c["revealed"]=True;need-=1
            s.data["terminal"]=True;s.data["winner"]=pid;s.data["phase"]="terminal"
            s.data["pending"]=[];s.data["current_player"]=pid

    def returns(self,state):
        n=len(state.data["players"])
        if not state.data["terminal"]:return [0.0]*n
        return [1.0 if i==state.data["winner"] else -1.0 for i in range(n)]

    def action_to_name(self,a):
        labels={"roll_dice":"Würfeln","end_trade":"Handel beenden",
                "end_turn":"Zug beenden","buy_development":"Entwicklungskarte kaufen"}
        base=labels.get(a.type,a.type.replace("_"," ").title())
        suffix=", ".join(f"{k}={json.dumps(v,separators=(',',':'))}" for k,v in sorted(a.args.items()))
        return f"{base} [Spieler {a.actor}]" + (f": {suffix}" if suffix else "")

    def name_to_action(self,name):
        # Names are deliberately a presentation of canonical actions; search the
        # finite action vocabulary and parse the stable suffix.
        import re
        m=re.fullmatch(r"(.+) \[Spieler ([0-9]+)\](?:: (.*))?",name)
        if not m:raise ValueError("invalid action name")
        label,actor,tail=m.groups();rev={"Würfeln":"roll_dice","Handel beenden":"end_trade",
          "Zug beenden":"end_turn","Entwicklungskarte kaufen":"buy_development"}
        typ=rev.get(label,label.lower().replace(" ","_"))
        if typ not in ACTION_TYPES:raise ValueError("unknown action name")
        args={}
        if tail:
            # Values contain no commas except the only list argument; split keys
            # with a tiny JSON decoder rather than ambiguous string splitting.
            dec=json.JSONDecoder();pos=0
            while pos<len(tail):
                eq=tail.index("=",pos);key=tail[pos:eq];val,end=dec.raw_decode(tail,eq+1)
                args[key]=val;pos=end+2
        return Action(typ,int(actor),args)

    def action_to_data(self,a):
        return {"schema":ACTION_SCHEMA,"data":{"type":a.type,"actor":a.actor,
                                               "args":copy.deepcopy(a.args)}}

    def action_from_data(self,payload):
        self._envelope(payload,ACTION_SCHEMA)
        d=payload["data"]
        if set(d)!={"type","actor","args"} or d["type"] not in ACTION_TYPES:
            raise ValueError("invalid action payload")
        if not isinstance(d["actor"],int) or isinstance(d["actor"],bool) or not isinstance(d["args"],dict):
            raise ValueError("invalid action fields")
        return Action(d["type"],d["actor"],copy.deepcopy(d["args"]))

    def state_to_data(self,state):
        return {"schema":STATE_SCHEMA,"data":copy.deepcopy(state.data)}

    def state_from_data(self,payload):
        self._envelope(payload,STATE_SCHEMA);d=payload["data"]
        required={"configuration","current_player","active_player","phase","turn","terminal",
          "winner","players","board","bank","special_cards","pending","chance","zones"}
        if set(d)!=required or not isinstance(d["players"],list) or d["phase"] not in PHASES:
            raise ValueError("invalid state payload")
        n=d["configuration"].get("players")
        if n not in (3,4) or len(d["players"])!=n:raise ValueError("invalid player count")
        return GameState(copy.deepcopy(d))

    def _envelope(self,p,schema):
        if not isinstance(p,dict) or set(p)!={"schema","data"} or p["schema"]!=schema or not isinstance(p["data"],dict):
            raise ValueError("invalid canonical envelope")

    def observation_to_data(self,state,player):
        d=state.data
        if not isinstance(player,int) or player<0 or player>=len(d["players"]):raise ValueError("invalid player")
        me=d["players"][player]
        pending=copy.deepcopy(d["pending"])
        for f in pending:
            if f["type"]=="discard":f.pop("selected",None)
        data={"player":player,"current_player":d["current_player"],"active_player":d["active_player"],
          "phase":d["phase"],"turn":copy.deepcopy(d["turn"]),"terminal":d["terminal"],
          "winner":d["winner"],"own_resources":copy.deepcopy(me["resources"]),
          "own_development":copy.deepcopy(me["development_hand"]),
          "opponents":[{"id":p["id"],"resource_count":sum(p["resources"].values()),
             "development_count":sum(not c["revealed"] for c in p["development_hand"]),
             "played_knights":p["played_knights"]} for p in d["players"] if p["id"]!=player],
          "board":copy.deepcopy(d["board"]),
          "bank":{"resources":copy.deepcopy(d["bank"]["resources"]),
             "development_deck_size":len(d["bank"]["development_deck"]),
             "played_development":copy.deepcopy(d["bank"]["played_development"])},
          "visible_scores":[self._score(state,i,False) for i in range(len(d["players"]))],
          "special_cards":copy.deepcopy(d["special_cards"]),"pending":pending}
        return {"schema":OBS_SCHEMA,"data":data}

    def render(self,state):
        d=state.data
        scores=", ".join(f"{p['color']}={self._score(state,p['id'],False)}"
                         for p in d["players"])
        return f"CATAN turn {d['turn']['number']} phase={d['phase']} player={d['current_player']} scores: {scores}"
