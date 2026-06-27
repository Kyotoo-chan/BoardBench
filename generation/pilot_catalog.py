"""Canonical pilot implementations and their source commits in git history."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from generation.config import RERUN_ORDER, output_stem

REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class PilotRun:
    game: str
    impl_backend: str  # gpt | claude | codex
    variant: str  # oneshot | agentic
    source_commit: str
    legacy_stem: str  # filename prefix in the source commit


# Best single commit per implementation (code + checks; judge may come from elsewhere).
PILOT_RUNS: tuple[PilotRun, ...] = (
    PilotRun("havannah", "gpt", "oneshot", "eab08ce", "havannah_oneshot"),
    PilotRun("havannah", "gpt", "agentic", "eab08ce", "havannah_agentic"),
    PilotRun("havannah", "claude", "oneshot", "f399d51", "havannah_oneshot"),
    PilotRun("havannah", "claude", "agentic", "f399d51", "havannah_agentic"),
    PilotRun("havannah", "codex", "oneshot", "59c4e5a", "havannah_oneshot"),
    PilotRun("havannah", "codex", "agentic", "59c4e5a", "havannah_agentic"),
    PilotRun("abalone", "gpt", "oneshot", "c077a8e", "abalone_oneshot"),
    PilotRun("abalone", "gpt", "agentic", "c077a8e", "abalone_agentic"),
    PilotRun("abalone", "claude", "oneshot", "0c2c94d", "abalone_oneshot"),
    PilotRun("abalone", "claude", "agentic", "0c2c94d", "abalone_agentic"),
    PilotRun("abalone", "codex", "oneshot", "5ad33e0", "abalone_oneshot"),
    PilotRun("abalone", "codex", "agentic", "5ad33e0", "abalone_agentic"),
    PilotRun("exploding_kittens", "gpt", "oneshot", "60e52d4", "exploding_kittens_oneshot"),
    PilotRun("exploding_kittens", "gpt", "agentic", "60e52d4", "exploding_kittens_agentic"),
    PilotRun("exploding_kittens", "claude", "oneshot", "c1ab5b9", "exploding_kittens_oneshot"),
    PilotRun("exploding_kittens", "claude", "agentic", "c1ab5b9", "exploding_kittens_agentic"),
    PilotRun("exploding_kittens", "codex", "oneshot", "b20ef7f", "expl_codex_os"),
    PilotRun("exploding_kittens", "codex", "agentic", "b20ef7f", "expl_codex_ag"),
)

# Optional extra judge-only sources when judge was committed separately from code.
JUDGE_SOURCES: dict[tuple[str, str, str, str], str] = {
    # game, impl_backend, variant, judge_backend -> commit
    ("havannah", "codex", "oneshot", "codex"): "c8f05a2",
    ("havannah", "codex", "agentic", "codex"): "c8f05a2",
    ("abalone", "codex", "oneshot", "codex"): "c8f05a2",
    ("abalone", "codex", "agentic", "codex"): "c8f05a2",
}

OPEN_SPIEL_SUFFIXES = (
    "_pre_align.py",
    "_action_align.md",
)

PAIR_SUFFIXES = (
    "_pair_action_align.md",
    "_pair_action_compare.txt",
)

SKIP_SUFFIXES = (
    "_generation_packet.md",
    "_first_gen.md",
    "_first_gen.py",
    "_pi_rerun_timing.txt",
    "_judge_packet.md",
)


def canonical_stem(game: str, impl_backend: str, variant: str) -> str:
    return output_stem(game, impl_backend, variant)


def iter_runs_for_game(game: str) -> list[PilotRun]:
    return [run for run in PILOT_RUNS if run.game == game]


def all_games() -> tuple[str, ...]:
    return RERUN_ORDER
