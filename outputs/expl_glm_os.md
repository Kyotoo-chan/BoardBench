## Open questions / assumptions

1. **Cat card types**: The rule text explicitly names "Zombiekatze" and "Augenmampfende" as cat cards and states "4 jeder Art" (4 of each type). With 56 total cards and 36 non-cat cards, there must be 5 cat types (20 cards / 4 each). I name the 3 unknown types `cat_3`, `cat_4`, `cat_5` as placeholders.

2. **Shuffle randomness**: The rules require shuffling (initial deck, Shuffle card). Modeling every possible shuffle outcome as explicit chance nodes is computationally infeasible (factorial outcomes). I use `random.Random` with a configurable seed, documented as a deviation from the explicit chance-node pattern.

3. **Random steals**: Cat pair steals are random. I use the same RNG rather than explicit chance nodes, for simplicity.

4. **No! reaction timing**: The real game allows any player to slap down No! at any time. I model this as a sequential polling of alive players in turn order during a "reaction" phase, which is a deterministic simplification.

5. **Five-different combo**: When selecting a card from the discard pile, I let the player choose by card type (taking the topmost match) rather than by exact index, for a simpler action space.

6. **Single cat card plays**: The rules say cat cards are "machtlos" (powerless) individually. I do not allow playing single cat cards; they can only be used in combos.

7. **Hidden information**: Hands and deck order are private. The `GameState` contains full truth for correctness. `information_state` is not fully implemented; `render` shows full debug state.

8. **2-player Defuse variant**: The rules say "Mischt nur 2 Karten 'Entschärfung' in den Spielstapel" for 2 players. For 3+ players, all remaining Defuses (6 − num_players) go into the deck.

9. **Attack under death**: If an attacked player dies from an EK, the next player gets a normal turn (turns_remaining = 1), not the inherited attack turns.

10. **Favor target selection**: The player names the target when playing Favor (before the No! window). After resolution, the target chooses which card to give.

```python
"""Exploding Kittens (NSFW Edition) — standard-library implementation.

Game type: 2-5 players, sequential with reaction interrupts (No!), hidden
information (hands/deck), chance (shuffle, random steal).

Simplifications: randomness via seeded RNG (not explicit chance nodes);
No! reactions polled in turn order (not real-time); single cat cards not
playable individually; five-different discard selection by type (topmost).
"""

import random
import copy
from dataclasses import dataclass, field
from itertools import combinations

# ── Sentinels ──────────────────────────────────────────────────────────────
TERMINAL = -1
CHANCE = -2
SIMULTANEOUS = -3

# ── Card types ─────────────────────────────────────────────────────────────
EK = "exploding_kitten"
DEFUSE = "defuse"
ATTACK = "attack"
SKIP = "skip"
FAVOR = "favor"
SHUFFLE = "shuffle"
SEE_FUTURE = "see_future"
NOPE = "nope"
CAT_ZOMBIE = "cat_zombie"
CAT_EYEMUNCH = "cat_eyemunch"
CAT_3 = "cat_3"
CAT_4 = "cat_4"
CAT_5 = "cat_5"

CAT_TYPES = [CAT_ZOMBIE, CAT_EYEMUNCH, CAT_3, CAT_4, CAT_5]
ALL_TYPES = [EK, DEFUSE, ATTACK, SKIP, FAVOR, SHUFFLE, SEE_FUTURE, NOPE,
             CAT_ZOMBIE, CAT_EYEMUNCH, CAT_3, CAT_4, CAT_5]
# Types that can be demanded via a triple (all except EK, which is never in hand)
DEMAND_TYPES = [DEFUSE, ATTACK, SKIP, FAVOR, SHUFFLE, SEE_FUTURE, NOPE,
                CAT_ZOMBIE, CAT_EYEMUNCH, CAT_3, CAT_4, CAT_5]

CARD_COUNTS = {
    EK: 4, DEFUSE: 6, ATTACK: 4, SKIP: 4, FAVOR: 4,
    SHUFFLE: 4, SEE_FUTURE: 5, NOPE: 5,
    CAT_ZOMBIE: 4, CAT_EYEMUNCH: 4, CAT_3: 4, CAT_4: 4, CAT_5: 4,
}

# Cards playable individually during the turn phase (cats excluded — "machtlos")
SINGLE_PLAYABLE = [ATTACK, SKIP, SHUFFLE, SEE_FUTURE]


# ── State ──────────────────────────────────────────────────────────────────
@dataclass
class GameState:
    num_players: int = 2
    deck: list = field(default_factory=list)        # top = index 0
    discard: list = field(default_factory=list)
    hands: list = field(default_factory=list)        # hands[p] = list[str]
    alive: list = field(default_factory=list)
    current_player: int = 0
    phase: str = "turn"                              # turn|reaction|favor_give|defuse|see_future|five_select|terminal
    turns_remaining: int = 1                         # >1 when attacked
    # reaction bookkeeping
    actor: int = -1
    pending_action: dict = field(default_factory=dict)
    nope_count: int = 0
    responders: list = field(default_factory=list)
    responder_idx: int = 0
    # sub-phase bookkeeping
    favor_target: int = -1
    favor_actor: int = -1
    future_cards: list = field(default_factory=list)
    winners: list = field(default_factory=list)


# ── Game ───────────────────────────────────────────────────────────────────
class Game:
    def __init__(self, num_players: int = 2, seed: int | None = None):
        if not 2 <= num_players <= 5:
            raise ValueError("num_players must be 2-5")
        self.num_players = num_players
        self.rng = random.Random(seed)

    # ── Setup ──────────────────────────────────────────────────────────────
    def initial_state(self) -> GameState:
        n = self.num_players
        s = GameState(num_players=n)

        # Build deck from non-EK, non-Defuse cards
        pool = []
        for ct, cnt in CARD_COUNTS.items():
            if ct in (EK, DEFUSE):
                continue
            pool.extend([ct] * cnt)
        self.rng.shuffle(pool)

        # Deal 7 cards to each player
        s.hands = [[] for _ in range(n)]
        for _ in range(7):
            for p in range(n):
                s.hands[p].append(pool.pop())

        # Each player gets 1 Defuse (8 starting cards)
        for p in range(n):
            s.hands[p].append(DEFUSE)

        # Add (n-1) Exploding Kittens to deck
        pool.extend([EK] * (n - 1))

        # Add remaining Defuses (2-player variant: only 2; others: 6-n)
        pool.extend([DEFUSE] * (2 if n == 2 else 6 - n))

        self.rng.shuffle(pool)
        s.deck = pool
        s.alive = [True] * n
        s.current_player = 0
        s.phase = "turn"
        s.turns_remaining = 1
        return s

    # ── Player ─────────────────────────────────────────────────────────────
    def current_player(self, state: GameState) -> int:
        if state.phase == "terminal":
            return TERMINAL
        if state.phase == "reaction":
            if state.responders and state.responder_idx < len(state.responders):
                return state.responders[state.responder_idx]
            return state.actor
        if state.phase == "favor_give":
            return state.favor_target
        return state.current_player

    # ── Legal actions ──────────────────────────────────────────────────────
    def legal_actions(self, state: GameState) -> list:
        if state.phase == "terminal":
            return []
        return {
            "turn": self._legal_turn,
            "reaction": self._legal_reaction,
            "favor_give": self._legal_favor_give,
            "defuse": self._legal_defuse,
            "see_future": lambda s: [("see_future_done",)],
            "five_select": self._legal_five_select,
        }[state.phase](state)

    def _legal_turn(self, s: GameState) -> list:
        p = s.current_player
        hand = s.hands[p]
        acts = [("pass",)]

        counts: dict[str, int] = {}
        for c in hand:
            counts[c] = counts.get(c, 0) + 1

        # Single card plays (Attack, Skip, Shuffle, See Future)
        for ct in SINGLE_PLAYABLE:
            if counts.get(ct, 0) >= 1:
                acts.append(("play", ct))

        # Favor (needs target)
        if counts.get(FAVOR, 0) >= 1:
            for t in range(s.num_players):
                if t != p and s.alive[t]:
                    acts.append(("play_favor", t))

        # Pairs — any type except EK (advanced rule: "alle gleichen Karten")
        for ct in sorted(counts):
            if ct == EK:
                continue
            if counts[ct] >= 2:
                for t in range(s.num_players):
                    if t != p and s.alive[t]:
                        acts.append(("play_pair", ct, t))

        # Triples — demand a specific card
        for ct in sorted(counts):
            if ct == EK:
                continue
            if counts[ct] >= 3:
                for t in range(s.num_players):
                    if t != p and s.alive[t]:
                        for dem in DEMAND_TYPES:
                            acts.append(("play_triple", ct, t, dem))

        # Five different — take from discard
        distinct = sorted(c for c in counts if c != EK)
        if len(distinct) >= 5:
            for combo in combinations(distinct, 5):
                acts.append(("play_five",) + combo)

        return acts

    def _legal_reaction(self, s: GameState) -> list:
        acts = [("pass_reaction",)]
        resp = s.responders[s.responder_idx]
        if NOPE in s.hands[resp]:
            acts.append(("nope",))
        return acts

    def _legal_favor_give(self, s: GameState) -> list:
        t = s.favor_target
        return [("favor_give", i) for i in range(len(s.hands[t]))]

    def _legal_defuse(self, s: GameState) -> list:
        return [("defuse", pos) for pos in range(len(s.deck) + 1)]

    def _legal_five_select(self, s: GameState) -> list:
        return [("five_select", ct) for ct in sorted(set(s.discard))]

    # ── Apply action (returns new state) ───────────────────────────────────
    def apply_action(self, state: GameState, action) -> GameState:
        s = copy.deepcopy(state)
        {
            "turn": self._apply_turn,
            "reaction": self._apply_reaction,
            "favor_give": self._apply_favor_give,
            "defuse": self._apply_defuse,
            "see_future": self._apply_see_future,
            "five_select": self._apply_five_select,
        }[s.phase](s, action)
        return s

    def _apply_turn(self, s: GameState, action):
        p = s.current_player
        if action == ("pass",):
            self._draw_card(s, p)
            return

        tag = action[0]
        if tag == "play":
            ct = action[1]
            s.hands[p].remove(ct)
            s.discard.append(ct)
            s.pending_action = {"type": "single", "card": ct}
            self._start_reaction(s, p)

        elif tag == "play_favor":
            target = action[1]
            s.hands[p].remove(FAVOR)
            s.discard.append(FAVOR)
            s.pending_action = {"type": "favor", "target": target}
            self._start_reaction(s, p)

        elif tag == "play_pair":
            ct, target = action[1], action[2]
            s.hands[p].remove(ct); s.hands[p].remove(ct)
            s.discard += [ct, ct]
            s.pending_action = {"type": "pair", "target": target}
            self._start_reaction(s, p)

        elif tag == "play_triple":
            ct, target, demand = action[1], action[2], action[3]
            for _ in range(3):
                s.hands[p].remove(ct)
            s.discard += [ct, ct, ct]
            s.pending_action = {"type": "triple", "target": target, "demand": demand}
            self._start_reaction(s, p)

        elif tag == "play_five":
            cards = list(action[1:6])
            for ct in cards:
                s.hands[p].remove(ct)
            s.discard += cards
            s.pending_action = {"type": "five"}
            self._start_reaction(s, p)

    def _draw_card(self, s: GameState, p: int):
        if not s.deck:
            self._end_turn(s)
            return
        card = s.deck.pop(0)
        if card == EK:
            if DEFUSE in s.hands[p]:
                s.phase = "defuse"
            else:
                self._kill_player(s, p)
        else:
            s.hands[p].append(card)
            self._end_turn(s)

    # ── Reaction (No!) system ──────────────────────────────────────────────
    def _start_reaction(self, s: GameState, actor: int):
        s.actor = actor
        s.phase = "reaction"
        s.nope_count = 0
        s.responders = self._alive_except(s, actor, start_after=actor)
        s.responder_idx = 0
        if not s.responders:
            self._resolve_reaction(s)

    def _apply_reaction(self, s: GameState, action):
        if action == ("nope",):
            resp = s.responders[s.responder_idx]
            s.hands[resp].remove(NOPE)
            s.discard.append(NOPE)
            s.nope_count += 1
            # Everyone except the No!-player gets a chance to respond
            s.responders = self._alive_except(s, resp, start_after=resp)
            s.responder_idx = 0
            if not s.responders:
                self._resolve_reaction(s)
        else:  # pass_reaction
            s.responder_idx += 1
            if s.responder_idx >= len(s.responders):
                self._resolve_reaction(s)

    def _resolve_reaction(self, s: GameState):
        s.responders = []
        s.responder_idx = 0
        if s.nope_count % 2 == 1:
            # Action cancelled — actor continues turn
            s.phase = "turn"
            s.current_player = s.actor
            s.pending_action = {}
            s.actor = -1
            return
        self._execute_action(s)

    def _execute_action(self, s: GameState):
        pa = s.pending_action
        actor = s.actor
        s.pending_action = {}
        s.actor = -1
        atype = pa["type"]

        if atype == "single":
            card = pa["card"]
            if card == ATTACK:
                self._end_turn_attack(s); return
            if card == SKIP:
                self._end_turn_skip(s); return
            if card == SHUFFLE:
                self.rng.shuffle(s.deck)
            elif card == SEE_FUTURE:
                s.future_cards = list(s.deck[:3])
                s.phase = "see_future"
                s.current_player = actor
                return
            s.phase = "turn"
            s.current_player = actor

        elif atype == "favor":
            s.favor_target = pa["target"]
            s.favor_actor = actor
            s.phase = "favor_give"

        elif atype == "pair":
            target = pa["target"]
            if s.hands[target]:
                idx = self.rng.randint(0, len(s.hands[target]) - 1)
                s.hands[actor].append(s.hands[target].pop(idx))
            s.phase = "turn"
            s.current_player = actor

        elif atype == "triple":
            target, demand = pa["target"], pa["demand"]
            if demand in s.hands[target]:
                s.hands[target].remove(demand)
                s.hands[actor].append(demand)
            s.phase = "turn"
            s.current_player = actor

        elif atype == "five":
            s.phase = "five_select"
            s.current_player = actor

    # ── Sub-phase handlers ─────────────────────────────────────────────────
    def _apply_favor_give(self, s: GameState, action):
        idx = action[1]
        card = s.hands[s.favor_target].pop(idx)
        s.hands[s.favor_actor].append(card)
        s.phase = "turn"
        s.current_player = s.favor_actor
        s.favor_target = -1
        s.favor_actor = -1

    def _apply_defuse(self, s: GameState, action):
        pos = min(action[1], len(s.deck))
        p = s.current_player
        s.hands[p].remove(DEFUSE)
        s.discard.append(DEFUSE)
        s.deck.insert(pos, EK)
        s.phase = "turn"
        self._end_turn(s)

    def _apply_see_future(self, s: GameState, action):
        s.future_cards = []
        s.phase = "turn"

    def _apply_five_select(self, s: GameState, action):
        ct = action[1]
        for i in range(len(s.discard) - 1, -1, -1):
            if s.discard[i] == ct:
                s.discard.pop(i)
                s.hands[s.current_player].append(ct)
                break
        s.phase = "turn"

    # ── Turn-ending helpers ────────────────────────────────────────────────
    def _end_turn(self, s: GameState):
        """Called after a normal draw or after defusing."""
        if s.turns_remaining > 1:
            s.turns_remaining -= 1
        else:
            s.turns_remaining = 1
            s.current_player = self._next_alive(s, s.current_player)
        self._check_win(s)

    def _end_turn_attack(self, s: GameState):
        s.turns_remaining = 2
        s.current_player = self._next_alive(s, s.current_player)
        s.phase = "turn"
        self._check_win(s)

    def _end_turn_skip(self, s: GameState):
        if s.turns_remaining > 1:
            s.turns_remaining -= 1
        else:
            s.turns_remaining = 1
            s.current_player = self._next_alive(s, s.current_player)
        s.phase = "turn"
        self._check_win(s)

    # ── Death / win ────────────────────────────────────────────────────────
    def _kill_player(self, s: GameState, p: int):
        s.alive[p] = False
        s.discard += s.hands[p]
        s.hands[p] = []
        s.discard.append(EK)
        if sum(s.alive) <= 1:
            s.phase = "terminal"
            s.winners = [i for i, a in enumerate(s.alive) if a]
        else:
            s.turns_remaining = 1
            s.current_player = self._next_alive(s, p)
            s.phase = "turn"

    def _check_win(self, s: GameState):
        if sum(s.alive) <= 1:
            s.phase = "terminal"
            s.winners = [i for i, a in enumerate(s.alive) if a]

    def _next_alive(self, s: GameState, p: int) -> int:
        nxt = (p + 1) % s.num_players
        while not s.alive[nxt]:
            nxt = (nxt + 1) % s.num_players
        return nxt

    def _alive_except(self, s: GameState, excl: int, start_after: int) -> list:
        out = []
        p = (start_after + 1) % s.num_players
        while p != excl:
            if s.alive[p]:
                out.append(p)
            p = (p + 1) % s.num_players
        return out

    # ── Terminal / returns ─────────────────────────────────────────────────
    def is_terminal(self, state: GameState) -> bool:
        return state.phase == "terminal"

    def returns(self, state: GameState) -> list:
        r = [0.0] * state.num_players
        if state.phase == "terminal":
            for w in state.winners:
                r[w] = 1.0
        return r

    # ── Render ─────────────────────────────────────────────────────────────
    def render(self, state: GameState) -> str:
        s = state
        L = []
        L.append(f"== {s.phase} | P{s.current_player} | turns={s.turns_remaining} ==")
        alive_str = " ".join(f"P{i}" if a else "X" for i, a in enumerate(s.alive))
        L.append(f"Alive: [{alive_str}]  Deck:{len(s.deck)}  DiscardTop:{s.discard[-1] if s.discard else '-'}")
        for p in range(s.num_players):
            counts: dict[str, int] = {}
            for c in s.hands[p]:
                counts[c] = counts.get(c, 0) + 1
            st = "alive" if s.alive[p] else "DEAD"
            h = " ".join(f"{ct}:{n}" for ct, n in sorted(counts.items())) or "-"
            L.append(f"  P{p}[{st}] {len(s.hands[p])}cards: {h}")
        if s.phase == "reaction":
            r = s.responders[s.responder_idx] if s.responder_idx < len(s.responders) else "?"
            L.append(f"  REACT actor=P{s.actor} nope={s.nope_count} responder=P{r}")
            L.append(f"  pending={s.pending_action}")
        if s.phase == "see_future":
            L.append(f"  FUTURE: {s.future_cards}")
        if s.phase == "favor_give":
            L.append(f"  FAVOR: P{s.favor_target} -> P{s.favor_actor}")
        if s.phase == "defuse":
            L.append(f"  DEFUSE: pick pos 0..{len(s.deck)}")
        if s.phase == "five_select":
            L.append(f"  FIVE: pick from {sorted(set(s.discard))}")
        if s.phase == "terminal":
            L.append(f"  WINNERS: {s.winners}")
        return "\n".join(L)

    # ── Action naming ──────────────────────────────────────────────────────
    def action_to_name(self, action) -> str:
        if action == ("pass",):
            return "pass"
        if action == ("nope",):
            return "nope"
        if action == ("pass_reaction",):
            return "pass_reaction"
        if action == ("see_future_done",):
            return "see_future_done"
        tag = action[0]
        if tag == "play":
            return f"play:{action[1]}"
        if tag == "play_favor":
            return f"play:favor:p{action[1]}"
        if tag == "play_pair":
            return f"play:pair:{action[1]}:p{action[2]}"
        if tag == "play_triple":
            return f"play:triple:{action[1]}:p{action[2]}:{action[3]}"
        if tag == "play_five":
            return f"play:five:{':'.join(action[1:6])}"
        if tag == "favor_give":
            return f"favor_give:idx{action[1]}"
        if tag == "defuse":
            return f"defuse:pos{action[1]}"
        if tag == "five_select":
            return f"five_select:{action[1]}"
        raise ValueError(f"Unknown action: {action}")

    def name_to_action(self, name: str):
        if name == "pass":
            return ("pass",)
        if name == "nope":
            return ("nope",)
        if name == "pass_reaction":
            return ("pass_reaction",)
        if name == "see_future_done":
            return ("see_future_done",)
        # Order matters: longer prefixes first
        if name.startswith("play:five:"):
            parts = name.split(":")
            return ("play_five", parts[2], parts[3], parts[4], parts[5], parts[6])
        if name.startswith("play:triple:"):
            parts = name.split(":")
            return ("play_triple", parts[2], int(parts[3][1:]), parts[4])
        if name.startswith("play:pair:"):
            parts = name.split(":")
            return ("play_pair", parts[2], int(parts[3][1:]))
        if name.startswith("play:favor:"):
            parts = name.split(":")
            return ("play_favor", int(parts[2][1:]))
        if name.startswith("play:"):
            return ("play", name.split(":")[1])
        if name.startswith("favor_give:idx"):
            return ("favor_give", int(name[len("favor_give:idx"):]))
        if name.startswith("defuse:pos"):
            return ("defuse", int(name[len("defuse:pos"):]))
        if name.startswith("five_select:"):
            return ("five_select", name[len("five_select:"):])
        raise ValueError(f"Unknown action name: {name}")
```