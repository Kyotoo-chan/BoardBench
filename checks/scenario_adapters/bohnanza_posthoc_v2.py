"""Evaluator-only semantic adapter for generated Bohnanza modules."""

from __future__ import annotations

import ast
import inspect
import textwrap
from collections import Counter
from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import is_dataclass, replace
from typing import Any

ALIASES = {
    "weinbrand": ("weinbrand", "brandy"),
    "blau": ("blaue", "blau", "blue"),
    "feuer": ("feuer", "fire"),
    "sau": ("saubohne", "sau", "broad"),
    "brech": ("brech", "wax"),
    "soja": ("soja", "soy"),
    "augen": ("augen", "black-eyed", "black eyed"),
    "rot": ("rote", "rot", "red"),
    "garten": ("garten", "garden"),
    "acker": ("acker", "field bean"),
}
PLAYER_FIELDS = ("active_player", "current", "player", "active")
DISCARD_FIELDS = ("discard", "discard_pile", "ablage")
REVEALED_FIELDS = ("revealed", "face_up", "market", "table", "turned", "trade_cards")
COIN_FIELDS = ("coins", "scores", "talers", "taler")
DEPLETION_FIELDS = ("depletions", "depletion_count", "empty_count", "deck_empties", "reshuffles")
PHASE_ALIASES = {
    "plant_hand": ("plant_first", "plant1", "phase1_first", "phase1_must_plant", "plant_hand"),
    "plant_hand_second": ("plant_second", "plant2", "phase1_second", "phase1_optional"),
    "reveal": ("reveal", "flip", "phase2_draw"),
    "trade": ("trade", "phase2_trade"),
    "plant_traded": ("plant_traded", "plant_pending", "plant_acquired", "plant_received", "plant_incoming", "plant_trades", "phase3"),
    "draw": ("draw_round", "draw_each", "draw_three", "phase4", "draw"),
}


class AdapterUntestable(Exception):
    """The legacy implementation cannot represent the requested canonical fixture."""


def is_untestable(error: Exception) -> bool:
    return isinstance(error, AdapterUntestable)


def _cards(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        return [card for card, count in value.items() for _ in range(int(count))]
    if isinstance(value, (str, bytes)):
        return [value]
    return list(value)


def _like(original: Any, values: list[Any]) -> Any:
    if isinstance(original, Mapping):
        result = original.copy()
        for key in result:
            result[key] = 0
        for value in values:
            result[value] = result.get(value, 0) + 1
        return result
    if isinstance(original, tuple):
        return tuple(values)
    if isinstance(original, list):
        return list(values)
    return list(values)


def _all_cards(state: Any) -> list[Any]:
    found: list[Any] = []
    for name in ("deck", *DISCARD_FIELDS, *REVEALED_FIELDS, "pending_cards"):
        if hasattr(state, name):
            found.extend(_cards(getattr(state, name)))
    for name in ("hands", "fields", "bean_fields", "pending_received", "traded", "received", "sideways"):
        if not hasattr(state, name):
            continue
        value = getattr(state, name)
        groups = value.values() if isinstance(value, Mapping) else value
        for group in groups:
            subgroups = group.values() if isinstance(group, Mapping) else group
            if name in ("fields", "bean_fields"):
                for field in subgroups:
                    found.extend(_cards(field))
            else:
                found.extend(_cards(group))
    players = getattr(state, "players", None)
    if not hasattr(state, "hands") and isinstance(players, Sequence) and not isinstance(players, (str, bytes)):
        for player in players:
            found.extend(_cards(getattr(player, "hand", ())))
            for field in getattr(player, "fields", ()):
                found.extend(_cards(field))
    return found


def _card(module: Any, game: Any, semantic: str) -> Any:
    candidates: list[Any] = []
    for name in ("CARD_COUNTS", "BEAN_COUNTS", "CARDS", "BEANS", "CARD_TYPES", "BEAN_TYPES"):
        value = getattr(module, name, ())
        raw = value.keys() if isinstance(value, Mapping) else value
        for candidate in raw:
            if isinstance(candidate, Sequence) and not isinstance(candidate, (str, bytes)) and candidate and isinstance(candidate[0], str):
                candidates.append(candidate[0])
            else:
                candidates.append(candidate)
    try:
        candidates.extend(_all_cards(game.initial_state()))
    except Exception:
        pass
    aliases = ALIASES[semantic]
    seen: set[str] = set()
    for candidate in candidates:
        key = f"{type(candidate).__name__}:{candidate!r}"
        if key in seen:
            continue
        seen.add(key)
        text = str(getattr(candidate, "value", candidate)).casefold()
        if any(alias in text for alias in aliases):
            return candidate
    for name, value in vars(module).items():
        if isinstance(value, Mapping):
            for key in value:
                text = str(getattr(key, "value", key)).casefold()
                if any(alias in text for alias in aliases):
                    return key
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            for item in value:
                candidate = item[0] if isinstance(item, Sequence) and not isinstance(item, (str, bytes)) and item else item
                text = str(getattr(candidate, "value", candidate)).casefold()
                if any(alias in text for alias in aliases):
                    return candidate
        else:
            text = f"{name} {value}".casefold()
            if any(alias in text for alias in aliases):
                return value
    raise AdapterUntestable(f"implementation has no identifiable {semantic!r} card")


def _field(state: Any, names: Sequence[str]) -> str | None:
    return next((name for name in names if hasattr(state, name)), None)


def _convert_like(original: Any, value: Any) -> Any:
    enum_type = type(original)
    if hasattr(enum_type, "__members__"):
        folded = str(value).casefold()
        for member in enum_type:
            if folded in f"{member.name} {member.value}".casefold():
                return member
    if isinstance(original, str):
        return {
            "plant_hand": "phase1",
            "plant_hand_second": "phase1",
            "reveal": "phase2_draw",
            "trade": "phase2_trade",
            "plant_traded": "phase3",
            "draw": "phase4",
        }.get(str(value), value)
    return value


def _phase_like(game: Any, original: Any, value: str) -> Any:
    aliases = PHASE_ALIASES[str(value)]
    enum_type = type(original)
    if hasattr(enum_type, "__members__"):
        for member in enum_type:
            text = f"{member.name} {member.value}".casefold()
            if any(alias in text for alias in aliases):
                return member
    if isinstance(original, str):
        available: set[str] = set()
        try:
            tree = ast.parse(textwrap.dedent(inspect.getsource(game.legal_actions)))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Compare) or not isinstance(node.left, ast.Attribute) or node.left.attr != "phase":
                    continue
                for comparator in node.comparators:
                    values = comparator.elts if isinstance(comparator, (ast.Tuple, ast.List)) else [comparator]
                    available.update(value.value for value in values if isinstance(value, ast.Constant) and isinstance(value.value, str))
        except (OSError, TypeError, IndentationError, SyntaxError):
            pass
        for alias in aliases:
            if alias in available:
                return alias
    raise AdapterUntestable(f"implementation has no canonical phase for {value!r}")


def _with(state: Any, changes: dict[str, Any]) -> Any:
    valid = {key: value for key, value in changes.items() if hasattr(state, key)}
    if is_dataclass(state):
        return replace(state, **valid)
    result = deepcopy(state)
    for key, value in valid.items():
        setattr(result, key, value)
    return result


def _player_groups(state: Any, names: Sequence[str]) -> tuple[str, list[Any]]:
    name = _field(state, names)
    if name is None:
        raise AdapterUntestable(f"state has none of {tuple(names)!r}")
    value = getattr(state, name)
    if isinstance(value, Mapping):
        return name, [value[key] for key in sorted(value, key=lambda item: int(item))]
    return name, list(value)


def _set_player_groups(original: Any, groups: list[Any]) -> Any:
    if isinstance(original, tuple):
        return tuple(groups)
    if isinstance(original, Mapping):
        result = original.copy()
        for index, value in enumerate(groups):
            key = index if index in result else str(index)
            result[key] = value
        return result
    return groups


def _named_actions(game: Any, state: Any) -> list[str]:
    return [str(game.action_to_name(action)).casefold() for action in game.legal_actions(state)]


def _has_number(action: Any, wanted: int) -> bool:
    if not isinstance(action, tuple):
        return False
    for value in action[1:]:
        try:
            if int(value) == wanted:
                return True
        except (TypeError, ValueError):
            continue
    return False


def setup(module: Any, game: Any, fixture: dict[str, Any]) -> Any:
    state = game.initial_state()
    changes: dict[str, Any] = {}

    if "hands" in fixture:
        name, groups = _player_groups(state, ("hands", "hand"))
        for player, semantic_cards in fixture["hands"].items():
            index = int(player)
            groups[index] = _like(groups[index], [_card(module, game, card) for card in semantic_cards])
        changes[name] = _set_player_groups(getattr(state, name), groups)

    if "fields" in fixture:
        name, groups = _player_groups(state, ("fields", "bean_fields", "farms"))
        for player, semantic_fields in fixture["fields"].items():
            index = int(player)
            existing = list(groups[index])
            converted = []
            for field_index, semantic_cards in enumerate(semantic_fields):
                template = existing[field_index] if field_index < len(existing) else []
                converted.append(_like(template, [_card(module, game, card) for card in semantic_cards]))
            groups[index] = tuple(converted) if isinstance(groups[index], tuple) else converted
        changes[name] = _set_player_groups(getattr(state, name), groups)

    for fixture_name, state_names in (
        ("deck", ("deck", "draw_pile")),
        ("discard", DISCARD_FIELDS),
        ("revealed", REVEALED_FIELDS),
    ):
        if fixture_name not in fixture:
            continue
        name = _field(state, state_names)
        if name is None:
            raise AdapterUntestable(f"state has no {fixture_name} container")
        values = [_card(module, game, card) for card in fixture[fixture_name]]
        changes[name] = _like(getattr(state, name), values)

    if "pending_received" in fixture:
        name = _field(state, ("pending_received", "traded", "received", "sideways"))
        if name is None:
            raise AdapterUntestable("state has no pending-received container")
        original = getattr(state, name)
        result = list(original) if isinstance(original, tuple) else deepcopy(original)
        for player, cards in fixture["pending_received"].items():
            key = int(player) if not isinstance(result, Mapping) or int(player) in result else str(player)
            template = result[key]
            result[key] = _like(template, [_card(module, game, card) for card in cards])
        changes[name] = tuple(result) if isinstance(original, tuple) else result

    direct = (
        ("phase", ("phase",)),
        ("active_player", PLAYER_FIELDS),
        ("depletions", DEPLETION_FIELDS),
        ("start_player", ("start_player", "starting_player")),
        ("winner", ("winner", "winners")),
        ("terminal", ("terminal", "done", "game_over")),
    )
    for fixture_name, names in direct:
        if fixture_name not in fixture:
            continue
        name = _field(state, names)
        if name is None:
            if fixture_name in ("winner", "terminal") or (fixture_name == "start_player" and fixture[fixture_name] == 0):
                continue
            raise AdapterUntestable(f"state has no field for {fixture_name}")
        value = fixture[fixture_name]
        if fixture_name == "winner" and name == "winners":
            value = [int(value)]
        changes[name] = _phase_like(game, getattr(state, name), value) if fixture_name == "phase" else _convert_like(getattr(state, name), value)

    if fixture.get("phase") == "plant_hand_second" and hasattr(state, "phase1_planted"):
        changes["phase1_planted"] = 1
    if fixture.get("phase") == "draw" and hasattr(state, "draw_order"):
        player_count = int(getattr(state, "players", len(getattr(state, "hands", []))))
        active = int(fixture.get("active_player", getattr(state, _field(state, PLAYER_FIELDS) or "active", 0)))
        changes["draw_order"] = [(active + offset) % player_count for offset in range(player_count)]

    if "pending_gift" in fixture:
        gift = fixture["pending_gift"]
        if not hasattr(module, "TradeDraft") or not hasattr(state, "trade"):
            raise AdapterUntestable("implementation has no pending trade representation")
        sender, recipient = int(gift["from"]), int(gift["to"])
        offered = [_card(module, game, card) for card in gift["cards"]]
        hand = list(changes.get("hands", state.hands)[sender])
        indices = [hand.index(card) for card in offered]
        changes["trade"] = module.TradeDraft(recipient, offered_hand=indices, awaiting_consent=True)
        decision_name = _field(state, ("decision", *PLAYER_FIELDS))
        if decision_name:
            changes[decision_name] = recipient

    if "coins" in fixture:
        name = _field(state, COIN_FIELDS)
        if name is None:
            raise AdapterUntestable("state has no coin/score field")
        original = getattr(state, name)
        values = list(original)
        for player, count in fixture["coins"].items():
            values[int(player)] = int(count)
        changes[name] = tuple(values) if isinstance(original, tuple) else values

    if fixture.get("third_field"):
        name = _field(state, ("third_field", "third_fields", "field_unlocked", "field_counts"))
        if name is not None:
            original = getattr(state, name)
            values = list(original) if not isinstance(original, Mapping) else original.copy()
            for player, enabled in fixture["third_field"].items():
                index = int(player)
                key = index if not isinstance(values, Mapping) or index in values else str(index)
                values[key] = 3 if "count" in name else bool(enabled)
            changes[name] = tuple(values) if isinstance(original, tuple) else values

    result = _with(state, changes)
    if fixture.get("terminal") and not fixture.get("winner") and hasattr(game, "_finish"):
        game._finish(result)
    return result


def _assert_equal(label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def check(module: Any, game: Any, state: Any, expected: dict[str, Any]) -> None:
    if "total_cards" in expected or "card_counts" in expected:
        cards = _all_cards(state)
        if "total_cards" in expected:
            _assert_equal("total_cards", len(cards), int(expected["total_cards"]))
        for semantic, wanted in expected.get("card_counts", {}).items():
            _assert_equal(f"card_counts[{semantic}]", cards.count(_card(module, game, semantic)), int(wanted))

    hands_name = _field(state, ("hands", "hand"))
    if any(key in expected for key in ("hand_size", "hand_size_all", "hand_order")):
        if hands_name is None:
            raise AdapterUntestable("state has no hands")
        _, hands = _player_groups(state, (hands_name,))
        if "hand_size_all" in expected:
            for player, hand in enumerate(hands):
                _assert_equal(f"hand_size[{player}]", len(_cards(hand)), int(expected["hand_size_all"]))
        for player, wanted in expected.get("hand_size", {}).items():
            _assert_equal(f"hand_size[{player}]", len(_cards(hands[int(player)])), int(wanted))
        for player, wanted in expected.get("hand_order", {}).items():
            actual = _cards(hands[int(player)])
            semantic = [_card(module, game, card) for card in wanted]
            _assert_equal(f"hand_order[{player}]", actual, semantic)

    fields_name = _field(state, ("fields", "bean_fields", "farms"))
    if any(key in expected for key in ("field_count", "field_sizes", "field_counts")):
        if fields_name is None:
            raise AdapterUntestable("state has no bean fields")
        _, fields = _player_groups(state, (fields_name,))
        player = int(expected.get("player", 0))
        if "field_count" in expected:
            _assert_equal("field_count", len(fields[player]), int(expected["field_count"]))
        for owner, wanted in expected.get("field_sizes", {}).items():
            actual = [len(_cards(field)) for field in fields[int(owner)]]
            _assert_equal(f"field_sizes[{owner}]", actual, [int(value) for value in wanted])
        for owner, wanted in expected.get("field_counts", {}).items():
            cards = [card for field in fields[int(owner)] for card in _cards(field)]
            for semantic, count in wanted.items():
                _assert_equal(f"field_counts[{owner}][{semantic}]", cards.count(_card(module, game, semantic)), int(count))

    if "coins" in expected:
        name = _field(state, COIN_FIELDS)
        if name is None:
            raise AdapterUntestable("state has no coin/score field")
        values = getattr(state, name)
        for player, wanted in expected["coins"].items():
            actual = values[int(player)] if not isinstance(values, Mapping) else values.get(int(player), values.get(str(player)))
            _assert_equal(f"coins[{player}]", int(actual), int(wanted))

    if "discard_count" in expected or "discard_size" in expected:
        name = _field(state, DISCARD_FIELDS)
        if name is None:
            raise AdapterUntestable("state has no discard")
        cards = _cards(getattr(state, name))
        if "discard_size" in expected:
            _assert_equal("discard_size", len(cards), int(expected["discard_size"]))
        for semantic, wanted in expected.get("discard_count", {}).items():
            _assert_equal(f"discard_count[{semantic}]", cards.count(_card(module, game, semantic)), int(wanted))

    if "revealed_size" in expected:
        name = _field(state, REVEALED_FIELDS)
        if name is None:
            raise AdapterUntestable("state has no revealed-card container")
        _assert_equal("revealed_size", len(_cards(getattr(state, name))), int(expected["revealed_size"]))

    if "deck_size" in expected:
        name = _field(state, ("deck", "draw_pile"))
        if name is None:
            raise AdapterUntestable("state has no deck")
        _assert_equal("deck_size", len(_cards(getattr(state, name))), int(expected["deck_size"]))

    if "depletions" in expected:
        name = _field(state, DEPLETION_FIELDS)
        if name is None:
            raise AdapterUntestable("state has no depletion counter")
        _assert_equal("depletions", int(getattr(state, name)), int(expected["depletions"]))

    if "phase_contains_any" in expected:
        name = _field(state, ("phase",))
        if name is None:
            raise AdapterUntestable("state has no phase")
        text = str(getattr(state, name)).casefold()
        if not any(fragment.casefold() in text for fragment in expected["phase_contains_any"]):
            raise AssertionError(f"phase {text!r} contains none of {expected['phase_contains_any']!r}")

    if "winner" in expected:
        name = _field(state, ("winner", "winners"))
        if name is None:
            values = list(game.returns(state))
            best = max(values)
            winners = [index for index, value in enumerate(values) if value == best]
            actual = winners[0] if len(winners) == 1 else winners
        else:
            actual = getattr(state, name)
            if name == "winners":
                actual = actual[0] if len(actual) == 1 else actual
        _assert_equal("winner", actual, int(expected["winner"]))

    if expected.get("alive_all"):
        name = _field(state, ("alive", "eliminated"))
        if name is not None:
            values = list(getattr(state, name))
            actual = all(values) if name == "alive" else not any(values)
            _assert_equal("alive_all", actual, True)

    actions = list(game.legal_actions(state))
    names = _named_actions(game, state)
    for item in expected.get("harvest_legal", []):
        player, field = int(item.get("player", 0)), int(item["field"])
        found = any(isinstance(action, tuple) and len(action) >= 3 and any(word in str(action[0]).casefold() for word in ("ernt", "harvest")) and int(action[1]) == player and int(action[2]) == field for action in actions)
        _assert_equal(f"harvest_legal[{player},{field}]", found, bool(item["expected"]))
    for item in expected.get("plant_legal", []):
        field = int(item["field"])
        found = any(isinstance(action, tuple) and len(action) >= 2 and any(word in str(action[0]).casefold() for word in ("anbau", "plant")) and _has_number(action, field) for action in actions)
        _assert_equal(f"plant_legal[{field}]", found, bool(item["expected"]))
    if "legal_plant_types" in expected:
        hands_name = _field(state, ("hands", "hand"))
        if hands_name is None:
            raise AdapterUntestable("state has no hands")
        _, hands = _player_groups(state, (hands_name,))
        player_name = _field(state, PLAYER_FIELDS)
        player = int(getattr(state, player_name)) if player_name else 0
        front = _cards(hands[player])[:1]
        for semantic in expected["legal_plant_types"]:
            if _card(module, game, semantic) not in front or not any(any(word in str(action[0]).casefold() for word in ("anbau", "plant")) for action in actions if isinstance(action, tuple)):
                raise AssertionError(f"no legal planting action for {semantic!r}")
    for item in expected.get("trade_allowed", []):
        a, b = int(item["a"]), int(item["b"])
        found = any(str(b) in name and any(word in name for word in ("handel", "trade", "gift", "schenk")) for name in names)
        if a != int(getattr(state, _field(state, PLAYER_FIELDS) or "active_player", a)):
            found = False
        _assert_equal(f"trade_allowed[{a},{b}]", found, bool(item["expected"]))

    if "pending_received" in expected:
        name = _field(state, ("pending_received", "traded", "received", "sideways"))
        if name is None:
            raise AdapterUntestable("state has no pending-received container")
        values = getattr(state, name)
        for player, wanted in expected["pending_received"].items():
            actual = values[int(player)] if not isinstance(values, Mapping) else values.get(int(player), values.get(str(player), []))
            _assert_equal(f"pending_received[{player}]", _cards(actual), [_card(module, game, card) for card in wanted])

    if "private_hand_visibility" in expected:
        spec = expected["private_hand_visibility"]
        rendered = str(game.render(state))
        for semantic in spec["own"]:
            card = str(_card(module, game, semantic))
            if card not in rendered:
                raise AssertionError(f"owner-visible card {card!r} missing from render")
        for player, hidden in spec["hidden"].items():
            for semantic in hidden:
                card = str(_card(module, game, semantic))
                if card in rendered:
                    raise AssertionError(f"opponent card {card!r} leaked in render")

    if "five_player_setup" in expected:
        spec = expected["five_player_setup"]
        try:
            probe_game = module.Game(players=int(spec["players"]), seed=1)
        except TypeError:
            try:
                probe_game = module.Game(int(spec["players"]))
            except TypeError as error:
                raise AssertionError("five-player setup is unsupported") from error
        probe = probe_game.initial_state()
        if hasattr(probe, "hands") and hasattr(probe, "fields"):
            hands, fields = probe.hands, probe.fields
        elif isinstance(getattr(probe, "players", None), Sequence):
            hands = [player.hand for player in probe.players]
            fields = [player.fields for player in probe.players]
        else:
            raise AdapterUntestable("five-player state has no canonical hands/fields")
        _assert_equal("five_player.players", len(hands), int(spec["players"]))
        for player, player_fields in enumerate(fields):
            _assert_equal(f"five_player.fields[{player}]", len(player_fields), int(spec["fields_each"]))
        for player, hand in enumerate(hands):
            _assert_equal(f"five_player.hand[{player}]", len(_cards(hand)), int(spec["hand_size"]))
        _assert_equal("five_player.total_cards", len(_all_cards(probe)), int(spec["total_cards"]))

    if "no_hand_reorder_action" in expected:
        player = int(expected["no_hand_reorder_action"].get("player", 0))
        before = _cards(state.hands[player])
        for action in game.legal_actions(state):
            after_state = game.apply_action(state, action)
            after = _cards(after_state.hands[player])
            if len(after) == len(before) and Counter(after) == Counter(before) and after != before:
                raise AssertionError(f"legal action {game.action_to_name(action)!r} reorders hand {before!r} to {after!r}")

    if "harvest_curve" in expected:
        spec = expected["harvest_curve"]
        for case in spec["cases"]:
            probe = setup(module, game, {
                "fields": {"0": [[spec["bean"]] * int(case["size"]), []]},
                "coins": {"0": 0},
                "discard": [],
                "phase": "trade",
                "active_player": 0,
            })
            action = next((action for action in game.legal_actions(probe)
                           if isinstance(action, tuple) and len(action) >= 3
                           and any(word in str(action[0]).casefold() for word in ("ernt", "harvest"))
                           and int(action[1]) == 0 and int(action[2]) == 0), None)
            if action is None:
                raise AssertionError(f"no legal harvest for {spec['bean']} size {case['size']}")
            after = game.apply_action(probe, action)
            coin_name = _field(after, COIN_FIELDS)
            if coin_name is None:
                raise AdapterUntestable("state has no coin/score field")
            coins = getattr(after, coin_name)
            actual = coins[0] if not isinstance(coins, Mapping) else coins.get(0, coins.get("0"))
            _assert_equal(f"harvest_curve[{spec['bean']}][{case['size']}]", int(actual), int(case["coins"]))
