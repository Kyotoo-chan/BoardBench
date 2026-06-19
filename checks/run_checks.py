from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path

from common import CheckContext, resolve_code_path, resolve_repo_root


def load_check(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run BoardBench checks for a generated game result.")
    parser.add_argument("--game", default="antichess", help="OpenSpiel/game name used for output lookup")
    parser.add_argument("--code-path", default=None, help="Generated Python file to check")
    parser.add_argument("--rollouts", type=int, default=100, help="Random games to run in rollout checks")
    parser.add_argument("--max-steps", type=int, default=1000, help="Maximum steps per random game")
    parser.add_argument("--seed", type=int, default=1, help="Random seed for reproducible checks")
    parser.add_argument("--check", action="append", default=[], help="Run only this check name, e.g. check_05_random_rollouts")
    parser.add_argument("--include-final", action="store_true", help="Also run final/slow checks such as OpenSpiel comparison")
    return parser.parse_args()


def selected_checks(check_dir: Path, requested: list[str], include_final: bool) -> list[Path]:
    paths = sorted(check_dir.glob("check_*.py"))
    if requested:
        names = {name[:-3] if name.endswith(".py") else name for name in requested}
        paths = [path for path in paths if path.stem in names]
        missing = names - {path.stem for path in paths}
        if missing:
            raise RuntimeError("unknown checks: " + ", ".join(sorted(missing)))
        return paths

    if include_final:
        return paths

    kept = []
    for path in paths:
        module = load_check(path)
        if not getattr(module, "FINAL_CHECK", False):
            kept.append(path)
    return kept


def main() -> int:
    args = parse_args()
    repo_root = resolve_repo_root()
    raw_code_path = args.code_path or f"code/outputs/{args.game}.py"
    ctx = CheckContext(
        repo_root=repo_root,
        game=args.game,
        code_path=resolve_code_path(raw_code_path, repo_root),
        rollouts=args.rollouts,
        max_steps=args.max_steps,
        seed=args.seed,
    )

    check_dir = Path(__file__).resolve().parent
    try:
        check_paths = selected_checks(check_dir, args.check, args.include_final)
    except Exception as exc:
        print(f"FAIL check selection: {exc}")
        return 1

    if not check_paths:
        print("no checks selected")
        return 0

    print(f"checking: {ctx.code_path}")
    failed = 0
    for path in check_paths:
        try:
            module = load_check(path)
            if not hasattr(module, "run"):
                raise RuntimeError("missing run(ctx)")

            message = module.run(ctx)
        except Exception as exc:
            message = str(exc) or exc.__class__.__name__

        if message:
            failed += 1
            print(f"FAIL {path.name}: {message}")
        else:
            print(f"OK   {path.name}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
