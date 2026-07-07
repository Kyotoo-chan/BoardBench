#!/usr/bin/env python3
"""Run pi CLI generations for BoardBench games (oneshot + agentic).

Mirrors ``run_codex_series.py`` but uses ``pi -p`` with GPT-5.5 xhigh.

Example::

  python generation/run_pi_series.py --game catan --variant oneshot
  python generation/run_pi_series.py --game catan --all
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "checks") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "checks"))

from generation.config import RERUN_ORDER, activate_game_rules, game_spec, output_stem  # noqa: E402
from generation.game_run_workflow import auto_clear_before_run  # noqa: E402
from generation.llm_cli import (  # noqa: E402
    build_llm_command,
    extract_code_block,
    llm_failure_message,
    run_llm_subprocess,
)
from generation.run_codex_series import load_notebook_namespace, run_base_checks  # noqa: E402

DEFAULT_MODEL = "openai-codex/gpt-5.5:xhigh"
DEFAULT_EFFORT = "xhigh"


def configure_namespace(ns: dict, game: str, variant: str) -> None:
    ns["GAME"] = game
    ns["RUN_VARIANT"] = variant
    ns["LLM_BACKEND"] = "pi"
    ns["LLM_MODEL"] = DEFAULT_MODEL
    ns["LLM_EFFORT"] = DEFAULT_EFFORT
    ns["TIMEOUT_SECONDS"] = 4000 if variant == "agentic" else 2000
    spec = game_spec(game)
    ns["OPEN_SPIEL_GAME"] = spec.open_spiel_game
    ns["INCLUDE_OPENSPIEL_COMPARE"] = spec.include_openspiel_compare
    ns["USE_IMPLEMENTATION_BRIEF"] = spec.use_implementation_brief

    output_dir: Path = ns["OUTPUT_DIR"]
    stem = output_stem(game, "gpt", variant)
    ns["RUN_STEM"] = stem
    ns["IMPLEMENTATION_BRIEF_PATH"] = output_dir / f"{game}_implementation_brief.md"
    ns["CODE_PATH"] = output_dir / f"{stem}.py"
    ns["RESPONSE_PATH"] = output_dir / f"{stem}.md"
    ns["CHECK_LOG_PATH"] = output_dir / f"{stem}_checks.txt"
    ns["JUDGE_REVIEW_PATH"] = output_dir / f"{stem}_judge_gpt.md"


def run_pi_generation(ns: dict) -> float:
    game = ns["GAME"]
    variant = ns["RUN_VARIANT"]
    prompt_text, file_args = (
        ns["build_one_shot_prompt"]() if variant == "oneshot" else ns["build_agentic_prompt"]()
    )

    workspace: Path | None = None
    command_file_args = file_args
    cwd: Path | None = None
    if variant == "agentic":
        workspace, command_file_args = ns["prepare_agentic_workspace"](file_args)
        prompt_text = ns["rewrite_attachment_paths"](prompt_text, file_args, command_file_args)
        cwd = workspace

    command = build_llm_command(
        "pi",
        ns["LLM_MODEL"],
        ns["LLM_EFFORT"],
        mode="agentic" if variant == "agentic" else "oneshot",
        file_args=command_file_args,
        add_dirs=[cwd] if cwd is not None else None,
    )

    code_path: Path = ns["CODE_PATH"]
    response_path: Path = ns["RESPONSE_PATH"]
    output_dir: Path = ns["OUTPUT_DIR"]
    started = time.perf_counter()
    try:
        result = run_llm_subprocess(
            command,
            prompt_text=prompt_text,
            cwd=cwd,
            timeout=ns["TIMEOUT_SECONDS"],
            output_dir=output_dir,
        )
        response_path.write_text(result.stdout or "", encoding="utf-8")
        if result.returncode != 0:
            raise RuntimeError(llm_failure_message(result, step="pi generation"))

        code = extract_code_block(result.stdout or "")
        if code is not None:
            code_path.write_text(code, encoding="utf-8")
        elif workspace is not None and ns["copy_workspace_code"](workspace):
            pass
        elif code_path.exists():
            pass
        else:
            raise RuntimeError("No fenced python block in pi response and no workspace code file")

        elapsed = time.perf_counter() - started
        print(f"OK generation {elapsed:.1f}s -> {code_path.as_posix()}")
        return elapsed
    finally:
        if workspace is not None:
            shutil.rmtree(workspace, ignore_errors=True)


def run_one(game: str, variant: str, *, skip_checks: bool) -> None:
    auto_clear_before_run(game, "gpt", variant)
    activate_game_rules(game)
    ns = load_notebook_namespace(variant)
    configure_namespace(ns, game, variant)
    print(f"\n=== {game} {variant} (pi) ===")
    run_pi_generation(ns)
    if not skip_checks:
        code, _output = run_base_checks(ns)
        if code != 0:
            raise RuntimeError(f"base checks failed for {game} {variant}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", choices=RERUN_ORDER)
    parser.add_argument("--variant", choices=("oneshot", "agentic"))
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--skip-checks", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.all:
        for game in RERUN_ORDER:
            for variant in ("oneshot", "agentic"):
                run_one(game, variant, skip_checks=args.skip_checks)
        return 0
    if not args.game or not args.variant:
        raise SystemExit("Provide --game and --variant, or use --all")
    run_one(args.game, args.variant, skip_checks=args.skip_checks)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
