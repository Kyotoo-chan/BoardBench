Open questions / assumptions

- The 56-card total implies five four-card cat titles; three names are missing, so all five use neutral `Katzenkarte_1`–`Katzenkarte_5` labels.
- Missing Nö timing is modeled as an explicit response round. Each Nö toggles cancellation, allowing “Nö” to counter “Nö”; played cards remain discarded.
- An Angriff ends all remaining obligations of its player and gives the next player two turns.
- The omitted five-different-title combination is not implemented.
- A player may decline Entschärfung and explode. Reinsertion positions are explicit, though the public action necessarily reveals the chosen position.
- Runtime probes could not be executed because this workspace’s read-only policy rejected Python execution.

```python
"""Self-contained implementation based only on the supplied rulebook."""

from copy import deepcopy
from dataclasses import dataclass, field
import random


EXPLODING = "Exploding_Kitten"
DEFUSE = "Entschaerfung"
ATTACK = "Angriff"
SKIP = "Hops"
SHUFFLE = "Mischen"
SEE = "Blick_in_die_Zukunft"
FAVOR = "Wunsch"
NOPE = "Noe"

# The source gives 56 total cards and says cat cards occur four times per
# title. Its readable card list accounts for 36 other cards, implying five
# four-card cat titles, but not all five names are present.
CATS = tuple(f"Katzenkarte_{number}" for number in range(1, 6))

HAND_TITLES = (
    DEFUSE,
    ATTACK,
    SKIP,
    SHUFFLE,
    SEE,
    FAVOR,
    NOPE,
) + CATS


def _empty_hands(num_players):
    return [
        {title: 0 for title in HAND_TITLES}
        for _ in range(num_players)
    ]


@dataclass
class GameState:
    num_players: int
    hands: list
    deck: list
    discard: list
    alive: list
    player: int = 0
    phase: str = "play"
    turns_left: int = 1
    peeked: dict = field(default_factory=dict)
    pending: dict | None = None
    reaction_last: int | None = None
    reaction_passes: int = 0
    donor: int | None = None
    receiver: int | None = None
    rng: random.Random = field(
        default_factory=random.Random,
        repr=False,
    )


class Game:
    def __init__(self, num_players=2, seed=None):
        if not 2 <= num_players <= 5:
            raise ValueError("num_players must be between 2 and 5")
        self.num_players = num_players
        self.seed = seed

    def initial_state(self):
        rng = random.Random(self.seed)

        # Exploding Kittens and Entschärfung cards are initially set aside.
        draw_pool = (
            [ATTACK] * 4
            + [SKIP] * 4
            + [SHUFFLE] * 4
            + [SEE] * 5
            + [FAVOR] * 4
            + [NOPE] * 5
        )
        for cat in CATS:
            draw_pool.extend([cat] * 4)

        rng.shuffle(draw_pool)
        hands = _empty_hands(self.num_players)

        # Each player receives seven random cards and one Entschärfung.
        for player in range(self.num_players):
            hands[player][DEFUSE] = 1
            for _ in range(7):
                hands[player][draw_pool.pop()] += 1

        # For two players, the source explicitly says to add only two
        # Entschärfung cards. Otherwise all unused ones are added.
        extra_defuses = (
            2 if self.num_players == 2
            else 6 - self.num_players
        )

        deck = (
            draw_pool
            + [DEFUSE] * extra_defuses
            + [EXPLODING] * (self.num_players - 1)
        )
        rng.shuffle(deck)

        return GameState(
            num_players=self.num_players,
            hands=hands,
            deck=deck,
            discard=[],
            alive=[True] * self.num_players,
            rng=rng,
        )

    def current_player(self, state):
        return -1 if self.is_terminal(state) else state.player

    def legal_actions(self, state):
        if self.is_terminal(state):
            return []

        player = state.player
        hand = state.hands[player]

        if state.phase == "defuse":
            actions = ["explode"]
            if hand[DEFUSE] > 0:
                actions.extend(
                    f"defuse:insert_at:{position}"
                    for position in range(len(state.deck) + 1)
                )
            return actions

        if state.phase == "donate":
            return [
                f"give:{card}"
                for card in HAND_TITLES
                if hand[card] > 0
            ]

        if state.phase == "reaction":
            actions = ["react:pass"]
            if hand[NOPE] > 0:
                actions.append("react:nope")
            return actions

        actions = []
        if state.deck:
            actions.append("draw")

        for card in (ATTACK, SKIP, SHUFFLE, SEE):
            if hand[card] > 0:
                actions.append(f"play:{card}")

        if hand[FAVOR] > 0:
            for target in range(state.num_players):
                if (
                    target != player
                    and state.alive[target]
                    and self._hand_size(state, target) > 0
                ):
                    actions.append(
                        f"play:{FAVOR}:target:{target}"
                    )

        # Pairs may use any two cards with the same title.
        for card in HAND_TITLES:
            if hand[card] >= 2:
                for target in range(state.num_players):
                    if (
                        target != player
                        and state.alive[target]
                        and self._hand_size(state, target) > 0
                    ):
                        actions.append(
                            f"pair:{card}:target:{target}"
                        )

            # Triples name the requested title explicitly.
            if hand[card] >= 3:
                for target in range(state.num_players):
                    if target == player or not state.alive[target]:
                        continue
                    for requested in HAND_TITLES:
                        actions.append(
                            f"triple:{card}:target:{target}"
                            f":request:{requested}"
                        )

        return actions

    def apply_action(self, state, action):
        if action not in self.legal_actions(state):
            raise ValueError(f"illegal action: {action}")

        new_state = deepcopy(state)

        if new_state.phase == "defuse":
            self._apply_defuse(new_state, action)
        elif new_state.phase == "donate":
            self._apply_donation(new_state, action)
        elif new_state.phase == "reaction":
            self._apply_reaction(new_state, action)
        elif action == "draw":
            self._draw(new_state)
        else:
            self._begin_card_action(new_state, action)

        return new_state

    def is_terminal(self, state):
        return sum(state.alive) <= 1

    def returns(self, state):
        if not self.is_terminal(state):
            return [0] * state.num_players
        return [
            1 if state.alive[player] else -1
            for player in range(state.num_players)
        ]

    def render(self, state):
        if self.is_terminal(state):
            winner = next(
                (
                    player
                    for player, alive in enumerate(state.alive)
                    if alive
                ),
                None,
            )
            return (
                f"terminal; winner={winner}; "
                f"returns={self.returns(state)}"
            )

        player = state.player
        visible_hand = {
            card: count
            for card, count in state.hands[player].items()
            if count
        }
        hand_sizes = [
            sum(hand.values())
            for hand in state.hands
        ]
        parts = [
            f"player={player}",
            f"phase={state.phase}",
            f"turns_left={state.turns_left}",
            f"deck_size={len(state.deck)}",
            f"hand_sizes={hand_sizes}",
            f"your_hand={visible_hand}",
            f"alive={state.alive}",
        ]

        # Only the player who used Blick in die Zukunft sees their peek.
        if player in state.peeked:
            parts.append(f"your_peek={state.peeked[player]}")

        return "; ".join(parts)

    def action_to_name(self, action):
        if not isinstance(action, str):
            raise TypeError("actions are strings")
        return action

    def name_to_action(self, name):
        if not isinstance(name, str):
            raise TypeError("action names are strings")
        return name

    @staticmethod
    def _hand_size(state, player):
        return sum(state.hands[player].values())

    @staticmethod
    def _clear_peeks(state):
        state.peeked.clear()

    def _next_alive(self, state, after, exclude=None):
        for offset in range(1, state.num_players + 1):
            candidate = (after + offset) % state.num_players
            if (
                state.alive[candidate]
                and candidate != exclude
            ):
                return candidate
        raise RuntimeError("no eligible living player")

    def _finish_one_turn(self, state):
        state.turns_left -= 1

        # During an Angriff obligation, completing one turn leaves the same
        # player to begin the next required turn.
        if state.turns_left > 0:
            state.phase = "play"
            return

        state.player = self._next_alive(state, state.player)
        state.turns_left = 1
        state.phase = "play"

    def _draw(self, state):
        card = state.deck.pop(0)
        self._clear_peeks(state)

        if card != EXPLODING:
            state.hands[state.player][card] += 1
            self._finish_one_turn(state)
            return

        if state.hands[state.player][DEFUSE] > 0:
            state.phase = "defuse"
        else:
            self._explode(state)

    def _apply_defuse(self, state, action):
        if action == "explode":
            self._explode(state)
            return

        position = int(action.rsplit(":", 1)[1])
        state.hands[state.player][DEFUSE] -= 1
        state.discard.append(DEFUSE)
        state.deck.insert(position, EXPLODING)
        self._clear_peeks(state)
        self._finish_one_turn(state)

    def _explode(self, state):
        dead_player = state.player

        for card, count in state.hands[dead_player].items():
            state.discard.extend([card] * count)
            state.hands[dead_player][card] = 0

        state.discard.append(EXPLODING)
        state.alive[dead_player] = False
        state.peeked.pop(dead_player, None)

        if not self.is_terminal(state):
            state.player = self._next_alive(state, dead_player)
            state.turns_left = 1
            state.phase = "play"

    def _apply_donation(self, state, action):
        card = action.removeprefix("give:")
        state.hands[state.donor][card] -= 1
        state.hands[state.receiver][card] += 1
        state.player = state.receiver
        state.phase = "play"
        state.donor = None
        state.receiver = None

    def _begin_card_action(self, state, action):
        actor = state.player

        if action.startswith("play:"):
            parts = action.split(":")
            card = parts[1]
            state.hands[actor][card] -= 1
            state.discard.append(card)
            pending = {
                "kind": "single",
                "card": card,
                "actor": actor,
                "valid": True,
            }
            if card == FAVOR:
                pending["target"] = int(parts[3])

        elif action.startswith("pair:"):
            parts = action.split(":")
            card = parts[1]
            target = int(parts[3])
            state.hands[actor][card] -= 2
            state.discard.extend([card, card])
            pending = {
                "kind": "pair",
                "card": card,
                "target": target,
                "actor": actor,
                "valid": True,
            }

        else:
            parts = action.split(":")
            card = parts[1]
            target = int(parts[3])
            requested = parts[5]
            state.hands[actor][card] -= 3
            state.discard.extend([card, card, card])
            pending = {
                "kind": "triple",
                "card": card,
                "target": target,
                "requested": requested,
                "actor": actor,
                "valid": True,
            }

        # Missing reaction timing is represented by a response round among
        # every living player other than the last card player.
        state.pending = pending
        state.phase = "reaction"
        state.reaction_last = actor
        state.reaction_passes = 0
        state.player = self._next_alive(
            state,
            actor,
            exclude=actor,
        )

    def _apply_reaction(self, state, action):
        responder = state.player

        if action == "react:nope":
            state.hands[responder][NOPE] -= 1
            state.discard.append(NOPE)

            # The source's “Doch!” example is treated as permitting a Nö
            # against a Nö, so every Nö toggles the pending result.
            state.pending["valid"] = not state.pending["valid"]
            state.reaction_last = responder
            state.reaction_passes = 0
            state.player = self._next_alive(
                state,
                responder,
                exclude=responder,
            )
            return

        state.reaction_passes += 1
        required_passes = sum(state.alive) - 1

        if state.reaction_passes >= required_passes:
            self._resolve_pending(state)
        else:
            state.player = self._next_alive(
                state,
                responder,
                exclude=state.reaction_last,
            )

    def _resolve_pending(self, state):
        pending = state.pending
        actor = pending["actor"]

        state.pending = None
        state.reaction_last = None
        state.reaction_passes = 0
        state.player = actor
        state.phase = "play"

        if not pending["valid"]:
            return

        if pending["kind"] == "pair":
            target = pending["target"]
            target_cards = [
                card
                for card in HAND_TITLES
                for _ in range(state.hands[target][card])
            ]
            if target_cards:
                stolen = state.rng.choice(target_cards)
                state.hands[target][stolen] -= 1
                state.hands[actor][stolen] += 1
            return

        if pending["kind"] == "triple":
            target = pending["target"]
            requested = pending["requested"]
            if state.hands[target][requested] > 0:
                state.hands[target][requested] -= 1
                state.hands[actor][requested] += 1
            return

        card = pending["card"]

        if card == SEE:
            state.peeked[actor] = list(state.deck[:3])

        elif card == SHUFFLE:
            state.rng.shuffle(state.deck)
            self._clear_peeks(state)

        elif card == SKIP:
            self._finish_one_turn(state)

        elif card == ATTACK:
            # The detailed Angriff section is missing. The earlier text says
            # it ends the player's turn and makes the next player take two.
            state.player = self._next_alive(state, actor)
            state.turns_left = 2
            state.phase = "play"

        elif card == FAVOR:
            target = pending["target"]

            # The target could have spent their last card as a Nö while the
            # Wunsch was pending. In that case there is nothing to donate.
            if self._hand_size(state, target) > 0:
                state.player = target
                state.phase = "donate"
                state.donor = target
                state.receiver = actor
```