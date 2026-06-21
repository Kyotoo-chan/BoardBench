"""Check the saved LLM-judge review verdict.
Why: judge review is a qualitative check for likely missing rules and logic errors.
"""

from __future__ import annotations

import re
from pathlib import Path

from common import CheckContext

JUDGE_CHECK = True
PASSING_VERDICTS = {"pass", "provisional pass"}
VERDICT_RE = re.compile(r"(?im)^\s*verdict\s*:\s*(provisional pass|pass|revise|fail)\b")


def find_default_judge_path(ctx: CheckContext) -> Path | None:
    matches = sorted((ctx.repo_root / "outputs").glob(f"{ctx.game}_judge*.md"))
    return matches[-1] if matches else None


def run(ctx: CheckContext) -> str | None:
    judge_path = ctx.judge_path or find_default_judge_path(ctx)
    if judge_path is None:
        return f"missing LLM judge review: outputs/{ctx.game}_judge*.md"
    if not judge_path.exists():
        return f"LLM judge review not found: {judge_path}"

    text = judge_path.read_text(encoding="utf-8")
    match = VERDICT_RE.search(text)
    if match is None:
        return "LLM judge review is missing machine-readable verdict"

    verdict = match.group(1).lower()
    if verdict not in PASSING_VERDICTS:
        return f"LLM judge verdict is {verdict!r}: {judge_path}"

    return None
