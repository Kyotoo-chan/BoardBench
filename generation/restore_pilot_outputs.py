#!/usr/bin/env python3
"""Restore canonical pilot artifacts from git history into outputs/<game_short>/."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from generation.config import OUTPUTS_ROOT, RERUN_ORDER, clear_for_new_game_run, game_output_dir  # noqa: E402
from generation.pilot_catalog import (  # noqa: E402
    JUDGE_SOURCES,
    OPEN_SPIEL_SUFFIXES,
    PAIR_SUFFIXES,
    PILOT_RUNS,
    canonical_stem,
    iter_runs_for_game,
)


def git_show(commit: str, path: str) -> bytes | None:
    result = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=REPO_ROOT,
        capture_output=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout


def restore_file(commit: str, repo_path: str, target: Path) -> bool:
    data = git_show(commit, repo_path)
    if data is None:
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return True


def migrate_legacy_judge(
    game_dir: Path,
    stem: str,
    impl_backend: str,
    commit: str,
    legacy_stem: str,
) -> None:
    target = game_dir / f"{stem}_judge_{impl_backend}.md"
    if target.exists() and target.read_text(encoding="utf-8").strip():
        return
    legacy_repo = f"outputs/{legacy_stem}_judge.md"
    restore_file(commit, legacy_repo, target)


def restore_run(run, *, include_pair: bool) -> list[Path]:
    stem = canonical_stem(run.game, run.impl_backend, run.variant)
    game_dir = game_output_dir(run.game, create=True)
    written: list[Path] = []

    mappings = [
        (f"outputs/{run.legacy_stem}.py", game_dir / f"{stem}.py"),
        (f"outputs/{run.legacy_stem}.md", game_dir / f"{stem}.md"),
        (f"outputs/{run.legacy_stem}_checks.txt", game_dir / f"{stem}_checks.txt"),
    ]
    for repo_path, target in mappings:
        if restore_file(run.source_commit, repo_path, target):
            written.append(target)

    migrate_legacy_judge(game_dir, stem, run.impl_backend, run.source_commit, run.legacy_stem)

    judge_commit = JUDGE_SOURCES.get(
        (run.game, run.impl_backend, run.variant, run.impl_backend),
        run.source_commit,
    )
    if judge_commit != run.source_commit:
        migrate_legacy_judge(game_dir, stem, run.impl_backend, judge_commit, run.legacy_stem)

    for suffix in OPEN_SPIEL_SUFFIXES:
        repo_path = f"outputs/{run.legacy_stem}{suffix}"
        target = game_dir / f"{stem}{suffix}"
        if restore_file(run.source_commit, repo_path, target):
            written.append(target)

    return written


def restore_pair_artifacts(game: str, commit: str, legacy_prefix: str, backend: str) -> None:
    from generation.config import GAME_SHORT

    game_dir = game_output_dir(game, create=True)
    short = GAME_SHORT[game]
    for suffix in PAIR_SUFFIXES:
        repo_path = f"outputs/{legacy_prefix}{suffix}"
        target = game_dir / f"{short}_{backend}{suffix}"
        restore_file(commit, repo_path, target)


def clear_outputs(keep_gitkeep: bool = True) -> None:
    if not OUTPUTS_ROOT.exists():
        OUTPUTS_ROOT.mkdir(parents=True)
        return
    for path in OUTPUTS_ROOT.iterdir():
        if path.name == ".gitkeep" and keep_gitkeep:
            continue
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)


def restore_game(game: str, *, clear: bool) -> None:
    if clear:
        clear_for_new_game_run(game)
    else:
        game_output_dir(game, create=True)
    runs = iter_runs_for_game(game)
    for run in runs:
        restore_run(run, include_pair=False)
    if game == "havannah":
        restore_pair_artifacts("havannah", "f399d51", "havannah", "claude")
    elif game == "abalone":
        restore_pair_artifacts("abalone", "0c2c94d", "abalone", "claude")


def restore_all(*, clear: bool) -> None:
    if clear:
        clear_outputs()
    for run in PILOT_RUNS:
        restore_run(run, include_pair=False)
    restore_pair_artifacts("havannah", "f399d51", "havannah", "claude")
    restore_pair_artifacts("abalone", "0c2c94d", "abalone", "claude")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", choices=RERUN_ORDER)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--no-clear", action="store_true", help="Do not wipe outputs/ first")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    clear = not args.no_clear
    if args.all:
        restore_all(clear=clear)
        return 0
    if not args.game:
        raise SystemExit("Provide --game or --all")
    restore_game(args.game, clear=clear)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
