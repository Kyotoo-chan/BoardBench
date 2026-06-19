from __future__ import annotations

import random

from common import CheckContext, make_game, random_rollout


def run(ctx: CheckContext) -> str | None:
    rng = random.Random(ctx.seed)

    try:
        _module, game, _state = make_game(ctx)
    except Exception as exc:
        return f"could not start generated game: {exc}"

    for rollout_index in range(ctx.rollouts):
        try:
            state = game.initial_state()
            message = random_rollout(game, state, rng, ctx.max_steps)
        except Exception as exc:
            return f"random rollout {rollout_index + 1} crashed: {exc}"

        if message:
            return f"random rollout {rollout_index + 1} failed: {message}"

    return None
