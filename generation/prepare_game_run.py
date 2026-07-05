#!/usr/bin/env python3
"""Prepare archived inputs, agentic workspace, and generation packets for one game."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from generation.config import (  # noqa: E402
    activate_game_rules,
    agentic_workspace_dir,
    archived_rules_path,
    clear_for_new_game_run,
    game_spec,
)

PROMPT_PATH = REPO_ROOT / "prompts" / "rulebook_to_python.txt"
BACKBONE_PATH = REPO_ROOT / "prompts" / "open_spiel_backbone.md"
OUTPUT_DIR = REPO_ROOT / "outputs"


def copy_if_exists(source: Path, target: Path) -> bool:
    if not source.exists():
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return True


def prepare_agentic_workspace(slug: str) -> Path:
    workspace = agentic_workspace_dir(slug)
    input_dir = workspace / "inputs"
    output_dir = workspace / "outputs"
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    game_out = OUTPUT_DIR

    copy_if_exists(PROMPT_PATH, input_dir / "rulebook_to_python.txt")
    copy_if_exists(BACKBONE_PATH, input_dir / "open_spiel_backbone.md")

    brief = game_out / f"{slug}_implementation_brief.md"
    copy_if_exists(brief, input_dir / "implementation_brief.md")

    rules_source = archived_rules_path(slug)
    copy_if_exists(rules_source, input_dir / rules_source.name)
    return workspace


def write_oneshot_packet(slug: str) -> Path:
    rules_source = archived_rules_path(slug)
    packet_path = OUTPUT_DIR / f"{slug}_oneshot_generation_packet.md"
    body = [
        "# BoardBench one-shot generation packet",
        f"- game: {slug}",
        "- variant: oneshot",
        "- backend: claude",
        f"- expected code path: outputs/<stem>.py",
        f"- expected response path: outputs/<stem>.md",
        "",
        "## Instructions for Claude",
        "Use only the listed attachments and rulebook material.",
        "Do not read BoardBench checks/.",
        "Return assumptions plus one fenced ```python block with the full module.",
        "",
        "## Attachments",
        f"- {PROMPT_PATH.as_posix()}",
        f"- {BACKBONE_PATH.as_posix()}",
        f"- rulebook: inputs/game_rules.pdf (active copy of {rules_source.as_posix()})",
    ]
    if (OUTPUT_DIR / f"{slug}_implementation_brief.md").exists():
        body.append(f"- implementation brief: outputs/{slug}_implementation_brief.md")
    body.extend(
        [
            "",
            "## Notebook",
            "- Run from evaluation2.ipynb with GAME set to this slug.",
            "- After Claude responds, save to outputs/<game>_oneshot.md and run ingest_generation_response().",
        ]
    )
    packet_path.parent.mkdir(parents=True, exist_ok=True)
    packet_path.write_text("\n".join(body), encoding="utf-8")
    return packet_path


def write_agentic_packet(slug: str, workspace: Path) -> Path:
    packet_path = OUTPUT_DIR / f"{slug}_agentic_generation_packet.md"
    body = [
        "# BoardBench agentic generation packet",
        f"- game: {slug}",
        "- variant: agentic",
        "- backend: claude",
        f"- workspace: {workspace.as_posix()}",
        f"- expected workspace code path: {workspace.as_posix()}/outputs/{slug}_agentic.py",
        f"- expected repo response path: outputs/<stem>.md",
        f"- expected repo code path after ingest: outputs/<stem>.py",
        "",
        "## Instructions for Claude / Cursor",
        "Work only inside the workspace inputs/ and outputs/ directories.",
        "Do not read BoardBench checks/ or other repo evaluation files.",
        "You may run small syntax/import smoke checks on your own generated file.",
        "Return assumptions plus one fenced ```python block with the final module.",
        "",
        "## Workspace attachments",
        f"- {workspace.as_posix()}/inputs/rulebook_to_python.txt",
        f"- {workspace.as_posix()}/inputs/open_spiel_backbone.md",
        f"- {workspace.as_posix()}/inputs/{archived_rules_path(slug).name}",
        "",
        "## Notebook",
        "- Run from evaluation.ipynb with GAME set to this slug.",
        "- After Claude responds, save to outputs/<game>_agentic.md and run ingest_generation_response().",
    ]
    packet_path.write_text("\n".join(body), encoding="utf-8")
    return packet_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slug")
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Empty outputs/ before preparing (artifacts stay in git history)",
    )
    args = parser.parse_args()

    if args.clear:
        cleared = clear_for_new_game_run(args.slug)
        print(f"Cleared run dir: {cleared.as_posix()}")

    active = activate_game_rules(args.slug)
    workspace = prepare_agentic_workspace(args.slug)
    oneshot_packet = write_oneshot_packet(args.slug)
    agentic_packet = write_agentic_packet(args.slug, workspace)

    print(f"Activated rulebook: {active.as_posix()}")
    print(f"Agentic workspace: {workspace.as_posix()}")
    print(f"Oneshot packet: {oneshot_packet.as_posix()}")
    print(f"Agentic packet: {agentic_packet.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
