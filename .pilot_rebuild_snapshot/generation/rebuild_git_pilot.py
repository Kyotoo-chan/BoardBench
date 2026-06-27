#!/usr/bin/env python3
"""Rebuild pilot outputs git history: one game in outputs/, canonical names, cross judges separate."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from generation.config import output_stem  # noqa: E402
from generation.pilot_catalog import iter_runs_for_game  # noqa: E402

BASE_COMMIT = "d66ad6e"  # consolidate pilot problem analysis (before claude rerun)

INFRA_RESTORE_PATHS = [
    "docs/claude_generation_workflow.md",
    "docs/claude_rerun_series.md",
    "checks/06_action_language.py",
    "generation/llm_cli.py",
    "generation/run_codex_series.py",
    "generation/run_codex_eval.py",
    "docs/codex_pilot_workflow.md",
]

CODE_INFRA_PATHS = [
    "AGENTS.md",
    "checks/90_llm_judge.py",
    "generation/llm_cli.py",
    "generation/pdf_pages.py",
    "generation/pilot_catalog.py",
    "generation/restore_pilot_outputs.py",
    "generation/run_cross_judges.py",
    "generation/run_pilot_checks.py",
    "generation/rebuild_git_pilot.py",
    "plots/collect_scores.py",
    "plots/make_plots.py",
]

DATES = {
    "prepare_hav": "2026-06-27 23:51:00",
    "hav_gpt": "2026-06-24 16:03:00",
    "hav_claude": "2026-06-28 11:47:00",
    "hav_codex": "2026-06-30 23:40:00",
    "hav_cross": None,
    "prepare_aba": "2026-06-28 11:52:00",
    "aba_gpt": "2026-06-24 23:14:00",
    "aba_claude": "2026-06-29 00:25:00",
    "aba_codex": "2026-07-01 00:25:00",
    "aba_cross": None,
    "prepare_expl": "2026-06-29 00:52:00",
    "expl_gpt": "2026-06-26 14:39:00",
    "expl_claude": "2026-06-30 22:15:00",
    "expl_codex": "2026-07-01 00:52:00",
    "expl_cross": None,
    "tooling": None,
    "plots": None,
}


@dataclass
class PlannedCommit:
    message: str
    date_key: str | None
    output_paths: list[str]
    extra_paths: list[str]
    clear_outputs: bool = True


def game_short(game: str) -> str:
    return {"havannah": "hav", "abalone": "aba", "exploding_kittens": "expl"}[game]


def stem_artifact_paths(game: str, backend: str, variant: str, *, include_judges: bool) -> list[str]:
    stem = output_stem(game, backend, variant)
    paths = [
        f"outputs/{stem}.py",
        f"outputs/{stem}.md",
        f"outputs/{stem}_checks.txt",
    ]
    if include_judges:
        for judge_backend in ("gpt", "codex", "claude"):
            paths.append(f"outputs/{stem}_judge_{judge_backend}.md")
    if game == "havannah":
        for suffix in ("_pre_align.py", "_action_align.md"):
            paths.append(f"outputs/{stem}{suffix}")
    if game == "exploding_kittens" and backend == "gpt":
        for suffix in ("_pre_align.py", "_action_align.md"):
            paths.append(f"outputs/{stem}{suffix}")
    return paths


def backend_output_paths(game: str, backend: str, *, include_judges: bool) -> list[str]:
    paths: list[str] = []
    for variant in ("oneshot", "agentic"):
        paths.extend(stem_artifact_paths(game, backend, variant, include_judges=include_judges))
    if backend == "claude" and game in {"havannah", "abalone"}:
        short = game_short(game)
        paths += [
            f"outputs/{short}_claude_pair_action_align.md",
            f"outputs/{short}_claude_pair_action_compare.txt",
        ]
    return paths


def game_judge_paths(game: str) -> list[str]:
    paths: list[str] = []
    for run in iter_runs_for_game(game):
        stem = output_stem(run.game, run.impl_backend, run.variant)
        for judge_backend in ("gpt", "codex", "claude"):
            paths.append(f"outputs/{stem}_judge_{judge_backend}.md")
    return paths


def game_check_paths(game: str) -> list[str]:
    paths: list[str] = []
    for run in iter_runs_for_game(game):
        stem = output_stem(run.game, run.impl_backend, run.variant)
        paths.append(f"outputs/{stem}_checks.txt")
    return paths


def all_game_output_paths(game: str, *, include_judges: bool) -> list[str]:
    paths: list[str] = []
    for backend in ("gpt", "claude", "codex"):
        paths.extend(backend_output_paths(game, backend, include_judges=include_judges))
    return paths


def build_plan() -> list[PlannedCommit]:
    plan: list[PlannedCommit] = [
        PlannedCommit(
            "prepare havannah for claude oneshot and agentic generations",
            "prepare_hav",
            [],
            ["inputs/game_rules.pdf"],
        ),
        PlannedCommit(
            "save havannah gpt oneshot and agentic generations and checks",
            "hav_gpt",
            backend_output_paths("havannah", "gpt", include_judges=False),
            [],
        ),
        PlannedCommit(
            "save havannah claude oneshot and agentic generations and checks",
            "hav_claude",
            backend_output_paths("havannah", "claude", include_judges=False),
            [],
        ),
        PlannedCommit(
            "save havannah codex oneshot and agentic generations and checks",
            "hav_codex",
            backend_output_paths("havannah", "codex", include_judges=False),
            [],
        ),
        PlannedCommit(
            "save hav cross-model judge reviews",
            "hav_cross",
            all_game_output_paths("havannah", include_judges=True),
            [],
            clear_outputs=True,
        ),
        PlannedCommit(
            "prepare abalone for claude oneshot and agentic generations",
            "prepare_aba",
            [],
            ["inputs/game_rules.pdf"],
        ),
        PlannedCommit(
            "save abalone gpt oneshot and agentic generations and checks",
            "aba_gpt",
            backend_output_paths("abalone", "gpt", include_judges=False),
            [],
        ),
        PlannedCommit(
            "save abalone claude oneshot and agentic generations and checks",
            "aba_claude",
            backend_output_paths("abalone", "claude", include_judges=False),
            [],
        ),
        PlannedCommit(
            "save abalone codex oneshot and agentic generations and checks",
            "aba_codex",
            backend_output_paths("abalone", "codex", include_judges=False),
            [],
        ),
        PlannedCommit(
            "save aba cross-model judge reviews",
            "aba_cross",
            all_game_output_paths("abalone", include_judges=True),
            [],
            clear_outputs=True,
        ),
        PlannedCommit(
            "prepare exploding kittens for claude oneshot and agentic generations",
            "prepare_expl",
            [],
            ["inputs/game_rules.pdf"],
        ),
        PlannedCommit(
            "save exploding kittens gpt oneshot and agentic generations and checks",
            "expl_gpt",
            backend_output_paths("exploding_kittens", "gpt", include_judges=False),
            [],
        ),
        PlannedCommit(
            "save exploding kittens claude oneshot and agentic generations and checks",
            "expl_claude",
            backend_output_paths("exploding_kittens", "claude", include_judges=False),
            [],
        ),
        PlannedCommit(
            "save exploding kittens codex oneshot and agentic generations and checks",
            "expl_codex",
            backend_output_paths("exploding_kittens", "codex", include_judges=False),
            [],
        ),
        PlannedCommit(
            "save expl cross-model judge reviews",
            "expl_cross",
            all_game_output_paths("exploding_kittens", include_judges=True),
            [],
            clear_outputs=True,
        ),
        PlannedCommit(
            "add cross-model judge tooling and multi-judge check parsing",
            "tooling",
            [],
            CODE_INFRA_PATHS,
            clear_outputs=False,
        ),
        PlannedCommit(
            "update score plots from cross-model judge averages",
            "plots",
            [],
            [
                "plots/hav_scores.png",
                "plots/hav_scores.txt",
                "plots/aba_scores.png",
                "plots/aba_scores.txt",
                "plots/expl_scores.png",
                "plots/expl_scores.txt",
            ],
            clear_outputs=False,
        ),
    ]
    return plan


def run_git(*args: str, env: dict | None = None) -> str:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=merged,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed:\n{result.stderr or result.stdout}")
    return (result.stdout or "").strip()


def now_date() -> str:
    return subprocess.check_output(
        ["powershell", "-Command", "Get-Date -Format 'yyyy-MM-dd HH:mm:ss'"],
        text=True,
        cwd=REPO_ROOT,
    ).strip()


def commit_date(key: str | None) -> str:
    if key is None:
        return now_date()
    value = DATES.get(key)
    return value if value else now_date()


def snapshot_workspace() -> Path:
    snap = REPO_ROOT / ".pilot_rebuild_snapshot"
    if snap.exists():
        shutil.rmtree(snap)
    snap.mkdir()
    for rel in CODE_INFRA_PATHS:
        src = REPO_ROOT / rel
        if src.is_file():
            dst = snap / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    for path in (REPO_ROOT / "outputs").rglob("*"):
        if path.is_file() and "_judge_packet" not in path.name:
            rel = path.relative_to(REPO_ROOT)
            dst = snap / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dst)
    for game in ("havannah", "abalone", "exploding_kittens"):
        src = REPO_ROOT / "inputs" / "games" / game / "game_rules.pdf"
        if src.exists():
            dst = snap / "inputs" / "game_rules.pdf"
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    return snap


def clear_outputs_dir() -> None:
    out = REPO_ROOT / "outputs"
    for path in out.iterdir():
        if path.name == ".gitkeep":
            continue
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)


def restore_paths(snap: Path, rel_paths: list[str]) -> None:
    for rel in rel_paths:
        src = snap / rel
        if not src.exists():
            continue
        dst = REPO_ROOT / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def filter_existing(snap: Path, paths: list[str]) -> list[str]:
    return [p for p in paths if (snap / p).exists()]


def apply_plan(plan: list[PlannedCommit], snap: Path) -> None:
    # Save current branch tip for safety
    original_branch = run_git("rev-parse", "--abbrev-ref", "HEAD")
    run_git("branch", "-f", "pilot-rebuild-backup", "HEAD")
    run_git("reset", "--hard", "HEAD")
    run_git("clean", "-fd", "outputs")
    run_git("checkout", BASE_COMMIT)
    run_git("branch", "-f", "pilot-rebuild-tmp", "HEAD")
    run_git("checkout", "pilot-rebuild-tmp")

    restore_paths(snap, filter_existing(snap, INFRA_RESTORE_PATHS))
    for rel in INFRA_RESTORE_PATHS:
        try:
            run_git("checkout", "pilot-rebuild-backup", "--", rel)
        except RuntimeError:
            restore_paths(snap, [rel])
    date = "2026-06-27 23:33:00"
    run_git("add", "-A")
    run_git(
        "commit",
        "-m",
        "add claude and codex pilot infra before clean game commits",
        env={"GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date},
    )
    print("committed: add claude and codex pilot infra before clean game commits")

    for item in plan:
        if item.clear_outputs:
            clear_outputs_dir()
        output_paths = filter_existing(snap, item.output_paths)
        restore_paths(snap, output_paths)
        restore_paths(snap, filter_existing(snap, item.extra_paths))

        run_git("add", "-A")
        # Drop judge packets if any slipped in
        staged = run_git("diff", "--cached", "--name-only")
        for line in staged.splitlines():
            if "_judge_packet" in line or re.search(r"judge_packet_.*\.md$", line):
                run_git("reset", "HEAD", "--", line)
                path = REPO_ROOT / line
                if path.exists():
                    path.unlink()

        date = commit_date(item.date_key)
        env = {"GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date}
        run_git("commit", "-m", item.message, env=env)
        print(f"committed: {item.message} @ {date}")

    run_git("branch", "-f", original_branch, "pilot-rebuild-tmp")
    run_git("checkout", original_branch)
    print(f"Updated {original_branch} from pilot-rebuild-tmp (backup: pilot-rebuild-backup)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    plan = build_plan()
    if args.dry_run:
        print(json.dumps([{"message": p.message, "date": commit_date(p.date_key), "files": len(p.output_paths + p.extra_paths)} for p in plan], indent=2))
        return 0
    if not args.apply:
        raise SystemExit("Use --dry-run or --apply")
    snap = snapshot_workspace()
    apply_plan(plan, snap)
    shutil.rmtree(snap, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
