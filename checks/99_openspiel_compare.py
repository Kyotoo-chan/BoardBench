"""Optionally compare sampled trajectories against an OpenSpiel reference.
Why: reference games help calibrate action names, terminal timing, and returns.
"""

from __future__ import annotations

import random
import re
from typing import Any

from common import CheckContext, CheckResult, apply_action, is_terminal, legal_actions, make_game

FINAL_CHECK = True

PROMOTION_WORDS = {
    "q": "q",
    "queen": "q",
    "dame": "q",
    "r": "r",
    "rook": "r",
    "turm": "r",
    "b": "b",
    "bishop": "b",
    "laeufer": "b",
    "läufer": "b",
    "n": "n",
    "knight": "n",
    "springer": "n",
    "k": "k",
    "king": "k",
    "koenig": "k",
    "könig": "k",
}


def canonical_action_name(name: str) -> str:
    lowered = name.lower()
    squares = re.findall(r"[a-h][1-8]", lowered)
    if len(squares) >= 2:
        promotion = ""
        after_target = lowered.split(squares[1], 1)[1]
        if "=" in after_target:
            promotion_text = re.split(r"[^a-zäöü]+", after_target.split("=", 1)[1])[0]
            promotion = PROMOTION_WORDS.get(promotion_text, "")
        elif after_target[:1] in PROMOTION_WORDS:
            promotion = PROMOTION_WORDS[after_target[:1]]
        return squares[0] + squares[1] + promotion

    return re.sub(r"[^a-z0-9]+", "", lowered)


def build_custom_action_map(game: Any, state: Any) -> dict[str, Any]:
    action_map: dict[str, Any] = {}
    for action in legal_actions(game, state):
        name = game.action_to_name(action)
        key = canonical_action_name(name)
        if key in action_map:
            raise RuntimeError(f"ambiguous generated action key {key!r}")
        action_map[key] = action
    return action_map


def build_open_action_map(open_state: Any) -> dict[str, int]:
    player = open_state.current_player()
    action_map: dict[str, int] = {}
    for action in open_state.legal_actions(player):
        name = open_state.action_to_string(player, action)
        key = canonical_action_name(name)
        if key in action_map:
            raise RuntimeError(f"ambiguous OpenSpiel action key {key!r}")
        action_map[key] = action
    return action_map


def choose_from_open(open_state: Any, custom_game: Any, custom_state: Any, rng: random.Random) -> tuple[int, Any]:
    open_actions = build_open_action_map(open_state)
    custom_actions = build_custom_action_map(custom_game, custom_state)
    key = rng.choice(list(open_actions))
    if key not in custom_actions:
        raise RuntimeError(f"generated game does not offer OpenSpiel action {key!r}")
    return open_actions[key], custom_actions[key]


def choose_from_custom(open_state: Any, custom_game: Any, custom_state: Any, rng: random.Random) -> tuple[int, Any]:
    open_actions = build_open_action_map(open_state)
    custom_actions = build_custom_action_map(custom_game, custom_state)
    key = rng.choice(list(custom_actions))
    if key not in open_actions:
        raise RuntimeError(f"OpenSpiel does not offer generated action {key!r}")
    return open_actions[key], custom_actions[key]


def run(ctx: CheckContext) -> CheckResult | str | None:
    try:
        import pyspiel
    except ImportError as exc:
        return f"pyspiel is required for the final OpenSpiel comparison: {exc}"

    try:
        open_game = pyspiel.load_game(ctx.game)
    except Exception as exc:
        return f"could not load OpenSpiel game {ctx.game!r}: {exc}"

    try:
        _module, custom_game, _state = make_game(ctx)
    except Exception as exc:
        return f"could not start generated game: {exc}"

    rng = random.Random(ctx.seed)

    for rollout_index in range(ctx.rollouts):
        open_state = open_game.new_initial_state()
        custom_state = custom_game.initial_state()
        open_drives = rollout_index % 2 == 0

        for step in range(ctx.max_steps):
            open_terminal = open_state.is_terminal()
            custom_terminal = is_terminal(custom_game, custom_state)

            if open_terminal or custom_terminal:
                if open_terminal != custom_terminal:
                    return CheckResult(
                        rollout_index,
                        ctx.rollouts,
                        f"terminal mismatch in rollout {rollout_index + 1}, step {step}: "
                        f"openspiel={open_terminal}, generated={custom_terminal}",
                    )
                break

            try:
                if open_drives:
                    open_action, custom_action = choose_from_open(open_state, custom_game, custom_state, rng)
                else:
                    open_action, custom_action = choose_from_custom(open_state, custom_game, custom_state, rng)
            except Exception as exc:
                mode = "openspiel-driven" if open_drives else "generated-driven"
                return CheckResult(
                    rollout_index,
                    ctx.rollouts,
                    f"{mode} action matching failed in rollout {rollout_index + 1}, step {step}: {exc}",
                )

            open_state.apply_action(open_action)
            try:
                custom_state = apply_action(custom_game, custom_state, custom_action)
            except Exception as exc:
                return CheckResult(
                    rollout_index,
                    ctx.rollouts,
                    f"generated apply_action crashed in rollout {rollout_index + 1}, step {step}: {exc}",
                )
        else:
            return CheckResult(
                rollout_index,
                ctx.rollouts,
                f"comparison rollout {rollout_index + 1} did not terminate within {ctx.max_steps} steps",
            )

    return CheckResult(ctx.rollouts, ctx.rollouts)
