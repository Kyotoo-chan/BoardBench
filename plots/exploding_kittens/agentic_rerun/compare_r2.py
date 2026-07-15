#!/usr/bin/env python3
"""Re-evaluate and compare the six pilot/r2 pairs under rubric expl-v2.2."""

from __future__ import annotations

import csv
import json
import re
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = Path(__file__).resolve().parent
EVAL_DIR = OUT_DIR / "evaluation_v2_2"
OLD_JUDGES = OUT_DIR.parent / "variants" / "evaluation_v2"
CONDITIONS = [
    ("Original PDF", "expl_pdf", "d703218", "expl_pdf_r2", "1cd9a33"),
    ("Faithful TXT", "expl_txt", "8a0a89e", "expl_txt_r2", "cde02b6"),
    ("Anonymized", "expl_anon", "fd10842", "expl_anon_r2", "3763af7"),
    ("Omissions", "expl_omit", "6b64b25", "expl_omit_r2", "46f7014"),
    ("False rules", "expl_error", "adbd388", "expl_error_r2", "bc37dca"),
    ("Vague rules", "expl_vague", "9a7896e", "expl_vague_r2", "0a1a7e3"),
]


def git_show(commit: str, path: str) -> str:
    return subprocess.check_output(
        ["git", "show", f"{commit}:{path}"],
        cwd=REPO_ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def run(command: list[str]) -> tuple[int, str]:
    result = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return result.returncode, (result.stdout or "") + (result.stderr or "")


def parse_score(pattern: str, text: str, default: float = 0.0) -> float:
    matches = re.findall(pattern, text, re.I | re.M)
    return float(matches[-1]) if matches else default


def parse_judge(text: str) -> float:
    return parse_score(r"^score:\s*(?:\*\*)?([01](?:\.\d+)?)(?:\*\*)?\s*$", text)


def evaluate(code_path: Path, stem: str) -> tuple[dict[str, object], str]:
    python = sys.executable
    scenario_path = EVAL_DIR / f"{stem}_scenarios.json"
    groups = [
        ("technical gate 01-04", [python, "checks/run_checks.py", "--game", "expl", "--code-path", str(code_path), "--check", "01_result_file", "--check", "02_python_syntax", "--check", "03_startable_game", "--check", "04_required_api"]),
        ("runtime robustness 05", [python, "checks/run_checks.py", "--game", "expl", "--code-path", str(code_path), "--check", "05_random_rollouts", "--rollouts", "100", "--max-steps", "1000", "--seed", "1"]),
        ("interface 06", [python, "checks/run_checks.py", "--game", "expl", "--code-path", str(code_path), "--check", "06_action_language", "--max-steps", "1000", "--seed", "1"]),
        ("cited scenarios expl-v2.2", [python, "checks/run_scenarios.py", "--code-path", str(code_path), "--scenarios", "checks/scenarios/expl.json", "--json-output", str(scenario_path)]),
    ]
    sections = []
    for label, command in groups:
        returncode, output = run(command)
        sections.append(f"=== {label} ===\nexit_code={returncode}\n{output.rstrip()}")
    text = "\n\n".join(sections) + "\n"
    scenario = json.loads(scenario_path.read_text(encoding="utf-8"))
    parsed = {
        "technical_gate": 1.0 if re.search(r"summary\s+4/4", sections[0]) else 0.0,
        "robustness": parse_score(r"05_random_rollouts[^\n]*score=([0-9.]+)", text),
        "interface": parse_score(r"06_action_language[^\n]*score=([0-9.]+)", text),
        "scenario_passed": scenario["counts"]["PASS"],
        "scenario_failed": scenario["counts"]["FAIL"],
        "scenario_crashed": scenario["counts"]["CRASH"],
        "scenario_unreached": scenario["counts"]["UNREACHED"],
        "scenario_untestable": scenario["counts"]["UNTESTABLE"],
        "scenario_coverage": scenario["coverage"],
        "clear_passed": scenario["basis_scores"]["clear"]["passed"],
        "clear_total": scenario["basis_scores"]["clear"]["evaluated"],
        "clear_score": scenario["basis_scores"]["clear"]["score"],
        "human_passed": scenario["basis_scores"]["human_decision"]["passed"],
        "human_total": scenario["basis_scores"]["human_decision"]["evaluated"],
        "human_score": scenario["basis_scores"]["human_decision"]["score"],
        "scenario_statuses": {item["id"]: item["status"] for item in scenario["results"]},
        "suite_sha256": scenario["suite_sha256"],
        "adapter_sha256": scenario["adapter_sha256"],
        "code_sha256": scenario["code_sha256"],
    }
    return parsed, text


def collect() -> list[dict[str, object]]:
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="boardbench_compare_r2_") as temporary:
        temp = Path(temporary)
        for label, old_stem, old_commit, new_stem, new_commit in CONDITIONS:
            for generation, stem, commit in (("pilot", old_stem, old_commit), ("r2", new_stem, new_commit)):
                print(f"[{label} {generation}] evaluator v2.2", flush=True)
                code = git_show(commit, f"outputs/{stem}.py")
                code_path = temp / f"{stem}.py"
                code_path.write_text(code, encoding="utf-8")
                evaluated, checks_text = evaluate(code_path, stem)
                (EVAL_DIR / f"{stem}_checks.txt").write_text(checks_text, encoding="utf-8")

                if generation == "pilot":
                    judge_texts = [(OLD_JUDGES / f"{stem}_judge_{index}.md").read_text(encoding="utf-8") for index in range(1, 4)]
                    agentic_gate = False
                    repairs = None
                    protocol = "pilot-no-agentic-evidence-gate"
                else:
                    judge_texts = [git_show(commit, f"outputs/{stem}_judge_{index}.md") for index in range(1, 4)]
                    evidence = json.loads(git_show(commit, f"outputs/{stem}_agentic_evidence.json"))
                    agentic_gate = bool(evidence["independent_gate_passed"] and evidence["agent_ran_self_check"])
                    repairs = int(evidence["repair_count"])
                    protocol = str(evidence.get("protocol") or "agentic-v2")

                scores = [parse_judge(text) for text in judge_texts]
                usage = json.loads(git_show(commit, f"outputs/{stem}_usage.json"))
                row: dict[str, object] = {
                    "label": label,
                    "generation": generation,
                    "stem": stem,
                    "commit": commit,
                    "protocol": protocol,
                    "agentic_gate": agentic_gate,
                    "repair_count": repairs,
                    **evaluated,
                    "judge_1": scores[0],
                    "judge_2": scores[1],
                    "judge_3": scores[2],
                    "judge_mean": statistics.mean(scores),
                    "judge_stdev": statistics.stdev(scores),
                    "code_lines": len(code.splitlines()),
                    "input_tokens": int(usage.get("token_totals", {}).get("input_tokens", 0)),
                    "cached_input_tokens": int(usage.get("token_totals", {}).get("cached_input_tokens", 0)),
                    "output_tokens": int(usage.get("token_totals", {}).get("output_tokens", 0)),
                    "reasoning_tokens": int(usage.get("token_totals", {}).get("reasoning_output_tokens", usage.get("token_totals", {}).get("reasoning_tokens", 0))),
                    "provider_seconds": float(usage.get("elapsed_seconds_total", 0)),
                    "call_count": int(usage.get("call_count", 0)),
                }
                rows.append(row)
    return rows


def save(rows: list[dict[str, object]]) -> None:
    (OUT_DIR / "r2_metrics.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    flat_rows = [{key: json.dumps(value, ensure_ascii=False, sort_keys=True) if isinstance(value, dict) else value for key, value in row.items()} for row in rows]
    with (OUT_DIR / "r2_metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(flat_rows[0]))
        writer.writeheader()
        writer.writerows(flat_rows)


def paired(rows: list[dict[str, object]], key: str, generation: str) -> list[float]:
    return [float(next(row[key] for row in rows if row["label"] == label and row["generation"] == generation)) for label, *_ in CONDITIONS]


def finish(name: str) -> None:
    plt.tight_layout()
    plt.savefig(OUT_DIR / name, dpi=180, bbox_inches="tight")
    plt.close()


def plots(rows: list[dict[str, object]]) -> None:
    labels = [item[0] for item in CONDITIONS]
    x = np.arange(len(labels))
    width = 0.36

    fig, axes = plt.subplots(2, 1, figsize=(11, 9), sharex=True)
    for ax, key, title in ((axes[0], "clear_score", "Clear printed-rule scenarios"), (axes[1], "human_score", "Approved human-decision scenarios")):
        old = ax.bar(x - width / 2, paired(rows, key, "pilot"), width, label="Pilot")
        new = ax.bar(x + width / 2, paired(rows, key, "r2"), width, label="Agentic v2 rerun")
        ax.bar_label(old, fmt="%.2f", padding=2, fontsize=8)
        ax.bar_label(new, fmt="%.2f", padding=2, fontsize=8)
        ax.set_ylim(0, 1.1)
        ax.set_ylabel("Scenario score")
        ax.set_title(title)
        ax.legend()
    axes[1].set_xticks(x, labels, rotation=18, ha="right")
    finish("04_r2_rule_evidence.png")

    fig, ax = plt.subplots(figsize=(11, 5.5))
    old = ax.bar(x - width / 2, paired(rows, "judge_mean", "pilot"), width, label="Pilot corrected judge mean")
    new = ax.bar(x + width / 2, paired(rows, "judge_mean", "r2"), width, label="Agentic v2 rerun mean")
    ax.bar_label(old, fmt="%.3f", padding=2, fontsize=8)
    ax.bar_label(new, fmt="%.3f", padding=2, fontsize=8)
    ax.set_ylim(0, 1)
    ax.set_ylabel("Judge mean (n=3)")
    ax.set_xticks(x, labels, rotation=18, ha="right")
    ax.set_title("Three blind corrected reviews per implementation")
    ax.legend()
    finish("05_r2_judge_means.png")

    fig, ax = plt.subplots(figsize=(11, 5.5))
    old = ax.bar(x - width / 2, paired(rows, "code_lines", "pilot"), width, label="Pilot")
    new = ax.bar(x + width / 2, paired(rows, "code_lines", "r2"), width, label="Agentic v2 rerun")
    ax.bar_label(old, fmt="%.0f", padding=2, fontsize=8)
    ax.bar_label(new, fmt="%.0f", padding=2, fontsize=8)
    ax.set_ylabel("Python lines")
    ax.set_xticks(x, labels, rotation=18, ha="right")
    ax.set_title("Generated module size")
    ax.legend()
    finish("06_r2_code_lines.png")


def main() -> int:
    rows = collect()
    save(rows)
    plots(rows)
    print(f"wrote {len(rows)} rows to {OUT_DIR.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
