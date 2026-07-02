#!/usr/bin/env python3
"""Run cross-model LLM judges (pi + codex) on pilot implementations.

Judge reviews are saved as ``{stem}_judge_{judge_backend}.md`` where
``judge_backend`` is ``gpt`` (pi) or ``codex``. Existing reviews are skipped.
Judge packets are assembled in a temp file only (not committed).

Use the boardbench conda env (pypdf + poppler for PDF rulebooks).
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
import tempfile
import time
from functools import partial
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "checks") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "checks"))

import importlib.util

from generation.config import RERUN_ORDER, activate_game_rules, game_spec, output_stem  # noqa: E402
from generation.llm_cli import build_llm_command, ensure_direct_llm_response, run_llm_subprocess  # noqa: E402
from generation.pdf_pages import render_pdf_pages as render_pdf_pages_fallback  # noqa: E402
from generation.pilot_catalog import PILOT_RUNS  # noqa: E402
from generation.run_codex_series import load_notebook_namespace  # noqa: E402

# Reuse score parser from check 90
_spec = importlib.util.spec_from_file_location("judge90", REPO_ROOT / "checks" / "90_llm_judge.py")
_judge_mod = importlib.util.module_from_spec(_spec)
assert _spec and _spec.loader
_spec.loader.exec_module(_judge_mod)
parse_score = _judge_mod.parse_score

JUDGE_PROFILES = {
    "gpt": {
        "cli_backend": "pi",
        "model": "openai-codex/gpt-5.5:xhigh",
        "effort": None,
        "timeout_oneshot": 2000,
        "timeout_agentic": 4000,
    },
    "codex": {
        "cli_backend": "codex",
        "model": "gpt-5.5",
        "effort": "xhigh",
        "timeout_oneshot": 2000,
        "timeout_agentic": 4000,
    },
    "claude": {
        "cli_backend": "claude",
        "model": "opus",
        "effort": "max",
        "timeout_oneshot": 2000,
        "timeout_agentic": 4000,
    },
}

ACTIVE_JUDGE_BACKENDS = ("gpt", "codex")
CLAUDE_JUDGE_BACKEND = "claude"


def judge_review_path(stem: str, judge_backend: str) -> Path:
    return REPO_ROOT / "outputs" / f"{stem}_judge_{judge_backend}.md"


def has_valid_judge(path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return False
    return parse_score(text) is not None


def run_one_judge(
    game: str,
    impl_backend: str,
    variant: str,
    judge_backend: str,
    *,
    force: bool,
) -> bool:
    stem = output_stem(game, impl_backend, variant)
    review_path = judge_review_path(stem, judge_backend)
    code_path = REPO_ROOT / "outputs" / f"{stem}.py"

    if not code_path.exists():
        print(f"SKIP missing code {code_path.as_posix()}", flush=True)
        return False

    if not force and has_valid_judge(review_path):
        score = parse_score(review_path.read_text(encoding="utf-8"))
        print(f"SKIP {stem} judge={judge_backend} score={score:.3f} (exists)", flush=True)
        return False

    profile = JUDGE_PROFILES[judge_backend]
    activate_game_rules(game)
    ns = load_notebook_namespace(variant)
    spec = game_spec(game)
    ns["GAME"] = game
    ns["RUN_VARIANT"] = variant
    ns["OPEN_SPIEL_GAME"] = spec.open_spiel_game
    ns["USE_IMPLEMENTATION_BRIEF"] = spec.use_implementation_brief
    ns["RUN_STEM"] = stem
    ns["CODE_PATH"] = code_path
    ns["RESPONSE_PATH"] = REPO_ROOT / "outputs" / f"{stem}.md"
    ns["CHECK_LOG_PATH"] = REPO_ROOT / "outputs" / f"{stem}_checks.txt"
    ns["IMPLEMENTATION_BRIEF_PATH"] = REPO_ROOT / "outputs" / f"{game}_implementation_brief.md"
    ns["TIMEOUT_SECONDS"] = (
        profile["timeout_agentic"] if variant == "agentic" else profile["timeout_oneshot"]
    )

    def _render_pdf_pages(rules_path: Path) -> list[Path]:
        page_dir = ns["INPUT_DIR"] / "rulebook_pages" / rules_path.stem
        return render_pdf_pages_fallback(rules_path, page_dir)

    ns["render_pdf_pages"] = _render_pdf_pages

    output_dir: Path = ns["OUTPUT_DIR"]
    ns["run_llm_subprocess"] = partial(run_llm_subprocess, output_dir=output_dir)

    with tempfile.NamedTemporaryFile(
        prefix=f"judge_packet_{stem}_{judge_backend}_",
        suffix=".md",
        delete=False,
        dir=output_dir,
    ) as tmp:
        packet_path = Path(tmp.name)

    try:
        started = time.perf_counter()
        ns["build_judge_packet_for"](
            code_path=code_path,
            check_log_path=ns["CHECK_LOG_PATH"],
            output_path=packet_path,
            judge_review_path=review_path,
            variant=variant,
        )

        judge_attachments = []
        rules_path = ns["find_rules_path"]()
        if rules_path.suffix.lower() == ".pdf" and not ns["read_rules_text"](rules_path).strip():
            judge_attachments = ns["render_pdf_pages"](rules_path)

        command = build_llm_command(
            profile["cli_backend"],
            profile["model"],
            profile["effort"],
            mode="judge",
            file_args=judge_attachments,
            add_dirs=[ns["INPUT_DIR"]] if judge_attachments else None,
        )
        result = ns["run_llm_subprocess"](
            command,
            prompt_text=packet_path.read_text(encoding="utf-8"),
            timeout=ns["TIMEOUT_SECONDS"],
        )
        review_text = ensure_direct_llm_response(result, step=f"judge {judge_backend}")
        review_path.write_text(review_text, encoding="utf-8")
        elapsed = time.perf_counter() - started
        score = parse_score(review_text)
        if score is None:
            raise RuntimeError(f"{stem} judge={judge_backend} missing machine-readable score block")
        print(f"OK {stem} judge={judge_backend} score={score:.3f} ({elapsed:.1f}s)", flush=True)
        return True
    finally:
        packet_path.unlink(missing_ok=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", choices=RERUN_ORDER)
    parser.add_argument("--impl-backend", choices=("gpt", "claude", "codex"))
    parser.add_argument("--variant", choices=("oneshot", "agentic"))
    parser.add_argument("--judge-backend", choices=(*ACTIVE_JUDGE_BACKENDS, CLAUDE_JUDGE_BACKEND))
    parser.add_argument(
        "--claude-judges",
        action="store_true",
        help="Run claude judge on claude-generated implementations only",
    )
    parser.add_argument("--all", action="store_true", help="All missing gpt+codex judges")
    parser.add_argument("--force", action="store_true", help="Re-run even if review exists")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ran = 0

    if args.claude_judges:
        for run in PILOT_RUNS:
            if run.impl_backend != "claude":
                continue
            if run_one_judge(
                run.game,
                run.impl_backend,
                run.variant,
                CLAUDE_JUDGE_BACKEND,
                force=args.force,
            ):
                ran += 1
        print(f"\ncompleted {ran} new claude judge run(s)", flush=True)
        return 0

    if args.all:
        for run in PILOT_RUNS:
            for judge_backend in ACTIVE_JUDGE_BACKENDS:
                if run_one_judge(
                    run.game,
                    run.impl_backend,
                    run.variant,
                    judge_backend,
                    force=args.force,
                ):
                    ran += 1
        print(f"\ncompleted {ran} new judge run(s)", flush=True)
        return 0

    if not args.game or not args.impl_backend or not args.variant or not args.judge_backend:
        raise SystemExit("Provide --all or --game --impl-backend --variant --judge-backend")
    if run_one_judge(args.game, args.impl_backend, args.variant, args.judge_backend, force=args.force):
        ran += 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
