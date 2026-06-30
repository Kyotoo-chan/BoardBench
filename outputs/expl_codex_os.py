from collections import Counter
from dataclasses import dataclass
from itertools import combinations

TERMINAL = -1
CHANCE = -2

EXPLODING_KITTEN = "exploding_kitten"
DEFUSE = "entschaerfung"
ATTACK = "angriff"
SKIP = "hops"
FAVOR = "wunsch"
SHUFFLE = "mischen"
SEE_FUTURE = "blick_in_die_zukunft"
NOPE = "noe"

CAT_ZOMBIE = "augenmampfende_zombiekatze"
CAT_UNNAMED_2 = "katzenkarte_unbenannt_2"
CAT_UNNAMED_3 = "katzenkarte_unbenannt_3"
CAT_UNNAMED_4 = "katzenkarte_unbenannt_4"
CAT_UNNAMED_5 = "katzenkarte_unbenannt_5"

CAT_CARDS = (
    CAT_ZOMBIE,
    CAT_UNNAMED_2,
    CAT_UNNAMED_3,
    CAT_UNNAMED_4,
    CAT_UNNAMED_5,
)

CARD_TITLES = (
    EXPLODING_KITTEN,
    DEFUSE,
    ATTACK,
    SKIP,
    FAVOR,
    SHUFFLE,
    SEE_FUTURE,
    NOPE,
) + CAT_CARDS

REQUESTABLE_CARDS = tuple(c for c in CARD_TITLES if c != EXPLODING_KITTEN)
CARD_ORDER = {card: i for i, card in enumerate(CARD_TITLES)}

CARD_LABELS = {
    EXPLODING_KITTEN: "Exploding Kitten",
    DEFUSE: "Entschaerfung",
    ATTACK: "Angriff",
    SKIP: "Hops",
    FAVOR: "Wunsch",
    SHUFFLE: "Mischen",
    SEE_FUTURE: "Blick in die Zukunft",
    NOPE: "Noe",
    CAT_ZOMBIE: "Augenmampfende Zombiekatze",
    CAT_UNNAMED_2: "Katzenkarte unbenannt 2",
    CAT_UNNAMED_3: "Katzenkarte unbenannt 3",
    CAT_UNNAMED_4: "Katzenkarte unbenannt 4",
    CAT_UNNAMED_5: "Katzenkarte unbenannt 5",
}


@dataclass(frozen=True)
class GameState:
    hands: tuple
    deck: tuple
    discard: tuple
    alive: tuple
    current: int
    turns_remaining: int = 1
    phase: str = "main"
    pending: tuple = ()
    history: tuple = ()


def _sort_cards(cards):
    return tuple(sorted(cards, key=lambda c: (CARD_ORDER.get(c, 999), c)))


def _unique_cards(cards):
    return tuple(sorted(Counter(cards), key=lambda c: (CARD_ORDER.get(c, 999), c)))


def _remove_one(cards, card):
    items = list(cards)
    items.remove(card)
    return tuple(items)


def _remove_n(cards, card, count):
    result = tuple(cards)
    for _ in range(count):
        result = _remove_one(result, card)
    return result


def _add_one(cards, card):
    return _sort_cards(tuple(cards) + (card,))


def _replace_hand(hands, player, new_hand):
    hands = list(hands)
    hands[player] = _sort_cards(new_hand)
    return tuple(hands)


def _stable_value(text):
    return sum((i + 1) * ord(ch) for i, ch in enumerate(text))


def _canonical_shuffle(cards):
    """Deterministic stand-in for shuffling; no random module is used."""
    cards = tuple(cards)
    n = len(cards)
    decorated = []
    for i, card in enumerate(cards):
        key = ((_stable_value(card) * 37 + (i + 1) * 101 + n * 17) % (n * n + 97), i)
        decorated.append((key, card))
    return tuple(card for key, card in sorted(decorated))


def _position_name(pos, deck_len):
    if pos == 0:
        return "pos0_top"
    if pos == deck_len:
        return f"pos{pos}_bottom"
    return f"pos{pos}"


def _parse_position(token):
    if not token.startswith("pos"):
        raise ValueError(f"bad position: {token}")
    digits = []
    for ch in token[3:]:
        if ch.isdigit():
            digits.append(ch)
        else:
            break
    if not digits:
        raise ValueError(f"bad position: {token}")
    return int("".join(digits))


def _counts_text(cards):
    counts = Counter(cards)
    if not counts:
        return "empty"
    parts = []
    for card in sorted(counts, key=lambda c: (CARD_ORDER.get(c, 999), c)):
        parts.append(f"{card}={counts[card]}")
    return ",".join(parts)


class Game:
    def __init__(self, num_players=2, start_player=0):
        if not 2 <= num_players <= 5:
            raise ValueError("rule text supports 2 to 5 players")
        if not 0 <= start_player < num_players:
            raise ValueError("bad start_player")
        self.num_players = num_players
        self.start_player = start_player

    def initial_state(self):
        cards = []
        cards += [ATTACK] * 4
        cards += [SKIP] * 4
        cards += [FAVOR] * 4
        cards += [SHUFFLE] * 4
        cards += [SEE_FUTURE] * 5
        cards += [NOPE] * 5
        for cat in CAT_CARDS:
            cards += [cat] * 4

        cards = list(_canonical_shuffle(cards))
        hands = [[] for _ in range(self.num_players)]
        index = 0
        for _ in range(7):
            for player in range(self.num_players):
                hands[player].append(cards[index])
                index += 1

        deck = list(cards[index:])
        for player in range(self.num_players):
            hands[player].append(DEFUSE)

        extra_defuses = 2 if self.num_players == 2 else 6 - self.num_players
        deck += [DEFUSE] * extra_defuses
        deck += [EXPLODING_KITTEN] * (self.num_players - 1)
        deck = _canonical_shuffle(deck)

        return GameState(
            hands=tuple(_sort_cards(hand) for hand in hands),
            deck=deck,
            discard=(),
            alive=tuple(True for _ in range(self.num_players)),
            current=self.start_player,
            turns_remaining=1,
            phase="main",
            pending=(),
            history=("setup:canonical",),
        )

    def current_player(self, state):
        if self.is_terminal(state):
            return TERMINAL
        if state.phase == "steal_chance":
            return CHANCE
        return state.current

    def legal_actions(self, state):
        if self.is_terminal(state):
            return []

        if state.phase == "steal_chance":
            return [action for action, probability in self.chance_outcomes(state)]

        if state.phase == "defuse":
            return [
                f"defuse:insert:{_position_name(pos, len(state.deck))}"
                for pos in range(len(state.deck) + 1)
            ]

        if state.phase == "give":
            hand = state.hands[state.current]
            cards = _unique_cards(hand)
            return [f"give:{card}" for card in cards] if cards else ["give:none"]

        player = state.current
        hand = state.hands[player]
        counts = Counter(hand)
        actions = []

        if state.deck:
            actions.append("draw")

        for card in (SKIP, ATTACK, SHUFFLE, SEE_FUTURE):
            if counts[card] > 0:
                actions.append(f"play:{card}")

        for target in self._other_alive_players(state, player):
            if counts[FAVOR] > 0 and state.hands[target]:
                actions.append(f"play:{FAVOR}:target:p{target}")

        for card in _unique_cards(hand):
            if counts[card] >= 2:
                for target in self._other_alive_players(state, player):
                    if state.hands[target]:
                        actions.append(f"combo:pair:{card}:target:p{target}")

            if counts[card] >= 3:
                for target in self._other_alive_players(state, player):
                    for wanted in REQUESTABLE_CARDS:
                        actions.append(f"combo:triple:{card}:target:p{target}:want:{wanted}")

        distinct = _unique_cards(hand)
        discard_cards = _unique_cards(state.discard)
        if len(distinct) >= 5 and discard_cards:
            for selected in combinations(distinct, 5):
                selected_name = "+".join(selected)
                for take in discard_cards:
                    actions.append(f"combo:five:{selected_name}:take:{take}")

        return actions

    def apply_action(self, state, action):
        if action not in self.legal_actions(state):
            raise ValueError(f"illegal action: {action}")

        if state.phase == "defuse":
            return self._apply_defuse(state, action)
        if state.phase == "give":
            return self._apply_give(state, action)
        if state.phase == "steal_chance":
            return self._apply_steal_chance(state, action)

        if action == "draw":
            return self._apply_draw(state)

        if action.startswith("play:"):
            return self._apply_single_card(state, action)

        if action.startswith("combo:pair:"):
            return self._apply_pair(state, action)

        if action.startswith("combo:triple:"):
            return self._apply_triple(state, action)

        if action.startswith("combo:five:"):
            return self._apply_five(state, action)

        raise ValueError(f"unhandled action: {action}")

    def is_terminal(self, state):
        return sum(1 for alive in state.alive if alive) <= 1

    def returns(self, state):
        if not self.is_terminal(state):
            return [0.0 for _ in range(self.num_players)]
        if any(state.alive):
            return [1.0 if alive else -1.0 for alive in state.alive]
        return [-1.0 for _ in range(self.num_players)]

    def render(self, state):
        lines = [
            f"phase={state.phase}",
            f"current={self.current_player(state)}",
            f"turns_remaining={state.turns_remaining}",
            "alive=" + ",".join(f"p{i}:{int(v)}" for i, v in enumerate(state.alive)),
            "deck_top_to_bottom=" + ",".join(state.deck),
            "discard=" + _counts_text(state.discard),
        ]
        for player, hand in enumerate(state.hands):
            lines.append(f"hand:p{player}=" + _counts_text(hand))
        if state.pending:
            lines.append("pending=" + repr(state.pending))
        if state.history:
            lines.append("history_tail=" + " | ".join(state.history[-6:]))
        return "\n".join(lines)

    def action_to_name(self, action):
        if not isinstance(action, str):
            raise TypeError("actions are canonical strings")
        return action

    def name_to_action(self, name):
        if not isinstance(name, str):
            raise TypeError("action names are strings")
        return name

    def chance_outcomes(self, state):
        if self.is_terminal(state) or state.phase != "steal_chance":
            return []
        _, receiver, target = state.pending
        hand = state.hands[target]
        if not hand:
            return [("chance:steal:none", 1.0)]
        counts = Counter(hand)
        total = float(len(hand))
        return [
            (f"chance:steal:{card}", counts[card] / total)
            for card in sorted(counts, key=lambda c: (CARD_ORDER.get(c, 999), c))
        ]

    def information_state(self, state, player):
        if not 0 <= player < self.num_players:
            raise ValueError("bad player")
        lines = [
            f"player=p{player}",
            f"phase={state.phase}",
            f"current={self.current_player(state)}",
            f"turns_remaining={state.turns_remaining}",
            "alive=" + ",".join(f"p{i}:{int(v)}" for i, v in enumerate(state.alive)),
            f"deck_count={len(state.deck)}",
            "discard=" + _counts_text(state.discard),
            "own_hand=" + _counts_text(state.hands[player]),
        ]
        return "\n".join(lines)

    def _other_alive_players(self, state, player):
        return [p for p, alive in enumerate(state.alive) if alive and p != player]

    def _next_alive(self, alive, after_player):
        for offset in range(1, self.num_players + 1):
            candidate = (after_player + offset) % self.num_players
            if alive[candidate]:
                return candidate
        return TERMINAL

    def _finish_one_turn(self, state, hands, deck, discard, alive, history):
        if sum(1 for value in alive if value) <= 1:
            return GameState(hands, deck, discard, alive, TERMINAL, 0, "terminal", (), history)

        if alive[state.current] and state.turns_remaining > 1:
            return GameState(
                hands, deck, discard, alive, state.current,
                state.turns_remaining - 1, "main", (), history
            )

        next_player = self._next_alive(alive, state.current)
        return GameState(hands, deck, discard, alive, next_player, 1, "main", (), history)

    def _apply_draw(self, state):
        player = state.current
        card = state.deck[0]
        deck = state.deck[1:]
        hand = state.hands[player]
        history = state.history + (f"p{player}:draw:{card}",)

        if card == EXPLODING_KITTEN:
            if DEFUSE in hand:
                return GameState(
                    state.hands, deck, state.discard, state.alive,
                    player, state.turns_remaining, "defuse",
                    ("drawn_exploding_kitten",), history
                )

            hands = _replace_hand(state.hands, player, ())
            discard = state.discard + tuple(hand) + (EXPLODING_KITTEN,)
            alive = list(state.alive)
            alive[player] = False
            alive = tuple(alive)
            if sum(1 for value in alive if value) <= 1:
                return GameState(hands, deck, discard, alive, TERMINAL, 0, "terminal", (), history)
            next_player = self._next_alive(alive, player)
            return GameState(hands, deck, discard, alive, next_player, 1, "main", (), history)

        hands = _replace_hand(state.hands, player, _add_one(hand, card))
        return self._finish_one_turn(state, hands, deck, state.discard, state.alive, history)

    def _apply_defuse(self, state, action):
        player = state.current
        token = action.split(":")[-1]
        pos = _parse_position(token)
        deck = state.deck[:pos] + (EXPLODING_KITTEN,) + state.deck[pos:]
        hand = _remove_one(state.hands[player], DEFUSE)
        hands = _replace_hand(state.hands, player, hand)
        discard = state.discard + (DEFUSE,)
        history = state.history + (f"p{player}:{action}",)
        return self._finish_one_turn(state, hands, deck, discard, state.alive, history)

    def _apply_single_card(self, state, action):
        player = state.current
        card = action.split(":")[1]
        hand = _remove_one(state.hands[player], card)
        hands = _replace_hand(state.hands, player, hand)
        discard = state.discard + (card,)
        history = state.history + (f"p{player}:{action}",)

        if card == SKIP:
            return self._finish_one_turn(state, hands, state.deck, discard, state.alive, history)

        if card == ATTACK:
            if sum(1 for value in state.alive if value) <= 1:
                return GameState(hands, state.deck, discard, state.alive, TERMINAL, 0, "terminal", (), history)
            target = self._next_alive(state.alive, player)
            return GameState(hands, state.deck, discard, state.alive, target, 2, "main", (), history)

        if card == SHUFFLE:
            return GameState(
                hands, _canonical_shuffle(state.deck), discard, state.alive,
                player, state.turns_remaining, "main", (), history
            )

        if card == SEE_FUTURE:
            return GameState(
                hands, state.deck, discard, state.alive,
                player, state.turns_remaining, "main", (), history
            )

        if card == FAVOR:
            target = int(action.split(":target:p")[1])
            return GameState(
                hands, state.deck, discard, state.alive,
                target, state.turns_remaining, "give", ("wunsch", player), history
            )

        raise ValueError(f"unsupported single card: {card}")

    def _apply_give(self, state, action):
        receiver = state.pending[1]
        giver = state.current
        card = action.split(":", 1)[1]
        hands = state.hands
        if card != "none":
            giver_hand = _remove_one(hands[giver], card)
            receiver_hand = _add_one(hands[receiver], card)
            hands = _replace_hand(hands, giver, giver_hand)
            hands = _replace_hand(hands, receiver, receiver_hand)
        history = state.history + (f"p{giver}:{action}:to:p{receiver}",)
        return GameState(
            hands, state.deck, state.discard, state.alive,
            receiver, state.turns_remaining, "main", (), history
        )

    def _apply_pair(self, state, action):
        player = state.current
        parts = action.split(":")
        card = parts[2]
        target = int(parts[4][1:])
        hand = _remove_n(state.hands[player], card, 2)
        hands = _replace_hand(state.hands, player, hand)
        discard = state.discard + (card, card)
        history = state.history + (f"p{player}:{action}",)
        return GameState(
            hands, state.deck, discard, state.alive,
            player, state.turns_remaining, "steal_chance",
            ("steal", player, target), history
        )

    def _apply_steal_chance(self, state, action):
        _, receiver, target = state.pending
        card = action.split("chance:steal:", 1)[1]
        hands = state.hands
        if card != "none":
            target_hand = _remove_one(hands[target], card)
            receiver_hand = _add_one(hands[receiver], card)
            hands = _replace_hand(hands, target, target_hand)
            hands = _replace_hand(hands, receiver, receiver_hand)
        history = state.history + (action,)
        return GameState(
            hands, state.deck, state.discard, state.alive,
            receiver, state.turns_remaining, "main", (), history
        )

    def _apply_triple(self, state, action):
        player = state.current
        parts = action.split(":")
        card = parts[2]
        target = int(parts[4][1:])
        wanted = parts[6]

        hand = _remove_n(state.hands[player], card, 3)
        hands = _replace_hand(state.hands, player, hand)
        discard = state.discard + (card, card, card)

        if wanted in hands[target]:
            target_hand = _remove_one(hands[target], wanted)
            player_hand = _add_one(hands[player], wanted)
            hands = _replace_hand(hands, target, target_hand)
            hands = _replace_hand(hands, player, player_hand)

        history = state.history + (f"p{player}:{action}",)
        return GameState(
            hands, state.deck, discard, state.alive,
            player, state.turns_remaining, "main", (), history
        )

    def _apply_five(self, state, action):
        player = state.current
        rest = action[len("combo:five:"):]
        selected_text, take = rest.split(":take:")
        selected = tuple(selected_text.split("+"))

        hand = state.hands[player]
        for card in selected:
            hand = _remove_one(hand, card)

        discard = _remove_one(state.discard, take)
        discard = discard + selected
        hand = _add_one(hand, take)
        hands = _replace_hand(state.hands, player, hand)

        history = state.history + (f"p{player}:{action}",)
        return GameState(
            hands, state.deck, discard, state.alive,
            player, state.turns_remaining, "main", (), history
        )
