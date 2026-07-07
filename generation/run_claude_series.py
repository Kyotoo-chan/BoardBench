#!/usr/bin/env python3
"""Run Claude CLI generations for BoardBench games (oneshot + agentic).

Mirrors ``run_codex_series.py`` but uses ``claude -p`` with subscription auth.
Retries on Claude session-limit errors (waits 5 hours by default).

Example::

  python generation/run_claude_series.py --game catan --variant oneshot
  python generation/run_claude_series.py --game catan --all
"""

from __future__ import annotations

import argparse
import json
import re
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
from generation.llm_cli import (  # noqa: E402
    build_llm_command,
    extract_code_block,
    llm_failure_message,
    run_llm_subprocess,
)
from generation.run_codex_series import configure_namespace as _codex_configure  # noqa: E402
from generation.run_codex_series import load_notebook_namespace, run_base_checks  # noqa: E402

DEFAULT_MODEL = "opus"
DEFAULT_EFFORT = "max"
SESSION_LIMIT_WAIT_SECONDS = 5 * 3600
SESSION_LIMIT_RE = re.compile(r"session limit|hit your session limit", re.I)


def configure_namespace(ns: dict, game: str, variant: str) -> None:
    _codex_configure(ns, game, variant)
    ns["LLM_BACKEND"] = "claude"
    ns["LLM_MODEL"] = DEFAULT_MODEL
    ns["LLM_EFFORT"] = DEFAULT_EFFORT
    ns["TIMEOUT_SECONDS"] = 4000 if variant == "agentic" else 3600
    stem = output_stem(game, "claude", variant)
    ns["RUN_STEM"] = stem
    ns["CODE_PATH"] = ns["OUTPUT_DIR"] / f"{stem}.py"
    ns["RESPONSE_PATH"] = ns["OUTPUT_DIR"] / f"{stem}.md"
    ns["CHECK_LOG_PATH"] = ns["OUTPUT_DIR"] / f"{stem}_checks.txt"
    ns["JUDGE_REVIEW_PATH"] = ns["OUTPUT_DIR"] / f"{stem}_judge_claude.md"


def run_claude_generation(ns: dict) -> float:
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
        "claude",
        ns["LLM_MODEL"],
        ns["LLM_EFFORT"],
        mode="agentic" if variant == "agentic" else "oneshot",
        file_args=command_file_args,
        add_dirs=[cwd] if cwd is not None else None,
    )

    response_path: Path = ns["RESPONSE_PATH"]
    code_path: Path = ns["CODE_PATH"]
    output_dir: Path = ns["OUTPUT_DIR"]
    output_dir.mkdir(parents=True, exist_ok=True)

    started_total = time.perf_counter()
    attempt = 0
    while True:
        attempt += 1
        started = time.perf_counter()
        try:
            result = run_llm_subprocess(
                command,
                prompt_text=prompt_text,
                cwd=cwd,
                timeout=ns["TIMEOUT_SECONDS"],
                output_dir=output_dir,
            )
            if result.returncode != 0:
                detail = llm_failure_message(result, step="claude generation")
                if SESSION_LIMIT_RE.search(detail):
                    raise RuntimeError(detail)
                raise RuntimeError(detail)

            response_text = result.stdout or ""
            response_path.write_text(response_text, encoding="utf-8")
            code = extract_code_block(response_text)
            if code is not None:
                code_path.write_text(code, encoding="utf-8")
            elif workspace is not None and ns["copy_workspace_code"](workspace):
                pass
            elif code_path.exists():
                pass
            else:
                raise RuntimeError("No fenced python block in Claude response and no workspace code file")

            elapsed = time.perf_counter() - started_total
            print(f"OK generation {elapsed:.1f}s -> {code_path.as_posix()}")
            return elapsed
        except RuntimeError as exc:
            if not SESSION_LIMIT_RE.search(str(exc)):
                raise
            waited = time.perf_counter() - started_total
            print(
                f"session limit hit after {waited:.0f}s (attempt {attempt}); "
                f"waiting {SESSION_LIMIT_WAIT_SECONDS // 3600}h",
                flush=True,
            )
            time.sleep(SESSION_LIMIT_WAIT_SECONDS)
        finally:
            if workspace is not None and attempt > 1:
                # ponytail: rebuild workspace between retries after a partial agentic run
                shutil.rmtree(workspace, ignore_errors=True)
                workspace, command_file_args = ns["prepare_agentic_workspace"](file_args)
                prompt_text = ns["rewrite_attachment_paths"](
                    ns["build_agentic_prompt"]()[0], file_args, command_file_args
                )
                cwd = workspace
                command = build_llm_command(
                    "claude",
                    ns["LLM_MODEL"],
                    ns["LLM_EFFORT"],
                    mode="agentic",
                    file_args=command_file_args,
                    add_dirs=[cwd],
                )


def run_one(game: str, variant: str, *, skip_checks: bool) -> None:
    activate_game_rules(game)
    ns = load_notebook_namespace(variant)
    configure_namespace(ns, game, variant)
    print(f"\n=== {game} {variant} (claude) ===", flush=True)
    run_claude_generation(ns)
    if not skip_checks:
        code, _output = run_base_checks(ns)
        if code != 0:
            raise RuntimeError(f"base checks failed for {game} {variant}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", choices=RERUN_ORDER)
    parser.add_argument("--variant", choices=("oneshot", "agentic"))
    parser.add_argument("--all", action="store_true", help="Run all games in RERUN_ORDER")
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
