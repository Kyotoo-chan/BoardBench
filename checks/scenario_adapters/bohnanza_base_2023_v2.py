"""Bohnanza Base 2023 V2 adapter using only canonical data and the public Game API."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from typing import Any

STATE_SCHEMA = "boardbench/bohnanza-base-2023/state/2"
ACTION_SCHEMA = "boardbench/bohnanza-base-2023/action/2"
OBSERVATION_SCHEMA = "boardbench/bohnanza-base-2023/observation/2"
BEANS = {
    "blau": "blaue_bohne",
    "feuer": "feuerbohne",
    "sau": "saubohne",
    "brech": "brechbohne",
    "soja": "sojabohne",
    "augen": "augenbohne",
    "rot": "rote_bohne",
    "garten": "gartenbohne",
}


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
        if not isinstance(data.get("type"), str) or not isinstance(data.get("args"), dict):
            raise AdapterUntestable("invalid canonical action data")
        result.append((action, data))
    return result


def _bean(value: str) -> str:
    try:
        return BEANS[value]
    except KeyError as error:
        raise AdapterUntestable(f"unknown fixture bean {value!r}") from error


def _all_cards(data: dict[str, Any]) -> list[str]:
    cards = []
    for player in data["players"]:
        cards.extend(player["hand"])
        for field in player["fields"]:
            cards.extend(field)
    zones = data["zones"]
    for name in ("deck", "discard", "revealed", "reserve"):
        cards.extend(zones[name])
    for group in zones["pending_received"]:
        cards.extend(group)
    return cards


def _card_total(data: dict[str, Any]) -> int:
    """Coin counts are flipped bean cards whose identities are no longer represented."""
    return len(_all_cards(data)) + sum(int(player["coins"]) for player in data["players"])


def _matches(data: dict[str, Any], selector: dict[str, Any]) -> bool:
    if "actor" in selector and data["actor"] != selector["actor"]:
        return False
    if "type" in selector and data["type"] != selector["type"]:
        return False
    if "type_any" in selector and data["type"] not in selector["type_any"]:
        return False
    return all(data["args"].get(key) == value for key, value in selector.get("args", {}).items())


def make_game(module: Any, fixture: dict[str, Any]) -> Any:
    count = int(fixture.get("player_count", 3))
    for key in ("hands", "fields", "pending_received", "coins"):
        if fixture.get(key):
            count = max(count, max(int(player) for player in fixture[key]) + 1)
    if fixture.get("pending_gift"):
        count = max(count, int(fixture["pending_gift"]["from"]) + 1, int(fixture["pending_gift"]["to"]) + 1)
    return module.Game(num_players=count, seed=int(fixture.get("seed", 1)))


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
        player["fields"] = [[] for _ in player["fields"]]
        player["coins"] = 0
    zones = data["zones"]
    for name in ("deck", "discard", "revealed", "reserve"):
        zones[name] = []
    zones["pending_received"] = [[] for _ in data["players"]]
    data["depletions"] = 0
    data["pending"] = None
    data["terminal"] = False
    data["chance"]["counter"] = 0
    return inventory


def setup(module: Any, game: Any, fixture: dict[str, Any]) -> Any:
    fixture_game = make_game(module, fixture)
    payload = deepcopy(fixture_game.state_to_data(fixture_game.initial_state()))
    data = _envelope(payload, STATE_SCHEMA)
    inventory = _blank(data)

    for player, cards in fixture.get("hands", {}).items():
        data["players"][int(player)]["hand"] = [_bean(card) for card in cards]
    for player, fields in fixture.get("fields", {}).items():
        converted = [[_bean(card) for card in field] for field in fields]
        data["players"][int(player)]["fields"] = converted
    for fixture_name, zone_name in (("discard", "discard"), ("revealed", "revealed")):
        if fixture_name in fixture:
            data["zones"][zone_name] = [_bean(card) for card in fixture[fixture_name]]
    if "deck" in fixture:
        # Fixtures are written next-draw first; canonical state is bottom-to-top.
        data["zones"]["deck"] = list(reversed([_bean(card) for card in fixture["deck"]]))
    for player, cards in fixture.get("pending_received", {}).items():
        data["zones"]["pending_received"][int(player)] = [_bean(card) for card in cards]
    for player, count in fixture.get("coins", {}).items():
        data["players"][int(player)]["coins"] = int(count)


    if "active_player" in fixture:
        data["active_player"] = int(fixture["active_player"])
        data["current_player"] = int(fixture["active_player"])
    if "current_player" in fixture:
        data["current_player"] = int(fixture["current_player"])
    if "start_player" in fixture:
        data["start_player"] = int(fixture["start_player"])
    if "phase" in fixture:
        data["phase"] = str(fixture["phase"])
    if "depletions" in fixture:
        data["depletions"] = int(fixture["depletions"])
    if "terminal" in fixture:
        data["terminal"] = bool(fixture["terminal"])
        if data["terminal"]:
            data["phase"] = "terminal"
    data["winner"] = int(fixture["winner"]) if fixture.get("winner") is not None else None
    pending_spec = fixture.get("pending_gift") or fixture.get("pending_trade")
    if pending_spec:
        sender, recipient = int(pending_spec["from"]), int(pending_spec["to"])
        offered = [_bean(card) for card in pending_spec.get("cards", pending_spec.get("offered", []))]
        requested = [_bean(card) for card in pending_spec.get("requested", [])]
        data["phase"] = "trade_response"
        data["pending"] = {
            "type": "gift" if fixture.get("pending_gift") else "trade",
            "actor": sender,
            "partner": recipient,
            "offered": [{"owner": sender, "zone": "hand", "index": index, "bean": card} for index, card in enumerate(offered)],
            "requested": [{"owner": recipient, "zone": "hand", "index": index, "bean": card} for index, card in enumerate(requested)],
            "awaiting_player": recipient,
        }
        data["current_player"] = recipient

    used = Counter(_all_cards(data))
    remaining = inventory - used
    if used - inventory:
        raise AdapterUntestable("fixture exceeds canonical component inventory")
    coin_cards = sum(int(player["coins"]) for player in data["players"])
    if coin_cards > remaining.total():
        raise AdapterUntestable("fixture coins exceed canonical component inventory")
    for bean in sorted(remaining):
        taken = min(coin_cards, remaining[bean])
        remaining[bean] -= taken
        coin_cards -= taken
        if not coin_cards:
            break
    data["zones"]["reserve"] = sorted(remaining.elements())
    try:
        state = fixture_game.state_from_data(payload)
    except (TypeError, ValueError, AssertionError) as error:
        raise AdapterUntestable(f"state_from_data rejected canonical fixture: {error}") from error
    if fixture_game.state_to_data(state) != payload:
        raise AdapterUntestable("canonical fixture does not round-trip")
    return state


def _assert_equal(label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def check(module: Any, game: Any, state: Any, expected: dict[str, Any]) -> None:
    data = _state(game, state)
    cards = _all_cards(data)
    for key in ("current_player", "active_player", "start_player", "phase", "winner", "depletions", "turn_number"):
        if key in expected:
            _assert_equal(key, data[key], expected[key])
    if "terminal" in expected:
        _assert_equal("terminal", bool(data["terminal"]), bool(expected["terminal"]))
    if "deck" in expected:
        _assert_equal("deck", list(reversed(data["zones"]["deck"])), [_bean(card) for card in expected["deck"]])
    total_before = _card_total(data)
    if "total_cards" in expected:
        _assert_equal("total_cards", total_before, int(expected["total_cards"]))
    for semantic, wanted in expected.get("card_counts", {}).items():
        _assert_equal(f"card_counts[{semantic}]", cards.count(_bean(semantic)), int(wanted))

    if expected.get("valid_base_setup"):
        count = len(data["players"])
        if count not in (3, 4, 5):
            raise AssertionError(f"default player count must be 3, 4, or 5, got {count}")
        wanted_fields = 3 if count == 3 else 2
        for entry in data["players"]:
            _assert_equal(f"setup.fields[{entry['id']}]", len(entry["fields"]), wanted_fields)
    for player, wanted in expected.get("hand_size", {}).items():
        _assert_equal(f"hand_size[{player}]", len(data["players"][int(player)]["hand"]), int(wanted))
    if "hand_size_all" in expected:
        for player in data["players"]:
            _assert_equal(f"hand_size[{player['id']}]", len(player["hand"]), int(expected["hand_size_all"]))
    for player, wanted in expected.get("hand_order", {}).items():
        _assert_equal(f"hand_order[{player}]", data["players"][int(player)]["hand"], [_bean(card) for card in wanted])
    for player, wanted in expected.get("hand_prefix", {}).items():
        prefix = [_bean(card) for card in wanted]
        _assert_equal(f"hand_prefix[{player}]", data["players"][int(player)]["hand"][:len(prefix)], prefix)

    player = int(expected.get("player", 0))
    if "field_count" in expected:
        _assert_equal("field_count", len(data["players"][player]["fields"]), int(expected["field_count"]))
    for owner, wanted in expected.get("field_sizes", {}).items():
        _assert_equal(f"field_sizes[{owner}]", [len(field) for field in data["players"][int(owner)]["fields"]], [int(value) for value in wanted])
    for owner, wanted in expected.get("field_counts", {}).items():
        field_cards = [card for field in data["players"][int(owner)]["fields"] for card in field]
        for semantic, count in wanted.items():
            _assert_equal(f"field_counts[{owner}][{semantic}]", field_cards.count(_bean(semantic)), int(count))

    for owner, wanted in expected.get("coins", {}).items():
        _assert_equal(f"coins[{owner}]", data["players"][int(owner)]["coins"], int(wanted))
    if "discard_size" in expected:
        _assert_equal("discard_size", len(data["zones"]["discard"]), int(expected["discard_size"]))
    for semantic, wanted in expected.get("discard_count", {}).items():
        _assert_equal(f"discard_count[{semantic}]", data["zones"]["discard"].count(_bean(semantic)), int(wanted))
    if "revealed_size" in expected:
        _assert_equal("revealed_size", len(data["zones"]["revealed"]), int(expected["revealed_size"]))
    if "revealed" in expected:
        _assert_equal("revealed", data["zones"]["revealed"], [_bean(card) for card in expected["revealed"]])
    if "revealed_prefix" in expected:
        prefix = [_bean(card) for card in expected["revealed_prefix"]]
        _assert_equal("revealed_prefix", data["zones"]["revealed"][:len(prefix)], prefix)
    if "deck_size" in expected:
        _assert_equal("deck_size", len(data["zones"]["deck"]), int(expected["deck_size"]))
    if "depletions" in expected:
        _assert_equal("depletions", data["depletions"], int(expected["depletions"]))
    if "phase_contains_any" in expected and not any(value in data["phase"] for value in expected["phase_contains_any"]):
        raise AssertionError(f"phase {data['phase']!r} contains none of {expected['phase_contains_any']!r}")
    if "winner" in expected:
        values = list(game.returns(state))
        best = max(values)
        winners = [index for index, value in enumerate(values) if value == best]
        _assert_equal("winner", winners[0] if len(winners) == 1 else winners, int(expected["winner"]))
    actions = [action for _, action in _actions(game, state)]
    if "legal_action_type_any" in expected and not any(action["type"] in expected["legal_action_type_any"] for action in actions):
        raise AssertionError(f"no canonical legal action type in {expected['legal_action_type_any']!r}")
    if "legal_action_type_not" in expected:
        forbidden = set(expected["legal_action_type_not"])
        if any(action["type"] in forbidden for action in actions):
            raise AssertionError(f"forbidden canonical legal action type in {sorted(forbidden)!r}")
    for item in expected.get("harvest_legal", []):
        selector = {"type": "harvest", "args": {"player": int(item.get("player", 0)), "field": int(item["field"])}}
        _assert_equal(f"harvest_legal[{selector['args']['player']},{selector['args']['field']}]", any(_matches(action, selector) for action in actions), bool(item["expected"]))
    for item in expected.get("plant_legal", []):
        selector = {"type": "plant", "args": {"field": int(item["field"])}}
        _assert_equal(f"plant_legal[{item['field']}]", any(_matches(action, selector) for action in actions), bool(item["expected"]))
    if "legal_plant_types" in expected:
        front = data["players"][data["current_player"]]["hand"][:1]
        for semantic in expected["legal_plant_types"]:
            bean = _bean(semantic)
            if bean not in front or not any(action["type"] == "plant" and action["args"].get("bean") == bean for action in actions):
                raise AssertionError(f"no legal planting action for {semantic!r}")
    for item in expected.get("trade_allowed", []):
        actor, partner = int(item["a"]), int(item["b"])
        found = any(action["type"].startswith(("trade_", "gift_")) and action["actor"] == actor and action["args"].get("partner") == partner for action in actions)
        _assert_equal(f"trade_allowed[{actor},{partner}]", found, bool(item["expected"]))
    for item in expected.get("legal_action_selectors", []):
        selector = item["selector"]
        _assert_equal(f"legal_action[{selector}]", any(_matches(action, selector) for action in actions), bool(item["expected"]))

    for item in expected.get("trade_bundle_legal", []):
        wanted_offered = Counter((int(ref["owner"]), ref["zone"], int(ref["index"]), _bean(ref["bean"])) for ref in item["offered"])
        wanted_requested = Counter((int(ref["owner"]), ref["zone"], int(ref["index"]), _bean(ref["bean"])) for ref in item["requested"])
        found = False
        for action in actions:
            args = action["args"]
            if action["type"] != "trade_propose" or action["actor"] != int(item["actor"]) or args.get("partner") != int(item["partner"]):
                continue
            offered = Counter((int(ref["owner"]), ref["zone"], int(ref["index"]), ref["bean"]) for ref in args.get("offered", []))
            requested = Counter((int(ref["owner"]), ref["zone"], int(ref["index"]), ref["bean"]) for ref in args.get("requested", []))
            if offered == wanted_offered and requested == wanted_requested and bool(args.get("gift")) is bool(item.get("gift", False)):
                found = True
                break
        _assert_equal("trade_bundle_legal", found, bool(item.get("expected", True)))

    for item in expected.get("plant_revealed_choices", []):
        actor = int(item["actor"]);wanted = {_bean(bean) for bean in item["beans"]}
        found = {action["args"].get("bean") for _, action in _actions(game, state) if action["type"] == "plant" and action["actor"] == actor and action["args"].get("source") == "revealed"}
        if not wanted <= found:
            raise AssertionError(f"player {actor} revealed-card choices: expected {sorted(wanted)!r}, got {sorted(found)!r}")

    for item in expected.get("plant_received_choices", []):
        actor = int(item["actor"])
        wanted = {_bean(bean) for bean in item["beans"]}
        found = {action["args"].get("bean") for action in actions if action["type"] == "plant" and action["actor"] == actor and action["args"].get("source") == "received"}
        if not wanted <= found:
            raise AssertionError(f"player {actor} received-card choices: expected {sorted(wanted)!r}, got {sorted(found)!r}")

    for player, wanted in expected.get("pending_received", {}).items():
        _assert_equal(f"pending_received[{player}]", Counter(data["zones"]["pending_received"][int(player)]), Counter(_bean(card) for card in wanted))

    if "private_hand_visibility" in expected:
        spec = expected["private_hand_visibility"]
        observation = _envelope(game.observation_to_data(state, int(spec.get("player", 0))), OBSERVATION_SCHEMA)
        _assert_equal("own_hand", observation["own_hand"], [_bean(card) for card in spec["own"]])
        opponents = {entry["id"]: entry for entry in observation["opponents"]}
        for owner, hand in spec.get("opponents", {}).items():
            entry = opponents[int(owner)]
            _assert_equal(f"opponents[{owner}].keys", set(entry), {"id", "hand_size", "front_card"})
            _assert_equal(f"opponents[{owner}].hand_size", entry["hand_size"], len(hand))
            _assert_equal(f"opponents[{owner}].front_card", entry["front_card"], _bean(hand[0]) if hand else None)
        _assert_equal("observation keys", set(observation), set(spec["allowed_keys"]))

    for probe_spec in expected.get("replay_probes", []):
        probe_fixture = probe_spec["fixture"]
        probe_game = make_game(module, probe_fixture)
        probe_state = setup(module, probe_game, probe_fixture)
        if probe_spec.get("initial"):
            check(module, probe_game, probe_state, probe_spec["initial"])
        for probe_step in probe_spec.get("steps", []):
            selector = probe_step["action"]
            action = resolve_action(module, probe_game, probe_state, list(probe_game.legal_actions(probe_state)), selector)
            probe_state = probe_game.apply_action(probe_state, action)
            if probe_step.get("expect"):
                check(module, probe_game, probe_state, probe_step["expect"])

    if "setup_probe" in expected:
        spec = expected["setup_probe"]
        count, seed = int(spec["players"]), int(spec.get("seed", 20260727))
        probe_game = module.Game(num_players=count, seed=seed)
        probe_state = probe_game.initial_state()
        probe = _state(probe_game, probe_state)
        _assert_equal("setup.players", len(probe["players"]), count)
        again = module.Game(num_players=count, seed=seed)
        _assert_equal("setup.start_player", probe["start_player"], _state(again, again.initial_state())["start_player"])
        for entry in probe["players"]:
            _assert_equal(f"setup.fields[{entry['id']}]", len(entry["fields"]), int(spec["fields_each"]))
            _assert_equal(f"setup.hand[{entry['id']}]", len(entry["hand"]), int(spec["hand_size"]))
        _assert_equal("setup.deck_size", len(probe["zones"]["deck"]), int(spec["deck_size"]))
        _assert_equal("setup.total_cards", _card_total(probe), int(spec["total_cards"]))
        if not list(probe_game.legal_actions(probe_state)):
            raise AssertionError("setup has no initial legal action")

    if "seeded_start_probe" in expected:
        spec = expected["seeded_start_probe"]
        starts = []
        for seed in spec["seeds"]:
            first_game = module.Game(num_players=int(spec["players"]), seed=int(seed))
            second_game = module.Game(num_players=int(spec["players"]), seed=int(seed))
            first = _state(first_game, first_game.initial_state())["start_player"]
            second = _state(second_game, second_game.initial_state())["start_player"]
            _assert_equal(f"same-seed start[{seed}]", first, second)
            starts.append(first)
        if spec.get("require_distinct") and len(set(starts)) < 2:
            raise AssertionError("different seeds never influence the selected start player")

    if "reject_player_counts" in expected:
        for count in expected["reject_player_counts"]:
            try:
                module.Game(num_players=int(count), seed=20260727)
            except ValueError:
                continue
            raise AssertionError(f"unsupported player count accepted: {count}")

    if "bounded_play" in expected:
        spec = expected["bounded_play"]
        for count in spec["players"]:
            probe_game = module.Game(num_players=int(count), seed=int(spec["seed"]))
            probe = probe_game.initial_state()
            for _ in range(int(spec["steps"])):
                actions = list(probe_game.legal_actions(probe))
                if probe_game.is_terminal(probe):
                    break
                if not actions:
                    raise AssertionError(f"{count}-player bounded play deadlocked")
                probe = probe_game.apply_action(probe, min(actions, key=probe_game.action_to_name))

    if expected.get("conserve_cards") and _card_total(data) != total_before:
        raise AssertionError("card-plus-coin total changed during check")

    if "harvest_curve" in expected:
        spec = expected["harvest_curve"]
        for case in spec["cases"]:
            probe = setup(module, game, {"fields": {"0": [[spec["bean"]] * int(case["size"]), []]}, "coins": {"0": 0}, "discard": [], "phase": "trade", "active_player": 0})
            selector = {"type": "harvest", "args": {"player": 0, "field": 0}}
            action = resolve_action(module, game, probe, list(game.legal_actions(probe)), selector)
            after = _state(game, game.apply_action(probe, action))
            _assert_equal(f"harvest_curve[{spec['bean']}][{case['size']}]", after["players"][0]["coins"], int(case["coins"]))
