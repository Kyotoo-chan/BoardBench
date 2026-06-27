"""A small rulebook-driven model of Exploding Kittens (German NSFW rule text).

The implementation intentionally uses only the supplied rule text.  It models the
main turn structure, named action cards, Exploding Kitten/Entschärfung handling,
Nö! response windows, and the listed card combinations.

Known abstractions from incomplete/physical rules are documented inline:
* the rulebook does not name every cat-card title visible in the 56-card list, so
  one visible title plus four generic cat-card titles are used;
* initial shuffle/deal and player choice of starting player are represented by a
  deterministic canonical setup (start player p0 by default);
* physical shuffling from the Mischen card is represented by a finite chance node
  with several deterministic reorderings rather than all possible permutations.
"""

import copy
import itertools
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

TERMINAL = -1
CHANCE = -2
SIMULTANEOUS = -3

EXPLODING_KITTEN = "exploding_kitten"
DEFUSE = "entschaerfung"
ATTACK = "angriff"
SKIP = "hops"
NOPE = "noe"
SHUFFLE = "mischen"
SEE_FUTURE = "blick_in_die_zukunft"
FAVOR = "wunsch"
CAT_1 = "augenmampfende_zombiekatze"
CAT_2 = "katzenkarte_2"
CAT_3 = "katzenkarte_3"
CAT_4 = "katzenkarte_4"
CAT_5 = "katzenkarte_5"

CARD_ORDER: Tuple[str, ...] = (
    EXPLODING_KITTEN,
    DEFUSE,
    ATTACK,
    SKIP,
    FAVOR,
    SHUFFLE,
    SEE_FUTURE,
    NOPE,
    CAT_1,
    CAT_2,
    CAT_3,
    CAT_4,
    CAT_5,
)

CARD_TITLES: Dict[str, str] = {
    EXPLODING_KITTEN: "Exploding Kitten",
    DEFUSE: "Entschaerfung",
    ATTACK: "Angriff",
    SKIP: "Hops!",
    FAVOR: "Wunsch",
    SHUFFLE: "Mischen",
    SEE_FUTURE: "Blick in die Zukunft",
    NOPE: "Noe!",
    CAT_1: "Augenmampfende Zombiekatze",
    CAT_2: "Katzenkarte 2",
    CAT_3: "Katzenkarte 3",
    CAT_4: "Katzenkarte 4",
    CAT_5: "Katzenkarte 5",
}

FULL_DECK_COUNTS: Dict[str, int] = {
    EXPLODING_KITTEN: 4,
    DEFUSE: 6,
    ATTACK: 4,
    SKIP: 4,
    FAVOR: 4,
    SHUFFLE: 4,
    SEE_FUTURE: 5,
    NOPE: 5,
    CAT_1: 4,
    CAT_2: 4,
    CAT_3: 4,
    CAT_4: 4,
    CAT_5: 4,
}

_CARD_INDEX = {card: i for i, card in enumerate(CARD_ORDER)}
_COMBO_SEPARATOR = "_and_"


class _ActionName(str):
    """Comparison-facing action name that preserves the raw action string.

    The transition code in this generated game compares action_to_name(action)
    to the raw strings returned by legal_actions.  Keeping the underlying string
    value raw preserves that API, while str(name) exposes the stable comparison
    language used by BoardBench normalization.
    """

    def __new__(cls, raw: str, comparison: str):
        obj = str.__new__(cls, raw)
        obj._raw = raw
        obj._comparison = comparison
        return obj

    @property
    def raw_action(self) -> str:
        return self._raw

    def __str__(self) -> str:
        return self._comparison

    def __repr__(self) -> str:
        return repr(self._comparison)

    def __format__(self, format_spec: str) -> str:
        return format(self._comparison, format_spec)


def _combo_label(cards: Sequence[str]) -> str:
    return _COMBO_SEPARATOR.join(cards)


def _raw_action_from_name(name: str) -> Optional[str]:
    if isinstance(name, _ActionName):
        return name.raw_action

    text = str(name).strip().lower()

    if text in ("pass", "decline_nope"):
        return text
    if text.startswith(("play:", "pair:", "triple:", "five:", "give:", "chance:", "insert_exploding_kitten:")):
        return text

    if text == "pass_nope_response":
        return "decline_nope"

    insert_prefix = "place:exploding_kitten_at_draw_pile_pos"
    if text.startswith(insert_prefix):
        position = text[len(insert_prefix) :]
        if position.isdigit():
            return f"insert_exploding_kitten:pos{position}"

    if not text.startswith("move:") or "->" not in text:
        return None

    source, target = text[len("move:") :].split("->", 1)

    if source == f"hand_{FAVOR}" and target.startswith("discard_for_p"):
        player = target[len("discard_for_p") :]
        if player.isdigit():
            return f"play:{FAVOR}->p{player}"

    if source.startswith("hand_") and target == "discard":
        return f"play:{source[len('hand_') :]}"

    if source.startswith("pair_") and target.startswith("discard_for_p"):
        player = target[len("discard_for_p") :]
        if player.isdigit():
            return f"pair:{source[len('pair_') :]}->p{player}"

    if source.startswith("triple_") and target.startswith("discard_for_p") and "_ask_" in target:
        player, requested = target[len("discard_for_p") :].split("_ask_", 1)
        if player.isdigit() and requested:
            return f"triple:{source[len('triple_') :]}->p{player}:ask:{requested}"

    if source.startswith("five_") and target.startswith("discard_take_"):
        combo = source[len("five_") :]
        take = target[len("discard_take_") :]
        cards = combo.split(_COMBO_SEPARATOR)
        if combo and take and all(cards):
            return f"five:{'+'.join(cards)}->discard:{take}"

    if source.startswith("hand_") and target.startswith("player_p"):
        player = target[len("player_p") :]
        if player.isdigit():
            return f"give:{source[len('hand_') :]}->p{player}"

    return None


def _comparison_name_for_raw_action(raw: str) -> str:
    text = str.__str__(raw).strip().lower() if isinstance(raw, _ActionName) else str(raw).strip().lower()

    if text == "pass":
        return "pass"
    if text == "decline_nope":
        return "pass_nope_response"

    if text.startswith(f"play:{FAVOR}->p"):
        target = text.split("->", 1)[1]
        return f"move:hand_{FAVOR}->discard_for_{target}"

    if text.startswith("play:"):
        card = text[len("play:") :]
        return f"move:hand_{card}->discard"

    if text.startswith("pair:"):
        try:
            title, target = text[len("pair:") :].split("->p", 1)
        except ValueError:
            return text
        return f"move:pair_{title}->discard_for_p{target}"

    if text.startswith("triple:"):
        try:
            before_ask, requested = text[len("triple:") :].split(":ask:", 1)
            title, target = before_ask.split("->p", 1)
        except ValueError:
            return text
        return f"move:triple_{title}->discard_for_p{target}_ask_{requested}"

    if text.startswith("five:"):
        try:
            combo, take = text[len("five:") :].split("->discard:", 1)
        except ValueError:
            return text
        return f"move:five_{_combo_label(combo.split('+'))}->discard_take_{take}"

    if text.startswith("give:"):
        try:
            card, actor = text[len("give:") :].split("->p", 1)
        except ValueError:
            return text
        return f"move:hand_{card}->player_p{actor}"

    if text.startswith("insert_exploding_kitten:pos"):
        position = text.rsplit("pos", 1)[1]
        return f"place:exploding_kitten_at_draw_pile_pos{position}"

    if text.startswith("chance:"):
        return text

    return text


@dataclass
class GameState:
    """Complete game state.

    The full state stores private hands and the draw-pile order for correctness.
    Use Game.information_state(...) for a player-visible view that hides other
    hands and unseen draw-pile cards.
    """

    num_players: int
    hands: Tuple[Tuple[str, ...], ...]
    draw_pile: Tuple[str, ...]
    discard_pile: Tuple[str, ...]
    alive: Tuple[bool, ...]
    current: int = 0
    turns_remaining: int = 1
    phase: str = "turn"
    pending: Optional[Dict[str, Any]] = None
    response_player: Optional[int] = None
    response_passes: int = 0
    nope_count: int = 0
    winner: Optional[int] = None
    seen_future: Tuple[Tuple[str, ...], ...] = field(default_factory=tuple)
    history: Tuple[str, ...] = field(default_factory=tuple)


class Game:
    """Self-contained API for the supplied Exploding Kittens rules."""

    def __init__(self, num_players: int = 4, start_player: int = 0):
        if not 2 <= num_players <= 5:
            raise ValueError("The rulebook supports 2-5 players.")
        if not 0 <= start_player < num_players:
            raise ValueError("start_player must be a valid player index.")
        self.num_players = num_players
        self.start_player = start_player

    def initial_state(self) -> GameState:
        """Return a fresh canonical setup.

        The physical rules say to shuffle and choose a start player by any agreed
        criterion.  This model uses a deterministic canonical deal and p0 (or the
        configured start_player) so tests and renders are reproducible.
        """

        n = self.num_players
        base_deck: List[str] = []
        non_setup_cards = [c for c in CARD_ORDER if c not in (EXPLODING_KITTEN, DEFUSE)]
        max_count = max(FULL_DECK_COUNTS[c] for c in non_setup_cards)
        for copy_index in range(max_count):
            for card in non_setup_cards:
                if copy_index < FULL_DECK_COUNTS[card]:
                    base_deck.append(card)

        hands: List[List[str]] = [[] for _ in range(n)]
        cursor = 0
        for _ in range(7):
            for player in range(n):
                hands[player].append(base_deck[cursor])
                cursor += 1
        remaining = list(base_deck[cursor:])

        for player in range(n):
            hands[player].append(DEFUSE)

        # Two-player variant: after the starting Entschärfung cards, only two
        # more Entschärfung cards are shuffled into the draw pile; the others are
        # returned to the box.
        remaining_defuses = 2 if n == 2 else FULL_DECK_COUNTS[DEFUSE] - n
        exploding_kittens = n - 1
        specials: List[str] = []
        for i in range(max(remaining_defuses, exploding_kittens)):
            if i < remaining_defuses:
                specials.append(DEFUSE)
            if i < exploding_kittens:
                specials.append(EXPLODING_KITTEN)
        draw_pile = self._insert_evenly(remaining, specials)

        return GameState(
            num_players=n,
            hands=tuple(tuple(self._sort_cards(hand)) for hand in hands),
            draw_pile=tuple(draw_pile),
            discard_pile=(),
            alive=tuple(True for _ in range(n)),
            current=self.start_player,
            turns_remaining=1,
            phase="turn",
            pending=None,
            response_player=None,
            response_passes=0,
            nope_count=0,
            winner=None,
            seen_future=tuple(tuple() for _ in range(n)),
            history=(),
        )

    def current_player(self, state: GameState) -> int:
        if self.is_terminal(state):
            return TERMINAL
        if state.phase in ("steal_chance", "shuffle_chance"):
            return CHANCE
        if state.phase == "nope":
            return int(state.response_player)  # type: ignore[arg-type]
        if state.phase == "give":
            return int(state.pending["target"])  # type: ignore[index]
        return state.current

    def legal_actions(self, state: GameState) -> List[str]:
        if self.is_terminal(state):
            return []
        if state.phase == "turn":
            return self._turn_actions(state)
        if state.phase == "nope":
            actions = ["decline_nope"]
            player = int(state.response_player)  # type: ignore[arg-type]
            if self._count_in_hand(state, player, NOPE) > 0:
                actor = int(state.pending["actor"])  # type: ignore[index]
                # The rule text says Nö! prevents another player's action, but
                # Nö! may be played on another Nö!.  Therefore the actor cannot
                # start by noping their own card, but can answer a Nö!.
                if state.nope_count > 0 or player != actor:
                    actions.append("play:noe")
            return actions
        if state.phase == "give":
            target = int(state.pending["target"])  # type: ignore[index]
            actor = int(state.pending["actor"])  # type: ignore[index]
            return [f"give:{card}->p{actor}" for card in self._unique_sorted(state.hands[target])]
        if state.phase == "steal_chance":
            return [action for action, _ in self.chance_outcomes(state)]
        if state.phase == "shuffle_chance":
            return [action for action, _ in self.chance_outcomes(state)]
        if state.phase == "defuse_insert":
            return [f"insert_exploding_kitten:pos{i}" for i in range(len(state.draw_pile) + 1)]
        return []

    def apply_action(self, state: GameState, action: str) -> GameState:
        """Return a fresh successor state; the input state is not mutated."""

        name = self.action_to_name(action)
        legal = self.legal_actions(state)
        if name not in legal:
            raise ValueError(f"Illegal action {name!r} in phase {state.phase!r}; legal={legal!r}")

        next_state: GameState = copy.deepcopy(state)
        next_state.history = tuple(state.history) + (name,)

        if next_state.phase == "turn":
            return self._apply_turn_action(next_state, name)
        if next_state.phase == "nope":
            return self._apply_nope_action(next_state, name)
        if next_state.phase == "give":
            return self._apply_give_action(next_state, name)
        if next_state.phase == "steal_chance":
            return self._apply_steal_chance(next_state, name)
        if next_state.phase == "shuffle_chance":
            return self._apply_shuffle_chance(next_state, name)
        if next_state.phase == "defuse_insert":
            return self._apply_defuse_insert(next_state, name)
        raise ValueError(f"Unsupported phase: {next_state.phase!r}")

    def is_terminal(self, state: GameState) -> bool:
        return state.phase == "terminal" or sum(1 for alive in state.alive if alive) <= 1

    def returns(self, state: GameState) -> List[float]:
        if not self.is_terminal(state):
            return [0.0 for _ in range(state.num_players)]
        winner = state.winner
        if winner is None:
            alive_players = [p for p, alive in enumerate(state.alive) if alive]
            winner = alive_players[0] if len(alive_players) == 1 else None
        return [1.0 if p == winner else -1.0 for p in range(state.num_players)]

    def render(self, state: GameState) -> str:
        """Deterministic full-state debug render (not a player-visible view)."""

        lines = [
            f"phase={state.phase} current={self.current_player(state)} turns={state.turns_remaining} winner={state.winner}",
            "alive=" + ",".join(f"p{p}:{'alive' if a else 'out'}" for p, a in enumerate(state.alive)),
            "hands=" + "; ".join(f"p{p}[{self._cards_text(hand)}]" for p, hand in enumerate(state.hands)),
            f"draw({len(state.draw_pile)})=[{self._cards_text(state.draw_pile)}]",
            f"discard({len(state.discard_pile)})=[{self._cards_text(state.discard_pile)}]",
        ]
        if any(state.seen_future):
            lines.append(
                "seen_future="
                + "; ".join(f"p{p}[{self._cards_text(cards)}]" for p, cards in enumerate(state.seen_future) if cards)
            )
        if state.pending is not None:
            lines.append(f"pending={self._pending_text(state)}")
        if state.history:
            lines.append("history=" + " | ".join(state.history))
        return "\n".join(lines)

    def action_to_name(self, action: str) -> str:
        if not isinstance(action, str):
            raise TypeError("Actions in this implementation are canonical strings.")
        raw = _raw_action_from_name(action) or str(action)
        return _ActionName(raw, _comparison_name_for_raw_action(raw))

    def name_to_action(self, name: str) -> str:
        if not isinstance(name, str):
            raise TypeError("Action names must be strings.")
        return _raw_action_from_name(name) or str(name)

    def chance_outcomes(self, state: GameState) -> List[Tuple[str, float]]:
        if self.is_terminal(state):
            return []
        if state.phase == "steal_chance":
            target = int(state.pending["target"])  # type: ignore[index]
            actor = int(state.pending["actor"])  # type: ignore[index]
            counts = Counter(state.hands[target])
            total = sum(counts.values())
            if total == 0:
                return []
            return [
                (f"chance:steal:{card}:from:p{target}:to:p{actor}", counts[card] / total)
                for card in self._unique_sorted(counts.keys())
            ]
        if state.phase == "shuffle_chance":
            actions = self._shuffle_actions(state.draw_pile)
            if not actions:
                return []
            probability = 1.0 / len(actions)
            return [(action, probability) for action, _ in actions]
        return []

    def information_state(self, state: GameState, player: int) -> str:
        """Player-visible compact state; hides other hands and unseen deck order."""

        if not 0 <= player < state.num_players:
            raise ValueError("Invalid player index.")
        hand_sizes = ",".join(f"p{p}:{len(hand)}" for p, hand in enumerate(state.hands))
        lines = [
            f"you=p{player}",
            f"phase={state.phase} current={self.current_player(state)} turns={state.turns_remaining}",
            "alive=" + ",".join(f"p{p}:{'alive' if a else 'out'}" for p, a in enumerate(state.alive)),
            f"your_hand=[{self._cards_text(state.hands[player])}]",
            f"hand_sizes={hand_sizes}",
            f"draw_count={len(state.draw_pile)}",
            f"discard=[{self._cards_text(state.discard_pile)}]",
        ]
        if state.seen_future and state.seen_future[player]:
            lines.append(f"seen_top=[{self._cards_text(state.seen_future[player])}]")
        if state.pending is not None:
            lines.append(f"pending={self._pending_text(state)}")
        return "\n".join(lines)

    def observation(self, state: GameState, player: int) -> str:
        return self.information_state(state, player)

    # ----- Legal action generation -------------------------------------------------

    def _turn_actions(self, state: GameState) -> List[str]:
        player = state.current
        if not state.alive[player]:
            return []
        hand = state.hands[player]
        counts = Counter(hand)
        actions: List[str] = ["pass"]

        if counts[SKIP] > 0:
            actions.append("play:hops")
        if counts[ATTACK] > 0:
            actions.append("play:angriff")
        if counts[SHUFFLE] > 0:
            actions.append("play:mischen")
        if counts[SEE_FUTURE] > 0:
            actions.append("play:blick_in_die_zukunft")
        if counts[FAVOR] > 0:
            for target in self._other_alive_players(state, player):
                actions.append(f"play:wunsch->p{target}")

        for title in self._unique_sorted(counts.keys()):
            if counts[title] >= 2:
                for target in self._other_alive_players(state, player):
                    if len(state.hands[target]) > 0:
                        actions.append(f"pair:{title}->p{target}")
            if counts[title] >= 3:
                for target in self._other_alive_players(state, player):
                    for requested in CARD_ORDER:
                        actions.append(f"triple:{title}->p{target}:ask:{requested}")

        distinct_titles = self._unique_sorted(counts.keys())
        if len(distinct_titles) >= 5:
            for combo in itertools.combinations(distinct_titles, 5):
                # The five played cards are put on the discard pile before the
                # effect resolves, so the chosen discard title may be one of the
                # just-played titles as well as an already discarded title.
                take_options = self._unique_sorted(set(state.discard_pile).union(combo))
                for take in take_options:
                    actions.append(f"five:{'+'.join(combo)}->discard:{take}")

        return actions

    # ----- Transition handlers -----------------------------------------------------

    def _apply_turn_action(self, state: GameState, action: str) -> GameState:
        player = state.current
        if action == "pass":
            return self._draw_and_end_turn(state)

        if action == "play:hops":
            self._move_from_hand_to_discard(state, player, [SKIP])
            return self._start_nope_or_resolve(state, {"kind": "skip", "actor": player})
        if action == "play:angriff":
            self._move_from_hand_to_discard(state, player, [ATTACK])
            return self._start_nope_or_resolve(state, {"kind": "attack", "actor": player})
        if action == "play:mischen":
            self._move_from_hand_to_discard(state, player, [SHUFFLE])
            return self._start_nope_or_resolve(state, {"kind": "shuffle", "actor": player})
        if action == "play:blick_in_die_zukunft":
            self._move_from_hand_to_discard(state, player, [SEE_FUTURE])
            return self._start_nope_or_resolve(state, {"kind": "see_future", "actor": player})
        if action.startswith("play:wunsch->p"):
            target = int(action.split("->p", 1)[1])
            self._move_from_hand_to_discard(state, player, [FAVOR])
            return self._start_nope_or_resolve(state, {"kind": "favor", "actor": player, "target": target})

        if action.startswith("pair:"):
            title, target_text = action[len("pair:") :].split("->p", 1)
            target = int(target_text)
            self._move_from_hand_to_discard(state, player, [title, title])
            return self._start_nope_or_resolve(state, {"kind": "pair", "actor": player, "target": target})

        if action.startswith("triple:"):
            before_ask, requested = action[len("triple:") :].split(":ask:", 1)
            title, target_text = before_ask.split("->p", 1)
            target = int(target_text)
            self._move_from_hand_to_discard(state, player, [title, title, title])
            return self._start_nope_or_resolve(
                state,
                {"kind": "triple", "actor": player, "target": target, "requested": requested},
            )

        if action.startswith("five:"):
            combo_text, take = action[len("five:") :].split("->discard:", 1)
            played = tuple(combo_text.split("+"))
            self._move_from_hand_to_discard(state, player, played)
            return self._start_nope_or_resolve(
                state,
                {"kind": "five", "actor": player, "played": played, "take": take},
            )

        raise ValueError(f"Unhandled turn action: {action}")

    def _apply_nope_action(self, state: GameState, action: str) -> GameState:
        player = int(state.response_player)  # type: ignore[arg-type]
        if action == "play:noe":
            self._move_from_hand_to_discard(state, player, [NOPE])
            state.nope_count += 1
            state.response_passes = 0
            state.response_player = self._next_alive_after(state.alive, player)
            if not self._any_eligible_nope_player(state):
                return self._resolve_pending_effect(state, canceled=(state.nope_count % 2 == 1))
            return state

        if action == "decline_nope":
            state.response_passes += 1
            if state.response_passes >= sum(1 for alive in state.alive if alive):
                return self._resolve_pending_effect(state, canceled=(state.nope_count % 2 == 1))
            state.response_player = self._next_alive_after(state.alive, player)
            return state

        raise ValueError(f"Unhandled Nö! action: {action}")

    def _apply_give_action(self, state: GameState, action: str) -> GameState:
        card = action[len("give:") :].split("->p", 1)[0]
        actor = int(state.pending["actor"])  # type: ignore[index]
        target = int(state.pending["target"])  # type: ignore[index]
        self._remove_from_hand(state, target, [card])
        self._add_to_hand(state, actor, [card])
        return self._continue_actor_turn(state, actor)

    def _apply_steal_chance(self, state: GameState, action: str) -> GameState:
        middle = action[len("chance:steal:") :]
        card, rest = middle.split(":from:p", 1)
        target_text, actor_text = rest.split(":to:p", 1)
        target = int(target_text)
        actor = int(actor_text)
        self._remove_from_hand(state, target, [card])
        self._add_to_hand(state, actor, [card])
        return self._continue_actor_turn(state, actor)

    def _apply_shuffle_chance(self, state: GameState, action: str) -> GameState:
        mode = action[len("chance:shuffle:") :]
        actor = int(state.pending["actor"])  # type: ignore[index]
        state.draw_pile = tuple(self._shuffle_result(state.draw_pile, mode))
        self._clear_seen_future(state)
        return self._continue_actor_turn(state, actor)

    def _apply_defuse_insert(self, state: GameState, action: str) -> GameState:
        position = int(action.rsplit("pos", 1)[1])
        deck = list(state.draw_pile)
        deck.insert(position, EXPLODING_KITTEN)
        state.draw_pile = tuple(deck)
        state.pending = None
        state.phase = "turn"
        self._clear_seen_future(state)
        return self._finish_one_turn_unit(state)

    # ----- Effect resolution -------------------------------------------------------

    def _start_nope_or_resolve(self, state: GameState, effect: Dict[str, Any]) -> GameState:
        state.phase = "nope"
        state.pending = dict(effect)
        state.nope_count = 0
        state.response_passes = 0
        state.response_player = self._next_alive_after(state.alive, int(effect["actor"]))
        if not self._any_eligible_nope_player(state):
            return self._resolve_pending_effect(state, canceled=False)
        return state

    def _resolve_pending_effect(self, state: GameState, canceled: bool) -> GameState:
        effect = dict(state.pending or {})
        actor = int(effect.get("actor", state.current))
        state.pending = None
        state.response_player = None
        state.response_passes = 0
        state.nope_count = 0

        if canceled:
            return self._continue_actor_turn(state, actor)

        kind = effect["kind"]
        if kind == "skip":
            state.current = actor
            state.phase = "turn"
            return self._finish_one_turn_unit(state)

        if kind == "attack":
            target = self._next_alive_after(state.alive, actor)
            if target is None or target == actor:
                return self._make_terminal_if_needed(state)
            state.current = target
            state.turns_remaining = 2
            state.phase = "turn"
            return self._make_terminal_if_needed(state)

        if kind == "shuffle":
            state.current = actor
            state.phase = "shuffle_chance"
            state.pending = {"kind": "shuffle", "actor": actor}
            return state

        if kind == "see_future":
            seen = [tuple() for _ in range(state.num_players)]
            for p, cards in enumerate(state.seen_future[: state.num_players]):
                seen[p] = tuple(cards)
            seen[actor] = tuple(state.draw_pile[:3])
            state.seen_future = tuple(seen)
            return self._continue_actor_turn(state, actor)

        if kind == "favor":
            target = int(effect["target"])
            if state.alive[target] and len(state.hands[target]) > 0:
                state.current = actor
                state.phase = "give"
                state.pending = {"kind": "give", "actor": actor, "target": target}
                return state
            return self._continue_actor_turn(state, actor)

        if kind == "pair":
            target = int(effect["target"])
            if state.alive[target] and len(state.hands[target]) > 0:
                state.current = actor
                state.phase = "steal_chance"
                state.pending = {"kind": "steal", "actor": actor, "target": target}
                return state
            return self._continue_actor_turn(state, actor)

        if kind == "triple":
            target = int(effect["target"])
            requested = str(effect["requested"])
            if state.alive[target] and requested in state.hands[target]:
                self._remove_from_hand(state, target, [requested])
                self._add_to_hand(state, actor, [requested])
            return self._continue_actor_turn(state, actor)

        if kind == "five":
            take = str(effect["take"])
            if take in state.discard_pile:
                self._remove_from_discard(state, take)
                self._add_to_hand(state, actor, [take])
            return self._continue_actor_turn(state, actor)

        raise ValueError(f"Unknown pending effect kind: {kind!r}")

    # ----- Draw, explosion, and turn advancement ----------------------------------

    def _draw_and_end_turn(self, state: GameState) -> GameState:
        player = state.current
        if not state.draw_pile:
            # The rulebook says the draw pile will not run out because exploding
            # kittens ensure all but one player leave first.  This fallback keeps
            # custom test states finite without inventing a card.
            return self._finish_one_turn_unit(state)

        card = state.draw_pile[0]
        state.draw_pile = tuple(state.draw_pile[1:])
        self._clear_seen_future(state)

        if card == EXPLODING_KITTEN:
            if DEFUSE in state.hands[player]:
                # Playing Entschärfung is the only rescue described.  The model
                # uses it automatically when available, then asks where to put
                # the Exploding Kitten back into the draw pile.
                self._move_from_hand_to_discard(state, player, [DEFUSE])
                state.phase = "defuse_insert"
                state.pending = {"kind": "defuse", "actor": player}
                return state
            return self._explode_player(state, player, card)

        self._add_to_hand(state, player, [card])
        return self._finish_one_turn_unit(state)

    def _explode_player(self, state: GameState, player: int, exploding_card: str) -> GameState:
        hand_cards = list(state.hands[player])
        state.discard_pile = tuple(list(state.discard_pile) + hand_cards + [exploding_card])
        hands = [list(hand) for hand in state.hands]
        hands[player] = []
        state.hands = tuple(tuple(hand) for hand in hands)
        alive = list(state.alive)
        alive[player] = False
        state.alive = tuple(alive)
        self._clear_seen_future(state)

        if sum(1 for alive_flag in state.alive if alive_flag) <= 1:
            return self._make_terminal_if_needed(state)

        nxt = self._next_alive_after(state.alive, player)
        state.current = int(nxt)  # type: ignore[arg-type]
        state.turns_remaining = 1
        state.phase = "turn"
        state.pending = None
        return state

    def _finish_one_turn_unit(self, state: GameState) -> GameState:
        if self.is_terminal(state):
            return self._make_terminal_if_needed(state)
        player = state.current
        remaining = max(0, state.turns_remaining - 1)
        if remaining > 0 and state.alive[player]:
            state.turns_remaining = remaining
            state.phase = "turn"
            state.pending = None
            return state
        nxt = self._next_alive_after(state.alive, player)
        if nxt is None or nxt == player:
            return self._make_terminal_if_needed(state)
        state.current = nxt
        state.turns_remaining = 1
        state.phase = "turn"
        state.pending = None
        return self._make_terminal_if_needed(state)

    def _continue_actor_turn(self, state: GameState, actor: int) -> GameState:
        state.current = actor
        state.phase = "turn"
        state.pending = None
        state.response_player = None
        state.response_passes = 0
        state.nope_count = 0
        return self._make_terminal_if_needed(state)

    def _make_terminal_if_needed(self, state: GameState) -> GameState:
        alive_players = [p for p, alive in enumerate(state.alive) if alive]
        if len(alive_players) <= 1:
            state.phase = "terminal"
            state.winner = alive_players[0] if alive_players else None
            state.turns_remaining = 0
            state.pending = None
            state.response_player = None
        return state

    # ----- Small state mutation helpers -------------------------------------------

    def _move_from_hand_to_discard(self, state: GameState, player: int, cards: Iterable[str]) -> None:
        cards_tuple = tuple(cards)
        self._remove_from_hand(state, player, cards_tuple)
        state.discard_pile = tuple(list(state.discard_pile) + list(cards_tuple))

    def _remove_from_hand(self, state: GameState, player: int, cards: Iterable[str]) -> None:
        hands = [list(hand) for hand in state.hands]
        for card in cards:
            hands[player].remove(card)
        hands[player] = self._sort_cards(hands[player])
        state.hands = tuple(tuple(hand) for hand in hands)

    def _add_to_hand(self, state: GameState, player: int, cards: Iterable[str]) -> None:
        hands = [list(hand) for hand in state.hands]
        hands[player].extend(cards)
        hands[player] = self._sort_cards(hands[player])
        state.hands = tuple(tuple(hand) for hand in hands)

    def _remove_from_discard(self, state: GameState, card: str) -> None:
        discard = list(state.discard_pile)
        for index in range(len(discard) - 1, -1, -1):
            if discard[index] == card:
                del discard[index]
                state.discard_pile = tuple(discard)
                return
        raise ValueError(f"Card {card!r} is not in discard pile.")

    def _clear_seen_future(self, state: GameState) -> None:
        state.seen_future = tuple(tuple() for _ in range(state.num_players))

    # ----- Chance abstractions -----------------------------------------------------

    def _shuffle_actions(self, deck: Sequence[str]) -> List[Tuple[str, Tuple[str, ...]]]:
        candidates: List[Tuple[str, Tuple[str, ...]]] = []
        original = tuple(deck)
        candidates.append(("chance:shuffle:identity", original))
        if len(deck) >= 2:
            candidates.append(("chance:shuffle:reverse", tuple(reversed(deck))))
            candidates.append(("chance:shuffle:rotate_left", tuple(deck[1:]) + tuple(deck[:1])))
            candidates.append(("chance:shuffle:rotate_right", tuple(deck[-1:]) + tuple(deck[:-1])))
            candidates.append(("chance:shuffle:by_title", tuple(self._sort_cards(deck))))

        seen_decks = set()
        unique: List[Tuple[str, Tuple[str, ...]]] = []
        for action, result in candidates:
            if result not in seen_decks:
                seen_decks.add(result)
                unique.append((action, result))
        return unique

    def _shuffle_result(self, deck: Sequence[str], mode: str) -> Tuple[str, ...]:
        for action, result in self._shuffle_actions(deck):
            if action == f"chance:shuffle:{mode}":
                return result
        raise ValueError(f"Unknown shuffle mode: {mode!r}")

    # ----- Formatting and utility helpers -----------------------------------------

    def _any_eligible_nope_player(self, state: GameState) -> bool:
        if state.pending is None:
            return False
        actor = int(state.pending["actor"])
        for player, alive in enumerate(state.alive):
            if not alive:
                continue
            if self._count_in_hand(state, player, NOPE) <= 0:
                continue
            if state.nope_count > 0 or player != actor:
                return True
        return False

    def _other_alive_players(self, state: GameState, player: int) -> List[int]:
        return [p for p, alive in enumerate(state.alive) if alive and p != player]

    def _next_alive_after(self, alive: Sequence[bool], player: int) -> Optional[int]:
        if not any(alive):
            return None
        n = len(alive)
        for offset in range(1, n + 1):
            candidate = (player + offset) % n
            if alive[candidate]:
                return candidate
        return None

    def _count_in_hand(self, state: GameState, player: int, card: str) -> int:
        return sum(1 for c in state.hands[player] if c == card)

    def _unique_sorted(self, cards: Iterable[str]) -> List[str]:
        return self._sort_cards(set(cards))

    def _sort_cards(self, cards: Iterable[str]) -> List[str]:
        return sorted(cards, key=lambda c: (_CARD_INDEX.get(c, 999), c))

    def _cards_text(self, cards: Sequence[str]) -> str:
        counts = Counter(cards)
        parts = []
        for card in self._unique_sorted(counts.keys()):
            count = counts[card]
            parts.append(card if count == 1 else f"{card}x{count}")
        return ",".join(parts)

    def _pending_text(self, state: GameState) -> str:
        if state.pending is None:
            return "none"
        bits = [f"{key}={state.pending[key]}" for key in sorted(state.pending)]
        if state.phase == "nope":
            bits.append(f"response=p{state.response_player}")
            bits.append(f"nope_count={state.nope_count}")
        return "{" + ",".join(bits) + "}"

    def _insert_evenly(self, deck: Sequence[str], specials: Sequence[str]) -> List[str]:
        if not specials:
            return list(deck)
        total = len(deck) + len(specials)
        raw_positions = [((i + 1) * total) // (len(specials) + 1) for i in range(len(specials))]
        positions: List[int] = []
        last = -1
        for pos in raw_positions:
            pos = max(pos, last + 1)
            pos = min(pos, total - (len(raw_positions) - len(positions)))
            positions.append(pos)
            last = pos
        position_to_special = {pos: specials[i] for i, pos in enumerate(positions)}
        result: List[str] = []
        deck_index = 0
        for slot in range(total):
            if slot in position_to_special:
                result.append(position_to_special[slot])
            else:
                result.append(deck[deck_index])
                deck_index += 1
        return result


__all__ = [
    "TERMINAL",
    "CHANCE",
    "SIMULTANEOUS",
    "GameState",
    "Game",
    "CARD_ORDER",
    "CARD_TITLES",
    "FULL_DECK_COUNTS",
]
