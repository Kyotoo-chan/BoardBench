"""Run selected BoardBench checks and print timing plus passed/total counts.
Why: the notebook and CLI both need one small, consistent check entry point.
"""

from __future__ import annotations

import argparse
import importlib.util
import time
from pathlib import Path
from typing import Any

from common import (
    DEFAULT_ROLLOUTS,
    CheckContext,
    CheckResult,
    DISPLAY_NAME_WIDTH,
    ParsedCheckLine,
    format_check_line,
    format_summary_line,
    resolve_code_path,
    resolve_repo_root,
    weighted_score_from_checks,
)


def load_check(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run BoardBench checks for a generated game result.")
    parser.add_argument("--game", required=True, help="Game slug used for output lookup")
    parser.add_argument("--code-path", default=None, help="Generated Python file to check")
    parser.add_argument("--rollouts", type=int, default=DEFAULT_ROLLOUTS, help="Random games to run in rollout checks")
    parser.add_argument("--max-steps", type=int, default=1000, help="Maximum steps per random game")
    parser.add_argument("--seed", type=int, default=1, help="Random seed for reproducible checks")
    parser.add_argument("--check", action="append", default=[], help="Run only this check, e.g. 05_random_rollouts")
    parser.add_argument("--no-summary", action="store_true", help="Skip the final summary line (for notebook pipeline phases)")
    return parser.parse_args()


def check_key(name: str) -> str:
    stem = name[:-3] if name.endswith(".py") else name
    if stem.startswith("check_"):
        stem = stem[6:]
    return stem


def selected_checks(check_dir: Path, requested: list[str]) -> list[Path]:
    paths = sorted(check_dir.glob("[0-9][0-9]_*.py"))
    if requested:
        names = {check_key(name) for name in requested}
        selected = [path for path in paths if check_key(path.stem) in names]
        missing = names - {check_key(path.stem) for path in selected}
        if missing:
            raise RuntimeError("unknown checks: " + ", ".join(sorted(missing)))
        return selected

    return paths


def normalize_result(value: Any) -> CheckResult:
    if isinstance(value, CheckResult):
        return value
    if value is None:
        return CheckResult(1, 1)
    return CheckResult(0, 1, str(value))


def main() -> int:
    args = parse_args()
    repo_root = resolve_repo_root()
    raw_code_path = args.code_path or f"outputs/{args.game}.py"
    ctx = CheckContext(
        repo_root=repo_root,
        game=args.game,
        code_path=resolve_code_path(raw_code_path, repo_root),
        judge_path=None,
        rollouts=args.rollouts,
        max_steps=args.max_steps,
        seed=args.seed,
    )

    check_dir = Path(__file__).resolve().parent
    try:
        check_paths = selected_checks(check_dir, args.check)
    except Exception as exc:
        print(f"FAIL check selection: {exc}", flush=True)
        return 1

    if not check_paths:
        print("no checks selected", flush=True)
        return 0

    total_started = time.perf_counter()
    failed = 0
    parsed_checks: list[ParsedCheckLine] = []
    name_width = max(DISPLAY_NAME_WIDTH, len("summary"), *(len(path.stem) for path in check_paths))

    for path in check_paths:
        started = time.perf_counter()
        try:
            module = load_check(path)
            if not hasattr(module, "run"):
                raise RuntimeError("missing run(ctx)")
            result = normalize_result(module.run(ctx))
        except Exception as exc:
            result = CheckResult(0, 1, str(exc) or exc.__class__.__name__)

        elapsed = time.perf_counter() - started
        status = "OK" if result.message is None else "FAIL"
        units = f"{result.passed}/{result.total}"
        if result.message:
            failed += 1
        print(
            format_check_line(status, path.stem, units, result.score, elapsed, result.message, name_width=name_width),
            flush=True,
        )
        parsed_checks.append(
            ParsedCheckLine(
                status=status,
                name=path.stem,
                passed=result.passed,
                total=result.total,
                score=result.score,
                elapsed=elapsed,
                message=result.message,
            )
        )

    total_elapsed = time.perf_counter() - total_started
    if not args.no_summary:
        passed_checks = len(check_paths) - failed
        print(
            format_summary_line(
                passed_checks,
                len(check_paths),
                weighted_score_from_checks(parsed_checks),
                total_elapsed,
                name_width=name_width,
            ),
            flush=True,
        )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
