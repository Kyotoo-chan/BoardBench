#!/usr/bin/env python3
"""Activate one archived game rulebook for notebook evaluation runs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from generation.config import GAME_CATALOG, RERUN_ORDER, activate_game_rules, game_spec  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "slug",
        nargs="?",
        choices=sorted(GAME_CATALOG),
        help="Game slug to activate (default: print catalog)",
    )
    parser.add_argument("--list", action="store_true", help="Print rerun order and exit")
    args = parser.parse_args()

    if args.list or args.slug is None:
        print("Rerun order:")
        for index, slug in enumerate(RERUN_ORDER, start=1):
            spec = game_spec(slug)
            print(f"  {index}. {slug} — OpenSpiel={spec.open_spiel_game}")
        return 0

    target = activate_game_rules(args.slug)
    spec = game_spec(args.slug)
    print(f"Activated {args.slug} -> {target.as_posix()}")
    print(f"Suggested notebook values:")
    print(f"  GAME = {args.slug!r}")
    print(f"  OPEN_SPIEL_GAME = {spec.open_spiel_game!r}")
    print(f"  INCLUDE_OPENSPIEL_COMPARE = {str(spec.include_openspiel_compare)}")
    print(f"  USE_IMPLEMENTATION_BRIEF = {str(spec.use_implementation_brief)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
