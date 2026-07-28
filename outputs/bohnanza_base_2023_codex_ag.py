"""Self-contained Bohnanza base game model, from the supplied German rules (v5.4)."""
from __future__ import annotations

import copy
import json
import random
from typing import Any

BEANS = ("gartenbohne", "rote_bohne", "augenbohne", "sojabohne",
         "brechbohne", "saubohne", "feuerbohne", "blaue_bohne")
COUNTS = dict(zip(BEANS, (6, 8, 10, 12, 14, 16, 18, 20)))
# The thresholds printed on the eight supplied bean cards (coins 1..4).
METERS = {
    "gartenbohne": (2, 3, 4, 5), "rote_bohne": (2, 3, 4, 5),
    "augenbohne": (2, 4, 5, 6), "sojabohne": (2, 3, 5, 7),
    "brechbohne": (3, 5, 6, 7), "saubohne": (3, 5, 7, 8),
    "feuerbohne": (3, 6, 8, 9), "blaue_bohne": (4, 6, 8, 10),
}
PHASES = ("plant_first", "plant_second", "reveal", "trade",
          "trade_response", "plant_received", "draw", "terminal")
STATE_SCHEMA = "boardbench/bohnanza-base-2023/state/2"
ACTION_SCHEMA = "boardbench/bohnanza-base-2023/action/2"
OBS_SCHEMA = "boardbench/bohnanza-base-2023/observation/2"


class GameState:
    FIELDS = ("configuration", "current_player", "active_player", "start_player",
              "phase", "terminal", "winner", "players", "zones", "depletions",
              "pending", "turn_number", "chance")

    def __init__(self, *values, **named):
        if values:
            if named or len(values) != len(self.FIELDS):
                raise TypeError("invalid GameState arguments")
            named = dict(zip(self.FIELDS, values))
        if set(named) != set(self.FIELDS):
            raise TypeError("invalid GameState fields")
        self.__dict__.update(named)

    def __eq__(self, other):
        return isinstance(other, GameState) and self.__dict__ == other.__dict__


class Action:
    __slots__ = ("type", "actor", "args_json")

    def __init__(self, type, actor, args_json="{}"):
        self.type, self.actor, self.args_json = type, actor, args_json

    def __eq__(self, other):
        return (isinstance(other, Action) and self.type == other.type and
                self.actor == other.actor and self.args_json == other.args_json)

    def __hash__(self):
        return hash((self.type, self.actor, self.args_json))

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
            raise ValueError("seed must be an integer or None")
        self.seed = seed

    def initial_state(self):
        rng = random.Random(self.seed)
        deck = [b for b in BEANS for _ in range(COUNTS[b])]
        rng.shuffle(deck)
        start = rng.randrange(self.num_players)
        hands = [[] for _ in range(self.num_players)]
        for p in range(self.num_players):
            for _ in range(5):
                hands[p].append(deck.pop())
        nf = 3 if self.num_players == 3 else 2
        players = [{"id": p, "hand": hands[p], "fields": [[] for _ in range(nf)],
                    "coins": 0} for p in range(self.num_players)]
        return GameState(
            {"players": self.num_players, "seed": self.seed, "variant": "base_2023"},
            start, start, start, "plant_first", False, None, players,
            {"deck": deck, "discard": [], "revealed": [],
             "pending_received": [[] for _ in players], "reserve": []},
            0, None, 0, {"seed": self.seed, "counter": 0})

    def current_player(self, state):
        return state.current_player

    def is_terminal(self, state):
        return state.terminal

    def returns(self, state):
        if not state.terminal:
            return [0 for _ in state.players]
        return [1 if p["id"] == state.winner else 0 for p in state.players]

    @staticmethod
    def _plant_actions(s, actor, source, cards):
        if not cards:
            return []
        indexes = [0] if source == "hand" else range(len(cards))
        result = []
        for i in indexes:
            bean = cards[i]
            for f, field in enumerate(s.players[actor]["fields"]):
                if not field or field[0] == bean:
                    result.append(_action("plant", actor, field=f, source=source,
                                          index=i, bean=bean))
        return result

    @staticmethod
    def _harvest_actions(s):
        out = []
        for p in s.players:
            sizes = [len(f) for f in p["fields"]]
            for i, size in enumerate(sizes):
                if size and (size > 1 or not any(x > 1 for x in sizes)):
                    out.append(_action("harvest", p["id"], player=p["id"], field=i))
        return out

    def legal_actions(self, s):
        if s.terminal:
            return []
        a = self._harvest_actions(s)
        p = s.active_player
        if s.phase == "plant_first":
            if s.players[p]["hand"]:
                a += self._plant_actions(s, p, "hand", s.players[p]["hand"])
            else:
                a.append(_action("pass", p))
        elif s.phase == "plant_second":
            a += self._plant_actions(s, p, "hand", s.players[p]["hand"])
            a.append(_action("pass", p))
        elif s.phase == "reveal":
            a.append(_action("reveal", p))
        elif s.phase == "trade":
            a += self._trade_actions(s)
            a.append(_action("end_trade", p))
        elif s.phase == "trade_response":
            q = s.pending["awaiting_player"]
            a += [_action("trade_accept", q), _action("trade_reject", q)]
        elif s.phase == "plant_received":
            for owner, cards in enumerate(s.zones["pending_received"]):
                a += self._plant_actions(s, owner, "received", cards)
            a += self._plant_actions(s, p, "revealed", s.zones["revealed"])
            if not s.zones["revealed"] and not any(s.zones["pending_received"]):
                a.append(_action("pass", p))
        elif s.phase == "draw":
            a.append(_action("draw", p))
        return a

    def _trade_actions(self, s):
        p = s.active_player
        offered = ([{"owner": p, "zone": "hand", "index": i, "bean": b}
                    for i, b in enumerate(s.players[p]["hand"])] +
                   [{"owner": p, "zone": "revealed", "index": i, "bean": b}
                    for i, b in enumerate(s.zones["revealed"])])
        out = []
        # Single-card proposals are sufficient to express successive source-legal deals.
        for partner in range(len(s.players)):
            if partner == p:
                continue
            requested = [{"owner": partner, "zone": "hand", "index": i, "bean": b}
                         for i, b in enumerate(s.players[partner]["hand"])]
            for x in offered:
                out.append(_action("trade_propose", p, partner=partner,
                                   offered=[x], requested=[], gift=True))
                for y in requested:
                    out.append(_action("trade_propose", p, partner=partner,
                                       offered=[x], requested=[y], gift=False))
        return out

    def apply_action(self, state, action):
        if action not in self.legal_actions(state):
            raise ValueError("illegal action")
        s = copy.deepcopy(state)
        t, actor, x = action.type, action.actor, action.args
        if t == "harvest":
            self._harvest(s, x["player"], x["field"])
        elif t == "plant":
            self._plant(s, actor, x)
        elif t == "pass":
            if s.phase == "plant_first":
                s.phase = "reveal"
            elif s.phase == "plant_second":
                s.phase = "reveal"
            elif s.phase == "plant_received":
                s.phase = "draw"
        elif t == "reveal":
            for _ in range(2):
                card = self._draw_one(s)
                if card is not None:
                    s.zones["revealed"].append(card)
            s.phase = "trade"
        elif t == "trade_propose":
            s.pending = {"type": "gift" if x["gift"] else "trade", "actor": actor,
                         "partner": x["partner"], "offered": x["offered"],
                         "requested": x["requested"], "awaiting_player": x["partner"]}
            s.current_player = x["partner"]
            s.phase = "trade_response"
        elif t == "trade_reject":
            s.pending = None
            s.current_player = s.active_player
            s.phase = "trade"
        elif t == "trade_accept":
            self._accept(s)
            s.pending = None
            s.current_player = s.active_player
            s.phase = "trade"
        elif t == "end_trade":
            s.phase = "plant_received"
        elif t == "draw":
            for _ in range(3):
                card = self._draw_one(s)
                if card is not None:
                    s.players[s.active_player]["hand"].append(card)
            if s.depletions >= 3:
                self._finish(s)
            else:
                s.active_player = (s.active_player + 1) % len(s.players)
                s.current_player = s.active_player
                s.turn_number += 1
                s.phase = "plant_first"
        if not s.terminal:
            s.current_player = self._decision_player(s)
        return s

    def _decision_player(self, s):
        if s.phase == "trade_response":
            return s.pending["awaiting_player"]
        if s.phase == "plant_received":
            for p, cards in enumerate(s.zones["pending_received"]):
                if cards:
                    return p
        return s.active_player

    def _plant(self, s, actor, x):
        if x["source"] == "hand":
            card = s.players[actor]["hand"].pop(0)
            s.players[actor]["fields"][x["field"]].append(card)
            s.phase = "plant_second" if s.phase == "plant_first" else "reveal"
        elif x["source"] == "revealed":
            card = s.zones["revealed"].pop(x["index"])
            s.players[actor]["fields"][x["field"]].append(card)
        else:
            card = s.zones["pending_received"][actor].pop(x["index"])
            s.players[actor]["fields"][x["field"]].append(card)

    def _harvest(self, s, player, field):
        cards = s.players[player]["fields"][field]
        n = len(cards)
        coins = sum(n >= threshold for threshold in METERS[cards[0]])
        s.players[player]["coins"] += coins
        s.zones["discard"].extend(cards[:-coins] if coins else cards)
        s.players[player]["fields"][field] = []

    def _accept(self, s):
        q = s.pending
        transfers = [(r, q["partner"]) for r in q["offered"]]
        transfers += [(r, q["actor"]) for r in q["requested"]]
        removed = []
        for ref, recipient in sorted(transfers, key=lambda z: z[0]["index"],
                                     reverse=True):
            zone = (s.players[ref["owner"]]["hand"] if ref["zone"] == "hand"
                    else s.zones["revealed"])
            if ref["index"] >= len(zone) or zone[ref["index"]] != ref["bean"]:
                raise ValueError("stale trade reference")
            removed.append((zone.pop(ref["index"]), recipient))
        for bean, recipient in removed:
            s.zones["pending_received"][recipient].append(bean)

    def _draw_one(self, s):
        if not s.zones["deck"]:
            if s.depletions >= 3 or not s.zones["discard"]:
                return None
            cards = s.zones["discard"]
            s.zones["discard"] = []
            rng = random.Random(f"{s.chance['seed']}:{s.chance['counter']}")
            rng.shuffle(cards)
            s.chance["counter"] += 1
            s.zones["deck"] = cards
        card = s.zones["deck"].pop()
        if not s.zones["deck"]:
            s.depletions += 1
        return card

    def _finish(self, s):
        for p in s.players:
            for i in range(len(p["fields"])):
                if p["fields"][i]:
                    self._harvest(s, p["id"], i)
        best = max(p["coins"] for p in s.players)
        tied = {p["id"] for p in s.players if p["coins"] == best}
        order = [(s.start_player + i) % len(s.players) for i in range(len(s.players))]
        s.winner = next(p for p in reversed(order) if p in tied)
        s.phase, s.terminal, s.pending = "terminal", True, None

    def action_to_name(self, action):
        return f"{action.type}|actor={action.actor}|args={action.args_json}"

    def name_to_action(self, name):
        try:
            kind, actor, args = name.split("|", 2)
            return Action(kind, int(actor.split("=", 1)[1]), args.split("=", 1)[1])
        except Exception as exc:
            raise ValueError("invalid action name") from exc

    def action_to_data(self, action):
        if not isinstance(action, Action):
            raise ValueError("invalid action")
        return {"schema": ACTION_SCHEMA, "data": {"type": action.type,
                "actor": action.actor, "args": copy.deepcopy(action.args)}}

    def action_from_data(self, payload):
        if not isinstance(payload, dict) or set(payload) != {"schema", "data"} or payload["schema"] != ACTION_SCHEMA:
            raise ValueError("invalid action envelope")
        d = payload["data"]
        if not isinstance(d, dict) or set(d) != {"type", "actor", "args"}:
            raise ValueError("invalid action data")
        if d["type"] not in ("plant", "harvest", "reveal", "trade_propose",
                             "trade_accept", "trade_reject", "end_trade", "draw", "pass"):
            raise ValueError("unknown action type")
        if type(d["actor"]) is not int or not isinstance(d["args"], dict):
            raise ValueError("invalid action fields")
        return _action(d["type"], d["actor"], **d["args"])

    def state_to_data(self, state):
        return {"schema": STATE_SCHEMA, "data": copy.deepcopy(state.__dict__)}

    def state_from_data(self, payload):
        if not isinstance(payload, dict) or set(payload) != {"schema", "data"} or payload["schema"] != STATE_SCHEMA:
            raise ValueError("invalid state envelope")
        d = payload["data"]
        required = set(GameState.FIELDS)
        if not isinstance(d, dict) or set(d) != required:
            raise ValueError("invalid state fields")
        self._validate_state(d)
        return GameState(**copy.deepcopy(d))

    def _validate_state(self, d):
        c = d["configuration"]
        if not isinstance(c, dict) or set(c) != {"players", "seed", "variant"} or c["variant"] != "base_2023" or c["players"] not in (3, 4, 5):
            raise ValueError("invalid configuration")
        n = c["players"]
        if len(d["players"]) != n or d["phase"] not in PHASES or type(d["terminal"]) is not bool:
            raise ValueError("invalid state")
        if any(type(d[k]) is not int for k in ("current_player", "active_player", "start_player", "depletions", "turn_number")):
            raise ValueError("invalid integer field")
        if not all(0 <= d[k] < n for k in ("current_player", "active_player", "start_player")) or not 0 <= d["depletions"] <= 3:
            raise ValueError("integer out of range")
        if not isinstance(d["zones"], dict) or set(d["zones"]) != {"deck", "discard", "revealed", "pending_received", "reserve"}:
            raise ValueError("invalid zones")
        if len(d["zones"]["pending_received"]) != n:
            raise ValueError("invalid received zones")
        cards = []
        for p, player in enumerate(d["players"]):
            if set(player) != {"id", "hand", "fields", "coins"} or player["id"] != p or type(player["coins"]) is not int or player["coins"] < 0:
                raise ValueError("invalid player")
            cards += player["hand"]
            for field in player["fields"]:
                if field and any(b != field[0] for b in field):
                    raise ValueError("mixed field")
                cards += field
        for z in ("deck", "discard", "revealed", "reserve"):
            cards += d["zones"][z]
        for z in d["zones"]["pending_received"]:
            cards += z
        if any(b not in BEANS for b in cards):
            raise ValueError("unknown bean")
        if len(cards) + sum(p["coins"] for p in d["players"]) != 104:
            raise ValueError("inventory must total 104")
        if not isinstance(d["chance"], dict) or set(d["chance"]) != {"seed", "counter"}:
            raise ValueError("invalid chance")

    def observation_to_data(self, s, player):
        if type(player) is not int or not 0 <= player < len(s.players):
            raise ValueError("invalid observer")
        opponents = [{"id": p["id"], "hand_size": len(p["hand"]),
                      "front_card": p["hand"][0] if p["hand"] else None}
                     for p in s.players if p["id"] != player]
        data = {"player": player, "current_player": s.current_player,
                "active_player": s.active_player, "start_player": s.start_player,
                "phase": s.phase, "terminal": s.terminal, "winner": s.winner,
                "own_hand": copy.deepcopy(s.players[player]["hand"]),
                "opponents": opponents,
                "fields": copy.deepcopy([p["fields"] for p in s.players]),
                "coins": [p["coins"] for p in s.players],
                "revealed": copy.deepcopy(s.zones["revealed"]),
                "deck_size": len(s.zones["deck"]),
                "discard_size": len(s.zones["discard"]),
                "pending_received_counts": [len(x) for x in s.zones["pending_received"]],
                "pending": copy.deepcopy(s.pending), "turn_number": s.turn_number}
        return {"schema": OBS_SCHEMA, "data": data}

    def render(self, s):
        return (f"Bohnanza turn={s.turn_number} phase={s.phase} "
                f"active={s.active_player} deck={len(s.zones['deck'])}\n" +
                "\n".join(f"P{p['id']}: coins={p['coins']} hand={len(p['hand'])} "
                          f"fields={p['fields']}" for p in s.players))
