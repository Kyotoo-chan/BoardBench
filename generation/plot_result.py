#!/usr/bin/env python3
"""Plot one or two separated BoardBench result profiles."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

GROUPS = (
    ("Robustness", "robustness"),
    ("Interface", "interface"),
    ("Clear rules", "clear_rules"),
    ("Human decisions", "human_decisions"),
    ("Coverage", "coverage"),
)


def load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def setting(result: dict[str, object]) -> str:
    runs = result["runs"]
    generation = sorted({f"{run['model']}:{run['thinking']}" for run in runs})
    judges = result["review_evidence"]["neutral_judges"]
    judge_models = judges.get("models", ["unknown"])
    judge_thinking = judges.get("thinking", ["unknown"])
    return f"generation {', '.join(generation)} · judges {','.join(judge_models)}:{','.join(judge_thinking)}"


def plot(results: list[dict[str, object]], output: Path) -> None:
    if not 1 <= len(results) <= 2:
        raise ValueError("plots support one or two rulebook conditions")
    labels = [str(result["identity"].get("condition", f"condition {index + 1}")) for index, result in enumerate(results)]
    group_labels = [label for label, _ in GROUPS] + ["Neutral judges"]
    values = []
    for result in results:
        evidence = result["implementation_evidence"]
        values.append([evidence[key]["mean"] for _, key in GROUPS] + [result["review_evidence"]["neutral_judges"]["mean"]])

    x = np.arange(len(group_labels))
    width = 0.64 / len(results)
    fig, ax = plt.subplots(figsize=(10, 5.4))
    for index, (label, row) in enumerate(zip(labels, values)):
        offset = (index - (len(results) - 1) / 2) * width
        bars = ax.bar(x + offset, row, width, label=label)
        ax.bar_label(bars, fmt="%.2f", padding=2, fontsize=8)

    ax.set_ylim(0, 1.12)
    ax.set_ylabel("Score within evidence group")
    ax.set_xticks(x, group_labels, rotation=18, ha="right")
    ax.set_title(str(results[0]["identity"].get("game", "BoardBench")))
    if len(results) > 1:
        ax.legend(frameon=False)
    details = []
    for label, result in zip(labels, results):
        evidence = result["implementation_evidence"]
        details.append(
            f"{label}: {setting(result)} · n={result['reproducibility']['run_count']} · "
            f"technical={evidence['technical_gate_pass_rate']:.2f} · agentic={evidence['agentic_gate_pass_rate']:.2f}"
        )
    fig.text(0.5, 0.01, "\n".join(details), ha="center", va="bottom", fontsize=8)
    fig.tight_layout(rect=(0, 0.1, 1, 1))
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    plot([load(path) for path in args.result], args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
