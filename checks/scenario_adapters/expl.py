"""Evaluator-only deterministic state adapter for generated Exploding Kittens modules."""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any

CARD_CONSTANTS = {
    "kitten": ("EXPLODING_KITTEN", "EXPLODING"),
    "defuse": ("DEFUSE",),
    "attack": ("ATTACK",),
    "skip": ("SKIP",),
    "future": ("SEE_FUTURE", "SEE", "FUTURE"),
    "shuffle": ("SHUFFLE",),
    "favor": ("FAVOR",),
    "nope": ("NOPE",),
}
PLAYER_FIELDS = ("active_player", "turn_player", "player")
DEBT_FIELDS = ("turns_left", "turns_remaining", "turn_debt")


def _card(module: Any, semantic_name: str) -> Any:
    if semantic_name == "cat":
        for constant in ("CAT_CARDS", "CATS", "SYMBOLS"):
            cards = getattr(module, constant, ())
            if cards:
                return cards[0]
    for constant in CARD_CONSTANTS.get(semantic_name, (semantic_name,)):
        if hasattr(module, constant):
            return getattr(module, constant)
    raise NotImplementedError(f"implementation has no card constant for {semantic_name!r}")


def _replace_cards(container: Any, cards: list[Any]) -> None:
    if isinstance(container, MutableMapping):
        for card in container:
            container[card] = 0
        for card in cards:
            container[card] = container.get(card, 0) + 1
    else:
        container[:] = cards


def _cards(container: Any) -> list[Any]:
    if isinstance(container, MutableMapping):
        return [card for card, count in container.items() for _ in range(int(count))]
    return list(container)


def _set_first(state: Any, fields: tuple[str, ...], value: Any) -> None:
    for field in fields:
        if hasattr(state, field):
            setattr(state, field, value)
            return
    raise NotImplementedError(f"state has none of {fields!r}")


def _get_first(state: Any, fields: tuple[str, ...]) -> Any:
    for field in fields:
        if hasattr(state, field):
            return getattr(state, field)
    raise NotImplementedError(f"state has none of {fields!r}")


def setup(module: Any, game: Any, fixture: dict[str, Any]) -> Any:
    state = game.initial_state()
    hands = getattr(state, "hands", None)
    if not isinstance(hands, list):
        raise NotImplementedError("state.hands is not a player list")

    requested_hands = fixture.get("hands", {})
    for player, hand in enumerate(hands):
        semantic_cards = requested_hands.get(str(player), requested_hands.get(player, []))
        _replace_cards(hand, [_card(module, name) for name in semantic_cards])

    _replace_cards(state.deck, [_card(module, name) for name in fixture.get("deck", ["shuffle"])])
    _replace_cards(state.discard, [_card(module, name) for name in fixture.get("discard", [])])

    if hasattr(state, "alive"):
        state.alive[:] = list(fixture.get("alive", [True] * len(hands)))
    _set_first(state, PLAYER_FIELDS, int(fixture.get("active_player", 0)))
    _set_first(state, DEBT_FIELDS, int(fixture.get("turns_owed", 1)))

    if hasattr(state, "winner"):
        state.winner = None
    if hasattr(state, "pending"):
        state.pending = None
    return state


def check(module: Any, game: Any, state: Any, expected: dict[str, Any]) -> None:
    if "turns_owed" in expected:
        actual = int(_get_first(state, DEBT_FIELDS))
        wanted = int(expected["turns_owed"])
        if actual != wanted:
            raise AssertionError(f"turns_owed: expected {wanted}, got {actual}")
    if "hand_size" in expected:
        for player, wanted in expected["hand_size"].items():
            actual = len(_cards(state.hands[int(player)]))
            if actual != int(wanted):
                raise AssertionError(f"hand_size[{player}]: expected {wanted}, got {actual}")
    if "hand_count" in expected:
        for player, card_counts in expected["hand_count"].items():
            cards = _cards(state.hands[int(player)])
            for semantic_name, wanted in card_counts.items():
                actual = cards.count(_card(module, semantic_name))
                if actual != int(wanted):
                    raise AssertionError(
                        f"hand_count[{player}][{semantic_name}]: expected {wanted}, got {actual}"
                    )
    if "discard_size" in expected:
        actual = len(_cards(state.discard))
        wanted = int(expected["discard_size"])
        if actual != wanted:
            raise AssertionError(f"discard_size: expected {wanted}, got {actual}")
    if "discard_count" in expected:
        cards = _cards(state.discard)
        for semantic_name, wanted in expected["discard_count"].items():
            actual = cards.count(_card(module, semantic_name))
            if actual != int(wanted):
                raise AssertionError(f"discard_count[{semantic_name}]: expected {wanted}, got {actual}")
    if "alive" in expected:
        actual = list(state.alive)
        wanted = list(expected["alive"])
        if actual != wanted:
            raise AssertionError(f"alive: expected {wanted}, got {actual}")
