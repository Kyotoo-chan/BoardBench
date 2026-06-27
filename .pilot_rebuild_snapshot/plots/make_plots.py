"""Render BoardBench overall-score plots (one per game) plus a tiny detail file.

Layout: two variant groups (one-shot | agentic), three bars ordered pi | Codex | Claude.
Run: ``python plots/make_plots.py``
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Patch

from plots.collect_scores import collect_all_games

OUT_DIR = Path(__file__).resolve().parent

SMOKE_COUNT = 4
SMOKE_WEIGHT = 1
QUALITY_WEIGHT = 10

# channel, model detail, color — three distinct hues (no duplicate blues).
BACKENDS = [
    ("pi", "pi", "GPT-5.5 xhigh", "#4A9B7F"),
    ("codex", "Codex", "GPT-5.5 xhigh", "#3B6FB6"),
    ("claude", "Claude", "Opus 4.8 max", "#D96B4B"),
]
GROUPS = [("one-shot", -0.52), ("agentic", 0.52)]
INNER_GAP = 0.24
BAR_WIDTH = 0.20
LEGEND_CHANNEL_W = 6  # channel column; " · " then model on one line.


def legend_label(channel: str, model: str) -> str:
    return f"{channel:<{LEGEND_CHANNEL_W}} · {model}"


GAMES: dict[str, dict] = collect_all_games()


def overall_score(quality_scores: list[float]) -> float:
    weighted = SMOKE_WEIGHT * SMOKE_COUNT * 1.0 + QUALITY_WEIGHT * sum(quality_scores)
    total = SMOKE_WEIGHT * SMOKE_COUNT + QUALITY_WEIGHT * len(quality_scores)
    return weighted / total


def render_plot(slug: str, spec: dict, overall: dict[tuple[str, str], float]) -> Path:
    fig, ax = plt.subplots(figsize=(7.0, 4.6))

    for group_label, group_center in GROUPS:
        for idx, (backend_key, _channel, _model, color) in enumerate(BACKENDS):
            offset = group_center + (idx - 1) * INNER_GAP
            score = overall[(backend_key, group_label)]
            ax.bar(offset, score, width=BAR_WIDTH, color=color, edgecolor="white", linewidth=1.0)
            ax.text(offset, score + 0.014, f"{score:.3f}", ha="center", va="bottom", fontsize=8)

    ax.set_xticks([center for _, center in GROUPS])
    ax.set_xticklabels([label for label, _ in GROUPS], fontsize=10)
    ax.set_xlim(-0.95, 0.95)
    ax.set_ylim(0.0, 1.06)
    ax.set_ylabel("weighted score")
    ax.set_title(spec["title"])
    ax.grid(axis="y", linestyle=":", alpha=0.35, linewidth=0.8, color="#AAAAAA")
    ax.set_axisbelow(True)

    legend_handles = [
        Patch(facecolor=color, edgecolor="white", label=legend_label(channel, model))
        for _, channel, model, color in BACKENDS
    ]
    legend_font = FontProperties(family="DejaVu Sans Mono", size=8.5)
    ax.legend(
        handles=legend_handles,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.07),
        ncol=1,
        frameon=False,
        handlelength=1.4,
        labelspacing=0.35,
        prop=legend_font,
    )

    fig.subplots_adjust(bottom=0.22)
    out_path = OUT_DIR / f"{slug}_scores.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out_path


def write_detail(slug: str, spec: dict, overall: dict[tuple[str, str], float]) -> Path:
    columns = [(backend_key, group_label) for group_label, _ in GROUPS for backend_key, _, _, _ in BACKENDS]
    short = {
        ("pi", "one-shot"): "pi_os",
        ("codex", "one-shot"): "cod_os",
        ("claude", "one-shot"): "cla_os",
        ("pi", "agentic"): "pi_ag",
        ("codex", "agentic"): "cod_ag",
        ("claude", "agentic"): "cla_ag",
    }

    lines = [
        f"{spec['title']} - overall weighted score",
        "(smoke 01-04 weight 1; quality 05/06/90/99 weight 10)",
        "",
    ]
    for key in columns:
        backend_key, group_label = key
        row = next((channel, model) for bk, channel, model, _ in BACKENDS if bk == backend_key)
        lines.append(f"{legend_label(row[0], row[1])}  {group_label:<9}: {overall[key]:.3f}")
    lines.extend(["", f"{'per check':<22}" + "".join(f"{short[k]:>8}" for k in columns)])
    metrics = spec["quality_metrics"]
    scores = spec["scores"]
    for i, metric in enumerate(metrics):
        row = "".join(f"{scores[k][i]:>8.3f}" for k in columns)
        lines.append(f"{metric:<22}{row}")
    lines.append(f"{'01-04 smoke':<22}" + "".join(f"{1.0:>8.3f}" for _ in columns))

    out_path = OUT_DIR / f"{slug}_scores.txt"
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path


def main() -> None:
    for slug, spec in GAMES.items():
        overall = {key: overall_score(values) for key, values in spec["scores"].items()}
        png = render_plot(slug, spec, overall)
        txt = write_detail(slug, spec, overall)
        print(f"wrote {png.as_posix()} and {txt.as_posix()}")


if __name__ == "__main__":
    main()
