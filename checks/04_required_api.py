"""Check the minimal BoardBench API and first action-name round-trip.
Why: later comparisons need stable rendering, returns, legal actions, and action names.
"""

from __future__ import annotations

from numbers import Number

from common import CheckContext, CheckResult, REQUIRED_GAME_METHODS, legal_actions, make_game, suppress_generated_output


def run(ctx: CheckContext) -> CheckResult | str | None:
    passed = 0
    total = 8

    def fail(message: str) -> CheckResult:
        return CheckResult(passed, total, message)

    try:
        module, game, state = make_game(ctx)
    except Exception as exc:
        return fail(f"could not start generated game: {exc}")
    passed += 1

    if not hasattr(module, "GameState"):
        return fail("missing GameState")
    passed += 1

    if not hasattr(module, "Game"):
        return fail("missing Game")
    passed += 1

    missing = [name for name in REQUIRED_GAME_METHODS if not callable(getattr(game, name, None))]
    if missing:
        return fail("missing Game methods: " + ", ".join(missing))
    passed += 1

    try:
        with suppress_generated_output():
            rendered = game.render(state)
    except Exception as exc:
        return fail(f"render(initial_state) failed: {exc}")
    if not isinstance(rendered, str) or not rendered:
        return fail("render(initial_state) must return a non-empty string")
    passed += 1

    try:
        actions = legal_actions(game, state)
    except Exception as exc:
        return fail(f"legal_actions(initial_state) failed: {exc}")
    passed += 1

    if actions:
        action = actions[0]
        try:
            with suppress_generated_output():
                name = game.action_to_name(action)
                roundtrip = game.name_to_action(name)
        except Exception as exc:
            return fail(f"action name roundtrip failed: {exc}")
        if roundtrip != action:
            return fail("name_to_action(action_to_name(action)) did not round-trip")
    passed += 1

    try:
        with suppress_generated_output():
            returns = list(game.returns(state))
    except Exception as exc:
        return fail(f"returns(initial_state) failed: {exc}")
    if not returns or not all(isinstance(value, Number) for value in returns):
        return fail("returns(initial_state) must yield numeric values, one per player")
    passed += 1

    return CheckResult(passed, total)
