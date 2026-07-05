"""Collect pilot scores from outputs/ for plots."""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "checks") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "checks"))

from generation.config import GAME_SHORT, RERUN_ORDER, output_stem  # noqa: E402
OUT_DIR = REPO_ROOT / "outputs"

CHECK_LINE_RE = re.compile(
    r"^(?P<status>OK|FAIL)\s+"
    r"(?P<name>\S+)\s+"
    r"(?P<passed>\d+)/(?P<total>\d+)\s+"
    r"score=(?P<score>[0-9.]+)"
)

_spec = importlib.util.spec_from_file_location("judge90", REPO_ROOT / "checks" / "90_llm_judge.py")
_judge_mod = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_judge_mod)
parse_score = _judge_mod.parse_score

GAME_TITLES = {
    "havannah": "Havannah",
    "abalone": "Abalone",
    "exploding_kittens": "Exploding Kittens",
    "mahjong": "Mahjong",
}

PLOT_BACKEND = {
    "gpt": "pi",
    "codex": "codex",
    "claude": "claude",
}

PLOT_VARIANT = {
    "oneshot": "one-shot",
    "agentic": "agentic",
}

# Quality rows when outputs/ was cleared but pilot scores live in git history.
# hav rows include 99_openspiel_compare as the fourth value.
PINNED_QUALITY: dict[str, dict[tuple[str, str], list[float]]] = {
    "hav": {
        ("pi", "one-shot"): [0.0, 0.0, 0.0, 0.996],
        ("pi", "agentic"): [1.0, 1.0, 0.90, 0.996],
        ("codex", "one-shot"): [1.0, 1.0, 0.88, 1.0],
        ("codex", "agentic"): [1.0, 1.0, 0.88, 1.0],
        ("claude", "one-shot"): [1.0, 1.0, 0.75, 0.999],
        ("claude", "agentic"): [1.0, 1.0, 0.85, 0.996],
    },
    "aba": {
        ("pi", "one-shot"): [1.0, 1.0, 0.60],
        ("pi", "agentic"): [1.0, 1.0, 0.78],
        ("codex", "one-shot"): [1.0, 1.0, 0.62],
        ("codex", "agentic"): [1.0, 1.0, 0.76],
        ("claude", "one-shot"): [1.0, 1.0, 0.80],
        ("claude", "agentic"): [1.0, 1.0, 0.85],
    },
    "expl": {
        ("pi", "one-shot"): [0.09, 0.971, 0.685],
        ("pi", "agentic"): [1.0, 1.0, 0.71],
        ("codex", "one-shot"): [1.0, 1.0, 0.55],
        ("codex", "agentic"): [1.0, 1.0, 0.75],
        ("claude", "one-shot"): [1.0, 1.0, 0.767],
        ("claude", "agentic"): [1.0, 1.0, 0.853],
    },
}


def judge_backends_for(impl_backend: str) -> tuple[str, ...]:
    if impl_backend == "claude":
        return ("gpt", "codex", "claude")
    return ("gpt", "codex")


def average_judge_score(stem: str, impl_backend: str) -> float | None:
    scores: list[float] = []
    for backend in judge_backends_for(impl_backend):
        path = OUT_DIR / f"{stem}_judge_{backend}.md"
        if not path.exists():
            continue
        score = parse_score(path.read_text(encoding="utf-8"))
        if score is not None:
            scores.append(score)
    if not scores:
        legacy = OUT_DIR / f"{stem}_judge.md"
        if legacy.exists():
            score = parse_score(legacy.read_text(encoding="utf-8"))
            if score is not None:
                scores.append(score)
    if not scores:
        return None
    return sum(scores) / len(scores)


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


def collect_game_scores(game: str) -> dict:
    slug = GAME_SHORT[game]
    quality_metrics = ["05_random_rollouts", "06_action_language", "90_llm_judge"]
    if game == "havannah":
        quality_metrics.append("99_openspiel_compare")

    scores: dict[tuple[str, str], list[float]] = {}
    for impl in ("gpt", "codex", "claude"):
        for variant in ("oneshot", "agentic"):
            stem = output_stem(game, impl, variant)
            check_log = OUT_DIR / f"{stem}_checks.txt"
            row: list[float] = []
            for metric in quality_metrics:
                if metric == "90_llm_judge":
                    value = average_judge_score(stem, impl)
                    if value is None:
                        value = 0.0
                    row.append(value)
                else:
                    value = read_check_score(check_log, metric)
                    row.append(1.0 if value is None else value)
            plot_key = (PLOT_BACKEND[impl], PLOT_VARIANT[variant])
            scores[plot_key] = row

    slug = GAME_SHORT[game]
    for plot_key, pinned in PINNED_QUALITY.get(slug, {}).items():
        impl = "gpt" if plot_key[0] == "pi" else plot_key[0]
        variant = "oneshot" if plot_key[1] == "one-shot" else "agentic"
        stem = output_stem(game, impl, variant)
        if not (OUT_DIR / f"{stem}_checks.txt").exists():
            scores[plot_key] = pinned

    return {
        "title": GAME_TITLES[game],
        "quality_metrics": quality_metrics,
        "scores": scores,
    }


def collect_all_games() -> dict[str, dict]:
    return {GAME_SHORT[game]: collect_game_scores(game) for game in RERUN_ORDER}
