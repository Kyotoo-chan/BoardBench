#!/usr/bin/env python3
"""LLM judge calibration: wrong rulebook vs existing code.

  python checks/run_judge_calibration.py --scenario ek_vs_hav
  python checks/run_judge_calibration.py --scenario aba_vs_ek --judge pi,codex
  python checks/run_judge_calibration.py --verify-only --scenario aba_vs_ek
"""

from __future__ import annotations

import argparse
import re
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
_CHECKS_DIR = Path(__file__).resolve().parent
for path in (REPO_ROOT, _CHECKS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from judge_packet import build_judge_packet  # noqa: E402
from generation.llm_cli import build_llm_command, ensure_direct_llm_response, run_llm_subprocess  # noqa: E402

MISMATCH_MAX_SCORE = 0.55
MIN_GAP_FROM_MATCHED = 0.10
SCORE_RE = re.compile(r"(?im)^\s*score\s*:\s*([01](?:\.\d+)?)\s*$")
MATCHED_JUDGE_RE = re.compile(r"score:\s*([01](?:\.\d+)?)")

PI_MODEL = "openai-codex/gpt-5.5:xhigh"
CODEX_MODEL = "gpt-5.4"
CLAUDE_MODEL = "opus"
TIMEOUT_SECONDS = 900

GAMES = REPO_ROOT / "inputs" / "games"


@dataclass(frozen=True)
class Scenario:
    name: str
    cases: tuple[tuple[str, str], ...]  # (stem, code rel path)
    rules_path: Path
    rules_slug: str
    note: str


SCENARIOS: dict[str, Scenario] = {
    "ek_vs_hav": Scenario(
        name="ek_vs_hav",
        cases=(
            ("expl_gpt_os", "outputs/expl_gpt_os.py"),
            ("expl_codex_os", "outputs/expl_codex_os.py"),
            ("expl_claude_os", "outputs/expl_claude_os.py"),
        ),
        rules_path=GAMES / "havannah" / "game_rules.pdf",
        rules_slug="havannah",
        note="CALIBRATION: code is Exploding Kittens; rulebook is Havannah. Expect score near 0.",
    ),
    "aba_vs_ek": Scenario(
        name="aba_vs_ek",
        cases=(("aba_gpt_os", "outputs/aba_gpt_os.py"),),
        rules_path=GAMES / "exploding_kittens" / "game_rules.pdf",
        rules_slug="expl",
        note="CALIBRATION: code is Abalone; rulebook is Exploding Kittens. Expect score near 0.",
    ),
}

JUDGE_DEFAULTS = {
    "pi": (PI_MODEL, "xhigh"),
    "codex": (CODEX_MODEL, "xhigh"),
    "claude": (CLAUDE_MODEL, "max"),
}


def parse_score(text: str) -> float | None:
    matches = SCORE_RE.findall(text)
    if not matches:
        return None
    try:
        score = float(matches[-1])
    except ValueError:
        return None
    return score if 0.0 <= score <= 1.0 else None


def matched_judge_score(stem: str) -> float | None:
    scores: list[float] = []
    for path in sorted((REPO_ROOT / "outputs").glob(f"{stem}_judge_*.md")):
        for match in MATCHED_JUDGE_RE.findall(path.read_text(encoding="utf-8")):
            try:
                scores.append(float(match))
            except ValueError:
                continue
    return max(scores) if scores else None


def review_path(code_stem: str, rules_slug: str, judge_backend: str) -> Path:
    suffix = "" if judge_backend == "pi" else f"_{judge_backend}"
    return REPO_ROOT / "outputs" / f"judge_cal_{code_stem}_vs_{rules_slug}{suffix}.md"


def run_one(
    scenario: Scenario,
    code_stem: str,
    code_rel: str,
    *,
    judge_backend: str,
) -> tuple[float, Path]:
    model, effort = JUDGE_DEFAULTS[judge_backend]
    code_path = REPO_ROOT / code_rel
    out_path = review_path(code_stem, scenario.rules_slug, judge_backend)

    with tempfile.NamedTemporaryFile(
        prefix=f"judge_cal_{code_stem}_",
        suffix=".md",
        dir=REPO_ROOT / "outputs",
        delete=False,
    ) as tmp:
        packet_path = Path(tmp.name)

    try:
        build_judge_packet(
            code_path=code_path,
            rules_path=scenario.rules_path,
            output_path=packet_path,
            game_label=f"{code_stem} ({scenario.name})",
            variant="calibration",
            note=scenario.note,
        )
        command = build_llm_command(judge_backend, model, effort, mode="judge")
        started = time.perf_counter()
        result = run_llm_subprocess(
            command,
            prompt_text=packet_path.read_text(encoding="utf-8"),
            cwd=REPO_ROOT,
            timeout=TIMEOUT_SECONDS,
        )
        text = ensure_direct_llm_response(result, step=f"judge cal {code_stem}/{judge_backend}")
        out_path.write_text(text, encoding="utf-8")
        elapsed = time.perf_counter() - started
        score = parse_score(text)
        if score is None:
            raise RuntimeError(f"no score in reply: {out_path.name}")
        print(
            f"OK   {code_stem} judge={judge_backend}  score={score:.3f}  {elapsed:.0f}s  -> {out_path.name}",
            flush=True,
        )
        return score, out_path
    finally:
        packet_path.unlink(missing_ok=True)


def verify_one(code_stem: str, rules_slug: str, judge_backend: str, score: float | None = None) -> tuple[bool, str]:
    path = review_path(code_stem, rules_slug, judge_backend)
    if not path.exists():
        return False, f"missing {path.name}"
    if score is None:
        score = parse_score(path.read_text(encoding="utf-8"))
    if score is None:
        return False, "no parseable score"

    matched = matched_judge_score(code_stem)
    reasons: list[str] = []
    if score > MISMATCH_MAX_SCORE:
        reasons.append(f"score {score:.3f} > {MISMATCH_MAX_SCORE}")
    if matched is not None and (matched - score) < MIN_GAP_FROM_MATCHED:
        reasons.append(f"gap to matched {matched:.3f} only {matched - score:.3f}")
    if reasons:
        return False, "; ".join(reasons)
    gap = f", gap={matched - score:.3f}" if matched is not None else ""
    return True, f"score={score:.3f}{gap}"


def parse_judge_list(raw: str) -> list[str]:
    backends = [part.strip() for part in raw.split(",") if part.strip()]
    unknown = set(backends) - set(JUDGE_DEFAULTS)
    if unknown:
        raise ValueError(f"unknown judge backends: {', '.join(sorted(unknown))}")
    return backends


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", default="ek_vs_hav", choices=sorted(SCENARIOS))
    parser.add_argument("--judge", default="pi", help="comma-separated: pi,codex,claude")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()

    scenario = SCENARIOS[args.scenario]
    if not scenario.rules_path.exists():
        print(f"FAIL missing rulebook: {scenario.rules_path}", flush=True)
        return 1

    judges = parse_judge_list(args.judge)
    total = len(scenario.cases) * len(judges)
    failed = 0

    for judge_backend in judges:
        for code_stem, code_rel in scenario.cases:
            if args.verify_only:
                ok, msg = verify_one(code_stem, scenario.rules_slug, judge_backend)
                print(f"{'OK' if ok else 'FAIL'} {code_stem}/{judge_backend}  {msg}", flush=True)
                if not ok:
                    failed += 1
                continue
            try:
                score, _ = run_one(scenario, code_stem, code_rel, judge_backend=judge_backend)
                ok, msg = verify_one(code_stem, scenario.rules_slug, judge_backend, score)
                if not ok:
                    print(f"FAIL verify {code_stem}/{judge_backend}  {msg}", flush=True)
                    failed += 1
                else:
                    print(f"     verify {code_stem}/{judge_backend}  {msg}", flush=True)
            except Exception as exc:
                print(f"FAIL {code_stem}/{judge_backend}  {exc}", flush=True)
                failed += 1

    ok_count = total - failed
    print(f"---- summary  {ok_count}/{total}  scenario={args.scenario}", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
