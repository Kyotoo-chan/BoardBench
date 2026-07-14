"""Standard-library implementation derived solely from the supplied rulebook."""

from __future__ import annotations

import copy
import itertools
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


EXPLODING = "exploding_kitten"
DEFUSE = "defuse"
ATTACK = "attack"
SKIP = "skip"
FAVOR = "favor"
SHUFFLE = "shuffle"
SEE_FUTURE = "see_future"
NOPE = "nope"

CAT_CARDS = (
    "cat_zombie",
    "cat_eye_eater",
    "cat_unknown_1",
    "cat_unknown_2",
    "cat_unknown_3",
)

NORMAL_PLAY_CARDS = (ATTACK, SKIP, SHUFFLE, SEE_FUTURE) + CAT_CARDS

ALL_CARD_TYPES = (
    EXPLODING,
    DEFUSE,
    ATTACK,
    SKIP,
    FAVOR,
    SHUFFLE,
    SEE_FUTURE,
    NOPE,
) + CAT_CARDS

CARD_COUNTS = {
    EXPLODING: 4,
    DEFUSE: 6,
    ATTACK: 4,
    SKIP: 4,
    FAVOR: 4,
    SHUFFLE: 4,
    SEE_FUTURE: 5,
    NOPE: 5,
    **{card: 4 for card in CAT_CARDS},
}


@dataclass
class GameState:
    num_players: int
    hands: List[List[str]]
    deck: List[str]
    discard: List[str]
    alive: List[bool]
    turn_player: int = 0
    turns_left: int = 1
    phase: str = "main"

    pending: Optional[Dict[str, object]] = None
    response_player: Optional[int] = None
    response_passes: int = 0

    choice_player: Optional[int] = None
    choice_recipient: Optional[int] = None

    drawn_exploding_player: Optional[int] = None
    private_views: Dict[int, Tuple[str, ...]] = field(default_factory=dict)
    rng: random.Random = field(default_factory=random.Random, repr=False)

    def current_player(self) -> int:
        return _current_player(self)

    def legal_actions(self) -> List[str]:
        return _legal_actions(self)

    def apply_action(self, action: str) -> "GameState":
        return _apply_action(self, action)

    def is_terminal(self) -> bool:
        return _is_terminal(self)

    def returns(self) -> List[int]:
        return _returns(self)

    def render(self) -> str:
        return _render(self)

    @staticmethod
    def action_to_name(action: str) -> str:
        if not isinstance(action, str):
            raise TypeError("Actions must be strings")
        return action

    @staticmethod
    def name_to_action(name: str) -> str:
        if not isinstance(name, str):
            raise TypeError("Action names must be strings")
        return name


class Game:
    def __init__(self, num_players: int = 2, seed: Optional[int] = 0):
        if not 2 <= num_players <= 5:
            raise ValueError("num_players must be between 2 and 5")
        self.num_players = num_players
        self.seed = seed

    def initial_state(self) -> GameState:
        rng = random.Random(self.seed)

        ordinary_cards: List[str] = []
        for card, count in CARD_COUNTS.items():
            if card not in (EXPLODING, DEFUSE):
                ordinary_cards.extend([card] * count)
        rng.shuffle(ordinary_cards)

        hands = [[] for _ in range(self.num_players)]
        for player in range(self.num_players):
            for _ in range(7):
                hands[player].append(ordinary_cards.pop())
            hands[player].append(DEFUSE)

        deck = ordinary_cards

        # The two-player variant uses exactly two additional Defuse cards.
        deck_defuses = 2 if self.num_players == 2 else 6 - self.num_players
        deck.extend([DEFUSE] * deck_defuses)
        deck.extend([EXPLODING] * (self.num_players - 1))
        rng.shuffle(deck)

        return GameState(
            num_players=self.num_players,
            hands=hands,
            deck=deck,
            discard=[],
            alive=[True] * self.num_players,
            rng=rng,
        )

    @staticmethod
    def current_player(state: GameState) -> int:
        return state.current_player()

    @staticmethod
    def legal_actions(state: GameState) -> List[str]:
        return state.legal_actions()

    @staticmethod
    def apply_action(state: GameState, action: str) -> GameState:
        return state.apply_action(action)

    @staticmethod
    def is_terminal(state: GameState) -> bool:
        return state.is_terminal()

    @staticmethod
    def returns(state: GameState) -> List[int]:
        return state.returns()

    @staticmethod
    def render(state: GameState) -> str:
        return state.render()

    @staticmethod
    def action_to_name(action: str) -> str:
        return GameState.action_to_name(action)

    @staticmethod
    def name_to_action(name: str) -> str:
        return GameState.name_to_action(name)


def _alive_players(state: GameState) -> List[int]:
    return [p for p, alive in enumerate(state.alive) if alive]


def _is_terminal(state: GameState) -> bool:
    return len(_alive_players(state)) <= 1


def _current_player(state: GameState) -> int:
    if _is_terminal(state):
        return -1
    if state.phase == "response":
        assert state.response_player is not None
        return state.response_player
    if state.phase in ("give", "take_discard"):
        assert state.choice_player is not None
        return state.choice_player
    if state.phase in ("exploding", "insert"):
        assert state.drawn_exploding_player is not None
        return state.drawn_exploding_player
    return state.turn_player


def _next_alive(state: GameState, player: int) -> int:
    for offset in range(1, state.num_players + 1):
        candidate = (player + offset) % state.num_players
        if state.alive[candidate]:
            return candidate
    return player


def _card_counts(hand: List[str]) -> Dict[str, int]:
    result: Dict[str, int] = {}
    for card in hand:
        result[card] = result.get(card, 0) + 1
    return result


def _opponents(state: GameState, player: int) -> List[int]:
    return [
        other
        for other in range(state.num_players)
        if other != player and state.alive[other]
    ]


def _legal_actions(state: GameState) -> List[str]:
    if _is_terminal(state):
        return []

    if state.phase == "response":
        player = state.response_player
        assert player is not None
        actions = ["react:pass"]
        if NOPE in state.hands[player]:
            actions.append("react:nope")
        return actions

    if state.phase == "give":
        player = state.choice_player
        assert player is not None
        return [f"give:{card}" for card in sorted(set(state.hands[player]))]

    if state.phase == "take_discard":
        return [
            f"take_discard:{card}"
            for card in sorted(set(state.discard))
        ]

    if state.phase == "exploding":
        player = state.drawn_exploding_player
        assert player is not None
        actions = ["accept:explode"]
        if DEFUSE in state.hands[player]:
            actions.insert(0, "use:defuse")
        return actions

    if state.phase == "insert":
        return [
            f"insert_kitten:position:{position}"
            for position in range(len(state.deck) + 1)
        ]

    if state.phase != "main":
        raise RuntimeError(f"Unknown phase: {state.phase}")

    player = state.turn_player
    hand = state.hands[player]
    counts = _card_counts(hand)
    opponents = _opponents(state, player)
    actions: List[str] = []

    if state.deck:
        actions.append("draw")

    for card in NORMAL_PLAY_CARDS:
        if counts.get(card, 0):
            actions.append(f"play:{card}")

    if counts.get(FAVOR, 0):
        for target in opponents:
            actions.append(f"play:favor:target:{target}")

    # Any two matching cards form a pair.
    for card in ALL_CARD_TYPES:
        if counts.get(card, 0) >= 2:
            for target in opponents:
                actions.append(f"combo:pair:{card}:target:{target}")

    # Any three matching cards form a requested-card combination.
    for card in ALL_CARD_TYPES:
        if counts.get(card, 0) >= 3:
            for target in opponents:
                for requested in ALL_CARD_TYPES:
                    actions.append(
                        f"combo:triple:{card}:target:{target}:request:{requested}"
                    )

    # Five cards with five distinct titles form the discard-retrieval combination.
    distinct = sorted(counts)
    for selected in itertools.combinations(distinct, 5):
        actions.append(f"combo:five:{'+'.join(selected)}")

    return actions


def _remove_cards(hand: List[str], card: str, count: int) -> None:
    for _ in range(count):
        hand.remove(card)


def _begin_effect(
    state: GameState,
    actor: int,
    effect: Dict[str, object],
) -> None:
    state.pending = {"actor": actor, "active": True, **effect}
    state.phase = "response"
    state.response_player = _next_alive(state, actor)
    state.response_passes = 0


def _return_to_main(state: GameState, actor: int) -> None:
    state.phase = "main"
    state.turn_player = actor
    state.pending = None
    state.response_player = None
    state.response_passes = 0
    state.choice_player = None
    state.choice_recipient = None


def _end_one_turn(state: GameState, player: int) -> None:
    if state.turns_left > 1:
        state.turns_left -= 1
        state.turn_player = player
    else:
        state.turn_player = _next_alive(state, player)
        state.turns_left = 1

    state.phase = "main"
    state.pending = None
    state.response_player = None
    state.response_passes = 0
    state.choice_player = None
    state.choice_recipient = None
    state.private_views.clear()


def _resolve_pending(state: GameState) -> None:
    assert state.pending is not None
    pending = state.pending
    actor = int(pending["actor"])
    active = bool(pending["active"])
    kind = str(pending["kind"])

    state.pending = None
    state.response_player = None
    state.response_passes = 0

    if not active:
        _return_to_main(state, actor)
        return

    if kind == "noop":
        _return_to_main(state, actor)
        return

    if kind == "see_future":
        state.private_views[actor] = tuple(state.deck[:3])
        _return_to_main(state, actor)
        return

    if kind == "shuffle":
        state.rng.shuffle(state.deck)
        state.private_views.clear()
        _return_to_main(state, actor)
        return

    if kind == "favor":
        target = int(pending["target"])
        if state.hands[target]:
            state.phase = "give"
            state.choice_player = target
            state.choice_recipient = actor
        else:
            _return_to_main(state, actor)
        return

    if kind == "pair":
        target = int(pending["target"])
        if state.hands[target]:
            index = state.rng.randrange(len(state.hands[target]))
            state.hands[actor].append(state.hands[target].pop(index))
        _return_to_main(state, actor)
        return

    if kind == "triple":
        target = int(pending["target"])
        requested = str(pending["requested"])
        if requested in state.hands[target]:
            state.hands[target].remove(requested)
            state.hands[actor].append(requested)
        _return_to_main(state, actor)
        return

    if kind == "five":
        state.phase = "take_discard"
        state.choice_player = actor
        return

    if kind == "skip":
        _end_one_turn(state, actor)
        return

    if kind == "attack":
        next_player = _next_alive(state, actor)
        state.turn_player = next_player
        state.turns_left = 2
        state.phase = "main"
        state.private_views.clear()
        return

    raise RuntimeError(f"Unknown pending effect: {kind}")


def _draw(state: GameState) -> None:
    player = state.turn_player
    card = state.deck.pop(0)
    state.private_views.clear()

    if card == EXPLODING:
        state.drawn_exploding_player = player
        state.phase = "exploding"
    else:
        state.hands[player].append(card)
        _end_one_turn(state, player)


def _eliminate(state: GameState, player: int) -> None:
    state.discard.append(EXPLODING)
    state.discard.extend(state.hands[player])
    state.hands[player].clear()
    state.alive[player] = False
    state.drawn_exploding_player = None
    state.private_views.clear()

    if _is_terminal(state):
        state.phase = "terminal"
        return

    state.turn_player = _next_alive(state, player)
    state.turns_left = 1
    state.phase = "main"


def _apply_action(state: GameState, action: str) -> GameState:
    if action not in _legal_actions(state):
        raise ValueError(f"Illegal action: {action}")

    result = copy.deepcopy(state)

    if result.phase == "response":
        responder = result.response_player
        assert responder is not None
        assert result.pending is not None

        if action == "react:nope":
            result.hands[responder].remove(NOPE)
            result.discard.append(NOPE)
            result.pending["active"] = not bool(result.pending["active"])
            result.response_player = _next_alive(result, responder)
            result.response_passes = 0
        else:
            result.response_passes += 1
            if result.response_passes >= len(_alive_players(result)):
                _resolve_pending(result)
            else:
                result.response_player = _next_alive(result, responder)
        return result

    if result.phase == "give":
        giver = result.choice_player
        recipient = result.choice_recipient
        assert giver is not None and recipient is not None
        card = action.removeprefix("give:")
        result.hands[giver].remove(card)
        result.hands[recipient].append(card)
        _return_to_main(result, recipient)
        return result

    if result.phase == "take_discard":
        player = result.choice_player
        assert player is not None
        card = action.removeprefix("take_discard:")
        result.discard.remove(card)
        result.hands[player].append(card)
        _return_to_main(result, player)
        return result

    if result.phase == "exploding":
        player = result.drawn_exploding_player
        assert player is not None

        if action == "accept:explode":
            _eliminate(result, player)
        else:
            result.hands[player].remove(DEFUSE)
            result.discard.append(DEFUSE)
            result.phase = "insert"
        return result

    if result.phase == "insert":
        player = result.drawn_exploding_player
        assert player is not None
        position = int(action.rsplit(":", 1)[1])
        result.deck.insert(position, EXPLODING)
        result.drawn_exploding_player = None
        _end_one_turn(result, player)
        return result

    player = result.turn_player

    if action == "draw":
        _draw(result)
        return result

    if action.startswith("play:favor:target:"):
        target = int(action.rsplit(":", 1)[1])
        result.hands[player].remove(FAVOR)
        result.discard.append(FAVOR)
        _begin_effect(
            result,
            player,
            {"kind": "favor", "target": target},
        )
        return result

    if action.startswith("play:"):
        card = action.removeprefix("play:")
        result.hands[player].remove(card)
        result.discard.append(card)

        if card == ATTACK:
            kind = "attack"
        elif card == SKIP:
            kind = "skip"
        elif card == SHUFFLE:
            kind = "shuffle"
        elif card == SEE_FUTURE:
            kind = "see_future"
        elif card in CAT_CARDS:
            kind = "noop"
        else:
            raise RuntimeError(f"Unsupported played card: {card}")

        _begin_effect(result, player, {"kind": kind})
        return result

    if action.startswith("combo:pair:"):
        parts = action.split(":")
        card = parts[2]
        target = int(parts[4])
        _remove_cards(result.hands[player], card, 2)
        result.discard.extend([card, card])
        _begin_effect(
            result,
            player,
            {"kind": "pair", "target": target},
        )
        return result

    if action.startswith("combo:triple:"):
        parts = action.split(":")
        card = parts[2]
        target = int(parts[4])
        requested = parts[6]
        _remove_cards(result.hands[player], card, 3)
        result.discard.extend([card, card, card])
        _begin_effect(
            result,
            player,
            {
                "kind": "triple",
                "target": target,
                "requested": requested,
            },
        )
        return result

    if action.startswith("combo:five:"):
        selected = action.removeprefix("combo:five:").split("+")
        for card in selected:
            result.hands[player].remove(card)
            result.discard.append(card)
        _begin_effect(result, player, {"kind": "five"})
        return result

    raise RuntimeError(f"Unhandled legal action: {action}")


def _returns(state: GameState) -> List[int]:
    if not _is_terminal(state):
        return [0] * state.num_players

    alive = _alive_players(state)
    if not alive:
        return [-1] * state.num_players

    winner = alive[0]
    return [1 if player == winner else -1 for player in range(state.num_players)]


def _render(state: GameState) -> str:
    if _is_terminal(state):
        alive = _alive_players(state)
        winner = alive[0] if alive else None
        return (
            f"Terminal\n"
            f"Winner: {winner}\n"
            f"Returns: {_returns(state)}\n"
            f"Discard: {', '.join(state.discard) or '(empty)'}"
        )

    viewer = _current_player(state)
    lines = [
        f"Phase: {state.phase}",
        f"Current player: {viewer}",
        f"Turn owner: {state.turn_player}",
        f"Turns remaining for owner: {state.turns_left}",
        f"Draw pile: {len(state.deck)} cards",
        f"Discard top: {state.discard[-1] if state.discard else '(empty)'}",
    ]

    for player in range(state.num_players):
        status = "alive" if state.alive[player] else "eliminated"
        if player == viewer:
            cards = ", ".join(sorted(state.hands[player])) or "(empty)"
            lines.append(f"Player {player} ({status}) hand: {cards}")
        else:
            lines.append(
                f"Player {player} ({status}) hand: "
                f"{len(state.hands[player])} hidden cards"
            )

    if viewer in state.private_views:
        viewed = ", ".join(state.private_views[viewer]) or "(none)"
        lines.append(f"Private future view for player {viewer}: {viewed}")

    if state.phase == "response" and state.pending is not None:
        lines.append(
            "Pending action: "
            f"{state.pending['kind']} "
            f"({'active' if state.pending['active'] else 'cancelled'})"
        )

    return "\n".join(lines)
