#!/usr/bin/env python3
"""Per-backend BoardBench git workflow: generation, tests, plot — each one commit for both variants.

``outputs/`` is cleared automatically on ``prepare`` and before each backend's oneshot run
(no separate clear commit).

Default judge set: gpt + codex only (no claude judge).

Example::

  python generation/game_run_workflow.py prepare catan
  python generation/game_run_workflow.py files --step generation --game catan --backend codex
  python generation/game_run_workflow.py plot --game catan --backend codex
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "plots") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "plots"))

from generation.config import GAME_SHORT, activate_game_rules, clear_outputs, game_spec, output_stem  # noqa: E402
from plots.collect_scores import (  # noqa: E402
    PLOT_BACKEND,
    PLOT_VARIANT,
    WORKFLOW_JUDGE_BACKENDS,
    collect_game_scores,
    pin_key,
    pinned_path,
    read_pinned_file,
    write_pinned_file,
)

OUTPUTS = REPO_ROOT / "outputs"
PLOTS = REPO_ROOT / "plots"

BACKEND_ALIASES = {"pi": "gpt", "gpt": "gpt", "codex": "codex", "claude": "claude"}
VARIANTS = ("oneshot", "agentic")


def normalize_backend(name: str) -> str:
    key = name.strip().lower()
    if key not in BACKEND_ALIASES:
        raise ValueError(f"Unknown backend {name!r}")
    return BACKEND_ALIASES[key]


def stem_for(game: str, backend: str, variant: str) -> str:
    return output_stem(game, normalize_backend(backend), variant)


def variants_for(variant: str | None) -> tuple[str, ...]:
    if variant:
        return (variant,)
    return VARIANTS


def generation_files(game: str, backend: str, variant: str | None = None) -> list[Path]:
    paths: list[Path] = []
    for item in variants_for(variant):
        stem = stem_for(game, backend, item)
        paths.extend([OUTPUTS / f"{stem}.py", OUTPUTS / f"{stem}.md"])
    return [path for path in paths if path.exists()]


def test_files(game: str, backend: str, variant: str | None = None) -> list[Path]:
    paths: list[Path] = []
    for item in variants_for(variant):
        stem = stem_for(game, backend, item)
        paths.append(OUTPUTS / f"{stem}_checks.txt")
        for judge in WORKFLOW_JUDGE_BACKENDS:
            paths.append(OUTPUTS / f"{stem}_judge_{judge}.md")
    return [path for path in paths if path.exists()]


def plot_files(game: str) -> list[Path]:
    slug = GAME_SHORT[game]
    paths = [
        PLOTS / f"{slug}_scores.png",
        PLOTS / f"{slug}_scores.txt",
        pinned_path(slug),
    ]
    return [path for path in paths if path.exists()]


def pin_run(game: str, backend: str, variant: str) -> Path:
    impl = normalize_backend(backend)
    data = collect_game_scores(game)
    plot_backend = PLOT_BACKEND[impl]
    plot_variant = PLOT_VARIANT[variant]
    plot_key = (plot_backend, plot_variant)
    row = data["scores"][plot_key]
    slug = GAME_SHORT[game]
    pinned = read_pinned_file(slug)
    pinned[pin_key(plot_backend, plot_variant)] = row
    return write_pinned_file(slug, pinned)


def run_plot(game: str) -> None:
    subprocess.run(
        [sys.executable, str(PLOTS / "make_plots.py"), "--game", game],
        cwd=REPO_ROOT,
        check=True,
    )


def auto_clear_before_run(game: str, backend: str, variant: str) -> None:
    """Clear stale outputs before the first variant of a backend batch."""
    if variant != "oneshot":
        return
    clear_outputs()
    print(f"cleared outputs/ before {game} {normalize_backend(backend)} oneshot")


def pin_backend(game: str, backend: str, variant: str | None = None) -> list[Path]:
    paths: list[Path] = []
    for item in variants_for(variant):
        paths.append(pin_run(game, backend, item))
    return paths


def plot_backend(game: str, backend: str, variant: str | None = None) -> None:
    pin_backend(game, backend, variant)
    run_plot(game)


def cmd_files(args: argparse.Namespace) -> int:
    step = args.step
    variant = args.variant or None
    if step == "generation":
        paths = generation_files(args.game, args.backend, variant)
    elif step == "tests":
        paths = test_files(args.game, args.backend, variant)
    elif step == "plot":
        paths = plot_files(args.game)
    elif step == "prepare":
        paths = [REPO_ROOT / "inputs" / "game_rules.pdf"]
        brief = OUTPUTS / f"{args.game}_implementation_brief.md"
        if brief.exists():
            paths.append(brief)
    else:
        raise SystemExit(f"Unknown step: {step}")
    for path in paths:
        print(path.relative_to(REPO_ROOT).as_posix())
    return 0


def cmd_pin(args: argparse.Namespace) -> int:
    paths = pin_backend(args.game, args.backend, args.variant or None)
    for path in paths:
        print(f"pinned {args.game} {args.backend} -> {path.as_posix()}")
    return 0


def cmd_plot(args: argparse.Namespace) -> int:
    plot_backend(args.game, args.backend, args.variant or None)
    return 0


def cmd_clear(args: argparse.Namespace) -> int:
    clear_outputs()
    print(f"cleared outputs/ ({args.game})")
    return 0


def cmd_prepare(args: argparse.Namespace) -> int:
    clear_outputs()
    activate_game_rules(args.game)
    print(f"cleared outputs/ and activated rulebook for {args.game}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    files = sub.add_parser("files", help="Print repo-relative paths to stage for one commit step")
    files.add_argument("--step", choices=("prepare", "generation", "tests", "plot"))
    files.add_argument("--game", required=True)
    files.add_argument("--backend", default="")
    files.add_argument("--variant", choices=VARIANTS, default="")

    for name in ("pin", "plot"):
        p = sub.add_parser(name)
        p.add_argument("--game", required=True)
        p.add_argument("--backend", required=True)
        p.add_argument("--variant", choices=VARIANTS, default="")

    clear = sub.add_parser("clear", help="Manual clear only; normal workflow clears on prepare/oneshot")
    clear.add_argument("--game", default="")

    prep = sub.add_parser("prepare", help="Clear outputs/ and activate archived rulebook into inputs/")
    prep.add_argument("game")

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "files":
        if args.step in {"generation", "tests"} and not args.backend:
            raise SystemExit("--backend required for generation/tests")
        return cmd_files(args)
    if args.command == "pin":
        return cmd_pin(args)
    if args.command == "plot":
        return cmd_plot(args)
    if args.command == "clear":
        return cmd_clear(args)
    if args.command == "prepare":
        return cmd_prepare(args)
    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
