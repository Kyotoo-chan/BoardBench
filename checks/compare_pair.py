"""Compare two generated BoardBench implementations through normalized action names.
Why: one-shot and agentic runs may use different harmless syntax for the same legal move.
"""

from __future__ import annotations

import argparse
import random
import time
from pathlib import Path
from typing import Any

from action_normalizer import normalize_action_name
from common import (
    CheckContext,
    CheckResult,
    apply_action,
    current_player,
    is_terminal,
    legal_actions,
    make_game,
    resolve_code_path,
    resolve_repo_root,
    returns,
    suppress_generated_output,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare two generated game files by normalized legal-action language.")
    parser.add_argument("--game", default="antichess", help="Game name for reporting")
    parser.add_argument("--left-code-path", required=True, help="First generated Python file")
    parser.add_argument("--right-code-path", required=True, help="Second generated Python file")
    parser.add_argument("--left-label", default="oneshot", help="Label for the first implementation")
    parser.add_argument("--right-label", default="agentic", help="Label for the second implementation")
    parser.add_argument("--rollouts", type=int, default=100, help="Random lockstep trajectories to compare")
    parser.add_argument("--max-steps", type=int, default=1000, help="Maximum steps per trajectory")
    parser.add_argument("--seed", type=int, default=1, help="Random seed")
    return parser.parse_args()


def action_map(game: Any, state: Any) -> tuple[dict[str, Any], dict[str, str]]:
    mapped: dict[str, Any] = {}
    raw_by_key: dict[str, str] = {}
    raw_names: set[str] = set()

    for action in legal_actions(game, state):
        with suppress_generated_output():
            raw_name = str(game.action_to_name(action))
            roundtrip = game.name_to_action(raw_name)
        if roundtrip != action:
            raise RuntimeError(f"action name did not round-trip: {raw_name!r}")
        if raw_name in raw_names:
            raise RuntimeError(f"duplicate raw action name {raw_name!r}")
        raw_names.add(raw_name)

        key = normalize_action_name(raw_name)
        if not key:
            raise RuntimeError(f"empty normalized action name for {raw_name!r}")
        if key in mapped:
            raise RuntimeError(f"ambiguous normalized action key {key!r}: {raw_by_key[key]!r} and {raw_name!r}")
        mapped[key] = action
        raw_by_key[key] = raw_name
    return mapped, raw_by_key


def describe_diff(left_keys: set[str], right_keys: set[str], left_label: str, right_label: str) -> str:
    missing_from_right = sorted(left_keys - right_keys)
    missing_from_left = sorted(right_keys - left_keys)
    parts = [f"{left_label}={len(left_keys)} {right_label}={len(right_keys)}"]
    if missing_from_right:
        parts.append(f"only_{left_label}=" + ", ".join(missing_from_right[:10]))
    if missing_from_left:
        parts.append(f"only_{right_label}=" + ", ".join(missing_from_left[:10]))
    return "; ".join(parts)


def compare(args: argparse.Namespace) -> CheckResult | str | None:
    repo_root = resolve_repo_root()
    left_ctx = CheckContext(
        repo_root=repo_root,
        game=args.game,
        code_path=resolve_code_path(args.left_code_path, repo_root),
        rollouts=args.rollouts,
        max_steps=args.max_steps,
        seed=args.seed,
    )
    right_ctx = CheckContext(
        repo_root=repo_root,
        game=args.game,
        code_path=resolve_code_path(args.right_code_path, repo_root),
        rollouts=args.rollouts,
        max_steps=args.max_steps,
        seed=args.seed,
    )

    try:
        _left_module, left_game, _left_state = make_game(left_ctx)
        _right_module, right_game, _right_state = make_game(right_ctx)
    except Exception as exc:
        return f"could not start both generated games: {exc}"

    rng = random.Random(args.seed)
    for rollout_index in range(args.rollouts):
        left_state = left_game.initial_state()
        right_state = right_game.initial_state()

        for step in range(args.max_steps):
            try:
                left_terminal = is_terminal(left_game, left_state)
                right_terminal = is_terminal(right_game, right_state)
                if left_terminal != right_terminal:
                    return CheckResult(
                        rollout_index,
                        args.rollouts,
                        f"rollout {rollout_index + 1}, step {step}: terminal mismatch "
                        f"{args.left_label}={left_terminal} {args.right_label}={right_terminal}",
                    )

                if not left_terminal:
                    left_player = current_player(left_game, left_state)
                    right_player = current_player(right_game, right_state)
                    if left_player != right_player:
                        return CheckResult(
                            rollout_index,
                            args.rollouts,
                            f"rollout {rollout_index + 1}, step {step}: current player mismatch "
                            f"{args.left_label}={left_player} {args.right_label}={right_player}",
                        )

                left_actions, _left_raw = action_map(left_game, left_state)
                right_actions, _right_raw = action_map(right_game, right_state)
            except Exception as exc:
                return CheckResult(rollout_index, args.rollouts, f"rollout {rollout_index + 1}, step {step}: {exc}")

            left_keys = set(left_actions)
            right_keys = set(right_actions)
            if left_keys != right_keys:
                return CheckResult(
                    rollout_index,
                    args.rollouts,
                    f"legal action mismatch in rollout {rollout_index + 1}, step {step}: "
                    + describe_diff(left_keys, right_keys, args.left_label, args.right_label),
                )

            if not left_keys:
                if left_terminal and right_terminal:
                    left_returns = returns(left_game, left_state)
                    right_returns = returns(right_game, right_state)
                    if [float(value) for value in left_returns] != [float(value) for value in right_returns]:
                        return CheckResult(
                            rollout_index,
                            args.rollouts,
                            f"rollout {rollout_index + 1}, step {step}: return mismatch "
                            f"{args.left_label}={left_returns} {args.right_label}={right_returns}",
                        )
                break

            key = rng.choice(sorted(left_keys))
            try:
                left_state = apply_action(left_game, left_state, left_actions[key])
                right_state = apply_action(right_game, right_state, right_actions[key])
            except Exception as exc:
                return CheckResult(rollout_index, args.rollouts, f"apply failed in rollout {rollout_index + 1}, step {step}: {exc}")
        # Hitting the cap is allowed here. This comparison checks that both
        # implementations expose the same normalized action language along the
        # sampled prefix, not that every sampled game must terminate quickly.

    return CheckResult(args.rollouts, args.rollouts)


def main() -> int:
    args = parse_args()
    print(f"comparing action language: {args.left_code_path} <-> {args.right_code_path}", flush=True)
    started = time.perf_counter()
    result = compare(args)
    elapsed = time.perf_counter() - started

    if isinstance(result, CheckResult):
        status = "OK" if result.message is None else "FAIL"
        print(f"{status:<4} pair_action_compare {result.passed}/{result.total} {elapsed:.2f}s" + (f"  {result.message}" if result.message else ""), flush=True)
        print(f"summary: {1 if result.message is None else 0}/1 checks, {result.passed}/{result.total} units, {elapsed:.2f}s", flush=True)
        return 1 if result.message else 0

    if result is None:
        print(f"OK   pair_action_compare {args.rollouts}/{args.rollouts} {elapsed:.2f}s", flush=True)
        print(f"summary: 1/1 checks, {args.rollouts}/{args.rollouts} units, {elapsed:.2f}s", flush=True)
        return 0

    print(f"FAIL pair_action_compare 0/1 {elapsed:.2f}s  {result}", flush=True)
    print(f"summary: 0/1 checks, 0/1 units, {elapsed:.2f}s", flush=True)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
