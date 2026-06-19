from __future__ import annotations

from numbers import Number

from common import REQUIRED_GAME_METHODS, CheckContext, legal_actions, make_game, suppress_generated_output


def run(ctx: CheckContext) -> str | None:
    try:
        module, game, state = make_game(ctx)
    except Exception as exc:
        return f"could not start generated game: {exc}"

    if not hasattr(module, "GameState"):
        return "missing GameState"
    if not hasattr(module, "Game"):
        return "missing Game"

    missing = [name for name in REQUIRED_GAME_METHODS if not callable(getattr(game, name, None))]
    if missing:
        return "missing Game methods: " + ", ".join(missing)

    try:
        with suppress_generated_output():
            rendered = game.render(state)
    except Exception as exc:
        return f"render(initial_state) failed: {exc}"
    if not isinstance(rendered, str) or not rendered:
        return "render(initial_state) must return a non-empty string"

    try:
        actions = legal_actions(game, state)
    except Exception as exc:
        return f"legal_actions(initial_state) failed: {exc}"

    if actions:
        action = actions[0]
        try:
            with suppress_generated_output():
                name = game.action_to_name(action)
                roundtrip = game.name_to_action(name)
        except Exception as exc:
            return f"action name roundtrip failed: {exc}"
        if roundtrip != action:
            return "name_to_action(action_to_name(action)) did not round-trip"

    try:
        with suppress_generated_output():
            returns = list(game.returns(state))
    except Exception as exc:
        return f"returns(initial_state) failed: {exc}"
    if not returns or not all(isinstance(value, Number) for value in returns):
        return "returns(initial_state) must yield numeric values, one per player"

    return None
