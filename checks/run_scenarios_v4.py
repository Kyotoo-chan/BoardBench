#!/usr/bin/env python3
"""Run version-4 cited scenarios with atomic-claim mapping evidence."""

from __future__ import annotations

import argparse
from copy import deepcopy
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from checks.claim_coverage import validate_claim_coverage
from checks.common import CheckContext, make_game
from checks.run_scenarios import (
    ScenarioResult,
    ScenarioUnreached,
    ScenarioUntestable,
    _load_adapter,
    _rulebook_hash,
    _validate_hashed_source,
    run_scenario,
)


def load_suite(path: Path, repo_root: Path) -> dict[str, Any]:
    suite = json.loads(path.read_text(encoding="utf-8"))
    if suite.get("version") != 4:
        raise ValueError("version-4 runner requires scenario suite version 4")
    sources = suite.get("sources") or [suite.get("rulebook", {})]
    if not isinstance(sources, list) or not sources:
        raise ValueError("scenario suite needs rulebook or sources")
    for source in sources:
        if not isinstance(source, dict):
            raise ValueError("each source must be an object")
        _validate_hashed_source(source, repo_root)
    scenarios = suite.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        raise ValueError("scenario suite needs at least one scenario")
    for scenario in scenarios:
        if not scenario.get("fact_ids"):
            raise ValueError(f"version-4 scenario {scenario.get('id')!r} needs fact_ids")
        if scenario.get("basis") not in {"clear", "human_decision"}:
            raise ValueError(f"version-4 scenario {scenario.get('id')!r} needs a valid basis")
        if "cases" in scenario:
            cases = scenario["cases"]
            if not isinstance(cases, list) or not cases or not all(isinstance(case, dict) for case in cases):
                raise ValueError(f"scenario {scenario.get('id')!r} cases must be a nonempty object list")
            names = [str(case.get("name", index)) for index, case in enumerate(cases, start=1)]
            if len(names) != len(set(names)):
                raise ValueError(f"scenario {scenario.get('id')!r} has duplicate case names")
    inventory = suite.get("claim_inventory")
    if not inventory:
        raise ValueError("version-4 suite needs claim_inventory")
    suite["claim_coverage"] = validate_claim_coverage((repo_root / inventory).resolve(), scenarios)
    return suite


def run_scenario_v4(game: Any, scenario: dict[str, Any], module: Any, adapter: Any | None) -> None:
    if "cases" not in scenario:
        run_scenario(game, scenario, module, adapter)
        return
    base = {key: deepcopy(value) for key, value in scenario.items() if key != "cases"}
    errors = []
    for index, raw_case in enumerate(scenario["cases"], start=1):
        case = deepcopy(raw_case)
        name = str(case.pop("name", index))
        merged = deepcopy(base)
        merged.update(case)
        try:
            run_scenario(game, merged, module, adapter)
        except Exception as error:
            errors.append((name, error))
    if not errors:
        return
    detail = "; ".join(f"case {name}: {error}" for name, error in errors)
    unexpected = [error for _, error in errors if not isinstance(error, (AssertionError, ScenarioUnreached, ScenarioUntestable))]
    if unexpected:
        raise RuntimeError(detail) from unexpected[0]
    if any(isinstance(error, AssertionError) for _, error in errors):
        raise AssertionError(detail)
    if any(isinstance(error, ScenarioUnreached) for _, error in errors):
        raise ScenarioUnreached(detail)
    raise ScenarioUntestable(detail)


def run_suite(code_path: Path, suite_path: Path) -> dict[str, Any]:
    repo_root = Path(__file__).resolve().parents[1]
    suite = load_suite(suite_path, repo_root)
    ctx = CheckContext(repo_root, str(suite.get("game", code_path.stem)), code_path.resolve(), 1, 1, 1)
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
            run_scenario_v4(game, scenario, module, adapter)
        except ScenarioUnreached as exc:
            results.append(ScenarioResult(scenario_id, "UNREACHED", str(exc), **metadata))
        except ScenarioUntestable as exc:
            results.append(ScenarioResult(scenario_id, "UNTESTABLE", str(exc), **metadata))
        except AssertionError as exc:
            results.append(ScenarioResult(scenario_id, "FAIL", str(exc), **metadata))
        except Exception as exc:
            if adapter is not None and hasattr(adapter, "is_untestable") and adapter.is_untestable(exc):
                results.append(ScenarioResult(scenario_id, "UNTESTABLE", str(exc), **metadata))
            else:
                results.append(ScenarioResult(scenario_id, "CRASH", f"{exc.__class__.__name__}: {exc}", **metadata))
        else:
            results.append(ScenarioResult(scenario_id, "PASS", **metadata))

    counts = {status: sum(result.status == status for result in results) for status in ("PASS", "FAIL", "CRASH", "UNREACHED", "UNTESTABLE")}
    evaluated = counts["PASS"] + counts["FAIL"] + counts["CRASH"]
    basis_scores = {}
    for basis in ("clear", "human_decision"):
        selected = [result for result in results if result.basis == basis and result.status not in {"UNREACHED", "UNTESTABLE"}]
        basis_scores[basis] = {
            "passed": sum(result.status == "PASS" for result in selected),
            "evaluated": len(selected),
            "score": sum(result.status == "PASS" for result in selected) / len(selected) if selected else None,
        }
    claims = suite["claim_coverage"]
    evaluated_claims = {
        claim_id
        for result in results if result.status not in {"UNREACHED", "UNTESTABLE"}
        for claim_id in result.fact_ids
    }
    required_claims = set(claims["required"])
    claims = {
        **claims,
        "evaluated": sorted(required_claims & evaluated_claims),
        "evaluated_coverage": len(required_claims & evaluated_claims) / len(required_claims) if required_claims else 1.0,
    }
    adapter_path = suite.get("adapter")
    resolved_adapter = (repo_root / str(adapter_path)).resolve() if adapter_path else None
    return {
        "version": 4,
        "rubric_version": suite.get("rubric_version"),
        "suite": suite_path.as_posix(),
        "suite_sha256": _rulebook_hash(suite_path),
        "adapter": str(adapter_path) if adapter_path else None,
        "adapter_sha256": _rulebook_hash(resolved_adapter) if resolved_adapter else None,
        "runner_sha256": _rulebook_hash(Path(__file__).resolve()),
        "code": code_path.as_posix(),
        "code_sha256": _rulebook_hash(code_path),
        "counts": counts,
        "evaluated": evaluated,
        "total": len(results),
        "coverage": evaluated / len(results) if results else 0.0,
        "basis_scores": basis_scores,
        "claim_coverage": claims,
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
    basis_text = " ".join(f"{name}={values['passed']}/{values['evaluated']}" for name, values in result["basis_scores"].items())
    print(
        "SCENARIOS "
        + " ".join(f"{key}={counts[key]}" for key in ("PASS", "FAIL", "CRASH", "UNREACHED", "UNTESTABLE"))
        + f" evaluated={result['evaluated']}/{result['total']} coverage={result['coverage']:.3f} {basis_text}"
    )
    claims = result["claim_coverage"]
    print(
        f"CLAIMS mapped={len(claims['scenario_covered'])}/{len(claims['required'])} "
        f"evaluated={len(claims['evaluated'])}/{len(claims['required'])} "
        f"exceptions={len(claims['coverage_exceptions'])}"
    )
    if args.json_output:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if counts["FAIL"] or counts["CRASH"]:
        return 1
    return 2 if counts["UNREACHED"] or counts["UNTESTABLE"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
