"""Self-contained implementation of the supplied German 6 nimmt! rulebook."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, NamedTuple


STATE_SCHEMA = "boardbench/six-nimmt/state/2"
ACTION_SCHEMA = "boardbench/six-nimmt/action/2"
OBS_SCHEMA = "boardbench/six-nimmt/observation/2"


class Action(NamedTuple):
    type: str
    actor: int
    arg: int


class GameState:
    def __init__(self, data: dict[str, Any]):
        self.data = data


def _bullheads(card: int) -> int:
    if card == 55:
        return 7
    if card % 11 == 0:
        return 5
    if card % 10 == 0:
        return 3
    if card % 5 == 0:
        return 2
    return 1


class Game:
    def __init__(self, num_players: int | None = None, seed: int | None = None):
        self.num_players = 2 if num_players is None else num_players
        if type(self.num_players) is not int or self.num_players not in range(2, 11):
            raise ValueError("num_players must be one of 2..10")
        if seed is not None and type(seed) is not int:
            raise ValueError("seed must be an integer or None")
        self.seed = seed

    @staticmethod
    def _shuffle(cards: list[int], chance: dict[str, Any]) -> None:
        # Small, fully serializable deterministic generator.
        x = chance["rng_state"]["state"]
        for i in range(len(cards) - 1, 0, -1):
            x = (6364136223846793005 * x + 1442695040888963407) & ((1 << 64) - 1)
            j = x % (i + 1)
            cards[i], cards[j] = cards[j], cards[i]
        chance["rng_state"]["state"] = x
        chance["shuffle_index"] += 1

    def _deal(self, data: dict[str, Any]) -> None:
        deck = list(range(1, 105))
        self._shuffle(deck, data["chance"])
        for p in data["players"]:
            p["hand"] = sorted(deck[:10])
            del deck[:10]
            p["captured"] = []
            p["game_bullheads"] = 0
            p["committed_card"] = None
        data["zones"] = {
            "rows": [[deck.pop(0)] for _ in range(4)],
            "reserve": deck,
            "revealed": [],
            "resolved": [],
        }
        data.update(round_number=1, phase="commit", current_player=0,
                    pending=None, terminal=False, winners=[])

    def initial_state(self) -> GameState:
        initial_seed = 0 if self.seed is None else self.seed
        data = {
            "configuration": {"players": self.num_players, "seed": self.seed,
                              "variant": "base", "match_target": 66},
            "game_number": 1, "round_number": 1, "phase": "commit",
            "current_player": 0,
            "players": [{"id": i, "hand": [], "captured": [],
                         "game_bullheads": 0, "total_bullheads": 0,
                         "committed_card": None} for i in range(self.num_players)],
            "card_bullheads": {str(c): _bullheads(c) for c in range(1, 105)},
            "zones": {}, "pending": None, "terminal": False, "winners": [],
            "chance": {"seed": initial_seed, "shuffle_index": 0,
                       "rng_state": {"state": initial_seed & ((1 << 64) - 1)}},
        }
        self._deal(data)
        return GameState(data)

    def current_player(self, state: GameState) -> int | None:
        return state.data["current_player"]

    def legal_actions(self, state: GameState) -> list[Action]:
        d = state.data
        if d["terminal"] or d["phase"] == "terminal":
            return []
        actor = d["current_player"]
        if d["phase"] == "commit" and actor is not None:
            return [Action("commit_card", actor, c) for c in d["players"][actor]["hand"]]
        if d["phase"] == "choose_row" and actor is not None:
            return [Action("choose_row", actor, r) for r in range(4)]
        return []

    def _capture(self, d: dict[str, Any], player: int, row: int) -> list[int]:
        taken = d["zones"]["rows"][row]
        d["players"][player]["captured"].extend(taken)
        d["players"][player]["game_bullheads"] += sum(_bullheads(c) for c in taken)
        return taken

    def _continue_resolution(self, d: dict[str, Any], remaining: list[dict[str, int]]) -> None:
        while remaining:
            item = remaining.pop(0)
            player, card = item["player"], item["card"]
            eligible = [(card - row[-1], r) for r, row in enumerate(d["zones"]["rows"])
                        if row[-1] < card]
            if not eligible:
                d["phase"] = "choose_row"
                d["current_player"] = player
                d["pending"] = {"type": "low_choice", "player": player,
                                "card": card, "remaining": remaining}
                return
            row = min(eligible)[1]
            captured: list[int] = []
            if len(d["zones"]["rows"][row]) == 5:
                captured = self._capture(d, player, row)
                d["zones"]["rows"][row] = []
            d["zones"]["rows"][row].append(card)
            d["zones"]["resolved"].append({"player": player, "card": card,
                                           "row": row, "captured": captured})
        self._finish_round(d)

    def _finish_round(self, d: dict[str, Any]) -> None:
        for p in d["players"]:
            p["committed_card"] = None
        if d["round_number"] < 10:
            d["round_number"] += 1
            d["phase"], d["current_player"], d["pending"] = "commit", 0, None
            d["zones"]["revealed"] = []
            d["zones"]["resolved"] = []
            return
        for p in d["players"]:
            p["total_bullheads"] += p["game_bullheads"]
        if any(p["total_bullheads"] > d["configuration"]["match_target"] for p in d["players"]):
            best = min(p["total_bullheads"] for p in d["players"])
            d["winners"] = [p["id"] for p in d["players"] if p["total_bullheads"] == best]
            d["phase"], d["current_player"], d["terminal"] = "terminal", None, True
            d["pending"] = None
        else:
            d["game_number"] += 1
            self._deal(d)

    def apply_action(self, state: GameState, action: Action) -> GameState:
        if action not in self.legal_actions(state):
            raise ValueError("illegal action")
        out = GameState(deepcopy(state.data))
        d = out.data
        if action.type == "commit_card":
            p = d["players"][action.actor]
            p["hand"].remove(action.arg)
            p["committed_card"] = action.arg
            uncommitted = [x["id"] for x in d["players"] if x["committed_card"] is None]
            if uncommitted:
                d["current_player"] = uncommitted[0]
            else:
                revealed = sorted(({"player": p["id"], "card": p["committed_card"]}
                                   for p in d["players"]), key=lambda x: x["card"])
                d["zones"]["revealed"] = deepcopy(revealed)
                d["zones"]["resolved"] = []
                self._continue_resolution(d, revealed)
        else:
            pending = d["pending"]
            captured = self._capture(d, action.actor, action.arg)
            d["zones"]["rows"][action.arg] = [pending["card"]]
            d["zones"]["resolved"].append({"player": action.actor, "card": pending["card"],
                                           "row": action.arg, "captured": captured})
            remaining = pending["remaining"]
            d["pending"] = None
            self._continue_resolution(d, remaining)
        return out

    def is_terminal(self, state: GameState) -> bool:
        return bool(state.data["terminal"])

    def returns(self, state: GameState) -> list[int]:
        if not self.is_terminal(state):
            return [0] * len(state.data["players"])
        return [1 if i in state.data["winners"] else -1
                for i in range(len(state.data["players"]))]

    def render(self, state: GameState) -> str:
        d = state.data
        rows = "\n".join(f"{i}: {' '.join(map(str, row))}" for i, row in enumerate(d["zones"]["rows"]))
        scores = ", ".join(f"P{p['id']}={p['total_bullheads']}+{p['game_bullheads']}"
                           for p in d["players"])
        return f"Game {d['game_number']} round {d['round_number']} ({d['phase']})\n{rows}\n{scores}"

    def action_to_name(self, action: Action) -> str:
        if action.type == "commit_card":
            return f"Player {action.actor}: play card {action.arg}"
        return f"Player {action.actor}: choose row {action.arg + 1} (top-to-bottom)"

    def name_to_action(self, name: str) -> Action:
        import re
        m = re.fullmatch(r"Player (\d+): play card (\d+)", name)
        if m:
            return Action("commit_card", int(m[1]), int(m[2]))
        m = re.fullmatch(r"Player (\d+): choose row ([1-4]) \(top-to-bottom\)", name)
        if m:
            return Action("choose_row", int(m[1]), int(m[2]) - 1)
        raise ValueError("unknown action name")

    def action_to_data(self, action: Action) -> dict[str, Any]:
        if type(action) is not Action or type(action.actor) is not int or not 0 <= action.actor < self.num_players:
            raise ValueError("invalid action")
        if action.type == "commit_card" and type(action.arg) is int and 1 <= action.arg <= 104:
            args = {"card": action.arg}
        elif action.type == "choose_row" and type(action.arg) is int and 0 <= action.arg <= 3:
            args = {"row": action.arg}
        else:
            raise ValueError("invalid action")
        return {"schema": ACTION_SCHEMA, "data": {"type": action.type,
                "actor": action.actor, "args": args}}

    def action_from_data(self, payload: dict[str, Any]) -> Action:
        if type(payload) is not dict or set(payload) != {"schema", "data"} or payload.get("schema") != ACTION_SCHEMA:
            raise ValueError("invalid action envelope")
        d = payload["data"]
        if (type(d) is not dict or set(d) != {"type", "actor", "args"}
                or type(d["type"]) is not str or type(d["actor"]) is not int
                or not 0 <= d["actor"] < self.num_players):
            raise ValueError("invalid action data")
        if d["type"] == "commit_card" and type(d["args"]) is dict and set(d["args"]) == {"card"} and type(d["args"]["card"]) is int and 1 <= d["args"]["card"] <= 104:
            return Action("commit_card", d["actor"], d["args"]["card"])
        if d["type"] == "choose_row" and type(d["args"]) is dict and set(d["args"]) == {"row"} and type(d["args"]["row"]) is int and 0 <= d["args"]["row"] <= 3:
            return Action("choose_row", d["actor"], d["args"]["row"])
        raise ValueError("invalid action data")

    def state_to_data(self, state: GameState) -> dict[str, Any]:
        return {"schema": STATE_SCHEMA, "data": deepcopy(state.data)}

    def state_from_data(self, payload: dict[str, Any]) -> GameState:
        if type(payload) is not dict or set(payload) != {"schema", "data"} or payload.get("schema") != STATE_SCHEMA:
            raise ValueError("invalid state envelope")
        d = payload["data"]
        required = {"configuration", "game_number", "round_number", "phase", "current_player",
                    "players", "card_bullheads", "zones", "pending", "terminal", "winners", "chance"}
        if type(d) is not dict or set(d) != required:
            raise ValueError("invalid state fields")
        def fail() -> None:
            raise ValueError("invalid state values")

        def integer(value: Any, low: int | None = None, high: int | None = None) -> bool:
            return (type(value) is int and (low is None or value >= low)
                    and (high is None or value <= high))

        def exact(obj: Any, keys: set[str]) -> bool:
            return type(obj) is dict and set(obj) == keys and all(type(k) is str for k in obj)

        def json_domain(value: Any) -> bool:
            if value is None or type(value) in (bool, int, str):
                return True
            if type(value) is float:
                import math
                return math.isfinite(value)
            if type(value) is list:
                return all(json_domain(x) for x in value)
            if type(value) is dict:
                return all(type(k) is str and json_domain(v) for k, v in value.items())
            return False

        def card(value: Any) -> bool:
            return type(value) is int

        def card_list(value: Any) -> bool:
            return type(value) is list and all(card(x) for x in value)

        def play_ref(value: Any) -> bool:
            return (exact(value, {"player", "card"}) and type(value["player"]) is int
                    and card(value["card"]))

        if not json_domain(payload):
            fail()
        cfg = d["configuration"]
        if not exact(cfg, {"players", "seed", "variant", "match_target"}):
            fail()
        count = cfg["players"]
        if (not integer(count, 2, 10) or (cfg["seed"] is not None and type(cfg["seed"]) is not int)
                or cfg["variant"] != "base" or type(cfg["match_target"]) is not int):
            fail()
        if (not integer(d["game_number"], 1) or not integer(d["round_number"], 1, 10)
                or d["phase"] not in ("commit", "choose_row", "terminal")
                or type(d["terminal"]) is not bool):
            fail()
        if d["current_player"] is not None and type(d["current_player"]) is not int:
            fail()

        players = d["players"]
        player_keys = {"id", "hand", "captured", "game_bullheads", "total_bullheads", "committed_card"}
        if type(players) is not list:
            fail()
        for player in players:
            if (not exact(player, player_keys) or type(player["id"]) is not int
                    or not card_list(player["hand"]) or not card_list(player["captured"])
                    or type(player["game_bullheads"]) is not int
                    or type(player["total_bullheads"]) is not int
                    or (player["committed_card"] is not None and not card(player["committed_card"]))):
                fail()

        if (type(d["card_bullheads"]) is not dict
                or not all(type(k) is str and type(v) is int
                           for k, v in d["card_bullheads"].items())):
            fail()
        zones = d["zones"]
        if not exact(zones, {"rows", "reserve", "revealed", "resolved"}):
            fail()
        if (type(zones["rows"]) is not list
                or not all(card_list(row) for row in zones["rows"])
                or not card_list(zones["reserve"])
                or type(zones["revealed"]) is not list
                or not all(play_ref(x) for x in zones["revealed"])
                or type(zones["resolved"]) is not list):
            fail()
        resolved_keys = {"player", "card", "row", "captured"}
        for item in zones["resolved"]:
            if (not exact(item, resolved_keys) or type(item["player"]) is not int
                    or not card(item["card"]) or not integer(item["row"], 0, 3)
                    or not card_list(item["captured"])):
                fail()

        pending = d["pending"]
        if pending is not None:
            if (not exact(pending, {"type", "player", "card", "remaining"})
                    or pending["type"] != "low_choice" or type(pending["player"]) is not int
                    or not card(pending["card"]) or type(pending["remaining"]) is not list
                    or not all(play_ref(x) for x in pending["remaining"])):
                fail()
        if type(d["winners"]) is not list or not all(type(x) is int for x in d["winners"]):
            fail()

        chance = d["chance"]
        if (not exact(chance, {"seed", "shuffle_index", "rng_state"})
                or type(chance["seed"]) is not int or type(chance["shuffle_index"]) is not int
                or not exact(chance["rng_state"], {"state"})
                or type(chance["rng_state"]["state"]) is not int):
            fail()
        return GameState(deepcopy(d))

    def observation_to_data(self, state: GameState, player: int) -> dict[str, Any]:
        d = state.data
        if type(player) is not int or not 0 <= player < len(d["players"]):
            raise ValueError("invalid player")
        own = d["players"][player]
        resolved = [{"player": x["player"], "card": x["card"], "row": x["row"],
                     "captured_count": len(x["captured"]),
                     "captured_bullheads": sum(_bullheads(c) for c in x["captured"])}
                    for x in d["zones"]["resolved"]]
        pending = deepcopy(d["pending"])
        data = {
            "player": player,
            "configuration": {k: d["configuration"][k] for k in ("players", "variant", "match_target")},
            "game_number": d["game_number"], "round_number": d["round_number"],
            "phase": d["phase"], "current_player": d["current_player"],
            "own_hand": deepcopy(own["hand"]), "own_captured": deepcopy(own["captured"]),
            "players": [{"id": p["id"], "hand_size": len(p["hand"]),
                         "captured_count": len(p["captured"]),
                         "game_bullheads": p["game_bullheads"],
                         "total_bullheads": p["total_bullheads"]} for p in d["players"]],
            "card_bullheads": deepcopy(d["card_bullheads"]),
            "rows": deepcopy(d["zones"]["rows"]), "reserve_size": len(d["zones"]["reserve"]),
            "commit_status": [p["committed_card"] is not None for p in d["players"]],
            "revealed": deepcopy(d["zones"]["revealed"]), "resolved": resolved,
            "pending": pending, "terminal": d["terminal"], "winners": deepcopy(d["winners"]),
        }
        return {"schema": OBS_SCHEMA, "data": data}
