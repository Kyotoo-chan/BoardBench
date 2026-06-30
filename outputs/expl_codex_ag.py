from __future__ import annotations

from dataclasses import dataclass, replace
from itertools import combinations
from typing import Any, Dict, Iterable, List, Optional, Tuple


TERMINAL = -1
CHANCE = -2
SIMULTANEOUS = -3


# ASCII transliterations of the German rulebook card names.
EXPLODING_KITTEN = "Exploding_Kitten"
DEFUSE = "Entschaerfung"
ATTACK = "Angriff"
SKIP = "Hops"
FAVOR = "Wunsch"
SHUFFLE = "Mischen"
SEE_FUTURE = "Blick_in_die_Zukunft"
NOPE = "Noe"

# The extracted rule text states "cat cards, 4 of each kind" but only exposes one
# full cat-card title. The total card count implies five such titles, so the
# implementation uses neutral numbered labels for the five kinds.
CAT_CARDS = (
    "Katzenkarte_1",
    "Katzenkarte_2",
    "Katzenkarte_3",
    "Katzenkarte_4",
    "Katzenkarte_5",
)

CARD_ORDER = (
    EXPLODING_KITTEN,
    DEFUSE,
    ATTACK,
    SKIP,
    FAVOR,
    SHUFFLE,
    SEE_FUTURE,
    NOPE,
) + CAT_CARDS

CARD_INDEX = {card: i for i, card in enumerate(CARD_ORDER)}

CARD_COUNTS = {
    EXPLODING_KITTEN: 4,
    DEFUSE: 6,
    ATTACK: 4,
    SKIP: 4,
    FAVOR: 4,
    SHUFFLE: 4,
    SEE_FUTURE: 5,
    NOPE: 5,
    "Katzenkarte_1": 4,
    "Katzenkarte_2": 4,
    "Katzenkarte_3": 4,
    "Katzenkarte_4": 4,
    "Katzenkarte_5": 4,
}

PLAYABLE_SINGLE_CARDS = (ATTACK, SKIP, FAVOR, SHUFFLE, SEE_FUTURE)


@dataclass(frozen=True)
class GameState:
    """Complete game state.

    This is a full-information debug state. Use information_state() for a
    player-visible hidden-information view.
    """

    num_players: int
    hands: Tuple[Tuple[str, ...], ...]
    deck: Tuple[str, ...]
    discard: Tuple[str, ...]
    alive: Tuple[bool, ...]
    current: int
    phase: str
    turns_remaining: int = 1
    setup_counts: Tuple[Tuple[str, int], ...] = ()
    setup_index: int = 0
    pending_action: Optional[Tuple[Any, ...]] = None
    response_player: int = 0
    nope_count: int = 0
    nope_passes: int = 0
    seen_top: Tuple[Tuple[str, ...], ...] = ()
    history: Tuple[str, ...] = ()


class Game:
    """Exploding Kittens NSFW edition model from the supplied German rules."""

    def __init__(self, num_players: int = 4, start_player: int = 0):
        if num_players < 2 or num_players > 5:
            raise ValueError("The rulebook supports 2 to 5 players.")
        if start_player < 0 or start_player >= num_players:
            raise ValueError("start_player must be a valid player index.")
        self.num_players = num_players
        self.start_player = start_player

    def initial_state(self) -> GameState:
        hands = tuple(_sort_cards((DEFUSE,)) for _ in range(self.num_players))
        counts = {
            card: count
            for card, count in CARD_COUNTS.items()
            if card not in (EXPLODING_KITTEN, DEFUSE)
        }
        return GameState(
            num_players=self.num_players,
            hands=hands,
            deck=(),
            discard=(),
            alive=tuple(True for _ in range(self.num_players)),
            current=self.start_player,
            phase="setup_deal",
            turns_remaining=1,
            setup_counts=_counts_to_tuple(counts),
            setup_index=0,
            seen_top=_empty_seen(self.num_players),
            history=("setup:start",),
        )

    def current_player(self, state: GameState) -> int:
        if self.is_terminal(state):
            return TERMINAL
        if state.phase in ("setup_deal", "setup_deck", "steal_random"):
            return CHANCE
        if state.phase == "nope":
            return state.response_player
        if state.phase == "favor_give":
            return state.response_player
        return state.current

    def legal_actions(self, state: GameState) -> List[str]:
        if self.is_terminal(state):
            return []
        if state.phase == "setup_deal":
            counts = _counts_from_tuple(state.setup_counts)
            player = state.setup_index % state.num_players
            return [
                f"chance:setup-deal:p{player}:{card}"
                for card in CARD_ORDER
                if counts.get(card, 0) > 0
            ]
        if state.phase == "setup_deck":
            counts = _counts_from_tuple(state.setup_counts)
            return [
                f"chance:setup-deck:{card}"
                for card in CARD_ORDER
                if counts.get(card, 0) > 0
            ]
        if state.phase == "steal_random":
            if state.pending_action is None:
                return []
            _, thief, target = state.pending_action
            counts = _card_counts(state.hands[target])
            return [
                f"chance:steal:p{target}->p{thief}:{card}"
                for card in CARD_ORDER
                if counts.get(card, 0) > 0
            ]
        if state.phase == "nope":
            actions = ["nope:pass"]
            if self._can_play_nope(state, state.response_player):
                actions.append("nope:play")
            return actions
        if state.phase == "favor_give":
            if state.pending_action is None:
                return []
            _, requester, target = state.pending_action
            counts = _card_counts(state.hands[target])
            return [
                f"give:{card}->p{requester}"
                for card in CARD_ORDER
                if counts.get(card, 0) > 0
            ]
        if state.phase == "defuse_insert":
            if DEFUSE not in state.hands[state.current]:
                return []
            return [f"defuse:insert:pos{pos}" for pos in range(len(state.deck) + 1)]
        if state.phase != "action":
            return []

        player = state.current
        if not state.alive[player]:
            return []

        hand = state.hands[player]
        counts = _card_counts(hand)
        actions: List[str] = []

        if state.deck:
            actions.append("draw")

        if counts.get(ATTACK, 0) > 0:
            actions.append(f"play:{ATTACK}")
        if counts.get(SKIP, 0) > 0:
            actions.append(f"play:{SKIP}")
        if counts.get(SHUFFLE, 0) > 0:
            actions.append(f"play:{SHUFFLE}")
        if counts.get(SEE_FUTURE, 0) > 0:
            actions.append(f"play:{SEE_FUTURE}")
        if counts.get(FAVOR, 0) > 0:
            for target in self._other_alive_players(state, player, require_cards=True):
                actions.append(f"play:{FAVOR}->p{target}")

        for card in CARD_ORDER:
            if counts.get(card, 0) >= 2:
                for target in self._other_alive_players(state, player, require_cards=True):
                    actions.append(f"combo:pair:{card}->p{target}")

        for card in CARD_ORDER:
            if counts.get(card, 0) >= 3:
                for target in self._other_alive_players(state, player):
                    for wanted in CARD_ORDER:
                        actions.append(f"combo:triple:{card}->p{target}:ask:{wanted}")

        discard_choices = [card for card in CARD_ORDER if card in state.discard]
        distinct_hand_cards = [card for card in CARD_ORDER if counts.get(card, 0) > 0]
        if len(distinct_hand_cards) >= 5 and discard_choices:
            for combo_cards in combinations(distinct_hand_cards, 5):
                combo_name = "+".join(combo_cards)
                for take_card in discard_choices:
                    actions.append(f"combo:five-different:{combo_name}:take:{take_card}")

        return actions

    def apply_action(self, state: GameState, action: str) -> GameState:
        if action not in self.legal_actions(state):
            raise ValueError(f"Illegal action for phase {state.phase}: {action}")

        if state.phase == "setup_deal":
            return self._apply_setup_deal(state, action)
        if state.phase == "setup_deck":
            return self._apply_setup_deck(state, action)
        if state.phase == "steal_random":
            return self._apply_steal_random(state, action)
        if state.phase == "nope":
            return self._apply_nope_response(state, action)
        if state.phase == "favor_give":
            return self._apply_favor_give(state, action)
        if state.phase == "defuse_insert":
            return self._apply_defuse_insert(state, action)
        if state.phase != "action":
            raise ValueError(f"Unhandled phase: {state.phase}")

        if action == "draw":
            return self._draw_card(state)
        if action.startswith("play:"):
            return self._play_single_card(state, action)
        if action.startswith("combo:pair:"):
            return self._play_pair(state, action)
        if action.startswith("combo:triple:"):
            return self._play_triple(state, action)
        if action.startswith("combo:five-different:"):
            return self._play_five_different(state, action)
        raise ValueError(f"Unhandled action: {action}")

    def is_terminal(self, state: GameState) -> bool:
        return state.phase == "terminal" or sum(1 for alive in state.alive if alive) <= 1

    def returns(self, state: GameState) -> List[float]:
        if not self.is_terminal(state):
            return [0.0 for _ in range(state.num_players)]
        alive_players = [p for p, alive in enumerate(state.alive) if alive]
        if len(alive_players) != 1:
            return [0.0 for _ in range(state.num_players)]
        winner = alive_players[0]
        return [1.0 if p == winner else -1.0 for p in range(state.num_players)]

    def render(self, state: GameState) -> str:
        hands = ";".join(
            f"p{p}:{_format_cards(state.hands[p])}" for p in range(state.num_players)
        )
        seen = ";".join(
            f"p{p}:{_format_cards(state.seen_top[p])}" for p in range(state.num_players)
        )
        alive = ",".join(f"p{p}={int(state.alive[p])}" for p in range(state.num_players))
        pending = "-" if state.pending_action is None else repr(state.pending_action)
        return (
            f"phase={state.phase}|current={self.current_player(state)}|"
            f"turn_player={state.current}|turns={state.turns_remaining}|"
            f"alive={alive}|deck({len(state.deck)})={_format_cards(state.deck)}|"
            f"discard({len(state.discard)})={_format_cards(state.discard)}|"
            f"hands={hands}|seen={seen}|pending={pending}|"
            f"nope_count={state.nope_count}|history={len(state.history)}"
        )

    def action_to_name(self, action: str) -> str:
        return str(action)

    def name_to_action(self, name: str) -> str:
        return str(name)

    def chance_outcomes(self, state: GameState) -> List[Tuple[str, float]]:
        if state.phase == "setup_deal":
            counts = _counts_from_tuple(state.setup_counts)
            total = sum(counts.values())
            if total <= 0:
                return []
            player = state.setup_index % state.num_players
            return [
                (f"chance:setup-deal:p{player}:{card}", counts[card] / total)
                for card in CARD_ORDER
                if counts.get(card, 0) > 0
            ]
        if state.phase == "setup_deck":
            counts = _counts_from_tuple(state.setup_counts)
            total = sum(counts.values())
            if total <= 0:
                return []
            return [
                (f"chance:setup-deck:{card}", counts[card] / total)
                for card in CARD_ORDER
                if counts.get(card, 0) > 0
            ]
        if state.phase == "steal_random":
            if state.pending_action is None:
                return []
            _, thief, target = state.pending_action
            counts = _card_counts(state.hands[target])
            total = sum(counts.values())
            if total <= 0:
                return []
            return [
                (f"chance:steal:p{target}->p{thief}:{card}", counts[card] / total)
                for card in CARD_ORDER
                if counts.get(card, 0) > 0
            ]
        return []

    def information_state(self, state: GameState, player: int) -> str:
        if player < 0 or player >= state.num_players:
            raise ValueError("Invalid player index.")
        hand_parts = []
        for p in range(state.num_players):
            if p == player:
                hand_parts.append(f"p{p}:{_format_cards(state.hands[p])}")
            else:
                hand_parts.append(f"p{p}:count{len(state.hands[p])}")
        alive_text = ",".join(
            f"p{p}={int(state.alive[p])}" for p in range(state.num_players)
        )
        pending = "-" if state.pending_action is None else repr(state.pending_action)
        return (
            f"player=p{player}|phase={state.phase}|current={self.current_player(state)}|"
            f"turn_player=p{state.current}|turns={state.turns_remaining}|"
            f"alive={alive_text}|deck_count={len(state.deck)}|"
            f"discard={_format_cards(state.discard)}|"
            f"own_seen_top={_format_cards(state.seen_top[player])}|"
            f"hands={';'.join(hand_parts)}|pending={pending}"
        )

    def _apply_setup_deal(self, state: GameState, action: str) -> GameState:
        prefix = "chance:setup-deal:"
        tail = action[len(prefix) :]
        player_text, card = tail.split(":", 1)
        player = _parse_player(player_text)
        expected_player = state.setup_index % state.num_players
        if player != expected_player:
            raise ValueError("Setup deal action targets the wrong player.")
        counts = _counts_from_tuple(state.setup_counts)
        _require_card_available(counts, card)
        counts[card] -= 1

        hands = _replace_hand(state.hands, player, _add_card(state.hands[player], card))
        next_index = state.setup_index + 1
        if next_index == 7 * state.num_players:
            deck_counts = {c: n for c, n in counts.items() if n > 0}
            deck_counts[EXPLODING_KITTEN] = state.num_players - 1
            if state.num_players == 2:
                deck_counts[DEFUSE] = 2
            else:
                deck_counts[DEFUSE] = CARD_COUNTS[DEFUSE] - state.num_players
            return replace(
                state,
                hands=hands,
                phase="setup_deck",
                setup_counts=_counts_to_tuple(deck_counts),
                setup_index=0,
                history=state.history + (action,),
            )
        return replace(
            state,
            hands=hands,
            setup_counts=_counts_to_tuple(counts),
            setup_index=next_index,
            history=state.history + (action,),
        )

    def _apply_setup_deck(self, state: GameState, action: str) -> GameState:
        card = action[len("chance:setup-deck:") :]
        counts = _counts_from_tuple(state.setup_counts)
        _require_card_available(counts, card)
        counts[card] -= 1
        deck = state.deck + (card,)
        remaining = {c: n for c, n in counts.items() if n > 0}
        if not remaining:
            return replace(
                state,
                deck=deck,
                phase="action",
                current=self.start_player,
                turns_remaining=1,
                setup_counts=(),
                setup_index=0,
                history=state.history + (action, "setup:complete"),
            )
        return replace(
            state,
            deck=deck,
            setup_counts=_counts_to_tuple(remaining),
            history=state.history + (action,),
        )

    def _play_single_card(self, state: GameState, action: str) -> GameState:
        player = state.current
        tail = action[len("play:") :]
        if "->" in tail:
            card, target_text = tail.split("->", 1)
            target = _parse_player(target_text)
        else:
            card = tail
            target = None
        if card not in PLAYABLE_SINGLE_CARDS:
            raise ValueError(f"Card cannot be played singly here: {card}")
        hands, discard = self._discard_from_hand(state, player, (card,))
        pending = ("single", player, card, target)
        next_state = replace(
            state,
            hands=hands,
            discard=discard,
            history=state.history + (action,),
        )
        return self._begin_nope_window(next_state, pending)

    def _play_pair(self, state: GameState, action: str) -> GameState:
        player = state.current
        tail = action[len("combo:pair:") :]
        card, target_text = tail.split("->", 1)
        target = _parse_player(target_text)
        hands, discard = self._discard_from_hand(state, player, (card, card))
        pending = ("pair", player, target, card)
        next_state = replace(
            state,
            hands=hands,
            discard=discard,
            history=state.history + (action,),
        )
        return self._begin_nope_window(next_state, pending)

    def _play_triple(self, state: GameState, action: str) -> GameState:
        player = state.current
        tail = action[len("combo:triple:") :]
        left, wanted = tail.split(":ask:", 1)
        card, target_text = left.split("->", 1)
        target = _parse_player(target_text)
        hands, discard = self._discard_from_hand(state, player, (card, card, card))
        pending = ("triple", player, target, card, wanted)
        next_state = replace(
            state,
            hands=hands,
            discard=discard,
            history=state.history + (action,),
        )
        return self._begin_nope_window(next_state, pending)

    def _play_five_different(self, state: GameState, action: str) -> GameState:
        player = state.current
        tail = action[len("combo:five-different:") :]
        cards_text, take_card = tail.split(":take:", 1)
        cards = tuple(cards_text.split("+"))
        if len(cards) != 5 or len(set(cards)) != 5:
            raise ValueError("Five-different combo must contain five titles.")
        hands, discard = self._discard_from_hand(state, player, cards)
        pending = ("five", player, cards, take_card)
        next_state = replace(
            state,
            hands=hands,
            discard=discard,
            history=state.history + (action,),
        )
        return self._begin_nope_window(next_state, pending)

    def _draw_card(self, state: GameState) -> GameState:
        if not state.deck:
            raise ValueError("Cannot draw from an empty deck.")
        player = state.current
        card = state.deck[0]
        deck = state.deck[1:]
        base = replace(
            state,
            deck=deck,
            seen_top=_empty_seen(state.num_players),
            history=state.history + (f"draw:{card}",),
        )
        if card == EXPLODING_KITTEN:
            if DEFUSE in state.hands[player]:
                return replace(
                    base,
                    phase="defuse_insert",
                    pending_action=("defuse", player),
                    response_player=player,
                )
            hand_cards = state.hands[player]
            hands = _replace_hand(base.hands, player, ())
            alive = _replace_bool(base.alive, player, False)
            exploded = replace(
                base,
                hands=hands,
                alive=alive,
                discard=base.discard + hand_cards + (EXPLODING_KITTEN,),
                history=base.history + (f"explode:p{player}",),
            )
            if self.is_terminal(exploded):
                return self._terminalize(exploded)
            return self._finish_one_turn(exploded, f"turn:end:p{player}:exploded")

        hands = _replace_hand(base.hands, player, _add_card(base.hands[player], card))
        drew = replace(base, hands=hands)
        return self._finish_one_turn(drew, f"turn:end:p{player}:draw")

    def _apply_defuse_insert(self, state: GameState, action: str) -> GameState:
        player = state.current
        pos_text = action[len("defuse:insert:pos") :]
        position = int(pos_text)
        if position < 0 or position > len(state.deck):
            raise ValueError("Defuse insertion position is out of range.")
        hand = _remove_cards(state.hands[player], (DEFUSE,))
        hands = _replace_hand(state.hands, player, hand)
        deck = state.deck[:position] + (EXPLODING_KITTEN,) + state.deck[position:]
        base = replace(
            state,
            hands=hands,
            deck=deck,
            discard=state.discard + (DEFUSE,),
            phase="action",
            pending_action=None,
            response_player=0,
            seen_top=_empty_seen(state.num_players),
            history=state.history + (action, f"turn:end:p{player}:defused"),
        )
        return self._finish_one_turn(base, f"turn:advance:p{player}:defused")

    def _apply_nope_response(self, state: GameState, action: str) -> GameState:
        if action == "nope:pass":
            passes = state.nope_passes + 1
            if passes >= self._alive_count(state):
                return self._resolve_pending(
                    state,
                    canceled=(state.nope_count % 2 == 1),
                    extra_history=("nope:all-pass",),
                )
            return replace(
                state,
                response_player=self._next_alive_after(state, state.response_player),
                nope_passes=passes,
                history=state.history + (action,),
            )

        player = state.response_player
        hand = _remove_cards(state.hands[player], (NOPE,))
        hands = _replace_hand(state.hands, player, hand)
        next_state = replace(
            state,
            hands=hands,
            discard=state.discard + (NOPE,),
            response_player=self._next_alive_after(state, player),
            nope_count=state.nope_count + 1,
            nope_passes=0,
            history=state.history + (f"nope:play:p{player}",),
        )
        if not self._any_player_can_nope(next_state):
            return self._resolve_pending(
                next_state,
                canceled=(next_state.nope_count % 2 == 1),
                extra_history=("nope:no-more",),
            )
        return next_state

    def _apply_favor_give(self, state: GameState, action: str) -> GameState:
        if state.pending_action is None:
            raise ValueError("Missing favor pending action.")
        _, requester, target = state.pending_action
        card, requester_text = action[len("give:") :].split("->", 1)
        if _parse_player(requester_text) != requester:
            raise ValueError("Favor give action targets the wrong requester.")
        target_hand = _remove_cards(state.hands[target], (card,))
        requester_hand = _add_card(state.hands[requester], card)
        hands = _replace_hand(state.hands, target, target_hand)
        hands = _replace_hand(hands, requester, requester_hand)
        return replace(
            state,
            hands=hands,
            phase="action",
            current=requester,
            pending_action=None,
            response_player=0,
            history=state.history + (action,),
        )

    def _apply_steal_random(self, state: GameState, action: str) -> GameState:
        if state.pending_action is None:
            raise ValueError("Missing steal pending action.")
        _, thief, target = state.pending_action
        tail = action[len("chance:steal:") :]
        movement, card = tail.split(":", 1)
        from_text, to_text = movement.split("->", 1)
        if _parse_player(from_text) != target or _parse_player(to_text) != thief:
            raise ValueError("Steal chance action has wrong players.")
        target_hand = _remove_cards(state.hands[target], (card,))
        thief_hand = _add_card(state.hands[thief], card)
        hands = _replace_hand(state.hands, target, target_hand)
        hands = _replace_hand(hands, thief, thief_hand)
        return replace(
            state,
            hands=hands,
            phase="action",
            current=thief,
            pending_action=None,
            response_player=0,
            history=state.history + (action,),
        )

    def _begin_nope_window(
        self, state: GameState, pending: Tuple[Any, ...]
    ) -> GameState:
        pending_state = replace(
            state,
            phase="nope",
            pending_action=pending,
            response_player=self._next_alive_after(state, pending[1]),
            nope_count=0,
            nope_passes=0,
        )
        if not self._any_player_can_nope(pending_state):
            return self._resolve_pending(
                pending_state,
                canceled=False,
                extra_history=("nope:none",),
            )
        return pending_state

    def _resolve_pending(
        self,
        state: GameState,
        canceled: bool,
        extra_history: Tuple[str, ...] = (),
    ) -> GameState:
        if state.pending_action is None:
            raise ValueError("No pending action to resolve.")
        pending = state.pending_action
        base = replace(
            state,
            phase="action",
            pending_action=None,
            response_player=0,
            nope_count=0,
            nope_passes=0,
            history=state.history + extra_history,
        )
        if canceled:
            return replace(base, history=base.history + ("nope:canceled",))

        kind = pending[0]
        if kind == "single":
            _, player, card, target = pending
            if card == ATTACK:
                return self._effect_attack(base, player)
            if card == SKIP:
                return self._finish_one_turn(base, f"turn:end:p{player}:hops")
            if card == SHUFFLE:
                return replace(
                    base,
                    deck=_deterministic_shuffle(base.deck),
                    seen_top=_empty_seen(base.num_players),
                    history=base.history + (f"effect:{SHUFFLE}",),
                )
            if card == SEE_FUTURE:
                seen = list(base.seen_top)
                seen[player] = base.deck[:3]
                return replace(
                    base,
                    seen_top=tuple(seen),
                    history=base.history + (f"effect:{SEE_FUTURE}:p{player}",),
                )
            if card == FAVOR:
                if target is None or not base.alive[target] or not base.hands[target]:
                    return replace(base, history=base.history + ("effect:Wunsch:none",))
                return replace(
                    base,
                    phase="favor_give",
                    pending_action=("favor_give", player, target),
                    response_player=target,
                    history=base.history + (f"effect:Wunsch:p{target}",),
                )

        if kind == "pair":
            _, thief, target, _card = pending
            if not base.alive[target] or not base.hands[target]:
                return replace(base, history=base.history + ("effect:pair:none",))
            return replace(
                base,
                phase="steal_random",
                pending_action=("steal", thief, target),
                response_player=0,
                history=base.history + (f"effect:pair:p{target}->p{thief}",),
            )

        if kind == "triple":
            _, player, target, _played_card, wanted = pending
            if base.alive[target] and wanted in base.hands[target]:
                target_hand = _remove_cards(base.hands[target], (wanted,))
                player_hand = _add_card(base.hands[player], wanted)
                hands = _replace_hand(base.hands, target, target_hand)
                hands = _replace_hand(hands, player, player_hand)
                return replace(
                    base,
                    hands=hands,
                    history=base.history + (f"effect:triple:{wanted}",),
                )
            return replace(base, history=base.history + (f"effect:triple:miss:{wanted}",))

        if kind == "five":
            _, player, _cards, take_card = pending
            if take_card not in base.discard:
                return replace(base, history=base.history + ("effect:five:none",))
            discard = _remove_one_from_tuple(base.discard, take_card)
            hand = _add_card(base.hands[player], take_card)
            hands = _replace_hand(base.hands, player, hand)
            return replace(
                base,
                hands=hands,
                discard=discard,
                history=base.history + (f"effect:five:{take_card}",),
            )

        raise ValueError(f"Unknown pending action: {pending!r}")

    def _effect_attack(self, state: GameState, player: int) -> GameState:
        next_player = self._next_alive_after(state, player)
        if next_player == player:
            return self._terminalize(state)
        return replace(
            state,
            current=next_player,
            turns_remaining=2,
            phase="action",
            history=state.history + (f"turn:attack:p{player}->p{next_player}",),
        )

    def _finish_one_turn(self, state: GameState, history_entry: str) -> GameState:
        if self.is_terminal(state):
            return self._terminalize(state)

        player = state.current
        if state.alive[player] and state.turns_remaining > 1:
            return replace(
                state,
                phase="action",
                turns_remaining=state.turns_remaining - 1,
                history=state.history + (history_entry,),
            )

        next_player = self._next_alive_after(state, player)
        if next_player == player:
            return self._terminalize(state)
        return replace(
            state,
            phase="action",
            current=next_player,
            turns_remaining=1,
            history=state.history + (history_entry,),
        )

    def _terminalize(self, state: GameState) -> GameState:
        if state.phase == "terminal":
            return state
        return replace(
            state,
            phase="terminal",
            current=TERMINAL,
            turns_remaining=0,
            pending_action=None,
            response_player=0,
            nope_count=0,
            nope_passes=0,
            history=state.history + ("terminal",),
        )

    def _discard_from_hand(
        self, state: GameState, player: int, cards: Iterable[str]
    ) -> Tuple[Tuple[Tuple[str, ...], ...], Tuple[str, ...]]:
        cards_tuple = tuple(cards)
        for card in cards_tuple:
            _validate_card(card)
        hand = _remove_cards(state.hands[player], cards_tuple)
        hands = _replace_hand(state.hands, player, hand)
        discard = state.discard + cards_tuple
        return hands, discard

    def _other_alive_players(
        self, state: GameState, player: int, require_cards: bool = False
    ) -> List[int]:
        return [
            p
            for p in range(state.num_players)
            if p != player
            and state.alive[p]
            and (not require_cards or len(state.hands[p]) > 0)
        ]

    def _alive_count(self, state: GameState) -> int:
        return sum(1 for alive in state.alive if alive)

    def _next_alive_after(self, state: GameState, player: int) -> int:
        for offset in range(1, state.num_players + 1):
            candidate = (player + offset) % state.num_players
            if state.alive[candidate]:
                return candidate
        return player

    def _can_play_nope(self, state: GameState, player: int) -> bool:
        if state.pending_action is None:
            return False
        if not state.alive[player] or NOPE not in state.hands[player]:
            return False
        actor = state.pending_action[1]
        return player != actor or state.nope_count > 0

    def _any_player_can_nope(self, state: GameState) -> bool:
        return any(self._can_play_nope(state, p) for p in range(state.num_players))


def _validate_card(card: str) -> None:
    if card not in CARD_INDEX:
        raise ValueError(f"Unknown card title: {card}")


def _sort_cards(cards: Iterable[str]) -> Tuple[str, ...]:
    return tuple(sorted(cards, key=lambda card: CARD_INDEX[card]))


def _add_card(hand: Tuple[str, ...], card: str) -> Tuple[str, ...]:
    _validate_card(card)
    return _sort_cards(hand + (card,))


def _remove_cards(hand: Tuple[str, ...], cards: Iterable[str]) -> Tuple[str, ...]:
    remaining = list(hand)
    for card in cards:
        _validate_card(card)
        try:
            remaining.remove(card)
        except ValueError as exc:
            raise ValueError(f"Hand does not contain required card: {card}") from exc
    return _sort_cards(remaining)


def _remove_one_from_tuple(cards: Tuple[str, ...], card: str) -> Tuple[str, ...]:
    items = list(cards)
    try:
        items.remove(card)
    except ValueError as exc:
        raise ValueError(f"Card not present: {card}") from exc
    return tuple(items)


def _replace_hand(
    hands: Tuple[Tuple[str, ...], ...], player: int, hand: Tuple[str, ...]
) -> Tuple[Tuple[str, ...], ...]:
    items = list(hands)
    items[player] = _sort_cards(hand)
    return tuple(items)


def _replace_bool(values: Tuple[bool, ...], index: int, value: bool) -> Tuple[bool, ...]:
    items = list(values)
    items[index] = value
    return tuple(items)


def _card_counts(cards: Iterable[str]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for card in cards:
        _validate_card(card)
        counts[card] = counts.get(card, 0) + 1
    return counts


def _counts_to_tuple(counts: Dict[str, int]) -> Tuple[Tuple[str, int], ...]:
    return tuple((card, counts[card]) for card in CARD_ORDER if counts.get(card, 0) > 0)


def _counts_from_tuple(items: Tuple[Tuple[str, int], ...]) -> Dict[str, int]:
    return {card: count for card, count in items if count > 0}


def _require_card_available(counts: Dict[str, int], card: str) -> None:
    _validate_card(card)
    if counts.get(card, 0) <= 0:
        raise ValueError(f"No remaining setup card: {card}")


def _empty_seen(num_players: int) -> Tuple[Tuple[str, ...], ...]:
    return tuple(() for _ in range(num_players))


def _format_cards(cards: Iterable[str]) -> str:
    cards_tuple = tuple(cards)
    if not cards_tuple:
        return "-"
    counts = _card_counts(cards_tuple)
    parts = []
    for card in CARD_ORDER:
        count = counts.get(card, 0)
        if count == 1:
            parts.append(card)
        elif count > 1:
            parts.append(f"{card}x{count}")
    return ",".join(parts)


def _parse_player(text: str) -> int:
    if not text.startswith("p"):
        raise ValueError(f"Expected player token, got: {text}")
    return int(text[1:])


def _deterministic_shuffle(deck: Tuple[str, ...]) -> Tuple[str, ...]:
    """A deterministic stand-in for the rulebook's shuffle instruction."""
    if len(deck) <= 1:
        return deck
    midpoint = (len(deck) + 1) // 2
    left = list(deck[:midpoint])
    right = list(deck[midpoint:])
    shuffled: List[str] = []
    while left or right:
        if right:
            shuffled.append(right.pop(0))
        if left:
            shuffled.append(left.pop(0))
    return tuple(shuffled)
