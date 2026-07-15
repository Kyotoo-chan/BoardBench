"""Evaluator-only deterministic state adapter for generated Exploding Kittens modules."""

from __future__ import annotations

from collections.abc import MutableMapping
from dataclasses import is_dataclass, replace
from typing import Any

CARD_CONSTANTS = {
    "kitten": ("EXPLODING_KITTEN", "EXPLODING", "GEFAHR"),
    "defuse": ("DEFUSE", "SCHUTZ"),
    "attack": ("ATTACK",),
    "skip": ("SKIP",),
    "future": ("SEE_FUTURE", "SEE", "FUTURE"),
    "shuffle": ("SHUFFLE",),
    "favor": ("FAVOR",),
    "nope": ("NOPE",),
}
CARD_ALIASES = {
    "kitten": ("Exploding Kitten", "Gefahrenkarte", "danger"),
    "defuse": ("Entschärfung", "Schutzkarte", "protection"),
    "attack": ("Angriff", "Doppelzug", "double_turn"),
    "skip": ("Hops!", "Überspringen", "skip"),
    "future": ("Blick in die Zukunft", "Vorschau", "preview"),
    "shuffle": ("Mischen", "Neuordnen", "reorder"),
    "favor": ("Wunsch", "Auswahl", "choice"),
    "nope": ("Nö!", "Widerspruch", "contradiction"),
}
PLAYER_FIELDS = ("active_player", "turn_player", "player")
DEBT_FIELDS = ("turns_left", "turns_remaining", "turn_debt", "turns_due")


def _catalog(module: Any) -> list[Any]:
    cards: list[Any] = []
    for name in ("CARDS", "CARD_TYPES", "CARD_TITLES", "PLAYABLE", "CAT_CARDS", "CAT_TYPES", "CAT_TITLES", "CATS", "SYMBOLS"):
        value = getattr(module, name, ())
        if isinstance(value, MutableMapping):
            cards.extend(value)
        elif isinstance(value, (list, tuple, set)):
            cards.extend(value)
    counts = getattr(module, "CARD_COUNTS", {})
    if isinstance(counts, MutableMapping):
        cards.extend(counts)
    return list(dict.fromkeys(cards))


def _card(module: Any, semantic_name: str) -> Any:
    catalog = _catalog(module)
    if semantic_name == "cat":
        for constant in ("CAT_CARDS", "CAT_TYPES", "CATS", "SYMBOLS"):
            cards = getattr(module, constant, ())
            if cards:
                return cards[0]
        for card in catalog:
            folded = str(card).casefold()
            if any(fragment in folded for fragment in ("katze", "cat", "symbol", "zombie", "auge")):
                return card
    for constant in CARD_CONSTANTS.get(semantic_name, (semantic_name,)):
        if hasattr(module, constant):
            return getattr(module, constant)
    aliases = CARD_ALIASES.get(semantic_name, ())
    for alias in aliases:
        for card in catalog:
            if str(card).casefold() == alias.casefold():
                return card
    raise NotImplementedError(f"implementation has no card constant for {semantic_name!r}")


def _cards_like(container: Any, cards: list[Any]) -> Any:
    if isinstance(container, MutableMapping):
        result = container.copy()
        for card in result:
            result[card] = 0
        for card in cards:
            result[card] = result.get(card, 0) + 1
        return result
    if isinstance(container, tuple):
        return tuple(cards)
    if isinstance(container, list):
        return list(cards)
    raise NotImplementedError(f"unsupported card container {type(container).__name__}")


def _cards(container: Any) -> list[Any]:
    if isinstance(container, MutableMapping):
        return [card for card, count in container.items() for _ in range(int(count))]
    return list(container)


def _get_first(state: Any, fields: tuple[str, ...]) -> Any:
    for field in fields:
        if hasattr(state, field):
            return getattr(state, field)
    raise NotImplementedError(f"state has none of {fields!r}")


def setup(module: Any, game: Any, fixture: dict[str, Any]) -> Any:
    state = game.initial_state()
    hands = getattr(state, "hands", None)
    if not isinstance(hands, (list, tuple)):
        raise NotImplementedError("state.hands is not a player sequence")

    requested_hands = fixture.get("hands", {})
    new_hands = []
    for player, hand in enumerate(hands):
        semantic_cards = requested_hands.get(str(player), requested_hands.get(player, []))
        new_hands.append(_cards_like(hand, [_card(module, name) for name in semantic_cards]))

    changes: dict[str, Any] = {
        "hands": tuple(new_hands) if isinstance(hands, tuple) else new_hands,
        "deck": _cards_like(state.deck, [_card(module, name) for name in fixture.get("deck", ["shuffle"])]),
        "discard": _cards_like(state.discard, [_card(module, name) for name in fixture.get("discard", [])]),
    }
    if hasattr(state, "alive"):
        alive = list(fixture.get("alive", [True] * len(hands)))
        changes["alive"] = tuple(alive) if isinstance(state.alive, tuple) else alive
    for fields, value in (
        (PLAYER_FIELDS, int(fixture.get("active_player", 0))),
        (DEBT_FIELDS, int(fixture.get("turns_owed", 1))),
    ):
        field = next((name for name in fields if hasattr(state, name)), None)
        if field is None:
            raise NotImplementedError(f"state has none of {fields!r}")
        changes[field] = value
    if hasattr(state, "winner"):
        changes["winner"] = None
    if hasattr(state, "pending"):
        changes["pending"] = () if isinstance(state.pending, tuple) else None

    if is_dataclass(state):
        return replace(state, **changes)
    for field, value in changes.items():
        setattr(state, field, value)
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
