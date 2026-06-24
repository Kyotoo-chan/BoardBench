"""Run many random rollouts through the generated game.
Why: random play catches crashes, invalid dead states, and terminal states with actions.
"""

from __future__ import annotations

import random

from common import CheckContext, CheckResult, make_game, random_rollout


def run(ctx: CheckContext) -> CheckResult | str | None:
    rng = random.Random(ctx.seed)

    try:
        _module, game, _state = make_game(ctx)
    except Exception as exc:
        return f"could not start generated game: {exc}"

    passed = 0
    first_error: str | None = None

    for rollout_index in range(ctx.rollouts):
        try:
            state = game.initial_state()
            message = random_rollout(game, state, rng, ctx.max_steps)
        except Exception as exc:
            message = f"random rollout {rollout_index + 1} crashed: {exc}"

        if message:
            if first_error is None:
                first_error = message
            continue
        passed += 1

    if passed == ctx.rollouts:
        return CheckResult(passed, ctx.rollouts)
    return CheckResult(passed, ctx.rollouts, first_error)
