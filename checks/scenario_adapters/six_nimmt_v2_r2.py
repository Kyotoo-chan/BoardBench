"""Contract-v2 6 nimmt! adapter using only canonical data and the public Game API."""

from __future__ import annotations

from copy import deepcopy
import json
from typing import Any

STATE_SCHEMA = "boardbench/six-nimmt/state/2"
ACTION_SCHEMA = "boardbench/six-nimmt/action/2"
OBSERVATION_SCHEMA = "boardbench/six-nimmt/observation/2"
ACTION_ARGS = {"commit_card": {"card"}, "choose_row": {"row"}}
OBSERVATION_KEYS = {
    "player", "configuration", "game_number", "round_number", "phase", "current_player",
    "own_hand", "own_captured", "players", "card_bullheads", "rows", "reserve_size",
    "commit_status", "revealed", "resolved", "pending", "terminal", "winners",
}
OBSERVATION_PLAYER_KEYS = {"id", "hand_size", "captured_count", "game_bullheads", "total_bullheads"}


class AdapterUntestable(Exception):
    pass


def is_untestable(error: Exception) -> bool:
    return isinstance(error, AdapterUntestable)


def _envelope(payload: Any, schema: str) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != {"schema", "data"} or payload.get("schema") != schema or not isinstance(payload.get("data"), dict):
        raise AdapterUntestable(f"invalid canonical envelope for {schema}")
    return payload["data"]


def _state(game: Any, state: Any) -> dict[str, Any]:
    return _envelope(game.state_to_data(state), STATE_SCHEMA)


def _action_pairs(game: Any, actions: list[Any]) -> list[tuple[Any, dict[str, Any]]]:
    result = []
    seen = set()
    for action in actions:
        payload = game.action_to_data(action)
        data = _envelope(payload, ACTION_SCHEMA)
        if set(data) != {"type", "actor", "args"} or data["type"] not in ACTION_ARGS or set(data["args"]) != ACTION_ARGS[data["type"]]:
            raise AdapterUntestable(f"invalid canonical action data: {data!r}")
        if game.action_to_data(game.action_from_data(deepcopy(payload))) != payload:
            raise AdapterUntestable("canonical action does not round-trip")
        key = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        if key in seen:
            raise AdapterUntestable("duplicate canonical legal action")
        seen.add(key)
        result.append((action, data))
    return result


def _matches(data: dict[str, Any], selector: dict[str, Any]) -> bool:
    return ("type" not in selector or data["type"] == selector["type"]) and ("actor" not in selector or data["actor"] == selector["actor"]) and all(data["args"].get(k) == v for k, v in selector.get("args", {}).items())


def resolve_action(module: Any, game: Any, state: Any, actions: list[Any], selector: dict[str, Any]) -> Any:
    matches = [action for action, data in _action_pairs(game, actions) if _matches(data, selector)]
    if not matches:
        raise AssertionError(f"canonical action is not legal: {selector!r}")
    if len(matches) != 1 and not selector.get("choose_first"):
        raise AssertionError(f"canonical action is ambiguous: {selector!r}")
    return matches[0]


def _all_cards(data: dict[str, Any]) -> list[int]:
    cards = []
    for player in data["players"]:
        cards.extend(player["hand"])
        cards.extend(player["captured"])
        if player["committed_card"] is not None:
            cards.append(player["committed_card"])
    cards.extend(data["zones"]["reserve"])
    for row in data["zones"]["rows"]:
        cards.extend(row)
    pending = data.get("pending")
    if pending:
        cards.append(pending["card"])
        cards.extend(item["card"] for item in pending["remaining"])
    return cards


def setup(module: Any, game: Any, fixture: dict[str, Any]) -> Any:
    try:
        payload = game.state_to_data(game.initial_state())
        data = _envelope(payload, STATE_SCHEMA)
        count = int(data["configuration"]["players"])
        if count != int(fixture.get("players", count)):
            raise AdapterUntestable("fixture player count differs from runner game")
        if set(data.get("card_bullheads", {})) != {str(card) for card in range(1, 105)}:
            raise AdapterUntestable("canonical card_bullheads keys must be strings 1..104")
        hands = {int(k): list(v) for k, v in fixture.get("hands", {}).items()}
        captured = {int(k): list(v) for k, v in fixture.get("captured", {}).items()}
        committed = {int(k): v for k, v in fixture.get("committed", {}).items()}
        totals = {int(k): int(v) for k, v in fixture.get("total_bullheads", {}).items()}
        game_scores = {int(k): int(v) for k, v in fixture.get("game_bullheads", {}).items()}
        for player in data["players"]:
            p = player["id"]
            player["hand"] = hands.get(p, [])
            player["captured"] = captured.get(p, [])
            player["committed_card"] = committed.get(p)
            player["total_bullheads"] = totals.get(p, 0)
            player["game_bullheads"] = game_scores.get(p, sum(data["card_bullheads"][str(card)] for card in player["captured"]))
        rows = deepcopy(fixture.get("rows", [[10], [30], [50], [70]]))
        pending = deepcopy(fixture.get("pending"))
        used = [card for values in hands.values() for card in values] + [card for values in captured.values() for card in values] + [card for card in committed.values() if card is not None] + [card for row in rows for card in row]
        if pending:
            used.append(pending["card"])
            used.extend(item["card"] for item in pending["remaining"])
        if len(used) != len(set(used)) or any(not 1 <= card <= 104 for card in used):
            raise AdapterUntestable("fixture cards must be unique values 1..104")
        reserve = [card for card in range(1, 105) if card not in set(used)]
        data["zones"] = {
            "rows": rows,
            "reserve": reserve,
            "revealed": deepcopy(fixture.get("revealed", [])),
            "resolved": deepcopy(fixture.get("resolved", [])),
        }
        data["game_number"] = int(fixture.get("game_number", 1))
        data["round_number"] = int(fixture.get("round_number", 1))
        data["phase"] = fixture.get("phase", "commit")
        data["current_player"] = fixture.get("current_player", 0)
        data["pending"] = pending
        data["terminal"] = bool(fixture.get("terminal", False))
        data["winners"] = list(fixture.get("winners", []))
        if data["terminal"]:
            data["phase"] = "terminal"
            data["current_player"] = None
        return game.state_from_data(payload)
    except AdapterUntestable:
        raise
    except Exception as error:
        raise AdapterUntestable(f"canonical fixture reconstruction failed: {error}") from error


def _new_game(module: Any, players: int, seed: int = 1):
    try:
        return module.Game(num_players=players, seed=seed)
    except Exception as error:
        raise AdapterUntestable(f"could not construct {players}-player game: {error}") from error


def _apply(game: Any, state: Any, action: Any) -> Any:
    before = game.state_to_data(state)
    result = game.apply_action(state, action)
    if result is None:
        result = state
    if game.state_to_data(state) != before:
        raise AdapterUntestable("apply_action mutated its input state")
    return result


def _first_action(game: Any, state: Any) -> Any:
    pairs = _action_pairs(game, list(game.legal_actions(state)))
    if not pairs:
        raise AssertionError("nonterminal state has no legal actions")
    pairs.sort(key=lambda pair: json.dumps(pair[1], sort_keys=True, separators=(",", ":")))
    return pairs[0][0]


def _assert(label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def _observation(game: Any, state: Any, player: int) -> dict[str, Any]:
    data = _envelope(game.observation_to_data(state, player), OBSERVATION_SCHEMA)
    if set(data) != OBSERVATION_KEYS:
        raise AssertionError(f"observation fields: expected {sorted(OBSERVATION_KEYS)}, got {sorted(data)}")
    for entry in data["players"]:
        if set(entry) != OBSERVATION_PLAYER_KEYS:
            raise AssertionError(f"observation player fields leak or omit data: {sorted(entry)}")
    return data


def _check_observation(obs: dict[str, Any], spec: dict[str, Any], label: str) -> None:
    for key, expected in spec.get("equals", {}).items():
        _assert(f"{label}.{key}", obs.get(key), expected)
    for key in spec.get("absent", []):
        if key in obs:
            raise AssertionError(f"{label}: private key leaked: {key}")
    if "opponent_no_identity" in spec:
        opponent = int(spec["opponent_no_identity"])
        entry = next(item for item in obs["players"] if item["id"] == opponent)
        if any(key in entry for key in ("hand", "captured", "committed_card")):
            raise AssertionError(f"{label}: opponent identity data leaked")
    if "own_hand" in spec:
        _assert(f"{label}.own_hand", obs["own_hand"], spec["own_hand"])
    if "own_captured" in spec:
        _assert(f"{label}.own_captured", obs["own_captured"], spec["own_captured"])
    if "visible_cards" in spec:
        visible = {card for row in obs["rows"] for card in row}
        visible |= {item["card"] for item in obs["revealed"]} | {item["card"] for item in obs["resolved"]}
        missing = set(spec["visible_cards"]) - visible
        if missing:
            raise AssertionError(f"{label}.visible_cards missing public cards: {sorted(missing)}")
    if "opponent_aggregates" in spec:
        for raw, wanted in spec["opponent_aggregates"].items():
            entry = next(item for item in obs["players"] if item["id"] == int(raw))
            for key, expected in wanted.items():
                _assert(f"{label}.players[{raw}].{key}", entry[key], expected)


def check(module: Any, game: Any, state: Any, expected: dict[str, Any]) -> None:
    if "setup_probe" in expected:
        spec = expected["setup_probe"]
        probe = _new_game(module, int(spec["players"]), int(spec.get("seed", 1)))
        data = _state(probe, probe.initial_state())
        _assert("players", len(data["players"]), int(spec["players"]))
        _assert("hand_sizes", [len(p["hand"]) for p in data["players"]], [int(spec["hand_each"])] * int(spec["players"]))
        _assert("row_sizes", [len(row) for row in data["zones"]["rows"]], list(spec["row_sizes"]))
        _assert("reserve_size", len(data["zones"]["reserve"]), int(spec["reserve_size"]))
    if "initial_play_probe" in expected:
        spec = expected["initial_play_probe"]
        probe = _new_game(module, int(spec["players"]), int(spec.get("seed", 1)))
        state0 = probe.initial_state()
        data = _state(probe, state0)
        if any(not p["hand"] for p in data["players"]):
            raise AssertionError("a supported player has no initial hand card")
        pairs = _action_pairs(probe, list(probe.legal_actions(state0)))
        if not any(a["type"] == "commit_card" and a["actor"] == data["current_player"] for _, a in pairs):
            raise AssertionError("current seat has no initial commit action")
    if "bounded_game_probe" in expected:
        spec = expected["bounded_game_probe"]
        players = int(spec["players"])
        probe = _new_game(module, players, int(spec.get("seed", 1)))
        current = probe.initial_state()
        initial_game = _state(probe, current)["game_number"]
        commit_count = 0
        seen_rounds = set()
        final_precommit_hands = None
        for _ in range(int(spec["max_steps"])):
            before = _state(probe, current)
            if probe.is_terminal(current) or before["game_number"] > initial_game:
                break
            seen_rounds.add(before["round_number"])
            chosen = _first_action(probe, current)
            action_data = _envelope(probe.action_to_data(chosen), ACTION_SCHEMA)
            if action_data["type"] == "commit_card":
                if commit_count == players * int(spec["expected_rounds"]) - 1:
                    final_precommit_hands = [len(p["hand"]) for p in before["players"]]
                commit_count += 1
            current = _apply(probe, current, chosen)
        else:
            raise AssertionError("bounded rollout did not finish one game")
        _assert("bounded commit count", commit_count, players * int(spec["expected_rounds"]))
        _assert("bounded rounds", seen_rounds, set(range(1, int(spec["expected_rounds"]) + 1)))
        _assert("final precommit hand sizes", sorted(final_precommit_hands or []), [0] * (players - 1) + [1])
    if "reject_players" in expected:
        count = int(expected["reject_players"])
        try:
            module.Game(num_players=count, seed=1)
        except ValueError:
            pass
        else:
            raise AssertionError(f"unsupported player count accepted: {count}")
    if "reject_action_type" in expected:
        payload = {"schema": ACTION_SCHEMA, "data": {"type": expected["reject_action_type"], "actor": 0, "args": {}}}
        try:
            game.action_from_data(payload)
        except ValueError:
            pass
        else:
            raise AssertionError(f"unknown action type accepted: {expected['reject_action_type']}")
    if "inventory_probe" in expected:
        spec = expected["inventory_probe"]
        data = _state(game, state)
        _assert("card_inventory", sorted(_all_cards(data)), list(spec["cards"]))
        _assert("card_bullheads", data["card_bullheads"], spec["bullheads"])
    if "seed_probe" in expected:
        spec = expected["seed_probe"]
        def snapshot(seed: int, advance: bool):
            probe = _new_game(module, int(spec.get("players", 4)), seed)
            current = probe.initial_state()
            if advance:
                initial_game = _state(probe, current)["game_number"]
                for _ in range(int(spec.get("max_steps", 200))):
                    if probe.is_terminal(current) or _state(probe, current)["game_number"] > initial_game:
                        break
                    current = _apply(probe, current, _first_action(probe, current))
            data = _state(probe, current)
            return [p["hand"] for p in data["players"]], data["zones"]["rows"], data["zones"]["reserve"]
        a = snapshot(int(spec["seed_a"]), bool(spec.get("advance")))
        b = snapshot(int(spec.get("seed_b", spec["seed_a"])), bool(spec.get("advance")))
        if spec["relation"] == "equal":
            _assert("seeded snapshots", a, b)
        elif a == b:
            raise AssertionError("different seeds produced identical snapshots")
    if "reset_inventory_probe" in expected:
        spec = expected["reset_inventory_probe"]
        probe = _new_game(module, int(spec.get("players", 4)), int(spec.get("seed", 1)))
        current = probe.initial_state()
        initial_game = _state(probe, current)["game_number"]
        for _ in range(int(spec.get("max_steps", 200))):
            if probe.is_terminal(current) or _state(probe, current)["game_number"] > initial_game:
                break
            current = _apply(probe, current, _first_action(probe, current))
        data1 = _state(probe, current)
        _assert("reset_inventory", sorted(_all_cards(data1)), list(spec["cards"]))
        if not probe.is_terminal(current):
            _assert("reset_hand_sizes", [len(p["hand"]) for p in data1["players"]], [10] * int(spec.get("players", 4)))
            _assert("reset_row_sizes", [len(row) for row in data1["zones"]["rows"]], [1, 1, 1, 1])
            _assert("reset_capture_sizes", [len(p["captured"]) for p in data1["players"]], [0] * int(spec.get("players", 4)))
    data = _state(game, state)
    for key in ("phase", "current_player", "round_number", "game_number", "terminal", "winners"):
        if key in expected:
            _assert(key, data[key], expected[key])
    if "rows" in expected:
        _assert("rows", data["zones"]["rows"], expected["rows"])
    if "resolved_cards" in expected:
        _assert("resolved_cards", [item["card"] for item in data["zones"]["resolved"]], expected["resolved_cards"])
    if "pending_type" in expected:
        _assert("pending_type", data["pending"]["type"] if data["pending"] else None, expected["pending_type"])
    if "pending_remaining" in expected:
        _assert("pending_remaining", data["pending"]["remaining"], expected["pending_remaining"])
    for raw, cards in expected.get("hands", {}).items():
        _assert(f"hands[{raw}]", data["players"][int(raw)]["hand"], cards)
    for raw, size in expected.get("hand_sizes", {}).items():
        _assert(f"hand_sizes[{raw}]", len(data["players"][int(raw)]["hand"]), int(size))
    for raw, cards in expected.get("captured", {}).items():
        _assert(f"captured[{raw}]", data["players"][int(raw)]["captured"], cards)
    for raw, value in expected.get("captured_count", {}).items():
        _assert(f"captured_count[{raw}]", len(data["players"][int(raw)]["captured"]), int(value))
    for raw, value in expected.get("game_bullheads", {}).items():
        _assert(f"game_bullheads[{raw}]", data["players"][int(raw)]["game_bullheads"], int(value))
    for raw, value in expected.get("total_bullheads", {}).items():
        _assert(f"total_bullheads[{raw}]", data["players"][int(raw)]["total_bullheads"], int(value))
    if "returns" in expected:
        _assert("returns", game.returns(state), expected["returns"])
    if "legal_rows" in expected:
        rows = sorted(item["args"]["row"] for _, item in _action_pairs(game, list(game.legal_actions(state))) if item["type"] == "choose_row")
        _assert("legal_rows", rows, expected["legal_rows"])
    if "legal_commit_actor" in expected:
        pairs = _action_pairs(game, list(game.legal_actions(state)))
        actors = {item["actor"] for _, item in pairs if item["type"] == "commit_card"}
        _assert("legal_commit_actors", actors, {int(expected["legal_commit_actor"])})
    if "legal_action_types_not" in expected:
        present = {item["type"] for _, item in _action_pairs(game, list(game.legal_actions(state)))}
        forbidden = set(expected["legal_action_types_not"])
        if present & forbidden:
            raise AssertionError(f"forbidden legal action types: {sorted(present & forbidden)}")
    if "legal_commit_cards_not" in expected:
        present = {item["args"]["card"] for _, item in _action_pairs(game, list(game.legal_actions(state)) if not data["terminal"] else []) if item["type"] == "commit_card"}
        forbidden = set(expected["legal_commit_cards_not"])
        if present & forbidden:
            raise AssertionError(f"captured cards became legal commits: {sorted(present & forbidden)}")
    for raw, spec in expected.get("observations", {}).items():
        _check_observation(_observation(game, state, int(raw)), spec, f"observation[{raw}]")
