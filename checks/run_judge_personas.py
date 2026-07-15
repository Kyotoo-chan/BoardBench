#!/usr/bin/env python3
"""Run three blind, non-aggregated BoardBench judge personas."""

from __future__ import annotations

import argparse
import concurrent.futures
import shutil
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from generation.codex_native import run_codex
from generation.pdf_pages import render_pdf_pages

PERSONAS = ("rule_fidelity", "ambiguity", "executable_systems")


def run_persona(
    persona: str,
    rulebook: Path,
    rulefacts: Path,
    code: Path,
    output_dir: Path,
    stem: str,
    model: str,
    effort: str,
) -> None:
    workspace = Path(tempfile.mkdtemp(prefix=f"boardbench_{stem}_{persona}_"))
    try:
        local_rules = workspace / f"canonical_rulebook{rulebook.suffix.lower()}"
        shutil.copy2(rulebook, local_rules)
        shutil.copy2(rulefacts, workspace / "canonical_rulefacts.md")
        shutil.copy2(code, workspace / "implementation.py")
        images = render_pdf_pages(local_rules, workspace / "pages", dpi=150) if local_rules.suffix == ".pdf" else []
        persona_prompt = (REPO_ROOT / "inputs" / "prompts" / "judge_personas" / f"{persona}.md").read_text(encoding="utf-8")
        prompt = f"""You are a fresh blind BoardBench persona reviewer. Work only with the canonical rulebook, canonical_rulefacts.md, attached page images, and implementation.py in this isolated packet. Do not inspect checks, scenarios, other implementations, or other reviews. Do not use outside game knowledge.\n\n{persona_prompt}\n"""
        run_codex(
            prompt=prompt,
            cwd=workspace,
            response_path=output_dir / f"{stem}_persona_{persona}.md",
            events_path=output_dir / f"{stem}_persona_{persona}_events.jsonl",
            usage_path=output_dir / f"{stem}_persona_{persona}_usage.json",
            model=model,
            effort=effort,
            mode="judge",
            image_paths=images,
        )
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rulebook", type=Path, required=True)
    parser.add_argument("--rulefacts", type=Path, required=True)
    parser.add_argument("--code", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--stem", required=True)
    parser.add_argument("--model", default="gpt-5.6-sol")
    parser.add_argument("--effort", default="medium")
    args = parser.parse_args()
    for path in (args.rulebook, args.rulefacts, args.code):
        if not path.is_file():
            parser.error(f"missing file: {path}")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(
                run_persona,
                persona,
                args.rulebook.resolve(),
                args.rulefacts.resolve(),
                args.code.resolve(),
                args.output_dir.resolve(),
                args.stem,
                args.model,
                args.effort,
            )
            for persona in PERSONAS
        ]
        for future in concurrent.futures.as_completed(futures):
            future.result()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
