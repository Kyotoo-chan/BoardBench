"""Verify that action-language alignment did not change game behaviour.

The align step may rename actions, but it must not change legal moves, state
transitions, terminal states, or returns. This guard compares short seeded
trajectories before and after alignment and raises on the first difference.
"""

from __future__ import annotations

import argparse
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from common import (
        CheckContext,
        apply_action,
        current_player,
        is_terminal,
        legal_actions,
        make_game,
        returns,
        suppress_generated_output,
    )
except ModuleNotFoundError:  # Imported as checks.align_guard from a notebook.
    from checks.common import (
        CheckContext,
        apply_action,
        current_player,
        is_terminal,
        legal_actions,
        make_game,
        returns,
        suppress_generated_output,
    )


@dataclass(frozen=True)
class GuardResult:
    rollouts: int
    states: int


def _action_value(value: Any) -> Any:
    """Convert common action objects to a module-independent comparable value."""

    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, tuple):
        return ("tuple", tuple(_action_value(item) for item in value))
    if isinstance(value, list):
        return ("list", tuple(_action_value(item) for item in value))
    if isinstance(value, dict):
        return (
            "dict",
            tuple(sorted((str(key), _action_value(item)) for key, item in value.items())),
        )
    if hasattr(value, "value"):
        return (value.__class__.__name__, _action_value(value.value))
    if hasattr(value, "__dict__"):
        return (
            value.__class__.__name__,
            tuple(sorted((key, _action_value(item)) for key, item in vars(value).items())),
        )
    return repr(value)


def _seed(value: int) -> None:
    random.seed(value)
    try:
        import numpy as np
    except ImportError:
        return
    np.random.seed(value % (2**32))


def _make(path: Path, seed: int) -> tuple[Any, Any]:
    _seed(seed)
    ctx = CheckContext(
        repo_root=Path(__file__).resolve().parents[1],
        game=path.stem,
        code_path=path.resolve(),
        rollouts=1,
        max_steps=1,
        seed=seed,
    )
    _, game, state = make_game(ctx)
    return game, state


def _observable(game: Any, state: Any, actions: list[Any]) -> tuple[Any, ...]:
    terminal = is_terminal(game, state)
    with suppress_generated_output():
        rendered = game.render(state)
    return (
        current_player(game, state),
        terminal,
        tuple(_action_value(action) for action in actions),
        tuple(returns(game, state)) if terminal else None,
        rendered,
    )


def compare_alignment(
    before_path: Path,
    after_path: Path,
    *,
    rollouts: int = 5,
    max_steps: int = 100,
    seed: int = 1,
) -> GuardResult:
    """Compare seeded trajectories while deliberately ignoring action names."""

    states_checked = 0
    for rollout in range(rollouts):
        rollout_seed = seed + rollout
        before_game, before_state = _make(before_path, rollout_seed)
        after_game, after_state = _make(after_path, rollout_seed)
        chooser = random.Random(rollout_seed)

        for step in range(max_steps + 1):
            before_actions = legal_actions(before_game, before_state)
            after_actions = legal_actions(after_game, after_state)
            before_view = _observable(before_game, before_state, before_actions)
            after_view = _observable(after_game, after_state, after_actions)
            states_checked += 1

            if before_view != after_view:
                labels = ("current_player", "terminal", "legal_actions", "returns", "render")
                changed = [label for label, left, right in zip(labels, before_view, after_view) if left != right]
                raise RuntimeError(
                    f"alignment changed {', '.join(changed)} at rollout {rollout}, step {step}"
                )

            if before_view[1] or step == max_steps:
                break
            if not before_actions:
                break

            index = chooser.randrange(len(before_actions))
            transition_seed = rollout_seed * 100_000 + step
            _seed(transition_seed)
            before_state = apply_action(before_game, before_state, before_actions[index])
            _seed(transition_seed)
            after_state = apply_action(after_game, after_state, after_actions[index])

    return GuardResult(rollouts=rollouts, states=states_checked)


def assert_alignment_preserves_behavior(
    before_path: Path,
    after_path: Path,
    *,
    rollouts: int = 5,
    max_steps: int = 100,
    seed: int = 1,
) -> GuardResult:
    return compare_alignment(
        Path(before_path),
        Path(after_path),
        rollouts=rollouts,
        max_steps=max_steps,
        seed=seed,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    parser.add_argument("--rollouts", type=int, default=5)
    parser.add_argument("--max-steps", type=int, default=100)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()

    try:
        result = compare_alignment(
            args.before,
            args.after,
            rollouts=args.rollouts,
            max_steps=args.max_steps,
            seed=args.seed,
        )
    except Exception as exc:
        print(f"FAIL align_guard: {exc}")
        return 1

    print(f"OK align_guard {result.states} states across {result.rollouts} rollouts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
