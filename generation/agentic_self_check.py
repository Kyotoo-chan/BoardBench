#!/usr/bin/env python3
"""Evaluator-neutral self-check copied into isolated implementation workspaces."""

from __future__ import annotations

import copy
import importlib.util
import random
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("implementation.py")
MAX_ROLLOUTS = 40
MAX_STEPS = 300
MAX_STATES = 300


def load_module():
    spec = importlib.util.spec_from_file_location("generated_implementation", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    module = load_module()
    game = module.Game()
    rng = random.Random(1)
    checked_states = 0
    checked_actions = 0

    for _ in range(MAX_ROLLOUTS):
        state = game.initial_state()
        for _ in range(MAX_STEPS):
            terminal = bool(game.is_terminal(state))
            actions = list(game.legal_actions(state))
            if terminal:
                assert not actions, "terminal state exposes legal actions"
                break
            assert actions, "nonterminal state has no legal actions"

            raw_names = []
            for action in actions:
                name = str(game.action_to_name(action))
                assert name, "empty action name"
                assert game.name_to_action(name) == action, f"action does not round-trip: {name!r}"
                raw_names.append(name)

                cloned_game, cloned_state, cloned_action = copy.deepcopy((game, state, action))
                next_state = cloned_game.apply_action(cloned_state, cloned_action)
                if next_state is None:
                    next_state = cloned_state
                cloned_game.current_player(next_state)
                cloned_game.legal_actions(next_state)
                cloned_game.is_terminal(next_state)
                cloned_game.returns(next_state)
                checked_actions += 1

            assert len(raw_names) == len(set(raw_names)), "duplicate legal action names"
            state = game.apply_action(state, rng.choice(actions))
            if state is None:
                raise AssertionError("apply_action returned None")
            checked_states += 1
            if checked_states >= MAX_STATES:
                print(f"agentic-self-check OK states={checked_states} actions={checked_actions}")
                return

    assert checked_states > 0 and checked_actions > 0
    print(f"agentic-self-check OK states={checked_states} actions={checked_actions}")


if __name__ == "__main__":
    main()
