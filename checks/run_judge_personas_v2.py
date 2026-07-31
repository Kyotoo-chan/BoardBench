#!/usr/bin/env python3
"""Run three blind, non-aggregated personas with a complete attributed source packet."""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from generation.codex_native import run_codex
from generation.pdf_pages import render_pdf_pages

PERSONAS = ("rule_fidelity", "ambiguity", "executable_systems")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_persona(persona: str, args: argparse.Namespace) -> None:
    workspace = Path(tempfile.mkdtemp(prefix=f"boardbench_{args.stem}_{persona}_"))
    try:
        assigned = [
            (args.rulebook, "canonical_rulebook", args.rulebook_source_id, "publisher_rulebook"),
            (args.rulefacts, "canonical_rulefacts", args.rulefacts_source_id, "approved_fact_inventory"),
            (args.claims, "canonical_claims", args.claims_source_id, "atomic_claim_inventory"),
        ]
        if args.supplement:
            assigned.append((args.supplement, "canonical_supplement", args.supplement_source_id, args.supplement_role))
        manifest = {"scope": args.scope, "sources": []}
        images = []
        packet_names = []
        for source, stem, source_id, role in assigned:
            target = workspace / f"{stem}{source.suffix.lower()}"
            shutil.copy2(source, target)
            packet_names.append(target.name)
            manifest["sources"].append({
                "source_id": source_id,
                "role": role,
                "packet_name": target.name,
                "sha256": sha256(target),
            })
            if target.suffix.lower() == ".pdf":
                images.extend(render_pdf_pages(target, workspace / f"{stem}_pages", dpi=150))
        shutil.copy2(args.code, workspace / "implementation.py")
        (workspace / "SOURCE_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        persona_prompt = (ROOT / "inputs/prompts/judge_personas" / f"{persona}.md").read_text(encoding="utf-8")
        prompt = f"""You are a fresh blind BoardBench persona reviewer. Work only with SOURCE_MANIFEST.json, its listed sources, the attached complete 150-DPI PDF page images and render manifests, and implementation.py. Assigned files: {', '.join(packet_names)}. Respect source roles and the declared scope. Do not inspect checks, scenarios, scores, prior reviews, other implementations, or other source conditions. Do not use outside game knowledge. Cite canonical claim IDs where applicable.\n\n{persona_prompt}\n"""
        run_codex(
            prompt=prompt,
            cwd=workspace,
            response_path=args.output_dir / f"{args.stem}_persona_{persona}.md",
            events_path=args.output_dir / f"{args.stem}_persona_{persona}_events.jsonl",
            usage_path=args.output_dir / f"{args.stem}_persona_{persona}_usage.json",
            model=args.model,
            effort=args.effort,
            verbosity="low",
            mode="judge",
            timeout=1200,
            image_paths=images,
            sandbox="workspace-write",
        )
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rulebook", type=Path, required=True)
    parser.add_argument("--rulefacts", type=Path, required=True)
    parser.add_argument("--claims", type=Path, required=True)
    parser.add_argument("--code", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--stem", required=True)
    parser.add_argument("--scope", required=True)
    parser.add_argument("--rulebook-source-id", required=True)
    parser.add_argument("--rulefacts-source-id", required=True)
    parser.add_argument("--claims-source-id", required=True)
    parser.add_argument("--supplement", type=Path)
    parser.add_argument("--supplement-source-id")
    parser.add_argument("--supplement-role", default="user_observation")
    parser.add_argument("--model", default="gpt-5.6-sol")
    parser.add_argument("--effort", default="medium")
    args = parser.parse_args()
    if bool(args.supplement) != bool(args.supplement_source_id):
        parser.error("--supplement and --supplement-source-id must be supplied together")
    for path in (args.rulebook, args.rulefacts, args.claims, args.code, args.supplement):
        if path is not None and not path.is_file():
            parser.error(f"missing file: {path}")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(run_persona, persona, args) for persona in PERSONAS]
        for future in concurrent.futures.as_completed(futures):
            future.result()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
