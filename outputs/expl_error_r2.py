"""Small, self-contained implementation of the supplied German rule sheet.

The rule sheet is internally inconsistent in a few places.  The explicit choices
made here are collected in ``Game.ASSUMPTIONS`` rather than hidden in the code.
"""

from collections import Counter
from copy import deepcopy
from dataclasses import dataclass, field
import itertools
import random
from typing import Any


EXPLODING = "Exploding Kitten"
DEFUSE = "Entschärfung"
FUTURE = "Blick in die Zukunft"
SKIP = "Hops!"
ATTACK = "Angriff"
NOPE = "Nö!"
SHUFFLE = "Mischen"
FAVOR = "Wunsch"

# Only these two cat-card titles survive in the supplied text extraction.  The
# sheet nevertheless says 56 cards and "4 jeder art", which requires five
# four-card cat families.  Neutral placeholders keep that unresolved gap visible.
CAT_TITLES = (
    "Zombiekatze",
    "Augenmampfende",
    "unbenannte Katzen-Karte 1",
    "unbenannte Katzen-Karte 2",
    "unbenannte Katzen-Karte 3",
)
CARD_TITLES = (EXPLODING, DEFUSE, FUTURE, SKIP, ATTACK, NOPE, SHUFFLE, FAVOR) + CAT_TITLES


@dataclass
class GameState:
    hands: list[list[str]]
    deck: list[str]                 # index 0 is the top
    discard: list[str] = field(default_factory=list)
    alive: list[bool] = field(default_factory=list)
    turn_player: int = 0
    turns_left: int = 1
    phase: str = "main"             # main, reaction, donate, defuse, insert, terminal
    reactor: int | None = None
    reaction_passes: int = 0
    pending: dict[str, Any] | None = None
    choice_player: int | None = None
    knowledge: list[tuple[str, ...]] = field(default_factory=list)
    rng_state: object | None = None
    winner: int | None = None


class Game:
    ASSUMPTIONS = (
        "The three cat-family titles missing from the supplied extraction are explicit placeholders.",
        "Angriff assigns two turns (the value printed twice, including the example), not three.",
        "An attacked player who plays Angriff ends that subturn and assigns two turns to the next player.",
        "Entschärfung may reinsert at any deck position, following the general rule rather than the later top-only sentence.",
        "Blick in die Zukunft reveals three cards and does not reorder them; the later unlabeled four-card effect is omitted.",
        "Nö! reactions proceed clockwise until every living player passes consecutively.",
    )

    def __init__(self, num_players: int = 2, seed: int | None = 0):
        if not 2 <= num_players <= 5:
            raise ValueError("num_players must be between 2 and 5")
        self.num_players = num_players
        self.seed = seed

    def initial_state(self) -> GameState:
        rng = random.Random(self.seed)
        ordinary: list[str] = []
        for title, count in ((ATTACK, 4), (SKIP, 4), (FAVOR, 4), (SHUFFLE, 4),
                             (FUTURE, 5), (NOPE, 5)):
            ordinary.extend([title] * count)
        for title in CAT_TITLES:
            ordinary.extend([title] * 4)
        rng.shuffle(ordinary)
        hands = [[] for _ in range(self.num_players)]
        for _ in range(7):
            for player in range(self.num_players):
                hands[player].append(ordinary.pop(0))
        for hand in hands:
            hand.append(DEFUSE)
        extra_defuses = 2 if self.num_players == 2 else 6 - self.num_players
        deck = ordinary + [DEFUSE] * extra_defuses + [EXPLODING] * (self.num_players - 1)
        rng.shuffle(deck)
        return GameState(
            hands=hands, deck=deck, alive=[True] * self.num_players,
            knowledge=[tuple() for _ in range(self.num_players)], rng_state=rng.getstate()
        )

    def current_player(self, state: GameState) -> int:
        if state.phase == "reaction":
            assert state.reactor is not None
            return state.reactor
        if state.phase == "donate":
            assert state.choice_player is not None
            return state.choice_player
        return state.turn_player

    def legal_actions(self, state: GameState) -> list[str]:
        if self.is_terminal(state):
            return []
        player = self.current_player(state)
        hand = state.hands[player]
        if state.phase == "reaction":
            actions = ["reaction:pass"]
            pending = state.pending or {}
            if NOPE in hand and (pending.get("nope_count", 0) > 0 or player != pending.get("actor")):
                actions.append("reaction:Nö!")
            return actions
        if state.phase == "donate":
            recipient = state.pending["actor"]  # type: ignore[index]
            return [f"give:{card}->player:{recipient}" for card in sorted(set(hand))]
        if state.phase == "defuse":
            actions = ["explode:voluntarily"]
            if DEFUSE in hand:
                actions.insert(0, "react:Entschärfung")
            return actions
        if state.phase == "insert":
            return [f"place:Exploding Kitten@position:{i}" for i in range(len(state.deck) + 1)]

        actions = ["draw"]
        counts = Counter(hand)
        for card in (FUTURE, SKIP, ATTACK, SHUFFLE):
            if counts[card]:
                actions.append(f"play:{card}")
        others = [p for p in range(self.num_players) if state.alive[p] and p != player]
        if counts[FAVOR]:
            actions.extend(f"play:Wunsch->player:{target}" for target in others)
        for card in sorted(counts):
            if counts[card] >= 2:
                actions.extend(f"pair:{card}->player:{target}" for target in others)
            if counts[card] >= 3:
                for target in others:
                    actions.extend(
                        f"triple:{card}->player:{target};request:{wanted}"
                        for wanted in CARD_TITLES
                    )
        distinct = sorted(counts)
        if len(distinct) >= 5 and state.discard:
            takeable = sorted(set(state.discard))
            for chosen in itertools.combinations(distinct, 5):
                cards = "|".join(chosen)
                actions.extend(f"five:{cards};take:{card}" for card in takeable)
        return actions

    def apply_action(self, state: GameState, action: str) -> GameState:
        if action not in self.legal_actions(state):
            raise ValueError(f"illegal action: {action}")
        s = deepcopy(state)
        player = self.current_player(s)
        if s.phase == "reaction":
            if action == "reaction:pass":
                s.reaction_passes += 1
                if s.reaction_passes >= sum(s.alive):
                    self._settle_pending(s)
                else:
                    s.reactor = self._next_alive(s, player)
            else:
                s.hands[player].remove(NOPE)
                s.discard.append(NOPE)
                s.pending["nope_count"] += 1  # type: ignore[index]
                s.reaction_passes = 0
                s.reactor = self._next_alive(s, player)
            return s
        if s.phase == "donate":
            card = action[len("give:"):].rsplit("->player:", 1)[0]
            recipient = s.pending["actor"]  # type: ignore[index]
            s.hands[player].remove(card)
            s.hands[recipient].append(card)
            s.phase, s.pending, s.choice_player = "main", None, None
            return s
        if s.phase == "defuse":
            if action == "react:Entschärfung":
                s.hands[player].remove(DEFUSE)
                s.discard.append(DEFUSE)
                s.phase = "insert"
            else:
                self._eliminate(s, player, include_exploding=True)
            return s
        if s.phase == "insert":
            pos = int(action.rsplit(":", 1)[1])
            s.deck.insert(pos, EXPLODING)
            self._finish_draw_turn(s)
            return s

        if action == "draw":
            card = s.deck.pop(0)
            s.knowledge[player] = tuple()
            if card == EXPLODING:
                s.phase = "defuse"
            else:
                s.hands[player].append(card)
                self._finish_draw_turn(s)
            return s

        pending: dict[str, Any] = {"actor": player, "nope_count": 0}
        if action.startswith("play:"):
            rest = action[len("play:"):]
            if "->player:" in rest:
                card, target_text = rest.rsplit("->player:", 1)
                pending.update(kind="favor", target=int(target_text), cards=[card])
            else:
                card = rest
                pending.update(kind={FUTURE: "future", SKIP: "skip", ATTACK: "attack", SHUFFLE: "shuffle"}[card], cards=[card])
        elif action.startswith("pair:"):
            card, target_text = action[len("pair:"):].rsplit("->player:", 1)
            pending.update(kind="pair", target=int(target_text), cards=[card, card])
        elif action.startswith("triple:"):
            left, wanted = action[len("triple:"):].split(";request:", 1)
            card, target_text = left.rsplit("->player:", 1)
            pending.update(kind="triple", target=int(target_text), wanted=wanted, cards=[card] * 3)
        else:
            left, wanted = action[len("five:"):].split(";take:", 1)
            pending.update(kind="five", wanted=wanted, cards=left.split("|"))
        for card in pending["cards"]:
            s.hands[player].remove(card)
            s.discard.append(card)
        s.pending = pending
        s.phase = "reaction"
        s.reactor = self._next_alive(s, player)
        s.reaction_passes = 0
        return s

    def _settle_pending(self, s: GameState) -> None:
        p = s.pending
        assert p is not None
        cancelled = p["nope_count"] % 2 == 1
        actor, kind = p["actor"], p["kind"]
        s.phase, s.reactor, s.reaction_passes = "main", None, 0
        if cancelled:
            s.pending = None
            return
        if kind == "future":
            s.knowledge[actor] = tuple(s.deck[:3])
        elif kind == "shuffle":
            rng = random.Random()
            rng.setstate(s.rng_state)
            rng.shuffle(s.deck)
            s.rng_state = rng.getstate()
            s.knowledge = [tuple() for _ in s.knowledge]
        elif kind == "skip":
            s.pending = None
            self._advance_to(s, self._next_alive(s, actor), 1)
            return
        elif kind == "attack":
            s.pending = None
            self._advance_to(s, self._next_alive(s, actor), 2)
            return
        elif kind == "favor":
            target = p["target"]
            if s.hands[target]:
                s.phase, s.choice_player = "donate", target
                return
        elif kind == "pair":
            target = p["target"]
            if s.hands[target]:
                rng = random.Random()
                rng.setstate(s.rng_state)
                index = rng.randrange(len(s.hands[target]))
                s.hands[actor].append(s.hands[target].pop(index))
                s.rng_state = rng.getstate()
        elif kind == "triple":
            target, wanted = p["target"], p["wanted"]
            if wanted in s.hands[target]:
                s.hands[target].remove(wanted)
                s.hands[actor].append(wanted)
        elif kind == "five":
            wanted = p["wanted"]
            # Remove the most recent matching discard; this also permits taking
            # one of the five just played, as "beliebige Karte" says.
            reverse_index = s.discard[::-1].index(wanted)
            s.discard.pop(len(s.discard) - 1 - reverse_index)
            if wanted == EXPLODING:
                s.pending = None
                s.phase = "defuse"
                return
            s.hands[actor].append(wanted)
        s.pending = None

    def _finish_draw_turn(self, s: GameState) -> None:
        if s.turns_left > 1:
            s.turns_left -= 1
            s.phase = "main"
        else:
            self._advance_to(s, self._next_alive(s, s.turn_player), 1)

    def _advance_to(self, s: GameState, player: int, turns: int) -> None:
        s.turn_player, s.turns_left, s.phase = player, turns, "main"

    def _next_alive(self, s: GameState, player: int) -> int:
        nxt = (player + 1) % self.num_players
        while not s.alive[nxt]:
            nxt = (nxt + 1) % self.num_players
        return nxt

    def _eliminate(self, s: GameState, player: int, include_exploding: bool) -> None:
        s.discard.extend(s.hands[player])
        s.hands[player].clear()
        if include_exploding:
            s.discard.append(EXPLODING)
        s.alive[player] = False
        s.pending = None
        living = [p for p, alive in enumerate(s.alive) if alive]
        if len(living) == 1:
            s.winner, s.phase = living[0], "terminal"
        else:
            self._advance_to(s, self._next_alive(s, player), 1)

    def is_terminal(self, state: GameState) -> bool:
        return state.winner is not None

    def returns(self, state: GameState) -> list[int]:
        if not self.is_terminal(state):
            return [0] * self.num_players
        return [1 if p == state.winner else -1 for p in range(self.num_players)]

    def render(self, state: GameState) -> str:
        viewer = self.current_player(state)
        lines = [f"phase={state.phase} current_player={viewer} deck={len(state.deck)}"]
        for p in range(self.num_players):
            status = "alive" if state.alive[p] else "exploded"
            cards = (", ".join(state.hands[p]) or "-") if p == viewer else f"{len(state.hands[p])} hidden cards"
            lines.append(f"player {p} ({status}): {cards}")
        lines.append(f"discard: {', '.join(state.discard) or '-'}")
        if state.phase == "main" and state.knowledge[state.turn_player]:
            lines.append("Blick in die Zukunft: " + ", ".join(state.knowledge[state.turn_player]))
        return "\n".join(lines)

    def action_to_name(self, action: str) -> str:
        return action

    def name_to_action(self, name: str) -> str:
        return name
