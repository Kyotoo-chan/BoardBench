"""Render a separate comparison plot: pilot backends + GLM for one game.

Does not overwrite ``{slug}_scores.png`` / ``.txt``; writes ``{slug}_scores_glm.*``.

Example::

  python plots/make_glm_compare_plot.py --game exploding_kittens
"""

from __future__ import annotations

import importlib.util
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

from generation.config import GAME_SHORT, output_stem
from plots.collect_scores import (
    CHECK_LINE_RE,
    GAME_TITLES,
    PLOT_VARIANT,
    WORKFLOW_JUDGE_BACKENDS,
    game_plot_dir,
    merged_pinned_rows,
)

OUTPUTS = _REPO_ROOT / "outputs"

SMOKE_COUNT = 4
SMOKE_WEIGHT = 1
QUALITY_WEIGHT = 10

BACKENDS = [
    ("pi", "pi", "GPT-5.5 xhigh", "#4A9B7F"),
    ("codex", "Codex", "GPT-5.5 xhigh", "#3B6FB6"),
    ("claude", "Claude", "Opus 4.8 max", "#D96B4B"),
    ("glm", "GLM", "GLM-5.2 high", "#7C5CBF"),
]
GROUPS = [("one-shot", -0.62), ("agentic", 0.62)]
INNER_GAP = 0.18
BAR_WIDTH = 0.16
LEGEND_CHANNEL_W = 6

_spec = importlib.util.spec_from_file_location("judge90", _REPO_ROOT / "checks" / "90_llm_judge.py")
_judge_mod = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_judge_mod)
parse_score = _judge_mod.parse_score


def legend_label(channel: str, model: str) -> str:
    return f"{channel:<{LEGEND_CHANNEL_W}} · {model}"


def overall_score(quality_scores: list[float]) -> float:
    weighted = SMOKE_WEIGHT * SMOKE_COUNT * 1.0 + QUALITY_WEIGHT * sum(quality_scores)
    total = SMOKE_WEIGHT * SMOKE_COUNT + QUALITY_WEIGHT * len(quality_scores)
    return weighted / total


def read_check_score(check_log: Path, check_name: str) -> float | None:
    if not check_log.exists():
        return None
    for line in check_log.read_text(encoding="utf-8").splitlines():
        if not line.strip().startswith(("OK", "FAIL")):
            continue
        match = CHECK_LINE_RE.match(line)
        if match and match.group("name") == check_name:
            return float(match.group("score"))
    return None


def average_judge_score(stem: str) -> float | None:
    scores: list[float] = []
    for backend in WORKFLOW_JUDGE_BACKENDS:
        path = OUTPUTS / f"{stem}_judge_{backend}.md"
        if not path.exists():
            continue
        score = parse_score(path.read_text(encoding="utf-8"))
        if score is not None:
            scores.append(score)
    if not scores:
        return None
    return sum(scores) / len(scores)


def collect_glm_row(game: str, variant: str, quality_metrics: list[str]) -> list[float] | None:
    stem = output_stem(game, "glm", variant)
    check_log = OUTPUTS / f"{stem}_checks.txt"
    if not check_log.exists():
        return None
    row: list[float] = []
    for metric in quality_metrics:
        if metric == "90_llm_judge":
            value = average_judge_score(stem)
            row.append(0.0 if value is None else value)
        else:
            value = read_check_score(check_log, metric)
            row.append(1.0 if value is None else value)
    return row


def collect_spec(game: str) -> dict:
    slug = GAME_SHORT[game]
    quality_metrics = ["05_random_rollouts", "06_action_language", "90_llm_judge"]
    if game == "havannah":
        quality_metrics.append("99_openspiel_compare")

    scores: dict[tuple[str, str], list[float]] = dict(merged_pinned_rows(slug))
    glm_rows: dict[str, list[float]] = {}
    for variant in ("oneshot", "agentic"):
        row = collect_glm_row(game, variant, quality_metrics)
        if row is not None:
            plot_key = ("glm", PLOT_VARIANT[variant])
            scores[plot_key] = row
            glm_rows[variant] = row

    if not glm_rows:
        raise FileNotFoundError(
            f"No GLM outputs for {game}; expected outputs/{output_stem(game, 'glm', 'oneshot')}_checks.txt"
        )

    return {
        "title": f"{GAME_TITLES[game]} (with GLM)",
        "quality_metrics": quality_metrics,
        "scores": scores,
    }


def active_backends(overall: dict[tuple[str, str], float]) -> list[tuple[str, str, str, str]]:
    return [backend for backend in BACKENDS if all((backend[0], group_label) in overall for group_label, _ in GROUPS)]


def render_plot(slug: str, spec: dict, overall: dict[tuple[str, str], float]) -> Path:
    fig, ax = plt.subplots(figsize=(8.0, 4.8))
    backends = active_backends(overall)
    center_shift = (len(backends) - 1) / 2

    for group_label, group_center in GROUPS:
        for idx, (backend_key, _channel, _model, color) in enumerate(backends):
            offset = group_center + (idx - center_shift) * INNER_GAP
            score = overall[(backend_key, group_label)]
            ax.bar(offset, score, width=BAR_WIDTH, color=color, edgecolor="white", linewidth=1.0)
            ax.text(offset, score + 0.014, f"{score:.3f}", ha="center", va="bottom", fontsize=7.5)

    ax.set_xticks([center for _, center in GROUPS])
    ax.set_xticklabels([label for label, _ in GROUPS], fontsize=10)
    ax.set_xlim(-1.05, 1.05)
    ax.set_ylim(0.0, 1.06)
    ax.set_ylabel("weighted score")
    ax.set_title(spec["title"])
    ax.grid(axis="y", linestyle=":", alpha=0.35, linewidth=0.8, color="#AAAAAA")
    ax.set_axisbelow(True)

    legend_handles = [
        Patch(facecolor=color, edgecolor="white", label=legend_label(channel, model))
        for _, channel, model, color in backends
    ]
    legend_font = FontProperties(family="DejaVu Sans Mono", size=8.0)
    ax.legend(
        handles=legend_handles,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.08),
        ncol=2,
        frameon=False,
        handlelength=1.4,
        labelspacing=0.35,
        prop=legend_font,
    )

    fig.subplots_adjust(bottom=0.24)
    out_path = game_plot_dir(slug) / f"{slug}_scores_glm.png"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out_path


def write_detail(slug: str, spec: dict, overall: dict[tuple[str, str], float]) -> Path:
    backends = active_backends(overall)
    columns = [(backend_key, group_label) for group_label, _ in GROUPS for backend_key, _, _, _ in backends]
    short = {
        ("pi", "one-shot"): "pi_os",
        ("codex", "one-shot"): "cod_os",
        ("claude", "one-shot"): "cla_os",
        ("glm", "one-shot"): "glm_os",
        ("pi", "agentic"): "pi_ag",
        ("codex", "agentic"): "cod_ag",
        ("claude", "agentic"): "cla_ag",
        ("glm", "agentic"): "glm_ag",
    }

    lines = [
        f"{spec['title']} - overall weighted score",
        "(smoke 01-04 weight 1; quality 05/06/90/99 weight 10)",
        "GLM rows read from live outputs/; pilot backends from pinned scores.",
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

    out_path = game_plot_dir(slug) / f"{slug}_scores_glm.txt"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path


def main() -> int:
    import argparse

    from generation.config import RERUN_ORDER

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", default="exploding_kittens", choices=RERUN_ORDER)
    args = parser.parse_args()

    slug = GAME_SHORT[args.game]
    spec = collect_spec(args.game)
    overall = {key: overall_score(values) for key, values in spec["scores"].items()}
    png = render_plot(slug, spec, overall)
    txt = write_detail(slug, spec, overall)
    print(f"wrote {png.as_posix()} and {txt.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
