"""
Exploding Kittens (NSFW Edition) - BoardBench game implementation.

Rules source: inputs/game_rules_extracted.txt (German NSFW edition).
Follows rulebook_to_python.txt and open_spiel_backbone.md guidelines.

Assumptions and simplifications:
- 5 cat card types assumed (deck total = 56 implies 5 types x 4 cards each).
  Only 2 cat names visible in extracted text (Zombiekatze, Augenmampfende);
  remaining 3 are placeholder-named cat_3/cat_4/cat_5.
- Deck shuffled with a fixed-seed RNG for determinism (chance_outcomes not
  implemented; randomness handled via fixed-seed RNG, documented gap).
- Nope window: all alive players respond clockwise (card player goes last);
  after each Nope, all responders get another round. Window closes after a
  full pass round. Odd Nope count = action cancelled.
- Favor: target player chooses which card to give (explicit action).
- Pair steal: random card stolen using RNG (deterministic given seed).
- Triple: named card requested; if target has it, must give it.
- Five-different: take any card from discard including the 5 just played.
- Defuse placement: player chooses position in deck (0 = top).
- Information states: hands are private; deck order is private.
  information_state shows only the player's hand and public info.
- Single cat cards can be played (discarded with no effect).
- Defuse can only be played as reaction to Exploding Kitten (not proactively).
- Nope cannot be played on Exploding Kitten draws or Defuse reactions.
- Attack chains: if attacked player plays Attack, remaining turns don't stack;
  next player takes 2 turns.
- See Future results are logged but not tracked per-player in information_state
  (simplification; full state visible in debug render).
- EK count = num_players - 1 (one fewer than players) for all player counts.
- 2-player variant: only 2 Defuse shuffled into deck (not all remaining).
"""

import random
from collections import Counter
from itertools import combinations

# ---------------------------------------------------------------------------
# Card constants
# ---------------------------------------------------------------------------
EXPLODING_KITTEN = "exploding_kitten"
DEFUSE = "defuse"
SEE_FUTURE = "see_future"
SKIP = "skip"
ATTACK = "attack"
NOPE = "nope"
SHUFFLE = "shuffle"
FAVOR = "favor"
CAT_ZOMBIE = "cat_zombie"
CAT_EYEBALL = "cat_eyeball"
CAT_3 = "cat_3"
CAT_4 = "cat_4"
CAT_5 = "cat_5"

CAT_CARDS = [CAT_ZOMBIE, CAT_EYEBALL, CAT_3, CAT_4, CAT_5]
ALL_CARDS = [
    EXPLODING_KITTEN, DEFUSE, SEE_FUTURE, SKIP, ATTACK,
    NOPE, SHUFFLE, FAVOR,
] + CAT_CARDS

CARD_DISPLAY = {
    EXPLODING_KITTEN: "ExplodingKitten",
    DEFUSE: "Defuse",
    SEE_FUTURE: "SeeFuture",
    SKIP: "Skip",
    ATTACK: "Attack",
    NOPE: "Nope",
    SHUFFLE: "Shuffle",
    FAVOR: "Favor",
    CAT_ZOMBIE: "CatZombie",
    CAT_EYEBALL: "CatEyeball",
    CAT_3: "Cat3",
    CAT_4: "Cat4",
    CAT_5: "Cat5",
}

# Cards playable as standalone single-card actions in the main phase.
PLAYABLE_STANDALONE = {SEE_FUTURE, SKIP, ATTACK, SHUFFLE} | set(CAT_CARDS)

# ---------------------------------------------------------------------------
# Sentinels (OpenSpiel-style)
# ---------------------------------------------------------------------------
TERMINAL = -1
CHANCE = -2
SIMULTANEOUS = -3


# ---------------------------------------------------------------------------
# Game state
# ---------------------------------------------------------------------------
class GameState:
    """Full game state (includes private data for correctness)."""

    def __init__(self):
        self.num_players = 4
        self.hands = []          # list[list[str]]  hands[p] = card list
        self.deck = []           # list[str]  deck[0] = top
        self.discard = []        # list[str]
        self.alive = []          # list[bool]
        self.current = 0         # current player index (main phase)
        self.turns_remaining = 1 # 1 normal, 2 when attacked
        self.phase = "main"      # "main" | "nope_window" | "defuse_place" | "favor_give"
        # nope-window bookkeeping
        self.nope_count = 0
        self.nope_responders = []
        self.nope_idx = 0
        self.nope_passes = 0
        self.pending = None      # dict describing the action awaiting Nope resolution
        # defuse bookkeeping
        self.defuse_player = None
        self.held_ek = None      # EK held aside during defuse placement
        # favor bookkeeping
        self.favor_from = None
        self.favor_to = None
        # terminal
        self.terminal = False
        self.winner = None
        # log
        self.log = []
        # rng
        self._rng = None

    def clone(self):
        s = GameState()
        s.num_players = self.num_players
        s.hands = [list(h) for h in self.hands]
        s.deck = list(self.deck)
        s.discard = list(self.discard)
        s.alive = list(self.alive)
        s.current = self.current
        s.turns_remaining = self.turns_remaining
        s.phase = self.phase
        s.nope_count = self.nope_count
        s.nope_responders = list(self.nope_responders)
        s.nope_idx = self.nope_idx
        s.nope_passes = self.nope_passes
        s.pending = dict(self.pending) if self.pending else None
        s.defuse_player = self.defuse_player
        s.held_ek = self.held_ek
        s.favor_from = self.favor_from
        s.favor_to = self.favor_to
        s.terminal = self.terminal
        s.winner = self.winner
        s.log = list(self.log)
        if self._rng is not None:
            s._rng = random.Random()
            s._rng.setstate(self._rng.getstate())
        return s


# ---------------------------------------------------------------------------
# Game
# ---------------------------------------------------------------------------
class Game:
    def __init__(self, num_players=4, seed=42):
        assert 2 <= num_players <= 5, "Exploding Kittens supports 2-5 players"
        self.num_players = num_players
        self.seed = seed

    # ------------------------------------------------------------------ setup
    def _build_full_deck(self):
        deck = []
        deck.extend([EXPLODING_KITTEN] * 4)
        deck.extend([DEFUSE] * 6)
        deck.extend([SEE_FUTURE] * 5)
        deck.extend([SKIP] * 4)
        deck.extend([ATTACK] * 4)
        deck.extend([NOPE] * 5)
        deck.extend([SHUFFLE] * 4)
        deck.extend([FAVOR] * 4)
        for cat in CAT_CARDS:
            deck.extend([cat] * 4)
        assert len(deck) == 56, f"Deck size {len(deck)} != 56"
        return deck

    def _setup(self, n, rng):
        """Return (hands, deck) for *n* players.

        EK count = n - 1 (one fewer than players).
        2-player variant: only 2 Defuse shuffled into deck.
        3-5 players: all remaining Defuse (6 - n) shuffled into deck.
        """
        all_cards = self._build_full_deck()
        others = [c for c in all_cards if c not in (EXPLODING_KITTEN, DEFUSE)]
        rng.shuffle(others)

        hands = [[] for _ in range(n)]
        for i in range(7 * n):
            hands[i % n].append(others.pop())
        for i in range(n):
            hands[i].append(DEFUSE)

        ek_count = n - 1
        if n == 2:
            defuse_count = 2
        else:
            defuse_count = 6 - n

        deck = others[:]
        deck.extend([EXPLODING_KITTEN] * ek_count)
        deck.extend([DEFUSE] * defuse_count)
        rng.shuffle(deck)
        return hands, deck

    def initial_state(self):
        rng = random.Random(self.seed)
        state = GameState()
        state.num_players = self.num_players
        state._rng = rng
        hands, deck = self._setup(self.num_players, rng)
        state.hands = hands
        state.deck = deck
        state.discard = []
        state.alive = [True] * self.num_players
        state.current = 0
        state.turns_remaining = 1
        state.phase = "main"
        state.terminal = False
        state.winner = None
        state.log = [f"Game start: {self.num_players} players, {len(deck)} cards in deck"]
        return state

    # ----------------------------------------------------------- player utils
    def _alive_count(self, state):
        return sum(state.alive)

    def _next_alive(self, state, player):
        for i in range(1, state.num_players):
            p = (player + i) % state.num_players
            if state.alive[p]:
                return p
        return player

    def _alive_others(self, state, exclude):
        result = []
        for i in range(1, state.num_players):
            p = (exclude + i) % state.num_players
            if state.alive[p]:
                result.append(p)
        return result

    def _nope_responders(self, state, card_player):
        """All alive players clockwise starting after card_player (card_player last)."""
        result = []
        for i in range(1, state.num_players + 1):
            p = (card_player + i) % state.num_players
            if state.alive[p]:
                result.append(p)
        return result

    def _check_terminal(self, state):
        if self._alive_count(state) <= 1:
            state.terminal = True
            for i in range(state.num_players):
                if state.alive[i]:
                    state.winner = i
            state.log.append(f"Game over. Player {state.winner} wins!")

    # -------------------------------------------------------------- API: player
    def current_player(self, state):
        if state.terminal:
            return TERMINAL
        if state.phase == "nope_window":
            if state.nope_responders and state.nope_idx < len(state.nope_responders):
                return state.nope_responders[state.nope_idx]
            return TERMINAL
        if state.phase == "defuse_place":
            return state.defuse_player
        if state.phase == "favor_give":
            return state.favor_from
        return state.current

    # --------------------------------------------------------- API: legal actions
    def legal_actions(self, state):
        if state.terminal:
            return []
        player = self.current_player(state)
        if state.phase == "main":
            return self._legal_main(state, player)
        elif state.phase == "nope_window":
            return self._legal_nope(state, player)
        elif state.phase == "defuse_place":
            return self._legal_defuse(state, player)
        elif state.phase == "favor_give":
            return self._legal_favor_give(state, player)
        return []

    def _legal_main(self, state, player):
        actions = []
        hand = state.hands[player]
        counts = Counter(hand)

        # Pass (then draw)
        actions.append(("pass",))

        # Play single standalone cards
        for card in sorted(set(hand)):
            if card in PLAYABLE_STANDALONE:
                actions.append(("play", card))

        # Favor (needs target)
        if FAVOR in hand:
            for target in self._alive_others(state, player):
                actions.append(("favor", target))

        # Pair - any two identical cards (except EK) -> steal random from target
        for card in sorted(set(hand)):
            if counts[card] >= 2 and card != EXPLODING_KITTEN:
                for target in self._alive_others(state, player):
                    actions.append(("pair", card, target))

        # Triple - three identical cards -> request named card from target
        for card in sorted(set(hand)):
            if counts[card] >= 3 and card != EXPLODING_KITTEN:
                for target in self._alive_others(state, player):
                    for named in sorted(ALL_CARDS):
                        actions.append(("triple", card, target, named))

        # Five different - 5 cards with distinct titles -> take from discard
        unique = sorted(c for c in set(hand) if c != EXPLODING_KITTEN)
        if len(unique) >= 5:
            current_discard_set = set(state.discard)
            for combo in combinations(unique, 5):
                future = current_discard_set | set(combo)
                for take_card in sorted(future):
                    actions.append(("five", combo, take_card))

        return actions

    def _legal_nope(self, state, player):
        actions = []
        if NOPE in state.hands[player]:
            actions.append(("nope",))
        actions.append(("nope_pass",))
        return actions

    def _legal_defuse(self, state, player):
        return [("defuse_place", pos) for pos in range(len(state.deck) + 1)]

    def _legal_favor_give(self, state, player):
        return [("favor_give", card) for card in sorted(set(state.hands[player]))]

    # -------------------------------------------------------- API: apply action
    def apply_action(self, state, action):
        """Return a new state (input is not mutated)."""
        new_state = state.clone()
        if new_state.phase == "main":
            self._apply_main(new_state, action)
        elif new_state.phase == "nope_window":
            self._apply_nope(new_state, action)
        elif new_state.phase == "defuse_place":
            self._apply_defuse_place(new_state, action)
        elif new_state.phase == "favor_give":
            self._apply_favor_give(new_state, action)
        self._check_terminal(new_state)
        return new_state

    def _apply_main(self, state, action):
        player = state.current
        atype = action[0]

        if atype == "pass":
            self._draw_and_end_turn(state, player)

        elif atype == "play":
            card = action[1]
            assert card in state.hands[player], f"Player {player} does not have {card}"
            state.hands[player].remove(card)
            state.discard.append(card)
            state.log.append(f"P{player} plays {CARD_DISPLAY.get(card, card)}")
            if card in CAT_CARDS:
                return  # powerless alone, stay in main
            self._start_nope_window(state, {"type": "play", "card": card, "player": player})

        elif atype == "favor":
            target = action[1]
            assert FAVOR in state.hands[player]
            state.hands[player].remove(FAVOR)
            state.discard.append(FAVOR)
            state.log.append(f"P{player} plays Favor targeting P{target}")
            self._start_nope_window(state, {"type": "favor", "player": player, "target": target})

        elif atype == "pair":
            card, target = action[1], action[2]
            assert state.hands[player].count(card) >= 2
            state.hands[player].remove(card)
            state.hands[player].remove(card)
            state.discard.append(card)
            state.discard.append(card)
            state.log.append(f"P{player} plays pair:{CARD_DISPLAY.get(card, card)} -> P{target}")
            self._start_nope_window(state, {"type": "pair", "player": player, "target": target})

        elif atype == "triple":
            card, target, named = action[1], action[2], action[3]
            assert state.hands[player].count(card) >= 3
            for _ in range(3):
                state.hands[player].remove(card)
                state.discard.append(card)
            state.log.append(f"P{player} plays triple:{CARD_DISPLAY.get(card, card)} -> P{target} wants {named}")
            self._start_nope_window(state, {
                "type": "triple", "player": player,
                "target": target, "named": named,
            })

        elif atype == "five":
            combo, take_card = action[1], action[2]
            for c in combo:
                assert c in state.hands[player]
                state.hands[player].remove(c)
                state.discard.append(c)
            state.log.append(f"P{player} plays five-diff -> take {take_card} from discard")
            self._start_nope_window(state, {"type": "five", "player": player, "take_card": take_card})

    # ------------------------------------------------------- nope window logic
    def _start_nope_window(self, state, pending):
        state.phase = "nope_window"
        state.nope_count = 0
        state.nope_responders = self._nope_responders(state, pending["player"])
        state.nope_idx = 0
        state.nope_passes = 0
        state.pending = pending
        if len(state.nope_responders) == 0:
            self._resolve_pending(state)

    def _apply_nope(self, state, action):
        atype = action[0]
        n = len(state.nope_responders)
        if atype == "nope":
            player = self.current_player(state)
            assert NOPE in state.hands[player]
            state.hands[player].remove(NOPE)
            state.discard.append(NOPE)
            state.nope_count += 1
            state.nope_passes = 0
            state.log.append(f"P{player} plays Nope!")
            if n > 0:
                state.nope_idx = (state.nope_idx + 1) % n
        elif atype == "nope_pass":
            state.nope_passes += 1
            if n > 0:
                state.nope_idx = (state.nope_idx + 1) % n
            if state.nope_passes >= n:
                self._resolve_pending(state)

    def _resolve_pending(self, state):
        pending = state.pending
        noped = state.nope_count % 2 == 1

        if noped:
            state.log.append(f"Action '{pending['type']}' noped (cancelled)")
            state.phase = "main"
        else:
            ptype = pending["type"]
            player = pending["player"]
            if ptype == "play":
                self._execute_card(state, player, pending["card"])
            elif ptype == "favor":
                self._execute_favor(state, player, pending["target"])
            elif ptype == "pair":
                self._execute_pair(state, player, pending["target"])
            elif ptype == "triple":
                self._execute_triple(state, player, pending["target"], pending["named"])
            elif ptype == "five":
                self._execute_five(state, player, pending["take_card"])
            if state.phase == "nope_window":
                state.phase = "main"

        # clean up
        state.nope_count = 0
        state.nope_responders = []
        state.nope_idx = 0
        state.nope_passes = 0
        state.pending = None

    # ----------------------------------------------------- card effect handlers
    def _execute_card(self, state, player, card):
        if card == SEE_FUTURE:
            top3 = state.deck[:3]
            state.log.append(f"P{player} sees future: {' '.join(CARD_DISPLAY.get(c, c) for c in top3)}")
            state.phase = "main"
        elif card == SKIP:
            state.log.append(f"P{player} skips (no draw)")
            self._end_turn(state, player)
        elif card == ATTACK:
            state.log.append(f"P{player} attacks -> next player takes 2 turns")
            self._end_turn_attack(state, player)
        elif card == SHUFFLE:
            state._rng.shuffle(state.deck)
            state.log.append(f"P{player} shuffles deck")
            state.phase = "main"

    def _execute_favor(self, state, player, target):
        if len(state.hands[target]) == 0:
            state.log.append(f"P{target} has no cards to give to P{player}")
            state.phase = "main"
        else:
            state.phase = "favor_give"
            state.favor_from = target
            state.favor_to = player

    def _execute_pair(self, state, player, target):
        if len(state.hands[target]) > 0:
            idx = state._rng.randint(0, len(state.hands[target]) - 1)
            stolen = state.hands[target].pop(idx)
            state.hands[player].append(stolen)
            state.log.append(f"P{player} steals {CARD_DISPLAY.get(stolen, stolen)} from P{target}")
        else:
            state.log.append(f"P{target} has no cards to steal")
        state.phase = "main"

    def _execute_triple(self, state, player, target, named):
        if named in state.hands[target]:
            state.hands[target].remove(named)
            state.hands[player].append(named)
            state.log.append(f"P{player} takes {CARD_DISPLAY.get(named, named)} from P{target}")
        else:
            state.log.append(f"P{player} wanted {named} from P{target} - not found")
        state.phase = "main"

    def _execute_five(self, state, player, take_card):
        # remove last occurrence of take_card from discard
        for i in range(len(state.discard) - 1, -1, -1):
            if state.discard[i] == take_card:
                state.discard.pop(i)
                break
        state.hands[player].append(take_card)
        state.log.append(f"P{player} takes {CARD_DISPLAY.get(take_card, take_card)} from discard")
        state.phase = "main"

    # ----------------------------------------------------------- draw and turns
    def _draw_and_end_turn(self, state, player):
        if len(state.deck) == 0:
            state.log.append("Deck empty - game ends unexpectedly")
            state.terminal = True
            return

        card = state.deck.pop(0)
        state.log.append(f"P{player} draws {CARD_DISPLAY.get(card, card)}")

        if card == EXPLODING_KITTEN:
            if DEFUSE in state.hands[player]:
                state.hands[player].remove(DEFUSE)
                state.discard.append(DEFUSE)
                state.held_ek = EXPLODING_KITTEN
                state.phase = "defuse_place"
                state.defuse_player = player
                state.log.append(f"P{player} defuses Exploding Kitten")
            else:
                state.alive[player] = False
                state.discard.extend(state.hands[player])
                state.hands[player] = []
                state.discard.append(card)
                state.log.append(f"P{player} EXPLODES!")
                self._end_turn(state, player)
        else:
            state.hands[player].append(card)
            self._end_turn(state, player)

    def _end_turn(self, state, player):
        state.turns_remaining -= 1
        if state.turns_remaining <= 0 or not state.alive[player]:
            state.current = self._next_alive(state, player)
            state.turns_remaining = 1
        state.phase = "main"

    def _end_turn_attack(self, state, player):
        state.current = self._next_alive(state, player)
        state.turns_remaining = 2
        state.phase = "main"

    # --------------------------------------------------- phase-specific apply
    def _apply_defuse_place(self, state, action):
        pos = action[1]
        player = state.defuse_player
        state.deck.insert(pos, state.held_ek)
        state.held_ek = None
        state.defuse_player = None
        state.log.append(f"P{player} places Exploding Kitten at deck pos {pos}")
        self._end_turn(state, player)

    def _apply_favor_give(self, state, action):
        card = action[1]
        giver = state.favor_from
        receiver = state.favor_to
        assert card in state.hands[giver]
        state.hands[giver].remove(card)
        state.hands[receiver].append(card)
        state.log.append(f"P{giver} gives {CARD_DISPLAY.get(card, card)} to P{receiver}")
        state.favor_from = None
        state.favor_to = None
        state.phase = "main"

    # ----------------------------------------------------------- API: terminal
    def is_terminal(self, state):
        return state.terminal

    def returns(self, state):
        if not state.terminal:
            return [0.0] * state.num_players
        return [1.0 if i == state.winner else 0.0 for i in range(state.num_players)]

    # ----------------------------------------------------------- API: render
    def render(self, state):
        lines = []
        lines.append(f"Phase: {state.phase}")
        if state.phase == "main":
            lines.append(f"Current: P{state.current} | Turns: {state.turns_remaining}")
        elif state.phase == "nope_window":
            resp = "?"
            if state.nope_responders and state.nope_idx < len(state.nope_responders):
                resp = f"P{state.nope_responders[state.nope_idx]}"
            cp = state.pending["player"] if state.pending else "?"
            lines.append(f"CardPlayer: P{cp} | Responder: {resp} | Nopes: {state.nope_count}")
        elif state.phase == "defuse_place":
            lines.append(f"Defuse: P{state.defuse_player} placing EK in deck({len(state.deck)})")
        elif state.phase == "favor_give":
            lines.append(f"Favor: P{state.favor_from} -> P{state.favor_to}")

        for i in range(state.num_players):
            status = "ALIVE" if state.alive[i] else "DEAD"
            hand = sorted(state.hands[i])
            hand_str = " ".join(hand) if hand else "(empty)"
            lines.append(f"P{i}[{status}]({len(hand)}): {hand_str}")

        lines.append(f"Deck: {len(state.deck)}")
        if state.discard:
            lines.append(f"Discard: {' '.join(state.discard[-8:])}")
        else:
            lines.append("Discard: (empty)")

        if state.log:
            lines.append(f"Last: {state.log[-1]}")
        return "\n".join(lines)

    # ----------------------------------------------------- API: action names
    def action_to_name(self, action):
        atype = action[0]
        if atype == "pass":
            return "pass"
        if atype == "play":
            return f"play:{action[1]}"
        if atype == "favor":
            return f"favor:p{action[1]}"
        if atype == "pair":
            return f"pair:{action[1]}:p{action[2]}"
        if atype == "triple":
            return f"triple:{action[1]}:p{action[2]}:{action[3]}"
        if atype == "five":
            cards = action[1]
            return f"five:{':'.join(cards)}:{action[2]}"
        if atype == "nope":
            return "nope"
        if atype == "nope_pass":
            return "nope_pass"
        if atype == "defuse_place":
            return f"defuse_place:{action[1]}"
        if atype == "favor_give":
            return f"favor_give:{action[1]}"
        raise ValueError(f"Unknown action: {action}")

    def name_to_action(self, name):
        parts = name.split(":")
        atype = parts[0]
        if atype == "pass":
            return ("pass",)
        if atype == "play":
            return ("play", parts[1])
        if atype == "favor":
            return ("favor", int(parts[1][1:]))
        if atype == "pair":
            return ("pair", parts[1], int(parts[2][1:]))
        if atype == "triple":
            return ("triple", parts[1], int(parts[2][1:]), parts[3])
        if atype == "five":
            cards = tuple(parts[1:6])
            take_card = parts[6]
            return ("five", cards, take_card)
        if atype == "nope":
            return ("nope",)
        if atype == "nope_pass":
            return ("nope_pass",)
        if atype == "defuse_place":
            return ("defuse_place", int(parts[1]))
        if atype == "favor_give":
            return ("favor_give", parts[1])
        raise ValueError(f"Unknown action name: {name}")

    # --------------------------------------------------- API: hidden info
    def information_state(self, state, player):
        """Player-visible information (no other hands, no deck order)."""
        lines = []
        lines.append(f"Phase: {state.phase}")
        lines.append(f"You: P{player} ({'ALIVE' if state.alive[player] else 'DEAD'})")
        if state.phase == "main" and state.current == player:
            lines.append(f"Your turn (turns remaining: {state.turns_remaining})")
        hand = sorted(state.hands[player])
        lines.append(f"Hand({len(hand)}): {' '.join(hand) if hand else '(empty)'}")
        for i in range(state.num_players):
            if i == player:
                continue
            status = "ALIVE" if state.alive[i] else "DEAD"
            lines.append(f"P{i}[{status}]({len(state.hands[i])} cards)")
        lines.append(f"Deck: {len(state.deck)} cards")
        if state.discard:
            lines.append(f"Discard: {' '.join(state.discard)}")
        else:
            lines.append("Discard: (empty)")
        return "\n".join(lines)