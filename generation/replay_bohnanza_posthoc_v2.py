#!/usr/bin/env python3
"""Replay preserved Bohnanza implementations with the post-hoc representation-safe evaluator."""

from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "results/scores/bohnanza/source_experiment"
SUITE = ROOT / "checks/scenarios/bohnanza_posthoc_v2.json"
TARGET = BASE / "posthoc_v2"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def runs() -> list[tuple[str, Path, Path]]:
    result = []
    for directory in sorted((BASE / "runs").iterdir()):
        stem = f"bohnanza_src_{directory.name}_ag"
        result.append((directory.name, directory / f"{stem}.py", directory / f"{stem}_scenarios.json"))
    directory = BASE / "diagnostics/json_clean_diagnostic_1"
    stem = "bohnanza_src_json_clean_diagnostic_1_ag"
    result.append(("json_clean_diagnostic_1", directory / f"{stem}.py", directory / f"{stem}_scenarios.json"))
    return result


def evaluated(counts: dict[str, int]) -> int:
    return sum(int(counts[key]) for key in ("PASS", "FAIL", "CRASH"))


def fraction(counts: dict[str, int]) -> float | None:
    count = evaluated(counts)
    return int(counts["PASS"]) / count if count else None


def coverage(counts: dict[str, int]) -> float:
    return evaluated(counts) / sum(int(value) for value in counts.values())


def fmt(value: float | None) -> str:
    return "n/a" if value is None else f"{value:.3f}"


def main() -> int:
    TARGET.mkdir(parents=True, exist_ok=True)
    rows = []
    transitions: Counter[tuple[str, str]] = Counter()
    groups: dict[str, list[dict]] = defaultdict(list)
    for run_id, code, original_path in runs():
        output = TARGET / f"{run_id}.json"
        command = [
            sys.executable,
            str(ROOT / "checks/run_scenarios.py"),
            "--code-path", str(code),
            "--scenarios", str(SUITE),
            "--json-output", str(output),
        ]
        completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        if completed.returncode not in (0, 1, 2):
            raise RuntimeError(f"replay failed for {run_id}:\n{completed.stdout}{completed.stderr}")
        (TARGET / f"{run_id}.txt").write_text(completed.stdout + completed.stderr, encoding="utf-8")
        original, replay = load(original_path), load(output)
        original_results = {item["id"]: item for item in original["results"]}
        for item in replay["results"]:
            transitions[(original_results[item["id"]]["status"], item["status"])] += 1
        condition = "diagnostic" if "diagnostic" in run_id else run_id.rsplit("_", 1)[0]
        row = {
            "run": run_id,
            "condition": condition,
            "original": original["counts"],
            "posthoc_v2": replay["counts"],
            "original_pass_fraction": fraction(original["counts"]),
            "posthoc_v2_pass_fraction": fraction(replay["counts"]),
            "original_coverage": coverage(original["counts"]),
            "posthoc_v2_coverage": coverage(replay["counts"]),
            "posthoc_suite_sha256": replay["suite_sha256"],
            "posthoc_adapter_sha256": replay["adapter_sha256"],
            "posthoc_runner_sha256": replay["runner_sha256"],
        }
        rows.append(row)
        groups[condition].append(row)

    aggregate = {}
    for condition, items in groups.items():
        counts = {version: {key: sum(item[version][key] for item in items) for key in ("PASS", "FAIL", "CRASH", "UNREACHED", "UNTESTABLE")} for version in ("original", "posthoc_v2")}
        aggregate[condition] = {
            "runs": len(items),
            **counts,
            "original_pass_fraction": fraction(counts["original"]),
            "posthoc_v2_pass_fraction": fraction(counts["posthoc_v2"]),
            "original_coverage": coverage(counts["original"]),
            "posthoc_v2_coverage": coverage(counts["posthoc_v2"]),
        }

    summary = {
        "schema_version": 1,
        "label": "post-hoc representation-safety replay; frozen originals unchanged",
        "runs": rows,
        "conditions": aggregate,
        "status_transitions": [
            {"original": old, "posthoc_v2": new, "count": count}
            for (old, new), count in sorted(transitions.items())
        ],
    }
    (TARGET / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Bohnanza post-hoc evaluator-v2 replay",
        "",
        "The frozen original results remain unchanged. V2 removes representation-dependent card flattening/hash failures, uses broader phase/container aliases, and classifies unsupported evaluator reconstruction as UNTESTABLE rather than implementation CRASH.",
        "",
        "| Condition | Runs | Original P/F/C/U | V2 P/F/C/U | Original pass / coverage | V2 pass / coverage |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for condition, item in aggregate.items():
        def counts(version: str) -> str:
            value = item[version]
            return f"{value['PASS']}/{value['FAIL']}/{value['CRASH']}/{value['UNREACHED'] + value['UNTESTABLE']}"
        lines.append(f"| `{condition}` | {item['runs']} | {counts('original')} | {counts('posthoc_v2')} | {fmt(item['original_pass_fraction'])} / {fmt(item['original_coverage'])} | {fmt(item['posthoc_v2_pass_fraction'])} / {fmt(item['posthoc_v2_coverage'])} |")
    lines += [
        "",
        "## Per run",
        "",
        "| Run | Original P/F/C/U | V2 P/F/C/U | Original pass / coverage | V2 pass / coverage |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        def row_counts(version: str) -> str:
            value = row[version]
            return f"{value['PASS']}/{value['FAIL']}/{value['CRASH']}/{value['UNREACHED'] + value['UNTESTABLE']}"
        lines.append(f"| `{row['run']}` | {row_counts('original')} | {row_counts('posthoc_v2')} | {fmt(row['original_pass_fraction'])} / {fmt(row['original_coverage'])} | {fmt(row['posthoc_v2_pass_fraction'])} / {fmt(row['posthoc_v2_coverage'])} |")
    lines += [
        "",
        "## Boundary",
        "",
        "V2 is still a legacy compatibility adapter over heterogeneous implementations. It is more representation-safe, but only future implementations generated against the canonical BoardBench state/action data contract can eliminate heuristic introspection. V2 outcomes are post-hoc diagnostic evidence and must not replace the preregistered frozen scores.",
        "",
    ]
    (TARGET / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
