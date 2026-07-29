"""Bohnanza base game, implemented only from the supplied German rulebook."""
from dataclasses import dataclass
import copy
import json
import random

BEANS = ("gartenbohne", "rote_bohne", "augenbohne", "sojabohne",
         "brechbohne", "saubohne", "feuerbohne", "blaue_bohne")
COUNTS = dict(zip(BEANS, (6, 8, 10, 12, 14, 16, 18, 20)))
# bean meter: field size -> coins (largest satisfied threshold wins)
METERS = {
    "gartenbohne": ((2, 1), (3, 2)),
    "rote_bohne": ((2, 1), (3, 2), (4, 3), (5, 4)),
    "augenbohne": ((2, 1), (4, 2), (5, 3), (6, 4)),
    "sojabohne": ((2, 1), (4, 2), (6, 3), (7, 4)),
    "brechbohne": ((3, 1), (5, 2), (6, 3), (7, 4)),
    "saubohne": ((3, 1), (5, 2), (7, 3), (8, 4)),
    "feuerbohne": ((3, 1), (6, 2), (8, 3), (9, 4)),
    "blaue_bohne": ((4, 1), (6, 2), (8, 3), (10, 4)),
}
PHASES = ("plant_first", "plant_second", "reveal", "trade",
          "trade_response", "plant_received", "draw", "terminal")
ACTION_TYPES = ("plant", "harvest", "reveal", "trade_propose",
                "trade_accept", "trade_reject", "end_trade", "draw", "pass")
STATE_SCHEMA = "boardbench/bohnanza-base-2023/state/2"
ACTION_SCHEMA = "boardbench/bohnanza-base-2023/action/2"
OBS_SCHEMA = "boardbench/bohnanza-base-2023/observation/2"


@dataclass(frozen=True)
class Action:
    type: str
    actor: int
    args_json: str = "{}"

    @property
    def args(self):
        return json.loads(self.args_json)


@dataclass
class GameState:
    data: dict


def _action(kind, actor, **args):
    return Action(kind, actor, json.dumps(args, sort_keys=True, separators=(",", ":")))


class Game:
    def __init__(self, num_players=None, seed=None):
        self.num_players = 3 if num_players is None else num_players
        if type(self.num_players) is not int or self.num_players not in (3, 4, 5):
            raise ValueError("num_players must be 3, 4, or 5")
        if seed is not None and type(seed) is not int:
            raise ValueError("seed must be an integer or None")
        self.seed = seed

    def _rng(self, d):
        # Complete serialized chance state, independent of mutable Game instance.
        marker = f"{d['chance']['seed']}:{d['chance']['counter']}"
        d["chance"]["counter"] += 1
        return random.Random(marker)

    def initial_state(self):
        deck = [b for b in BEANS for _ in range(COUNTS[b])]
        d = {
            "configuration": {"players": self.num_players, "seed": self.seed,
                              "variant": "base_2023"},
            "current_player": 0, "active_player": 0, "start_player": 0,
            "phase": "plant_first", "terminal": False, "winner": None,
            "players": [{"id": i, "hand": [], "fields": [[], []], "coins": 0}
                        for i in range(self.num_players)],
            "zones": {"deck": deck, "discard": [], "revealed": [],
                      "pending_received": [[] for _ in range(self.num_players)],
                      "reserve": []},
            "depletions": 0, "pending": None, "turn_number": 0,
            "chance": {"seed": self.seed, "counter": 0},
        }
        rng = self._rng(d)
        rng.shuffle(d["zones"]["deck"])
        start = rng.randrange(self.num_players)
        d["current_player"] = d["active_player"] = d["start_player"] = start
        for _ in range(5):
            for p in d["players"]:
                p["hand"].append(d["zones"]["deck"].pop())
        return GameState(d)

    def current_player(self, state):
        return state.data["current_player"]

    def _can_plant(self, p, field, bean):
        fields = p["fields"]
        return 0 <= field < len(fields) and (not fields[field] or fields[field][0] == bean)

    def _harvestable(self, d, pi, fi):
        fields = d["players"][pi]["fields"]
        if not (0 <= fi < len(fields)) or not fields[fi]:
            return False
        # Bean protection: a one-card field cannot be harvested if another has >1.
        return len(fields[fi]) > 1 or not any(len(f) > 1 for f in fields)

    def legal_actions(self, state):
        d = state.data
        if d["terminal"]:
            return []
        cp, ap, phase = d["current_player"], d["active_player"], d["phase"]
        out = []
        # Harvest is always available at stable decisions, to the field owner.
        for fi in range(len(d["players"][cp]["fields"])):
            if self._harvestable(d, cp, fi):
                out.append(_action("harvest", cp, player=cp, field=fi))
        if phase in ("plant_first", "plant_second"):
            hand = d["players"][ap]["hand"]
            if hand:
                bean = hand[0]
                for fi in range(len(d["players"][ap]["fields"])):
                    if self._can_plant(d["players"][ap], fi, bean):
                        out.append(_action("plant", ap, field=fi, source="hand",
                                           index=0, bean=bean))
            elif phase == "plant_first":
                out.append(_action("pass", ap))
            if phase == "plant_second":
                out.append(_action("pass", ap))
        elif phase == "reveal":
            out.append(_action("reveal", ap))
        elif phase == "trade":
            out.append(_action("end_trade", ap))
            out.extend(self._trade_proposals(d))
        elif phase == "trade_response":
            out += [_action("trade_accept", cp), _action("trade_reject", cp)]
        elif phase == "plant_received":
            received = d["zones"]["pending_received"][cp]
            source = "received"
            cards = received
            if not cards and cp == ap and d["zones"]["revealed"]:
                source, cards = "revealed", d["zones"]["revealed"]
            if cards:
                bean = cards[0]
                for fi in range(len(d["players"][cp]["fields"])):
                    if self._can_plant(d["players"][cp], fi, bean):
                        out.append(_action("plant", cp, field=fi, source=source,
                                           index=0, bean=bean))
        elif phase == "draw":
            out.append(_action("draw", ap))
        return out

    def _refs(self, d, owner, zone):
        cards = d["players"][owner]["hand"] if zone == "hand" else d["zones"]["revealed"]
        return [{"owner": owner, "zone": zone, "index": i, "bean": b}
                for i, b in enumerate(cards)]

    def _trade_proposals(self, d):
        """Finite atomic offers: one or two cards each side; gifts are one offered card."""
        ap = d["active_player"]
        offered_pool = self._refs(d, ap, "hand") + self._refs(d, ap, "revealed")
        offers = [[x] for x in offered_pool]
        offers += [[offered_pool[i], offered_pool[j]]
                   for i in range(len(offered_pool)) for j in range(i + 1, len(offered_pool))]
        out = []
        for partner in range(len(d["players"])):
            if partner == ap:
                continue
            requested_pool = self._refs(d, partner, "hand")
            requests = [[x] for x in requested_pool]
            requests += [[requested_pool[i], requested_pool[j]]
                         for i in range(len(requested_pool))
                         for j in range(i + 1, len(requested_pool))]
            for o in offers:
                out.append(_action("trade_propose", ap, partner=partner,
                                   offered=o, requested=[], gift=True))
                for r in requests:
                    out.append(_action("trade_propose", ap, partner=partner,
                                       offered=o, requested=r, gift=False))
        return out

    def _recycle_or_end(self, d):
        if d["zones"]["deck"]:
            return True
        if d["depletions"] >= 2:
            self._finish(d)
            return False
        d["zones"]["deck"] = d["zones"]["discard"]
        d["zones"]["discard"] = []
        self._rng(d).shuffle(d["zones"]["deck"])
        d["depletions"] += 1
        if not d["zones"]["deck"]:
            self._finish(d)
            return False
        return True

    def _draw_one(self, d):
        if not self._recycle_or_end(d):
            return None
        card = d["zones"]["deck"].pop()
        if not d["zones"]["deck"] and d["depletions"] == 2:
            d["depletions"] = 3
        return card

    def _finish(self, d):
        d["terminal"] = True
        d["phase"] = "terminal"
        d["pending"] = None
        best = max(p["coins"] for p in d["players"])
        tied = {p["id"] for p in d["players"] if p["coins"] == best}
        # clockwise furthest from start = predecessor among tied players
        d["winner"] = max(tied, key=lambda i: (i - d["start_player"]) % len(d["players"]))
        d["current_player"] = d["winner"]

    def _next_phase3_actor(self, d):
        ap, n = d["active_player"], len(d["players"])
        candidates = [i for i in range(n) if d["zones"]["pending_received"][i]]
        if d["zones"]["revealed"]:
            candidates.append(ap)
        if candidates:
            d["phase"] = "plant_received"
            d["current_player"] = min(set(candidates), key=lambda i: (i - ap) % n)
        elif d["depletions"] == 3:
            self._finish(d)
        else:
            d["phase"] = "draw"
            d["current_player"] = ap

    def apply_action(self, state, action):
        legal = self.legal_actions(state)
        if action not in legal:
            raise ValueError("illegal action")
        s = copy.deepcopy(state)
        d, a = s.data, action.args
        kind, actor = action.type, action.actor
        if kind == "harvest":
            field = d["players"][actor]["fields"][a["field"]]
            bean, count = field[0], len(field)
            coins = max((v for threshold, v in METERS[bean] if count >= threshold), default=0)
            d["players"][actor]["coins"] += coins
            d["zones"]["discard"].extend(field[:count - coins])
            d["players"][actor]["fields"][a["field"]] = []
            return s
        if kind == "plant":
            if a["source"] == "hand":
                bean = d["players"][actor]["hand"].pop(0)
            elif a["source"] == "received":
                bean = d["zones"]["pending_received"][actor].pop(0)
            else:
                bean = d["zones"]["revealed"].pop(0)
            d["players"][actor]["fields"][a["field"]].append(bean)
            if d["phase"] == "plant_first":
                d["phase"] = "plant_second"
            elif d["phase"] == "plant_second":
                d["phase"] = "reveal"
            else:
                self._next_phase3_actor(d)
        elif kind == "pass":
            d["phase"] = "reveal"
        elif kind == "reveal":
            for _ in range(2):
                card = self._draw_one(d)
                if card is None:
                    # On the third depletion, printed rules finish phases 2 and 3.
                    if d["terminal"]:
                        d["terminal"] = False
                        d["winner"] = None
                        d["depletions"] = 3
                    break
                d["zones"]["revealed"].append(card)
            d["phase"] = "trade"
        elif kind == "trade_propose":
            d["pending"] = {"type": "gift" if a["gift"] else "trade",
                            "actor": actor, "partner": a["partner"],
                            "offered": a["offered"], "requested": a["requested"],
                            "awaiting_player": a["partner"]}
            d["phase"] = "trade_response"
            d["current_player"] = a["partner"]
        elif kind == "trade_reject":
            d["pending"] = None
            d["phase"] = "trade"
            d["current_player"] = d["active_player"]
        elif kind == "trade_accept":
            p = d["pending"]
            moved = []
            for ref, recipient in [(r, p["partner"]) for r in p["offered"]] + \
                                  [(r, p["actor"]) for r in p["requested"]]:
                zone = (d["players"][ref["owner"]]["hand"] if ref["zone"] == "hand"
                        else d["zones"]["revealed"])
                moved.append((ref, recipient, zone))
            for ref, recipient, zone in sorted(moved, key=lambda x: x[0]["index"], reverse=True):
                card = zone.pop(ref["index"])
                d["zones"]["pending_received"][recipient].append(card)
            d["pending"] = None
            d["phase"] = "trade"
            d["current_player"] = d["active_player"]
        elif kind == "end_trade":
            if d["depletions"] == 3 and not any(d["zones"]["pending_received"]) and not d["zones"]["revealed"]:
                self._finish(d)
            else:
                self._next_phase3_actor(d)
        elif kind == "draw":
            for _ in range(3):
                card = self._draw_one(d)
                if card is None:
                    return s
                d["players"][actor]["hand"].append(card)
                if d["depletions"] == 3:
                    self._finish(d)
                    return s
            nxt = (actor + 1) % len(d["players"])
            d["active_player"] = d["current_player"] = nxt
            d["phase"] = "plant_first"
            d["turn_number"] += 1
        return s

    def is_terminal(self, state):
        return state.data["terminal"]

    def returns(self, state):
        if not state.data["terminal"]:
            return [0 for _ in state.data["players"]]
        return [1 if p["id"] == state.data["winner"] else 0 for p in state.data["players"]]

    def action_to_data(self, action):
        if not isinstance(action, Action) or action.type not in ACTION_TYPES:
            raise ValueError("invalid action")
        return {"schema": ACTION_SCHEMA,
                "data": {"type": action.type, "actor": action.actor,
                         "args": copy.deepcopy(action.args)}}

    def action_from_data(self, payload):
        if type(payload) is not dict or set(payload) != {"schema", "data"} or payload["schema"] != ACTION_SCHEMA:
            raise ValueError("invalid action envelope")
        d = payload["data"]
        if type(d) is not dict or set(d) != {"type", "actor", "args"}:
            raise ValueError("invalid action fields")
        if d["type"] not in ACTION_TYPES or type(d["actor"]) is not int or type(d["args"]) is not dict:
            raise ValueError("invalid action values")
        # Canonicalize and ensure JSON-domain arguments.
        try:
            raw = json.dumps(d["args"], sort_keys=True, separators=(",", ":"), allow_nan=False)
        except (TypeError, ValueError) as e:
            raise ValueError("invalid action args") from e
        return Action(d["type"], d["actor"], raw)

    def action_to_name(self, action):
        d = self.action_to_data(action)["data"]
        return d["type"] + " " + str(d["actor"]) + " " + json.dumps(
            d["args"], ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    def name_to_action(self, name):
        try:
            kind, actor, raw = name.split(" ", 2)
            return self.action_from_data({"schema": ACTION_SCHEMA,
                "data": {"type": kind, "actor": int(actor), "args": json.loads(raw)}})
        except Exception as e:
            raise ValueError("invalid action name") from e

    def state_to_data(self, state):
        return {"schema": STATE_SCHEMA, "data": copy.deepcopy(state.data)}

    def state_from_data(self, payload):
        if type(payload) is not dict or set(payload) != {"schema", "data"} or payload["schema"] != STATE_SCHEMA:
            raise ValueError("invalid state envelope")
        d = payload["data"]
        required = {"configuration", "current_player", "active_player", "start_player",
                    "phase", "terminal", "winner", "players", "zones", "depletions",
                    "pending", "turn_number", "chance"}
        if type(d) is not dict or set(d) != required:
            raise ValueError("invalid state fields")
        try:
            json.dumps(d, allow_nan=False)
            n = d["configuration"]["players"]
            if type(n) is not int or n not in (3, 4, 5) or len(d["players"]) != n:
                raise ValueError
            if d["phase"] not in PHASES or type(d["terminal"]) is not bool:
                raise ValueError
            if len(d["zones"]["pending_received"]) != n:
                raise ValueError
            for key in ("deck", "discard", "revealed", "reserve"):
                if any(x not in BEANS for x in d["zones"][key]):
                    raise ValueError
            for p in d["players"]:
                if any(x not in BEANS for x in p["hand"]) or type(p["coins"]) is not int or p["coins"] < 0:
                    raise ValueError
                for f in p["fields"]:
                    if any(x not in BEANS for x in f) or (f and len(set(f)) != 1):
                        raise ValueError
        except (KeyError, TypeError, ValueError, OverflowError) as e:
            raise ValueError("invalid state values") from e
        return GameState(copy.deepcopy(d))

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
                "own_hand": list(d["players"][player]["hand"]),
                "opponents": opponents,
                "fields": copy.deepcopy([p["fields"] for p in d["players"]]),
                "coins": [p["coins"] for p in d["players"]],
                "revealed": list(d["zones"]["revealed"]),
                "deck_size": len(d["zones"]["deck"]),
                "discard_size": len(d["zones"]["discard"]),
                "pending_received_counts": [len(x) for x in d["zones"]["pending_received"]],
                "pending": copy.deepcopy(d["pending"]), "turn_number": d["turn_number"]}
        return {"schema": OBS_SCHEMA, "data": data}

    def render(self, state):
        d = state.data
        lines = [f"Bohnanza | phase={d['phase']} active={d['active_player']} current={d['current_player']}"]
        for p in d["players"]:
            fields = ["-"] + [] if False else [f"{f[0]}×{len(f)}" if f else "empty" for f in p["fields"]]
            lines.append(f"P{p['id']}: {p['coins']} coins; hand {len(p['hand'])}; fields {fields}")
        lines.append(f"revealed={d['zones']['revealed']} deck={len(d['zones']['deck'])} discard={len(d['zones']['discard'])}")
        return "\n".join(lines)
