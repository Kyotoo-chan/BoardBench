"""Parse a saved LLM-judge score.
Why: judge review is a qualitative score for likely missing rules and logic errors.
"""

from __future__ import annotations

import re
from pathlib import Path

from common import CheckContext, CheckResult

JUDGE_CHECK = True
SCORE_RE = re.compile(r"(?im)^\s*score\s*:\s*([01](?:\.\d+)?)\s*$")
CONFIDENCE_RE = re.compile(r"(?im)^\s*confidence\s*:\s*(low|medium|high)\b")


def find_default_judge_path(ctx: CheckContext) -> Path | None:
    code_stem = ctx.code_path.stem
    patterns = [f"{code_stem}_judge*.md", f"{ctx.game}_judge*.md"]
    for pattern in patterns:
        matches = sorted((ctx.repo_root / "outputs").glob(pattern))
        if matches:
            return matches[-1]
    return None


def parse_score(text: str) -> float | None:
    matches = SCORE_RE.findall(text)
    if not matches:
        return None
    try:
        score = float(matches[-1])
    except ValueError:
        return None
    if score < 0.0 or score > 1.0:
        return None
    return score


def run(ctx: CheckContext) -> CheckResult | str | None:
    judge_path = ctx.judge_path or find_default_judge_path(ctx)
    if judge_path is None:
        return f"missing LLM judge review: outputs/{ctx.code_path.stem}_judge*.md"
    if not judge_path.exists():
        return f"LLM judge review not found: {judge_path}"

    text = judge_path.read_text(encoding="utf-8")
    score = parse_score(text)
    if score is None:
        return "LLM judge review is missing machine-readable score: <0.0-1.0>"
    if CONFIDENCE_RE.search(text) is None:
        return "LLM judge review is missing machine-readable confidence"

    # A low judge score is data, not a runner failure. Invalid/missing format is
    # the only failure condition for this check.
    passed = round(score * 100)
    return CheckResult(passed, 100)
