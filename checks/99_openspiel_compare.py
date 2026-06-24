"""Optionally compare sampled trajectories against an OpenSpiel reference.
Why: reference games help calibrate legal action availability, turn order, and returns.
"""

from __future__ import annotations

import itertools
import random
import re
from typing import Any

from action_normalizer import normalize_action_name, parse_qr_coordinates
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


def describe_diff(open_keys: set[str], custom_keys: set[str]) -> str:
    missing = sorted(open_keys - custom_keys)
    extra = sorted(custom_keys - open_keys)
    parts = [f"openspiel={len(open_keys)} generated={len(custom_keys)}"]
    if missing:
        parts.append("missing=" + ", ".join(missing[:10]))
    if extra:
        parts.append("extra=" + ", ".join(extra[:10]))
    return "; ".join(parts)


def parse_open_spiel_board_size(game_name: str) -> int | None:
    match = re.search(r"board_size\s*=\s*(\d+)", game_name)
    if match is None:
        return None
    return int(match.group(1))


def havannah_open_label_from_axial(game_name: str, q: int, r: int) -> str | None:
    if not game_name.startswith("havannah"):
        return None
    board_size = parse_open_spiel_board_size(game_name)
    if board_size is None:
        return None

    radius = board_size - 1
    if max(abs(q), abs(r), abs(q + r)) > radius:
        return None
    row = r + radius + 1
    q_min = max(-radius, -r - radius)
    q_max = min(radius, -r + radius)
    if q < q_min or q > q_max:
        return None
    # OpenSpiel's Havannah labels keep absolute columns across rows: the top
    # half starts at `a`, the middle row spans `a..`, and the bottom half shifts
    # right (`b..`, `c..`, ...). For axial coordinates in row order this is
    # q + r + radius.
    column_index = q + r + radius
    if column_index < 0 or column_index >= 26:
        return None
    return f"{chr(ord('a') + column_index)}{row}"


def havannah_open_labels(game_name: str) -> set[str]:
    board_size = parse_open_spiel_board_size(game_name)
    if not game_name.startswith("havannah") or board_size is None:
        return set()
    radius = board_size - 1
    labels = set()
    for r in range(-radius, radius + 1):
        q_min = max(-radius, -r - radius)
        q_max = min(radius, -r + radius)
        for q in range(q_min, q_max + 1):
            label = havannah_open_label_from_axial(game_name, q, r)
            if label is not None:
                labels.add(label)
    return labels


def havannah_row_label_reference(game_name: str, action_name: str) -> str | None:
    """Map row-letter labels like A1, B1, ..., O8 to OpenSpiel labels."""

    if not game_name.startswith("havannah"):
        return None
    board_size = parse_open_spiel_board_size(game_name)
    if board_size is None:
        return None

    normalized = normalize_action_name(action_name)
    target = normalized[len("place:") :] if normalized.startswith("place:") else normalized
    match = re.fullmatch(r"([a-z])(\d+)", target)
    if match is None:
        return None

    radius = board_size - 1
    row_index = ord(match.group(1)) - ord("a")
    col = int(match.group(2))
    if row_index < 0 or row_index > 2 * radius or col <= 0:
        return None

    r = row_index - radius
    q_min = max(-radius, -r - radius)
    q_max = min(radius, -r + radius)
    if col > q_max - q_min + 1:
        return None
    q = q_min + col - 1
    return havannah_open_label_from_axial(game_name, q, r)


def havannah_reference_label(game_name: str, action_name: str) -> str | None:
    """Map generated axial q/r Havannah names to OpenSpiel point labels.

    OpenSpiel Havannah labels rows with numbers and columns with letters
    (`a1`, `b1`, ...). Generated implementations often use axial q/r
    coordinates instead because the scanned rulebook has no point labels. This
    adapter is only used inside the optional OpenSpiel comparison; general
    BoardBench checks keep using generated action names and the generic
    normalizer.
    """

    coords = parse_qr_coordinates(action_name)
    if coords is None:
        return None
    q, r = coords
    return havannah_open_label_from_axial(game_name, q, r)


def custom_reference_key(game_name: str, action_name: str, *, row_label_scheme: bool = False) -> str | None:
    label = havannah_reference_label(game_name, action_name)
    if label is not None:
        return label

    normalized = normalize_action_name(action_name)
    if row_label_scheme:
        label = havannah_row_label_reference(game_name, action_name)
        if label is not None:
            return label
    if normalized.startswith("place:"):
        target = normalized[len("place:") :]
        if re.fullmatch(r"[a-z]+\d+", target):
            return target
    return None


def infer_havannah_row_label_scheme(game_name: str, names: list[str]) -> bool:
    valid_open_labels = havannah_open_labels(game_name)
    if not valid_open_labels:
        return False
    saw_row_label = False
    for name in names:
        normalized = normalize_action_name(name)
        target = normalized[len("place:") :] if normalized.startswith("place:") else normalized
        if not re.fullmatch(r"[a-z]\d+", target):
            continue
        row_label = havannah_row_label_reference(game_name, name)
        if row_label is None:
            continue
        saw_row_label = True
        if target not in valid_open_labels:
            return True
    return False if not saw_row_label else False


def build_custom_action_map(game_name: str, game: Any, state: Any, row_label_scheme: bool | None = None) -> dict[str, Any]:
    items: list[tuple[Any, str]] = []
    raw_names: set[str] = set()
    for action in legal_actions(game, state):
        with suppress_generated_output():
            name = str(game.action_to_name(action))
            roundtrip = game.name_to_action(name)
        if roundtrip != action:
            raise RuntimeError(f"generated action name did not round-trip: {name!r}")
        if name in raw_names:
            raise RuntimeError(f"duplicate generated action name {name!r}")
        raw_names.add(name)
        items.append((action, name))

    if row_label_scheme is None:
        row_label_scheme = infer_havannah_row_label_scheme(game_name, [name for _action, name in items])
    action_map: dict[str, Any] = {}
    for action, name in items:
        key = custom_reference_key(game_name, name, row_label_scheme=row_label_scheme) or normalize_action_name(name)
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
        promotion = "=" + moved.lower()
    return normalize_action_name(f"move:{source}->{target}{promotion}")


def build_open_action_map(open_game: Any, open_state: Any) -> dict[str, Any]:
    action_map: dict[str, Any] = {}

    if open_state.is_terminal():
        action_items = []
    elif open_state.is_chance_node():
        action_items = [
            (normalize_action_name(open_state.action_to_string(open_state.current_player(), action)), action)
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
            action_items.append((normalize_action_name(name), tuple(joint_action)))
    else:
        player = open_state.current_player()
        action_items = []
        for action in open_state.legal_actions(player):
            name = open_state.action_to_string(player, action)
            key = fen_transition_key(open_state, action, name) or normalize_action_name(name)
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
    initial_names = []
    for action in legal_actions(custom_game, custom_initial):
        with suppress_generated_output():
            initial_names.append(str(custom_game.action_to_name(action)))
    custom_row_label_scheme = infer_havannah_row_label_scheme(ctx.game, initial_names)
    rng = random.Random(ctx.seed)

    passed_units = 0
    total_units = 0
    issue_count = 0
    issue_examples: list[str] = []

    def record_issue(message: str) -> None:
        nonlocal issue_count
        issue_count += 1
        if len(issue_examples) < 3:
            issue_examples.append(message)

    for rollout_index in range(ctx.rollouts):
        open_state = open_game.new_initial_state()
        custom_state = custom_game.initial_state()

        for step in range(ctx.max_steps):
            location = f"rollout {rollout_index + 1}, step {step}"
            try:
                open_actions = build_open_action_map(open_game, open_state)
                custom_actions = build_custom_action_map(ctx.game, custom_game, custom_state, custom_row_label_scheme)
            except Exception as exc:
                total_units += 1
                record_issue(f"{location}: {exc}")
                break

            open_keys = set(open_actions)
            custom_keys = set(custom_actions)
            common_keys = open_keys & custom_keys
            all_keys = open_keys | custom_keys

            # Legal-action agreement is scored by overlap, not as all-or-nothing.
            # This lets later rollouts continue and gives credit when many legal
            # actions still match despite missing/extra moves.
            action_units = max(len(all_keys), 1)
            total_units += action_units
            if open_keys == custom_keys:
                passed_units += action_units
            else:
                passed_units += len(common_keys)
                record_issue(f"legal action mismatch in {location}: " + describe_diff(open_keys, custom_keys))

            if not open_keys and not custom_keys:
                if open_state.is_terminal() and is_terminal(custom_game, custom_state):
                    total_units += 1
                    returns_message = compare_returns(open_state, custom_game, custom_state, player_map)
                    if returns_message:
                        record_issue(f"{location}: {returns_message}")
                    else:
                        passed_units += 1
                break

            total_units += 1
            turn_message = compare_turn(open_state, custom_game, custom_state, player_map)
            if turn_message:
                record_issue(f"{location}: {turn_message}")
            else:
                passed_units += 1

            if not common_keys:
                # There is no action that can be applied to both states. Stop
                # this rollout, but keep testing further sampled rollouts.
                record_issue(f"{location}: no shared legal action to continue this rollout")
                break

            key = rng.choice(sorted(common_keys))
            open_action = open_actions[key]
            custom_action = custom_actions[key]

            total_units += 1
            try:
                apply_open_action(open_state, open_action)
                custom_state = apply_action(custom_game, custom_state, custom_action)
            except Exception as exc:
                record_issue(f"apply failed in {location}: {exc}")
                break
            else:
                passed_units += 1
        # Hitting the cap is allowed here. This optional reference check verifies
        # that implementations expose matching legal-action prefixes along
        # sampled trajectories; many board games, and some OpenSpiel variants,
        # may not terminate within a small comparison budget.

    if total_units == 0:
        return CheckResult(0, 1, "no comparison states were evaluated")
    if issue_count:
        suffix = f"; {issue_count} total issue(s)" if issue_count > len(issue_examples) else ""
        return CheckResult(passed_units, total_units, "; ".join(issue_examples) + suffix)
    return CheckResult(passed_units, total_units)
