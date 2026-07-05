"""Shared game catalog and rulebook activation for BoardBench evaluation runs."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
INPUTS_DIR = REPO_ROOT / "inputs"
OUTPUTS_ROOT = REPO_ROOT / "outputs"
GAMES_DIR = INPUTS_DIR / "games"
WORKSPACES_DIR = REPO_ROOT / "generation_workspaces"


@dataclass(frozen=True)
class GameSpec:
    slug: str
    open_spiel_game: str
    include_openspiel_compare: bool
    use_implementation_brief: bool
    display_name: str
    notes: str = ""


GAME_CATALOG: dict[str, GameSpec] = {
    "havannah": GameSpec(
        slug="havannah",
        open_spiel_game="havannah(board_size=8)",
        include_openspiel_compare=True,
        use_implementation_brief=True,
        display_name="Havannah",
        notes="OpenSpiel reference available; pair compare worked 1000/1000 in first pilot.",
    ),
    "abalone": GameSpec(
        slug="abalone",
        open_spiel_game="none",
        include_openspiel_compare=False,
        use_implementation_brief=True,
        display_name="Abalone",
        notes="Setup depends on rulebook figures; no OpenSpiel compare in notebook defaults.",
    ),
    "exploding_kittens": GameSpec(
        slug="exploding_kittens",
        open_spiel_game="none",
        include_openspiel_compare=False,
        use_implementation_brief=True,
        display_name="Exploding Kittens",
        notes="Card game with chance and hidden information; no OpenSpiel reference.",
    ),
    "mahjong": GameSpec(
        slug="mahjong",
        open_spiel_game="none",
        include_openspiel_compare=False,
        use_implementation_brief=False,
        display_name="Mahjong",
        notes="Complex tile game; no OpenSpiel reference; PDF rulebook from user.",
    ),
}

RERUN_ORDER: tuple[str, ...] = ("havannah", "abalone", "exploding_kittens", "mahjong")

GAME_SHORT: dict[str, str] = {
    "havannah": "hav",
    "abalone": "aba",
    "exploding_kittens": "expl",
    "mahjong": "mjh",
}

VARIANT_SHORT: dict[str, str] = {
    "oneshot": "os",
    "agentic": "ag",
}

BACKEND_SHORT: dict[str, str] = {
    "pi": "gpt",
    "gpt": "gpt",
    "claude": "claude",
    "codex": "codex",
    "manual": "manual",
}


def normalize_backend(backend: str) -> str:
    key = backend.strip().lower()
    if key not in BACKEND_SHORT:
        raise KeyError(f"Unknown backend {backend!r}; known: {', '.join(BACKEND_SHORT)}")
    return BACKEND_SHORT[key]


def output_stem(game: str, backend: str, variant: str) -> str:
    """Build artifact stem like ``expl_codex_os`` (game_backend_variant)."""
    if variant not in VARIANT_SHORT:
        raise KeyError(f"Unknown variant {variant!r}; known: {', '.join(VARIANT_SHORT)}")
    if game not in GAME_SHORT:
        raise KeyError(f"Unknown game {game!r}; known: {', '.join(GAME_SHORT)}")
    return f"{GAME_SHORT[game]}_{normalize_backend(backend)}_{VARIANT_SHORT[variant]}"


def game_spec(slug: str) -> GameSpec:
    if slug not in GAME_CATALOG:
        known = ", ".join(GAME_CATALOG)
        raise KeyError(f"Unknown game slug {slug!r}; known: {known}")
    return GAME_CATALOG[slug]


def archived_rules_path(slug: str) -> Path:
    game_dir = GAMES_DIR / slug
    if not game_dir.is_dir():
        raise FileNotFoundError(f"Missing archived inputs directory: {game_dir.as_posix()}")

    candidates = sorted(
        path
        for path in game_dir.iterdir()
        if path.stem == "game_rules" and path.suffix.lower() in {".txt", ".pdf"}
    )
    if not candidates:
        raise FileNotFoundError(
            f"No archived game_rules file in {game_dir.as_posix()}; expected game_rules.txt or .pdf"
        )
    if len(candidates) > 1:
        names = ", ".join(path.name for path in candidates)
        raise RuntimeError(f"Multiple archived game_rules files in {game_dir.as_posix()}: {names}")
    return candidates[0]


def activate_game_rules(slug: str) -> Path:
    """Copy the archived rulebook for `slug` to inputs/game_rules.* for notebook runs."""

    source = archived_rules_path(slug)
    target = INPUTS_DIR / source.name

    for old in INPUTS_DIR.glob("game_rules.*"):
        if old.is_file() and old.name.startswith("game_rules."):
            old.unlink()

    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return target


def agentic_workspace_dir(slug: str) -> Path:
    return WORKSPACES_DIR / f"{slug}_agentic"


def game_output_dir(game: str, *, create: bool = False) -> Path:
    """Per-game run directory: ``outputs/<game_short>/`` (e.g. ``outputs/mjh/``)."""
    path = OUTPUTS_ROOT / GAME_SHORT[game]
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path


def clear_for_new_game_run(game: str) -> Path:
    """Keep only ``outputs/<game_short>/``; wipe it for a fresh run.

    Older runs live in git history (``git checkout <commit> -- outputs/...``).
    """
    short = GAME_SHORT[game]
    OUTPUTS_ROOT.mkdir(parents=True, exist_ok=True)
    for child in OUTPUTS_ROOT.iterdir():
        if child.name in {".gitkeep", short}:
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
    game_dir = OUTPUTS_ROOT / short
    if game_dir.exists():
        shutil.rmtree(game_dir)
    game_dir.mkdir(parents=True, exist_ok=True)
    return game_dir
