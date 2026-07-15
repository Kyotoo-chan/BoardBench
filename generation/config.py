"""Shared game catalog and rulebook activation for BoardBench evaluation runs."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
INPUTS_DIR = REPO_ROOT / "inputs"
OUTPUTS_ROOT = REPO_ROOT / "outputs"
RESULTS_ROOT = REPO_ROOT / "results"
SCORES_ROOT = RESULTS_ROOT / "scores"
PLOTS_ROOT = RESULTS_ROOT / "plots"
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
    "catan": GameSpec(
        slug="catan",
        open_spiel_game="none",
        include_openspiel_compare=False,
        use_implementation_brief=True,
        display_name="CATAN",
        notes="Classic resource/trading game; official Kosmos PDF; no OpenSpiel reference.",
    ),
    "conect": GameSpec(
        slug="conect",
        open_spiel_game="none",
        include_openspiel_compare=False,
        use_implementation_brief=True,
        display_name="Conect",
        notes="Mark Steere 2024 connection game on a cone; free PDF; unlikely in training data.",
    ),
}

RERUN_ORDER: tuple[str, ...] = (
    "havannah",
    "abalone",
    "exploding_kittens",
    "mahjong",
    "catan",
    "conect",
)

GAME_SHORT: dict[str, str] = {
    "havannah": "hav",
    "abalone": "aba",
    "exploding_kittens": "expl",
    "mahjong": "mjh",
    "catan": "cat",
    "conect": "con",
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
    "glm": "glm",
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

    # All active PDFs share the stem ``game_rules``. Reusing that directory
    # after a game switch can attach pages from the previous rulebook.
    rendered_pages = INPUTS_DIR / "rulebook_pages" / target.stem
    if rendered_pages.exists():
        shutil.rmtree(rendered_pages)
    return target


def agentic_workspace_dir(slug: str) -> Path:
    return WORKSPACES_DIR / f"{slug}_agentic"


def clear_outputs(*, keep_gitkeep: bool = True, keep_names: frozenset[str] | None = None) -> None:
    """Wipe ``outputs/``; committed artifacts remain in git history."""
    keep = keep_names or frozenset()
    OUTPUTS_ROOT.mkdir(parents=True, exist_ok=True)
    for child in OUTPUTS_ROOT.iterdir():
        if child.name == ".gitkeep" and keep_gitkeep:
            continue
        if child.name in keep:
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


def clear_run_artifacts(game: str) -> None:
    """Drop generated run files; keep implementation brief for later backends."""
    brief = f"{game}_implementation_brief.md"
    keep = frozenset({brief}) if (OUTPUTS_ROOT / brief).exists() else frozenset()
    clear_outputs(keep_names=keep)


def clear_for_new_game_run(game: str) -> Path:
    """Empty ``outputs/`` before a new experiment run (``game`` labels intent in logs)."""
    _ = game
    clear_outputs()
    return OUTPUTS_ROOT
