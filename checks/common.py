"""Shared helpers for BoardBench checks.
Why: keeps import, rollout, path, and result-reporting code out of tiny check files.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any


REQUIRED_GAME_METHODS = [
    "initial_state",
    "current_player",
    "legal_actions",
    "apply_action",
    "is_terminal",
    "returns",
    "render",
    "action_to_name",
    "name_to_action",
]


@dataclass(frozen=True)
class CheckResult:
    passed: int
    total: int
    message: str | None = None

    @property
    def score(self) -> float:
        """Normalized 0..1 score for this check.

        Checks report passed/total units. The score makes every check directly
        comparable while preserving the detailed unit counts.
        """

        if self.total <= 0:
            return 0.0
        return max(0.0, min(1.0, self.passed / self.total))


@dataclass(frozen=True)
class CheckContext:
    repo_root: Path
    game: str
    code_path: Path
    rollouts: int
    max_steps: int
    seed: int
    judge_path: Path | None = None


def resolve_repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_code_path(raw_path: str | Path, repo_root: Path) -> Path:
    requested = Path(raw_path)
    if requested.is_absolute():
        return requested

    candidates = [Path.cwd() / requested, repo_root / requested]
    if requested.parts and requested.parts[0] != "code":
        candidates.append(repo_root / "code" / requested)

    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()

    return candidates[0].resolve()


def resolve_optional_path(raw_path: str | Path | None, repo_root: Path) -> Path | None:
    if raw_path is None:
        return None
    requested = Path(raw_path)
    if requested.is_absolute():
        return requested
    for candidate in [Path.cwd() / requested, repo_root / requested]:
        if candidate.exists():
            return candidate.resolve()
    return (repo_root / requested).resolve()


def import_generated_module(ctx: CheckContext) -> ModuleType:
    module_name = f"boardbench_generated_{ctx.code_path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, ctx.code_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not import {ctx.code_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    with suppress_generated_output():
        spec.loader.exec_module(module)
    return module


@contextlib.contextmanager
def suppress_generated_output():
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        yield


def make_game(ctx: CheckContext) -> tuple[ModuleType, Any, Any]:
    module = import_generated_module(ctx)
    game_cls = getattr(module, "Game")
    with suppress_generated_output():
        game = game_cls()
        state = game.initial_state()
    return module, game, state


def apply_action(game: Any, state: Any, action: Any) -> Any:
    with suppress_generated_output():
        next_state = game.apply_action(state, action)
    return state if next_state is None else next_state


def legal_actions(game: Any, state: Any) -> list[Any]:
    with suppress_generated_output():
        return list(game.legal_actions(state))


def current_player(game: Any, state: Any) -> int:
    with suppress_generated_output():
        return int(game.current_player(state))


def is_terminal(game: Any, state: Any) -> bool:
    with suppress_generated_output():
        return bool(game.is_terminal(state))


def returns(game: Any, state: Any) -> list[float]:
    with suppress_generated_output():
        return list(game.returns(state))


def validate_state_basics(game: Any, state: Any, actions: list[Any]) -> str | None:
    with suppress_generated_output():
        rendered = game.render(state)
        if rendered != game.render(state):
            return "render(state) is not deterministic"

    names: set[str] = set()
    for action in actions:
        with suppress_generated_output():
            name = game.action_to_name(action)
            roundtrip = game.name_to_action(name)
        if name in names:
            return f"duplicate action name {name!r}"
        names.add(name)
        if roundtrip != action:
            return f"action name did not round-trip: {name!r}"
    return None


def random_rollout(game: Any, state: Any, rng: random.Random, max_steps: int) -> str | None:
    for _step in range(max_steps):
        terminal = is_terminal(game, state)
        actions = legal_actions(game, state)
        message = validate_state_basics(game, state, actions)
        if message:
            return message

        if terminal:
            if actions:
                return "terminal state still has legal actions"
            return None

        if not actions:
            return "non-terminal state has no legal actions"

        state = apply_action(game, state, rng.choice(actions))

    # The smoke test is about crashes/invalid states. Hitting the step cap is
    # allowed so long as every sampled state and action was usable.
    return None
