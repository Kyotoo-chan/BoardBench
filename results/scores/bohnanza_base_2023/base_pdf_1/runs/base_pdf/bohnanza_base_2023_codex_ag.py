"""Small, self-contained implementation of the supplied German Bohnanza rules."""
from dataclasses import dataclass
import copy
import itertools
import json
import random

BEANS = ("gartenbohne", "rote_bohne", "augenbohne", "sojabohne",
         "brechbohne", "saubohne", "feuerbohne", "blaue_bohne")
COUNTS = dict(zip(BEANS, (6, 8, 10, 12, 14, 16, 18, 20)))
# minimum field size paying respectively 1, 2, 3, 4 coins (read from the cards)
METERS = {
    "gartenbohne": (2, 3), "rote_bohne": (2, 3, 4, 5),
    "augenbohne": (2, 4, 5, 6), "sojabohne": (2, 4, 6, 7),
    "brechbohne": (3, 5, 6, 7), "saubohne": (3, 5, 7, 8),
    "feuerbohne": (3, 6, 8, 9), "blaue_bohne": (4, 6, 8, 10),
}
PHASES = ("plant_first", "plant_second", "reveal", "trade", "trade_response",
          "plant_received", "draw", "terminal")
STATE_SCHEMA = "boardbench/bohnanza-base-2023/state/1"
ACTION_SCHEMA = "boardbench/bohnanza-base-2023/action/1"
OBS_SCHEMA = "boardbench/bohnanza-base-2023/observation/1"


@dataclass(eq=True)
class Action:
    type: str
    actor: int
    args: dict


@dataclass(eq=True)
class GameState:
    configuration: dict
    current_player: int
    active_player: int
    start_player: int
    phase: str
    terminal: bool
    players: list
    zones: dict
    depletions: int
    pending: dict | None
    chance: dict


class Game:
    def __init__(self, num_players=None, seed=None):
        self.num_players = 3 if num_players is None else num_players
        if type(self.num_players) is not int or not 3 <= self.num_players <= 5:
            raise ValueError("num_players must be 3, 4, or 5")
        if seed is not None and type(seed) is not int:
            raise TypeError("seed must be int or None")
        self.seed = seed

    def initial_state(self):
        deck = [b for b in BEANS for _ in range(COUNTS[b])]
        random.Random(self.seed).shuffle(deck)
        fields = 3 if self.num_players == 3 else 2
        players = [{"id": p, "hand": [], "fields": [[] for _ in range(fields)], "coins": 0}
                   for p in range(self.num_players)]
        # Deal one at a time, preserving the order received; index zero is the front.
        for _ in range(5):
            for p in players:
                p["hand"].append(deck.pop())
        return GameState({"players": self.num_players, "seed": self.seed}, 0, 0, 0,
                         "plant_first", False, players,
                         {"deck": deck, "discard": [], "revealed": [],
                          "pending_received": [[] for _ in players], "reserve": []},
                         0, None, {"seed": self.seed, "draw_index": 0})

    def current_player(self, state): return state.current_player
    def is_terminal(self, state): return state.terminal

    def returns(self, state):
        if not state.terminal:
            return [0] * len(state.players)
        scores = [p["coins"] for p in state.players]
        m = max(scores)
        tied = [i for i, x in enumerate(scores) if x == m]
        winner = max(tied, key=lambda i: (i - state.start_player) % len(scores))
        return [1 if i == winner else 0 for i in range(len(scores))]

    def _ref(self, owner, zone, index, bean):
        return {"owner": owner, "zone": zone, "index": index, "bean": bean}

    def _harvest_actions(self, s):
        out = []
        for p in s.players:
            has_multi = any(len(f) > 1 for f in p["fields"])
            for i, f in enumerate(p["fields"]):
                if f and (len(f) > 1 or not has_multi):
                    out.append(Action("harvest", p["id"], {"player": p["id"], "field": i}))
        return out

    def _plant_actions(self, s, source, owner):
        if source == "hand":
            cards = s.players[owner]["hand"][:1]
        elif source == "revealed": cards = s.zones["revealed"]
        else: cards = s.zones["pending_received"][owner]
        if not cards: return []
        bean = cards[0]
        return [Action("plant", owner, {"field": i, "source": source, "index": 0, "bean": bean})
                for i, f in enumerate(s.players[owner]["fields"]) if not f or f[0] == bean]

    def legal_actions(self, s):
        if s.terminal: return []
        a = self._harvest_actions(s)
        p = s.active_player
        if s.phase == "plant_first":
            if s.players[p]["hand"]: a += self._plant_actions(s, "hand", p)
            else: a.append(Action("pass", p, {}))
        elif s.phase == "plant_second":
            a += self._plant_actions(s, "hand", p) + [Action("pass", p, {})]
        elif s.phase == "reveal": a.append(Action("reveal", p, {}))
        elif s.phase == "trade":
            a.append(Action("end_trade", p, {}))
            sources = [self._ref(p, "hand", i, b) for i, b in enumerate(s.players[p]["hand"])]
            sources += [self._ref(p, "revealed", i, b) for i, b in enumerate(s.zones["revealed"])]
            # Concrete one/two-card offers and requests cover the explicitly illustrated
            # unequal trades without making legal-action enumeration unboundedly large.
            offers = [list(x) for n in (1, 2) for x in itertools.combinations(sources, n)]
            for q in range(len(s.players)):
                if q == p: continue
                reqs = [self._ref(q, "hand", i, b) for i, b in enumerate(s.players[q]["hand"])]
                for offered in offers:
                    a.append(Action("trade_propose", p, {"partner": q, "offered": offered, "requested": [], "gift": True}))
                    for requested in reqs:
                        a.append(Action("trade_propose", p, {"partner": q, "offered": offered,
                                                               "requested": [requested], "gift": False}))
        elif s.phase == "trade_response":
            a += [Action("trade_accept", s.current_player, {}), Action("trade_reject", s.current_player, {})]
        elif s.phase == "plant_received":
            a += self._plant_actions(s, "received", p) + self._plant_actions(s, "revealed", p)
            if not s.zones["pending_received"][p] and not s.zones["revealed"]:
                a.append(Action("pass", p, {}))
        elif s.phase == "draw": a.append(Action("draw", p, {}))
        return a

    def _draw_one(self, s):
        if not s.zones["deck"]:
            s.depletions += 1
            if s.depletions >= 3:
                if s.phase != "reveal": self._finish(s)
                return None
            s.zones["deck"] = s.zones["discard"]
            s.zones["discard"] = []
            seed = s.chance["seed"]
            random.Random((0 if seed is None else seed) + s.chance["draw_index"] + 1).shuffle(s.zones["deck"])
            s.chance["draw_index"] += 1
            if not s.zones["deck"]: return None
        return s.zones["deck"].pop()

    def _finish(self, s):
        # At game end everybody harvests every field; hand cards have no value.
        for p in s.players:
            for f in p["fields"]:
                if f:
                    coins = sum(len(f) >= threshold for threshold in METERS[f[0]])
                    p["coins"] += coins
                    s.zones["discard"].extend(f[:len(f)-coins])
                    f.clear()
        s.terminal = True; s.phase = "terminal"

    def _get_ref(self, s, ref):
        return s.players[ref["owner"]]["hand"] if ref["zone"] == "hand" else s.zones["revealed"]

    def apply_action(self, state, action):
        s = copy.deepcopy(state)
        canon = self.action_to_data(action)
        legal = {json.dumps(self.action_to_data(x), sort_keys=True): x for x in self.legal_actions(s)}
        if json.dumps(canon, sort_keys=True) not in legal: raise ValueError("illegal action")
        t, p, x = action.type, action.actor, action.args
        if t == "harvest":
            f = s.players[x["player"]]["fields"][x["field"]]; n = len(f); bean = f[0]
            coins = sum(n >= threshold for threshold in METERS[bean])
            s.players[x["player"]]["coins"] += coins
            s.zones["discard"].extend(f[:n-coins]); s.players[x["player"]]["fields"][x["field"]] = []
            return s
        if t == "plant":
            if x["source"] == "hand": zone = s.players[p]["hand"]
            elif x["source"] == "revealed": zone = s.zones["revealed"]
            else: zone = s.zones["pending_received"][p]
            bean = zone.pop(x["index"]); s.players[p]["fields"][x["field"]].append(bean)
            if s.phase == "plant_first": s.phase = "plant_second"
            return s
        if t == "pass":
            if s.phase in ("plant_first", "plant_second"): s.phase = "reveal"
            elif s.phase == "plant_received":
                if s.depletions >= 3: self._finish(s)
                else: s.phase = "draw"
            return s
        if t == "reveal":
            for _ in range(2):
                card = self._draw_one(s)
                if card is None: break
                s.zones["revealed"].append(card)
            if not s.terminal: s.phase = "trade"
            return s
        if t == "trade_propose":
            s.pending = {"type": "gift" if x["gift"] else "trade", "actor": p, "partner": x["partner"],
                         "offered": copy.deepcopy(x["offered"]), "requested": copy.deepcopy(x["requested"]),
                         "awaiting_player": x["partner"]}
            s.phase = "trade_response"; s.current_player = x["partner"]; return s
        if t == "trade_reject":
            s.pending = None; s.phase = "trade"; s.current_player = s.active_player; return s
        if t == "trade_accept":
            pend = s.pending
            # Remove descending indices within each zone, then deliver to the other party.
            transfers = [(r, pend["partner"]) for r in pend["offered"]] + [(r, pend["actor"]) for r in pend["requested"]]
            for ref, recipient in sorted(transfers, key=lambda z: (z[0]["owner"], z[0]["zone"], -z[0]["index"])):
                bean = self._get_ref(s, ref).pop(ref["index"])
                s.zones["pending_received"][recipient].append(bean)
            s.pending = None; s.phase = "trade"; s.current_player = s.active_player; return s
        if t == "end_trade": s.phase = "plant_received"; return s
        if t == "draw":
            for _ in range(3):
                card = self._draw_one(s)
                if card is None: break
                s.players[p]["hand"].append(card)
            if not s.terminal:
                s.active_player = (p + 1) % len(s.players); s.current_player = s.active_player; s.phase = "plant_first"
            return s
        raise ValueError("unknown action")

    def action_to_name(self, action):
        return action.type + ":" + json.dumps({"actor": action.actor, "args": action.args}, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    def name_to_action(self, name):
        try:
            t, raw = name.split(":", 1); d = json.loads(raw)
            return self.action_from_data({"schema": ACTION_SCHEMA, "data": {"type": t, "actor": d["actor"], "args": d["args"]}})
        except Exception as e: raise ValueError("invalid action name") from e

    def action_to_data(self, action):
        if not isinstance(action, Action): raise TypeError("action must be Action")
        return {"schema": ACTION_SCHEMA, "data": {"type": action.type, "actor": action.actor, "args": copy.deepcopy(action.args)}}

    def action_from_data(self, payload):
        self._envelope(payload, ACTION_SCHEMA)
        d = payload["data"]
        if set(d) != {"type", "actor", "args"} or d["type"] not in ("plant", "harvest", "reveal", "trade_propose", "trade_accept", "trade_reject", "end_trade", "draw", "pass"):
            raise ValueError("invalid action fields")
        if type(d["actor"]) is not int or not isinstance(d["args"], dict): raise TypeError("invalid action types")
        expected = {"plant": {"field","source","index","bean"}, "harvest": {"player","field"}, "reveal": set(),
                    "trade_propose": {"partner","offered","requested","gift"}, "trade_accept": set(),
                    "trade_reject": set(), "end_trade": set(), "draw": set(), "pass": set()}[d["type"]]
        if set(d["args"]) != expected: raise ValueError("invalid action args")
        return Action(d["type"], d["actor"], copy.deepcopy(d["args"]))

    def state_to_data(self, s):
        return {"schema": STATE_SCHEMA, "data": copy.deepcopy(s.__dict__)}

    def state_from_data(self, payload):
        self._envelope(payload, STATE_SCHEMA); d = copy.deepcopy(payload["data"])
        required = {"configuration","current_player","active_player","start_player","phase","terminal","players","zones","depletions","pending","chance"}
        if set(d) != required: raise ValueError("invalid state fields")
        if d["phase"] not in PHASES or type(d["terminal"]) is not bool: raise ValueError("invalid state phase")
        if not isinstance(d["players"], list) or not isinstance(d["zones"], dict): raise TypeError("invalid state types")
        return GameState(**d)

    def observation_to_data(self, s, player):
        if type(player) is not int or not 0 <= player < len(s.players): raise ValueError("invalid player")
        opponents = [{"id": p["id"], "hand_size": len(p["hand"])} for p in s.players if p["id"] != player]
        pending = copy.deepcopy(s.pending)
        # A concrete proposal is known to its participants; hide referenced bean identities from others.
        if pending and player not in (pending["actor"], pending["partner"]): pending = None
        data = {"player": player, "current_player": s.current_player, "active_player": s.active_player,
                "phase": s.phase, "terminal": s.terminal, "own_hand": copy.deepcopy(s.players[player]["hand"]),
                "opponents": opponents, "fields": copy.deepcopy([p["fields"] for p in s.players]),
                "coins": [p["coins"] for p in s.players], "revealed": copy.deepcopy(s.zones["revealed"]),
                "deck_size": len(s.zones["deck"]), "discard_size": len(s.zones["discard"]), "pending": pending}
        return {"schema": OBS_SCHEMA, "data": data}

    def _envelope(self, p, schema):
        if not isinstance(p, dict) or set(p) != {"schema","data"} or p["schema"] != schema or not isinstance(p["data"], dict):
            raise ValueError("invalid canonical envelope")

    def render(self, s):
        lines = [f"phase={s.phase} active={s.active_player} deck={len(s.zones['deck'])} discard={len(s.zones['discard'])}"]
        for p in s.players: lines.append(f"P{p['id']} coins={p['coins']} hand={p['hand']} fields={p['fields']}")
        return "\n".join(lines)
