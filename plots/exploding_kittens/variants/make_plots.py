#!/usr/bin/env python3
"""Collect the six committed experiment snapshots and plot separate evidence groups."""

from __future__ import annotations

import csv
import json
import re
import statistics
import subprocess
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = Path(__file__).resolve().parent
EVALUATION_V2 = OUT_DIR / "evaluation_v2"
EXPERIMENTS = [
    (1, "expl_pdf", "Original PDF"),
    (2, "expl_txt", "Faithful TXT"),
    (3, "expl_anon", "Anonymized"),
    (4, "expl_omit", "Omissions"),
    (5, "expl_error", "False rules"),
    (6, "expl_vague", "Vague rules"),
]


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True, encoding="utf-8", errors="replace")


def experiment_commit(number: int) -> str:
    commits = git("log", "--format=%H%x09%s").splitlines()
    prefix = f"experiment {number:02d}:"
    matches = [line.split("\t", 1)[0] for line in commits if line.split("\t", 1)[1].startswith(prefix)]
    if len(matches) != 1:
        raise RuntimeError(f"expected one commit for {prefix}, found {len(matches)}")
    return matches[0]


def show(commit: str, path: str) -> str:
    return git("show", f"{commit}:{path}")


def last_number(pattern: str, text: str, default: float = 0.0) -> float:
    matches = re.findall(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
    return float(matches[-1]) if matches else default


def parse_checks(text: str) -> dict[str, float | int | str]:
    technical = 1.0 if re.search(r"technical gate 01-04.*?summary\s+4/4", text, re.S | re.I) else 0.0
    robustness = last_number(r"05_random_rollouts[^\n]*score=([0-9.]+)", text)
    interface = last_number(r"06_action_language[^\n]*score=([0-9.]+)", text)
    scenario = re.search(r"rulebook_scenarios\s+(\d+)/(\d+)\s+score=([0-9.]+)", text)
    failures = {
        match.group(1): match.group(2).strip()
        for match in re.finditer(r"^FAIL (EXPL-R\d+)[^:]*:\s*(.*)$", text, re.MULTILINE)
    }
    scenario_status: dict[str, str] = {}
    for number in range(1, 9):
        scenario_id = f"EXPL-R{number:02d}"
        message = failures.get(scenario_id)
        if message is None:
            status = "PASS"
        elif message.startswith("could not reach legal action"):
            status = "UNREACHED"
        elif any(fragment in message for fragment in ("list.remove", "invalid literal", "crashed", "exception")):
            status = "CRASH"
        else:
            status = "FAIL"
        scenario_status[f"scenario_r{number:02d}"] = status
    return {
        "technical_gate": technical,
        "robustness": robustness,
        "interface": interface,
        "scenario_passed": int(scenario.group(1)) if scenario else 0,
        "scenario_total": int(scenario.group(2)) if scenario else 0,
        "scenario_score": float(scenario.group(3)) if scenario else 0.0,
        "scenario_failed": sum(value == "FAIL" for value in scenario_status.values()),
        "scenario_unreached": sum(value == "UNREACHED" for value in scenario_status.values()),
        "scenario_crashed": sum(value == "CRASH" for value in scenario_status.values()),
        **scenario_status,
    }


def parse_judge(text: str) -> dict[str, float | int | str]:
    return {
        "score": last_number(r"^score:\s*(?:\*\*)?([01](?:\.\d+)?)(?:\*\*)?\s*$", text),
        "confidence": (re.findall(r"^confidence:\s*(low|medium|high)\s*$", text, re.I | re.M) or ["unknown"])[-1].lower(),
        "critical": int(last_number(r"^critical_issues:\s*(\d+)\s*$", text)),
        "major": int(last_number(r"^major_issues:\s*(\d+)\s*$", text)),
        "minor": int(last_number(r"^minor_issues:\s*(\d+)\s*$", text)),
    }


def quota_percent(quota: object, window: str) -> float | None:
    if not isinstance(quota, dict):
        return None
    data = quota.get(window)
    if not isinstance(data, dict) or not isinstance(data.get("used_percent"), (int, float)):
        return None
    return float(data["used_percent"])


def collect() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for number, stem, label in EXPERIMENTS:
        commit = experiment_commit(number)
        legacy_checks = parse_checks(show(commit, f"outputs/{stem}_checks.txt"))
        scenario_v2 = json.loads((EVALUATION_V2 / f"{stem}_scenarios.json").read_text(encoding="utf-8"))
        legacy_judges = [parse_judge(show(commit, f"outputs/{stem}_judge_{index}.md")) for index in range(1, 4)]
        judges = [parse_judge((EVALUATION_V2 / f"{stem}_judge_{index}.md").read_text(encoding="utf-8")) for index in range(1, 4)]
        rejudge_usage = [json.loads((EVALUATION_V2 / f"{stem}_judge_{index}_usage.json").read_text(encoding="utf-8")) for index in range(1, 4)]
        usage = json.loads(show(commit, f"outputs/{stem}_usage.json"))
        code = show(commit, f"outputs/{stem}.py")
        calls = sorted(usage.get("calls", []), key=lambda call: call.get("started_at", ""))
        tokens = usage.get("token_totals", {})
        judge_scores = [float(judge["score"]) for judge in judges]
        legacy_judge_scores = [float(judge["score"]) for judge in legacy_judges]
        scenario_counts = scenario_v2["counts"]
        scenario_status = {
            f"scenario_r{index:02d}": item["status"]
            for index, item in enumerate(scenario_v2["results"], start=1)
        }
        rejudge_tokens: dict[str, int] = {}
        for judge_usage in rejudge_usage:
            for key, value in judge_usage.get("token_summary", {}).items():
                rejudge_tokens[key] = rejudge_tokens.get(key, 0) + int(value)
        started_at = min((call.get("started_at") for call in calls if call.get("started_at")), default=None)
        ended_at = max((call.get("ended_at") for call in calls if call.get("ended_at")), default=None)
        quota_5h_start = quota_percent(calls[0].get("quota_before"), "5h") if calls else None
        quota_5h_end = quota_percent(calls[-1].get("quota_after"), "5h") if calls else None
        quota_7d_start = quota_percent(calls[0].get("quota_before"), "7d") if calls else None
        quota_7d_end = quota_percent(calls[-1].get("quota_after"), "7d") if calls else None
        commit_at = git("show", "-s", "--format=%cI", commit).strip()
        input_tokens = int(tokens.get("input_tokens", 0))
        cached_tokens = int(tokens.get("cached_input_tokens", 0))
        row: dict[str, object] = {
            "experiment": number,
            "stem": stem,
            "label": label,
            "commit": commit,
            "commit_at": commit_at,
            "started_at": started_at,
            "ended_at": ended_at,
            "technical_gate": legacy_checks["technical_gate"],
            "robustness": legacy_checks["robustness"],
            "interface": legacy_checks["interface"],
            "scenario_passed": scenario_counts["PASS"],
            "scenario_total": scenario_v2["total"],
            "scenario_evaluated": scenario_v2["evaluated"],
            "scenario_score": scenario_v2["score"],
            "scenario_coverage": scenario_v2["coverage"],
            "scenario_failed": scenario_counts["FAIL"],
            "scenario_crashed": scenario_counts["CRASH"],
            "scenario_unreached": scenario_counts["UNREACHED"],
            "scenario_untestable": scenario_counts["UNTESTABLE"],
            "scenario_clear_passed": scenario_v2["basis_scores"]["clear"]["passed"],
            "scenario_clear_evaluated": scenario_v2["basis_scores"]["clear"]["evaluated"],
            "scenario_clear_score": scenario_v2["basis_scores"]["clear"]["score"],
            "scenario_human_decision_passed": scenario_v2["basis_scores"]["human_decision"]["passed"],
            "scenario_human_decision_evaluated": scenario_v2["basis_scores"]["human_decision"]["evaluated"],
            "scenario_human_decision_score": scenario_v2["basis_scores"]["human_decision"]["score"],
            "scenario_v1_passed": legacy_checks["scenario_passed"],
            "scenario_v1_total": legacy_checks["scenario_total"],
            "scenario_v1_score": legacy_checks["scenario_score"],
            **scenario_status,
            "judge_1": judge_scores[0],
            "judge_2": judge_scores[1],
            "judge_3": judge_scores[2],
            "judge_score": statistics.mean(judge_scores),
            "judge_mean": statistics.mean(judge_scores),
            "judge_stdev": statistics.stdev(judge_scores),
            "judge_v1_mean": statistics.mean(legacy_judge_scores),
            "judge_v1_stdev": statistics.stdev(legacy_judge_scores),
            "critical_mean": statistics.mean(float(judge["critical"]) for judge in judges),
            "major_mean": statistics.mean(float(judge["major"]) for judge in judges),
            "minor_mean": statistics.mean(float(judge["minor"]) for judge in judges),
            "input_tokens": input_tokens,
            "cached_input_tokens": cached_tokens,
            "uncached_input_tokens": max(0, input_tokens - cached_tokens),
            "output_tokens": int(tokens.get("output_tokens", 0)),
            "reasoning_tokens": int(tokens.get("reasoning_output_tokens", tokens.get("reasoning_tokens", 0))),
            "cached_input_ratio": cached_tokens / input_tokens if input_tokens else 0.0,
            "elapsed_provider_seconds": float(usage.get("elapsed_seconds_total", 0)),
            "generation_seconds": float(calls[0].get("elapsed_seconds", 0)) if calls else 0.0,
            "judge_seconds_sum": sum(float(call.get("elapsed_seconds", 0)) for call in calls[1:]),
            "code_lines": len(code.splitlines()),
            "code_bytes": len(code.encode("utf-8")),
            "quota_5h_start": quota_5h_start,
            "quota_5h_end": quota_5h_end,
            "quota_7d_start": quota_7d_start,
            "quota_7d_end": quota_7d_end,
            "reevaluation_input_tokens": int(rejudge_tokens.get("input_tokens", 0)),
            "reevaluation_cached_input_tokens": int(rejudge_tokens.get("cached_input_tokens", 0)),
            "reevaluation_output_tokens": int(rejudge_tokens.get("output_tokens", 0)),
            "reevaluation_reasoning_tokens": int(rejudge_tokens.get("reasoning_output_tokens", rejudge_tokens.get("reasoning_tokens", 0))),
            "reevaluation_judge_seconds": sum(float(item.get("elapsed_seconds", 0)) for item in rejudge_usage),
            "evaluator_version": 2,
            "actual_subscription_cost": None,
        }
        rows.append(row)
    return rows


def save_data(rows: list[dict[str, object]]) -> None:
    (OUT_DIR / "metrics.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with (OUT_DIR / "metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def finish(name: str) -> None:
    plt.tight_layout()
    plt.savefig(OUT_DIR / name, dpi=180, bbox_inches="tight")
    plt.close()


def plots(rows: list[dict[str, object]]) -> None:
    labels = [str(row["label"]) for row in rows]
    x = np.arange(len(rows))

    width = 0.18
    fig, ax = plt.subplots(figsize=(13, 5.5))
    bars = [
        ax.bar(x - 1.5 * width, [row["robustness"] for row in rows], width, label="Runtime robustness"),
        ax.bar(x - 0.5 * width, [row["interface"] for row in rows], width, label="Interface"),
        ax.bar(x + 0.5 * width, [row["scenario_clear_score"] for row in rows], width, label="Clear-rule scenarios"),
        ax.bar(x + 1.5 * width, [row["scenario_human_decision_score"] for row in rows], width, label="Human-decision scenarios"),
    ]
    for group in bars:
        ax.bar_label(group, fmt="%.2f", padding=2, fontsize=8)
    for index, row in enumerate(rows):
        marker = "✓" if row["technical_gate"] == 1 else "✗"
        ax.text(index, 1.08, f"technical 01–04 {marker}", ha="center", fontsize=8)
    plt.ylim(0, 1.18)
    plt.xticks(x, labels, rotation=18, ha="right")
    plt.ylabel("Score within evidence group")
    plt.title("Evaluator v2 evidence groups (post-hoc; not aggregated)")
    ax.legend(loc="center left", bbox_to_anchor=(1.01, 0.5))
    finish("01_evidence_groups.png")

    fig, ax = plt.subplots(figsize=(11, 5.5))
    means = [row["judge_score"] for row in rows]
    stdevs = [row["judge_stdev"] for row in rows]
    mean_bars = ax.bar(x, means, yerr=stdevs, capsize=5, label="Judge mean (n=3)")
    ax.bar_label(mean_bars, fmt="%.3f", padding=5, fontsize=9)
    for judge_index, offset in enumerate((-0.10, 0, 0.10), start=1):
        ax.scatter(
            x + offset,
            [row[f"judge_{judge_index}"] for row in rows],
            color="black",
            alpha=0.35,
            s=22,
            zorder=3,
        )
    plt.ylim(0, 1)
    plt.xticks(x, labels, rotation=18, ha="right")
    plt.ylabel("Judge mean score")
    plt.title("Evaluator v2 judge mean (3 blind corrected reviews); error bars = sample SD")
    plt.legend()
    finish("02_judge_scores.png")

    fig, (tokens_ax, time_ax) = plt.subplots(2, 1, figsize=(11, 9), sharex=True)
    uncached = np.array([row["uncached_input_tokens"] for row in rows], dtype=float) / 1000
    cached = np.array([row["cached_input_tokens"] for row in rows], dtype=float) / 1000
    output = np.array([row["output_tokens"] for row in rows], dtype=float) / 1000
    tokens_ax.bar(x - 0.18, uncached, 0.36, label="Uncached input")
    tokens_ax.bar(x - 0.18, cached, 0.36, bottom=uncached, label="Cached input")
    tokens_ax.bar(x + 0.18, output, 0.36, label="Output")
    tokens_ax.set_ylabel("Tokens (thousands)")
    tokens_ax.set_title("Original experiment resource use (evaluator-v2 rejudges excluded)")
    tokens_ax.legend(ncol=3)

    generation = np.array([row["generation_seconds"] for row in rows], dtype=float) / 60
    judges = np.array([row["judge_seconds_sum"] for row in rows], dtype=float) / 60
    time_ax.bar(x, generation, label="Implementation")
    time_ax.bar(x, judges, bottom=generation, label="Three judges (summed)")
    time_ax.set_ylabel("Provider-call minutes")
    time_ax.set_xticks(x, labels, rotation=18, ha="right")
    time_ax.legend()
    finish("03_resource_usage.png")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for old_plot in OUT_DIR.glob("[0-9][0-9]_*.png"):
        old_plot.unlink()
    rows = collect()
    save_data(rows)
    plots(rows)
    plot_count = len(list(OUT_DIR.glob("[0-9][0-9]_*.png")))
    print(f"wrote {len(rows)} rows and {plot_count} plots to {OUT_DIR.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
