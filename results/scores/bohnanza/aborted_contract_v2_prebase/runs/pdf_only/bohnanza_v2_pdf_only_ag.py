"""Bohnanza base game, 4--5 player source condition."""
from dataclasses import dataclass
import copy, json, random

BEANS = ("blaue_bohne","feuerbohne","saubohne","brechbohne","sojabohne","augenbohne","rote_bohne","gartenbohne")
COUNTS = dict(zip(BEANS, (20,18,16,14,12,10,8,6)))
# Number of beans required for 1, 2, 3, 4 coins; a missing tier is impossible.
METERS = {
 "blaue_bohne":(4,6,8,10), "feuerbohne":(3,6,8,9),
 "saubohne":(3,5,7,8), "brechbohne":(3,5,6,7),
 "sojabohne":(2,4,6,7), "augenbohne":(2,4,5,6),
 "rote_bohne":(2,3,4,5), "gartenbohne":(2,3,None,None),
}
PHASES={"plant_first","plant_second","reveal","trade","trade_response","plant_received","draw","terminal"}
TYPES={"plant","harvest","reveal","trade_start","trade_add_offer_card","trade_add_request_card","trade_submit","trade_accept","trade_reject","gift_propose","gift_accept","gift_reject","end_trade","draw","pass","reorder_hand"}

@dataclass(frozen=True)
class Action:
    type: str
    actor: int
    args: tuple = ()

    @staticmethod
    def make(kind, actor, **args):
        return Action(kind, actor, tuple(sorted(args.items())))
    def argdict(self): return dict(self.args)

@dataclass
class GameState:
    configuration: dict; current_player: int; active_player: int; start_player: int
    phase: str; terminal: bool; players: list; zones: dict; depletions: int
    pending: dict|None; chance: dict

class Game:
    def __init__(self, num_players=None, seed=None):
        self.num_players = 4 if num_players is None else num_players
        if type(self.num_players) is not int or self.num_players not in (4,5): raise ValueError("base condition requires 4 or 5 players")
        if seed is not None and type(seed) is not int: raise TypeError("seed must be int or None")
        self.seed=seed

    def initial_state(self):
        deck=[b for b in BEANS for _ in range(COUNTS[b])]
        random.Random(self.seed).shuffle(deck)
        players=[]
        for p in range(self.num_players):
            hand=[deck.pop() for _ in range(5)]
            players.append({"id":p,"hand":hand,"fields":[[],[],[]],"coins":0,"third_field":True,"alive":True})
        return GameState({"players":self.num_players,"seed":self.seed},0,0,0,"plant_first",False,players,
          {"deck":deck,"discard":[],"revealed":[],"pending_received":[[] for _ in players],"reserve":[]},0,None,
          {"seed":self.seed,"draw_index":5*self.num_players})

    def current_player(self,s): return s.current_player
    def is_terminal(self,s): return s.terminal
    def returns(self,s):
        if not s.terminal:return [0.0]*len(s.players)
        scores=[p["coins"] for p in s.players]; best=max(scores)
        # Tie: later clockwise from start player wins.
        winner=max((i for i,x in enumerate(scores) if x==best), key=lambda i:(i-s.start_player)%len(scores))
        return [1.0 if i==winner else 0.0 for i in range(len(scores))]

    def _harvest_actions(self,s,p):
        out=[]
        nonempty=[i for i,f in enumerate(s.players[p]["fields"]) if f]
        multi=any(len(s.players[p]["fields"][i])>1 for i in nonempty)
        for i in nonempty:
            if len(s.players[p]["fields"][i])>1 or not multi:
                out.append(Action.make("harvest",p,field=i))
        return out

    def _plant_actions(self,s,p,bean,source,index):
        out=[]
        for i,f in enumerate(s.players[p]["fields"]):
            if not f or f[0]==bean: out.append(Action.make("plant",p,source=source,index=index,field=i))
        return out

    def legal_actions(self,s):
        if s.terminal:return []
        p=s.current_player; phase=s.phase; out=[]
        # Harvesting is an interrupt explicitly allowed even on another player's turn.
        for q in range(len(s.players)): out += self._harvest_actions(s,q)
        if phase in ("plant_first","plant_second"):
            h=s.players[p]["hand"]
            if h: out += self._plant_actions(s,p,h[0],"hand",0)
            else: out.append(Action.make("pass",p))
            if phase=="plant_second": out.append(Action.make("pass",p))
        elif phase=="reveal": out.append(Action.make("reveal",p))
        elif phase=="trade":
            # Begin a proposal with any other player, or finish negotiation.
            if s.pending is None:
                for q in range(len(s.players)):
                    if q!=p: out.append(Action.make("trade_start",p,partner=q))
                out.append(Action.make("end_trade",p))
            else:
                pend=s.pending; q=pend["partner"]
                used={(x["zone"],x["index"]) for x in pend["offered"]}
                for z,cards in (("hand",s.players[p]["hand"]),("revealed",s.zones["revealed"])):
                    for i,b in enumerate(cards):
                        if (z,i) not in used: out.append(Action.make("trade_add_offer_card",p,zone=z,index=i))
                usedq={x["index"] for x in pend["requested"]}
                for i,b in enumerate(s.players[q]["hand"]):
                    if i not in usedq: out.append(Action.make("trade_add_request_card",p,index=i))
                if pend["offered"] or pend["requested"]: out.append(Action.make("trade_submit",p))
                out.append(Action.make("trade_reject",p)) # cancel unsubmitted proposal
        elif phase=="trade_response":
            out += [Action.make("trade_accept",p),Action.make("trade_reject",p)]
        elif phase=="plant_received":
            cards=s.zones["pending_received"][p]
            if cards: out += self._plant_actions(s,p,cards[0],"received",0)
            else: out.append(Action.make("pass",p))
        elif phase=="draw": out.append(Action.make("draw",p))
        # De-duplicate (harvest plus phase actions cannot collide, but keep invariant explicit).
        return list(dict.fromkeys(out))

    def _coins(self,bean,n):
        return sum(t is not None and n>=t for t in METERS[bean])
    def _reshuffle_or_end(self,s):
        if s.zones["deck"]: return
        s.depletions += 1
        if s.depletions>=3:
            # During phase 2 the source requires phases 2 and 3 to be completed.
            if s.phase != "reveal": s.terminal=True;s.phase="terminal"
            return
        s.zones["deck"]=s.zones["discard"][:];s.zones["discard"].clear()
        random.Random((s.chance["seed"],s.depletions).__repr__()).shuffle(s.zones["deck"])
    def _draw_one(self,s):
        self._reshuffle_or_end(s)
        if s.terminal or not s.zones["deck"]:return None
        s.chance["draw_index"]+=1
        return s.zones["deck"].pop()

    def apply_action(self,state,action):
        s=copy.deepcopy(state)
        if action not in self.legal_actions(s): raise ValueError("illegal action")
        a=action.argdict(); p=action.actor
        if action.type=="harvest":
            f=s.players[p]["fields"][a["field"]]; bean=f[0]; coins=self._coins(bean,len(f))
            s.players[p]["coins"]+=coins; s.zones["reserve"].extend(f[:coins]); s.zones["discard"].extend(f[coins:]); f.clear()
        elif action.type=="plant":
            if a["source"]=="hand": bean=s.players[p]["hand"].pop(0)
            elif a["source"]=="received": bean=s.zones["pending_received"][p].pop(0)
            else: bean=s.zones["revealed"].pop(a["index"])
            s.players[p]["fields"][a["field"]].append(bean)
            if s.phase=="plant_first": s.phase="plant_second"
        elif action.type=="pass":
            if s.phase in ("plant_first","plant_second"): s.phase="reveal"
            elif s.phase=="plant_received": self._advance_received(s)
        elif action.type=="reveal":
            for _ in range(2):
                b=self._draw_one(s)
                if b is not None:s.zones["revealed"].append(b)
            if not s.terminal:s.phase="trade"
        elif action.type=="trade_start":
            s.pending={"type":"trade","actor":p,"partner":a["partner"],"offered":[],"requested":[],"awaiting_player":None}
        elif action.type in ("trade_add_offer_card","trade_add_request_card"):
            if action.type.endswith("offer_card"):
                zone=a["zone"]; i=a["index"]; cards=s.players[p]["hand"] if zone=="hand" else s.zones["revealed"]
                s.pending["offered"].append({"owner":p,"zone":zone,"index":i,"bean":cards[i]})
            else:
                q=s.pending["partner"];i=a["index"]
                s.pending["requested"].append({"owner":q,"zone":"hand","index":i,"bean":s.players[q]["hand"][i]})
        elif action.type=="trade_submit":
            s.pending["awaiting_player"]=s.pending["partner"];s.current_player=s.pending["partner"];s.phase="trade_response"
        elif action.type=="trade_accept":
            pend=s.pending; active=pend["actor"]; partner=pend["partner"]
            for item in sorted(pend["offered"],key=lambda x:x["index"],reverse=True):
                cards=s.players[active]["hand"] if item["zone"]=="hand" else s.zones["revealed"]
                s.zones["pending_received"][partner].append(cards.pop(item["index"]))
            for item in sorted(pend["requested"],key=lambda x:x["index"],reverse=True):
                s.zones["pending_received"][active].append(s.players[partner]["hand"].pop(item["index"]))
            s.pending=None;s.current_player=active;s.phase="trade"
        elif action.type=="trade_reject":
            active=s.active_player;s.pending=None;s.current_player=active;s.phase="trade"
        elif action.type=="end_trade":
            # Untraded face-up cards are the active player's planting obligation.
            s.zones["pending_received"][p].extend(s.zones["revealed"]);s.zones["revealed"].clear()
            s.phase="plant_received";s.current_player=0
            self._advance_received(s, allow_current=True)
        elif action.type=="draw":
            for _ in range(3):
                b=self._draw_one(s)
                if b is not None:s.players[p]["hand"].append(b)
            if not s.terminal:
                n=(s.active_player+1)%len(s.players);s.active_player=n;s.current_player=n;s.phase="plant_first"
        return s

    def _advance_received(self,s,allow_current=False):
        start=s.current_player if allow_current else s.current_player+1
        for q in range(start,len(s.players)):
            if s.zones["pending_received"][q]:s.current_player=q;return
        if s.depletions>=3:
            s.terminal=True;s.phase="terminal";s.current_player=s.active_player
        else:
            s.current_player=s.active_player;s.phase="draw"

    def action_to_name(self,a):
        d={"type":a.type,"actor":a.actor,"args":dict(a.args)}
        return json.dumps(d,ensure_ascii=False,sort_keys=True,separators=(",",":"))
    def name_to_action(self,name):
        try:d=json.loads(name);return self.action_from_data({"schema":"boardbench/bohnanza/action/1","data":d})
        except Exception as e: raise ValueError("invalid action name") from e
    def action_to_data(self,a):
        return {"schema":"boardbench/bohnanza/action/1","data":{"type":a.type,"actor":a.actor,"args":copy.deepcopy(dict(a.args))}}
    def action_from_data(self,payload):
        self._envelope(payload,"boardbench/bohnanza/action/1")
        d=payload["data"]
        if set(d)!={"type","actor","args"} or d["type"] not in TYPES or type(d["actor"]) is not int or not isinstance(d["args"],dict):raise ValueError("invalid action")
        if not all(isinstance(k,str) and type(v) in (str,int,bool,type(None)) for k,v in d["args"].items()):raise ValueError("invalid action args")
        return Action.make(d["type"],d["actor"],**d["args"])

    def state_to_data(self,s):
        return {"schema":"boardbench/bohnanza/state/1","data":copy.deepcopy({k:getattr(s,k) for k in ("configuration","current_player","active_player","start_player","phase","terminal","players","zones","depletions","pending","chance")})}
    def state_from_data(self,payload):
        self._envelope(payload,"boardbench/bohnanza/state/1");d=copy.deepcopy(payload["data"])
        req={"configuration","current_player","active_player","start_player","phase","terminal","players","zones","depletions","pending","chance"}
        if set(d)!=req:raise ValueError("invalid state fields")
        self._validate_state(d)
        return GameState(**d)
    def _envelope(self,p,schema):
        if not isinstance(p,dict) or set(p)!={"schema","data"} or p["schema"]!=schema or not isinstance(p["data"],dict):raise ValueError("invalid envelope")
    def _validate_state(self,d):
        if d["phase"] not in PHASES or type(d["terminal"]) is not bool or type(d["depletions"]) is not int:raise ValueError("invalid state")
        n=d["configuration"].get("players") if isinstance(d["configuration"],dict) else None
        if n not in (4,5) or len(d["players"])!=n:raise ValueError("invalid players")
        if set(d["zones"])!={"deck","discard","revealed","pending_received","reserve"}:raise ValueError("invalid zones")
        for seq in (d["zones"]["deck"],d["zones"]["discard"],d["zones"]["revealed"],d["zones"]["reserve"]):
            if not isinstance(seq,list) or any(x not in BEANS for x in seq):raise ValueError("invalid beans")
        if len(d["zones"]["pending_received"])!=n:raise ValueError("invalid received zones")

    def observation_to_data(self,s,player):
        if type(player) is not int or not 0<=player<len(s.players):raise ValueError("invalid player")
        pending=copy.deepcopy(s.pending)
        # Proposals concern public negotiations; hands themselves remain private.
        data={"player":player,"current_player":s.current_player,"active_player":s.active_player,"phase":s.phase,"terminal":s.terminal,
          "own_hand":s.players[player]["hand"][:],"opponents":[{"id":p["id"],"hand_size":len(p["hand"])} for p in s.players if p["id"]!=player],
          "fields":copy.deepcopy([p["fields"] for p in s.players]),"coins":[p["coins"] for p in s.players],"revealed":s.zones["revealed"][:],
          "deck_size":len(s.zones["deck"]),"discard_size":len(s.zones["discard"]),"pending":pending}
        return {"schema":"boardbench/bohnanza/observation/1","data":data}
    def render(self,s):
        return f"Bohnanza phase={s.phase} active={s.active_player} current={s.current_player} coins={[p['coins'] for p in s.players]}"
