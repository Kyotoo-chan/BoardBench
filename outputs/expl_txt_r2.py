"""A small, self-contained implementation of the supplied German rulebook.

The extracted rulebook names only two of the five four-card Katzen-Karte
families.  The three missing printed titles are represented by conspicuous
placeholders below; no effects are assigned to them.
"""

from dataclasses import dataclass, field
import copy
import itertools
import random


EXPLODING = "Exploding Kitten"
DEFUSE = "Entschärfung"
ATTACK = "Angriff"
SKIP = "Hops!"
FAVOR = "Wunsch"
SHUFFLE = "Mischen"
SEE = "Blick in die Zukunft"
NOPE = "Nö!"
CAT_TYPES = (
    "Zombiekatze",
    "Augenmampfende",
    "Unbenannte Katzen-Karte A",
    "Unbenannte Katzen-Karte B",
    "Unbenannte Katzen-Karte C",
)

# Public actions are immutable tuples so deepcopy/equality are unsurprising.
Action = tuple


@dataclass
class GameState:
    hands: list[list[str]]
    deck: list[str]
    discard: list[str]
    alive: list[bool]
    player: int = 0
    turns_left: int = 1
    phase: str = "turn"             # turn, reaction, donation, defuse, terminal
    pending: dict | None = None
    donor: int | None = None
    recipient: int | None = None
    drawn_kitten: bool = False
    knowledge: dict[int, tuple[str, ...]] = field(default_factory=dict)
    winner: int | None = None
    rng: random.Random = field(default_factory=random.Random, repr=False)


class Game:
    def __init__(self, num_players: int = 2, seed: int | None = 0):
        if not 2 <= num_players <= 5:
            raise ValueError("the rulebook allows 2–5 players")
        self.num_players = num_players
        self.seed = seed

    def initial_state(self) -> GameState:
        rng = random.Random(self.seed)
        ordinary = (
            [ATTACK] * 4 + [SKIP] * 4 + [FAVOR] * 4 + [SHUFFLE] * 4
            + [SEE] * 5 + [NOPE] * 5
            + [title for title in CAT_TYPES for _ in range(4)]
        )
        rng.shuffle(ordinary)
        hands = [[] for _ in range(self.num_players)]
        for _ in range(7):
            for hand in hands:
                hand.append(ordinary.pop())
        for hand in hands:
            hand.append(DEFUSE)

        # The two-player variant explicitly puts exactly two Entschärfung in;
        # otherwise all Entschärfung left after the initial deal are used.
        extra_defuses = 2 if self.num_players == 2 else 6 - self.num_players
        deck = ordinary + [DEFUSE] * extra_defuses + [EXPLODING] * (self.num_players - 1)
        rng.shuffle(deck)
        return GameState(hands, deck, [], [True] * self.num_players, rng=rng)

    def current_player(self, state: GameState) -> int:
        if state.phase == "reaction":
            return state.pending["responder"]
        if state.phase == "donation":
            return state.donor
        return state.player

    def legal_actions(self, state: GameState) -> list[Action]:
        if self.is_terminal(state):
            return []
        if state.phase == "reaction":
            p = state.pending["responder"]
            actions = [("reaction-pass",)]
            if NOPE in state.hands[p]:
                actions.append(("reaction-nope",))
            return actions
        if state.phase == "donation":
            hand = state.hands[state.donor]
            return [("donate", c) for c in sorted(set(hand))] or [("donate-nothing",)]
        if state.phase == "defuse":
            actions = [("explode",)]
            if DEFUSE in state.hands[state.player]:
                n = len(state.deck)
                positions = ["top"]
                positions += [("after", i) for i in range(1, n)]
                if n:
                    positions.append("bottom")
                actions += [("defuse", pos) for pos in positions]
            return actions

        p = state.player
        hand = state.hands[p]
        actions: list[Action] = [("draw",)]
        for card in (SKIP, ATTACK, SHUFFLE, SEE):
            if card in hand:
                actions.append(("play", card))
        if FAVOR in hand:
            actions += [("favor", q) for q in self._others(state, p)]

        counts = {c: hand.count(c) for c in set(hand)}
        for card in sorted(c for c, n in counts.items() if n >= 2):
            actions += [("pair", card, q) for q in self._others(state, p)]
        for card in sorted(c for c, n in counts.items() if n >= 3):
            for q in self._others(state, p):
                for wanted in self._all_titles():
                    actions.append(("triplet", card, q, wanted))

        distinct = sorted(counts)
        if len(distinct) >= 5 and state.discard:
            for cards in itertools.combinations(distinct, 5):
                for take in sorted(set(state.discard)):
                    actions.append(("five", cards, take))
        return actions

    def apply_action(self, state: GameState, action: Action) -> GameState:
        if action not in self.legal_actions(state):
            raise ValueError(f"illegal action: {action!r}")
        s = copy.deepcopy(state)
        kind = action[0]
        if kind == "reaction-pass":
            self._reaction_pass(s)
        elif kind == "reaction-nope":
            p = s.pending["responder"]
            s.hands[p].remove(NOPE)
            s.discard.append(NOPE)
            s.pending["cancelled"] = not s.pending["cancelled"]
            s.pending["last_actor"] = p
            s.pending["passes"] = 0
            s.pending["responder"] = self._next_alive(s, p)
        elif kind == "donate":
            s.hands[s.donor].remove(action[1])
            s.hands[s.recipient].append(action[1])
            self._clear_donation(s)
        elif kind == "donate-nothing":
            self._clear_donation(s)
        elif kind == "explode":
            self._kill(s, s.player)
        elif kind == "defuse":
            s.hands[s.player].remove(DEFUSE)
            s.discard.append(DEFUSE)
            pos = action[1]
            index = 0 if pos == "top" else len(s.deck) if pos == "bottom" else pos[1]
            s.deck.insert(index, EXPLODING)
            s.drawn_kitten = False
            s.phase = "turn"
            self._finish_one_turn(s)
        elif kind == "draw":
            self._draw(s)
        else:
            effect = action
            cards = self._cards_spent(action)
            for card in cards:
                s.hands[s.player].remove(card)
                s.discard.append(card)
            self._offer_reaction(s, s.player, effect)
        return s

    def is_terminal(self, state: GameState) -> bool:
        return state.winner is not None or sum(state.alive) <= 1

    def returns(self, state: GameState) -> list[int]:
        if not self.is_terminal(state):
            return [0] * self.num_players
        winner = state.winner
        if winner is None:
            winner = next(i for i, alive in enumerate(state.alive) if alive)
        return [1 if i == winner else -1 for i in range(self.num_players)]

    def render(self, state: GameState) -> str:
        viewer = self.current_player(state)
        lines = [
            f"phase={state.phase} current_player={viewer} turns_left={state.turns_left}",
            f"deck={len(state.deck)} discard={state.discard}",
        ]
        for i, hand in enumerate(state.hands):
            status = "alive" if state.alive[i] else "exploded"
            shown = sorted(hand) if i == viewer else f"{len(hand)} hidden cards"
            lines.append(f"player {i} ({status}): {shown}")
        if viewer in state.knowledge:
            lines.append(f"Blick in die Zukunft: {state.knowledge[viewer]}")
        return "\n".join(lines)

    def action_to_name(self, action: Action) -> str:
        k = action[0]
        if k == "draw": return "Passen:draw"
        if k == "play": return f"play:{action[1]}"
        if k == "favor": return f"play:{FAVOR}->player:{action[1]}"
        if k == "pair": return f"pair:{action[1]}->player:{action[2]}"
        if k == "triplet": return f"triplet:{action[1]}->player:{action[2]}:request:{action[3]}"
        if k == "five": return f"five:{'|'.join(action[1])}:take:{action[2]}"
        if k == "reaction-pass": return "reaction:pass"
        if k == "reaction-nope": return f"reaction:{NOPE}"
        if k == "donate": return f"donate:{action[1]}"
        if k == "donate-nothing": return "donate:nothing"
        if k == "explode": return "Exploding Kitten:explode"
        if k == "defuse":
            pos = action[1]
            label = pos if isinstance(pos, str) else f"after:{pos[1]}"
            return f"{DEFUSE}:place:{label}"
        raise ValueError(action)

    def name_to_action(self, name: str) -> Action:
        if name == "Passen:draw": return ("draw",)
        if name.startswith("play:"):
            rest = name[5:]
            marker = "->player:"
            if marker in rest:
                card, p = rest.split(marker, 1)
                if card != FAVOR: raise ValueError(name)
                return ("favor", int(p))
            return ("play", rest)
        if name.startswith("pair:"):
            card, p = name[5:].split("->player:", 1)
            return ("pair", card, int(p))
        if name.startswith("triplet:"):
            card, rest = name[8:].split("->player:", 1)
            p, wanted = rest.split(":request:", 1)
            return ("triplet", card, int(p), wanted)
        if name.startswith("five:"):
            cards, take = name[5:].split(":take:", 1)
            return ("five", tuple(cards.split("|")), take)
        if name == "reaction:pass": return ("reaction-pass",)
        if name == f"reaction:{NOPE}": return ("reaction-nope",)
        if name == "donate:nothing": return ("donate-nothing",)
        if name.startswith("donate:"): return ("donate", name[7:])
        if name == "Exploding Kitten:explode": return ("explode",)
        prefix = f"{DEFUSE}:place:"
        if name.startswith(prefix):
            pos = name[len(prefix):]
            return ("defuse", pos if pos in ("top", "bottom") else ("after", int(pos.split(":")[1])))
        raise ValueError(name)

    # ---- transition helpers -------------------------------------------------
    def _all_titles(self) -> tuple[str, ...]:
        return (EXPLODING, DEFUSE, ATTACK, SKIP, FAVOR, SHUFFLE, SEE, NOPE) + CAT_TYPES

    def _others(self, s: GameState, p: int) -> list[int]:
        return [q for q, alive in enumerate(s.alive) if alive and q != p]

    def _next_alive(self, s: GameState, p: int) -> int:
        q = (p + 1) % self.num_players
        while not s.alive[q]:
            q = (q + 1) % self.num_players
        return q

    def _cards_spent(self, action: Action) -> list[str]:
        if action[0] == "play": return [action[1]]
        if action[0] == "favor": return [FAVOR]
        if action[0] in ("pair", "triplet"):
            return [action[1]] * (2 if action[0] == "pair" else 3)
        if action[0] == "five": return list(action[1])
        raise ValueError(action)

    def _offer_reaction(self, s: GameState, actor: int, effect: Action) -> None:
        if any(NOPE in s.hands[q] for q in self._others(s, actor)):
            s.phase = "reaction"
            s.pending = {"effect": effect, "actor": actor, "cancelled": False,
                         "last_actor": actor, "responder": self._next_alive(s, actor), "passes": 0}
        else:
            self._resolve_effect(s, effect, actor)

    def _reaction_pass(self, s: GameState) -> None:
        p = s.pending["responder"]
        s.pending["passes"] += 1
        if s.pending["passes"] >= sum(s.alive) - 1:
            pending = s.pending
            s.pending = None
            s.phase = "turn"
            if not pending["cancelled"]:
                self._resolve_effect(s, pending["effect"], pending["actor"])
        else:
            s.pending["responder"] = self._next_alive(s, p)

    def _resolve_effect(self, s: GameState, effect: Action, actor: int) -> None:
        k = effect[0]
        if k == "play":
            card = effect[1]
            if card == SKIP:
                self._finish_one_turn(s)
            elif card == ATTACK:
                nxt = self._next_alive(s, actor)
                s.player, s.turns_left = nxt, 2
                s.knowledge.clear()
            elif card == SHUFFLE:
                s.rng.shuffle(s.deck)
                s.knowledge.clear()
            elif card == SEE:
                s.knowledge[actor] = tuple(s.deck[:3])
        elif k == "favor":
            target = effect[1]
            if s.hands[target]:
                s.phase, s.donor, s.recipient = "donation", target, actor
        elif k == "pair":
            target = effect[2]
            if s.hands[target]:
                i = s.rng.randrange(len(s.hands[target]))
                s.hands[actor].append(s.hands[target].pop(i))
        elif k == "triplet":
            target, wanted = effect[2], effect[3]
            if wanted in s.hands[target]:
                s.hands[target].remove(wanted)
                s.hands[actor].append(wanted)
        elif k == "five":
            wanted = effect[2]
            s.discard.remove(wanted)
            s.hands[actor].append(wanted)

    def _clear_donation(self, s: GameState) -> None:
        s.phase, s.donor, s.recipient = "turn", None, None

    def _draw(self, s: GameState) -> None:
        # The rulebook promises the deck cannot empty before the game ends.
        card = s.deck.pop(0)
        s.knowledge.clear()
        if card == EXPLODING:
            s.drawn_kitten = True
            if DEFUSE in s.hands[s.player]:
                s.phase = "defuse"
            else:
                self._kill(s, s.player)
        else:
            s.hands[s.player].append(card)
            self._finish_one_turn(s)

    def _finish_one_turn(self, s: GameState) -> None:
        s.turns_left -= 1
        if s.turns_left <= 0:
            s.player = self._next_alive(s, s.player)
            s.turns_left = 1
        s.phase = "turn"

    def _kill(self, s: GameState, p: int) -> None:
        s.discard.extend(s.hands[p])
        s.hands[p].clear()
        if s.drawn_kitten:
            s.discard.append(EXPLODING)
        s.drawn_kitten = False
        s.alive[p] = False
        if sum(s.alive) == 1:
            s.winner = next(i for i, alive in enumerate(s.alive) if alive)
            s.phase = "terminal"
        else:
            s.player = self._next_alive(s, p)
            s.turns_left = 1
            s.phase = "turn"
