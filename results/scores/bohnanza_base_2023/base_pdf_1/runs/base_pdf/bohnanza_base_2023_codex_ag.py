"""Self-contained Bohnanza environment, based only on the supplied German rules."""
from dataclasses import dataclass
import copy
import json
import random

BEANS = ("gartenbohne", "rote_bohne", "augenbohne", "sojabohne",
         "brechbohne", "saubohne", "feuerbohne", "blaue_bohne")
COUNTS = dict(zip(BEANS, (6, 8, 10, 12, 14, 16, 18, 20)))
PAY = {
    "gartenbohne": ((2, 1), (3, 2)),
    "rote_bohne": ((2, 1), (3, 2), (4, 3), (5, 4)),
    "augenbohne": ((2, 1), (4, 2), (5, 3), (6, 4)),
    "sojabohne": ((2, 1), (4, 2), (6, 3), (7, 4)),
    "brechbohne": ((3, 1), (5, 2), (6, 3), (7, 4)),
    "saubohne": ((3, 1), (5, 2), (7, 3), (8, 4)),
    "feuerbohne": ((3, 1), (6, 2), (8, 3), (9, 4)),
    "blaue_bohne": ((4, 1), (6, 2), (8, 3), (10, 4)),
}
PHASES = ("plant_first", "plant_second", "reveal", "trade", "trade_response",
          "plant_received", "draw", "terminal")
STATE_SCHEMA = "boardbench/bohnanza-base-2023/state/1"
ACTION_SCHEMA = "boardbench/bohnanza-base-2023/action/1"
OBS_SCHEMA = "boardbench/bohnanza-base-2023/observation/1"


@dataclass(eq=True)
class GameState:
    data: dict


@dataclass(frozen=True)
class Action:
    type: str
    actor: int
    args_json: str = "{}"

    @property
    def args(self):
        return json.loads(self.args_json)


def _action(kind, actor, args=None):
    return Action(kind, actor, json.dumps(args or {}, ensure_ascii=False,
                                           sort_keys=True, separators=(",", ":")))


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
        players = []
        fields = 3 if self.num_players == 3 else 2
        for p in range(self.num_players):
            hand = [deck.pop() for _ in range(5)]
            players.append({"id": p, "hand": hand,
                            "fields": [[] for _ in range(fields)], "coins": 0})
        d = {
            "configuration": {"players": self.num_players, "seed": self.seed},
            "current_player": 0, "active_player": 0, "start_player": 0,
            "phase": "plant_first", "terminal": False, "players": players,
            "zones": {"deck": deck, "discard": [], "revealed": [],
                      "pending_received": [[] for _ in players], "reserve": []},
            "depletions": 0, "pending": None,
            "chance": {"seed": self.seed, "draw_index": 5 * self.num_players},
        }
        return GameState(d)

    def current_player(self, state):
        return state.data["current_player"]

    def is_terminal(self, state):
        return bool(state.data["terminal"])

    def returns(self, state):
        n = len(state.data["players"])
        if not self.is_terminal(state):
            return [0] * n
        scores = [p["coins"] for p in state.data["players"]]
        best = max(scores)
        winners = [i for i, x in enumerate(scores) if x == best]
        if len(winners) > 1:
            start = state.data["start_player"]
            winners = [max(winners, key=lambda i: (i - start) % n)]
        return [1 if i == winners[0] else 0 for i in range(n)]

    def _can_harvest(self, d, p, f):
        field = d["players"][p]["fields"][f]
        if not field:
            return False
        if len(field) > 1:
            return True
        return not any(len(x) > 1 for x in d["players"][p]["fields"])

    def _harvest_actions(self, d):
        return [_action("harvest", p["id"], {"player": p["id"], "field": f})
                for p in d["players"] for f in range(len(p["fields"]))
                if self._can_harvest(d, p["id"], f)]

    def _plant_actions(self, d, source, actor, required=True):
        if source == "hand":
            cards = d["players"][actor]["hand"][:1]
        elif source == "revealed":
            cards = d["zones"]["revealed"]
        else:
            cards = d["zones"]["pending_received"][actor]
        out = []
        for i, bean in enumerate(cards):
            for f, field in enumerate(d["players"][actor]["fields"]):
                if not field or field[0] == bean:
                    out.append(_action("plant", actor, {"field": f, "source": source,
                                                       "index": i, "bean": bean}))
        return out

    def legal_actions(self, state):
        d = state.data
        if d["terminal"]:
            return []
        phase, a, cp = d["phase"], d["active_player"], d["current_player"]
        harvests = self._harvest_actions(d)
        if phase == "plant_first":
            plants = self._plant_actions(d, "hand", a)
            return harvests + plants if d["players"][a]["hand"] else [_action("pass", a)]
        if phase == "plant_second":
            return harvests + self._plant_actions(d, "hand", a) + [_action("pass", a)]
        if phase == "reveal":
            return harvests + [_action("reveal", a)]
        if phase == "trade_response":
            return [_action("trade_accept", cp), _action("trade_reject", cp)]
        if phase == "trade":
            out = harvests + [_action("end_trade", a)]
            own = ([{"owner": a, "zone": "hand", "index": i, "bean": b}
                    for i, b in enumerate(d["players"][a]["hand"])] +
                   [{"owner": a, "zone": "revealed", "index": i, "bean": b}
                    for i, b in enumerate(d["zones"]["revealed"])])
            # Any unequal card count is allowed. Enumerating all nonempty subsets
            # faithfully represents arbitrary offers while hands remain small.
            for partner in range(len(d["players"])):
                if partner == a:
                    continue
                theirs = [{"owner": partner, "zone": "hand", "index": i, "bean": b}
                          for i, b in enumerate(d["players"][partner]["hand"])]
                for omask in range(1, 1 << len(own)):
                    offered = [x for i, x in enumerate(own) if omask >> i & 1]
                    out.append(_action("trade_propose", a, {
                        "partner": partner, "offered": offered, "requested": [], "gift": True}))
                    for rmask in range(1, 1 << len(theirs)):
                        requested = [x for i, x in enumerate(theirs) if rmask >> i & 1]
                        out.append(_action("trade_propose", a, {
                            "partner": partner, "offered": offered,
                            "requested": requested, "gift": False}))
            return out
        if phase == "plant_received":
            received = d["zones"]["pending_received"][a]
            revealed = d["zones"]["revealed"]
            plants = (self._plant_actions(d, "received", a) +
                      self._plant_actions(d, "revealed", a))
            return harvests + plants if received or revealed else [_action("pass", a)]
        if phase == "draw":
            return [_action("draw", a)]
        return []

    def _draw_one(self, d):
        if not d["zones"]["deck"]:
            return None
        card = d["zones"]["deck"].pop()
        d["chance"]["draw_index"] += 1
        if not d["zones"]["deck"]:
            d["depletions"] += 1
            if d["depletions"] < 3:
                pile = d["zones"]["discard"]
                rng = random.Random(f"{d['chance']['seed']}:{d['chance']['draw_index']}")
                rng.shuffle(pile)
                d["zones"]["deck"] = pile
                d["zones"]["discard"] = []
        return card

    def _finish(self, d):
        d["terminal"] = True
        d["phase"] = "terminal"
        d["current_player"] = d["active_player"]
        for p in d["players"]:
            for f in range(len(p["fields"])):
                self._do_harvest(d, p["id"], f, final=True)
            p["coins"] += len(p["hand"])
            p["hand"] = []

    def _do_harvest(self, d, p, f, final=False):
        field = d["players"][p]["fields"][f]
        if not field:
            return
        count, bean = len(field), field[0]
        coins = max((c for needed, c in PAY[bean] if count >= needed), default=0)
        d["players"][p]["coins"] += coins
        d["zones"]["discard"].extend(field[:max(0, count - coins)])
        d["players"][p]["fields"][f] = []

    def apply_action(self, state, action):
        if state.data["terminal"] or not isinstance(action, Action):
            raise ValueError("illegal action")
        s, d, x = copy.deepcopy(state), None, action.args
        d = s.data
        a = action.actor
        if action.type == "harvest":
            self._do_harvest(d, x["player"], x["field"])
            return s
        if action.type == "pass":
            if d["phase"] == "plant_first": d["phase"] = "plant_second"
            elif d["phase"] == "plant_second": d["phase"] = "reveal"
            elif d["phase"] == "plant_received":
                if d["depletions"] >= 3:
                    self._finish(d)
                else:
                    d["phase"] = "draw"
            return s
        if action.type == "plant":
            src = x["source"]
            if src == "hand": cards = d["players"][a]["hand"]
            elif src == "revealed": cards = d["zones"]["revealed"]
            else: cards = d["zones"]["pending_received"][a]
            bean = cards.pop(x["index"])
            d["players"][a]["fields"][x["field"]].append(bean)
            if d["phase"] == "plant_first": d["phase"] = "plant_second"
            elif d["phase"] == "plant_second": d["phase"] = "reveal"
            elif d["phase"] == "plant_received":
                if not d["zones"]["pending_received"][a] and not d["zones"]["revealed"]:
                    if d["depletions"] >= 3:
                        self._finish(d)
            return s
        if action.type == "reveal":
            for _ in range(2):
                card = self._draw_one(d)
                if card is not None: d["zones"]["revealed"].append(card)
            d["phase"] = "trade"
            return s
        if action.type == "trade_propose":
            d["pending"] = {"type": "gift" if x["gift"] else "trade", "actor": a,
                            "partner": x["partner"], "offered": x["offered"],
                            "requested": x["requested"], "awaiting_player": x["partner"]}
            d["phase"], d["current_player"] = "trade_response", x["partner"]
            return s
        if action.type == "trade_reject":
            d["pending"] = None
            d["phase"], d["current_player"] = "trade", d["active_player"]
            return s
        if action.type == "trade_accept":
            p = d["pending"]
            transfers = ((p["offered"], p["partner"]), (p["requested"], p["actor"]))
            for refs, recipient in transfers:
                for ref in sorted(refs, key=lambda r: r["index"], reverse=True):
                    cards = (d["players"][ref["owner"]]["hand"] if ref["zone"] == "hand"
                             else d["zones"]["revealed"])
                    bean = cards.pop(ref["index"])
                    d["zones"]["pending_received"][recipient].append(bean)
            d["pending"] = None
            d["phase"], d["current_player"] = "trade", d["active_player"]
            return s
        if action.type == "end_trade":
            d["phase"] = "plant_received"
            return s
        if action.type == "draw":
            for _ in range(3):
                card = self._draw_one(d)
                if card is None: break
                d["players"][a]["hand"].append(card)
                if d["depletions"] >= 3:
                    self._finish(d)
                    return s
            nxt = (a + 1) % len(d["players"])
            d["active_player"] = d["current_player"] = nxt
            d["phase"] = "plant_first"
            return s
        raise ValueError("unknown action")

    def action_to_data(self, action):
        return {"schema": ACTION_SCHEMA, "data": {"type": action.type,
                "actor": action.actor, "args": copy.deepcopy(action.args)}}

    def action_from_data(self, payload):
        if not isinstance(payload, dict) or set(payload) != {"schema", "data"} or payload["schema"] != ACTION_SCHEMA:
            raise ValueError("invalid action envelope")
        d = payload["data"]
        if not isinstance(d, dict) or set(d) != {"type", "actor", "args"}:
            raise ValueError("invalid action fields")
        if d["type"] not in ("plant", "harvest", "reveal", "trade_propose",
                             "trade_accept", "trade_reject", "end_trade", "draw", "pass"):
            raise ValueError("invalid action type")
        if type(d["actor"]) is not int or not isinstance(d["args"], dict):
            raise ValueError("invalid action value")
        return _action(d["type"], d["actor"], d["args"])

    def action_to_name(self, action):
        return action.type.replace("_", " ") + " | " + str(action.actor) + " | " + action.args_json

    def name_to_action(self, name):
        try:
            label, actor, args = name.split(" | ", 2)
            return _action(label.replace(" ", "_"), int(actor), json.loads(args))
        except Exception as e:
            raise ValueError("invalid action name") from e

    def state_to_data(self, state):
        return {"schema": STATE_SCHEMA, "data": copy.deepcopy(state.data)}

    def state_from_data(self, payload):
        if not isinstance(payload, dict) or set(payload) != {"schema", "data"} or payload["schema"] != STATE_SCHEMA:
            raise ValueError("invalid state envelope")
        d = payload["data"]
        required = {"configuration", "current_player", "active_player", "start_player",
                    "phase", "terminal", "players", "zones", "depletions", "pending", "chance"}
        if not isinstance(d, dict) or set(d) != required:
            raise ValueError("invalid state fields")
        self._validate_state(d)
        return GameState(copy.deepcopy(d))

    def _validate_state(self, d):
        if d["phase"] not in PHASES or type(d["terminal"]) is not bool:
            raise ValueError("invalid phase")
        ps = d["players"]
        if not isinstance(ps, list) or not 3 <= len(ps) <= 5:
            raise ValueError("invalid players")
        ints = ("current_player", "active_player", "start_player", "depletions")
        if any(type(d[k]) is not int for k in ints):
            raise ValueError("invalid integer")
        for p in ps:
            if set(p) != {"id", "hand", "fields", "coins"} or type(p["id"]) is not int or type(p["coins"]) is not int:
                raise ValueError("invalid player")
            self._beans(p["hand"])
            if not isinstance(p["fields"], list): raise ValueError("invalid fields")
            for f in p["fields"]: self._beans(f)
        z = d["zones"]
        if set(z) != {"deck", "discard", "revealed", "pending_received", "reserve"}:
            raise ValueError("invalid zones")
        for k in ("deck", "discard", "revealed", "reserve"): self._beans(z[k])
        if not isinstance(z["pending_received"], list): raise ValueError("invalid received")
        for group in z["pending_received"]: self._beans(group)
        if set(d["configuration"]) != {"players", "seed"} or set(d["chance"]) != {"seed", "draw_index"}:
            raise ValueError("invalid configuration")
        json.dumps(d, allow_nan=False)

    @staticmethod
    def _beans(xs):
        if not isinstance(xs, list) or any(x not in BEANS for x in xs):
            raise ValueError("invalid bean list")

    def observation_to_data(self, state, player):
        d = state.data
        if type(player) is not int or not 0 <= player < len(d["players"]):
            raise ValueError("invalid observer")
        obs = {"player": player, "current_player": d["current_player"],
               "active_player": d["active_player"], "phase": d["phase"],
               "terminal": d["terminal"], "own_hand": copy.deepcopy(d["players"][player]["hand"]),
               "opponents": [{"id": p["id"], "hand_size": len(p["hand"])}
                             for p in d["players"] if p["id"] != player],
               "fields": copy.deepcopy([p["fields"] for p in d["players"]]),
               "coins": [p["coins"] for p in d["players"]],
               "revealed": copy.deepcopy(d["zones"]["revealed"]),
               "deck_size": len(d["zones"]["deck"]),
               "discard_size": len(d["zones"]["discard"]),
               "pending": copy.deepcopy(d["pending"])}
        if obs["pending"]:
            for key in ("offered", "requested"):
                obs["pending"][key] = [
                    ({**r} if r["owner"] == player or r["zone"] == "revealed"
                     else {"owner": r["owner"], "zone": r["zone"], "index": r["index"],
                           "bean": None}) for r in obs["pending"][key]]
        return {"schema": OBS_SCHEMA, "data": obs}

    def render(self, state):
        d = state.data
        lines = [f"Bohnanza | phase={d['phase']} active={d['active_player']} deck={len(d['zones']['deck'])}"]
        for p in d["players"]:
            lines.append(f"P{p['id']} coins={p['coins']} hand={p['hand']} fields={p['fields']}")
        return "\n".join(lines)
