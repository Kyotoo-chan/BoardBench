#!/usr/bin/env python3
"""Create side branches with claude judge reviews at historical timestamps."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from generation.config import output_stem  # noqa: E402

BRANCHES = (
    {
        "branch": "judges/hav-claude",
        "parent": "a6d72a2",
        "game": "havannah",
        "date": "2026-06-28 12:15:00 +0200",
        "message": "save havannah claude judge reviews",
    },
    {
        "branch": "judges/aba-claude",
        "parent": "f5bf3a1",
        "game": "abalone",
        "date": "2026-06-29 01:05:00 +0200",
        "message": "save abalone claude judge reviews",
    },
    {
        "branch": "judges/expl-claude",
        "parent": "b59976d",
        "game": "exploding_kittens",
        "date": "2026-06-30 23:05:00 +0200",
        "message": "save exploding kittens claude judge reviews",
    },
)


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


def judge_paths(game: str) -> list[str]:
    paths: list[str] = []
    for variant in ("oneshot", "agentic"):
        stem = output_stem(game, "claude", variant)
        rel = f"outputs/{stem}_judge_claude.md"
        if not (REPO_ROOT / rel).is_file():
            raise FileNotFoundError(f"missing {rel}")
        paths.append(rel)
    return paths


def main() -> int:
    original = run_git("rev-parse", "--abbrev-ref", "HEAD")
    for spec in BRANCHES:
        # ponytail: always return to the source branch before resolving file paths.
        # After detached commits, path checks would otherwise run in the wrong tree.
        run_git("checkout", original)
        paths = judge_paths(spec["game"])
        run_git("checkout", "--detach", spec["parent"])
        for rel in paths:
            run_git("checkout", original, "--", rel)
        run_git("add", *paths)
        env = {
            "GIT_AUTHOR_DATE": spec["date"],
            "GIT_COMMITTER_DATE": spec["date"],
        }
        parent = run_git("rev-parse", "HEAD")
        tree = run_git("write-tree")
        commit = run_git(
            "commit-tree",
            tree,
            "-p",
            parent,
            "-m",
            spec["message"],
            env=env,
        )
        run_git("update-ref", "HEAD", commit)
        run_git("branch", "-f", spec["branch"], commit)
        print(f"{spec['branch']} -> {commit[:7]} @ {spec['date']}")
    run_git("checkout", original)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
