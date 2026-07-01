from dataclasses import dataclass, replace
from itertools import combinations
from collections import Counter

TERMINAL = -1
CHANCE = -2

EXPLODING = "Exploding Kitten"
DEFUSE = "Entschärfung"
ATTACK = "Angriff"
SKIP = "Hops!"
FAVOR = "Wunsch"
SHUFFLE = "Mischen"
SEE_FUTURE = "Blick in die Zukunft"
NOPE = "Nö!"

CAT1 = "Augenmampfende Zombiekatze"
CAT2 = "Katzenkarte 2"  # Assumption: name not visible in supplied text.
CAT3 = "Katzenkarte 3"
CAT4 = "Katzenkarte 4"
CAT5 = "Katzenkarte 5"

CARD_ORDER = (
    ATTACK, SKIP, FAVOR, SHUFFLE, SEE_FUTURE, NOPE, DEFUSE,
    CAT1, CAT2, CAT3, CAT4, CAT5, EXPLODING
)

CARD_COUNTS = {
    EXPLODING: 4,
    ATTACK: 4,
    SKIP: 4,
    FAVOR: 4,
    SHUFFLE: 4,
    SEE_FUTURE: 5,
    DEFUSE: 6,
    NOPE: 5,
    CAT1: 4,
    CAT2: 4,
    CAT3: 4,
    CAT4: 4,
    CAT5: 4,
}

TITLE_TO_CODE = {
    EXPLODING: "Exploding_Kitten",
    DEFUSE: "Entschaerfung",
    ATTACK: "Angriff",
    SKIP: "Hops",
    FAVOR: "Wunsch",
    SHUFFLE: "Mischen",
    SEE_FUTURE: "Blick_in_die_Zukunft",
    NOPE: "Noe",
    CAT1: "Augenmampfende_Zombiekatze",
    CAT2: "Katzenkarte_2",
    CAT3: "Katzenkarte_3",
    CAT4: "Katzenkarte_4",
    CAT5: "Katzenkarte_5",
}
CODE_TO_TITLE = {v: k for k, v in TITLE_TO_CODE.items()}


# Action names use lowercase TITLE_TO_CODE labels with BoardBench grammar
# prefixes. The separators below are not card-label substrings, so raw names
# and normalized comparison keys stay 1-to-1.
def _card_label(title):
    return TITLE_TO_CODE[title].lower()


def _title_from_label(label):
    normalized = str(label).strip().lower()
    for title, code in TITLE_TO_CODE.items():
        if code.lower() == normalized:
            return title
    raise ValueError("Unknown card label: %r" % (label,))


def _join_card_labels(titles):
    return "_and_".join(_card_label(t) for t in titles)


def _split_card_labels(text):
    parts = text.split("_and_")
    if not parts or any(part == "" for part in parts):
        raise ValueError("Bad card label list.")
    return tuple(_title_from_label(part) for part in parts)


@dataclass(frozen=True)
class GameState:
    num_players: int
    hands: tuple
    deck: tuple
    discard: tuple
    alive: tuple
    current: int
    phase: str = "main"
    turns_remaining: int = 1
    pending: tuple = None
    nope_count: int = 0
    nope_passes: int = 0
    peeked: tuple = ()
    history: tuple = ()


class Game:
    def __init__(self, num_players=4, start_player=0):
        if not 2 <= num_players <= 5:
            raise ValueError("Rules allow 2-5 players.")
        if not 0 <= start_player < num_players:
            raise ValueError("Invalid start player.")
        self.num_players = num_players
        self.start_player = start_player

    def initial_state(self):
        # Assumption: physical random setup shuffle is replaced by deterministic setup.
        base = []
        for title, count in CARD_COUNTS.items():
            if title not in (EXPLODING, DEFUSE):
                base.extend([title] * count)
        base = list(self._deterministic_setup_shuffle(tuple(base)))

        hands = [[] for _ in range(self.num_players)]
        pos = 0
        for _ in range(7):
            for p in range(self.num_players):
                hands[p].append(base[pos])
                pos += 1
        deck = list(base[pos:])

        for p in range(self.num_players):
            hands[p].append(DEFUSE)

        if self.num_players == 2:
            defuses_in_deck = 2
        else:
            defuses_in_deck = 6 - self.num_players

        kittens_in_deck = self.num_players - 1
        deck.extend([DEFUSE] * defuses_in_deck)
        deck.extend([EXPLODING] * kittens_in_deck)
        deck = self._deterministic_setup_shuffle(tuple(deck))

        return GameState(
            num_players=self.num_players,
            hands=tuple(self._sort_cards(h) for h in hands),
            deck=tuple(deck),
            discard=(),
            alive=tuple(True for _ in range(self.num_players)),
            current=self.start_player,
            phase="main",
            turns_remaining=1,
            pending=None,
            peeked=tuple(() for _ in range(self.num_players)),
        )

    def current_player(self, state):
        if self.is_terminal(state):
            return TERMINAL
        if state.phase in ("chance_shuffle", "chance_steal"):
            return CHANCE
        return state.current

    def legal_actions(self, state):
        if self.is_terminal(state):
            return []

        if state.phase in ("chance_shuffle", "chance_steal"):
            return [a for a, _ in self.chance_outcomes(state)]

        if state.phase == "insert_kitten":
            return [("insert", i) for i in range(len(state.deck) + 1)]

        if state.phase == "give_favor":
            hand = state.hands[state.current]
            return [("give", t) for t in self._unique_titles(hand)]

        if state.phase == "nope":
            actions = [("pass",)]
            actor = state.pending[1]
            # Initial Nope must answer another player's action; after one Nope, anyone may counter.
            if NOPE in state.hands[state.current]:
                if state.nope_count > 0 or state.current != actor:
                    actions.append(("nope",))
            return actions

        if state.phase != "main":
            return []

        p = state.current
        hand = state.hands[p]
        counts = Counter(hand)
        actions = []

        if state.deck:
            actions.append(("draw",))

        for title in (SEE_FUTURE, SKIP, ATTACK, SHUFFLE):
            if counts[title] >= 1:
                actions.append(("play", title))

        if counts[FAVOR] >= 1:
            for target in self._alive_others_with_cards(state, p):
                actions.append(("favor", target))

        for title in CARD_ORDER:
            if counts[title] >= 2:
                for target in self._alive_others_with_cards(state, p):
                    actions.append(("pair", title, target))

        requestable = [t for t in CARD_ORDER if t != EXPLODING]
        for title in CARD_ORDER:
            if counts[title] >= 3:
                for target in self._alive_others(state, p):
                    for requested in requestable:
                        actions.append(("triplet", title, target, requested))

        distinct = [t for t in CARD_ORDER if counts[t] >= 1]
        discard_titles = self._unique_titles(state.discard)
        if len(distinct) >= 5 and discard_titles:
            for played in combinations(distinct, 5):
                for take in discard_titles:
                    actions.append(("five", tuple(played), take))

        return actions

    def apply_action(self, state, action):
        if action not in self.legal_actions(state):
            raise ValueError("Illegal action: %r" % (action,))

        name = self.action_to_name(action)

        if state.phase == "main":
            ns = self._apply_main(state, action)
        elif state.phase == "nope":
            ns = self._apply_nope_phase(state, action)
        elif state.phase == "give_favor":
            ns = self._apply_give(state, action)
        elif state.phase == "insert_kitten":
            ns = self._apply_insert(state, action)
        elif state.phase == "chance_steal":
            ns = self._apply_chance_steal(state, action)
        elif state.phase == "chance_shuffle":
            ns = self._apply_chance_shuffle(state, action)
        else:
            raise ValueError("Unknown phase.")

        return replace(ns, history=ns.history + (name,))

    def is_terminal(self, state):
        return state.phase == "terminal" or sum(1 for x in state.alive if x) <= 1

    def returns(self, state):
        if not self.is_terminal(state):
            return [0.0] * state.num_players
        if sum(1 for x in state.alive if x) == 1:
            return [1.0 if alive else -1.0 for alive in state.alive]
        return [0.0] * state.num_players

    def render(self, state):
        cp = self.current_player(state)
        cp_s = "TERMINAL" if cp == TERMINAL else ("CHANCE" if cp == CHANCE else "P%d" % cp)
        lines = [
            "phase=%s current=%s turns=%d" % (state.phase, cp_s, state.turns_remaining),
            "alive=" + ",".join("P%d:%s" % (i, "alive" if a else "out") for i, a in enumerate(state.alive)),
            "deck[%d]=" % len(state.deck) + "|".join(state.deck),
            "discard[%d]=" % len(state.discard) + "|".join(state.discard),
        ]
        for p, hand in enumerate(state.hands):
            lines.append("P%d hand[%d]=%s" % (p, len(hand), self._format_counts(hand)))
        if any(state.peeked):
            lines.append("peeked=" + ";".join("P%d:%s" % (i, "|".join(v)) for i, v in enumerate(state.peeked) if v))
        if state.pending:
            lines.append("pending=" + self._pending_text(state.pending))
        if state.history:
            lines.append("history_tail=" + ";".join(state.history[-8:]))
        return "\n".join(lines)

    def action_to_name(self, action):
        k = action[0]
        if k == "draw":
            return "draw"
        if k == "pass":
            return "pass"
        if k == "nope":
            return "nope"
        if k == "play":
            return "remove:%s" % _card_label(action[1])
        if k == "favor":
            return "remove:%s_target_player%d" % (_card_label(FAVOR), action[1])
        if k == "pair":
            return "remove:pair_%s_target_player%d" % (_card_label(action[1]), action[2])
        if k == "triplet":
            return "remove:triplet_%s_target_player%d_request_%s" % (
                _card_label(action[1]), action[2], _card_label(action[3])
            )
        if k == "five":
            return "remove:five_%s_take_%s" % (
                _join_card_labels(action[1]),
                _card_label(action[2]),
            )
        if k == "give":
            return "move:hand_%s->favor_requester" % _card_label(action[1])
        if k == "insert":
            return "place:deck_pos_%d_%s" % (action[1], _card_label(EXPLODING))
        if k == "chance_steal":
            return "chance:steal:" + _card_label(action[1])
        if k == "chance_shuffle":
            return "chance:shuffle:" + action[1]
        raise ValueError("Unknown action.")

    def name_to_action(self, name):
        if name == "draw":
            return ("draw",)
        if name == "pass":
            return ("pass",)
        if name == "nope":
            return ("nope",)

        if name.startswith("remove:"):
            rest = name[len("remove:"):]

            favor_prefix = "%s_target_player" % _card_label(FAVOR)
            if rest.startswith(favor_prefix):
                return ("favor", int(rest[len(favor_prefix):]))

            if rest.startswith("pair_"):
                payload = rest[len("pair_"):]
                code, p = payload.rsplit("_target_player", 1)
                return ("pair", _title_from_label(code), int(p))

            if rest.startswith("triplet_"):
                payload = rest[len("triplet_"):]
                left, requested = payload.rsplit("_request_", 1)
                code, p = left.rsplit("_target_player", 1)
                return ("triplet", _title_from_label(code), int(p), _title_from_label(requested))

            if rest.startswith("five_"):
                payload = rest[len("five_"):]
                played_s, take_s = payload.rsplit("_take_", 1)
                return ("five", _split_card_labels(played_s), _title_from_label(take_s))

            return ("play", _title_from_label(rest))

        give_prefix = "move:hand_"
        give_suffix = "->favor_requester"
        if name.startswith(give_prefix) and name.endswith(give_suffix):
            code = name[len(give_prefix):-len(give_suffix)]
            return ("give", _title_from_label(code))

        insert_prefix = "place:deck_pos_"
        insert_suffix = "_" + _card_label(EXPLODING)
        if name.startswith(insert_prefix) and name.endswith(insert_suffix):
            pos_s = name[len(insert_prefix):-len(insert_suffix)]
            return ("insert", int(pos_s))

        steal_prefix = "chance:steal:"
        if name.startswith(steal_prefix):
            return ("chance_steal", _title_from_label(name[len(steal_prefix):]))

        shuffle_prefix = "chance:shuffle:"
        if name.startswith(shuffle_prefix):
            return ("chance_shuffle", name[len(shuffle_prefix):])

        raise ValueError("Cannot parse action name.")

    def chance_outcomes(self, state):
        if state.phase == "chance_steal":
            _, actor, target = state.pending
            hand = state.hands[target]
            total = len(hand)
            counts = Counter(hand)
            return [(("chance_steal", t), counts[t] / total) for t in CARD_ORDER if counts[t]]

        if state.phase == "chance_shuffle":
            methods = ("keep", "reverse", "cut1", "cut_half", "even_then_odd")
            seen = {}
            for m in methods:
                new_deck = self._shuffle_method(state.deck, m)
                if new_deck not in seen:
                    seen[new_deck] = m
            actions = [("chance_shuffle", m) for m in seen.values()]
            p = 1.0 / len(actions)
            return [(a, p) for a in actions]

        return []

    def information_state(self, state, player):
        # Player-visible approximation: own hand, public discard, sizes, alive flags, and own peek.
        parts = [
            "player=P%d" % player,
            "phase=%s current=%s" % (state.phase, self.current_player(state)),
            "alive=" + ",".join("P%d:%s" % (i, "alive" if a else "out") for i, a in enumerate(state.alive)),
            "deck_size=%d" % len(state.deck),
            "discard=" + "|".join(state.discard),
        ]
        for p, hand in enumerate(state.hands):
            if p == player:
                parts.append("P%d_hand=%s" % (p, self._format_counts(hand)))
            else:
                parts.append("P%d_hand_size=%d" % (p, len(hand)))
        if state.peeked[player]:
            parts.append("peek_top=" + "|".join(state.peeked[player]))
        return "\n".join(parts)

    # ----- transition helpers -----

    def _apply_main(self, state, action):
        p = state.current
        k = action[0]

        if k == "draw":
            return self._draw_card(state)

        if k == "play":
            title = action[1]
            state = self._move_from_hand_to_discard(state, p, title, 1)
            return self._start_counterable(state, (title, p))

        if k == "favor":
            target = action[1]
            state = self._move_from_hand_to_discard(state, p, FAVOR, 1)
            return self._start_counterable(state, ("favor", p, target))

        if k == "pair":
            title, target = action[1], action[2]
            state = self._move_from_hand_to_discard(state, p, title, 2)
            return self._start_counterable(state, ("pair", p, target))

        if k == "triplet":
            title, target, requested = action[1], action[2], action[3]
            state = self._move_from_hand_to_discard(state, p, title, 3)
            return self._start_counterable(state, ("triplet", p, target, requested))

        if k == "five":
            played, take = action[1], action[2]
            for title in played:
                state = self._move_from_hand_to_discard(state, p, title, 1)
            # Assumption: chosen card must already have been in discard before the combo resolved.
            return self._start_counterable(state, ("five", p, take))

        raise ValueError("Bad main action.")

    def _start_counterable(self, state, pending):
        actor = pending[1]
        if any(state.alive[p] and p != actor and NOPE in state.hands[p] for p in range(state.num_players)):
            return replace(
                state,
                phase="nope",
                current=self._next_alive(state.alive, actor),
                pending=pending,
                nope_count=0,
                nope_passes=0,
            )
        return self._resolve_pending(state, pending, canceled=False)

    def _apply_nope_phase(self, state, action):
        if action[0] == "pass":
            required = (sum(state.alive) - 1) if state.nope_count == 0 else sum(state.alive)
            passes = state.nope_passes + 1
            if passes >= required:
                return self._resolve_pending(state, state.pending, canceled=(state.nope_count % 2 == 1))
            return replace(state, current=self._next_alive(state.alive, state.current), nope_passes=passes)

        if action[0] == "nope":
            p = state.current
            state = self._move_from_hand_to_discard(state, p, NOPE, 1)
            nope_count = state.nope_count + 1
            state = replace(
                state,
                nope_count=nope_count,
                nope_passes=0,
                current=self._next_alive(state.alive, p),
            )
            if not any(state.alive[i] and NOPE in state.hands[i] for i in range(state.num_players)):
                return self._resolve_pending(state, state.pending, canceled=(nope_count % 2 == 1))
            return state

        raise ValueError("Bad Nope phase action.")

    def _resolve_pending(self, state, pending, canceled):
        actor = pending[1]
        base = replace(state, phase="main", current=actor, pending=None, nope_count=0, nope_passes=0)

        if canceled:
            return base

        kind = pending[0]

        if kind == SEE_FUTURE:
            peeked = list(base.peeked)
            peeked[actor] = tuple(base.deck[:3])
            return replace(base, peeked=tuple(peeked))

        if kind == SKIP:
            return self._finish_one_turn(base)

        if kind == ATTACK:
            nxt = self._next_alive(base.alive, actor)
            return replace(base, current=nxt, turns_remaining=2, phase="main")

        if kind == SHUFFLE:
            return replace(base, phase="chance_shuffle", current=CHANCE, pending=("shuffle", actor))

        if kind == "favor":
            _, _, target = pending
            return replace(base, phase="give_favor", current=target, pending=("favor_give", actor, target))

        if kind == "pair":
            _, _, target = pending
            if not base.hands[target]:
                return base
            return replace(base, phase="chance_steal", current=CHANCE, pending=("steal", actor, target))

        if kind == "triplet":
            _, _, target, requested = pending
            if requested in base.hands[target]:
                hands = [list(h) for h in base.hands]
                hands[target].remove(requested)
                hands[actor].append(requested)
                return replace(base, hands=tuple(self._sort_cards(h) for h in hands))
            return base

        if kind == "five":
            _, _, take = pending
            if take in base.discard:
                discard = list(base.discard)
                discard.remove(take)
                hands = [list(h) for h in base.hands]
                hands[actor].append(take)
                return replace(base, hands=tuple(self._sort_cards(h) for h in hands), discard=tuple(discard))
            return base

        raise ValueError("Unknown pending effect.")

    def _apply_give(self, state, action):
        title = action[1]
        _, actor, target = state.pending
        hands = [list(h) for h in state.hands]
        hands[target].remove(title)
        hands[actor].append(title)
        return replace(
            state,
            hands=tuple(self._sort_cards(h) for h in hands),
            phase="main",
            current=actor,
            pending=None,
        )

    def _apply_chance_steal(self, state, action):
        title = action[1]
        _, actor, target = state.pending
        hands = [list(h) for h in state.hands]
        hands[target].remove(title)
        hands[actor].append(title)
        return replace(
            state,
            hands=tuple(self._sort_cards(h) for h in hands),
            phase="main",
            current=actor,
            pending=None,
        )

    def _apply_chance_shuffle(self, state, action):
        method = action[1]
        _, actor = state.pending
        return replace(
            state,
            deck=self._shuffle_method(state.deck, method),
            phase="main",
            current=actor,
            pending=None,
            peeked=tuple(() for _ in range(state.num_players)),
        )

    def _apply_insert(self, state, action):
        pos = action[1]
        deck = list(state.deck)
        deck.insert(pos, EXPLODING)
        state = replace(
            state,
            deck=tuple(deck),
            phase="main",
            pending=None,
            peeked=tuple(() for _ in range(state.num_players)),
        )
        return self._finish_one_turn(state)

    def _draw_card(self, state):
        p = state.current
        card = state.deck[0]
        deck = state.deck[1:]
        state = replace(state, deck=deck, peeked=tuple(() for _ in range(state.num_players)))

        if card == EXPLODING:
            if DEFUSE in state.hands[p]:
                state = self._move_from_hand_to_discard(state, p, DEFUSE, 1)
                return replace(state, phase="insert_kitten", current=p)
            hands = [list(h) for h in state.hands]
            discard = list(state.discard)
            discard.extend(hands[p])
            discard.append(EXPLODING)
            hands[p] = []
            alive = list(state.alive)
            alive[p] = False
            state = replace(
                state,
                hands=tuple(self._sort_cards(h) for h in hands),
                discard=tuple(discard),
                alive=tuple(alive),
            )
            if sum(alive) <= 1:
                return replace(state, phase="terminal", current=TERMINAL)
            return replace(state, current=self._next_alive(tuple(alive), p), turns_remaining=1, phase="main")

        hands = [list(h) for h in state.hands]
        hands[p].append(card)
        state = replace(state, hands=tuple(self._sort_cards(h) for h in hands))
        return self._finish_one_turn(state)

    def _finish_one_turn(self, state):
        p = state.current
        if sum(state.alive) <= 1:
            return replace(state, phase="terminal", current=TERMINAL)
        if state.turns_remaining > 1 and state.alive[p]:
            return replace(state, phase="main", current=p, turns_remaining=state.turns_remaining - 1, pending=None)
        return replace(
            state,
            phase="main",
            current=self._next_alive(state.alive, p),
            turns_remaining=1,
            pending=None,
        )

    # ----- utility helpers -----

    def _move_from_hand_to_discard(self, state, player, title, n):
        hands = [list(h) for h in state.hands]
        for _ in range(n):
            hands[player].remove(title)
        discard = state.discard + tuple([title] * n)
        return replace(state, hands=tuple(self._sort_cards(h) for h in hands), discard=discard)

    def _next_alive(self, alive, after):
        n = len(alive)
        for step in range(1, n + 1):
            p = (after + step) % n
            if alive[p]:
                return p
        return TERMINAL

    def _alive_others(self, state, p):
        return [i for i in range(state.num_players) if i != p and state.alive[i]]

    def _alive_others_with_cards(self, state, p):
        return [i for i in self._alive_others(state, p) if len(state.hands[i]) > 0]

    def _sort_cards(self, cards):
        order = {t: i for i, t in enumerate(CARD_ORDER)}
        return tuple(sorted(cards, key=lambda c: order[c]))

    def _unique_titles(self, cards):
        counts = Counter(cards)
        return [t for t in CARD_ORDER if counts[t] > 0]

    def _format_counts(self, cards):
        counts = Counter(cards)
        parts = []
        for t in CARD_ORDER:
            if counts[t]:
                parts.append("%sx%d" % (t, counts[t]))
        return ",".join(parts) if parts else "-"

    def _pending_text(self, pending):
        return ":".join(str(x) for x in pending)

    def _deterministic_setup_shuffle(self, deck):
        # Deterministic replacement for the rulebook's physical shuffle.
        if not deck:
            return ()
        deck = tuple(deck)
        return self._shuffle_method(self._shuffle_method(deck, "even_then_odd"), "reverse")

    def _shuffle_method(self, deck, method):
        deck = tuple(deck)
        if method == "keep":
            return deck
        if method == "reverse":
            return tuple(reversed(deck))
        if method == "cut1":
            return deck[1:] + deck[:1] if deck else deck
        if method == "cut_half":
            k = len(deck) // 2
            return deck[k:] + deck[:k]
        if method == "even_then_odd":
            return deck[::2] + deck[1::2]
        raise ValueError("Unknown shuffle method.")
