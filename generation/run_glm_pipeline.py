#!/usr/bin/env python3
"""Run one full GLM pipeline: generation, checks, and cross judges.

Default target is exploding_kittens with both variants and judges gpt+codex.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from generation.config import output_stem  # noqa: E402
from generation.run_cross_judges import parse_judge_backends, run_judges  # noqa: E402
from generation.run_glm_series import USAGE_LOG_PATH, run_one as run_glm_one  # noqa: E402


def _read_total_cost(game: str, variant: str) -> float | None:
    stem = output_stem(game, "glm", variant)
    if not USAGE_LOG_PATH.exists():
        return None
    last: float | None = None
    with USAGE_LOG_PATH.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("stem") != stem:
                continue
            raw = (row.get("total_cost_usd") or "").strip()
            if raw:
                last = float(raw)
    return last


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", default="exploding_kittens")
    parser.add_argument("--skip-checks", action="store_true")
    parser.add_argument("--judges", default="gpt,codex", help="Comma-separated judge backends")
    parser.add_argument("--force-judges", action="store_true")
    parser.add_argument("--effort", choices=("high", "max"), default="high")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print(
        f"pipeline start game={args.game} variants=oneshot+agentic judges={args.judges} effort={args.effort}",
        flush=True,
    )
    failed_variants: list[str] = []
    for variant in ("oneshot", "agentic"):
        try:
            run_glm_one(args.game, variant, skip_checks=args.skip_checks, effort=args.effort)
        except Exception as exc:
            failed_variants.append(variant)
            print(f"WARN generation step failed for {args.game} {variant}: {exc}", flush=True)

    judges = parse_judge_backends(args.judges)
    targets = [(args.game, "glm", "oneshot"), (args.game, "glm", "agentic")]
    run_judges(targets, judges, force=args.force_judges)

    os_cost = _read_total_cost(args.game, "oneshot")
    ag_cost = _read_total_cost(args.game, "agentic")
    known = [x for x in (os_cost, ag_cost) if x is not None]
    total = sum(known) if known else None
    total_text = "n/a" if total is None else f"${total:.6f}"
    print(f"pipeline done game={args.game} approx_generation_cost={total_text}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
