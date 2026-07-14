from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from itertools import combinations
import random
from typing import List, Optional, Tuple


EXPLODING = "Exploding Kitten"
DEFUSE = "Entschaerfung"
ATTACK = "Angriff"
SKIP = "Hops!"
FUTURE = "Blick in die Zukunft"
NOPE = "Noe!"
SHUFFLE = "Mischen"
FAVOR = "Wunsch"

# The source states that the game contains 56 cards and that each cat-card
# family contains four cards, but only two family names survive in the
# supplied text. These placeholders keep the unresolved identities explicit.
CATS = (
    "Zombiekatze",
    "Augenmampfende",
    "Unbenannte Katzenkarte A",
    "Unbenannte Katzenkarte B",
    "Unbenannte Katzenkarte C",
)

NORMAL_COUNTS = {
    ATTACK: 4,
    SKIP: 4,
    FUTURE: 5,
    NOPE: 5,
    SHUFFLE: 4,
    FAVOR: 4,
    **{card: 4 for card in CATS},
}

REQUESTABLE = tuple(NORMAL_COUNTS) + (DEFUSE,)
EFFECT_CARDS = (ATTACK, SKIP, FUTURE, SHUFFLE)


@dataclass
class GameState:
    num_players: int
    hands: List[List[str]]
    deck: List[str]
    discard: List[str]
    alive: List[bool]
    turn_player: int = 0
    turns_left: int = 1
    phase: str = "turn"
    pending: Optional[Tuple] = None
    reaction_player: int = 0
    reaction_passes: int = 0
    nope_count: int = 0
    knowledge: List[Optional[Tuple[str, ...]]] = field(default_factory=list)
    winner: Optional[int] = None
    rng: random.Random = field(default_factory=random.Random, repr=False)
    game: Optional["Game"] = field(default=None, repr=False, compare=False)

    def current_player(self) -> int:
        return self.game.current_player(self)

    def legal_actions(self) -> List[str]:
        return self.game.legal_actions(self)

    def apply_action(self, action: str) -> "GameState":
        return self.game.apply_action(self, action)

    def is_terminal(self) -> bool:
        return self.game.is_terminal(self)

    def returns(self) -> List[int]:
        return self.game.returns(self)

    def render(self) -> str:
        return self.game.render(self)


class Game:
    def __init__(self, num_players: int = 2, seed: Optional[int] = None):
        if not 2 <= num_players <= 5:
            raise ValueError("The rulebook allows 2-5 players")
        self.num_players = num_players
        self.seed = seed

    def initial_state(self) -> GameState:
        rng = random.Random(self.seed)
        pool = [
            card
            for card, count in NORMAL_COUNTS.items()
            for _ in range(count)
        ]
        rng.shuffle(pool)

        hands = [[] for _ in range(self.num_players)]
        for player in range(self.num_players):
            hands[player].append(DEFUSE)
            for _ in range(7):
                hands[player].append(pool.pop())

        extra_defuses = 2 if self.num_players == 2 else 6 - self.num_players
        kitten_count = self.num_players - 1

        deck = pool + [DEFUSE] * extra_defuses
        deck += [EXPLODING] * kitten_count
        rng.shuffle(deck)

        state = GameState(
            num_players=self.num_players,
            hands=hands,
            deck=deck,
            discard=[],
            alive=[True] * self.num_players,
            knowledge=[None] * self.num_players,
            rng=rng,
        )
        state.game = self
        return state

    def current_player(self, state: GameState) -> int:
        if self.is_terminal(state):
            return -1
        if state.phase == "reaction":
            return state.reaction_player
        if state.phase == "give":
            return state.pending[2]
        return state.turn_player

    def legal_actions(self, state: GameState) -> List[str]:
        if self.is_terminal(state):
            return []

        if state.phase == "reaction":
            actions = ["allow"]
            if NOPE in state.hands[state.reaction_player]:
                actions.append("nope")
            return actions

        if state.phase == "defuse":
            size = len(state.deck)
            if size == 0:
                return ["defuse:insert:top"]

            actions = [
                "defuse:insert:top",
                "defuse:insert:bottom",
            ]
            actions.extend(
                f"defuse:insert:depth:{depth}"
                for depth in range(1, size)
            )
            return actions

        if state.phase == "give":
            target = state.pending[2]
            return sorted({
                f"give:{card}"
                for card in state.hands[target]
            })

        player = state.turn_player
        hand = state.hands[player]
        counts = Counter(hand)
        targets = [
            other
            for other in range(state.num_players)
            if other != player and state.alive[other]
        ]

        actions = {"draw"}

        for card in EFFECT_CARDS:
            if counts[card]:
                actions.add(f"play:{card}")

        if counts[FAVOR]:
            actions.update(
                f"play:{FAVOR}|target:{target}"
                for target in targets
            )

        # The source allows every matching title, not only cat cards, to form
        # pairs and triples.
        for card, count in counts.items():
            if count >= 2:
                actions.update(
                    f"combo:pair|card:{card}|target:{target}"
                    for target in targets
                )

            if count >= 3:
                actions.update(
                    f"combo:triple|card:{card}|target:{target}"
                    f"|request:{wanted}"
                    for target in targets
                    for wanted in REQUESTABLE
                )

        # "Hinreichend verschiedene" is unresolved. Exactly five distinct
        # titles is the smallest executable interpretation.
        distinct = sorted(counts)
        available_discard = sorted(set(state.discard))
        if len(distinct) >= 5 and available_discard:
            for selected in combinations(distinct, 5):
                selected_text = ",".join(selected)
                for retrieved in available_discard:
                    actions.add(
                        f"combo:five|cards:{selected_text}|take:{retrieved}"
                    )

        return sorted(actions)

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

        if state.phase == "defuse":
            self._apply_defuse(state, action)
            return state

        if state.phase == "give":
            actor = state.pending[1]
            target = state.pending[2]
            card = action[len("give:"):]

            state.hands[target].remove(card)
            state.hands[actor].append(card)
            state.pending = None
            state.phase = "turn"
            return state

        if action == "draw":
            self._draw(state)
            return state

        player = state.turn_player

        if action.startswith("play:"):
            pieces = action.split("|")
            card = pieces[0][len("play:"):]

            state.hands[player].remove(card)
            state.discard.append(card)

            if card == FAVOR:
                target = int(pieces[1].split(":", 1)[1])
                effect = ("favor", player, target)
            else:
                effect = (card, player)

            self._open_reaction(state, effect)
            return state

        fields = dict(
            piece.split(":", 1)
            for piece in action.split("|")
        )
        kind = fields["combo"]

        if kind == "pair":
            card = fields["card"]
            self._remove_cards(state.hands[player], card, 2)
            state.discard.extend([card, card])
            effect = (
                "pair",
                player,
                int(fields["target"]),
            )

        elif kind == "triple":
            card = fields["card"]
            self._remove_cards(state.hands[player], card, 3)
            state.discard.extend([card, card, card])
            effect = (
                "triple",
                player,
                int(fields["target"]),
                fields["request"],
            )

        else:
            selected = tuple(fields["cards"].split(","))
            for card in selected:
                state.hands[player].remove(card)
                state.discard.append(card)

            effect = (
                "five",
                player,
                fields["take"],
            )

        self._open_reaction(state, effect)
        return state

    def is_terminal(self, state: GameState) -> bool:
        return state.winner is not None

    def returns(self, state: GameState) -> List[int]:
        if not self.is_terminal(state):
            return [0] * state.num_players

        return [
            1 if player == state.winner else -1
            for player in range(state.num_players)
        ]

    def render(self, state: GameState) -> str:
        viewer = self.current_player(state)
        lines = [
            f"phase={state.phase}",
            f"turn_player={state.turn_player}",
            f"current_player={viewer}",
            f"turns_left={state.turns_left}",
            f"deck_size={len(state.deck)}",
            f"discard={state.discard}",
        ]

        for player in range(state.num_players):
            status = "alive" if state.alive[player] else "eliminated"
            hand = state.hands[player]

            if player == viewer:
                hand_text = ", ".join(hand)
                lines.append(
                    f"player {player} ({status}) "
                    f"hand[{len(hand)}]={hand_text}"
                )
            else:
                lines.append(
                    f"player {player} ({status}) "
                    f"hand_size={len(hand)}"
                )

        if (
            0 <= viewer < state.num_players
            and state.knowledge[viewer] is not None
        ):
            lines.append(
                "known_top="
                + ", ".join(state.knowledge[viewer])
            )

        if state.winner is not None:
            lines.append(f"winner={state.winner}")

        return "\n".join(lines)

    @staticmethod
    def action_to_name(action: str) -> str:
        if not isinstance(action, str):
            raise TypeError("actions are strings")
        return action

    @staticmethod
    def name_to_action(name: str) -> str:
        if not isinstance(name, str):
            raise TypeError("action names are strings")
        return name

    @staticmethod
    def _remove_cards(
        hand: List[str],
        card: str,
        count: int,
    ) -> None:
        for _ in range(count):
            hand.remove(card)

    def _open_reaction(
        self,
        state: GameState,
        effect: Tuple,
    ) -> None:
        state.pending = effect
        state.phase = "reaction"
        state.nope_count = 0
        state.reaction_passes = 0
        state.reaction_player = self._next_alive(
            state,
            effect[1],
        )

    def _apply_reaction(
        self,
        state: GameState,
        action: str,
    ) -> None:
        player = state.reaction_player

        if action == "nope":
            state.hands[player].remove(NOPE)
            state.discard.append(NOPE)
            state.nope_count += 1
            state.reaction_passes = 0
        else:
            state.reaction_passes += 1

        state.reaction_player = self._next_alive(state, player)

        if state.reaction_passes >= sum(state.alive):
            effect = state.pending
            cancelled = state.nope_count % 2 == 1

            state.pending = None
            state.phase = "turn"

            if not cancelled:
                self._resolve_effect(state, effect)

    def _resolve_effect(
        self,
        state: GameState,
        effect: Tuple,
    ) -> None:
        kind = effect[0]
        actor = effect[1]

        if kind == FUTURE:
            state.knowledge[actor] = tuple(state.deck[:3])

        elif kind == SHUFFLE:
            state.rng.shuffle(state.deck)
            state.knowledge = [None] * state.num_players

        elif kind == SKIP:
            self._finish_subturn(state)

        elif kind == ATTACK:
            # The source does not define attack arithmetic precisely.
            # Doubling makes a normal attack impose two turns and makes an
            # attack played under a two-turn obligation pass four turns.
            burden = state.turns_left * 2
            state.turn_player = self._next_alive(state, actor)
            state.turns_left = burden

        elif kind == "favor":
            target = effect[2]
            if state.hands[target]:
                state.phase = "give"
                state.pending = ("give", actor, target)

        elif kind == "pair":
            target = effect[2]
            if state.hands[target]:
                index = state.rng.randrange(
                    len(state.hands[target])
                )
                stolen = state.hands[target].pop(index)
                state.hands[actor].append(stolen)

        elif kind == "triple":
            target = effect[2]
            wanted = effect[3]
            if wanted in state.hands[target]:
                state.hands[target].remove(wanted)
                state.hands[actor].append(wanted)

        elif kind == "five":
            retrieved = effect[2]
            state.discard.remove(retrieved)
            state.hands[actor].append(retrieved)

    def _draw(self, state: GameState) -> None:
        if not state.deck:
            raise RuntimeError(
                "The rulebook says the draw pile cannot become empty"
            )

        card = state.deck.pop(0)
        state.knowledge = [None] * state.num_players
        player = state.turn_player

        if card != EXPLODING:
            state.hands[player].append(card)
            self._finish_subturn(state)
            return

        if DEFUSE in state.hands[player]:
            state.phase = "defuse"
            state.pending = ("explosion", player)
            return

        state.discard.append(EXPLODING)
        self._eliminate(state, player)

    def _apply_defuse(
        self,
        state: GameState,
        action: str,
    ) -> None:
        player = state.turn_player

        state.hands[player].remove(DEFUSE)
        state.discard.append(DEFUSE)

        if action.endswith(":top"):
            position = 0
        elif action.endswith(":bottom"):
            position = len(state.deck)
        else:
            position = int(action.rsplit(":", 1)[1])

        state.deck.insert(position, EXPLODING)
        state.knowledge = [None] * state.num_players
        state.pending = None
        state.phase = "turn"
        self._finish_subturn(state)

    def _finish_subturn(self, state: GameState) -> None:
        state.turns_left -= 1
        state.phase = "turn"

        if state.turns_left <= 0:
            state.turn_player = self._next_alive(
                state,
                state.turn_player,
            )
            state.turns_left = 1

    def _eliminate(
        self,
        state: GameState,
        player: int,
    ) -> None:
        state.discard.extend(state.hands[player])
        state.hands[player].clear()
        state.alive[player] = False
        state.pending = None

        if sum(state.alive) == 1:
            state.winner = state.alive.index(True)
            state.phase = "terminal"
            return

        # The source does not specify whether an eliminated player's remaining
        # attack obligation transfers. It is cleared here.
        state.turn_player = self._next_alive(state, player)
        state.turns_left = 1
        state.phase = "turn"

    @staticmethod
    def _next_alive(
        state: GameState,
        player: int,
    ) -> int:
        candidate = player

        for _ in range(state.num_players):
            candidate = (candidate + 1) % state.num_players
            if state.alive[candidate]:
                return candidate

        return player
