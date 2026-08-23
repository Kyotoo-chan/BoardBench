"""Self-contained Bohnanza base-game environment (German rulebook v5.4)."""
from dataclasses import dataclass
from copy import deepcopy
from itertools import combinations
import json
import random

BEANS = ("gartenbohne", "rote_bohne", "augenbohne", "sojabohne",
         "brechbohne", "saubohne", "feuerbohne", "blaue_bohne")
COUNTS = dict(zip(BEANS, (6, 8, 10, 12, 14, 16, 18, 20)))
METERS = {
    "gartenbohne": ((2, 2), (3, 3)),
    "rote_bohne": ((3, 1), (6, 2), (7, 3), (8, 4)),
    "augenbohne": ((2, 1), (4, 2), (5, 3), (6, 4)),
    "sojabohne": ((2, 1), (4, 2), (6, 3), (7, 4)),
    "brechbohne": ((3, 1), (5, 2), (6, 3), (7, 4)),
    "saubohne": ((3, 1), (5, 2), (7, 3), (8, 4)),
    "feuerbohne": ((3, 1), (6, 2), (8, 3), (9, 4)),
    "blaue_bohne": ((4, 1), (6, 2), (8, 3), (10, 4)),
}
PHASES = {"plant_first", "plant_second", "reveal", "trade",
          "trade_response", "plant_received", "draw", "terminal"}
STATE_SCHEMA = "boardbench/bohnanza-base-2023/state/2"
ACTION_SCHEMA = "boardbench/bohnanza-base-2023/action/2"
OBS_SCHEMA = "boardbench/bohnanza-base-2023/observation/2"


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


def _action(kind, actor, **args):
    return Action(kind, actor, json.dumps(args, ensure_ascii=False,
                                           sort_keys=True, separators=(",", ":")))


class Game:
    def __init__(self, num_players=None, seed=None):
        self.num_players = 3 if num_players is None else num_players
        if type(self.num_players) is not int or self.num_players not in (3, 4, 5):
            raise ValueError("num_players must be 3, 4, or 5")
        if seed is not None and type(seed) is not int:
            raise ValueError("seed must be an int or None")
        self.seed = seed

    def initial_state(self):
        rng = random.Random(self.seed)
        cards = [bean for bean in BEANS for _ in range(COUNTS[bean])]
        rng.shuffle(cards)
        start = rng.randrange(self.num_players)
        players = [{"id": i, "hand": [], "fields": [[] for _ in
                    range(3 if self.num_players == 3 else 2)], "coins": 0}
                   for i in range(self.num_players)]
        # The source says five cards each, but gives no dealing sequence.
        for i in range(self.num_players):
            players[i]["hand"] = [cards.pop() for _ in range(5)]
        d = {
            "configuration": {"players": self.num_players, "seed": self.seed,
                              "variant": "base_2023"},
            "current_player": start, "active_player": start, "start_player": start,
            "phase": "plant_first", "terminal": False, "winner": None,
            "players": players,
            "zones": {"deck": cards, "discard": [], "revealed": [],
                      "pending_received": [[] for _ in players], "reserve": []},
            "depletions": 0, "pending": None, "turn_number": 0,
            "chance": {"seed": self.seed, "counter": 2},
        }
        return GameState(d)

    def current_player(self, state):
        return state.data["current_player"]

    @staticmethod
    def _harvestable(player, field):
        fields = player["fields"]
        if not (0 <= field < len(fields)) or not fields[field]:
            return False
        return len(fields[field]) > 1 or not any(len(f) > 1 for f in fields)

    @staticmethod
    def _plant_fields(player, bean):
        compatible = [i for i, f in enumerate(player["fields"])
                      if not f or f[0] == bean]
        if compatible:
            return compatible
        return [i for i in range(len(player["fields"]))
                if Game._harvestable(player, i)]

    def _harvest_actions(self, d):
        out = []
        for p in d["players"]:
            for f in range(len(p["fields"])):
                if self._harvestable(p, f):
                    out.append(_action("harvest", p["id"], player=p["id"], field=f))
        return out

    @staticmethod
    def _refs(owner, zone, cards):
        return [{"owner": owner, "zone": zone, "index": i, "bean": b}
                for i, b in enumerate(cards)]

    @staticmethod
    def _nonempty_subsets(items):
        for n in range(1, len(items) + 1):
            for group in combinations(items, n):
                yield list(group)

    def legal_actions(self, state):
        d = state.data
        if d["terminal"]:
            return []
        phase, active = d["phase"], d["active_player"]
        actions = self._harvest_actions(d)
        p = d["players"][active]
        if phase in ("plant_first", "plant_second"):
            if p["hand"]:
                bean = p["hand"][0]
                actions += [_action("plant", active, field=f, source="hand",
                                    index=0, bean=bean)
                            for f in self._plant_fields(p, bean)]
            if phase == "plant_second" or not p["hand"]:
                actions.append(_action("pass", active))
        elif phase == "reveal":
            actions.append(_action("reveal", active))
        elif phase == "trade":
            actions.append(_action("end_trade", active))
            offered_pool = (self._refs(active, "hand", p["hand"]) +
                            self._refs(active, "revealed", d["zones"]["revealed"]))
            offers = list(self._nonempty_subsets(offered_pool))
            for partner in range(len(d["players"])):
                if partner == active:
                    continue
                requested_pool = self._refs(partner, "hand",
                                            d["players"][partner]["hand"])
                for requested in self._nonempty_subsets(requested_pool):
                    actions.append(_action("trade_propose", active, partner=partner,
                                           offered=[], requested=requested, gift=True))
                for offered in offers:
                    actions.append(_action("trade_propose", active, partner=partner,
                                           offered=offered, requested=[], gift=True))
                    for requested in self._nonempty_subsets(requested_pool):
                        actions.append(_action("trade_propose", active, partner=partner,
                                               offered=offered, requested=requested,
                                               gift=False))
        elif phase == "trade_response":
            waiter = d["pending"]["awaiting_player"]
            actions += [_action("trade_accept", waiter), _action("trade_reject", waiter)]
        elif phase == "plant_received":
            for owner, cards in enumerate(d["zones"]["pending_received"]):
                if cards:
                    bean = cards[0]
                    actions += [_action("plant", owner, field=f, source="received",
                                        index=0, bean=bean)
                                for f in self._plant_fields(d["players"][owner], bean)]
            if d["zones"]["revealed"]:
                bean = d["zones"]["revealed"][0]
                actions += [_action("plant", active, field=f, source="revealed",
                                    index=0, bean=bean)
                            for f in self._plant_fields(p, bean)]
            if not d["zones"]["revealed"] and not any(d["zones"]["pending_received"]):
                actions.append(_action("pass", active))
        elif phase == "draw":
            actions.append(_action("draw", active))
        # Exact duplicates can arise only if malformed fixture data repeats refs.
        return list(dict.fromkeys(actions))

    def _rng_shuffle(self, d, cards):
        seed = d["chance"]["seed"]
        rng = random.Random(f"{seed!r}:{d['chance']['counter']}")
        rng.shuffle(cards)
        d["chance"]["counter"] += 1

    def _draw_one(self, d):
        if not d["zones"]["deck"]:
            return None
        card = d["zones"]["deck"].pop()
        if not d["zones"]["deck"]:
            d["depletions"] += 1
            if d["depletions"] < 3 and d["zones"]["discard"]:
                recycled = d["zones"]["discard"]
                d["zones"]["discard"] = []
                self._rng_shuffle(d, recycled)
                d["zones"]["deck"] = recycled
        return card

    @staticmethod
    def _payout(bean, count):
        result = 0
        for threshold, coins in METERS[bean]:
            if count >= threshold:
                result = coins
        return result

    def _harvest(self, d, player_id, field):
        p = d["players"][player_id]
        cards = p["fields"][field]
        coins = self._payout(cards[0], len(cards))
        p["coins"] += coins
        d["zones"]["discard"].extend(cards[coins:])
        p["fields"][field] = []

    def _finish(self, d):
        for p in d["players"]:
            for f in range(len(p["fields"])):
                if p["fields"][f]:
                    self._harvest(d, p["id"], f)
        best = max(p["coins"] for p in d["players"])
        tied = {p["id"] for p in d["players"] if p["coins"] == best}
        order = [(d["start_player"] + i) % len(d["players"])
                 for i in range(1, len(d["players"]) + 1)]
        d["winner"] = next(i for i in reversed(order) if i in tied)
        d["terminal"], d["phase"], d["pending"] = True, "terminal", None
        d["current_player"] = d["winner"]

    @staticmethod
    def _check_ref(d, ref):
        owner, zone, index, bean = (ref[k] for k in ("owner", "zone", "index", "bean"))
        cards = d["players"][owner]["hand"] if zone == "hand" else d["zones"]["revealed"]
        return 0 <= index < len(cards) and cards[index] == bean

    def apply_action(self, state, action):
        if action not in self.legal_actions(state):
            raise ValueError("illegal action")
        s, a = GameState(deepcopy(state.data)), action.args
        d = s.data
        if action.type == "harvest":
            self._harvest(d, a["player"], a["field"])
            return s
        if action.type == "plant":
            p = d["players"][action.actor]
            if a["source"] == "hand":
                bean = p["hand"].pop(0)
            elif a["source"] == "received":
                bean = d["zones"]["pending_received"][action.actor].pop(0)
            else:
                bean = d["zones"]["revealed"].pop(0)
            field = p["fields"][a["field"]]
            if field and field[0] != bean:
                self._harvest(d, action.actor, a["field"])
            p["fields"][a["field"]].append(bean)
            if d["phase"] == "plant_first":
                d["phase"] = "plant_second"
            return s
        if action.type == "pass":
            if d["phase"] == "plant_first":
                d["phase"] = "reveal"
            elif d["phase"] == "plant_second":
                d["phase"] = "reveal"
            elif d["phase"] == "plant_received":
                if d["depletions"] >= 3:
                    self._finish(d)
                else:
                    d["phase"] = "draw"
            return s
        if action.type == "reveal":
            for _ in range(2):
                card = self._draw_one(d)
                if card is not None:
                    d["zones"]["revealed"].append(card)
            d["phase"] = "trade"
            return s
        if action.type == "trade_propose":
            d["pending"] = {"type": "gift" if a["gift"] else "trade",
                            "actor": action.actor, "partner": a["partner"],
                            "offered": a["offered"], "requested": a["requested"],
                            "awaiting_player": a["partner"]}
            d["phase"], d["current_player"] = "trade_response", a["partner"]
            return s
        if action.type == "trade_reject":
            d["pending"] = None
            d["phase"], d["current_player"] = "trade", d["active_player"]
            return s
        if action.type == "trade_accept":
            proposal = d["pending"]
            if not all(self._check_ref(d, r)
                       for r in proposal["offered"] + proposal["requested"]):
                raise ValueError("proposal references changed cards")
            # Remove descending indices so snapshot references remain valid.
            transfers = []
            for ref in proposal["offered"] + proposal["requested"]:
                recipient = proposal["partner"] if ref["owner"] == proposal["actor"] else proposal["actor"]
                transfers.append((ref, recipient))
            for ref, recipient in sorted(transfers,
                                         key=lambda x: (x[0]["zone"], x[0]["owner"],
                                                        x[0]["index"]), reverse=True):
                cards = (d["players"][ref["owner"]]["hand"] if ref["zone"] == "hand"
                         else d["zones"]["revealed"])
                cards.pop(ref["index"])
                d["zones"]["pending_received"][recipient].append(ref["bean"])
            d["pending"] = None
            d["phase"], d["current_player"] = "trade", d["active_player"]
            return s
        if action.type == "end_trade":
            d["phase"] = "plant_received"
            return s
        if action.type == "draw":
            for _ in range(3):
                card = self._draw_one(d)
                if card is not None:
                    d["players"][d["active_player"]]["hand"].append(card)
                if d["depletions"] >= 3:
                    break
            if d["depletions"] >= 3:
                self._finish(d)
            else:
                nxt = (d["active_player"] + 1) % len(d["players"])
                d["active_player"] = d["current_player"] = nxt
                d["phase"], d["turn_number"] = "plant_first", d["turn_number"] + 1
            return s
        raise ValueError("unknown action")

    def is_terminal(self, state):
        return state.data["terminal"]

    def returns(self, state):
        if not state.data["terminal"]:
            return [0 for _ in state.data["players"]]
        return [1 if p["id"] == state.data["winner"] else 0
                for p in state.data["players"]]

    def render(self, state):
        d = state.data
        lines = [f"Bohnanza | phase={d['phase']} active={d['active_player']} "
                 f"current={d['current_player']} deck={len(d['zones']['deck'])}"]
        for p in d["players"]:
            lines.append(f"P{p['id']}: coins={p['coins']} hand={p['hand']} "
                         f"fields={p['fields']}")
        return "\n".join(lines)

    def action_to_data(self, action):
        if not isinstance(action, Action):
            raise ValueError("invalid action")
        return {"schema": ACTION_SCHEMA,
                "data": {"type": action.type, "actor": action.actor,
                         "args": deepcopy(action.args)}}

    def action_from_data(self, payload):
        self._envelope(payload, ACTION_SCHEMA)
        d = payload["data"]
        if set(d) != {"type", "actor", "args"} or type(d["actor"]) is not int or not isinstance(d["args"], dict):
            raise ValueError("invalid action fields")
        if d["type"] not in {"plant", "harvest", "reveal", "trade_propose",
                             "trade_accept", "trade_reject", "end_trade", "draw", "pass"}:
            raise ValueError("unknown action type")
        expected = {"plant": {"field", "source", "index", "bean"},
                    "harvest": {"player", "field"},
                    "trade_propose": {"partner", "offered", "requested", "gift"}}
        if set(d["args"]) != expected.get(d["type"], set()):
            raise ValueError("invalid action arguments")
        return _action(d["type"], d["actor"], **deepcopy(d["args"]))

    def action_to_name(self, action):
        d = self.action_to_data(action)["data"]
        return d["type"] + ":" + str(d["actor"]) + ":" + json.dumps(
            d["args"], ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    def name_to_action(self, name):
        try:
            kind, actor, raw = name.split(":", 2)
            return self.action_from_data({"schema": ACTION_SCHEMA,
                                          "data": {"type": kind, "actor": int(actor),
                                                   "args": json.loads(raw)}})
        except Exception as exc:
            raise ValueError("invalid action name") from exc

    @staticmethod
    def _envelope(payload, schema):
        if not isinstance(payload, dict) or set(payload) != {"schema", "data"}:
            raise ValueError("invalid envelope")
        if payload["schema"] != schema or not isinstance(payload["data"], dict):
            raise ValueError("invalid schema or data")

    def state_to_data(self, state):
        if not isinstance(state, GameState):
            raise ValueError("invalid state")
        return {"schema": STATE_SCHEMA, "data": deepcopy(state.data)}

    def state_from_data(self, payload):
        self._envelope(payload, STATE_SCHEMA)
        d = payload["data"]
        required = {"configuration", "current_player", "active_player", "start_player",
                    "phase", "terminal", "winner", "players", "zones", "depletions",
                    "pending", "turn_number", "chance"}
        if set(d) != required or d.get("phase") not in PHASES:
            raise ValueError("invalid state fields")
        if not isinstance(d.get("players"), list) or not isinstance(d.get("zones"), dict):
            raise ValueError("invalid state types")
        return GameState(deepcopy(d))

    def observation_to_data(self, state, player):
        d = state.data
        if type(player) is not int or not 0 <= player < len(d["players"]):
            raise ValueError("invalid player")
        opponents = [{"id": p["id"], "hand_size": len(p["hand"]),
                      "front_card": p["hand"][0] if p["hand"] else None}
                     for p in d["players"] if p["id"] != player]
        data = {"player": player, "current_player": d["current_player"],
                "active_player": d["active_player"], "start_player": d["start_player"],
                "phase": d["phase"], "terminal": d["terminal"], "winner": d["winner"],
                "own_hand": deepcopy(d["players"][player]["hand"]),
                "opponents": opponents,
                "fields": deepcopy([p["fields"] for p in d["players"]]),
                "coins": [p["coins"] for p in d["players"]],
                "revealed": deepcopy(d["zones"]["revealed"]),
                "deck_size": len(d["zones"]["deck"]),
                "discard_size": len(d["zones"]["discard"]),
                "pending_received_counts": [len(x) for x in d["zones"]["pending_received"]],
                "pending": deepcopy(d["pending"]), "turn_number": d["turn_number"]}
        return {"schema": OBS_SCHEMA, "data": data}
