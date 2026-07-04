#!/usr/bin/env python3
"""Run one BoardBench judge review with an optional persona overlay.

  python checks/run_judge_personas.py --list
  python checks/run_judge_personas.py --persona casual_beginner \\
      --code outputs/expl_gpt_ag.py --rules inputs/games/exploding_kittens/game_rules.pdf
"""

from __future__ import annotations

import argparse
import re
import sys
import tempfile
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
_CHECKS_DIR = Path(__file__).resolve().parent
for path in (REPO_ROOT, _CHECKS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from judge_packet import PERSONAS_DIR, build_judge_packet, resolve_persona_prompt  # noqa: E402
from generation.llm_cli import build_llm_command, ensure_direct_llm_response, run_llm_subprocess  # noqa: E402

PI_MODEL = "openai-codex/gpt-5.5:xhigh"
TIMEOUT_SECONDS = 900
SCORE_RE = re.compile(r"(?im)^\s*score\s*:\s*([01](?:\.\d+)?)\s*$")


def list_personas() -> list[str]:
    return sorted(path.stem for path in PERSONAS_DIR.glob("*.md"))


def output_path(code_path: Path, persona: str, judge_backend: str) -> Path:
    stem = code_path.stem
    suffix = "" if judge_backend == "pi" else f"_{judge_backend}"
    return REPO_ROOT / "outputs" / f"judge_persona_{persona}_{stem}{suffix}.md"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="List persona overlays")
    parser.add_argument("--persona", help="Persona name (filename without .md)")
    parser.add_argument("--code", type=Path, help="Generated Python module")
    parser.add_argument("--rules", type=Path, help="Rulebook path")
    parser.add_argument("--judge", default="pi", choices=["pi", "codex", "claude"])
    parser.add_argument("--note", default=None, help="Optional packet note")
    args = parser.parse_args()

    if args.list:
        for name in list_personas():
            print(name)
        return 0

    if not args.persona or not args.code or not args.rules:
        parser.error("--persona, --code, and --rules are required unless --list")

    resolve_persona_prompt(args.persona)
    code_path = args.code if args.code.is_absolute() else REPO_ROOT / args.code
    rules_path = args.rules if args.rules.is_absolute() else REPO_ROOT / args.rules
    out_path = output_path(code_path, args.persona, args.judge)

    with tempfile.NamedTemporaryFile(
        prefix=f"judge_persona_{args.persona}_",
        suffix=".md",
        dir=REPO_ROOT / "outputs",
        delete=False,
    ) as tmp:
        packet_path = Path(tmp.name)

    model = PI_MODEL if args.judge == "pi" else ("gpt-5.4" if args.judge == "codex" else "opus")
    effort = "xhigh" if args.judge in {"pi", "codex"} else "max"

    try:
        build_judge_packet(
            code_path=code_path,
            rules_path=rules_path,
            output_path=packet_path,
            game_label=f"{code_path.stem} persona={args.persona}",
            variant="persona",
            note=args.note,
            persona=args.persona,
        )
        command = build_llm_command(args.judge, model, effort, mode="judge")
        started = time.perf_counter()
        result = run_llm_subprocess(
            command,
            prompt_text=packet_path.read_text(encoding="utf-8"),
            cwd=REPO_ROOT,
            timeout=TIMEOUT_SECONDS,
        )
        text = ensure_direct_llm_response(result, step=f"judge persona {args.persona}")
        out_path.write_text(text, encoding="utf-8")
        elapsed = time.perf_counter() - started
        matches = SCORE_RE.findall(text)
        score = matches[-1] if matches else "?"
        print(f"OK  persona={args.persona}  score={score}  {elapsed:.0f}s  -> {out_path.name}", flush=True)
        return 0
    except Exception as exc:
        print(f"FAIL  {exc}", flush=True)
        return 1
    finally:
        packet_path.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
