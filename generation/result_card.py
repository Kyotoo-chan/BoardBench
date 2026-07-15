#!/usr/bin/env python3
"""Build one separated-evidence result profile for a concrete rulebook."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import statistics
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve(base: Path, value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    return path if path.is_absolute() else (base / path).resolve()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def summary(values: list[float]) -> dict[str, Any]:
    return {
        "values": values,
        "mean": statistics.mean(values) if values else None,
        "sample_sd": statistics.stdev(values) if len(values) > 1 else None,
    }


def parse_score(text: str, pattern: str) -> float:
    matches = re.findall(pattern, text, re.I | re.M)
    if not matches:
        raise ValueError(f"score pattern not found: {pattern}")
    return float(matches[-1])


def parse_judge(path: Path) -> float:
    text = path.read_text(encoding="utf-8")
    return parse_score(text, r"^score:\s*(?:\*\*)?([01](?:\.\d+)?)(?:\*\*)?")


def parse_run(base: Path, item: dict[str, Any]) -> dict[str, Any]:
    required = ("stem", "agentic_evidence", "checks", "scenarios", "usage", "code", "neutral_reviews")
    missing = [key for key in required if key not in item]
    if missing:
        raise ValueError(f"run missing fields: {missing}")
    paths = {key: resolve(base, item[key]) for key in ("agentic_evidence", "checks", "scenarios", "usage", "code")}
    if any(path is None or not path.is_file() for path in paths.values()):
        raise FileNotFoundError(f"run {item['stem']} has missing artifact")
    evidence = load_json(paths["agentic_evidence"])
    scenarios = load_json(paths["scenarios"])
    usage = load_json(paths["usage"])
    checks = paths["checks"].read_text(encoding="utf-8")
    reviews = [resolve(base, value) for value in item["neutral_reviews"]]
    if len(reviews) != 3 or any(path is None or not path.is_file() for path in reviews):
        raise ValueError(f"run {item['stem']} needs exactly three neutral reviews")

    assumptions_path = resolve(base, item.get("assumptions"))
    assumptions: list[dict[str, Any]] = []
    if assumptions_path:
        assumptions = load_json(assumptions_path).get("assumptions", [])
        if not isinstance(assumptions, list):
            raise ValueError("assumptions must be a list")

    personas: dict[str, Any] = {}
    for label, value in item.get("personas", {}).items():
        path = resolve(base, value)
        if path is None or not path.is_file():
            raise FileNotFoundError(f"missing persona review: {label}")
        personas[label] = {"path": str(value), "sha256": sha256(path)}

    totals = usage.get("token_totals", {})
    calls = usage.get("calls", [])
    judge_calls = [call for call in calls if call.get("mode") == "judge"]
    judge_models = sorted({str(call.get("model")) for call in judge_calls if call.get("model")})
    judge_efforts = sorted({str(call.get("reasoning_effort")) for call in judge_calls if call.get("reasoning_effort")})
    return {
        "stem": str(item["stem"]),
        "protocol": item.get("protocol", evidence.get("protocol")),
        "model": item.get("model", evidence.get("model")),
        "thinking": item.get("thinking", evidence.get("reasoning_effort")),
        "agentic_gate": bool(evidence.get("independent_gate_passed") and evidence.get("agent_ran_self_check")),
        "repairs": int(evidence.get("repair_count", 0)),
        "technical_gate": bool(re.search(r"summary\s+4/4\s+score=1\.000", checks)),
        "robustness": parse_score(checks, r"05_random_rollouts[^\n]*score=([0-9.]+)"),
        "interface": parse_score(checks, r"06_action_language[^\n]*score=([0-9.]+)"),
        "scenario": {
            "rubric_version": scenarios.get("rubric_version"),
            "suite_sha256": scenarios.get("suite_sha256"),
            "adapter_sha256": scenarios.get("adapter_sha256"),
            "counts": scenarios.get("counts"),
            "coverage": scenarios.get("coverage"),
            "clear": scenarios.get("basis_scores", {}).get("clear"),
            "human_decision": scenarios.get("basis_scores", {}).get("human_decision"),
            "results": scenarios.get("results", []),
        },
        "neutral_judges": [parse_judge(path) for path in reviews if path],
        "judge_model": item.get("judge_model", judge_models[0] if len(judge_models) == 1 else None),
        "judge_thinking": item.get("judge_thinking", judge_efforts[0] if len(judge_efforts) == 1 else None),
        "personas": personas,
        "assumptions": assumptions,
        "resources": {
            "calls": int(usage.get("call_count", 0)),
            "provider_seconds": float(usage.get("elapsed_seconds_total", 0)),
            "input_tokens": int(totals.get("input_tokens", 0)),
            "cached_input_tokens": int(totals.get("cached_input_tokens", 0)),
            "output_tokens": int(totals.get("output_tokens", 0)),
            "reasoning_tokens": int(totals.get("reasoning_output_tokens", totals.get("reasoning_tokens", 0))),
            "money": usage.get("actual_subscription_cost"),
            "code_lines": len(paths["code"].read_text(encoding="utf-8").splitlines()),
        },
        "hashes": {key: sha256(path) for key, path in paths.items() if path},
    }


def aggregate(spec: dict[str, Any], base: Path) -> dict[str, Any]:
    identity = dict(spec.get("identity", {}))
    source_path = resolve(base, identity.get("source_path"))
    if source_path and not source_path.is_file() and identity.get("source_path"):
        source_path = (Path.cwd() / str(identity["source_path"])).resolve()
    if source_path:
        if not source_path.is_file():
            raise FileNotFoundError(source_path)
        actual = sha256(source_path)
        expected = identity.get("source_sha256")
        if expected and expected != actual:
            raise ValueError(f"source hash mismatch: expected {expected}, got {actual}")
        identity["source_sha256"] = actual
    runs = [parse_run(base, item) for item in spec.get("runs", [])]
    if not runs:
        raise ValueError("result spec needs at least one run")
    suite_hashes = {run["scenario"]["suite_sha256"] for run in runs}
    adapter_hashes = {run["scenario"]["adapter_sha256"] for run in runs}
    if len(suite_hashes) != 1 or len(adapter_hashes) != 1:
        raise ValueError("runs use mismatched scenario or adapter hashes")

    def values(path: tuple[str, ...]) -> list[float]:
        result = []
        for run in runs:
            value: Any = run
            for key in path:
                value = value[key]
            if value is not None:
                result.append(float(value))
        return result

    assumptions = [assumption for run in runs for assumption in run["assumptions"]]
    alternatives: dict[str, dict[str, int]] = {}
    for assumption in assumptions:
        key = str(assumption.get("source_location", "unspecified"))
        selected = str(assumption.get("selected", "unspecified"))
        alternatives.setdefault(key, {})[selected] = alternatives.setdefault(key, {}).get(selected, 0) + 1

    money = [run["resources"]["money"] for run in runs]
    result = {
        "schema_version": 1,
        "identity": identity,
        "reproducibility": {
            "run_count": len(runs),
            "suite_sha256": next(iter(suite_hashes)),
            "adapter_sha256": next(iter(adapter_hashes)),
            "models": sorted({str(run["model"]) for run in runs}),
            "protocols": sorted({str(run["protocol"]) for run in runs}),
        },
        "source_diagnosis": spec.get("source_diagnosis", {}),
        "implementation_evidence": {
            "agentic_gate_pass_rate": sum(run["agentic_gate"] for run in runs) / len(runs),
            "technical_gate_pass_rate": sum(run["technical_gate"] for run in runs) / len(runs),
            "robustness": summary(values(("robustness",))),
            "interface": summary(values(("interface",))),
            "clear_rules": summary(values(("scenario", "clear", "score"))),
            "human_decisions": summary(values(("scenario", "human_decision", "score"))),
            "coverage": summary(values(("scenario", "coverage"))),
        },
        "review_evidence": {
            "neutral_judges": {
                **summary([score for run in runs for score in run["neutral_judges"]]),
                "models": sorted({str(run["judge_model"]) for run in runs if run["judge_model"]}),
                "thinking": sorted({str(run["judge_thinking"]) for run in runs if run["judge_thinking"]}),
            },
            "personas": {run["stem"]: run["personas"] for run in runs},
        },
        "assumption_evidence": {
            "material_count": len(assumptions),
            "interpretation_agreement": alternatives,
            "items": assumptions,
        },
        "efficiency": {
            key: summary(values(("resources", key)))
            for key in ("calls", "provider_seconds", "input_tokens", "cached_input_tokens", "output_tokens", "reasoning_tokens", "code_lines")
        },
        "monetary_cost": {"values": money, "exact_total": sum(money) if money and all(value is not None for value in money) else None},
        "headline": str(spec.get("headline", "Evidence profile generated; interpret groups separately.")),
        "runs": runs,
    }
    if "overall_correctness_score" in result:
        raise AssertionError("combined correctness scores are prohibited")
    return result


def fmt(value: Any) -> str:
    return "n/a" if value is None else f"{value:.3f}" if isinstance(value, float) else str(value)


def markdown(result: dict[str, Any]) -> str:
    identity = result["identity"]
    evidence = result["implementation_evidence"]
    review = result["review_evidence"]["neutral_judges"]
    efficiency = result["efficiency"]
    lines = [
        f"# {identity.get('game', 'Rulebook')} — result profile",
        "",
        f"> {result['headline']}",
        "",
        "## Identity",
        "",
        f"- Condition: {identity.get('condition', 'canonical')}",
        f"- Format: {identity.get('source_format', 'unknown')}",
        f"- SHA-256: `{identity.get('source_sha256', 'unknown')}`",
        f"- Runs: {result['reproducibility']['run_count']}",
        f"- Generation: {', '.join(result['reproducibility']['models'])} · thinking {', '.join(sorted({str(run['thinking']) for run in result['runs']}))}",
        f"- Neutral judges: {', '.join(review.get('models', [])) or 'unknown'} · thinking {', '.join(review.get('thinking', [])) or 'unknown'}",
        "",
        "## Evidence",
        "",
        "| Group | Mean | Sample SD |",
        "|---|---:|---:|",
    ]
    for label, key in (("Robustness", "robustness"), ("Interface", "interface"), ("Clear rules", "clear_rules"), ("Human decisions", "human_decisions"), ("Coverage", "coverage")):
        item = evidence[key]
        lines.append(f"| {label} | {fmt(item['mean'])} | {fmt(item['sample_sd'])} |")
    lines += [
        f"| Neutral judges | {fmt(review['mean'])} | {fmt(review['sample_sd'])} |",
        "",
        "## Assumptions",
        "",
        f"- Structured material declarations: {result['assumption_evidence']['material_count']}",
        "",
        "## Efficiency per run",
        "",
        "| Measure | Mean | Sample SD |",
        "|---|---:|---:|",
    ]
    for key in ("calls", "provider_seconds", "input_tokens", "output_tokens", "reasoning_tokens", "code_lines"):
        lines.append(f"| {key} | {fmt(efficiency[key]['mean'])} | {fmt(efficiency[key]['sample_sd'])} |")
    lines += ["", "Persona reviews and raw per-run evidence remain in `result.json`.", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    spec = load_json(args.spec)
    result = aggregate(spec, args.spec.resolve().parent)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (args.output_dir / "result.md").write_text(markdown(result), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
