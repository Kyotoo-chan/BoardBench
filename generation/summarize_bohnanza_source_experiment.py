#!/usr/bin/env python3
"""Build separated per-arm and cross-arm Bohnanza experiment results."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results/scores/bohnanza/source_experiment"
RUNS = RESULTS / "runs"
GAME = ROOT / "inputs/games/bohnanza"

CONDITIONS = {
    "pdf_only": [("RULES", "publisher_rulebook", GAME / "game_rules.pdf")],
    "json_clean": [
        ("RULES", "publisher_rulebook", GAME / "game_rules.pdf"),
        ("COMPONENTS", "user_observation", GAME / "game_components.json"),
    ],
    "json_mutated": [
        ("RULES", "publisher_rulebook", GAME / "game_rules.pdf"),
        ("COMPONENTS", "user_observation", GAME / "variants/components_mutated.json"),
    ],
    "pdf_mutated": [
        ("RULES", "publisher_rulebook", GAME / "variants/game_rules_mutated.pdf"),
        ("COMPONENTS", "user_observation", GAME / "game_components.json"),
    ],
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def run_dir(stem: str) -> Path:
    return RUNS / stem.removeprefix("bohnanza_src_").removesuffix("_ag")


def validate_corpus() -> None:
    order = [f"{condition}_{repeat}" for repeat in (1, 2, 3) for condition in CONDITIONS]
    progress = load(RESULTS / "progress.json")
    expected_judges = [f"{run}_judge_{index}" for run in order for index in (1, 2, 3)]
    if progress.get("completed") != order or progress.get("judged") != expected_judges or progress.get("failed"):
        raise ValueError("experiment progress is incomplete or failed")
    repository = str(ROOT.resolve()).replace("\\", "/").casefold()
    for run in order:
        stem = f"bohnanza_src_{run}_ag"
        required = [
            f"{stem}.py", f"{stem}.md", f"{stem}_agentic_evidence.json", f"{stem}_assumptions.json",
            f"{stem}_checks.txt", f"{stem}_events.jsonl", f"{stem}_generation_prompt.md",
            f"{stem}_generation_usage.json", f"{stem}_rule_coverage.md", f"{stem}_scenarios.json",
        ]
        required += [f"{stem}_judge_{index}{suffix}" for index in (1, 2, 3) for suffix in (".md", "_events.jsonl", "_usage.json")]
        directory = run_dir(stem)
        if any(not (directory / name).is_file() or not (directory / name).stat().st_size for name in required):
            raise FileNotFoundError(f"missing or empty artifact for {run}")
        for events in [directory / f"{stem}_events.jsonl", *[directory / f"{stem}_judge_{index}_events.jsonl" for index in (1, 2, 3)]]:
            normalized = events.read_text(encoding="utf-8").replace("\\\\", "/").replace("\\", "/").casefold()
            if repository in normalized:
                raise ValueError(f"repository path leaked in {events}")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def spec_ref(path: Path) -> str:
    return Path(os.path.relpath(path, RESULTS / "specs")).as_posix()


def combined_usage(stem: str) -> Path:
    directory = run_dir(stem)
    calls = [load(directory / f"{stem}_generation_usage.json")]
    calls += [load(directory / f"{stem}_judge_{index}_usage.json") for index in (1, 2, 3)]
    totals: dict[str, int] = {}
    for call in calls:
        for key, value in call.get("token_summary", {}).items():
            totals[key] = totals.get(key, 0) + int(value)
    value = {
        "call_count": len(calls),
        "elapsed_seconds_total": sum(float(call.get("elapsed_seconds", 0)) for call in calls),
        "token_totals": totals,
        "calls": calls,
        "actual_subscription_cost": None,
    }
    path = directory / f"{stem}_usage.json"
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def result_spec(condition: str) -> dict:
    sources = CONDITIONS[condition]
    runs = []
    for repeat in (1, 2, 3):
        stem = f"bohnanza_src_{condition}_{repeat}_ag"
        directory = run_dir(stem)
        combined_usage(stem)
        runs.append({
            "stem": stem,
            "agentic_evidence": spec_ref(directory / f"{stem}_agentic_evidence.json"),
            "checks": spec_ref(directory / f"{stem}_checks.txt"),
            "scenarios": spec_ref(directory / f"{stem}_scenarios.json"),
            "usage": spec_ref(directory / f"{stem}_usage.json"),
            "code": spec_ref(directory / f"{stem}.py"),
            "assumptions": spec_ref(directory / f"{stem}_assumptions.json"),
            "neutral_reviews": [spec_ref(directory / f"{stem}_judge_{index}.md") for index in (1, 2, 3)],
        })
    return {
        "identity": {
            "game": "bohnanza",
            "condition": condition,
            "source_path": spec_ref(sources[0][2]),
            "source_format": "pdf" if len(sources) == 1 else "pdf+json",
            "source_sha256": sha256(sources[0][2]),
            "sources": [
                {"id": source_id, "role": role, "path": spec_ref(path), "sha256": sha256(path)}
                for source_id, role, path in sources
            ],
        },
        "source_diagnosis": {},
        "headline": "Three frozen runs; evidence groups remain separate and are compared cross-condition.",
        "runs": runs,
    }


def aggregate_counts(result: dict) -> dict[str, int]:
    keys = ("PASS", "FAIL", "CRASH", "UNREACHED", "UNTESTABLE")
    return {key: sum(int(run["scenario"]["counts"].get(key, 0)) for run in result["runs"]) for key in keys}


def check_group_pass_rate(result: dict, heading: str) -> float:
    passed = 0
    for run in result["runs"]:
        text = (run_dir(run["stem"]) / f"{run['stem']}_checks.txt").read_text(encoding="utf-8")
        section = text.split(f"=== {heading} ===", 1)[1].split("===", 1)[0]
        passed += "exit_code=0" in section
    return passed / len(result["runs"])


def comparison(results: dict[str, dict]) -> dict:
    arms = {}
    for condition, result in results.items():
        evidence = result["implementation_evidence"]
        review = result["review_evidence"]["neutral_judges"]
        counts = aggregate_counts(result)
        evaluated = counts["PASS"] + counts["FAIL"] + counts["CRASH"]
        arms[condition] = {
            "runs": 3,
            "technical_gate_pass_rate": evidence["technical_gate_pass_rate"],
            "robustness_gate_pass_rate": check_group_pass_rate(result, "ROBUSTNESS 05"),
            "robustness": evidence["robustness"],
            "interface_gate_pass_rate": check_group_pass_rate(result, "INTERFACE 06"),
            "interface": evidence["interface"],
            "scenario_counts": counts,
            "scenario_pass_fraction_of_evaluated": counts["PASS"] / evaluated if evaluated else None,
            "scenario_coverage": evidence["coverage"],
            "clear_rule_scenarios": evidence["clear_rules"],
            "human_decision_scenarios": evidence["human_decisions"],
            "neutral_judges": review,
        }
    return {
        "schema_version": 1,
        "rubric_version": "bohnanza-source-experiment-2026-07-18",
        "warning": "No combined correctness score. Compare technical, robustness, interface, scenario, and judge evidence separately.",
        "arms": arms,
    }


def fmt(value) -> str:
    return "n/a" if value is None else f"{value:.3f}"


def comparison_markdown(value: dict) -> str:
    lines = [
        "# Bohnanza source-condition comparison",
        "",
        "Three fresh valid generations per arm. No combined correctness score.",
        "",
        "| Arm | Technical gate | Robustness gate / mean | Interface gate / mean | Scenarios P/F/C/U | Evaluated pass fraction | Coverage mean | Judges mean ± SD |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, arm in value["arms"].items():
        counts = arm["scenario_counts"]
        untestable = counts["UNTESTABLE"] + counts["UNREACHED"]
        judges = arm["neutral_judges"]
        lines.append(
            f"| `{name}` | {fmt(arm['technical_gate_pass_rate'])} | {fmt(arm['robustness_gate_pass_rate'])} / {fmt(arm['robustness']['mean'])} | "
            f"{fmt(arm['interface_gate_pass_rate'])} / {fmt(arm['interface']['mean'])} | {counts['PASS']}/{counts['FAIL']}/{counts['CRASH']}/{untestable} | "
            f"{fmt(arm['scenario_pass_fraction_of_evaluated'])} | {fmt(arm['scenario_coverage']['mean'])} | "
            f"{fmt(judges['mean'])} ± {fmt(judges['sample_sd'])} |"
        )
    lines += [
        "",
        "## Interpretation boundary",
        "",
        "These descriptive three-run samples do not establish statistical significance. Scenario failures and crashes are distinct, and untestable cases are not scored as rule failures. See `mutation_audit.md` for preregistered mutation uptake and detector blind spots, and `artifact_audit.md` for completeness and isolation evidence.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    validate_corpus()
    specs = RESULTS / "specs"
    specs.mkdir(parents=True, exist_ok=True)
    built = {}
    for condition in CONDITIONS:
        spec_path = specs / f"{condition}.json"
        spec_path.write_text(json.dumps(result_spec(condition), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        output_dir = RESULTS / condition
        subprocess.run([sys.executable, str(ROOT / "generation/result_card.py"), "--spec", str(spec_path), "--output-dir", str(output_dir)], check=True, cwd=ROOT)
        built[condition] = load(output_dir / "result.json")
    value = comparison(built)
    (RESULTS / "comparison.json").write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (RESULTS / "comparison.md").write_text(comparison_markdown(value), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
