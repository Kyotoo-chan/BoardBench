#!/usr/bin/env python3
"""Create cross-game thesis figures without combining evidence groups."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parents[1]
PLOTS_ROOT = ROOT / "results" / "plots"
OVERVIEW_REL = Path("overview")
GAME_REL = {
    "6 nimmt!": Path("6_nimmt/v2"),
    "Abalone": Path("abalone/v3"),
    "Bohnanza": Path("bohnanza_base_2023/v2"),
    "CATAN": Path("catan/v2"),
    "Exploding Kittens": Path("exploding_kittens/v2"),
    "Wizard": Path("wizard/v2"),
}
ABALONE_V2_REL = Path("abalone/v2")
METRICS = (
    ("Clear-basis\nscenarios", "clear_basis_scenarios"),
    ("Human-decision-basis\nscenarios", "human_decision_basis_scenarios"),
    ("Neutral judges", "neutral_judges"),
)
COLORS = {
    "Original": "#4C78A8",
    "Clear-rule emphasis": "#F58518",
    "Clear-rule emphasis (repeat)": "#E45756",
    "Structured clarification": "#8E6C8A",
    "Source-gap clarification": "#54A24B",
}
GAMES = {
    "6 nimmt!": [
        ("Original", "results/scores/6_nimmt/v2/result.json"),
    ],
    "Abalone": [
        ("Original", "results/scores/abalone/v3/original_result.json"),
        ("Clear-rule emphasis", "results/scores/abalone/v3/setup_emphasis_result.json"),
    ],
    "Bohnanza": [
        ("Original", "results/scores/bohnanza_base_2023/v2/original_result.json"),
        ("Clear-rule emphasis (repeat)", "results/scores/bohnanza_base_2023/v2/clear_rule_emphasis_2_result.json"),
        ("Structured clarification", "results/scores/bohnanza_base_2023/v2/structured_clarification_1_result.json"),
    ],
    "CATAN": [
        ("Original", "results/scores/catan/v2/original_r3_judge_r2_result.json"),
        ("Clear-rule emphasis", "results/scores/catan/v2/clear_rule_emphasis_judge_r2_result.json"),
        ("Source-gap clarification", "results/scores/catan/v2/clarified_result.json"),
    ],
    "Exploding Kittens": [
        ("Original", "results/scores/exploding_kittens/v2/original_result.json"),
        ("Source-gap clarification", "results/scores/exploding_kittens/v2/clarified_result.json"),
    ],
    "Wizard": [
        ("Original", "results/scores/wizard/v2/original_result.json"),
        ("Source-gap clarification", "results/scores/wizard/v2/clarified_result.json"),
    ],
}
ABALONE_V2 = [
    ("Original", "results/scores/abalone/v2/original_result.json"),
    ("Clear-rule emphasis", "results/scores/abalone/v2/setup_emphasis_result.json"),
]


def overview_dir() -> Path:
    return PLOTS_ROOT / OVERVIEW_REL


def game_dir(relative: Path) -> Path:
    return PLOTS_ROOT / relative


def load(relative: str) -> dict:
    data = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    if data.get("schema_version") != 2:
        raise ValueError(f"expected result schema 2: {relative}")
    return data


def value(result: dict, key: str) -> float:
    group = result["review_evidence"][key] if key == "neutral_judges" else result["implementation_evidence"][key]
    result_value = float(group["mean"])
    if not 0 <= result_value <= 1:
        raise ValueError(f"metric outside [0, 1]: {key}={result_value}")
    return result_value


def judge_sd(result: dict) -> float:
    return float(result["review_evidence"]["neutral_judges"].get("sample_sd") or 0)


def draw_profile(ax, game: str, conditions: list[tuple[str, str]], label_size: int = 7) -> None:
    x = np.arange(len(METRICS))
    width = 0.72 / len(conditions)
    for index, (label, path) in enumerate(conditions):
        result = load(path)
        row = [value(result, key) for _, key in METRICS]
        offset = (index - (len(conditions) - 1) / 2) * width
        bars = ax.bar(x + offset, row, width, label=label, color=COLORS[label], yerr=[0, 0, judge_sd(result)], capsize=2)
        ax.bar_label(bars, labels=[f"{v:.2f}" for v in row], padding=2, fontsize=label_size, rotation=90)
    ax.set_title(game, fontweight="bold")
    ax.set_xticks(x, [label for label, _ in METRICS], fontsize=8)
    ax.set_ylim(0, 1.13)
    ax.grid(axis="y", color="#D9D9D9", linewidth=0.7, alpha=0.7)
    ax.spines[["top", "right"]].set_visible(False)


def save_game_profile(game: str, conditions: list[tuple[str, str]], directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    draw_profile(ax, game, conditions, label_size=9)
    ax.set_ylabel("Observed value")
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels, frameon=False, fontsize=8, loc="lower center", bbox_to_anchor=(0.5, 0.055), ncol=len(labels))
    fig.text(0.5, 0.005, "Separate evidence groups; no combined correctness score.", ha="center", fontsize=8)
    fig.tight_layout(rect=(0, 0.14, 1, 1))
    fig.savefig(directory / "evidence_profile.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def profiles() -> None:
    output = overview_dir()
    output.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(2, 3, figsize=(14, 8), sharey=True)
    for ax, (game, conditions) in zip(axes.flat, GAMES.items()):
        draw_profile(ax, game, conditions)
    axes[0, 0].set_ylabel("Observed value")
    axes[1, 0].set_ylabel("Observed value")
    handles = [Patch(color=color, label=label) for label, color in COLORS.items()]
    fig.suptitle("BoardBench evidence profiles by game and condition", fontsize=15)
    fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 0.945), ncol=len(handles), frameon=False, fontsize=8)
    fig.text(0.5, 0.01, "Evidence groups are shown side by side and are not combined into a correctness score.", ha="center", fontsize=9)
    fig.tight_layout(rect=(0, 0.035, 1, 0.90))
    fig.savefig(output / "evidence_profiles.png", dpi=220, bbox_inches="tight")
    plt.close(fig)

    for game, conditions in GAMES.items():
        save_game_profile(game, conditions, game_dir(GAME_REL[game]))
    save_game_profile("Abalone", ABALONE_V2, game_dir(ABALONE_V2_REL))


def deltas() -> None:
    rows = []
    for game, conditions in GAMES.items():
        if len(conditions) == 1:
            continue
        original = load(conditions[0][1])
        for label, path in conditions[1:]:
            result = load(path)
            rows.append((f"{game} — {label}", label, [value(result, key) - value(original, key) for _, key in METRICS]))

    fig, axes = plt.subplots(1, 3, figsize=(15, 6), sharey=True)
    y = np.arange(len(rows))
    for metric_index, (ax, (metric_label, _)) in enumerate(zip(axes, METRICS)):
        changes = [row[2][metric_index] for row in rows]
        colors = [COLORS[row[1]] for row in rows]
        ax.barh(y, changes, color=colors, height=0.62)
        ax.axvline(0, color="#333333", linewidth=0.9)
        for yi, change in zip(y, changes):
            ax.text(change + (0.008 if change >= 0 else -0.008), yi, f"{change:+.2f}", va="center", ha="left" if change >= 0 else "right", fontsize=8)
        ax.set_title(metric_label.replace("\n", " "), fontsize=10, fontweight="bold")
        ax.set_xlim(-0.55, 0.55)
        ax.grid(axis="x", color="#D9D9D9", linewidth=0.7, alpha=0.7)
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.set_yticks(y, [row[0] for row in rows], fontsize=8)
        ax.tick_params(axis="y", length=0)
        ax.invert_yaxis()
    fig.suptitle("Observed change from each game's original run", fontsize=15)
    fig.text(0.5, 0.01, "Positive values indicate a higher observed value; adapted successors are not independent replicates.", ha="center", fontsize=9)
    fig.tight_layout(rect=(0, 0.035, 1, 0.95))
    output = overview_dir()
    output.mkdir(parents=True, exist_ok=True)
    fig.savefig(output / "intervention_deltas.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    profiles()
    deltas()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
