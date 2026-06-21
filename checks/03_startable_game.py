"""Check that the generated module imports and can create an initial state.
Why: the result must be runnable before deeper API or rollout checks matter.
"""

from __future__ import annotations

from common import CheckContext, make_game


def run(ctx: CheckContext) -> str | None:
    try:
        _module, game, state = make_game(ctx)
    except Exception as exc:
        return f"could not import/start generated game: {exc}"

    if game is None:
        return "Game() returned None"
    if state is None:
        return "initial_state() returned None"
    return None
