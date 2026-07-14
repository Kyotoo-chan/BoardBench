"""Run small rulebook-cited black-box scenarios against a generated game.

Scenario files use only the public BoardBench API. Every scenario must include a
page and a direct rulebook quote so that a passing test remains traceable to the
source instead of becoming another unverified oracle.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path
from typing import Any

try:
    from action_normalizer import normalize_action_name
    from common import (
        CheckContext,
        apply_action,
        current_player,
        is_terminal,
        legal_actions,
        make_game,
        returns,
        suppress_generated_output,
    )
except ModuleNotFoundError:  # Imported as checks.run_scenarios.
    from checks.action_normalizer import normalize_action_name
    from checks.common import (
        CheckContext,
        apply_action,
        current_player,
        is_terminal,
        legal_actions,
        make_game,
        returns,
        suppress_generated_output,
    )


def _rulebook_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _assert_equal(label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def _action_map(game: Any, actions: list[Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    exact: dict[str, Any] = {}
    normalized: dict[str, Any] = {}
    ambiguous: set[str] = set()
    for action in actions:
        with suppress_generated_output():
            name = str(game.action_to_name(action))
        if name in exact:
            raise AssertionError(f"duplicate emitted action name {name!r}")
        exact[name] = action
        key = normalize_action_name(name)
        if key in normalized:
            ambiguous.add(key)
        else:
            normalized[key] = action
    for key in ambiguous:
        normalized.pop(key, None)
    return exact, normalized


def _resolve_action(game: Any, actions: list[Any], selector: dict[str, Any]) -> Any:
    exact, normalized = _action_map(game, actions)
    if "name" in selector:
        name = str(selector["name"])
        if name not in exact:
            raise AssertionError(f"action name is not legal: {name!r}")
        return exact[name]
    if "normalized" in selector:
        key = str(selector["normalized"])
        if key not in normalized:
            raise AssertionError(f"normalized action is missing or ambiguous: {key!r}")
        return normalized[key]
    if selector.get("select") == "first":
        if not actions:
            raise AssertionError("cannot select first action from an empty legal action list")
        return actions[0]
    if selector.get("select") == "last":
        if not actions:
            raise AssertionError("cannot select last action from an empty legal action list")
        return actions[-1]
    if "index" in selector:
        return actions[int(selector["index"])]
    raise AssertionError("action selector needs name, normalized, select, or index")


def _check_expectations(
    game: Any,
    state: Any,
    expected: dict[str, Any],
    *,
    previous_action: Any | None = None,
    previous_legal_action_count: int | None = None,
) -> None:
    actions = legal_actions(game, state)
    if "current_player" in expected:
        _assert_equal("current_player", current_player(game, state), int(expected["current_player"]))
    if "terminal" in expected:
        _assert_equal("terminal", is_terminal(game, state), bool(expected["terminal"]))
    if "legal_action_count" in expected:
        _assert_equal("legal_action_count", len(actions), int(expected["legal_action_count"]))
    if "legal_action_count_min" in expected:
        minimum = int(expected["legal_action_count_min"])
        if len(actions) < minimum:
            raise AssertionError(f"legal_action_count: expected at least {minimum}, got {len(actions)}")
    if "legal_action_name_contains_any" in expected:
        needles = [normalize_action_name(str(item)) for item in expected["legal_action_name_contains_any"]]
        names = [normalize_action_name(str(game.action_to_name(action))) for action in actions]
        if not any(needle in name for needle in needles for name in names):
            raise AssertionError(f"no legal action name contains any of {needles!r}; got {names!r}")
    if "legal_action_delta" in expected:
        if previous_legal_action_count is None:
            raise AssertionError("legal_action_delta requires a preceding action")
        _assert_equal(
            "legal_action_delta",
            len(actions) - previous_legal_action_count,
            int(expected["legal_action_delta"]),
        )
    if "returns" in expected:
        _assert_equal("returns", returns(game, state), list(expected["returns"]))
    if "returns_sorted" in expected:
        _assert_equal("returns_sorted", sorted(returns(game, state)), sorted(expected["returns_sorted"]))
    if "previous_action_legal" in expected:
        if previous_action is None:
            raise AssertionError("previous_action_legal requires a preceding action")
        _assert_equal(
            "previous_action_legal",
            previous_action in actions,
            bool(expected["previous_action_legal"]),
        )


def _validate_source(scenario: dict[str, Any]) -> None:
    source = scenario.get("source")
    if not isinstance(source, dict):
        raise AssertionError("missing source object")
    if not isinstance(source.get("page"), int) or source["page"] < 1:
        raise AssertionError("source.page must be a positive page number")
    quote = source.get("quote")
    if not isinstance(quote, str) or len(quote.strip()) < 10:
        raise AssertionError("source.quote must contain a direct rulebook quote")


def _action_name(game: Any, action: Any) -> str:
    with suppress_generated_output():
        return normalize_action_name(str(game.action_to_name(action)))


def _find_action_scenario(game: Any, scenario: dict[str, Any]) -> None:
    search = scenario["search"]
    needles = [normalize_action_name(str(item)) for item in search["action_contains_any"]]
    rng = random.Random(int(search.get("seed", 1)))
    max_rollouts = int(search.get("max_rollouts", 200))
    max_steps = int(search.get("max_steps", 300))

    for _ in range(max_rollouts):
        with suppress_generated_output():
            state = game.initial_state()
        for _ in range(max_steps):
            if is_terminal(game, state):
                break
            actions = legal_actions(game, state)
            matches = [action for action in actions if any(needle in _action_name(game, action) for needle in needles)]
            if matches:
                before_player = current_player(game, state)
                before_count = len(actions)
                action = matches[0]
                state = apply_action(game, state, action)
                expected = scenario.get("expect", {})
                relation = expected.get("current_player_relation")
                after_player = current_player(game, state)
                if relation == "same" and after_player != before_player:
                    raise AssertionError(f"current_player changed from {before_player} to {after_player}")
                if relation == "changed" and after_player == before_player:
                    raise AssertionError(f"current_player did not change from {before_player}")
                _check_expectations(
                    game,
                    state,
                    {key: value for key, value in expected.items() if key != "current_player_relation"},
                    previous_action=action,
                    previous_legal_action_count=before_count,
                )
                return
            if not actions:
                break
            state = apply_action(game, state, rng.choice(actions))
    raise AssertionError(f"could not reach legal action containing any of {needles!r}")


def _terminal_rollout_scenario(game: Any, scenario: dict[str, Any]) -> None:
    search = scenario["terminal_rollout"]
    rng = random.Random(int(search.get("seed", 1)))
    max_rollouts = int(search.get("max_rollouts", 100))
    max_steps = int(search.get("max_steps", 1000))
    for _ in range(max_rollouts):
        with suppress_generated_output():
            state = game.initial_state()
        for _ in range(max_steps):
            if is_terminal(game, state):
                _check_expectations(game, state, scenario.get("expect", {}))
                return
            actions = legal_actions(game, state)
            if not actions:
                break
            state = apply_action(game, state, rng.choice(actions))
    raise AssertionError("no terminal state reached by public random actions")


def run_scenario(game: Any, scenario: dict[str, Any]) -> None:
    _validate_source(scenario)
    if "search" in scenario:
        _find_action_scenario(game, scenario)
        return
    if "terminal_rollout" in scenario:
        _terminal_rollout_scenario(game, scenario)
        return

    with suppress_generated_output():
        state = game.initial_state()
    _check_expectations(game, state, scenario.get("initial", {}))

    previous_action = None
    for step_number, step in enumerate(scenario.get("steps", []), start=1):
        actions = legal_actions(game, state)
        previous_legal_action_count = len(actions)
        previous_action = _resolve_action(game, actions, step.get("action", {}))
        state = apply_action(game, state, previous_action)
        try:
            _check_expectations(
                game,
                state,
                step.get("expect", {}),
                previous_action=previous_action,
                previous_legal_action_count=previous_legal_action_count,
            )
        except AssertionError as exc:
            raise AssertionError(f"step {step_number}: {exc}") from exc


def load_suite(path: Path, repo_root: Path) -> dict[str, Any]:
    suite = json.loads(path.read_text(encoding="utf-8"))
    if suite.get("version") not in {1, 2}:
        raise ValueError("scenario suite version must be 1 or 2")
    rulebook = suite.get("rulebook", {})
    raw_path = rulebook.get("path")
    expected_hash = str(rulebook.get("sha256", "")).lower()
    if not raw_path or len(expected_hash) != 64:
        raise ValueError("rulebook.path and full rulebook.sha256 are required")
    rulebook_path = (repo_root / raw_path).resolve()
    if not rulebook_path.exists():
        raise FileNotFoundError(f"rulebook not found: {rulebook_path}")
    actual_hash = _rulebook_hash(rulebook_path)
    if actual_hash != expected_hash:
        raise ValueError(
            f"rulebook hash mismatch: expected {expected_hash[:12]}, got {actual_hash[:12]}"
        )
    scenarios = suite.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        raise ValueError("scenario suite needs at least one scenario")
    return suite


def run_suite(code_path: Path, suite_path: Path) -> tuple[int, int, list[str]]:
    repo_root = Path(__file__).resolve().parents[1]
    suite = load_suite(suite_path, repo_root)
    ctx = CheckContext(
        repo_root=repo_root,
        game=str(suite.get("game", code_path.stem)),
        code_path=code_path.resolve(),
        rollouts=1,
        max_steps=1,
        seed=1,
    )
    _, game, _ = make_game(ctx)

    passed = 0
    failures: list[str] = []
    for scenario in suite["scenarios"]:
        scenario_id = str(scenario.get("id", "unnamed"))
        try:
            run_scenario(game, scenario)
        except Exception as exc:
            failures.append(f"{scenario_id}: {exc}")
        else:
            passed += 1
    return passed, len(suite["scenarios"]), failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code-path", type=Path, required=True)
    parser.add_argument("--scenarios", type=Path, required=True)
    args = parser.parse_args()

    try:
        passed, total, failures = run_suite(args.code_path, args.scenarios)
    except Exception as exc:
        print(f"FAIL scenario suite: {exc}")
        return 1

    for failure in failures:
        print(f"FAIL {failure}")
    score = passed / total
    status = "OK" if not failures else "FAIL"
    print(f"{status} rulebook_scenarios {passed}/{total} score={score:.3f}")
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
