#!/usr/bin/env python3
"""Plot one or two separated BoardBench result profiles."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

GROUPS = (
    ("Clear-basis-Szenarien (EV4)", "clear_basis_scenarios", "clear_rules"),
    ("Decision-basis-Szenarien (EV5)", "human_decision_basis_scenarios", "human_decisions"),
)

DISPLAY_NAMES = {"pdf": "Original-PDF", "clarified": "Präzisierte Fassung"}
COLORS = ("#579889", "#8972B3")


def load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def plot(results: list[dict[str, object]], output: Path) -> None:
    if not 1 <= len(results) <= 2:
        raise ValueError("plots support one or two rulebook conditions")
    conditions = [str(result["identity"].get("condition", f"condition {index + 1}")) for index, result in enumerate(results)]
    labels = [DISPLAY_NAMES.get(condition, condition) for condition in conditions]
    group_labels = [label for label, _, _ in GROUPS] + ["Neutrale Judges (EV7)"]
    values = []
    for result in results:
        evidence = result["implementation_evidence"]
        values.append([
            evidence[new_key if new_key in evidence else legacy_key]["mean"]
            for _, new_key, legacy_key in GROUPS
        ] + [result["review_evidence"]["neutral_judges"]["mean"]])

    x = np.arange(len(group_labels))
    width = 0.64 / len(results)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for index, (label, row) in enumerate(zip(labels, values)):
        offset = (index - (len(results) - 1) / 2) * width
        bars = ax.bar(x + offset, row, width, label=label, color=COLORS[index])
        ax.bar_label(bars, fmt="%.2f", padding=3, fontsize=9)

    ax.set_ylim(0, 1.15)
    ax.set_ylabel("Wert")
    ax.set_xticks(x, group_labels)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#D9D9D9", linewidth=0.7, alpha=0.6)
    ax.set_axisbelow(True)
    if len(results) > 1:
        ax.legend(loc="upper center", ncol=2, frameon=False)
    fig.tight_layout()
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
