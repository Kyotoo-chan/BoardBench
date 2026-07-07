"""One-shot notebook setup: activate rulebook, game spec, Claude auth, optional brief."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from generation.config import activate_game_rules, game_spec  # noqa: E402
from generation.llm_cli import (  # noqa: E402
    build_llm_command,
    ensure_direct_llm_response,
    get_claude_path,
    run_llm_subprocess,
)

BRIEF_PROMPT_PATH = REPO_ROOT / "prompts" / "rulebook_to_implementation_brief.md"
DEFAULT_TIMEOUT_SECONDS = 7200  # 2h for generation and judge steps


def _warn_api_key_overrides_subscription() -> None:
    if os.environ.get("ANTHROPIC_API_KEY"):
        print(
            "WARN: ANTHROPIC_API_KEY is set — Claude Code may bill API usage "
            "instead of your subscription. Unset it for subscription runs."
        )


def verify_claude_auth() -> None:
    _warn_api_key_overrides_subscription()
    claude = get_claude_path()
    result = subprocess.run(
        [claude, "auth", "status", "--text"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    text = (result.stdout or result.stderr or "").strip()
    if result.returncode != 0 or "not logged in" in text.lower():
        raise RuntimeError(
            "Claude Code is not logged in. Run once: claude auth login\n"
            f"({text or 'auth status failed'})"
        )
    print(f"OK claude auth ({claude})")


def ensure_implementation_brief(
    *,
    game: str,
    brief_path: Path,
    rules_path: Path,
    read_rules_text,
    render_pdf_pages,
    backend: str,
    model: str,
    effort: str | None,
    timeout: int,
    output_dir: Path,
) -> None:
    if brief_path.exists() and brief_path.read_text(encoding="utf-8").strip():
        return
    if not BRIEF_PROMPT_PATH.exists():
        raise FileNotFoundError(f"Missing brief prompt: {BRIEF_PROMPT_PATH}")

    print(f"generating implementation brief -> {brief_path.name}", flush=True)
    rules_text = read_rules_text(rules_path)
    attachments: list[Path] = []
    if not rules_text.strip() and rules_path.suffix.lower() == ".pdf":
        attachments = render_pdf_pages(rules_path)
        rules_block = (
            "Rulebook is image-only PDF; use attached page images as the only rule source."
        )
    else:
        rules_block = f"Hier folgt die Spielanleitung:\n\n{rules_text}"

    prompt = (
        f"{BRIEF_PROMPT_PATH.read_text(encoding='utf-8')}\n\n"
        f"# Game: {game}\n\n{rules_block}"
    )
    command = build_llm_command(
        backend,
        model,
        effort,
        mode="oneshot",
        file_args=attachments or None,
        add_dirs=[rules_path.parent] if attachments else None,
    )
    result = run_llm_subprocess(
        command,
        prompt_text=prompt,
        timeout=timeout,
        output_dir=output_dir,
    )
    text = ensure_direct_llm_response(result, step="implementation brief")
    brief_path.parent.mkdir(parents=True, exist_ok=True)
    brief_path.write_text(text, encoding="utf-8")
    print(f"OK implementation brief ({len(text)} chars)")


def bootstrap_notebook(ns: dict[str, Any], *, agentic_notebook: bool) -> None:
    """Activate game inputs and verify local Claude after the notebook setup cell runs."""

    game = ns["GAME"]
    backend = ns.get("LLM_BACKEND", "claude")
    if backend != "claude":
        raise ValueError("Pull-and-run notebooks expect LLM_BACKEND = 'claude'")

    spec = game_spec(game)
    active = activate_game_rules(game)
    ns["OPEN_SPIEL_GAME"] = spec.open_spiel_game
    ns["USE_IMPLEMENTATION_BRIEF"] = spec.use_implementation_brief
    if agentic_notebook:
        ns["INCLUDE_OPENSPIEL_COMPARE"] = spec.include_openspiel_compare

    ns["TIMEOUT_SECONDS"] = DEFAULT_TIMEOUT_SECONDS
    ns["OUTPUT_DIR"].mkdir(parents=True, exist_ok=True)

    verify_claude_auth()

    if spec.use_implementation_brief:
        ensure_implementation_brief(
            game=game,
            brief_path=ns["IMPLEMENTATION_BRIEF_PATH"],
            rules_path=ns["find_rules_path"](),
            read_rules_text=ns["read_rules_text"],
            render_pdf_pages=ns["render_pdf_pages"],
            backend=backend,
            model=ns["LLM_MODEL"],
            effort=ns.get("LLM_EFFORT"),
            timeout=ns["TIMEOUT_SECONDS"],
            output_dir=ns["OUTPUT_DIR"],
        )

    stem_fn = ns.get("output_stem")
    if stem_fn is None:
        from generation.config import output_stem as stem_fn
    backend_norm_fn = ns.get("normalize_backend")
    if backend_norm_fn is None:
        from generation.config import normalize_backend as backend_norm_fn
    variant = ns["RUN_VARIANT"]
    stem = stem_fn(game, backend, variant)
    backend_norm = backend_norm_fn(backend)
    ns["RUN_STEM"] = stem
    ns["CODE_PATH"] = ns["OUTPUT_DIR"] / f"{stem}.py"
    ns["RESPONSE_PATH"] = ns["OUTPUT_DIR"] / f"{stem}.md"
    ns["CHECK_LOG_PATH"] = ns["OUTPUT_DIR"] / f"{stem}_checks.txt"
    ns["JUDGE_REVIEW_PATH"] = ns["OUTPUT_DIR"] / f"{stem}_judge_{backend_norm}.md"
    ns["PRE_ALIGN_CODE_PATH"] = ns["OUTPUT_DIR"] / f"{stem}_pre_align.py"
    ns["ACTION_ALIGN_RESPONSE_PATH"] = ns["OUTPUT_DIR"] / f"{stem}_action_align.md"

    print(
        f"OK bootstrap game={game} variant={variant} "
        f"rules={active.name} stem={stem} timeout={ns['TIMEOUT_SECONDS']}s"
    )
