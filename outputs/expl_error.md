Open questions / assumptions

- The 56-card total implies five four-card cat sets, but only `Zombiekatze` and `Augenmampfende` are named. Three sets use explicit placeholder names.
- The unnamed top-four reorder instruction conflicts with the named top-three `Blick in die Zukunft`; only the attributable top-three effect is implemented.
- Defusing uses the general rule allowing any secret deck position, despite a later isolated top-only instruction.
- `Nö!` timing is modeled as clockwise reaction windows that restart after each `Nö!`.
- The source does not say what happens when a `Wunsch` target has no cards; no card is transferred.
- The sandbox blocked execution of the requested probes; an executable smoke probe is included under `__main__`.

```python
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from itertools import combinations
import random


EXPLODING = "exploding_kitten"
DEFUSE = "entschaerfung"
ATTACK = "angriff"
SKIP = "hops"
FAVOR = "wunsch"
SHUFFLE = "mischen"
SEE_FUTURE = "blick_in_die_zukunft"
NOPE = "noe"

# The source names only two cat-card sets. The total of 56 cards requires
# five sets of four cat cards, so three explicitly unnamed placeholders remain.
CAT_CARDS = (
    "zombiekatze",
    "augenmampfende",
    "unbenannte_katzenkarte_1",
    "unbenannte_katzenkarte_2",
    "unbenannte_katzenkarte_3",
)

REQUESTABLE_CARDS = (
    DEFUSE,
    ATTACK,
    SKIP,
    FAVOR,
    SHUFFLE,
    SEE_FUTURE,
    NOPE,
) + CAT_CARDS


@dataclass
class GameState:
    num_players: int
    deck: list[str]
    hands: list[list[str]]
    discard: list[str]
    alive: list[bool]

    active_player: int = 0
    turn_debt: int = 1
    phase: str = "play"

    pending: dict | None = None
    response_order: list[int] = field(default_factory=list)
    response_index: int = 0

    give_actor: int | None = None
    give_target: int | None = None

    peek_owner: int | None = None
    peek_cards: list[str] = field(default_factory=list)

    rng: random.Random = field(default_factory=random.Random, repr=False)


class Game:
    def __init__(self, num_players: int = 2, seed: int | None = None):
        if not 2 <= num_players <= 5:
            raise ValueError("The rulebook permits 2-5 players")
        self.num_players = num_players
        self.seed = seed

    def initial_state(self) -> GameState:
        rng = random.Random(self.seed)

        ordinary = (
            [ATTACK] * 4
            + [SKIP] * 4
            + [FAVOR] * 4
            + [SHUFFLE] * 4
            + [SEE_FUTURE] * 5
            + [NOPE] * 5
        )
        for card in CAT_CARDS:
            ordinary.extend([card] * 4)

        rng.shuffle(ordinary)
        hands = [[] for _ in range(self.num_players)]

        for _ in range(7):
            for hand in hands:
                hand.append(ordinary.pop())

        for hand in hands:
            hand.append(DEFUSE)
            hand.sort()

        # The two-player variant uses exactly two additional Defuse cards.
        extra_defuses = 2 if self.num_players == 2 else 6 - self.num_players
        deck = (
            ordinary
            + [DEFUSE] * extra_defuses
            + [EXPLODING] * (self.num_players - 1)
        )
        rng.shuffle(deck)

        return GameState(
            num_players=self.num_players,
            deck=deck,
            hands=hands,
            discard=[],
            alive=[True] * self.num_players,
            rng=rng,
        )

    def current_player(self, state: GameState) -> int:
        if self.is_terminal(state):
            return -1
        if state.phase == "reaction":
            return state.response_order[state.response_index]
        if state.phase == "give":
            assert state.give_target is not None
            return state.give_target
        return state.active_player

    def legal_actions(self, state: GameState) -> list[str]:
        if self.is_terminal(state):
            return []

        if state.phase == "reaction":
            player = self.current_player(state)
            actions = ["pass:nope"]
            if NOPE in state.hands[player]:
                actions.append("play:noe")
            return actions

        if state.phase == "give":
            assert state.give_target is not None
            return [
                f"give:{card}"
                for card in sorted(set(state.hands[state.give_target]))
            ]

        if state.phase == "defuse":
            player = state.active_player
            actions = ["defuse:decline"]
            if DEFUSE in state.hands[player]:
                actions.extend(
                    f"defuse:use:position:{position}"
                    for position in range(len(state.deck) + 1)
                )
            return actions

        player = state.active_player
        hand = state.hands[player]
        actions = ["draw"]

        for card in sorted(set(hand)):
            if card in (ATTACK, SKIP, SHUFFLE, SEE_FUTURE):
                actions.append(f"play:{card}")
            elif card == FAVOR:
                for target in self._other_alive(state, player):
                    actions.append(f"play:wunsch:target:{target}")

        counts = Counter(hand)

        for card in sorted(card for card, count in counts.items() if count >= 2):
            for target in self._other_alive(state, player):
                actions.append(f"pair:{card}:target:{target}")

        for card in sorted(card for card, count in counts.items() if count >= 3):
            for target in self._other_alive(state, player):
                for requested in REQUESTABLE_CARDS:
                    actions.append(
                        f"triple:{card}:target:{target}:request:{requested}"
                    )

        distinct = sorted(counts)
        if len(distinct) >= 5:
            for chosen in combinations(distinct, 5):
                selection = "+".join(chosen)

                # The five cards enter the discard before the effect resolves.
                available = sorted(set(state.discard) | set(chosen))
                for wanted in available:
                    actions.append(f"five:{selection}:take:{wanted}")

        return actions

    def apply_action(self, state: GameState, action: str) -> GameState:
        if action not in self.legal_actions(state):
            raise ValueError(f"Illegal action: {action}")

        if state.phase == "reaction":
            self._apply_reaction(state, action)
        elif state.phase == "give":
            self._apply_give(state, action)
        elif state.phase == "defuse":
            self._apply_defuse(state, action)
        elif action == "draw":
            self._draw(state)
        else:
            self._play(state, action)

        return state

    def is_terminal(self, state: GameState) -> bool:
        return sum(state.alive) <= 1

    def returns(self, state: GameState) -> list[int]:
        if not self.is_terminal(state):
            return [0] * state.num_players
        return [1 if alive else -1 for alive in state.alive]

    def render(self, state: GameState) -> str:
        if self.is_terminal(state):
            winner = next(
                (player for player, alive in enumerate(state.alive) if alive),
                None,
            )
            return (
                f"terminal; winner={winner}; "
                f"discard={state.discard}"
            )

        player = self.current_player(state)
        lines = [
            (
                f"phase={state.phase}; current_player={player}; "
                f"active_player={state.active_player}; "
                f"turns_remaining={state.turn_debt}; "
                f"deck_size={len(state.deck)}"
            ),
            (
                f"alive={state.alive}; "
                f"hand_sizes={[len(hand) for hand in state.hands]}"
            ),
            f"player_{player}_hand={state.hands[player]}",
            f"discard={state.discard}",
        ]

        if state.peek_owner == player:
            lines.append(f"private_top_cards={state.peek_cards}")

        return "\n".join(lines)

    def action_to_name(self, action: str) -> str:
        if not isinstance(action, str):
            raise TypeError("Actions are represented by their stable names")
        return action

    def name_to_action(self, name: str) -> str:
        if not isinstance(name, str):
            raise TypeError("Action names must be strings")
        return name

    @staticmethod
    def _other_alive(state: GameState, player: int) -> list[int]:
        return [
            other
            for other, alive in enumerate(state.alive)
            if alive and other != player
        ]

    @staticmethod
    def _next_alive(state: GameState, player: int) -> int:
        for offset in range(1, state.num_players + 1):
            candidate = (player + offset) % state.num_players
            if state.alive[candidate]:
                return candidate
        return player

    @staticmethod
    def _clockwise_others(state: GameState, player: int) -> list[int]:
        result = []
        for offset in range(1, state.num_players):
            candidate = (player + offset) % state.num_players
            if state.alive[candidate]:
                result.append(candidate)
        return result

    @staticmethod
    def _clear_peek(state: GameState) -> None:
        state.peek_owner = None
        state.peek_cards = []

    @staticmethod
    def _remove_cards(
        state: GameState,
        player: int,
        cards: list[str],
    ) -> None:
        for card in cards:
            state.hands[player].remove(card)
            state.discard.append(card)

    def _play(self, state: GameState, action: str) -> None:
        player = state.active_player

        if action.startswith("play:wunsch:target:"):
            target = int(action.rsplit(":", 1)[1])
            self._remove_cards(state, player, [FAVOR])
            effect = {
                "kind": "favor",
                "actor": player,
                "target": target,
            }

        elif action.startswith("play:"):
            card = action[5:]
            self._remove_cards(state, player, [card])
            effect = {
                "kind": card,
                "actor": player,
            }

        elif action.startswith("pair:"):
            _, card, _, target_text = action.split(":")
            self._remove_cards(state, player, [card, card])
            effect = {
                "kind": "pair",
                "actor": player,
                "target": int(target_text),
            }

        elif action.startswith("triple:"):
            parts = action.split(":")
            card = parts[1]
            target = int(parts[3])
            requested = parts[5]
            self._remove_cards(state, player, [card, card, card])
            effect = {
                "kind": "triple",
                "actor": player,
                "target": target,
                "wanted": requested,
            }

        elif action.startswith("five:"):
            left, wanted = action.split(":take:")
            chosen = left[5:].split("+")
            self._remove_cards(state, player, chosen)
            effect = {
                "kind": "five",
                "actor": player,
                "wanted": wanted,
            }

        else:
            raise ValueError(f"Unknown play action: {action}")

        self._begin_effect(state, effect, player)

    def _begin_effect(
        self,
        state: GameState,
        effect: dict,
        last_actor: int,
    ) -> None:
        state.pending = {
            "effect": effect,
            "cancelled": False,
        }
        state.response_order = self._clockwise_others(state, last_actor)
        state.response_index = 0

        if state.response_order:
            state.phase = "reaction"
        else:
            self._resolve_pending(state)

    def _apply_reaction(self, state: GameState, action: str) -> None:
        if action == "play:noe":
            player = self.current_player(state)
            state.hands[player].remove(NOPE)
            state.discard.append(NOPE)

            assert state.pending is not None
            state.pending["cancelled"] = not state.pending["cancelled"]

            # Every Nope opens a fresh opportunity to counter it.
            state.response_order = self._clockwise_others(state, player)
            state.response_index = 0

            if not state.response_order:
                self._resolve_pending(state)
            return

        state.response_index += 1
        if state.response_index >= len(state.response_order):
            self._resolve_pending(state)

    def _resolve_pending(self, state: GameState) -> None:
        assert state.pending is not None
        pending = state.pending

        state.pending = None
        state.response_order = []
        state.response_index = 0
        state.phase = "play"

        if pending["cancelled"]:
            return

        effect = pending["effect"]
        kind = effect["kind"]
        actor = effect["actor"]

        if kind == ATTACK:
            if state.turn_debt > 1:
                # The current attacked turn ends; two further turns are added.
                state.turn_debt += 1
            else:
                state.active_player = self._next_alive(state, actor)
                state.turn_debt = 3
            self._clear_peek(state)

        elif kind == SKIP:
            # Hops ends all currently outstanding attacked turns.
            state.active_player = self._next_alive(state, actor)
            state.turn_debt = 1
            self._clear_peek(state)

        elif kind == SHUFFLE:
            state.rng.shuffle(state.deck)
            self._clear_peek(state)

        elif kind == SEE_FUTURE:
            state.peek_owner = actor
            state.peek_cards = list(reversed(state.deck[-3:]))

        elif kind == "favor":
            target = effect["target"]
            if state.hands[target]:
                state.phase = "give"
                state.give_actor = actor
                state.give_target = target

        elif kind == "pair":
            target = effect["target"]
            if state.hands[target]:
                index = state.rng.randrange(len(state.hands[target]))
                stolen = state.hands[target].pop(index)
                state.hands[actor].append(stolen)
                state.hands[actor].sort()

        elif kind == "triple":
            target = effect["target"]
            wanted = effect["wanted"]
            if wanted in state.hands[target]:
                state.hands[target].remove(wanted)
                state.hands[actor].append(wanted)
                state.hands[actor].sort()

        elif kind == "five":
            wanted = effect["wanted"]

            # Retrieve the uppermost matching copy.
            reverse_index = state.discard[::-1].index(wanted)
            index = len(state.discard) - 1 - reverse_index
            recovered = state.discard.pop(index)

            if recovered == EXPLODING:
                state.phase = "defuse"
            else:
                state.hands[actor].append(recovered)
                state.hands[actor].sort()

    def _apply_give(self, state: GameState, action: str) -> None:
        assert state.give_actor is not None
        assert state.give_target is not None

        card = action[5:]
        state.hands[state.give_target].remove(card)
        state.hands[state.give_actor].append(card)
        state.hands[state.give_actor].sort()

        state.give_actor = None
        state.give_target = None
        state.phase = "play"

    def _draw(self, state: GameState) -> None:
        if not state.deck:
            raise RuntimeError(
                "The draw pile became empty despite the source's guarantee"
            )

        card = state.deck.pop()

        if card == EXPLODING:
            state.phase = "defuse"
            return

        player = state.active_player
        state.hands[player].append(card)
        state.hands[player].sort()
        self._finish_subturn(state)

    def _apply_defuse(self, state: GameState, action: str) -> None:
        player = state.active_player

        if action == "defuse:decline":
            state.discard.append(EXPLODING)
            state.discard.extend(state.hands[player])
            state.hands[player].clear()
            state.alive[player] = False
            self._clear_peek(state)

            if self.is_terminal(state):
                state.phase = "terminal"
            else:
                state.phase = "play"
                state.active_player = self._next_alive(state, player)
                state.turn_debt = 1
            return

        position = int(action.rsplit(":", 1)[1])
        state.hands[player].remove(DEFUSE)
        state.discard.append(DEFUSE)
        state.deck.insert(position, EXPLODING)
        state.phase = "play"
        self._finish_subturn(state)

    def _finish_subturn(self, state: GameState) -> None:
        self._clear_peek(state)

        if state.turn_debt > 1:
            state.turn_debt -= 1
        else:
            state.active_player = self._next_alive(
                state,
                state.active_player,
            )
            state.turn_debt = 1


if __name__ == "__main__":
    game = Game(seed=7)
    state = game.initial_state()

    for _ in range(1000):
        if game.is_terminal(state):
            break

        actions = game.legal_actions(state)
        assert actions
        assert len(actions) == len(set(actions))

        for action in actions:
            name = game.action_to_name(action)
            assert game.name_to_action(name) == action

        # Drawing/declining first produces a short deterministic smoke game.
        game.apply_action(state, actions[0])

    assert game.is_terminal(state)
    assert sorted(game.returns(state)) == [-1, 1]
```