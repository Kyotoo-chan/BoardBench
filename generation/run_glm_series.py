#!/usr/bin/env python3
"""Run GLM-5.2 generations for BoardBench games (oneshot + agentic).

Uses Z.ai OpenAI-compatible chat endpoint and writes per-run usage/cost files.

Example::

  python generation/run_glm_series.py --game exploding_kittens --variant oneshot
  python generation/run_glm_series.py --game exploding_kittens --all-variants
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import shutil
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "checks") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "checks"))

from generation.config import RERUN_ORDER, activate_game_rules, game_spec, output_stem  # noqa: E402
from generation.game_run_workflow import auto_clear_before_run  # noqa: E402
from generation.glm_agentic import (  # noqa: E402
    format_transcript_markdown,
    ingest_workspace_code,
    run_glm_agentic_loop,
)
from generation.llm_cli import extract_code_block  # noqa: E402
from generation.run_codex_series import load_notebook_namespace, run_base_checks  # noqa: E402

ZAI_CHAT_URL = "https://api.z.ai/api/paas/v4/chat/completions"
DEFAULT_MODEL = "glm-5.2"
DEFAULT_REASONING_EFFORT = "max"
USAGE_LOG_PATH = REPO_ROOT / "outputs" / "glm_usage_log.csv"


def _env_price(name: str) -> float | None:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return None
    return float(raw)


def _response_text_from_choice(message_content: object) -> str:
    if isinstance(message_content, str):
        return message_content
    if isinstance(message_content, list):
        chunks: list[str] = []
        for part in message_content:
            if isinstance(part, dict) and part.get("type") == "text":
                chunks.append(str(part.get("text", "")))
        return "\n".join(item for item in chunks if item).strip()
    return ""


def _price_breakdown(usage: dict[str, object]) -> dict[str, float | None]:
    prompt_tokens = int(usage.get("prompt_tokens", 0) or 0)
    completion_tokens = int(usage.get("completion_tokens", 0) or 0)
    reasoning_tokens = int(usage.get("reasoning_tokens", 0) or 0)
    details = usage.get("completion_tokens_details")
    if isinstance(details, dict):
        reasoning_tokens = int(details.get("reasoning_tokens", 0) or reasoning_tokens)

    in_price = _env_price("GLM_PRICE_INPUT_PER_1M")
    out_price = _env_price("GLM_PRICE_OUTPUT_PER_1M")
    reason_price = _env_price("GLM_PRICE_REASONING_PER_1M")

    input_cost = (prompt_tokens / 1_000_000.0) * in_price if in_price is not None else None
    output_cost = (completion_tokens / 1_000_000.0) * out_price if out_price is not None else None
    reasoning_cost = (reasoning_tokens / 1_000_000.0) * reason_price if reason_price is not None else None

    known = [value for value in (input_cost, output_cost, reasoning_cost) if value is not None]
    total_cost = sum(known) if known else None
    return {
        "prompt_tokens": float(prompt_tokens),
        "completion_tokens": float(completion_tokens),
        "reasoning_tokens": float(reasoning_tokens),
        "input_cost_usd": input_cost,
        "output_cost_usd": output_cost,
        "reasoning_cost_usd": reasoning_cost,
        "total_cost_usd": total_cost,
    }


def _append_usage_row(stem: str, game: str, variant: str, data: dict[str, float | None]) -> None:
    USAGE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    exists = USAGE_LOG_PATH.exists()
    with USAGE_LOG_PATH.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        if not exists:
            writer.writerow(
                [
                    "stem",
                    "game",
                    "variant",
                    "prompt_tokens",
                    "completion_tokens",
                    "reasoning_tokens",
                    "input_cost_usd",
                    "output_cost_usd",
                    "reasoning_cost_usd",
                    "total_cost_usd",
                ]
            )
        writer.writerow(
            [
                stem,
                game,
                variant,
                int(data["prompt_tokens"] or 0),
                int(data["completion_tokens"] or 0),
                int(data["reasoning_tokens"] or 0),
                "" if data["input_cost_usd"] is None else f"{data['input_cost_usd']:.8f}",
                "" if data["output_cost_usd"] is None else f"{data['output_cost_usd']:.8f}",
                "" if data["reasoning_cost_usd"] is None else f"{data['reasoning_cost_usd']:.8f}",
                "" if data["total_cost_usd"] is None else f"{data['total_cost_usd']:.8f}",
            ]
        )


def configure_namespace(ns: dict, game: str, variant: str, *, effort: str) -> None:
    ns["GAME"] = game
    ns["RUN_VARIANT"] = variant
    ns["LLM_BACKEND"] = "glm"
    ns["LLM_MODEL"] = DEFAULT_MODEL
    ns["LLM_EFFORT"] = effort
    ns["TIMEOUT_SECONDS"] = 4000 if variant == "agentic" else 2000
    spec = game_spec(game)
    ns["OPEN_SPIEL_GAME"] = spec.open_spiel_game
    ns["INCLUDE_OPENSPIEL_COMPARE"] = spec.include_openspiel_compare
    ns["USE_IMPLEMENTATION_BRIEF"] = spec.use_implementation_brief

    output_dir: Path = ns["OUTPUT_DIR"]
    stem = output_stem(game, "glm", variant)
    ns["RUN_STEM"] = stem
    ns["IMPLEMENTATION_BRIEF_PATH"] = output_dir / f"{game}_implementation_brief.md"
    ns["CODE_PATH"] = output_dir / f"{stem}.py"
    ns["RESPONSE_PATH"] = output_dir / f"{stem}.md"
    ns["CHECK_LOG_PATH"] = output_dir / f"{stem}_checks.txt"


def _write_usage_artifacts(
    ns: dict,
    *,
    game: str,
    variant: str,
    usage: dict[str, object],
) -> dict[str, float | None]:
    breakdown = _price_breakdown(usage)
    _append_usage_row(ns["RUN_STEM"], game, variant, breakdown)
    return breakdown


def _finalize_code(
    ns: dict,
    *,
    response_text: str,
    workspace: Path | None,
    final_text: str | None = None,
) -> None:
    code_path: Path = ns["CODE_PATH"]
    response_path: Path = ns["RESPONSE_PATH"]
    response_path.write_text(response_text, encoding="utf-8")

    if workspace is not None and ingest_workspace_code(workspace, code_path):
        return

    source = final_text if final_text is not None else response_text
    code = extract_code_block(source)
    if code is not None:
        code_path.write_text(code, encoding="utf-8")
    elif workspace is not None and ns["copy_workspace_code"](workspace):
        pass
    elif code_path.exists():
        pass
    else:
        raise RuntimeError("No fenced python block in GLM response and no workspace code file")


def run_glm_oneshot(api_key: str, ns: dict, *, prompt_text: str) -> tuple[float, dict[str, object]]:
    game = ns["GAME"]
    variant = ns["RUN_VARIANT"]
    payload = {
        "model": ns["LLM_MODEL"],
        "messages": [{"role": "user", "content": prompt_text}],
        "thinking": {"type": "enabled"},
        "reasoning_effort": ns["LLM_EFFORT"],
    }
    started = time.perf_counter()
    req = urllib.request.Request(
        ZAI_CHAT_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=ns["TIMEOUT_SECONDS"]) as resp:
            raw_bytes = resp.read()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Z.ai HTTP {exc.code}: {body}") from exc

    data = json.loads(raw_bytes.decode("utf-8", errors="replace"))
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise RuntimeError("GLM response missing choices")
    message = choices[0].get("message", {})
    response_text = _response_text_from_choice(message.get("content", ""))
    if not response_text.strip():
        raise RuntimeError("GLM returned empty message content")

    usage = data.get("usage", {}) if isinstance(data.get("usage", {}), dict) else {}
    _finalize_code(ns, response_text=response_text, workspace=None)
    breakdown = _write_usage_artifacts(ns, game=game, variant=variant, usage=usage)
    elapsed = time.perf_counter() - started
    return elapsed, breakdown  # type: ignore[return-value]


def run_glm_agentic(api_key: str, ns: dict, *, prompt_text: str, file_args: list[Path]) -> tuple[float, dict[str, float | None]]:
    game = ns["GAME"]
    variant = ns["RUN_VARIANT"]
    workspace, command_file_args = ns["prepare_agentic_workspace"](file_args)
    prompt_text = ns["rewrite_attachment_paths"](prompt_text, file_args, command_file_args)
    started = time.perf_counter()
    try:
        result = run_glm_agentic_loop(
            api_key=api_key,
            workspace=workspace,
            user_prompt=prompt_text,
            model=ns["LLM_MODEL"],
            effort=ns["LLM_EFFORT"],
            timeout=ns["TIMEOUT_SECONDS"],
            code_path=ns["CODE_PATH"],
        )
        response_text = format_transcript_markdown(result)
        _finalize_code(
            ns,
            response_text=response_text,
            workspace=workspace,
            final_text=result.final_text,
        )
        breakdown = _write_usage_artifacts(
            ns,
            game=game,
            variant=variant,
            usage=result.usage_total,
        )
        elapsed = time.perf_counter() - started
        return elapsed, breakdown
    finally:
        if workspace is not None:
            code_path = ns["CODE_PATH"]
            if code_path.exists() and code_path.stat().st_size > 0:
                shutil.rmtree(workspace, ignore_errors=True)
            else:
                print(
                    f"WARN keeping agentic workspace for debugging: {workspace.as_posix()}",
                    flush=True,
                )


def run_glm_generation(ns: dict) -> float:
    api_key = os.environ.get("ZAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Missing ZAI_API_KEY environment variable")

    variant = ns["RUN_VARIANT"]
    prompt_text, file_args = (
        ns["build_one_shot_prompt"]() if variant == "oneshot" else ns["build_agentic_prompt"]()
    )

    if variant == "oneshot" and file_args:
        raise RuntimeError("GLM oneshot currently supports text rulebooks only (no image attachments).")

    code_path: Path = ns["CODE_PATH"]
    if variant == "agentic":
        elapsed, breakdown = run_glm_agentic(api_key, ns, prompt_text=prompt_text, file_args=file_args)
    else:
        elapsed, breakdown = run_glm_oneshot(api_key, ns, prompt_text=prompt_text)

    total_cost = breakdown["total_cost_usd"]
    total_cost_text = "n/a" if total_cost is None else f"${total_cost:.6f}"
    print(
        f"OK generation {elapsed:.1f}s -> {code_path.as_posix()} "
        f"(prompt={int(breakdown['prompt_tokens'])}, completion={int(breakdown['completion_tokens'])}, cost={total_cost_text})"
    )
    return elapsed


def run_one(game: str, variant: str, *, skip_checks: bool, effort: str) -> None:
    auto_clear_before_run(game, "glm", variant)
    activate_game_rules(game)
    ns = load_notebook_namespace(variant)
    configure_namespace(ns, game, variant, effort=effort)
    print(f"\n=== {game} {variant} (glm) ===")
    run_glm_generation(ns)
    if not skip_checks:
        code, _output = run_base_checks(ns)
        if code != 0:
            print(f"WARN base checks failed for {game} {variant}; continuing pipeline", flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", choices=RERUN_ORDER)
    parser.add_argument("--variant", choices=("oneshot", "agentic"))
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--all-variants", action="store_true", help="Run both oneshot+agentic for --game")
    parser.add_argument("--skip-checks", action="store_true")
    parser.add_argument(
        "--effort",
        choices=("high", "max"),
        default=DEFAULT_REASONING_EFFORT,
        help="GLM reasoning effort (max is strongest but slowest).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.all:
        for game in RERUN_ORDER:
            for variant in ("oneshot", "agentic"):
                run_one(game, variant, skip_checks=args.skip_checks, effort=args.effort)
        return 0
    if args.game and args.all_variants:
        for variant in ("oneshot", "agentic"):
            run_one(args.game, variant, skip_checks=args.skip_checks, effort=args.effort)
        return 0
    if not args.game or not args.variant:
        raise SystemExit("Provide --game and --variant, --game --all-variants, or use --all")
    run_one(args.game, args.variant, skip_checks=args.skip_checks, effort=args.effort)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
