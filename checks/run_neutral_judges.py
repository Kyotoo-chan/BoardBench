#!/usr/bin/env python3
"""Run three mutually blind neutral BoardBench judges."""

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


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def judge(index: int, args: argparse.Namespace) -> None:
    workspace = Path(tempfile.mkdtemp(prefix=f"boardbench_{args.stem}_judge_{index}_"))
    try:
        rules = workspace / f"canonical_rulebook{args.rulebook.suffix.lower()}"
        facts = workspace / "canonical_rulefacts.md"
        claims = workspace / "canonical_claims.json"
        code = workspace / "implementation.py"
        for source, target in ((args.rulebook, rules), (args.rulefacts, facts), (args.claims, claims), (args.code, code)):
            shutil.copy2(source, target)
        manifest = {
            "scope": args.scope,
            "sources": [
                {"source_id": args.rulebook_source_id, "role": "publisher_rulebook", "packet_name": rules.name, "sha256": sha256(rules)},
                {"source_id": args.rulefacts_source_id, "role": "approved_fact_inventory", "packet_name": facts.name, "sha256": sha256(facts)},
                {"source_id": args.claims_source_id, "role": "atomic_claim_inventory", "packet_name": claims.name, "sha256": sha256(claims)},
            ],
        }
        packet_names = [rules.name, facts.name, claims.name, code.name]
        assigned = []
        if args.companion:
            assigned.append((args.companion, args.companion_source_id, args.companion_role, "canonical_companion"))
        if args.supplement:
            assigned.append((args.supplement, args.supplement_source_id, args.supplement_role, "canonical_supplement"))
        copied = []
        for source, source_id, role, stem in assigned:
            target = workspace / f"{stem}{source.suffix.lower()}"
            shutil.copy2(source, target)
            manifest["sources"].append({
                "source_id": source_id,
                "role": role,
                "packet_name": target.name,
                "sha256": sha256(target),
            })
            packet_names.append(target.name)
            copied.append(target)
        (workspace / "SOURCE_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        images = render_pdf_pages(rules, workspace / "canonical_rulebook_pages", dpi=150)
        for source in copied:
            if source.suffix.lower() == ".pdf":
                images.extend(render_pdf_pages(source, workspace / f"{source.stem}_pages", dpi=150))
        review = (ROOT / "inputs/prompts/llm_judge_review.md").read_text(encoding="utf-8")
        prompt = f"""You are one of three fresh, mutually blind neutral BoardBench rule reviewers. Work only with SOURCE_MANIFEST.json, its listed sources, the attached 150-DPI rulebook page images and render manifest, and implementation.py. Assigned files: {', '.join(packet_names)}. Respect the declared base-game scope and source roles. Do not inspect checks, scenarios, scores, prior reviews, other implementations, or other source conditions. Do not use outside game knowledge. Cite canonical claim IDs where applicable.\n\n{review}"""
        run_codex(
            prompt=prompt,
            cwd=workspace,
            response_path=args.output_dir / f"{args.stem}_judge_{index}.md",
            events_path=args.raw_dir / f"{args.condition}_judge_{index}_events.jsonl",
            usage_path=args.raw_dir / f"{args.condition}_judge_{index}_usage.json",
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
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--stem", required=True)
    parser.add_argument("--condition", required=True)
    parser.add_argument("--scope", required=True)
    parser.add_argument("--rulebook-source-id", required=True)
    parser.add_argument("--rulefacts-source-id", required=True)
    parser.add_argument("--claims-source-id", required=True)
    parser.add_argument("--companion", type=Path, help="Optional assigned publisher companion")
    parser.add_argument("--companion-source-id")
    parser.add_argument("--companion-role", default="publisher_companion")
    parser.add_argument("--supplement", type=Path, help="Optional assigned clarification source")
    parser.add_argument("--supplement-source-id")
    parser.add_argument("--supplement-role", default="experimenter_clarification")
    parser.add_argument("--model", default="gpt-5.6-sol")
    parser.add_argument("--effort", default="medium")
    args = parser.parse_args()
    if bool(args.companion) != bool(args.companion_source_id):
        parser.error("--companion and --companion-source-id must be supplied together")
    if bool(args.supplement) != bool(args.supplement_source_id):
        parser.error("--supplement and --supplement-source-id must be supplied together")
    extras = [path for path in (args.companion, args.supplement) if path]
    for path in (args.rulebook, args.rulefacts, args.claims, args.code, *extras):
        if not path.is_file():
            parser.error(f"missing file: {path}")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.raw_dir.mkdir(parents=True, exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(judge, index, args) for index in range(1, 4)]
        for future in concurrent.futures.as_completed(futures):
            future.result()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
