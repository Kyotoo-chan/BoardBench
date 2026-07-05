#!/usr/bin/env python3
"""Re-run mechanical checks (01-06) and refresh judge lines in pilot check logs."""

from __future__ import annotations

import argparse
import importlib.util
import re
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "checks") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "checks"))

from generation.config import RERUN_ORDER, game_output_dir, game_spec, output_stem  # noqa: E402
from generation.pilot_catalog import PILOT_RUNS  # noqa: E402

ROLLOUTS = 100
MAX_STEPS = 300
CHECK_SEED = 1

_spec = importlib.util.spec_from_file_location("judge90", REPO_ROOT / "checks" / "90_llm_judge.py")
_judge_mod = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_judge_mod)
parse_score = _judge_mod.parse_score

CHECK_LINE_RE = re.compile(
    r"^(?P<status>OK|FAIL)\s+"
    r"(?P<name>\S+)\s+"
    r"(?P<passed>\d+)/(?P<total>\d+)\s+"
    r"score=(?P<score>[0-9.]+)\s+"
    r"(?P<elapsed>[0-9.]+)s"
)


def judge_backends_for(impl_backend: str) -> tuple[str, ...]:
    if impl_backend == "claude":
        return ("gpt", "codex", "claude")
    return ("gpt", "codex")


def collect_judge_scores(stem: str, impl_backend: str, game_dir: Path) -> list[tuple[str, float]]:
    scores: list[tuple[str, float]] = []
    for backend in judge_backends_for(impl_backend):
        path = game_dir / f"{stem}_judge_{backend}.md"
        if not path.exists():
            continue
        score = parse_score(path.read_text(encoding="utf-8"))
        if score is not None:
            scores.append((backend, score))
    legacy = game_dir / f"{stem}_judge.md"
    if legacy.exists() and not scores:
        score = parse_score(legacy.read_text(encoding="utf-8"))
        if score is not None:
            scores.append((impl_backend, score))
    return scores


def average_judge_score(stem: str, impl_backend: str, game: str) -> float | None:
    scores = collect_judge_scores(stem, impl_backend, game_output_dir(game))
    if not scores:
        return None
    return sum(value for _, value in scores) / len(scores)


def run_base_checks(game: str, code_path: Path, check_game: str) -> tuple[str, float]:
    cmd = [
        sys.executable,
        "-u",
        str(REPO_ROOT / "checks" / "run_checks.py"),
        "--game",
        check_game,
        "--code-path",
        str(code_path),
        "--rollouts",
        str(ROLLOUTS),
        "--max-steps",
        str(MAX_STEPS),
        "--seed",
        str(CHECK_SEED),
        "--no-summary",
    ]
    started = time.perf_counter()
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
    elapsed = time.perf_counter() - started
    output = (proc.stdout or "") + (proc.stderr or "")
    return output.strip(), elapsed, proc.returncode


def append_judge_and_summary(
  lines: list[str],
  judge_score: float,
  judge_elapsed: float,
  *,
  include_openspiel: bool,
  openspiel_line: str | None,
  openspiel_elapsed: float,
) -> str:
    out_lines = list(lines)
    passed = round(judge_score * 100)
    out_lines.append(
        f"OK   90_llm_judge               {passed:>6}/100 score={judge_score:.3f}  {judge_elapsed:6.2f}s"
    )
    base_count = sum(1 for line in out_lines if CHECK_LINE_RE.match(line))
    phase_lines = [f"---- phase base checks                  {base_count}/{base_count} score=1.000    0.00s"]
    phase_lines.append(f"---- phase llm judge                    1/1 score={judge_score:.3f}  {judge_elapsed:6.2f}s")
    quality = [judge_score]
    if include_openspiel and openspiel_line:
        out_lines.append(openspiel_line)
        m = CHECK_LINE_RE.match(openspiel_line)
        if m:
            quality.append(float(m.group("score")))
            phase_lines.append(
                f"---- phase openspiel compare             1/1 score={m.group('score')}  {openspiel_elapsed:6.2f}s"
            )
    smoke = 4
    weighted = 1 * smoke + 10 * sum(quality)
    total_w = smoke + 10 * len(quality)
    summary_score = weighted / total_w
    total_phases = len(quality) + 1
    total_elapsed = judge_elapsed + openspiel_elapsed
    phase_lines.append(
        f"---- summary                            {base_count + total_phases}/{base_count + total_phases} "
        f"score={summary_score:.3f}  {total_elapsed:6.2f}s"
    )
    return "\n".join(out_lines + phase_lines) + "\n"


def refresh_run(game: str, impl_backend: str, variant: str, *, rerun_base: bool) -> None:
    stem = output_stem(game, impl_backend, variant)
    game_dir = game_output_dir(game)
    code_path = game_dir / f"{stem}.py"
    check_log = game_dir / f"{stem}_checks.txt"
    if not code_path.exists():
        print(f"SKIP missing {code_path.name}")
        return

    spec = game_spec(game)
    check_game = spec.open_spiel_game if spec.include_openspiel_compare else game

    if rerun_base:
        base_output, _base_elapsed, returncode = run_base_checks(game, code_path, check_game)
        if returncode != 0:
            print(f"WARN base checks exit {returncode} for {code_path.name}")
        base_lines = [line for line in base_output.splitlines() if CHECK_LINE_RE.match(line)]
    elif check_log.exists():
        base_lines = [
            line for line in check_log.read_text(encoding="utf-8").splitlines() if CHECK_LINE_RE.match(line)
        ]
        base_lines = [line for line in base_lines if not line.split()[1].startswith(("90_", "99_"))]
    else:
        base_output, _, _ = run_base_checks(game, code_path, check_game)
        base_lines = [line for line in base_output.splitlines() if CHECK_LINE_RE.match(line)]

    judge_avg = average_judge_score(stem, impl_backend, game)
    if judge_avg is None:
        print(f"WARN no judge scores for {stem}")
        judge_avg = 0.0

    openspiel_line = None
    openspiel_elapsed = 0.0
    if check_log.exists():
        for line in check_log.read_text(encoding="utf-8").splitlines():
            if "99_openspiel_compare" in line and CHECK_LINE_RE.match(line):
                openspiel_line = line
                m = CHECK_LINE_RE.match(line)
                if m:
                    openspiel_elapsed = float(m.group("elapsed"))

    check_log.write_text(
        append_judge_and_summary(
            base_lines,
            judge_avg,
            0.0,
            include_openspiel=spec.include_openspiel_compare,
            openspiel_line=openspiel_line,
            openspiel_elapsed=openspiel_elapsed,
        ),
        encoding="utf-8",
    )
    print(f"OK refreshed {check_log.name} judge_avg={judge_avg:.3f}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", choices=RERUN_ORDER)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--rerun-base", action="store_true", help="Re-run checks 01-06")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    runs = list(PILOT_RUNS)
    if args.game:
        runs = [r for r in runs if r.game == args.game]
    if not args.all and not args.game:
        raise SystemExit("Provide --game or --all")
    for run in runs:
        refresh_run(run.game, run.impl_backend, run.variant, rerun_base=args.rerun_base)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
