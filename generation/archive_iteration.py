#!/usr/bin/env python3
"""Copy the single active output run into one compact versioned result directory."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
RESULTS = ROOT / "results/scores"
NAME = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def archive(game: str, iteration: str, condition: str, stem: str) -> Path:
    for label, value in (("game", game), ("iteration", iteration), ("condition", condition), ("stem", stem)):
        if not NAME.fullmatch(value):
            raise ValueError(f"invalid {label}: {value}")
    sources = sorted(path for path in OUTPUTS.glob(f"{stem}*") if path.is_file())
    if not sources:
        raise FileNotFoundError(f"no output artifacts for stem {stem}")
    destination = RESULTS / game / iteration
    raw = destination / "raw"
    planned: list[tuple[Path, Path]] = []
    copied: dict[str, str] = {}
    for source in sources:
        suffix = source.name[len(stem):]
        target_dir = raw if suffix.endswith("_events.jsonl") or "_usage" in suffix else destination
        target = target_dir / f"{condition}{suffix}"
        planned.append((source, target))
        copied[target.relative_to(destination).as_posix()] = sha256(source)

    manifest_path = destination / "iteration_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {
        "schema_version": 1,
        "game": game,
        "iteration": iteration,
        "conditions": {},
    }
    existing = manifest["conditions"].get(condition)
    if existing is not None and existing != copied:
        raise FileExistsError(f"condition already archived with a different artifact set: {condition}")
    for source, target in planned:
        if target.exists() and target.read_bytes() != source.read_bytes():
            raise FileExistsError(f"refusing to replace iteration artifact: {target}")
    for source, target in planned:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    manifest["conditions"][condition] = copied
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", required=True)
    parser.add_argument("--iteration", default="v2")
    parser.add_argument("--condition", required=True)
    parser.add_argument("--stem", required=True)
    args = parser.parse_args()
    print(archive(args.game, args.iteration, args.condition, args.stem))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
