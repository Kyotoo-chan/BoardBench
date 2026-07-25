#!/usr/bin/env python3
"""Keep outputs/ as a single committed active-run workspace."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"


def entries(output_dir: Path) -> list[Path]:
    return sorted(path for path in output_dir.iterdir() if path.name != ".gitkeep")


def clean_outputs(
    output_dir: Path = OUTPUTS,
    *,
    keep_stem: str | None = None,
    require_tracked: bool = True,
) -> list[str]:
    candidates = [path for path in entries(output_dir) if not keep_stem or not path.name.startswith(keep_stem)]
    cache_dirs = [path for path in candidates if path.is_dir() and path.name == "__pycache__"]
    directories = [path.name for path in candidates if path.is_dir() and path.name != "__pycache__"]
    if directories:
        raise RuntimeError(f"outputs must stay flat; remove directories explicitly: {directories}")
    candidates = [path for path in candidates if not path.is_dir()]

    if require_tracked:
        uncommitted = []
        for path in candidates:
            relative = path.relative_to(ROOT).as_posix()
            result = subprocess.run(
                ["git", "cat-file", "-e", f"HEAD:{relative}"],
                cwd=ROOT,
                capture_output=True,
            )
            if result.returncode:
                uncommitted.append(relative)
        if uncommitted:
            raise RuntimeError(
                "refusing to clean uncommitted outputs; commit them first: " + ", ".join(uncommitted)
            )

    removed = []
    for path in cache_dirs:
        shutil.rmtree(path)
        removed.append(path.name)
    for path in candidates:
        path.unlink()
        removed.append(path.name)
    return removed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keep-stem", help="keep the current run while removing older committed runs")
    parser.add_argument("--check-empty", action="store_true", help="fail when outputs contains run artifacts")
    args = parser.parse_args()

    if args.check_empty:
        remaining = entries(OUTPUTS)
        if remaining:
            print("outputs not empty: " + ", ".join(path.name for path in remaining))
            return 1
        print("outputs clean")
        return 0

    removed = clean_outputs(keep_stem=args.keep_stem)
    print(f"removed {len(removed)} output artifact(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
