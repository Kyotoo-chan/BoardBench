#!/usr/bin/env python3
"""Run judge (+ OpenSpiel where configured) on existing Codex generation outputs.

Base checks 01-06 are assumed done by ``run_codex_series.py``. This script adds
the qualitative judge step and optional OpenSpiel compare, matching the manual
notebook pipeline order.
"""

from __future__ import annotations

import argparse
import sys
from functools import partial
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from generation.config import RERUN_ORDER, activate_game_rules, game_spec  # noqa: E402
from generation.llm_cli import run_llm_subprocess  # noqa: E402
from generation.run_codex_series import configure_namespace, load_notebook_namespace  # noqa: E402

DEFAULT_MODEL = "gpt-5.5"
DEFAULT_EFFORT = "xhigh"


def _patch_codex_subprocess(ns: dict) -> None:
    output_dir: Path = ns["OUTPUT_DIR"]
    ns["run_llm_subprocess"] = partial(run_llm_subprocess, output_dir=output_dir)


def run_eval(game: str, variant: str) -> None:
    activate_game_rules(game)
    ns = load_notebook_namespace(variant)
    configure_namespace(ns, game, variant)
    _patch_codex_subprocess(ns)

    spec = game_spec(game)
    code_path: Path = ns["CODE_PATH"]
    if not code_path.exists():
        raise FileNotFoundError(f"Missing generated code: {code_path.as_posix()}")

    print(f"\n=== {game} {variant} codex eval ===")
    try:
        ns["run_full_evaluation"](
            include_llm_judge=True,
            include_openspiel_compare=spec.include_openspiel_compare,
        )
    except RuntimeError as exc:
        print(f"WARN {exc}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", choices=RERUN_ORDER)
    parser.add_argument("--variant", choices=("oneshot", "agentic"))
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run eval for all games/variants that have outputs/<game>_<variant>.py",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.all:
        for game in RERUN_ORDER:
            for variant in ("oneshot", "agentic"):
                code_path = REPO_ROOT / "outputs" / f"{game}_{variant}.py"
                if code_path.exists():
                    run_eval(game, variant)
        return 0
    if not args.game or not args.variant:
        raise SystemExit("Provide --game and --variant, or use --all")
    run_eval(args.game, args.variant)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
