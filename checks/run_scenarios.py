"""Run cited black-box and deterministic scenarios against a generated game."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import random
import re
import sys
import unicodedata
from dataclasses import asdict, dataclass, field
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


class ScenarioUnreached(Exception):
    """The search budget did not reach the requested public action."""


class ScenarioUntestable(Exception):
    """The implementation cannot expose or construct the requested evidence."""


@dataclass
class ScenarioResult:
    id: str
    status: str
    message: str = ""
    basis: str = ""
    fact_ids: list[str] = field(default_factory=list)


def _rulebook_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _assert_equal(label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def _fold(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value).casefold()).replace("ß", "ss")
    folded = " ".join(re.findall(r"[a-z0-9]+", text))
    return folded.replace("schutzkarte", "protection").replace("gefahrenkarte", "danger")


def _contains(value: object, needle: object) -> bool:
    haystack = _fold(value)
    wanted = _fold(needle)
    return bool(wanted) and (wanted in haystack or wanted.replace(" ", "") in haystack.replace(" ", ""))


def _action_name_raw(game: Any, action: Any) -> str:
    with suppress_generated_output():
        return str(game.action_to_name(action))


def _matches_any(name: str, needles: list[object]) -> bool:
    return any(_contains(name, needle) for needle in needles)


def _action_map(game: Any, actions: list[Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    exact: dict[str, Any] = {}
    normalized: dict[str, Any] = {}
    ambiguous: set[str] = set()
    for action in actions:
        name = _action_name_raw(game, action)
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


def _selector_matches(name: str, selector: dict[str, Any]) -> bool:
    if "contains_any" in selector and not _matches_any(name, selector["contains_any"]):
        return False
    if "contains_all" in selector and not all(_contains(name, item) for item in selector["contains_all"]):
        return False
    if "contains_all_groups" in selector:
        if not all(_matches_any(name, group) for group in selector["contains_all_groups"]):
            return False
    return any(key in selector for key in ("contains_any", "contains_all", "contains_all_groups"))


def _resolve_action(game: Any, actions: list[Any], selector: dict[str, Any]) -> Any:
    exact, normalized = _action_map(game, actions)
    if "name" in selector:
        name = str(selector["name"])
        if name not in exact:
            raise AssertionError(f"action name is not legal: {name!r}; got {list(exact)!r}")
        return exact[name]
    if "normalized" in selector:
        key = str(selector["normalized"])
        if key not in normalized:
            raise AssertionError(f"normalized action is missing or ambiguous: {key!r}")
        return normalized[key]
    preferred_groups = selector.get("prefer_contains_all_groups")
    if preferred_groups:
        preferred = [
            action
            for name, action in exact.items()
            if all(_matches_any(name, group) for group in preferred_groups)
        ]
        if preferred:
            return preferred[int(selector.get("prefer_index", 0))]
    matching = [action for name, action in exact.items() if _selector_matches(name, selector)]
    if matching:
        return matching[0]
    if any(key in selector for key in ("contains_any", "contains_all", "contains_all_groups")):
        raise AssertionError(f"semantic action is not legal: {selector!r}; got {list(exact)!r}")
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
    raise AssertionError("action selector needs name, normalized, semantic contains, select, or index")


def _settle(game: Any, state: Any, configs: list[dict[str, Any]]) -> Any:
    for config in configs:
        allowed = list(config.get("while_all_contains_any", []))
        chosen = list(config.get("choose_contains_any", []))
        chosen_groups = list(config.get("choose_contains_all_groups", []))
        for _ in range(int(config.get("max_steps", 10))):
            actions = legal_actions(game, state)
            if not actions:
                break
            names = [_action_name_raw(game, action) for action in actions]
            if allowed and not all(_matches_any(name, allowed) for name in names):
                break
            matches = [
                action
                for action, name in zip(actions, names)
                if (not chosen or _matches_any(name, chosen))
                and not (_matches_any(name, ["draw", "ziehen"]) and _matches_any(name, ["pass"]))
                and (not chosen_groups or all(_matches_any(name, group) for group in chosen_groups))
            ]
            if not matches:
                break
            state = apply_action(game, state, matches[int(config.get("choose_index", 0))])
    return state


def _check_expectations(
    game: Any,
    state: Any,
    expected: dict[str, Any],
    *,
    module: Any | None = None,
    adapter: Any | None = None,
    previous_action: Any | None = None,
    previous_legal_action_count: int | None = None,
) -> None:
    actions = legal_actions(game, state)
    names = [_action_name_raw(game, action) for action in actions]
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
        needles = list(expected["legal_action_name_contains_any"])
        if not any(_matches_any(name, needles) for name in names):
            raise AssertionError(f"no legal action name contains any of {needles!r}; got {names!r}")
    if "legal_action_name_not_contains_any" in expected:
        needles = list(expected["legal_action_name_not_contains_any"])
        matched = [name for name in names if _matches_any(name, needles)]
        if matched:
            raise AssertionError(f"forbidden legal action names {matched!r}")
    if "legal_action_name_contains_all_groups" in expected:
        groups = list(expected["legal_action_name_contains_all_groups"])
        if not any(all(_matches_any(name, group) for group in groups) for name in names):
            raise AssertionError(f"no legal action name matches all semantic groups {groups!r}; got {names!r}")
    if "legal_action_name_not_contains_all_groups" in expected:
        for groups in expected["legal_action_name_not_contains_all_groups"]:
            matched = [name for name in names if all(_matches_any(name, group) for group in groups)]
            if matched:
                raise AssertionError(f"forbidden semantic legal action names {matched!r}")
    if "legal_action_delta" in expected:
        if previous_legal_action_count is None:
            raise AssertionError("legal_action_delta requires a preceding action")
        _assert_equal("legal_action_delta", len(actions) - previous_legal_action_count, int(expected["legal_action_delta"]))
    if "returns" in expected:
        _assert_equal("returns", returns(game, state), list(expected["returns"]))
    if "returns_sorted" in expected:
        _assert_equal("returns_sorted", sorted(returns(game, state)), sorted(expected["returns_sorted"]))
    if "previous_action_legal" in expected:
        if previous_action is None:
            raise AssertionError("previous_action_legal requires a preceding action")
        _assert_equal("previous_action_legal", previous_action in actions, bool(expected["previous_action_legal"]))
    if "adapter" in expected:
        if adapter is None:
            raise ScenarioUntestable("scenario expectation needs a configured adapter")
        adapter.check(module, game, state, expected["adapter"])


def _validate_source(scenario: dict[str, Any]) -> None:
    source = scenario.get("source")
    if not isinstance(source, dict):
        raise AssertionError("missing source object")
    if not isinstance(source.get("page"), int) or source["page"] < 1:
        raise AssertionError("source.page must be a positive page number")
    quote = source.get("quote")
    if not isinstance(quote, str) or len(quote.strip()) < 10:
        raise AssertionError("source.quote must contain a direct rulebook quote")


def _find_action_scenario(game: Any, scenario: dict[str, Any], module: Any, adapter: Any | None) -> None:
    search = scenario["search"]
    needles = list(search["action_contains_any"])
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
            matches = [action for action in actions if _matches_any(_action_name_raw(game, action), needles)]
            if matches:
                before_player = current_player(game, state)
                before_count = len(actions)
                action = matches[0]
                state = apply_action(game, state, action)
                state = _settle(game, state, list(scenario.get("settle", [])))
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
                    module=module,
                    adapter=adapter,
                    previous_action=action,
                    previous_legal_action_count=before_count,
                )
                return
            if not actions:
                break
            state = apply_action(game, state, rng.choice(actions))
    raise ScenarioUnreached(f"could not reach legal action containing any of {needles!r}")


def _terminal_rollout_scenario(game: Any, scenario: dict[str, Any], module: Any, adapter: Any | None) -> None:
    search = scenario["terminal_rollout"]
    rng = random.Random(int(search.get("seed", 1)))
    for _ in range(int(search.get("max_rollouts", 100))):
        with suppress_generated_output():
            state = game.initial_state()
        for _ in range(int(search.get("max_steps", 1000))):
            if is_terminal(game, state):
                _check_expectations(game, state, scenario.get("expect", {}), module=module, adapter=adapter)
                return
            actions = legal_actions(game, state)
            if not actions:
                break
            state = apply_action(game, state, rng.choice(actions))
    raise ScenarioUnreached("no terminal state reached by public random actions")


def run_scenario(game: Any, scenario: dict[str, Any], module: Any, adapter: Any | None) -> None:
    _validate_source(scenario)
    if "search" in scenario:
        _find_action_scenario(game, scenario, module, adapter)
        return
    if "terminal_rollout" in scenario:
        _terminal_rollout_scenario(game, scenario, module, adapter)
        return

    try:
        if "fixture" in scenario:
            if adapter is None:
                raise ScenarioUntestable("fixture needs a configured scenario adapter")
            state = adapter.setup(module, game, scenario["fixture"])
        else:
            with suppress_generated_output():
                state = game.initial_state()
    except NotImplementedError as exc:
        raise ScenarioUntestable(str(exc)) from exc

    _check_expectations(game, state, scenario.get("initial", {}), module=module, adapter=adapter)
    previous_action = None
    for step_number, step in enumerate(scenario.get("steps", []), start=1):
        actions = legal_actions(game, state)
        previous_legal_action_count = len(actions)
        previous_action = _resolve_action(game, actions, step.get("action", {}))
        state = apply_action(game, state, previous_action)
        state = _settle(game, state, list(step.get("settle", [])))
        try:
            _check_expectations(
                game,
                state,
                step.get("expect", {}),
                module=module,
                adapter=adapter,
                previous_action=previous_action,
                previous_legal_action_count=previous_legal_action_count,
            )
        except AssertionError as exc:
            raise AssertionError(f"step {step_number}: {exc}") from exc


def _load_adapter(suite: dict[str, Any], repo_root: Path) -> Any | None:
    raw_path = suite.get("adapter")
    if not raw_path:
        return None
    path = (repo_root / str(raw_path)).resolve()
    spec = importlib.util.spec_from_file_location(f"boardbench_adapter_{path.stem}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load scenario adapter: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_suite(path: Path, repo_root: Path) -> dict[str, Any]:
    suite = json.loads(path.read_text(encoding="utf-8"))
    if suite.get("version") not in {1, 2, 3}:
        raise ValueError("scenario suite version must be 1, 2, or 3")
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
        raise ValueError(f"rulebook hash mismatch: expected {expected_hash[:12]}, got {actual_hash[:12]}")
    scenarios = suite.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        raise ValueError("scenario suite needs at least one scenario")
    if suite.get("version") == 3:
        for scenario in scenarios:
            if not scenario.get("fact_ids"):
                raise ValueError(f"version-3 scenario {scenario.get('id')!r} needs fact_ids")
            if scenario.get("basis") not in {"clear", "human_decision"}:
                raise ValueError(f"version-3 scenario {scenario.get('id')!r} needs a valid basis")
    return suite


def run_suite(code_path: Path, suite_path: Path) -> dict[str, Any]:
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
    module, game, _ = make_game(ctx)
    adapter = _load_adapter(suite, repo_root)

    results: list[ScenarioResult] = []
    for scenario in suite["scenarios"]:
        scenario_id = str(scenario.get("id", "unnamed"))
        metadata = {
            "basis": str(scenario.get("basis", "")),
            "fact_ids": [str(item) for item in scenario.get("fact_ids", [])],
        }
        try:
            run_scenario(game, scenario, module, adapter)
        except ScenarioUnreached as exc:
            results.append(ScenarioResult(scenario_id, "UNREACHED", str(exc), **metadata))
        except ScenarioUntestable as exc:
            results.append(ScenarioResult(scenario_id, "UNTESTABLE", str(exc), **metadata))
        except AssertionError as exc:
            results.append(ScenarioResult(scenario_id, "FAIL", str(exc), **metadata))
        except Exception as exc:
            results.append(ScenarioResult(scenario_id, "CRASH", f"{exc.__class__.__name__}: {exc}", **metadata))
        else:
            results.append(ScenarioResult(scenario_id, "PASS", **metadata))

    counts = {status: sum(result.status == status for result in results) for status in ("PASS", "FAIL", "CRASH", "UNREACHED", "UNTESTABLE")}
    evaluated = counts["PASS"] + counts["FAIL"] + counts["CRASH"]
    total = len(results)
    basis_scores = {}
    for basis in ("clear", "human_decision"):
        selected = [result for result in results if result.basis == basis and result.status not in {"UNREACHED", "UNTESTABLE"}]
        basis_scores[basis] = {
            "passed": sum(result.status == "PASS" for result in selected),
            "evaluated": len(selected),
            "score": sum(result.status == "PASS" for result in selected) / len(selected) if selected else None,
        }
    adapter_path = suite.get("adapter")
    resolved_adapter = (repo_root / str(adapter_path)).resolve() if adapter_path else None
    return {
        "version": 3,
        "rubric_version": suite.get("rubric_version"),
        "suite": suite_path.as_posix(),
        "suite_sha256": _rulebook_hash(suite_path),
        "adapter": str(adapter_path) if adapter_path else None,
        "adapter_sha256": _rulebook_hash(resolved_adapter) if resolved_adapter else None,
        "code": code_path.as_posix(),
        "code_sha256": _rulebook_hash(code_path),
        "counts": counts,
        "evaluated": evaluated,
        "total": total,
        "score": counts["PASS"] / evaluated if evaluated else None,
        "coverage": evaluated / total if total else 0.0,
        "basis_scores": basis_scores,
        "results": [asdict(result) for result in results],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code-path", type=Path, required=True)
    parser.add_argument("--scenarios", type=Path, required=True)
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()

    try:
        result = run_suite(args.code_path, args.scenarios)
    except Exception as exc:
        print(f"FAIL scenario suite: {exc}")
        return 1

    for item in result["results"]:
        suffix = f": {item['message']}" if item["message"] else ""
        print(f"{item['status']} {item['id']}{suffix}")
    counts = result["counts"]
    score = "n/a" if result["score"] is None else f"{result['score']:.3f}"
    print(
        "SCENARIOS "
        + " ".join(f"{key}={counts[key]}" for key in ("PASS", "FAIL", "CRASH", "UNREACHED", "UNTESTABLE"))
        + f" evaluated={result['evaluated']}/{result['total']} score={score} coverage={result['coverage']:.3f}"
    )
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if counts["FAIL"] or counts["CRASH"]:
        return 1
    return 2 if counts["UNREACHED"] or counts["UNTESTABLE"] else 0


if __name__ == "__main__":
    sys.exit(main())
