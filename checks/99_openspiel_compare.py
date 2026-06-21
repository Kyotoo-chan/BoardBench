"""Optionally compare sampled trajectories against an OpenSpiel reference.
Why: reference games help calibrate legal action availability, turn order, and returns.
"""

from __future__ import annotations

import itertools
import random
import re
from typing import Any

from common import (
    CheckContext,
    CheckResult,
    apply_action,
    current_player,
    is_terminal,
    legal_actions,
    make_game,
    returns,
    suppress_generated_output,
)

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


def describe_diff(open_keys: set[str], custom_keys: set[str]) -> str:
    missing = sorted(open_keys - custom_keys)
    extra = sorted(custom_keys - open_keys)
    parts = [f"openspiel={len(open_keys)} generated={len(custom_keys)}"]
    if missing:
        parts.append("missing=" + ", ".join(missing[:10]))
    if extra:
        parts.append("extra=" + ", ".join(extra[:10]))
    return "; ".join(parts)


def build_custom_action_map(game: Any, state: Any) -> dict[str, Any]:
    action_map: dict[str, Any] = {}
    raw_names: set[str] = set()
    for action in legal_actions(game, state):
        with suppress_generated_output():
            name = game.action_to_name(action)
            roundtrip = game.name_to_action(name)
        if roundtrip != action:
            raise RuntimeError(f"generated action name did not round-trip: {name!r}")
        if name in raw_names:
            raise RuntimeError(f"duplicate generated action name {name!r}")
        raw_names.add(name)

        key = canonical_action_name(name)
        if key in action_map:
            raise RuntimeError(f"ambiguous generated action key {key!r}")
        action_map[key] = action
    return action_map


def parse_fen_board(text: str) -> dict[str, str] | None:
    board_part = text.split()[0] if text.split() else ""
    ranks = board_part.split("/")
    if len(ranks) != 8:
        return None

    board: dict[str, str] = {}
    for rank_index, rank_text in enumerate(reversed(ranks), start=1):
        file_index = 0
        for char in rank_text:
            if char.isdigit():
                file_index += int(char)
                continue
            if file_index >= 8:
                return None
            square = "abcdefgh"[file_index] + str(rank_index)
            board[square] = char
            file_index += 1
        if file_index != 8:
            return None
    return board


def fen_transition_key(open_state: Any, action: Any, action_name: str) -> str | None:
    before = parse_fen_board(str(open_state))
    if before is None:
        return None

    clone = open_state.clone()
    clone.apply_action(action)
    after = parse_fen_board(str(clone))
    if after is None:
        return None

    targets = re.findall(r"[a-h][1-8]", action_name.lower())
    if not targets:
        return None
    target = targets[-1]
    moved = after.get(target)
    if moved is None:
        return None

    changed_from = [square for square, piece in before.items() if after.get(square) != piece]
    source_candidates = [square for square in changed_from if square != target]
    matching_sources = [
        square for square in source_candidates
        if before[square].isupper() == moved.isupper()
        and (before[square].lower() == moved.lower() or before[square].lower() == "p")
    ]
    if len(matching_sources) == 1:
        source = matching_sources[0]
    elif len(source_candidates) == 1:
        source = source_candidates[0]
    else:
        return None

    promotion = ""
    if before[source].lower() == "p" and moved.lower() != "p":
        promotion = moved.lower()
    return source + target + promotion


def build_open_action_map(open_game: Any, open_state: Any) -> dict[str, Any]:
    action_map: dict[str, Any] = {}

    if open_state.is_terminal():
        action_items = []
    elif open_state.is_chance_node():
        action_items = [
            (canonical_action_name(open_state.action_to_string(open_state.current_player(), action)), action)
            for action, _probability in open_state.chance_outcomes()
        ]
    elif open_state.is_simultaneous_node():
        per_player_actions = [open_state.legal_actions(player) for player in range(open_game.num_players())]
        action_items = []
        for joint_action in itertools.product(*per_player_actions):
            name = "|".join(
                f"p{player}:{open_state.action_to_string(player, action)}"
                for player, action in enumerate(joint_action)
            )
            action_items.append((canonical_action_name(name), tuple(joint_action)))
    else:
        player = open_state.current_player()
        action_items = []
        for action in open_state.legal_actions(player):
            name = open_state.action_to_string(player, action)
            key = fen_transition_key(open_state, action, name) or canonical_action_name(name)
            action_items.append((key, action))

    for key, action in action_items:
        if key in action_map:
            raise RuntimeError(f"ambiguous OpenSpiel action key {key!r}")
        action_map[key] = action
    return action_map


def open_node_type(open_state: Any) -> str:
    if open_state.is_terminal():
        return "terminal"
    if open_state.is_chance_node():
        return "chance"
    if open_state.is_simultaneous_node():
        return "simultaneous"
    return "player"


def custom_node_type(game: Any, state: Any) -> str:
    if is_terminal(game, state):
        return "terminal"
    player = current_player(game, state)
    if player == -2:
        return "chance"
    if player == -3:
        return "simultaneous"
    return "player"


def infer_player_map(open_game: Any, open_state: Any, custom_game: Any, custom_state: Any) -> dict[int, int]:
    player_count = open_game.num_players()
    identity = {player: player for player in range(player_count)}
    if player_count != 2 or open_node_type(open_state) != "player" or custom_node_type(custom_game, custom_state) != "player":
        return identity

    open_player = open_state.current_player()
    custom_player = current_player(custom_game, custom_state)
    if open_player not in (0, 1) or custom_player not in (0, 1):
        return identity
    return {open_player: custom_player, 1 - open_player: 1 - custom_player}


def compare_turn(open_state: Any, custom_game: Any, custom_state: Any, player_map: dict[int, int]) -> str | None:
    # Keep this focused on whose turn it is, with player-id mapping inferred from
    # the initial position. Legal action sets decide whether play can continue.
    open_type = open_node_type(open_state)
    custom_type = custom_node_type(custom_game, custom_state)
    if "terminal" in {open_type, custom_type}:
        return None
    if open_type == "player" and custom_type == "player":
        expected_custom = player_map.get(open_state.current_player(), open_state.current_player())
        actual_custom = current_player(custom_game, custom_state)
        if expected_custom != actual_custom:
            return f"current player mismatch: openspiel maps to {expected_custom}, generated={actual_custom}"
    return None


def compare_returns(open_state: Any, custom_game: Any, custom_state: Any, player_map: dict[int, int]) -> str | None:
    open_returns = list(open_state.returns())
    custom_returns = returns(custom_game, custom_state)
    if len(open_returns) != len(custom_returns):
        return f"return length mismatch: openspiel={open_returns}, generated={custom_returns}"
    for open_player, custom_player in player_map.items():
        if abs(float(open_returns[open_player]) - float(custom_returns[custom_player])) > 1e-9:
            return f"return mismatch: openspiel={open_returns}, generated={custom_returns}, map={player_map}"
    return None


def apply_open_action(open_state: Any, open_action: Any) -> None:
    if open_state.is_simultaneous_node():
        open_state.apply_actions(list(open_action))
    else:
        open_state.apply_action(open_action)


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
        _module, custom_game, custom_initial = make_game(ctx)
    except Exception as exc:
        return f"could not start generated game: {exc}"

    open_initial = open_game.new_initial_state()
    player_map = infer_player_map(open_game, open_initial, custom_game, custom_initial)
    rng = random.Random(ctx.seed)

    for rollout_index in range(ctx.rollouts):
        open_state = open_game.new_initial_state()
        custom_state = custom_game.initial_state()
        open_drives = rollout_index % 2 == 0

        for step in range(ctx.max_steps):
            try:
                open_actions = build_open_action_map(open_game, open_state)
                custom_actions = build_custom_action_map(custom_game, custom_state)
            except Exception as exc:
                return CheckResult(rollout_index, ctx.rollouts, f"rollout {rollout_index + 1}, step {step}: {exc}")

            open_keys = set(open_actions)
            custom_keys = set(custom_actions)
            if open_keys != custom_keys:
                return CheckResult(
                    rollout_index,
                    ctx.rollouts,
                    f"legal action mismatch in rollout {rollout_index + 1}, step {step}: "
                    + describe_diff(open_keys, custom_keys),
                )

            if not open_keys:
                if open_state.is_terminal() and is_terminal(custom_game, custom_state):
                    returns_message = compare_returns(open_state, custom_game, custom_state, player_map)
                    if returns_message:
                        return CheckResult(rollout_index, ctx.rollouts, f"rollout {rollout_index + 1}, step {step}: {returns_message}")
                break

            turn_message = compare_turn(open_state, custom_game, custom_state, player_map)
            if turn_message:
                return CheckResult(rollout_index, ctx.rollouts, f"rollout {rollout_index + 1}, step {step}: {turn_message}")

            keys = sorted(open_keys if open_drives else custom_keys)
            key = rng.choice(keys)
            open_action = open_actions[key]
            custom_action = custom_actions[key]

            try:
                apply_open_action(open_state, open_action)
            except Exception as exc:
                return CheckResult(rollout_index, ctx.rollouts, f"OpenSpiel apply failed in rollout {rollout_index + 1}, step {step}: {exc}")
            try:
                custom_state = apply_action(custom_game, custom_state, custom_action)
            except Exception as exc:
                return CheckResult(rollout_index, ctx.rollouts, f"generated apply failed in rollout {rollout_index + 1}, step {step}: {exc}")
        else:
            return CheckResult(
                rollout_index,
                ctx.rollouts,
                f"comparison rollout {rollout_index + 1} did not terminate within {ctx.max_steps} steps",
            )

    return CheckResult(ctx.rollouts, ctx.rollouts)
