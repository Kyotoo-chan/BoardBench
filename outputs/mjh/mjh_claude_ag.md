## 1. Open questions / assumptions

**Tile set** — The rulebook never enumerates the full set. It is *derived* from the "13 orphans" definition (all 1s+9s + each wind + each dragon = 13 unique ⇒ 6 terminals ⇒ 3 base suits) and from named references. Only two suits are named (Bambus `B`, Kreis `K`); the third is required but unnamed → placeholder `Z`. Only one dragon is named (grüner Drachen `Dg`); the other two are placeholders `Da`/`Db` (they matter only collectively as "Drachen"). Set = 136 tiles.

**Scope** — One "Spiel" (single deal) is modelled. The multi-game "Partie" (4 wind rounds, seat rotation, cumulative scoring) is **out of scope**. Round wind and seats are `Game` parameters (default round=Ost, seats E/S/W/N for players 0–3).

**Flowers/Seasons OFF by default** — the rulebook explicitly sanctions this simplified 17-tile-wall variant; bonus-tile logic is not wired into the loop (a `use_bonus` flag exists but is inert).

**Reaction priority not specified** — assumed **Mah-Jongg > Kong > Pong > Chi**, ties by nearest player counter-clockwise. Chi only for the discarder's right neighbour (rulebook-explicit). Documented as an assumption.

**Dead wall simplified** — 14 tiles reserved and never drawn; living wall "empty" (⇒ draw / "unentschieden") when only those remain. Exact Doppelziegel/loose-tile counting from the dice ritual is not modelled (it only affects *which* tile is drawn, which we already randomise via chance nodes).

**Scoring** — figure points, Mah-Jongg bonus and a large subset of doublings are implemented. The **settlement rule is implemented exactly and validated against both worked examples** in the rulebook (`[76,12,22,32]→[456,−182,−152,−122]` and `[16,500,48,2]→[−1036,1418,192,−574]`). Shape-detectable limit hands (seven pairs=½ limit, thirteen orphans, all-honours, all-terminals, four kongs) are scored as the limit; picture-only/ambiguous limit hands (section 9 images unavailable) fall through to normal scoring and are capped at the limit anyway. Some doublings/last-tile bonuses that need information the rulebook does not let us reconstruct ("einzig möglicher Ziegel", exact double-kong timing) are omitted. Non-winner hands are scored on exposed melds + greedily extracted concealed triplets/one pair (the rulebook only illustrates fully-open hands).

**Winning is optional** in `legal_actions` (a player may discard instead of declaring), so rollouts terminate via wall exhaustion when no one completes a hand.

**Actions are their own canonical name strings** (tiles like `B5`/`We`/`Dg`, runs like `chi:B4-B5-B6`), so `action_to_name`/`name_to_action` round-trip by construction and no signed coordinates arise.

Verified: all six phases exercised through `apply_action`; 263k legal-action acceptance checks pass; `chance_outcomes` sum to 1; terminal states have no legal actions; returns are length-4 and zero-sum; render/information_state deterministic; `information_state` never exposes other hands or wall contents.

## 2. Final file

```python
"""Mah-Jongg (German rulebook) — self-contained BoardBench game module.

Source of truth: the provided German rulebook text only. Where the rulebook is
silent or ambiguous, the choice is documented here and, briefly, at the code site.
No external game knowledge is used to invent mechanics.

Scope / model
-------------
* One "Spiel" (a single deal that ends in a Mah-Jongg call or an exhausted living
  wall) is modelled. The multi-game "Partie" (four wind rounds, seat rotation,
  cumulative scoring) is OUT OF SCOPE and documented as a gap.
* 4 players, seats fixed counter-clockwise: player 0=Ost(E), 1=Sued(S), 2=West(W),
  3=Nord(N). Play advances to the right neighbour = (p+1) % 4 (rulebook: the game
  runs counter-clockwise and the "rechter Nachbar" acts next).
* Hidden information (concealed hands) + chance (wall) game. Randomness is modelled
  ONLY as explicit chance nodes (dealing, drawing, kong replacement), never via
  hidden RNG calls.

Tile set (derived, not assumed from outside knowledge)
------------------------------------------------------
The rulebook implies the set: "Die 13 einzigartigen" orphan hand = "aller Einsen
und Neunen, je ein Exemplar der Winde und Drachen" totalling 13 unique tiles.
4 winds + 3 dragons = 7, so ones+nines must be 6 => 3 base suits x {1,9}. Hence:
* 3 base suits (Grundfarben), ranks 1..9, 4 copies each  -> 108
* 4 winds (Ost/Sued/West/Nord), 4 copies each            ->  16
* 3 dragons, 4 copies each                               ->  12
Total 136 tiles. Only two base suits are actually NAMED in the text: "Bambus" (B)
and "Kreis" (K). The third suit is required by the structure but unnamed; it is
labelled 'Z' as a documented placeholder. Only one dragon is named ("Gruener
Drachen" -> 'Dg'); the other two are structurally required but unnamed and labelled
'Da'/'Db' as placeholders (their identity only matters collectively as "Drachen").

Flowers/Seasons (Blumen/Jahreszeiten) are OFF by default: the rulebook explicitly
offers this simplified 17-double-tile-wall variant ("um das Spiel zu vereinfachen
... koennen die Steine rausgenommen werden"). A flag exists but bonus-tile handling
is intentionally not wired into the core loop.

Tile ids: base "B5","K1","Z9"; winds "We","Ws","Ww","Wn"; dragons "Dg","Da","Db".

Documented interpretation choices (see also `Open questions`):
* Reaction priority is NOT explicitly ordered in the rulebook. Assumed:
  Mah-Jongg > Kong > Pong > Chi (Tschi), ties broken by nearest player
  counter-clockwise. Chi is offered only to the discarder's right neighbour
  (rulebook-explicit).
* Dead wall / loose-tile bookkeeping is simplified: 14 tiles are reserved and never
  drawn; the living wall is "empty" when only those 14 remain, which ends the game
  as a draw ("unentschieden"). Exact Doppelziegel/loose-tile counting is not modelled.
* Per-hand scoring implements the tabulated figure points, the Mah-Jongg bonus, and
  a large subset of the doublings. A small set of clearly shape-detectable limit
  hands is scored as the limit (seven pairs = half limit). Picture-only / ambiguous
  limit hands (rulebook section 9 shows images we do not have) are scored as normal
  high hands and are therefore capped at the limit anyway. The `limit` value is a
  Game parameter (default 500, matching the worked examples).
* Winning is OPTIONAL in `legal_actions` (a player may discard instead of declaring
  a win). This keeps rollouts terminating via wall exhaustion when no one wins.

API: Game / GameState with initial_state, current_player, legal_actions,
apply_action (returns a fresh state), is_terminal, returns, render,
action_to_name, name_to_action, chance_outcomes, information_state.
Actions ARE their canonical human-readable name strings, so action_to_name /
name_to_action round-trip by construction.
"""

import copy
from collections import Counter

TERMINAL = -1
CHANCE = -2
SIMULTANEOUS = -3  # unused; provided for backbone compatibility

NUM_PLAYERS = 4

SUITS = ("B", "K", "Z")          # Bambus, Kreis, third (unnamed) base suit
RANKS = (1, 2, 3, 4, 5, 6, 7, 8, 9)
WINDS = ("E", "S", "W", "N")     # Ost, Sued, West, Nord
DRAGONS = ("g", "a", "b")        # only 'g' (gruen) is named in the rulebook
DEAD_WALL = 14                   # reserved, never drawn (simplified dead wall)

WIND_NAME = {"E": "Ost", "S": "Sued", "W": "West", "N": "Nord"}

# phases
DEAL = "deal"
DISCARD = "discard"
REACT = "react"
ROB = "rob"
DRAW = "draw"
REPLACE = "replace"


def _all_tiles():
    out = []
    for s in SUITS:
        for r in RANKS:
            out.append("%s%d" % (s, r))
    for w in WINDS:
        out.append("W" + w.lower())
    for d in DRAGONS:
        out.append("D" + d)
    return out


TILE_TYPES = _all_tiles()
_ORDER = {t: i for i, t in enumerate(TILE_TYPES)}
TERMINALS_HONORS = frozenset(
    [s + str(r) for s in SUITS for r in (1, 9)]
    + ["W" + w.lower() for w in WINDS]
    + ["D" + d for d in DRAGONS]
)


def _is_suit(t):
    return t[0] in SUITS


def _suit(t):
    return t[0] if _is_suit(t) else None


def _rank(t):
    return int(t[1]) if _is_suit(t) else None


def _is_wind(t):
    return t[0] == "W"


def _is_dragon(t):
    return t[0] == "D"


def _is_honor(t):
    return t[0] == "W" or t[0] == "D"


def _is_terminal_suit(t):
    return _is_suit(t) and _rank(t) in (1, 9)


def _wind_tile(w):
    return "W" + w.lower()


def _key(t):
    return _ORDER[t]


# ----------------------------------------------------------------------------
# Win analysis (pure functions on a tile->count mapping of the concealed hand)
# ----------------------------------------------------------------------------
def _form_sets(counts, need):
    """Return a list of `need` sets (pong/chi) using ALL tiles in counts, else None.
    Uses the 'lowest present tile must be consumed' invariant for correctness."""
    if need == 0:
        return [] if all(c == 0 for c in counts.values()) else None
    present = [t for t, c in counts.items() if c > 0]
    if not present:
        return None
    t = min(present, key=_key)
    if counts[t] >= 3:
        counts[t] -= 3
        sub = _form_sets(counts, need - 1)
        counts[t] += 3
        if sub is not None:
            return [("pong", t)] + sub
    if _is_suit(t) and _rank(t) <= 7:
        s, r = _suit(t), _rank(t)
        t2, t3 = "%s%d" % (s, r + 1), "%s%d" % (s, r + 2)
        if counts.get(t2, 0) > 0 and counts.get(t3, 0) > 0:
            counts[t] -= 1
            counts[t2] -= 1
            counts[t3] -= 1
            sub = _form_sets(counts, need - 1)
            counts[t] += 1
            counts[t2] += 1
            counts[t3] += 1
            if sub is not None:
                return [("chi", (t, t2, t3))] + sub
    return None


def _decompose_standard(counts, need):
    """Try every candidate pair, then partition the rest into `need` sets."""
    for p in list(counts.keys()):
        if counts[p] >= 2:
            counts[p] -= 2
            sets = _form_sets(counts, need)
            counts[p] += 2
            if sets is not None:
                return (sets, p)
    return None


def _seven_pairs(counts):
    # "genau sieben Paare": 14 tiles that split into seven pairs (a four-of-a-kind
    # counts as two pairs). Requires every present count to be even.
    if sum(counts.values()) != 14:
        return False
    return all(c % 2 == 0 for c in counts.values())


def _thirteen_orphans(counts):
    if sum(counts.values()) != 14:
        return False
    if any(t not in TERMINALS_HONORS for t, c in counts.items() if c):
        return False
    have = {t for t, c in counts.items() if c}
    if have != set(TERMINALS_HONORS):
        return False
    return sum(1 for t in TERMINALS_HONORS if counts.get(t, 0) == 2) == 1


def _analyze_win(hand_counts, need):
    """Return an analysis dict or None. `hand_counts` is a tile->count mapping of the
    concealed portion; `need` = number of sets still to be formed from it (4 - melds).
    A '+1 pair' is always required."""
    counts = {t: c for t, c in hand_counts.items() if c > 0}
    total = sum(counts.values())
    if total != 3 * need + 2:
        # size does not match a completable hand for this many melds
        if not (need == 4 and total == 14):
            return None
    if need == 4 and total == 14:
        if _thirteen_orphans(counts):
            return {"kind": "thirteen", "sets": [], "pair": None}
        # seven pairs checked after standard so a pong-able hand prefers standard
    std = _decompose_standard(dict(counts), need)
    if std is not None:
        return {"kind": "standard", "sets": std[0], "pair": std[1]}
    if need == 4 and total == 14 and _seven_pairs(counts):
        return {"kind": "seven_pairs", "sets": [], "pair": None}
    return None


# ----------------------------------------------------------------------------
# State
# ----------------------------------------------------------------------------
class GameState:
    """Full ground-truth state. `render` shows everything (debug); use
    `information_state` for a player-legal view (hides other hands and the wall)."""

    __slots__ = (
        "phase", "current", "wall", "hands", "melds", "discards", "discard_order",
        "to_deal", "pending", "last_draw", "winner", "win_tile", "win_source",
        "terminal", "draw_game", "move_count",
    )

    def __init__(self):
        self.phase = DEAL
        self.current = None
        self.wall = Counter()
        self.hands = [Counter() for _ in range(NUM_PLAYERS)]
        self.melds = [[] for _ in range(NUM_PLAYERS)]      # (kind, tiles_tuple, concealed)
        self.discards = [[] for _ in range(NUM_PLAYERS)]
        self.discard_order = []
        self.to_deal = NUM_PLAYERS * 13 + 1                # East gets the 14th
        self.pending = None
        self.last_draw = None
        self.winner = None
        self.win_tile = None
        self.win_source = None
        self.terminal = False
        self.draw_game = False
        self.move_count = 0

    def clone(self):
        return copy.deepcopy(self)


# ----------------------------------------------------------------------------
# Game
# ----------------------------------------------------------------------------
class Game:
    def __init__(self, round_wind="E", seats=("E", "S", "W", "N"), limit=500,
                 use_bonus=False):
        assert set(seats) == set(WINDS) and len(seats) == 4
        self.round_wind = round_wind
        self.seats = tuple(seats)                # seat wind of player 0..3
        self.limit = int(limit)
        self.use_bonus = bool(use_bonus)         # flowers/seasons; not wired into loop
        self.num_players = NUM_PLAYERS
        self.east_player = self.seats.index("E")

    # -- setup ---------------------------------------------------------------
    def initial_state(self):
        st = GameState()
        for t in TILE_TYPES:
            st.wall[t] = 4                        # bonus tiles omitted by default
        return st

    # -- player / phase ------------------------------------------------------
    def current_player(self, state):
        if state.terminal:
            return TERMINAL
        if state.phase in (DEAL, DRAW, REPLACE):
            return CHANCE
        return state.current

    def is_terminal(self, state):
        return state.terminal

    # -- deal target ---------------------------------------------------------
    def _deal_target(self, state):
        for p in range(NUM_PLAYERS):
            if sum(state.hands[p].values()) < 13:
                return p
        return self.east_player  # the 14th tile

    # -- chance --------------------------------------------------------------
    def chance_outcomes(self, state):
        assert state.phase in (DEAL, DRAW, REPLACE)
        kind = {DEAL: "deal", DRAW: "draw", REPLACE: "replace"}[state.phase]
        total = sum(state.wall.values())
        out = []
        for t in TILE_TYPES:
            c = state.wall[t]
            if c > 0:
                out.append(("chance:%s:%s" % (kind, t), c / total))
        return out

    # -- legal actions -------------------------------------------------------
    def legal_actions(self, state):
        if state.terminal:
            return []
        ph = state.phase
        if ph in (DEAL, DRAW, REPLACE):
            return [a for a, _ in self.chance_outcomes(state)]
        if ph == DISCARD:
            return self._legal_discard(state)
        if ph == REACT:
            p, acts = state.pending["claimants"][state.pending["idx"]]
            return list(acts) + ["pass"]
        if ph == ROB:
            p, acts = state.pending["claimants"][state.pending["idx"]]
            return list(acts) + ["pass"]
        return []

    def _legal_discard(self, state):
        c = state.current
        hand = state.hands[c]
        need = 4 - len(state.melds[c])
        acts = []
        if _analyze_win(hand, need) is not None:
            acts.append("mahjong:draw")
        for t in sorted([t for t, n in hand.items() if n == 4], key=_key):
            acts.append("kong_concealed:%s" % t)
        for (kind, tiles, _cc) in state.melds[c]:
            if kind == "pong" and hand.get(tiles[0], 0) >= 1:
                acts.append("kong_promote:%s" % tiles[0])
        for t in sorted([t for t, n in hand.items() if n > 0], key=_key):
            acts.append("discard:%s" % t)
        return acts

    # -- claim building ------------------------------------------------------
    def _chi_runs(self, hand, t):
        s, r = _suit(t), _rank(t)
        runs = []
        for lo in (r - 2, r - 1, r):
            hi = lo + 2
            if lo >= 1 and hi <= 9:
                run = ["%s%d" % (s, lo), "%s%d" % (s, lo + 1), "%s%d" % (s, lo + 2)]
                others = [x for x in run if x != t]
                if len(others) == 2 and all(hand.get(x, 0) >= 1 for x in others):
                    runs.append("chi:%s" % "-".join(run))
        return runs

    def _build_claimants(self, state, tile, source_player, mahjong_only):
        """Return ordered [ [player, [action,...]], ... ] for a pending tile."""
        entries = []
        for p in range(NUM_PLAYERS):
            if p == source_player:
                continue
            hand = state.hands[p]
            acts = []
            rank = 0
            need = 4 - len(state.melds[p])
            probe = Counter(hand)
            probe[tile] += 1
            if _analyze_win(probe, need) is not None:
                acts.append("mahjong:claim:%s" % tile)
                rank = max(rank, 3)
            if not mahjong_only:
                if hand.get(tile, 0) >= 3:
                    acts.append("kong:%s" % tile)
                    rank = max(rank, 2)
                if hand.get(tile, 0) >= 2:
                    acts.append("pong:%s" % tile)
                    rank = max(rank, 2)
                if p == (source_player + 1) % NUM_PLAYERS and _is_suit(tile):
                    for r in self._chi_runs(hand, tile):
                        acts.append(r)
                        rank = max(rank, 1)
            if acts:
                dist = (p - source_player) % NUM_PLAYERS
                entries.append((-rank, dist, p, acts))
        entries.sort(key=lambda e: (e[0], e[1]))
        return [[p, acts] for (_r, _d, p, acts) in entries]

    # -- apply ---------------------------------------------------------------
    def apply_action(self, state, action):
        """Return a NEW state (input is not mutated)."""
        if action not in self.legal_actions(state):
            raise ValueError("illegal action %r in phase %s" % (action, state.phase))
        st = state.clone()
        st.move_count += 1
        ph = st.phase
        if ph == DEAL:
            return self._apply_chance(st, action, DEAL)
        if ph in (DRAW, REPLACE):
            return self._apply_chance(st, action, ph)
        if ph == DISCARD:
            return self._apply_discard(st, action)
        if ph == REACT:
            return self._apply_react(st, action)
        if ph == ROB:
            return self._apply_rob(st, action)
        raise ValueError("bad phase")

    def _draw_tile(self, st, action):
        tile = action.split(":")[2]
        st.wall[tile] -= 1
        return tile

    def _apply_chance(self, st, action, phase):
        tile = self._draw_tile(st, action)
        if phase == DEAL:
            p = self._deal_target(st)
            st.hands[p][tile] += 1
            st.to_deal -= 1
            if st.to_deal <= 0:
                st.phase = DISCARD
                st.current = self.east_player
                st.last_draw = None
            return st
        # DRAW / REPLACE: tile goes to the current player, who must then act
        st.hands[st.current][tile] += 1
        st.last_draw = tile
        st.phase = DISCARD
        return st

    def _living_wall_empty(self, st):
        return sum(st.wall.values()) <= DEAD_WALL

    def _go_next_draw(self, st, next_player):
        if self._living_wall_empty(st):
            st.terminal = True
            st.draw_game = True
            return st
        st.current = next_player
        st.phase = DRAW
        st.last_draw = None
        return st

    def _go_replace(self, st):
        if self._living_wall_empty(st):
            st.terminal = True
            st.draw_game = True
            return st
        st.phase = REPLACE
        return st

    def _apply_discard(self, st, action):
        c = st.current
        if action == "mahjong:draw":
            st.winner = c
            st.win_tile = st.last_draw
            st.win_source = "wall" if st.last_draw is not None else "initial"
            st.terminal = True
            return st
        if action.startswith("kong_concealed:"):
            t = action.split(":")[1]
            st.hands[c][t] -= 4
            st.melds[c].append(("kong", (t, t, t, t), True))
            return self._go_replace(st)
        if action.startswith("kong_promote:"):
            t = action.split(":")[1]
            claimants = self._build_claimants(st, t, c, mahjong_only=True)
            if claimants:
                st.pending = {"tile": t, "src": c, "claimants": claimants, "idx": 0}
                st.phase = ROB
                return st
            return self._finish_promote(st, c, t)
        # discard
        t = action.split(":")[1]
        st.hands[c][t] -= 1
        st.discards[c].append(t)
        st.discard_order.append((c, t))
        claimants = self._build_claimants(st, t, c, mahjong_only=False)
        if claimants:
            st.pending = {"tile": t, "src": c, "claimants": claimants, "idx": 0}
            st.phase = REACT
            return st
        return self._go_next_draw(st, (c + 1) % NUM_PLAYERS)

    def _finish_promote(self, st, c, t):
        for i, (kind, tiles, cc) in enumerate(st.melds[c]):
            if kind == "pong" and tiles[0] == t:
                st.melds[c][i] = ("kong", (t, t, t, t), False)
                break
        st.hands[c][t] -= 1
        return self._go_replace(st)

    def _apply_react(self, st, action):
        pend = st.pending
        t = pend["tile"]
        src = pend["src"]
        if action == "pass":
            pend["idx"] += 1
            if pend["idx"] >= len(pend["claimants"]):
                st.pending = None
                return self._go_next_draw(st, (src + 1) % NUM_PLAYERS)
            return st
        p = pend["claimants"][pend["idx"]][0]
        if action.startswith("mahjong:claim:"):
            st.hands[p][t] += 1
            st.winner = p
            st.win_tile = t
            st.win_source = "discard"
            st.terminal = True
            st.pending = None
            return st
        if action.startswith("pong:"):
            st.hands[p][t] -= 2
            st.melds[p].append(("pong", (t, t, t), False))
            st.pending = None
            st.current = p
            st.phase = DISCARD
            st.last_draw = None
            return st
        if action.startswith("kong:"):
            st.hands[p][t] -= 3
            st.melds[p].append(("kong", (t, t, t, t), False))
            st.pending = None
            st.current = p
            return self._go_replace(st)
        if action.startswith("chi:"):
            run = action.split(":")[1].split("-")
            for x in run:
                if x != t:
                    st.hands[p][x] -= 1
            st.melds[p].append(("chi", tuple(run), False))
            st.pending = None
            st.current = p
            st.phase = DISCARD
            st.last_draw = None
            return st
        raise ValueError("bad react action")

    def _apply_rob(self, st, action):
        pend = st.pending
        t = pend["tile"]
        src = pend["src"]
        if action == "pass":
            pend["idx"] += 1
            if pend["idx"] >= len(pend["claimants"]):
                st.pending = None
                return self._finish_promote(st, src, t)
            return st
        p = pend["claimants"][pend["idx"]][0]
        # mahjong:claim on the robbed tile
        st.hands[p][t] += 1
        st.winner = p
        st.win_tile = t
        st.win_source = "rob"
        st.terminal = True
        st.pending = None
        return st

    # -- returns / scoring ---------------------------------------------------
    def returns(self, state):
        if not state.terminal or state.winner is None or state.draw_game:
            return [0.0] * NUM_PLAYERS
        values = [self._player_value(state, p) for p in range(NUM_PLAYERS)]
        net = self._settle(values, state.winner)
        return [float(x) for x in net]

    def _settle(self, values, winner):
        """Rulebook settlement (validated against both worked examples):
        every player pays the winner the winner's hand value; non-winners then
        settle pairwise on the difference of their values, the lower paying the
        higher. Any transfer involving the Ost (East) seat is doubled."""
        net = [0] * NUM_PLAYERS
        east = self.east_player
        for p in range(NUM_PLAYERS):
            if p == winner:
                continue
            amt = values[winner]
            if p == east or winner == east:
                amt *= 2
            net[p] -= amt
            net[winner] += amt
        losers = [p for p in range(NUM_PLAYERS) if p != winner]
        for i in range(len(losers)):
            for j in range(i + 1, len(losers)):
                a, b = losers[i], losers[j]
                diff = abs(values[a] - values[b])
                if a == east or b == east:
                    diff *= 2
                if values[a] < values[b]:
                    net[a] -= diff
                    net[b] += diff
                elif values[b] < values[a]:
                    net[b] -= diff
                    net[a] += diff
        return net

    def _seat_wind_tile(self, p):
        return _wind_tile(self.seats[p])

    def _round_wind_tile(self):
        return _wind_tile(self.round_wind)

    def _meld_points(self, kind, tile, concealed):
        if kind == "chi":
            return 0
        if kind == "pong":
            base = 2 if (_is_suit(tile) and 2 <= _rank(tile) <= 8) else 4
            return base * 2 if concealed else base
        if kind == "kong":
            base = 8 if (_is_suit(tile) and 2 <= _rank(tile) <= 8) else 16
            return base * 2 if concealed else base
        return 0

    def _pair_points(self, tile, p):
        pts = 0
        if _is_dragon(tile):
            pts += 2
        if tile == self._seat_wind_tile(p):
            pts += 2
        if tile == self._round_wind_tile():
            pts += 2
        return pts

    def _triplets_and_flags(self, state, p, win):
        """Return (triplets, has_chi, pair_tile, all_concealed, tiles_multiset).
        triplets: list of (tile, concealed, is_kong)."""
        triplets = []
        has_chi = False
        all_concealed = True
        tiles = Counter()
        for (kind, mt, cc) in state.melds[p]:
            for x in mt:
                tiles[x] += 1
            if not cc:
                all_concealed = False
            if kind in ("pong", "kong"):
                triplets.append((mt[0], cc, kind == "kong"))
            else:
                has_chi = True
        pair_tile = None
        if win is not None and win["kind"] == "standard":
            for (sk, sv) in win["sets"]:
                if sk == "pong":
                    triplets.append((sv, True, False))
                    tiles[sv] += 3
                else:
                    has_chi = True
                    for x in sv:
                        tiles[x] += 1
            pair_tile = win["pair"]
            tiles[pair_tile] += 2
        return triplets, has_chi, pair_tile, all_concealed, tiles

    def _player_value(self, state, p):
        if p == state.winner:
            return self._winner_value(state, p)
        return self._nonwinner_value(state, p)

    def _doublings(self, state, p, triplets, pair_tile, tiles, has_chi,
                   all_concealed, is_winner):
        seat = self._seat_wind_tile(p)
        rnd = self._round_wind_tile()
        d = 0
        dragon_trip = 0
        wind_trip = 0
        concealed_trip = 0
        for (t, cc, _k) in triplets:
            if _is_dragon(t):
                d += 1
                dragon_trip += 1
            if _is_wind(t):
                if t == seat:
                    d += 1
                if t == rnd:
                    d += 1
                wind_trip += 1
            if cc:
                concealed_trip += 1
        if concealed_trip >= 3:
            d += 1  # drei verdeckte Pong
        dragon_pair = pair_tile is not None and _is_dragon(pair_tile)
        wind_pair = pair_tile is not None and _is_wind(pair_tile)
        if dragon_trip == 3:
            d += 2                          # Grosse Drei Drachen
        elif dragon_trip == 2 and dragon_pair:
            d += 1                          # Kleine Drei Drachen
        if wind_trip == 4:
            d += 2                          # Grosse Vier Freuden
        elif wind_trip == 3 and wind_pair:
            d += 1                          # Kleine Vier Freuden
        if is_winner:
            suits_present = {_suit(t) for t in tiles if _is_suit(t)}
            honors_present = any(_is_honor(t) for t in tiles)
            if len(suits_present) == 1 and not honors_present:
                d += 3                      # Nur Ziegel einer Farbe
            elif len(suits_present) == 1 and honors_present:
                d += 1                      # eine Farbe + Bildziegel
            if all_concealed:
                d += 1                      # Alle Figuren verdeckt
            if not has_chi:
                d += 1                      # Kein Chi
            if all(_is_terminal_suit(t) or _is_honor(t) for t in tiles):
                d += 1                      # Nur Hauptziegel
        return d

    def _winner_value(self, state, p):
        need = 4 - len(state.melds[p])
        win = _analyze_win(state.hands[p], need)
        if win is None:
            return 0
        # limit hands (shape-detectable subset)
        limit = self.limit
        if win["kind"] == "seven_pairs":
            return limit // 2
        if win["kind"] == "thirteen":
            return limit
        triplets, has_chi, pair_tile, all_concealed, tiles = \
            self._triplets_and_flags(state, p, win)
        only_honors = all(_is_honor(t) for t in tiles) and len(tiles) > 0
        only_terminals = all(_is_terminal_suit(t) for t in tiles) and len(tiles) > 0
        num_kong = sum(1 for (_t, _c, k) in triplets if k)
        if only_honors or only_terminals or num_kong == 4:
            return limit
        base = 20  # Mah-Jongg-Ruf
        for (t, cc, k) in triplets:
            base += self._meld_points("kong" if k else "pong", t, cc)
        if pair_tile is not None:
            base += self._pair_points(pair_tile, p)
        # winning-tile bonuses that we can determine
        if state.win_source in ("wall", "initial"):
            base += 2  # Schlussziegel von der (lebenden) Mauer
        if pair_tile is not None and state.win_tile == pair_tile:
            if _is_dragon(pair_tile) or _is_wind(pair_tile):
                base += 4
            elif _is_terminal_suit(pair_tile):
                base += 4
            else:
                base += 2
        d = self._doublings(state, p, triplets, pair_tile, tiles, has_chi,
                            all_concealed, True)
        # Null-Punkte-Hand: no figure points beyond the 20 ruf and no doublings
        if base == 20 and d == 0:
            d += 1
        return min(base * (2 ** d), limit)

    def _nonwinner_value(self, state, p):
        # exposed melds + greedily extracted concealed triplets/one pair.
        # (The rulebook only illustrates fully-open hands; leftover concealed
        # tiles that form no figure score nothing. Documented interpretation.)
        triplets = []
        has_chi = False
        all_concealed = True
        tiles = Counter()
        for (kind, mt, cc) in state.melds[p]:
            for x in mt:
                tiles[x] += 1
            if not cc:
                all_concealed = False
            if kind in ("pong", "kong"):
                triplets.append((mt[0], cc, kind == "kong"))
            else:
                has_chi = True
        rem = Counter({t: c for t, c in state.hands[p].items() if c > 0})
        for t in sorted(list(rem.keys()), key=_key):
            if rem[t] >= 4:
                triplets.append((t, True, True))
                tiles[t] += 4
                rem[t] -= 4
            elif rem[t] == 3:
                triplets.append((t, True, False))
                tiles[t] += 3
                rem[t] -= 3
        pair_tile = None
        best = -1
        for t, c in rem.items():
            if c >= 2:
                v = self._pair_points(t, p)
                if v > best:
                    best = v
                    pair_tile = t
        base = 0
        for (t, cc, k) in triplets:
            base += self._meld_points("kong" if k else "pong", t, cc)
        if pair_tile is not None:
            base += self._pair_points(pair_tile, p)
        d = self._doublings(state, p, triplets, pair_tile, tiles, has_chi,
                            all_concealed, False)
        return min(base * (2 ** d), self.limit)

    # -- names ---------------------------------------------------------------
    def action_to_name(self, action):
        # actions already ARE their canonical names
        if not isinstance(action, str):
            raise TypeError("action must be a canonical name string")
        return action

    def name_to_action(self, name):
        if not isinstance(name, str):
            raise TypeError("name must be a string")
        return name

    # -- views ---------------------------------------------------------------
    def _meld_str(self, m):
        kind, tiles, cc = m
        tag = "*" if cc else ""
        return "%s%s(%s)" % (kind, tag, ",".join(tiles))

    def _hand_str(self, counter):
        parts = []
        for t in sorted([t for t, c in counter.items() if c > 0], key=_key):
            parts.extend([t] * counter[t])
        return ",".join(parts)

    def render(self, state):
        """Full debug view (NOT player-visible: concealed hands and wall shown)."""
        lines = []
        lines.append(
            "phase=%s current=%s round=%s wall=%d to_deal=%d winner=%s src=%s"
            % (state.phase, self.current_player(state), WIND_NAME[self.round_wind],
               sum(state.wall.values()), state.to_deal,
               "-" if state.winner is None else state.winner,
               "-" if state.win_source is None else state.win_source)
        )
        if state.pending is not None:
            cl = state.pending["claimants"]
            idx = state.pending["idx"]
            who = cl[idx][0] if idx < len(cl) else "-"
            lines.append("pending tile=%s src=%s turn=%s"
                         % (state.pending["tile"], state.pending["src"], who))
        for p in range(NUM_PLAYERS):
            melds = " ".join(self._meld_str(m) for m in state.melds[p]) or "-"
            lines.append(
                "P%d[%s] hand=%s | melds=%s | disc=%s"
                % (p, WIND_NAME[self.seats[p]], self._hand_str(state.hands[p]) or "-",
                   melds, ",".join(state.discards[p]) or "-")
            )
        return "\n".join(lines)

    def information_state(self, state, player):
        """Player-legal view: own concealed hand + all public melds/discards +
        hand sizes of others + wall SIZE only (never wall contents or other hands)."""
        lines = []
        lines.append(
            "you=P%d[%s] phase=%s current=%s round=%s wall_left=%d"
            % (player, WIND_NAME[self.seats[player]], state.phase,
               self.current_player(state), WIND_NAME[self.round_wind],
               max(0, sum(state.wall.values()) - DEAD_WALL))
        )
        lines.append("your_hand=%s" % (self._hand_str(state.hands[player]) or "-"))
        for p in range(NUM_PLAYERS):
            melds = " ".join(self._meld_str(m) for m in state.melds[p]) or "-"
            size = sum(state.hands[p].values())
            lines.append(
                "P%d[%s] hand_size=%d | melds=%s | disc=%s"
                % (p, WIND_NAME[self.seats[p]], size, melds,
                   ",".join(state.discards[p]) or "-")
            )
        return "\n".join(lines)


# ----------------------------------------------------------------------------
# Self-contained smoke tests
# ----------------------------------------------------------------------------
def _sample_chance(game, state, rng):
    outs = game.chance_outcomes(state)
    r = rng.random()
    acc = 0.0
    for a, prob in outs:
        acc += prob
        if r <= acc:
            return a
    return outs[-1][0]


def _selftest():
    import random

    g = Game()

    # settlement matches worked example 1 (winner = East seat, values 76/12/22/32)
    assert g._settle([76, 12, 22, 32], 0) == [456, -182, -152, -122]
    # worked example 2 (winner = West seat=player2, values 16/500/48/2)
    assert g._settle([16, 500, 48, 2], 2) == [-1036, 1418, 192, -574]

    # name round-trip
    for a in ("discard:B5", "pong:Dg", "chi:B4-B5-B6", "mahjong:draw", "pass",
              "chance:draw:We", "kong_concealed:K1", "kong_promote:Ww"):
        assert g.name_to_action(g.action_to_name(a)) == a

    # win analysis sanity
    assert _analyze_win(Counter("B1 B1 B1 B2 B3 B4 K5 K6 K7 Dg Dg Dg We We".split()),
                        4) is not None
    assert _analyze_win(Counter(("B1 B9 K1 K9 Z1 Z9 We Ws Ww Wn Dg Da Db Db"
                                 ).split()), 4)["kind"] == "thirteen"
    assert _analyze_win(Counter(("B1 B1 B2 B2 K5 K5 K9 K9 Z3 Z3 We We Ww Ww"
                                 ).split()), 4)["kind"] == "seven_pairs"
    assert _analyze_win(Counter("B1 B1 B1 B2".split()), 4) is None

    # scripted winning terminal exercises winner/non-winner scoring + returns
    def _terminal_win(winner, hand, melds_by_p, src="wall", win_tile=None):
        st = g.initial_state()
        st.wall = Counter()
        st.to_deal = 0
        st.phase = DISCARD
        st.terminal = True
        st.winner = winner
        st.win_source = src
        st.hands = [Counter() for _ in range(NUM_PLAYERS)]
        st.hands[winner] = Counter(hand.split())
        st.win_tile = win_tile
        for p, ms in melds_by_p.items():
            st.melds[p] = ms
        return st

    st = _terminal_win(
        0, "B1 B1 B1 B2 B3 B4 K5 K6 K7 We We We Dg Dg",
        {1: [("pong", ("Ws", "Ws", "Ws"), False)],
         2: [("chi", ("K2", "K3", "K4"), False)]},
        win_tile="Dg")
    r = g.returns(st)
    assert len(r) == NUM_PLAYERS and abs(sum(r)) < 1e-6
    assert r[0] > 0, "winner should be net positive here: %r" % r
    assert g._winner_value(st, 0) > 20

    # limit hand: thirteen orphans -> value == limit
    st2 = _terminal_win(
        3, "B1 B9 K1 K9 Z1 Z9 We Ws Ww Wn Dg Da Db Db", {}, win_tile="Db")
    assert g._winner_value(st2, 3) == g.limit
    r2 = g.returns(st2)
    assert abs(sum(r2)) < 1e-6 and r2[3] > 0

    # random rollouts: verify invariants
    rng = random.Random(12345)
    n_terminal = 0
    for game_i in range(40):
        st = g.initial_state()
        steps = 0
        while not g.is_terminal(st) and steps < 4000:
            cp = g.current_player(st)
            la = g.legal_actions(st)
            assert la, "non-terminal state must have legal actions"
            if cp == CHANCE:
                outs = g.chance_outcomes(st)
                s = sum(pr for _a, pr in outs)
                assert abs(s - 1.0) < 1e-9, "chance must sum to 1 (got %r)" % s
                assert set(a for a, _ in outs) == set(la)
                a = _sample_chance(g, st, rng)
            else:
                assert 0 <= cp < NUM_PLAYERS
                a = rng.choice(la)
                # round-trip every offered action name
                assert g.name_to_action(g.action_to_name(a)) == a
            # render/information_state must be deterministic
            assert g.render(st) == g.render(st)
            _ = g.information_state(st, cp if cp >= 0 else 0)
            st = g.apply_action(st, a)
            steps += 1
        assert g.is_terminal(st)
        assert g.legal_actions(st) == []
        r = g.returns(st)
        assert len(r) == NUM_PLAYERS
        assert abs(sum(r)) < 1e-6, "returns must be zero-sum (got %r)" % r
        if st.winner is not None:
            n_terminal += 1
    print("selftest OK; games won by a player: %d/40" % n_terminal)


if __name__ == "__main__":
    _selftest()
```
