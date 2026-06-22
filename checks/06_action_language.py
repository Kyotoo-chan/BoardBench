"""Check normalized action-name language for sampled states.
Why: one-shot and agentic implementations must be comparable without inventing moves.
"""

from __future__ import annotations

import random

from action_normalizer import normalize_action_name
from common import CheckContext, CheckResult, apply_action, is_terminal, legal_actions, make_game, suppress_generated_output


def run(ctx: CheckContext) -> CheckResult | str | None:
    rng = random.Random(ctx.seed)
    samples = min(ctx.rollouts, 100)

    try:
        _module, game, _state = make_game(ctx)
    except Exception as exc:
        return f"could not start generated game: {exc}"

    for sample_index in range(samples):
        try:
            state = game.initial_state()
            for step in range(ctx.max_steps):
                actions = legal_actions(game, state)
                seen_raw: set[str] = set()
                seen_normalized: dict[str, str] = {}

                for action in actions:
                    with suppress_generated_output():
                        raw_name = str(game.action_to_name(action))
                        roundtrip = game.name_to_action(raw_name)
                    if roundtrip != action:
                        return CheckResult(sample_index, samples, f"action name did not round-trip: {raw_name!r}")
                    if raw_name in seen_raw:
                        return CheckResult(sample_index, samples, f"duplicate raw action name: {raw_name!r}")
                    seen_raw.add(raw_name)

                    normalized_name = normalize_action_name(raw_name)
                    if not normalized_name:
                        return CheckResult(sample_index, samples, f"empty normalized action name for {raw_name!r}")
                    previous = seen_normalized.get(normalized_name)
                    if previous is not None:
                        return CheckResult(
                            sample_index,
                            samples,
                            f"ambiguous normalized action name {normalized_name!r} from {previous!r} and {raw_name!r}",
                        )
                    seen_normalized[normalized_name] = raw_name

                if is_terminal(game, state) or not actions:
                    break
                state = apply_action(game, state, rng.choice(actions))
        except Exception as exc:
            return CheckResult(sample_index, samples, f"action-language sample {sample_index + 1} crashed: {exc}")

    return CheckResult(samples, samples)
