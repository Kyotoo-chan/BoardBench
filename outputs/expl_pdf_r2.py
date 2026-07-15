"""Small, self-contained implementation of the supplied Exploding Kittens rules.

Only the German rulebook supplied with this task is used as a rules source.
Unspecified timing details are documented in Game's docstring.
"""

from collections import Counter
from dataclasses import dataclass, replace
from itertools import combinations
import random
from typing import Optional, Tuple


EXPLODING = "Exploding Kitten"
DEFUSE = "Entschärfung"
ATTACK = "Angriff"
SKIP = "Hops!"
FAVOR = "Wunsch"
SHUFFLE = "Mischen"
SEE = "Blick in die Zukunft"
NOPE = "NÖ!"
CAT_CARDS = (
    # The booklet identifies these only as five pictured Katzen-Karten kinds;
    # it does not supply readable effect labels for the individual artworks.
    "Katzen-Karte Art 1",
    "Katzen-Karte Art 2",
    "Katzen-Karte Art 3",
    "Katzen-Karte Art 4",
    "Katzen-Karte Art 5",
)
CARD_TYPES = (EXPLODING, DEFUSE, ATTACK, SKIP, FAVOR, SHUFFLE, SEE, NOPE) + CAT_CARDS


@dataclass(frozen=True)
class GameState:
    hands: Tuple[Tuple[str, ...], ...]
    deck: Tuple[str, ...]
    discard: Tuple[str, ...]
    alive: Tuple[bool, ...]
    player: int
    turns_left: int = 1
    phase: str = "turn"
    # Pending effect: (kind, actor, optional arguments...).
    pending: Tuple[str, ...] = ()
    reaction_player: int = -1
    reaction_passes: int = 0
    nope_count: int = 0
    peek: Tuple[str, ...] = ()
    rng_state: object = None
    winner: Optional[int] = None


class Game:
    """Rules engine for 2--5 players (two players by default).

    Explicit minimal assumptions where the booklet is silent:
    * NÖ! response priority proceeds clockwise, beginning after the card player.
      An effect resolves after every living player passes consecutively; playing
      NÖ! resets that pass count.  An odd number cancels the effect.
    * A player may decline an available Entschärfung and explode.
    * A random Pärchen theft is sampled by the seeded PRNG at resolution time.
    * Targets with no cards are unavailable for Wunsch/Pärchen.
    * The five pictured, individually unlabeled Katzen-Karten artworks receive
      stable identifiers ``Katzen-Karte Art 1`` through ``Art 5``.
    """

    def __init__(self, num_players: int = 2, seed: Optional[int] = 0):
        if not 2 <= num_players <= 5:
            raise ValueError("num_players must be between 2 and 5")
        self.num_players = num_players
        self.seed = seed

    def initial_state(self) -> GameState:
        rng = random.Random(self.seed)
        # The five pictured cat-card kinds have four cards each.
        main = (
            [ATTACK] * 4 + [SKIP] * 4 + [FAVOR] * 4 + [SHUFFLE] * 4
            + [SEE] * 5 + [NOPE] * 5
        )
        for card in CAT_CARDS:
            main.extend([card] * 4)
        rng.shuffle(main)
        hands = []
        for _ in range(self.num_players):
            hand = [main.pop() for _ in range(7)] + [DEFUSE]
            hands.append(tuple(sorted(hand)))
        main.extend([EXPLODING] * (self.num_players - 1))
        # The two-player variant returns all but two remaining Defuses to the box.
        remaining_defuses = 2 if self.num_players == 2 else 6 - self.num_players
        main.extend([DEFUSE] * remaining_defuses)
        rng.shuffle(main)
        return GameState(
            hands=tuple(hands), deck=tuple(main), discard=(),
            alive=(True,) * self.num_players, player=0,
            rng_state=rng.getstate(),
        )

    def current_player(self, state: GameState) -> int:
        return -1 if self.is_terminal(state) else (
            state.reaction_player if state.phase == "nope" else state.player
        )

    def legal_actions(self, state: GameState):
        if self.is_terminal(state):
            return []
        if state.phase == "turn":
            return self._turn_actions(state)
        if state.phase == "nope":
            actions = ["NÖ!-Fenster:passen"]
            if NOPE in state.hands[state.reaction_player]:
                actions.append("NÖ!-Fenster:spielen:NÖ!")
            return actions
        if state.phase == "favor":
            target = state.player
            return [f"Wunsch:geben:{c}" for c in sorted(set(state.hands[target]))]
        if state.phase == "defuse":
            return ["Exploding Kitten:explodieren", "Exploding Kitten:spielen:Entschärfung"]
        if state.phase == "place":
            return [f"platzieren:Exploding Kitten:Position {i + 1} von oben"
                    for i in range(len(state.deck) + 1)]
        if state.phase == "peek":
            return ["Blick in die Zukunft:weiter"]
        raise ValueError(f"unknown phase {state.phase!r}")

    def _turn_actions(self, state: GameState):
        p = state.player
        hand = state.hands[p]
        counts = Counter(hand)
        actions = ["passen und ziehen", "ziehen"]
        for card in (ATTACK, SKIP, SHUFFLE, SEE):
            if counts[card]:
                actions.append(f"spielen:{card}")
        if counts[FAVOR]:
            for target in self._targets_with_cards(state, p):
                actions.append(f"spielen:{FAVOR}:von:Spieler {target}")

        targets = self._targets_with_cards(state, p)
        for card in sorted(counts):
            if counts[card] >= 2:
                for target in targets:
                    actions.append(f"kombination:Pärchen:{card}:von:Spieler {target}")
            if counts[card] >= 3:
                for target in targets:
                    for requested in CARD_TYPES:
                        actions.append(
                            f"kombination:Drilling:{card}:von:Spieler {target}:Karte:{requested}"
                        )
        distinct = sorted(counts)
        if len(distinct) >= 5 and state.discard:
            for cards in combinations(distinct, 5):
                used = "+".join(cards)
                for wanted in sorted(set(state.discard)):
                    actions.append(f"kombination:Fünfling:{used}:nehmen:{wanted}")
        return actions

    def apply_action(self, state: GameState, action):
        if action not in self.legal_actions(state):
            raise ValueError(f"illegal action: {action!r}")
        if state.phase == "turn":
            return self._apply_turn(state, action)
        if state.phase == "nope":
            return self._apply_nope(state, action)
        if state.phase == "favor":
            card = action[len("Wunsch:geben:"):]
            actor = int(state.pending[1])
            s = self._move_hand_card(state, state.player, actor, card)
            return replace(s, player=actor, phase="turn", pending=())
        if state.phase == "defuse":
            if action.endswith("Entschärfung"):
                s = self._remove_hand_cards(state, state.player, (DEFUSE,))
                return replace(s, discard=s.discard + (DEFUSE,), phase="place")
            return self._explode(state, state.player)
        if state.phase == "place":
            position = int(action.split("Position ", 1)[1].split(" ", 1)[0]) - 1
            deck = state.deck[:position] + (EXPLODING,) + state.deck[position:]
            return self._finish_draw(replace(state, deck=deck, phase="turn", pending=()))
        if state.phase == "peek":
            return replace(state, phase="turn", pending=(), peek=())
        raise ValueError("unreachable")

    def _apply_turn(self, state: GameState, action: str) -> GameState:
        if action in ("ziehen", "passen und ziehen"):
            return self._draw(state)
        if action.startswith("spielen:"):
            rest = action[len("spielen:"):]
            if rest.startswith(FAVOR + ":von:Spieler "):
                target = int(rest.rsplit(" ", 1)[1])
                return self._start_card(state, FAVOR, ("favor", str(state.player), str(target)))
            card = rest
            effects = {
                ATTACK: ("attack", str(state.player)),
                SKIP: ("skip", str(state.player)),
                SHUFFLE: ("shuffle", str(state.player)),
                SEE: ("see", str(state.player)),
            }
            return self._start_card(state, card, effects[card])
        if action.startswith("kombination:Pärchen:"):
            body = action[len("kombination:Pärchen:"):]
            card, target_text = body.rsplit(":von:Spieler ", 1)
            s = self._remove_hand_cards(state, state.player, (card, card))
            s = replace(s, discard=s.discard + (card, card))
            return self._start_nope(s, ("pair", str(state.player), target_text))
        if action.startswith("kombination:Drilling:"):
            body = action[len("kombination:Drilling:"):]
            card, tail = body.rsplit(":von:Spieler ", 1)
            target_text, requested = tail.split(":Karte:", 1)
            s = self._remove_hand_cards(state, state.player, (card, card, card))
            s = replace(s, discard=s.discard + (card, card, card))
            return self._start_nope(s, ("triple", str(state.player), target_text, requested))
        body = action[len("kombination:Fünfling:"):]
        used, wanted = body.split(":nehmen:", 1)
        cards = tuple(used.split("+"))
        s = self._remove_hand_cards(state, state.player, cards)
        s = replace(s, discard=s.discard + cards)
        return self._start_nope(s, ("five", str(state.player), wanted))

    def _start_card(self, state, card, effect):
        s = self._remove_hand_cards(state, state.player, (card,))
        s = replace(s, discard=s.discard + (card,))
        return self._start_nope(s, effect)

    def _start_nope(self, state, effect):
        first = self._next_alive(state, state.player)
        return replace(state, phase="nope", pending=effect, reaction_player=first,
                       reaction_passes=0, nope_count=0)

    def _apply_nope(self, state, action):
        rp = state.reaction_player
        if action.endswith("spielen:NÖ!"):
            s = self._remove_hand_cards(state, rp, (NOPE,))
            return replace(s, discard=s.discard + (NOPE,), nope_count=s.nope_count + 1,
                           reaction_passes=0, reaction_player=self._next_alive(s, rp))
        passes = state.reaction_passes + 1
        if passes < sum(state.alive):
            return replace(state, reaction_passes=passes,
                           reaction_player=self._next_alive(state, rp))
        if state.nope_count % 2:
            return replace(state, phase="turn", pending=(), reaction_player=-1,
                           reaction_passes=0, nope_count=0)
        return self._resolve_effect(replace(state, phase="turn", reaction_player=-1,
                                            reaction_passes=0, nope_count=0))

    def _resolve_effect(self, state):
        kind = state.pending[0]
        actor = int(state.pending[1])
        if kind == "attack":
            nxt = self._next_alive(state, actor)
            return replace(state, player=nxt, turns_left=2, phase="turn", pending=())
        if kind == "skip":
            return self._finish_draw(replace(state, player=actor, phase="turn", pending=()))
        if kind == "shuffle":
            rng = self._rng(state)
            deck = list(state.deck)
            rng.shuffle(deck)
            return replace(state, player=actor, deck=tuple(deck), rng_state=rng.getstate(),
                           phase="turn", pending=())
        if kind == "see":
            return replace(state, player=actor, phase="peek", peek=state.deck[:3])
        if kind == "favor":
            return replace(state, player=int(state.pending[2]), phase="favor")
        if kind == "pair":
            target = int(state.pending[2])
            rng = self._rng(state)
            card = rng.choice(state.hands[target])
            s = self._move_hand_card(state, target, actor, card)
            return replace(s, player=actor, phase="turn", pending=(), rng_state=rng.getstate())
        if kind == "triple":
            target, wanted = int(state.pending[2]), state.pending[3]
            s = state
            if wanted in state.hands[target]:
                s = self._move_hand_card(state, target, actor, wanted)
            return replace(s, player=actor, phase="turn", pending=())
        if kind == "five":
            wanted = state.pending[2]
            discard = list(state.discard)
            discard.remove(wanted)
            hands = [list(h) for h in state.hands]
            hands[actor].append(wanted)
            hands[actor].sort()
            return replace(state, hands=tuple(tuple(h) for h in hands), discard=tuple(discard),
                           player=actor, phase="turn", pending=())
        raise ValueError(f"unknown effect {kind}")

    def _draw(self, state):
        p = state.player
        if not state.deck:
            # The booklet explicitly says this cannot happen: all but one player
            # must encounter an Exploding Kitten before the pile can be empty.
            raise RuntimeError("rulebook invariant violated: empty Spielstapel")
        card, deck = state.deck[0], state.deck[1:]
        s = replace(state, deck=deck)
        if card == EXPLODING:
            if DEFUSE in s.hands[p]:
                return replace(s, phase="defuse", pending=("drawn", str(p)))
            return self._explode(s, p)
        hands = [list(h) for h in s.hands]
        hands[p].append(card)
        hands[p].sort()
        return self._finish_draw(replace(s, hands=tuple(tuple(h) for h in hands)))

    def _finish_draw(self, state):
        if state.turns_left > 1:
            return replace(state, turns_left=state.turns_left - 1, phase="turn",
                           pending=(), peek=())
        return replace(state, player=self._next_alive(state, state.player), turns_left=1,
                       phase="turn", pending=(), peek=())

    def _explode(self, state, player):
        discard = state.discard + (EXPLODING,) + state.hands[player]
        hands = list(state.hands)
        hands[player] = ()
        alive = list(state.alive)
        alive[player] = False
        survivors = [i for i, ok in enumerate(alive) if ok]
        if len(survivors) == 1:
            return replace(state, hands=tuple(hands), alive=tuple(alive), discard=discard,
                           phase="terminal", pending=(), winner=survivors[0])
        nxt = self._next_alive(replace(state, alive=tuple(alive)), player)
        return replace(state, hands=tuple(hands), alive=tuple(alive), discard=discard,
                       player=nxt, turns_left=1, phase="turn", pending=())

    def is_terminal(self, state: GameState) -> bool:
        return state.winner is not None

    def returns(self, state: GameState):
        if not self.is_terminal(state):
            return [0] * self.num_players
        return [1 if i == state.winner else -1 for i in range(self.num_players)]

    def render(self, state: GameState) -> str:
        if self.is_terminal(state):
            return f"Spielende — Spieler {state.winner} gewinnt."
        viewer = self.current_player(state)
        lines = [f"Phase: {state.phase}", f"Am Zug: Spieler {viewer}",
                 f"Spielstapel: {len(state.deck)} Karten",
                 "Ablagestapel: " + (state.discard[-1] if state.discard else "leer")]
        for i, hand in enumerate(state.hands):
            shown = ", ".join(hand) if i == viewer else f"{len(hand)} verdeckte Karten"
            lines.append(f"Spieler {i}: {shown}")
        if state.phase == "peek":
            lines.append("Blick in die Zukunft (oben zuerst): " + ", ".join(state.peek))
        return "\n".join(lines)

    def action_to_name(self, action):
        if not isinstance(action, str):
            raise ValueError("actions are strings")
        return action

    def name_to_action(self, name):
        if not isinstance(name, str):
            raise ValueError("action names are strings")
        return name

    def _targets_with_cards(self, state, actor):
        return [i for i in range(self.num_players)
                if i != actor and state.alive[i] and state.hands[i]]

    def _next_alive(self, state, player):
        for step in range(1, self.num_players + 1):
            candidate = (player + step) % self.num_players
            if state.alive[candidate]:
                return candidate
        return player

    @staticmethod
    def _remove_hand_cards(state, player, cards):
        hands = [list(h) for h in state.hands]
        for card in cards:
            hands[player].remove(card)
        hands[player].sort()
        return replace(state, hands=tuple(tuple(h) for h in hands))

    @staticmethod
    def _move_hand_card(state, source, target, card):
        hands = [list(h) for h in state.hands]
        hands[source].remove(card)
        hands[target].append(card)
        hands[source].sort()
        hands[target].sort()
        return replace(state, hands=tuple(tuple(h) for h in hands))

    @staticmethod
    def _rng(state):
        rng = random.Random()
        rng.setstate(state.rng_state)
        return rng
