"""Contract-v2 Wizard adapter using only canonical data and the public Game API."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any

STATE_SCHEMA = "boardbench/wizard/state/1"
ACTION_SCHEMA = "boardbench/wizard/action/1"
OBSERVATION_SCHEMA = "boardbench/wizard/observation/1"
SUITS = {"menschen_blau", "elfen_gruen", "zwerge_rot", "riesen_gelb"}
SPECIALS = {"zauberer", "narr"}


class AdapterUntestable(Exception):
    """The implementation rejects a complete canonical fixture."""


def is_untestable(error: Exception) -> bool:
    return isinstance(error, AdapterUntestable)


def _envelope(payload: Any, schema: str) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != {"schema", "data"} or payload.get("schema") != schema or not isinstance(payload.get("data"), dict):
        raise AdapterUntestable(f"invalid canonical envelope for {schema}")
    return payload["data"]


def _state(game: Any, state: Any) -> dict[str, Any]:
    return _envelope(game.state_to_data(state), STATE_SCHEMA)


def _actions(game: Any, state: Any) -> list[tuple[Any, dict[str, Any]]]:
    result = []
    for action in game.legal_actions(state):
        data = _envelope(game.action_to_data(action), ACTION_SCHEMA)
        if not isinstance(data.get("type"), str) or not isinstance(data.get("actor"), int) or not isinstance(data.get("args"), dict):
            raise AdapterUntestable("invalid canonical action data")
        result.append((action, data))
    return result


def _all_cards(data: dict[str, Any]) -> list[str]:
    cards = [card for player in data["players"] for card in player["hand"]]
    zones = data["zones"]
    cards.extend(zones["deck"])
    if zones["revealed_trump"] is not None:
        cards.append(zones["revealed_trump"])
    cards.extend(entry["card"] for entry in zones["trick"])
    for trick in zones["completed_tricks"]:
        cards.extend(trick["cards"])
    cards.extend(zones["reserve"])
    return cards


def _player(data: dict[str, Any], player_id: int) -> dict[str, Any]:
    matches = [player for player in data["players"] if player.get("id") == player_id]
    if len(matches) != 1:
        raise AdapterUntestable(f"expected one canonical player with id {player_id}")
    return matches[0]


def _matches(data: dict[str, Any], selector: dict[str, Any]) -> bool:
    if "type" in selector and data["type"] != selector["type"]:
        return False
    if "actor" in selector and data["actor"] != int(selector["actor"]):
        return False
    return all(data["args"].get(key) == value for key, value in selector.get("args", {}).items())


def resolve_action(module: Any, game: Any, state: Any, actions: list[Any], selector: dict[str, Any]) -> Any:
    matches = [action for action, data in _actions(game, state) if _matches(data, selector)]
    if not matches:
        raise AssertionError(f"canonical action is not legal: {selector!r}")
    if len(matches) > 1 and not selector.get("choose_first"):
        raise AssertionError(f"canonical action is ambiguous: {selector!r}")
    return matches[0]


def _blank(data: dict[str, Any]) -> Counter[str]:
    inventory = Counter(_all_cards(data))
    for player in data["players"]:
        player["hand"] = []
        player["prediction"] = None
        player["tricks_won"] = 0
        player["score"] = 0
    data["round_number"] = 1
    data["dealer"] = 0
    data["leader"] = 1 % len(data["players"])
    data["current_player"] = data["leader"]
    data["phase"] = "predict"
    data["terminal"] = False
    data["trump_suit"] = None
    data["led_suit"] = None
    data["zones"] = {"deck": [], "revealed_trump": None, "trick": [], "completed_tricks": [], "reserve": []}
    data["pending"] = None
    data["chance"]["shuffle_index"] = 0
    return inventory


def setup(module: Any, game: Any, fixture: dict[str, Any]) -> Any:
    payload = deepcopy(game.state_to_data(game.initial_state()))
    data = _envelope(payload, STATE_SCHEMA)
    inventory = _blank(data)

    for field in ("round_number", "max_round", "dealer", "leader", "current_player"):
        if field in fixture:
            data[field] = int(fixture[field])
    for field in ("phase", "trump_suit", "led_suit"):
        if field in fixture:
            data[field] = fixture[field]
    if "terminal" in fixture:
        data["terminal"] = bool(fixture["terminal"])
        if data["terminal"]:
            data["phase"] = "terminal"
    if "pending" in fixture:
        data["pending"] = deepcopy(fixture["pending"])

    for player, cards in fixture.get("hands", {}).items():
        _player(data, int(player))["hand"] = list(cards)
    for field in ("prediction", "tricks_won", "score"):
        for player, value in fixture.get(field, {}).items():
            _player(data, int(player))[field] = None if value is None else int(value)

    zones = data["zones"]
    zones["deck"] = list(fixture.get("deck", []))
    zones["revealed_trump"] = fixture.get("revealed_trump")
    zones["trick"] = [
        {"player": int(entry["player"]), "card": str(entry["card"])}
        for entry in fixture.get("trick", [])
    ]
    zones["completed_tricks"] = [
        {"winner": int(entry["winner"]), "cards": list(entry["cards"])}
        for entry in fixture.get("completed_tricks", [])
    ]

    used = Counter(_all_cards(data))
    if used - inventory:
        raise AdapterUntestable(f"fixture exceeds generated component inventory: {dict(used - inventory)}")
    remaining = sorted((inventory - used).elements())
    if fixture.get("remaining_to_deck"):
        zones["deck"].extend(remaining)
    else:
        zones["reserve"] = remaining
    try:
        state = game.state_from_data(payload)
    except (TypeError, ValueError, AssertionError) as error:
        raise AdapterUntestable(f"state_from_data rejected canonical fixture: {error}") from error
    if game.state_to_data(state) != payload:
        raise AdapterUntestable("canonical fixture does not round-trip")
    return state


def _assert_equal(label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def _card_parts(card: str) -> tuple[str | None, int | None]:
    if card in SPECIALS:
        return None, None
    try:
        suit, rank = card.split(":", 1)
        return suit, int(rank)
    except (ValueError, AttributeError) as error:
        raise AssertionError(f"invalid card ID {card!r}") from error


def check(module: Any, game: Any, state: Any, expected: dict[str, Any]) -> None:
    data = _state(game, state)
    cards = _all_cards(data)

    scalar_fields = {
        "round_number": "round_number",
        "max_round": "max_round",
        "dealer": "dealer",
        "leader": "leader",
        "phase": "phase",
        "trump_suit": "trump_suit",
        "led_suit": "led_suit",
    }
    for key, field in scalar_fields.items():
        if key in expected:
            _assert_equal(key, data[field], expected[key])

    if "total_cards" in expected:
        _assert_equal("total_cards", len(cards), int(expected["total_cards"]))
    if "special_counts" in expected:
        for special, count in expected["special_counts"].items():
            _assert_equal(f"special_counts[{special}]", cards.count(special), int(count))
    if "ordinary_count" in expected:
        _assert_equal("ordinary_count", sum(card not in SPECIALS for card in cards), int(expected["ordinary_count"]))
    if expected.get("exact_suit_ranks"):
        for suit in SUITS:
            ranks = sorted(rank for card in cards for card_suit, rank in [_card_parts(card)] if card_suit == suit)
            _assert_equal(f"ranks[{suit}]", ranks, list(range(1, 14)))
    for player, wanted in expected.get("hand_sizes", {}).items():
        _assert_equal(f"hand_sizes[{player}]", len(_player(data, int(player))["hand"]), int(wanted))
    for field in ("prediction", "tricks_won", "score"):
        for player, wanted in expected.get(field, {}).items():
            _assert_equal(f"{field}[{player}]", _player(data, int(player))[field], wanted)
    if "deck_size" in expected:
        _assert_equal("deck_size", len(data["zones"]["deck"]), int(expected["deck_size"]))
    if "revealed_trump" in expected:
        _assert_equal("revealed_trump", data["zones"]["revealed_trump"], expected["revealed_trump"])
    if "completed_trick_count" in expected:
        _assert_equal("completed_trick_count", len(data["zones"]["completed_tricks"]), int(expected["completed_trick_count"]))
    if "last_trick_winner" in expected:
        if not data["zones"]["completed_tricks"]:
            raise AssertionError("no completed trick")
        _assert_equal("last_trick_winner", data["zones"]["completed_tricks"][-1]["winner"], int(expected["last_trick_winner"]))

    actions = [action for _, action in _actions(game, state)]
    if "legal_action_types" in expected:
        _assert_equal("legal_action_types", sorted({action["type"] for action in actions}), sorted(expected["legal_action_types"]))
    if "legal_trump_suits" in expected:
        actual = sorted(action["args"].get("suit") for action in actions if action["type"] == "choose_trump")
        _assert_equal("legal_trump_suits", actual, sorted(expected["legal_trump_suits"]))
    if "legal_predictions" in expected:
        actual = sorted(action["args"].get("tricks") for action in actions if action["type"] == "predict")
        _assert_equal("legal_predictions", actual, sorted(int(value) for value in expected["legal_predictions"]))
    if "legal_play_cards" in expected:
        actual = sorted(action["args"].get("card") for action in actions if action["type"] == "play_card")
        _assert_equal("legal_play_cards", actual, sorted(expected["legal_play_cards"]))
    for card in expected.get("legal_play_contains", []):
        if not any(action["type"] == "play_card" and action["args"].get("card") == card for action in actions):
            raise AssertionError(f"expected legal play {card!r}")
    for card in expected.get("legal_play_excludes", []):
        if any(action["type"] == "play_card" and action["args"].get("card") == card for action in actions):
            raise AssertionError(f"forbidden legal play {card!r}")

    if "winner_players" in expected:
        values = list(game.returns(state))
        best = max(values)
        winners = [index for index, value in enumerate(values) if value == best]
        _assert_equal("winner_players", winners, [int(value) for value in expected["winner_players"]])

    if "private_observation" in expected:
        player = int(expected["private_observation"])
        observation = _envelope(game.observation_to_data(state, player), OBSERVATION_SCHEMA)
        _assert_equal("own_hand", observation["own_hand"], _player(data, player)["hand"])
        for entry in observation["players"]:
            if "hand" in entry:
                raise AssertionError("opponent private hand leaked in observation")
            _assert_equal(f"hand_size[{entry['id']}]", entry["hand_size"], len(_player(data, int(entry["id"]))["hand"]))

    for count, wanted in expected.get("player_count_max_rounds", {}).items():
        probe = module.Game(num_players=int(count), seed=1)
        probe_data = _state(probe, probe.initial_state())
        _assert_equal(f"max_round[{count}]", probe_data["max_round"], int(wanted))
        _assert_equal(f"players[{count}]", len(probe_data["players"]), int(count))
