"""Self-contained BoardBench model of the supplied German Bohnanza rulebook."""
from dataclasses import dataclass
import copy
import itertools
import json
import random
from typing import Any

BEANS = ("gartenbohne", "rote_bohne", "augenbohne", "sojabohne",
         "brechbohne", "saubohne", "feuerbohne", "blaue_bohne")
COUNTS = dict(zip(BEANS, (6, 8, 10, 12, 14, 16, 18, 20)))
THRESHOLDS = {
    "gartenbohne": (None, 2, 3, None), "rote_bohne": (2, 3, 4, 5),
    "augenbohne": (2, 4, 5, 6), "sojabohne": (2, 4, 6, 7),
    "brechbohne": (3, 5, 6, 7), "saubohne": (3, 5, 7, 8),
    "feuerbohne": (3, 6, 8, 9), "blaue_bohne": (4, 6, 8, 10),
}
PHASES = ("plant_first", "plant_second", "reveal", "trade", "trade_response",
          "plant_received", "draw", "terminal")
ACTION_TYPES = ("plant", "harvest", "reveal", "trade_propose", "trade_accept",
                "trade_reject", "end_trade", "draw", "pass")
STATE_SCHEMA = "boardbench/bohnanza-base-2023/state/1"
ACTION_SCHEMA = "boardbench/bohnanza-base-2023/action/1"
OBS_SCHEMA = "boardbench/bohnanza-base-2023/observation/1"


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

    def __deepcopy__(self, memo):
        # apply_action itself makes the isolating copy; validator tuple clones may share safely.
        return self


@dataclass(frozen=True)
class Action:
    type: str
    actor: int
    args_json: str = "{}"

    @property
    def args(self):
        return json.loads(self.args_json)

    def __deepcopy__(self, memo):
        return self


def _action(kind, actor, **args):
    return Action(kind, actor, json.dumps(args, ensure_ascii=False, sort_keys=True,
                                           separators=(",", ":")))


class Game:
    def __init__(self, num_players=None, seed=None):
        self.num_players = 4 if num_players is None else num_players
        if type(self.num_players) is not int or not 3 <= self.num_players <= 5:
            raise ValueError("num_players must be 3, 4, or 5")
        if seed is not None and type(seed) is not int:
            raise TypeError("seed must be an int or None")
        self.seed = seed

    def __deepcopy__(self, memo):
        return self

    def initial_state(self):
        deck = [b for b in BEANS for _ in range(COUNTS[b])]
        random.Random(self.seed).shuffle(deck)
        fields = 3 if self.num_players == 3 else 2
        players = [{"id": p, "hand": [], "fields": [[] for _ in range(fields)], "coins": 0}
                   for p in range(self.num_players)]
        # Deal one card at a time; append preserves each hand's immutable order.
        for _ in range(5):
            for player in players:
                player["hand"].append(deck.pop(0))
        return GameState({"players": self.num_players, "seed": self.seed}, 0, 0, 0,
                         "plant_first", False, players,
                         {"deck": deck, "discard": [], "revealed": [],
                          "pending_received": [[] for _ in players], "reserve": []},
                         0, None, {"seed": self.seed, "draw_index": 0})

    def current_player(self, state):
        return state.current_player

    @staticmethod
    def _plant_fields(state, player, bean):
        return [i for i, f in enumerate(state.players[player]["fields"])
                if not f or f[0] == bean]

    def _harvest_actions(self, state):
        out = []
        for p, player in enumerate(state.players):
            nonempty = [f for f in player["fields"] if f]
            protected = any(len(f) > 1 for f in nonempty)
            for i, field in enumerate(player["fields"]):
                if field and (len(field) > 1 or not protected):
                    out.append(_action("harvest", p, player=p, field=i))
        return out

    def legal_actions(self, state):
        if state.terminal or state.phase == "terminal":
            return []
        p, phase = state.current_player, state.phase
        actions = []
        if phase in ("plant_first", "plant_second"):
            hand = state.players[p]["hand"]
            if hand:
                bean = hand[0]
                actions += [_action("plant", p, field=f, source="hand", index=0, bean=bean)
                            for f in self._plant_fields(state, p, bean)]
            if phase == "plant_second" or not hand:
                actions.append(_action("pass", p))
        elif phase == "reveal":
            actions.append(_action("reveal", p))
        elif phase == "trade":
            actions.append(_action("end_trade", p))
            own_refs = ([{"owner": p, "zone": "hand", "index": i, "bean": b}
                         for i, b in enumerate(state.players[p]["hand"])] +
                        [{"owner": p, "zone": "revealed", "index": i, "bean": b}
                         for i, b in enumerate(state.zones["revealed"])])
            # All finite non-empty subsets are representable, as clarified.
            offered_sets = [c for n in range(1, len(own_refs) + 1)
                            for c in itertools.combinations(own_refs, n)]
            for partner in range(len(state.players)):
                if partner == p:
                    continue
                requested_refs = [{"owner": partner, "zone": "hand", "index": i, "bean": b}
                                  for i, b in enumerate(state.players[partner]["hand"])]
                for offered in offered_sets:
                    actions.append(_action("trade_propose", p, partner=partner,
                                           offered=list(offered), requested=[], gift=True))
                    for n in range(1, len(requested_refs) + 1):
                        for requested in itertools.combinations(requested_refs, n):
                            actions.append(_action("trade_propose", p, partner=partner,
                                                   offered=list(offered), requested=list(requested),
                                                   gift=False))
        elif phase == "trade_response":
            actions = [_action("trade_accept", p), _action("trade_reject", p)]
        elif phase == "plant_received":
            received = state.zones["pending_received"][p]
            if received:
                for i, bean in enumerate(received):
                    actions += [_action("plant", p, field=f, source="received", index=i, bean=bean)
                                for f in self._plant_fields(state, p, bean)]
            else:
                actions.append(_action("pass", p))
        elif phase == "draw":
            actions.append(_action("draw", p))
        # Harvesting is permitted at any time, including outside one's turn.
        actions += self._harvest_actions(state)
        return actions

    @staticmethod
    def _payout(bean, count):
        pay = 0
        for coins, threshold in enumerate(THRESHOLDS[bean], 1):
            if threshold is not None and count >= threshold:
                pay = coins
        return pay

    def _draw_one(self, s, destination, phase2=False):
        if not s.zones["deck"]:
            return False
        destination.append(s.zones["deck"].pop(0))
        s.chance["draw_index"] += 1
        if not s.zones["deck"]:
            s.depletions += 1
            if s.depletions >= 3:
                if not phase2:
                    s.terminal, s.phase = True, "terminal"
                return True
            if s.zones["discard"]:
                seed = s.chance["seed"]
                random.Random(None if seed is None else seed + s.chance["draw_index"]).shuffle(s.zones["discard"])
                s.zones["deck"] = s.zones["discard"]
                s.zones["discard"] = []
        return True

    def apply_action(self, state, action):
        if state.terminal or action.type not in ACTION_TYPES:
            raise ValueError("illegal action")
        s = GameState(**copy.deepcopy(state.__dict__))
        a, p = action.args, action.actor
        if action.type == "harvest":
            field = s.players[a["player"]]["fields"][a["field"]]
            pay = self._payout(field[0], len(field))
            s.players[a["player"]]["coins"] += pay
            s.zones["discard"].extend(field[pay:])
            s.players[a["player"]]["fields"][a["field"]] = []
            return s
        if action.type == "plant":
            source = a["source"]
            if source == "hand":
                bean = s.players[p]["hand"].pop(a["index"])
            elif source == "received":
                bean = s.zones["pending_received"][p].pop(a["index"])
            else:
                bean = s.zones["revealed"].pop(a["index"])
            s.players[p]["fields"][a["field"]].append(bean)
            if s.phase == "plant_first":
                s.phase = "plant_second"
            elif s.phase == "plant_second":
                s.phase = "reveal"
            return s
        if action.type == "pass":
            if s.phase == "plant_first": s.phase = "reveal"
            elif s.phase == "plant_second": s.phase = "reveal"
            elif s.phase == "plant_received": self._advance_received(s)
            return s
        if action.type == "reveal":
            for _ in range(2):
                if not self._draw_one(s, s.zones["revealed"], phase2=True): break
            s.phase = "trade"
            return s
        if action.type == "trade_propose":
            s.pending = {"type": "gift" if a["gift"] else "trade", "actor": p,
                         "partner": a["partner"], "offered": a["offered"],
                         "requested": a["requested"], "awaiting_player": a["partner"]}
            s.phase, s.current_player = "trade_response", a["partner"]
            return s
        if action.type == "trade_reject":
            s.pending = None
            s.phase, s.current_player = "trade", s.active_player
            return s
        if action.type == "trade_accept":
            q = s.pending
            moved_offer = self._remove_refs(s, q["offered"])
            moved_request = self._remove_refs(s, q["requested"])
            s.zones["pending_received"][q["partner"]].extend(moved_offer)
            s.zones["pending_received"][q["actor"]].extend(moved_request)
            s.pending = None
            s.phase, s.current_player = "trade", s.active_player
            return s
        if action.type == "end_trade":
            s.zones["pending_received"][s.active_player].extend(s.zones["revealed"])
            s.zones["revealed"] = []
            s.phase = "plant_received"
            self._set_next_recipient(s, s.active_player)
            return s
        if action.type == "draw":
            for _ in range(3):
                if not self._draw_one(s, s.players[s.active_player]["hand"]): break
                if s.terminal: break
            if not s.terminal:
                nxt = (s.active_player + 1) % len(s.players)
                s.active_player = s.current_player = nxt
                s.phase = "plant_first"
            return s
        raise ValueError("unknown action")

    @staticmethod
    def _remove_refs(s, refs):
        result = []
        groups = {}
        for r in refs: groups.setdefault((r["owner"], r["zone"]), []).append(r)
        for (owner, zone), rs in groups.items():
            cards = s.players[owner]["hand"] if zone == "hand" else s.zones["revealed"]
            for r in sorted(rs, key=lambda x: x["index"], reverse=True):
                result.append((r["index"], cards.pop(r["index"])))
        return [b for _, b in sorted(result)]

    def _set_next_recipient(self, s, start):
        for offset in range(len(s.players)):
            p = (start + offset) % len(s.players)
            if s.zones["pending_received"][p]:
                s.current_player = p
                return
        s.current_player = s.active_player
        if s.depletions >= 3:
            s.phase, s.terminal = "terminal", True
        else:
            s.phase = "draw"

    def _advance_received(self, s):
        start = (s.current_player + 1) % len(s.players)
        self._set_next_recipient(s, start)

    def is_terminal(self, state): return state.terminal

    def returns(self, state):
        if not state.terminal: return [0 for _ in state.players]
        scores = [p["coins"] for p in state.players]
        best = max(scores)
        tied = {i for i, score in enumerate(scores) if score == best}
        winner = next((state.start_player - d) % len(scores) for d in range(1, len(scores) + 1)
                      if (state.start_player - d) % len(scores) in tied)
        return [1 if i == winner else 0 for i in range(len(scores))]

    def render(self, state):
        rows = [f"phase={state.phase} active={state.active_player} current={state.current_player} deck={len(state.zones['deck'])} depletions={state.depletions}"]
        rows += [f"P{p['id']}: hand={len(p['hand'])} fields={p['fields']} coins={p['coins']}" for p in state.players]
        return "\n".join(rows)

    def action_to_name(self, action):
        return f"{action.type}@{action.actor}:{action.args_json}"

    def name_to_action(self, name):
        head, sep, raw = name.partition(":")
        kind, mark, actor_text = head.partition("@")
        if not sep or not mark or kind not in ACTION_TYPES: raise ValueError("unknown action name")
        try:
            actor, args = int(actor_text), json.loads(raw)
        except (ValueError, json.JSONDecodeError) as exc:
            raise ValueError("invalid action name") from exc
        return self.action_from_data({"schema": ACTION_SCHEMA,
                                      "data": {"type": kind, "actor": actor, "args": args}})

    def state_to_data(self, s):
        return {"schema": STATE_SCHEMA, "data": copy.deepcopy(s.__dict__)}

    def state_from_data(self, payload):
        d = self._envelope(payload, STATE_SCHEMA)
        required = {"configuration", "current_player", "active_player", "start_player", "phase", "terminal", "players", "zones", "depletions", "pending", "chance"}
        if set(d) != required: raise ValueError("invalid state fields")
        self._validate_state(d)
        return GameState(**copy.deepcopy(d))

    def action_to_data(self, action):
        return {"schema": ACTION_SCHEMA, "data": {"type": action.type, "actor": action.actor,
                                                    "args": copy.deepcopy(action.args)}}

    def action_from_data(self, payload):
        d = self._envelope(payload, ACTION_SCHEMA)
        if set(d) != {"type", "actor", "args"} or d["type"] not in ACTION_TYPES or type(d["actor"]) is not int or not isinstance(d["args"], dict):
            raise ValueError("invalid action")
        # Strictly validate by stable per-type key sets.
        keys = {"plant": {"field","source","index","bean"}, "harvest": {"player","field"},
                "reveal": set(), "trade_propose": {"partner","offered","requested","gift"},
                "trade_accept": set(), "trade_reject": set(), "end_trade": set(),
                "draw": set(), "pass": set()}
        if set(d["args"]) != keys[d["type"]]: raise ValueError("invalid action arguments")
        a = d["args"]
        if d["type"] == "plant" and (a["source"] not in ("hand","revealed","received") or a["bean"] not in BEANS or type(a["field"]) is not int or type(a["index"]) is not int):
            raise ValueError("invalid plant action")
        if d["type"] == "harvest" and any(type(a[x]) is not int for x in ("player","field")):
            raise ValueError("invalid harvest action")
        if d["type"] == "trade_propose":
            if type(a["partner"]) is not int or type(a["gift"]) is not bool or not isinstance(a["offered"],list) or not isinstance(a["requested"],list): raise ValueError("invalid trade action")
            for ref in a["offered"] + a["requested"]:
                if not self._valid_ref(ref): raise ValueError("invalid card reference")
        return _action(d["type"], d["actor"], **copy.deepcopy(d["args"]))

    @staticmethod
    def _valid_ref(ref):
        return (isinstance(ref,dict) and set(ref) == {"owner","zone","index","bean"}
                and type(ref["owner"]) is int and type(ref["index"]) is int
                and ref["zone"] in ("hand","revealed") and ref["bean"] in BEANS)

    def observation_to_data(self, s, player):
        if type(player) is not int or not 0 <= player < len(s.players): raise ValueError("invalid player")
        pending = copy.deepcopy(s.pending)
        data = {"player": player, "current_player": s.current_player, "active_player": s.active_player,
                "phase": s.phase, "terminal": s.terminal,
                "own_hand": copy.deepcopy(s.players[player]["hand"]),
                "opponents": [{"id": p["id"], "hand_size": len(p["hand"])} for p in s.players if p["id"] != player],
                "fields": copy.deepcopy([p["fields"] for p in s.players]),
                "coins": [p["coins"] for p in s.players], "revealed": copy.deepcopy(s.zones["revealed"]),
                "deck_size": len(s.zones["deck"]), "discard_size": len(s.zones["discard"]),
                "pending": pending}
        return {"schema": OBS_SCHEMA, "data": data}

    @staticmethod
    def _envelope(payload, schema):
        if not isinstance(payload, dict) or set(payload) != {"schema", "data"} or payload.get("schema") != schema or not isinstance(payload.get("data"), dict):
            raise ValueError("invalid envelope")
        return payload["data"]

    @staticmethod
    def _validate_state(d):
        if d["phase"] not in PHASES or type(d["terminal"]) is not bool: raise ValueError("invalid phase")
        if not isinstance(d["configuration"],dict) or set(d["configuration"]) != {"players","seed"} or (d["configuration"]["seed"] is not None and type(d["configuration"]["seed"]) is not int): raise ValueError("invalid configuration")
        n = d["configuration"]["players"]
        if type(n) is not int or not 3 <= n <= 5 or len(d["players"]) != n: raise ValueError("invalid players")
        for key in ("current_player","active_player","start_player"):
            if type(d[key]) is not int or not 0 <= d[key] < n: raise ValueError("invalid player index")
        for p, player in enumerate(d["players"]):
            if set(player) != {"id","hand","fields","coins"} or player["id"] != p or type(player["coins"]) is not int or player["coins"] < 0: raise ValueError("invalid player data")
            if not isinstance(player["fields"], list) or not all(isinstance(f,list) for f in player["fields"]): raise ValueError("invalid fields")
        zones = d["zones"]
        if not isinstance(zones, dict) or set(zones) != {"deck","discard","revealed","pending_received","reserve"} or len(zones["pending_received"]) != n: raise ValueError("invalid zones")
        card_lists = [p["hand"] for p in d["players"]] + [f for p in d["players"] for f in p["fields"]] + [zones[x] for x in ("deck","discard","revealed","reserve")] + zones["pending_received"]
        if any(not isinstance(x,list) or any(b not in BEANS for b in x) for x in card_lists): raise ValueError("invalid cards")
        if type(d["depletions"]) is not int or d["depletions"] < 0: raise ValueError("invalid depletions")
        if (not isinstance(d["chance"],dict) or set(d["chance"]) != {"seed","draw_index"}
                or (d["chance"]["seed"] is not None and type(d["chance"]["seed"]) is not int)
                or type(d["chance"]["draw_index"]) is not int or d["chance"]["draw_index"] < 0): raise ValueError("invalid chance")
        q = d["pending"]
        if q is not None:
            if not isinstance(q,dict) or set(q) != {"type","actor","partner","offered","requested","awaiting_player"} or q["type"] not in ("trade","gift"): raise ValueError("invalid pending decision")
            if any(type(q[x]) is not int or not 0 <= q[x] < n for x in ("actor","partner","awaiting_player")): raise ValueError("invalid pending player")
            if not isinstance(q["offered"],list) or not isinstance(q["requested"],list) or any(not Game._valid_ref(r) for r in q["offered"] + q["requested"]): raise ValueError("invalid pending references")
