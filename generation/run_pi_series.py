#!/usr/bin/env python3
"""Run one catalog game through the agentic Pi generation fallback.

The project skills are the preferred workflow. This script keeps the manual
notebook path reproducible for catalog games.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from generation.config import (  # noqa: E402
    RERUN_ORDER,
    activate_game_rules,
    clear_run_artifacts,
    game_spec,
    output_stem,
)
from generation.llm_cli import (  # noqa: E402
    build_llm_command,
    extract_code_block,
    llm_failure_message,
    run_llm_subprocess,
)

DEFAULT_MODEL = "openai-codex/gpt-5.6-sol"
DEFAULT_THINKING = "low"
ROLLOUTS = 100
MAX_STEPS = 300
CHECK_SEED = 1


def model_with_thinking(model: str, thinking: str) -> str:
    model_id = model.rsplit("/", 1)[-1]
    return model if ":" in model_id else f"{model}:{thinking}"


def load_notebook_namespace() -> dict:
    payload = json.loads((REPO_ROOT / "evaluation.ipynb").read_text(encoding="utf-8"))
    cell = next(cell for cell in payload["cells"] if cell.get("cell_type") == "code")
    code = "".join(cell["source"]) if isinstance(cell["source"], list) else cell["source"]
    namespace: dict = {"__name__": "__main__", "Path": Path}
    exec(code, namespace)
    return namespace


def configure_namespace(ns: dict, game: str, model: str, thinking: str) -> None:
    spec = game_spec(game)
    stem = output_stem(game, "gpt", "agentic")
    output_dir: Path = ns["OUTPUT_DIR"]

    ns.update(
        GAME=game,
        RUN_VARIANT="agentic",
        LLM_BACKEND="pi",
        LLM_MODEL=model_with_thinking(model, thinking),
        LLM_EFFORT=thinking,
        TIMEOUT_SECONDS=4000,
        OPEN_SPIEL_GAME=spec.open_spiel_game,
        INCLUDE_OPENSPIEL_COMPARE=spec.include_openspiel_compare,
        USE_IMPLEMENTATION_BRIEF=spec.use_implementation_brief,
        RUN_STEM=stem,
        IMPLEMENTATION_BRIEF_PATH=output_dir / f"{game}_implementation_brief.md",
        CODE_PATH=output_dir / f"{stem}.py",
        RESPONSE_PATH=output_dir / f"{stem}.md",
        CHECK_LOG_PATH=output_dir / f"{stem}_checks.txt",
        JUDGE_REVIEW_PATH=output_dir / f"{stem}_judge_gpt.md",
    )


def run_generation(ns: dict) -> float:
    prompt_text, file_args = ns["build_agentic_prompt"]()
    workspace, command_file_args = ns["prepare_agentic_workspace"](file_args)
    prompt_text = ns["rewrite_attachment_paths"](prompt_text, file_args, command_file_args)
    command = build_llm_command(
        "pi",
        ns["LLM_MODEL"],
        ns["LLM_EFFORT"],
        mode="agentic",
        file_args=command_file_args,
        add_dirs=[workspace],
    )

    code_path: Path = ns["CODE_PATH"]
    response_path: Path = ns["RESPONSE_PATH"]
    started = time.perf_counter()
    try:
        result = run_llm_subprocess(
            command,
            prompt_text=prompt_text,
            cwd=workspace,
            timeout=ns["TIMEOUT_SECONDS"],
            output_dir=ns["OUTPUT_DIR"],
        )
        response_path.write_text(result.stdout or "", encoding="utf-8")
        if result.returncode != 0:
            raise RuntimeError(llm_failure_message(result, step="pi generation"))

        code = extract_code_block(result.stdout or "")
        if code is not None:
            code_path.write_text(code, encoding="utf-8")
        elif not ns["copy_workspace_code"](workspace) and not code_path.exists():
            raise RuntimeError("No final Python module was produced")

        elapsed = time.perf_counter() - started
        print(f"OK generation {elapsed:.1f}s -> {code_path.as_posix()}")
        return elapsed
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def run_base_checks(ns: dict) -> int:
    spec = game_spec(ns["GAME"])
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
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
    output = (proc.stdout or "") + (proc.stderr or "")
    ns["CHECK_LOG_PATH"].write_text(output, encoding="utf-8")
    summary = next((line for line in output.splitlines() if line.startswith("---- summary")), "no summary")
    print(summary)
    return proc.returncode


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", choices=RERUN_ORDER)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument(
        "--thinking",
        choices=("off", "minimal", "low", "medium", "high", "xhigh", "max"),
        default=DEFAULT_THINKING,
    )
    parser.add_argument("--skip-checks", action="store_true")
    return parser.parse_args()


def run_one(game: str, *, model: str, thinking: str, skip_checks: bool) -> None:
    clear_run_artifacts(game)
    activate_game_rules(game)
    ns = load_notebook_namespace()
    configure_namespace(ns, game, model, thinking)
    print(f"\n=== {game} agentic ({ns['LLM_MODEL']}) ===")
    run_generation(ns)
    if not skip_checks and run_base_checks(ns) != 0:
        raise RuntimeError(f"base checks failed for {game}")


def main() -> int:
    args = parse_args()
    games = RERUN_ORDER if args.all else ((args.game,) if args.game else ())
    if not games:
        raise SystemExit("Provide --game or use --all")
    for game in games:
        run_one(game, model=args.model, thinking=args.thinking, skip_checks=args.skip_checks)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
