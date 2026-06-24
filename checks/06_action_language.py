"""Check normalized action-name language for sampled states.
Why: one-shot and agentic implementations must be comparable without inventing moves.

There is no finite global list of all possible actions for most games, so this
check samples random rollouts and validates every legal action name once in each
visited state. Each action check is one unit. The rollout budget is fixed at
100, matching the default notebook `ROLLOUTS` for `05_random_rollouts`.
"""

from __future__ import annotations

import random

from action_normalizer import normalize_action_name
from common import CheckContext, CheckResult, apply_action, is_terminal, legal_actions, make_game, suppress_generated_output

ACTION_LANGUAGE_ROLLOUTS = 100


def _validate_action(game, action, seen_raw: set[str], seen_normalized: dict[str, str]) -> str | None:
    with suppress_generated_output():
        raw_name = str(game.action_to_name(action))
        roundtrip = game.name_to_action(raw_name)
    if roundtrip != action:
        return f"action name did not round-trip: {raw_name!r}"
    if raw_name in seen_raw:
        return f"duplicate raw action name: {raw_name!r}"
    seen_raw.add(raw_name)

    normalized_name = normalize_action_name(raw_name)
    if not normalized_name:
        return f"empty normalized action name for {raw_name!r}"
    previous = seen_normalized.get(normalized_name)
    if previous is not None:
        return (
            f"ambiguous normalized action name {normalized_name!r} "
            f"from {previous!r} and {raw_name!r}"
        )
    seen_normalized[normalized_name] = raw_name
    return None


def run(ctx: CheckContext) -> CheckResult | str | None:
    rng = random.Random(ctx.seed)

    try:
        _module, game, _state = make_game(ctx)
    except Exception as exc:
        return f"could not start generated game: {exc}"

    passed = 0
    total = 0
    first_error: str | None = None

    for rollout_index in range(ACTION_LANGUAGE_ROLLOUTS):
        try:
            state = game.initial_state()
            for step in range(ctx.max_steps):
                actions = legal_actions(game, state)
                seen_raw: set[str] = set()
                seen_normalized: dict[str, str] = {}

                for action in actions:
                    total += 1
                    message = _validate_action(game, action, seen_raw, seen_normalized)
                    if message is not None:
                        if first_error is None:
                            first_error = (
                                f"rollout {rollout_index + 1}, step {step}: {message}"
                            )
                        continue
                    passed += 1

                if is_terminal(game, state) or not actions:
                    break
                state = apply_action(game, state, rng.choice(actions))
        except Exception as exc:
            total += 1
            if first_error is None:
                first_error = f"action-language rollout {rollout_index + 1} crashed: {exc}"

    if total == 0:
        return CheckResult(0, 0, "no action-language checks were run")
    if passed == total:
        return CheckResult(passed, total)
    return CheckResult(passed, total, first_error)
