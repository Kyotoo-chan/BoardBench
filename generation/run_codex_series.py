#!/usr/bin/env python3
"""Run Codex CLI generations for all three pilot games (oneshot + agentic).

Uses the same prompts and check pipeline as pi/Claude runs, but calls
`npx @openai/codex exec` directly. Intended for the `codex-pilot-rerun` branch.

Example:
  python generation/run_codex_series.py --game havannah --variant oneshot
  python generation/run_codex_series.py --all
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
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
    run_codex_subprocess,
)

DEFAULT_MODEL = "gpt-5.5"
DEFAULT_EFFORT = "xhigh"
ROLLOUTS = 100
MAX_STEPS = 300
CHECK_SEED = 1


def load_notebook_namespace(variant: str) -> dict:
    notebook_path = REPO_ROOT / ("evaluation2.ipynb" if variant == "oneshot" else "evaluation.ipynb")
    payload = json.loads(notebook_path.read_text(encoding="utf-8"))
    code = payload["cells"][0]["source"]
    if isinstance(code, list):
        code = "".join(code)
    namespace: dict = {"__name__": "__main__", "Path": Path}
    exec(code, namespace)
    return namespace


def run_codex_generation(ns: dict) -> float:
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
        "codex",
        ns["LLM_MODEL"],
        ns["LLM_EFFORT"],
        mode="agentic" if variant == "agentic" else "oneshot",
        file_args=command_file_args,
        add_dirs=[cwd] if cwd is not None else None,
    )

    response_path: Path = ns["RESPONSE_PATH"]
    code_path: Path = ns["CODE_PATH"]
    output_dir = ns["OUTPUT_DIR"]
    output_dir.mkdir(parents=True, exist_ok=True)

    started = time.perf_counter()
    with tempfile.NamedTemporaryFile(
        prefix=f"boardbench_{game}_{variant}_codex_",
        suffix=".md",
        delete=False,
        dir=output_dir,
    ) as tmp:
        message_path = Path(tmp.name)

    try:
        result = run_codex_subprocess(
            command,
            prompt_text=prompt_text,
            output_message_path=message_path,
            timeout=ns["TIMEOUT_SECONDS"],
            cwd=REPO_ROOT,
        )
        if result.returncode != 0:
            raise RuntimeError(llm_failure_message(result, step="codex generation"))

        response_text = message_path.read_text(encoding="utf-8")
        if not response_text.strip():
            raise RuntimeError("Codex returned an empty last message")

        response_path.write_text(response_text, encoding="utf-8")
        code = extract_code_block(response_text)
        if code is not None:
            code_path.write_text(code, encoding="utf-8")
        elif workspace is not None and ns["copy_workspace_code"](workspace):
            pass
        elif code_path.exists():
            pass
        else:
            raise RuntimeError("No fenced python block in Codex response and no workspace code file")

        elapsed = time.perf_counter() - started
        print(f"OK generation {elapsed:.1f}s -> {code_path.as_posix()}")
        return elapsed
    finally:
        message_path.unlink(missing_ok=True)
        if workspace is not None:
            shutil.rmtree(workspace, ignore_errors=True)


def run_base_checks(ns: dict) -> tuple[int, str]:
    spec = game_spec(ns["GAME"])
    check_log: Path = ns["CHECK_LOG_PATH"]
    cmd = [
        sys.executable,
        "-u",
        str(REPO_ROOT / "checks" / "run_checks.py"),
        "--game",
        spec.open_spiel_game if spec.include_openspiel_compare else ns["GAME"],
        "--code-path",
        str(ns["CODE_PATH"]),
        "--rollouts",
        str(ROLLOUTS),
        "--max-steps",
        str(MAX_STEPS),
        "--seed",
        str(CHECK_SEED),
    ]
    started = time.perf_counter()
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
    elapsed = time.perf_counter() - started
    output = (proc.stdout or "") + (proc.stderr or "")
    check_log.write_text(output, encoding="utf-8")
    summary = next((line for line in output.splitlines() if line.startswith("---- summary")), "no summary")
    print(f"{summary}  ({elapsed:.1f}s checks)")
    return proc.returncode, output


def configure_namespace(ns: dict, game: str, variant: str) -> None:
    ns["GAME"] = game
    ns["RUN_VARIANT"] = variant
    ns["LLM_BACKEND"] = "codex"
    ns["LLM_MODEL"] = DEFAULT_MODEL
    ns["LLM_EFFORT"] = DEFAULT_EFFORT
    ns["TIMEOUT_SECONDS"] = 4000 if variant == "agentic" else 2000
    spec = game_spec(game)
    ns["OPEN_SPIEL_GAME"] = spec.open_spiel_game
    ns["INCLUDE_OPENSPIEL_COMPARE"] = spec.include_openspiel_compare
    ns["USE_IMPLEMENTATION_BRIEF"] = spec.use_implementation_brief

    output_dir: Path = ns["OUTPUT_DIR"]
    stem = output_stem(game, "codex", variant)
    ns["VARIANT_STEMS"] = {
        "oneshot": output_stem(game, "codex", "oneshot"),
        "agentic": output_stem(game, "codex", "agentic"),
    }
    ns["RUN_STEM"] = stem
    ns["IMPLEMENTATION_BRIEF_PATH"] = output_dir / f"{game}_implementation_brief.md"
    ns["CODE_PATH"] = output_dir / f"{stem}.py"
    ns["RESPONSE_PATH"] = output_dir / f"{stem}.md"
    ns["CHECK_LOG_PATH"] = output_dir / f"{stem}_checks.txt"
    ns["JUDGE_PACKET_PATH"] = output_dir / f"{stem}_judge_packet.md"
    ns["JUDGE_REVIEW_PATH"] = output_dir / f"{stem}_judge.md"
    ns["PRE_ALIGN_CODE_PATH"] = output_dir / f"{stem}_pre_align.py"
    ns["ACTION_ALIGN_RESPONSE_PATH"] = output_dir / f"{stem}_action_align.md"
    ns["GENERATION_PACKET_PATH"] = output_dir / f"{stem}_generation_packet.md"


def run_one(game: str, variant: str, *, skip_checks: bool) -> None:
    activate_game_rules(game)
    ns = load_notebook_namespace(variant)
    configure_namespace(ns, game, variant)
    print(f"\n=== {game} {variant} (codex) ===")
    run_codex_generation(ns)
    if not skip_checks:
        code, _output = run_base_checks(ns)
        if code != 0:
            raise RuntimeError(f"base checks failed for {game} {variant}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", choices=RERUN_ORDER)
    parser.add_argument("--variant", choices=("oneshot", "agentic"))
    parser.add_argument("--all", action="store_true", help="Run all six pi-equivalent generations")
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
