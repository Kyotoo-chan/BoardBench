"""Self-contained Exploding Kittens environment based only on the supplied rules."""

from dataclasses import dataclass, field
from itertools import combinations
import random
from typing import Any, Dict, List, Optional


EXPLODING_KITTEN = "exploding_kitten"
DEFUSE = "defuse"
ATTACK = "attack"
SKIP = "skip"
FAVOR = "favor"
SHUFFLE = "shuffle"
SEE_FUTURE = "see_the_future"
NOPE = "nope"

CAT_CARDS = (
    "cat:taco",
    "cat:cattermelon",
    "cat:hairy_potato",
    "cat:beard",
    "cat:rainbow",
)

PLAYABLE_CARDS = (ATTACK, SKIP, FAVOR, SHUFFLE, SEE_FUTURE)
ALL_CARD_TYPES = (
    EXPLODING_KITTEN,
    DEFUSE,
    ATTACK,
    SKIP,
    FAVOR,
    SHUFFLE,
    SEE_FUTURE,
    NOPE,
) + CAT_CARDS


def _base_cards() -> List[str]:
    cards: List[str] = []
    cards += [EXPLODING_KITTEN] * 4
    cards += [DEFUSE] * 6
    cards += [ATTACK] * 4
    cards += [SKIP] * 4
    cards += [FAVOR] * 4
    cards += [SHUFFLE] * 4
    cards += [SEE_FUTURE] * 5
    cards += [NOPE] * 5
    for card in CAT_CARDS:
        cards += [card] * 4
    return cards


@dataclass
class GameState:
    num_players: int
    hands: List[List[str]]
    deck: List[str]
    discard: List[str]
    alive: List[bool]
    active_player: int = 0
    turns_left: int = 1
    phase: str = "play"
    pending: Optional[Dict[str, Any]] = None
    reaction_player: Optional[int] = None
    reaction_passes: int = 0
    peek_actor: Optional[int] = None
    peek_cards: List[str] = field(default_factory=list)
    winner: Optional[int] = None
    rng: random.Random = field(default_factory=random.Random, repr=False)

    def current_player(self) -> int:
        if self.is_terminal():
            return -1
        if self.phase == "reaction":
            assert self.reaction_player is not None
            return self.reaction_player
        return self.active_player

    def legal_actions(self) -> List[str]:
        if self.is_terminal():
            return []

        if self.phase == "reaction":
            actions = ["react:pass"]
            player = self.reaction_player
            if player is not None and NOPE in self.hands[player]:
                actions.append("react:nope")
            return actions

        if self.phase == "give":
            assert self.pending is not None
            donor = self.active_player
            recipient = self.pending["actor"]
            return sorted({
                f"give:{card}:to:player{recipient}"
                for card in self.hands[donor]
            })

        if self.phase == "defuse":
            return [
                f"defuse:insert:top+{distance}"
                for distance in range(len(self.deck) + 1)
            ]

        player = self.active_player
        hand = self.hands[player]
        actions = ["turn:draw"]

        for card in PLAYABLE_CARDS:
            if card in hand:
                if card == FAVOR:
                    for target in self._opponents(player):
                        actions.append(f"play:favor:target:player{target}")
                else:
                    actions.append(f"play:{card}")

        counts = {card: hand.count(card) for card in set(hand)}

        for card, count in counts.items():
            if count >= 2:
                for target in self._opponents(player):
                    actions.append(
                        f"combo:pair:{card}:target:player{target}"
                    )

            if count >= 3:
                for target in self._opponents(player):
                    for requested in ALL_CARD_TYPES:
                        actions.append(
                            f"combo:triple:{card}:target:player{target}"
                            f":request:{requested}"
                        )

        distinct = sorted(counts)
        if len(distinct) >= 5 and self.discard:
            retrievable = sorted(set(self.discard))
            for used_cards in combinations(distinct, 5):
                used = "+".join(used_cards)
                for retrieved in retrievable:
                    actions.append(
                        f"combo:five:{used}:retrieve:{retrieved}"
                    )

        return sorted(set(actions))

    def apply_action(self, action: str) -> "GameState":
        if action not in self.legal_actions():
            raise ValueError(f"Illegal action: {action!r}")

        if self.phase == "reaction":
            self._apply_reaction(action)
        elif self.phase == "give":
            self._apply_give(action)
        elif self.phase == "defuse":
            self._apply_defuse(action)
        elif action == "turn:draw":
            self._draw()
        elif action.startswith("play:"):
            self._play_card(action)
        elif action.startswith("combo:"):
            self._play_combo(action)
        else:
            raise ValueError(f"Unrecognized action: {action!r}")

        return self

    def is_terminal(self) -> bool:
        return self.winner is not None

    def returns(self) -> List[int]:
        if not self.is_terminal():
            return [0] * self.num_players
        return [
            1 if player == self.winner else -1
            for player in range(self.num_players)
        ]

    def render(self) -> str:
        if self.is_terminal():
            return (
                f"terminal winner=player{self.winner} "
                f"returns={self.returns()}"
            )

        viewer = self.current_player()
        lines = [
            f"phase={self.phase}",
            f"current_player=player{viewer}",
            f"turn_owner=player{self.active_player}",
            f"turns_left={self.turns_left}",
            f"deck_count={len(self.deck)}",
            f"discard_top={self.discard[-1] if self.discard else 'empty'}",
        ]

        for player in range(self.num_players):
            if not self.alive[player]:
                lines.append(f"player{player}=eliminated")
            elif player == viewer:
                lines.append(
                    f"player{player}_hand={sorted(self.hands[player])}"
                )
            else:
                lines.append(
                    f"player{player}_hand_count={len(self.hands[player])}"
                )

        if self.phase == "reaction" and self.pending is not None:
            status = "cancelled" if self.pending["noped"] else "active"
            lines.append(
                f"pending={self.pending['label']} status={status}"
            )

        if self.peek_actor == viewer and self.peek_cards:
            lines.append(f"private_top_cards={self.peek_cards}")

        return "\n".join(lines)

    @staticmethod
    def action_to_name(action: str) -> str:
        if not isinstance(action, str):
            raise TypeError("Actions are represented by strings")
        return action

    @staticmethod
    def name_to_action(name: str) -> str:
        if not isinstance(name, str):
            raise TypeError("Action names must be strings")
        return name

    def _living_count(self) -> int:
        return sum(self.alive)

    def _opponents(self, player: int) -> List[int]:
        return [
            other
            for other in range(self.num_players)
            if other != player and self.alive[other]
        ]

    def _next_alive(self, player: int) -> int:
        for offset in range(1, self.num_players + 1):
            candidate = (player + offset) % self.num_players
            if self.alive[candidate]:
                return candidate
        return player

    def _remove_cards(
        self, player: int, card: str, amount: int
    ) -> None:
        for _ in range(amount):
            self.hands[player].remove(card)
            self.discard.append(card)

    def _clear_peek_if_deck_changed(self) -> None:
        self.peek_actor = None
        self.peek_cards = []

    def _start_pending(
        self,
        actor: int,
        effect: str,
        label: str,
        **arguments: Any,
    ) -> None:
        self.pending = {
            "actor": actor,
            "effect": effect,
            "label": label,
            "arguments": arguments,
            "noped": False,
        }
        self.phase = "reaction"
        self.reaction_player = self._next_alive(actor)
        self.reaction_passes = 0

    def _apply_reaction(self, action: str) -> None:
        assert self.pending is not None
        assert self.reaction_player is not None

        if action == "react:nope":
            player = self.reaction_player
            self.hands[player].remove(NOPE)
            self.discard.append(NOPE)
            self.pending["noped"] = not self.pending["noped"]
            self.reaction_passes = 0
            self.reaction_player = self._next_alive(player)
            return

        self.reaction_passes += 1
        if self.reaction_passes >= self._living_count():
            pending = self.pending
            self.pending = None
            self.reaction_player = None
            self.reaction_passes = 0
            self.phase = "play"
            self.active_player = pending["actor"]

            if not pending["noped"]:
                self._resolve_effect(
                    pending["effect"],
                    pending["actor"],
                    pending["arguments"],
                )
        else:
            self.reaction_player = self._next_alive(
                self.reaction_player
            )

    def _play_card(self, action: str) -> None:
        actor = self.active_player

        if action.startswith("play:favor:target:player"):
            target = int(action.rsplit("player", 1)[1])
            self._remove_cards(actor, FAVOR, 1)
            self._start_pending(
                actor,
                FAVOR,
                f"favor targeting player{target}",
                target=target,
            )
            return

        card = action[len("play:"):]
        self._remove_cards(actor, card, 1)
        self._start_pending(actor, card, card)

    def _play_combo(self, action: str) -> None:
        actor = self.active_player
        parts = action.split(":")

        if parts[1] == "pair":
            card = parts[2]
            target = int(parts[4].removeprefix("player"))
            self._remove_cards(actor, card, 2)
            self._start_pending(
                actor,
                "pair",
                f"pair of {card} targeting player{target}",
                target=target,
            )
            return

        if parts[1] == "triple":
            card = parts[2]
            target = int(parts[4].removeprefix("player"))
            requested = ":".join(parts[6:])
            self._remove_cards(actor, card, 3)
            self._start_pending(
                actor,
                "triple",
                f"triple of {card} requesting {requested} "
                f"from player{target}",
                target=target,
                requested=requested,
            )
            return

        if parts[1] == "five":
            used_cards = parts[2].split("+")
            retrieved = ":".join(parts[4:])
            for card in used_cards:
                self._remove_cards(actor, card, 1)
            self._start_pending(
                actor,
                "five",
                f"five-card combo retrieving {retrieved}",
                retrieved=retrieved,
            )
            return

        raise ValueError(f"Unknown combination: {action!r}")

    def _resolve_effect(
        self,
        effect: str,
        actor: int,
        arguments: Dict[str, Any],
    ) -> None:
        if effect == ATTACK:
            self.active_player = self._next_alive(actor)
            self.turns_left = 2
            self.phase = "play"
            self.peek_actor = None
            self.peek_cards = []
            return

        if effect == SKIP:
            self._complete_turn_unit()
            return

        if effect == FAVOR:
            target = arguments["target"]
            if not self.hands[target]:
                return
            self.active_player = target
            self.phase = "give"
            self.pending = {"actor": actor}
            return

        if effect == SHUFFLE:
            self.rng.shuffle(self.deck)
            self._clear_peek_if_deck_changed()
            return

        if effect == SEE_FUTURE:
            self.peek_actor = actor
            self.peek_cards = list(reversed(self.deck[-3:]))
            return

        if effect == "pair":
            target = arguments["target"]
            if self.hands[target]:
                index = self.rng.randrange(len(self.hands[target]))
                stolen = self.hands[target].pop(index)
                self.hands[actor].append(stolen)
            return

        if effect == "triple":
            target = arguments["target"]
            requested = arguments["requested"]
            if requested in self.hands[target]:
                self.hands[target].remove(requested)
                self.hands[actor].append(requested)
            return

        if effect == "five":
            retrieved = arguments["retrieved"]
            if retrieved in self.discard:
                reverse_index = self.discard[::-1].index(retrieved)
                index = len(self.discard) - 1 - reverse_index
                self.discard.pop(index)
                self.hands[actor].append(retrieved)
            return

        raise RuntimeError(f"Unknown pending effect: {effect!r}")

    def _apply_give(self, action: str) -> None:
        assert self.pending is not None
        donor = self.active_player
        actor = self.pending["actor"]

        prefix = "give:"
        separator = f":to:player{actor}"
        card = action[len(prefix):-len(separator)]

        self.hands[donor].remove(card)
        self.hands[actor].append(card)
        self.active_player = actor
        self.phase = "play"
        self.pending = None

    def _draw(self) -> None:
        if not self.deck:
            raise RuntimeError(
                "The rulebook states the draw pile will not become empty"
            )

        actor = self.active_player
        card = self.deck.pop()
        self._clear_peek_if_deck_changed()

        if card != EXPLODING_KITTEN:
            self.hands[actor].append(card)
            self._complete_turn_unit()
            return

        if DEFUSE in self.hands[actor]:
            self.phase = "defuse"
            self.pending = {"kitten": EXPLODING_KITTEN}
            return

        self._eliminate(actor, EXPLODING_KITTEN)

    def _apply_defuse(self, action: str) -> None:
        actor = self.active_player
        distance = int(action.rsplit("+", 1)[1])

        self.hands[actor].remove(DEFUSE)
        self.discard.append(DEFUSE)

        # The end of the list is the top of the draw pile.
        insertion_index = len(self.deck) - distance
        self.deck.insert(insertion_index, EXPLODING_KITTEN)

        self.phase = "play"
        self.pending = None
        self._clear_peek_if_deck_changed()
        self._complete_turn_unit()

    def _complete_turn_unit(self) -> None:
        self.turns_left -= 1
        if self.turns_left > 0:
            self.phase = "play"
            return

        previous = self.active_player
        self.active_player = self._next_alive(previous)
        self.turns_left = 1
        self.phase = "play"

        if self.active_player != previous:
            self.peek_actor = None
            self.peek_cards = []

    def _eliminate(self, player: int, kitten: str) -> None:
        self.discard.extend(self.hands[player])
        self.hands[player].clear()
        self.discard.append(kitten)
        self.alive[player] = False
        self.phase = "play"
        self.pending = None
        self.peek_actor = None
        self.peek_cards = []

        living = [
            candidate
            for candidate, alive in enumerate(self.alive)
            if alive
        ]
        if len(living) == 1:
            self.winner = living[0]
            return

        self.active_player = self._next_alive(player)
        self.turns_left = 1


class Game:
    def __init__(
        self,
        num_players: int = 2,
        seed: Optional[int] = None,
    ):
        if not 2 <= num_players <= 5:
            raise ValueError("The supplied rules support 2 to 5 players")
        self.num_players = num_players
        self.seed = seed

    def initial_state(self) -> GameState:
        rng = random.Random(self.seed)
        cards = _base_cards()

        ordinary = [
            card
            for card in cards
            if card not in (EXPLODING_KITTEN, DEFUSE)
        ]
        rng.shuffle(ordinary)

        hands = [[] for _ in range(self.num_players)]
        for player in range(self.num_players):
            for _ in range(7):
                hands[player].append(ordinary.pop())
            hands[player].append(DEFUSE)

        if self.num_players == 2:
            extra_defuses = 2
        else:
            extra_defuses = 6 - self.num_players

        deck = ordinary
        deck += [DEFUSE] * extra_defuses
        deck += [EXPLODING_KITTEN] * (self.num_players - 1)
        rng.shuffle(deck)

        return GameState(
            num_players=self.num_players,
            hands=hands,
            deck=deck,
            discard=[],
            alive=[True] * self.num_players,
            active_player=0,
            turns_left=1,
            rng=rng,
        )

    @staticmethod
    def current_player(state: GameState) -> int:
        return state.current_player()

    @staticmethod
    def legal_actions(state: GameState) -> List[str]:
        return state.legal_actions()

    @staticmethod
    def apply_action(
        state: GameState, action: str
    ) -> GameState:
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
