## Open questions / assumptions

- The 56-card total implies five distinct four-card symbol sets; unreadable titles are represented as `symbol-a` through `symbol-e`.
- Contradiction reactions receive clockwise priority with explicit passes; playing one restarts priority after that player.
- Seeded random resolution handles shuffling and random pair theft.
- A player may decline protection and explode because the rule says they “can” play it.
- If a choice target has no cards, or a requested triple card is absent, the effect does nothing.

```python
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
import random
from typing import Any, Optional


EXPLODING = "danger"
DEFUSE = "protection"
ATTACK = "double_turn"
SKIP = "skip"
FAVOR = "choice"
SHUFFLE = "reorder"
SEE = "preview"
NOPE = "contradiction"

# The supplied text establishes 56 total cards and four cards of each
# symbol-card kind, but does not preserve their individual titles.
SYMBOLS = (
    "symbol_a",
    "symbol_b",
    "symbol_c",
    "symbol_d",
    "symbol_e",
)

CARD_TYPES = (
    EXPLODING,
    DEFUSE,
    ATTACK,
    SKIP,
    FAVOR,
    SHUFFLE,
    SEE,
    NOPE,
) + SYMBOLS

REQUESTABLE = tuple(card for card in CARD_TYPES if card != EXPLODING)

DISPLAY = {
    EXPLODING: "danger",
    DEFUSE: "protection",
    ATTACK: "double-turn",
    SKIP: "skip",
    FAVOR: "choice",
    SHUFFLE: "reorder",
    SEE: "preview",
    NOPE: "contradiction",
    "symbol_a": "symbol-a",
    "symbol_b": "symbol-b",
    "symbol_c": "symbol-c",
    "symbol_d": "symbol-d",
    "symbol_e": "symbol-e",
}
BY_DISPLAY = {display: card for card, display in DISPLAY.items()}


@dataclass
class GameState:
    game: "Game" = field(repr=False, compare=False)
    hands: list[list[str]]
    deck: list[str]
    discard: list[str]
    alive: list[bool]
    active_player: int = 0
    turns_remaining: int = 1
    phase: str = "main"
    pending: Optional[dict[str, Any]] = None
    reaction_queue: list[int] = field(default_factory=list)
    exploding_player: Optional[int] = None
    observations: list[tuple[str, ...]] = field(default_factory=list)
    winner: Optional[int] = None

    def initial_state(self) -> "GameState":
        return self.game.initial_state()

    def current_player(self) -> int:
        return self.game.current_player(self)

    def legal_actions(self) -> list[str]:
        return self.game.legal_actions(self)

    def apply_action(self, action: str) -> "GameState":
        return self.game.apply_action(self, action)

    def is_terminal(self) -> bool:
        return self.game.is_terminal(self)

    def returns(self) -> list[int]:
        return self.game.returns(self)

    def render(self) -> str:
        return self.game.render(self)

    def action_to_name(self, action: str) -> str:
        return self.game.action_to_name(action)

    def name_to_action(self, name: str) -> str:
        return self.game.name_to_action(name)


class Game:
    def __init__(
        self,
        num_players: int = 2,
        seed: Optional[int] = None,
    ):
        if not 2 <= num_players <= 5:
            raise ValueError("num_players must be between 2 and 5")

        self.num_players = num_players
        self.seed = seed
        self._rng = random.Random(seed)

    def initial_state(self) -> GameState:
        rng = random.Random(self.seed)

        ordinary_cards = (
            [ATTACK] * 4
            + [SKIP] * 4
            + [FAVOR] * 4
            + [SHUFFLE] * 4
            + [SEE] * 5
            + [NOPE] * 5
            + [symbol for symbol in SYMBOLS for _ in range(4)]
        )
        rng.shuffle(ordinary_cards)

        hands = [[] for _ in range(self.num_players)]
        for _ in range(7):
            for player in range(self.num_players):
                hands[player].append(ordinary_cards.pop())

        for hand in hands:
            hand.append(DEFUSE)

        remaining_defuses = (
            2 if self.num_players == 2 else 6 - self.num_players
        )
        deck = (
            ordinary_cards
            + [DEFUSE] * remaining_defuses
            + [EXPLODING] * (self.num_players - 1)
        )
        rng.shuffle(deck)
        self._rng = rng

        return GameState(
            game=self,
            hands=hands,
            deck=deck,
            discard=[],
            alive=[True] * self.num_players,
            observations=[tuple() for _ in range(self.num_players)],
        )

    def current_player(self, state: GameState) -> int:
        if self.is_terminal(state):
            return -1

        if state.phase == "reaction":
            return state.reaction_queue[0]

        if state.phase == "favor_give":
            return state.pending["target"]

        if state.phase in ("defuse", "insert"):
            assert state.exploding_player is not None
            return state.exploding_player

        return state.active_player

    def legal_actions(self, state: GameState) -> list[str]:
        if self.is_terminal(state):
            return []

        if state.phase == "reaction":
            player = state.reaction_queue[0]
            actions = ["reaction:pass"]
            if NOPE in state.hands[player]:
                actions.append("reaction:contradiction")
            return actions

        if state.phase == "favor_give":
            giver = state.pending["target"]
            return [
                f"give:{DISPLAY[card]}"
                for card in sorted(set(state.hands[giver]))
            ]

        if state.phase == "defuse":
            player = state.exploding_player
            assert player is not None

            actions = ["explode"]
            if DEFUSE in state.hands[player]:
                actions.insert(0, "defuse:use-protection")
            return actions

        if state.phase == "insert":
            return [
                f"insert-danger:{position}"
                for position in range(len(state.deck) + 1)
            ]

        player = state.active_player
        hand = state.hands[player]
        actions = ["draw"]

        for card, action in (
            (SKIP, "play:skip"),
            (ATTACK, "play:double-turn"),
            (SHUFFLE, "play:reorder"),
            (SEE, "play:preview"),
        ):
            if card in hand:
                actions.append(action)

        other_players = [
            other
            for other in range(self.num_players)
            if state.alive[other] and other != player
        ]

        if FAVOR in hand:
            actions.extend(
                f"play:choice:target:{target}"
                for target in other_players
            )

        counts = {card: hand.count(card) for card in set(hand)}

        for card in sorted(counts):
            if counts[card] >= 2:
                actions.extend(
                    f"combo:pair:{DISPLAY[card]}:target:{target}"
                    for target in other_players
                )

            if counts[card] >= 3:
                actions.extend(
                    (
                        f"combo:triple:{DISPLAY[card]}"
                        f":target:{target}"
                        f":request:{DISPLAY[requested]}"
                    )
                    for target in other_players
                    for requested in REQUESTABLE
                )

        distinct_cards = sorted(set(hand))
        if len(distinct_cards) >= 5:
            for chosen in combinations(distinct_cards, 5):
                # The selected cards enter the discard pile before recovery,
                # so one of their titles is also recoverable.
                recoverable = sorted(set(state.discard).union(chosen))
                encoded = "+".join(DISPLAY[card] for card in chosen)

                actions.extend(
                    (
                        f"combo:five:{encoded}"
                        f":recover:{DISPLAY[recovered]}"
                    )
                    for recovered in recoverable
                )

        return actions

    def apply_action(
        self,
        state: GameState,
        action: str,
    ) -> GameState:
        if action not in self.legal_actions(state):
            raise ValueError(f"illegal action: {action}")

        if state.phase == "reaction":
            self._apply_reaction(state, action)
            return state

        if state.phase == "favor_give":
            card = BY_DISPLAY[action.split(":", 1)[1]]
            giver = state.pending["target"]
            receiver = state.pending["actor"]

            state.hands[giver].remove(card)
            state.hands[receiver].append(card)
            state.pending = None
            state.phase = "main"
            state.active_player = receiver
            return state

        if state.phase == "defuse":
            player = state.exploding_player
            assert player is not None

            if action == "explode":
                self._eliminate(state, player)
            else:
                state.hands[player].remove(DEFUSE)
                state.discard.append(DEFUSE)
                state.phase = "insert"

            return state

        if state.phase == "insert":
            position = int(action.rsplit(":", 1)[1])
            player = state.exploding_player
            assert player is not None

            state.deck.insert(position, EXPLODING)
            state.observations = [
                tuple() for _ in range(self.num_players)
            ]
            state.observations[player] = (
                f"inserted-danger-at:{position}",
            )
            state.exploding_player = None
            state.phase = "main"
            self._finish_one_turn(state)
            return state

        player = state.active_player

        if action == "draw":
            self._draw(state, player)
            return state

        if action == "play:skip":
            self._spend_and_offer(
                state,
                player,
                [SKIP],
                {"kind": "skip", "actor": player},
            )

        elif action == "play:double-turn":
            self._spend_and_offer(
                state,
                player,
                [ATTACK],
                {"kind": "attack", "actor": player},
            )

        elif action == "play:reorder":
            self._spend_and_offer(
                state,
                player,
                [SHUFFLE],
                {"kind": "shuffle", "actor": player},
            )

        elif action == "play:preview":
            self._spend_and_offer(
                state,
                player,
                [SEE],
                {"kind": "see", "actor": player},
            )

        elif action.startswith("play:choice:target:"):
            target = int(action.rsplit(":", 1)[1])
            self._spend_and_offer(
                state,
                player,
                [FAVOR],
                {
                    "kind": "favor",
                    "actor": player,
                    "target": target,
                },
            )

        elif action.startswith("combo:pair:"):
            parts = action.split(":")
            card = BY_DISPLAY[parts[2]]
            target = int(parts[4])

            self._spend_and_offer(
                state,
                player,
                [card, card],
                {
                    "kind": "pair",
                    "actor": player,
                    "target": target,
                },
            )

        elif action.startswith("combo:triple:"):
            parts = action.split(":")
            card = BY_DISPLAY[parts[2]]
            target = int(parts[4])
            requested = BY_DISPLAY[parts[6]]

            self._spend_and_offer(
                state,
                player,
                [card, card, card],
                {
                    "kind": "triple",
                    "actor": player,
                    "target": target,
                    "requested": requested,
                },
            )

        elif action.startswith("combo:five:"):
            _, _, encoded, _, recovery = action.split(":")
            cards = [
                BY_DISPLAY[label]
                for label in encoded.split("+")
            ]

            self._spend_and_offer(
                state,
                player,
                cards,
                {
                    "kind": "five",
                    "actor": player,
                    "recovery": BY_DISPLAY[recovery],
                },
            )

        return state

    def _spend_and_offer(
        self,
        state: GameState,
        actor: int,
        cards: list[str],
        effect: dict[str, Any],
    ) -> None:
        for card in cards:
            state.hands[actor].remove(card)
            state.discard.append(card)

        state.pending = effect
        state.reaction_queue = self._clockwise_alive_after(
            state,
            actor,
        )

        if state.reaction_queue:
            state.phase = "reaction"
        else:
            self._resolve_pending(state)

    def _apply_reaction(
        self,
        state: GameState,
        action: str,
    ) -> None:
        responder = state.reaction_queue.pop(0)

        if action == "reaction:contradiction":
            state.hands[responder].remove(NOPE)
            state.discard.append(NOPE)
            state.pending["canceled"] = not state.pending.get(
                "canceled",
                False,
            )

            # A contradiction can itself be contradicted. Priority restarts
            # clockwise after the player who most recently reacted.
            state.reaction_queue = self._clockwise_alive_after(
                state,
                responder,
            )

        if not state.reaction_queue:
            self._resolve_pending(state)

    def _resolve_pending(self, state: GameState) -> None:
        effect = state.pending
        assert effect is not None

        state.reaction_queue = []
        state.phase = "main"

        if effect.get("canceled", False):
            state.active_player = effect["actor"]
            state.pending = None
            return

        kind = effect["kind"]
        actor = effect["actor"]

        if kind == "skip":
            state.pending = None
            self._finish_one_turn(state)

        elif kind == "attack":
            state.pending = None
            state.active_player = self._next_alive(state, actor)
            state.turns_remaining = 2

        elif kind == "shuffle":
            self._rng.shuffle(state.deck)
            state.observations = [
                tuple() for _ in range(self.num_players)
            ]
            state.pending = None
            state.active_player = actor

        elif kind == "see":
            state.observations[actor] = tuple(state.deck[:3])
            state.pending = None
            state.active_player = actor

        elif kind == "favor":
            target = effect["target"]
            if state.hands[target]:
                state.phase = "favor_give"
                state.active_player = actor
            else:
                state.pending = None
                state.active_player = actor

        elif kind == "pair":
            target = effect["target"]
            if state.hands[target]:
                index = self._rng.randrange(
                    len(state.hands[target])
                )
                card = state.hands[target].pop(index)
                state.hands[actor].append(card)

            state.pending = None
            state.active_player = actor

        elif kind == "triple":
            target = effect["target"]
            requested = effect["requested"]

            if requested in state.hands[target]:
                state.hands[target].remove(requested)
                state.hands[actor].append(requested)

            state.pending = None
            state.active_player = actor

        elif kind == "five":
            recovery = effect["recovery"]
            state.discard.remove(recovery)
            state.hands[actor].append(recovery)
            state.pending = None
            state.active_player = actor

    def _draw(
        self,
        state: GameState,
        player: int,
    ) -> None:
        if not state.deck:
            # The rulebook states that the pile cannot become empty.
            raise RuntimeError(
                "draw pile exhausted in a state the rulebook excludes"
            )

        card = state.deck.pop(0)

        if card == EXPLODING:
            state.exploding_player = player
            state.phase = "defuse"
        else:
            state.hands[player].append(card)
            self._finish_one_turn(state)

    def _finish_one_turn(self, state: GameState) -> None:
        if state.turns_remaining > 1:
            state.turns_remaining -= 1
        else:
            state.active_player = self._next_alive(
                state,
                state.active_player,
            )
            state.turns_remaining = 1

    def _eliminate(
        self,
        state: GameState,
        player: int,
    ) -> None:
        state.discard.extend(state.hands[player])
        state.hands[player].clear()
        state.discard.append(EXPLODING)
        state.alive[player] = False
        state.exploding_player = None

        living = [
            candidate
            for candidate, alive in enumerate(state.alive)
            if alive
        ]

        if len(living) == 1:
            state.winner = living[0]
            state.phase = "terminal"
            state.pending = None
            state.reaction_queue = []
        else:
            state.phase = "main"
            state.active_player = self._next_alive(state, player)
            state.turns_remaining = 1

    def _next_alive(
        self,
        state: GameState,
        player: int,
    ) -> int:
        for distance in range(1, self.num_players + 1):
            candidate = (player + distance) % self.num_players
            if state.alive[candidate]:
                return candidate

        return player

    def _clockwise_alive_after(
        self,
        state: GameState,
        player: int,
    ) -> list[int]:
        result = []

        for distance in range(1, self.num_players):
            candidate = (player + distance) % self.num_players
            if state.alive[candidate]:
                result.append(candidate)

        return result

    def is_terminal(self, state: GameState) -> bool:
        return state.winner is not None

    def returns(self, state: GameState) -> list[int]:
        if not self.is_terminal(state):
            return [0] * self.num_players

        return [
            1 if player == state.winner else -1
            for player in range(self.num_players)
        ]

    def render(self, state: GameState) -> str:
        current = self.current_player(state)
        lines = [
            f"phase={state.phase}",
            f"current_player={current}",
            f"deck_cards={len(state.deck)}",
            f"discard={[DISPLAY[card] for card in state.discard]}",
            f"alive={state.alive}",
            f"turns_remaining={state.turns_remaining}",
        ]

        for player, hand in enumerate(state.hands):
            if player == current:
                lines.append(
                    f"player_{player}_hand="
                    f"{[DISPLAY[card] for card in hand]}"
                )

                if state.observations[player]:
                    observation = [
                        DISPLAY.get(item, item)
                        for item in state.observations[player]
                    ]
                    lines.append(
                        f"player_{player}_private_observation="
                        f"{observation}"
                    )
            else:
                lines.append(
                    f"player_{player}_hand_count={len(hand)}"
                )

        if state.winner is not None:
            lines.append(f"winner={state.winner}")

        return "\n".join(lines)

    def action_to_name(self, action: str) -> str:
        if not isinstance(action, str):
            raise TypeError("actions are strings")
        return action

    def name_to_action(self, name: str) -> str:
        if not isinstance(name, str):
            raise TypeError("action names are strings")
        return name
```