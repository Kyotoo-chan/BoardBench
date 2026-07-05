## Open questions / assumptions

**Scope.** A faithful full Mah-Jongg is far larger than one self-contained file. I implement the **core playable game** (deal → draw/discard → claims → win/washout) plus the **scoring/settlement** from the rulebook's point/doubling tables, and document what is omitted. Where the rulebook is silent I state the assumption rather than invent standard-Mahjong rules.

**Tiles (partly unstated).** The rulebook names only *Bambus* and *Kreis* among the three "Grundfarben"; I assume the third is **Zeichen** (characters). 3 suits × 9 ranks × 4, 4 winds × 4, 3 dragons × 4 = 136 tiles (Kang = "alle vier" confirms 4 copies each).

**Flowers/Seasons removed.** The rulebook explicitly allows removing bonus tiles "um das Spiel zu vereinfachen" (17-tile walls). I take that sanctioned option, so no flower/season tiles, no flower doublings, dead wall = 14, kong replacement drawn from the **living** wall (rulebook: "Ersatzstein von der lebenden Mauer").

**Dice/wall position → chance deal.** Dice only determine the invisible break point; I model the shuffled wall as chance nodes drawing uniformly from unseen tiles (14 undrawn = dead wall). East's 14th tile is modeled as East's first `Draw` (functionally identical).

**Single deal, round wind = East** (as in the rulebook's worked example, §10). The 4-round *Partie* rotation, dealer-retention rules, and "Neunmal Mah-Jongg" are omitted.

**Claim priority (rulebook silent).** Assumed **Mahjong-claims > Pong/Kang > Chi**; within a tier, seat order counter-clockwise from the discarder. Chi only by the right neighbor (stated).

**Win shapes:** standard 4 sets + pair, plus **seven pairs** and **thirteen orphans** (validated + scored as limit hands). Other named limit hands (nine gates, four kongs, green hand, …) are **not** auto-detected; they score by the generic table instead (documented gap).

**Scoring implemented** = the point table (set/pair/Mahjong-call points; the fine "Schlussziegel +2" bonuses are omitted), the "für alle Hände" set-doublings (dragons/winds/round-wind/3-concealed-pong/small+big three-dragons/four-winds — verified additive against §10), and a subset of "Mah-Jongg-Hand" doublings (null-points, kein Chi, all-concealed, one-suit ±honors). **Limit cap** applies to every player. Non-winners score their best hand decomposition (unmelded tiles = 0). This reproduces the rulebook's §10 second example (and its caps) **exactly**; the first §10 example is internally inconsistent with the rulebook's own point table (exposed wind-pong listed as 8, single doubling not matching the melds) and is not followed.

**`LIMIT` = 500** (from §10). Payment follows §5: everyone pays the winner; East pays/receives double; non-winners settle pairwise differences (East double) — verified to reproduce both §10 settlement tables.

```python
"""Self-contained Mah-Jongg (OpenSpiel-style API), standard library only.

See the "Open questions / assumptions" notes accompanying this file for the
scope, the rulebook-sanctioned simplifications (no flowers/seasons, single deal,
round wind = East), the assumed claim priority, and the documented scoring gaps.
Only the point/doubling tables and settlement rules of the rulebook are encoded;
several named limit hands are not auto-detected and fall back to generic scoring.
"""

from collections import Counter

# ---- sentinels -------------------------------------------------------------
TERMINAL = -1
CHANCE = -2

# ---- tile universe ---------------------------------------------------------
SUITS = ("B", "K", "Z")                       # Bambus, Kreis, Zeichen (3rd assumed)
SUIT_NAME = {"B": "Bambus", "K": "Kreis", "Z": "Zeichen"}
WINDS_TILE = ("WE", "WS", "WW", "WN")         # player p's own wind = WINDS_TILE[p]
WIND_NAME = {"WE": "WindOst", "WS": "WindSued", "WW": "WindWest", "WN": "WindNord"}
DRAGONS = ("DR", "DG", "DW")
DRAGON_NAME = {"DR": "DracheRot", "DG": "DracheGruen", "DW": "DracheWeiss"}
ROUND_WIND = "WE"                             # assumption: round wind fixed to East
LIMIT = 500                                   # from the rulebook worked example

TYPES = [s + str(r) for s in SUITS for r in range(1, 10)] + list(WINDS_TILE) + list(DRAGONS)
TIDX = {t: i for i, t in enumerate(TYPES)}
CODE2NAME = {}
for t in TYPES:
    if t[0] in SUITS:
        CODE2NAME[t] = SUIT_NAME[t[0]] + t[1]
    elif t in WIND_NAME:
        CODE2NAME[t] = WIND_NAME[t]
    else:
        CODE2NAME[t] = DRAGON_NAME[t]
NAME2CODE = {v: k for k, v in CODE2NAME.items()}
ORPHANS = frozenset(("B1", "B9", "K1", "K9", "Z1", "Z9",
                     "WE", "WS", "WW", "WN", "DR", "DG", "DW"))

# ---- tile predicates -------------------------------------------------------
def is_suit(t): return t[0] in SUITS
def is_wind(t): return t[0] == "W"
def is_dragon(t): return t[0] == "D"
def is_honor(t): return not is_suit(t)
def rank(t): return int(t[1])
def is_terminal_tile(t): return is_suit(t) and rank(t) in (1, 9)

# ---- figure point values (rulebook point table) ----------------------------
def pong_pts(t, concealed):
    if is_honor(t) or is_terminal_tile(t):
        return 8 if concealed else 4
    return 4 if concealed else 2

def kong_pts(t, concealed):
    if is_honor(t) or is_terminal_tile(t):
        return 32 if concealed else 16
    return 16 if concealed else 8

def pair_pts(t, own):
    # separate lines in the table are added (own wind == round wind counts twice)
    if is_dragon(t):
        return 2
    p = 0
    if t == own:
        p += 2
    if t == ROUND_WIND:
        p += 2
    return p

def meld_pts(m, own):
    kind, tiles, concealed = m
    if kind == "chow":
        return 0
    if kind == "pong":
        return pong_pts(tiles[0], concealed)
    if kind == "kong":
        return kong_pts(tiles[0], concealed)
    return pair_pts(tiles[0], own)

# ---- winning-shape validation ---------------------------------------------
def is_seven_pairs(hand):
    return (sum(hand.values()) == 14
            and all(v % 2 == 0 for v in hand.values())
            and sum(v // 2 for v in hand.values()) == 7)

def is_thirteen_orphans(hand):
    live = [t for t in hand if hand[t] > 0]
    return (sum(hand.values()) == 14
            and set(live) <= ORPHANS
            and all(hand.get(t, 0) >= 1 for t in ORPHANS))

def _sets_ok(c, need):
    if need == 0:
        return sum(c.values()) == 0
    live = [t for t in c if c[t] > 0]
    if not live:
        return False
    t = min(live, key=lambda x: TIDX[x])
    if c[t] >= 3:
        c2 = c.copy(); c2[t] -= 3
        if _sets_ok(c2, need - 1):
            return True
    if is_suit(t) and rank(t) <= 7:
        t1, t2 = t[0] + str(rank(t) + 1), t[0] + str(rank(t) + 2)
        if c.get(t1, 0) >= 1 and c.get(t2, 0) >= 1:
            c2 = c.copy(); c2[t] -= 1; c2[t1] -= 1; c2[t2] -= 1
            if _sets_ok(c2, need - 1):
                return True
    return False

def _decompose_standard(hand, need):
    for p in list(hand):
        if hand[p] >= 2:
            c = hand.copy(); c[p] -= 2
            if _sets_ok(c, need):
                return True
    return False

def is_winning(hand, melds):
    total = sum(hand.values())
    nm = len(melds)
    if nm == 0 and (is_seven_pairs(hand) or is_thirteen_orphans(hand)):
        return True
    need = 4 - nm
    if need < 0 or total != 3 * need + 2:
        return False
    return _decompose_standard(hand, need)

def _can_chi(hand, t):
    if not is_suit(t):
        return False
    r = rank(t)
    for lo in (r - 2, r - 1, r):
        if 1 <= lo and lo + 2 <= 9:
            a, b, c = t[0] + str(lo), t[0] + str(lo + 1), t[0] + str(lo + 2)
            if all(hand.get(x, 0) >= (1 if x != t else 1) for x in (a, b, c)):
                # need the two tiles other than t already in hand
                others = [x for x in (a, b, c) if x != t]
                if all(hand.get(x, 0) >= 1 for x in others):
                    return True
    return False

def _chi_options(hand, t):
    opts = []
    r = rank(t)
    for lo in (r - 2, r - 1, r):
        if 1 <= lo and lo + 2 <= 9:
            seq = (t[0] + str(lo), t[0] + str(lo + 1), t[0] + str(lo + 2))
            others = [x for x in seq if x != t]
            if all(hand.get(x, 0) >= 1 for x in others):
                opts.append(seq)
    return opts

def _complete_win(hand, melds, t):
    c = hand.copy(); c[t] += 1
    return is_winning(c, melds)

# ---- best scoring decomposition (unmelded tiles score 0) -------------------
def _best_decomp(hand, own):
    memo = {}

    def rec(counter, pair_used):
        key = (tuple(sorted((k, v) for k, v in counter.items() if v > 0)), pair_used)
        if key in memo:
            return memo[key]
        live = [t for t in counter if counter[t] > 0]
        if not live:
            memo[key] = (0, [], None)
            return memo[key]
        t = min(live, key=lambda x: TIDX[x])
        best = None

        def consider(cand):
            nonlocal best
            if best is None or cand[0] > best[0]:
                best = cand

        c = counter.copy(); c[t] -= 1               # drop t as un-scoring tile
        b, m, p = rec(c, pair_used); consider((b, m, p))
        if not pair_used and counter[t] >= 2:        # pair
            c = counter.copy(); c[t] -= 2
            b, m, p = rec(c, True)
            consider((b + pair_pts(t, own), m, t))
        if counter[t] >= 3:                          # concealed pong (kong only if declared)
            c = counter.copy(); c[t] -= 3
            b, m, p = rec(c, pair_used)
            consider((b + pong_pts(t, True), m + [("pong", (t, t, t), True)], p))
        if is_suit(t) and rank(t) <= 7:              # chow
            t1, t2 = t[0] + str(rank(t) + 1), t[0] + str(rank(t) + 2)
            if counter.get(t1, 0) >= 1 and counter.get(t2, 0) >= 1:
                c = counter.copy(); c[t] -= 1; c[t1] -= 1; c[t2] -= 1
                b, m, p = rec(c, pair_used)
                consider((b, m + [("chow", (t, t1, t2), True)], p))
        memo[key] = best
        return best

    return rec(Counter(hand), False)

# ---- doublings -------------------------------------------------------------
def _set_doublings(melds, pair, own):
    pk = [m for m in melds if m[0] in ("pong", "kong")]
    drag = [m for m in pk if is_dragon(m[1][0])]
    wnd = [m for m in pk if is_wind(m[1][0])]
    d = 0
    for m in pk:
        t = m[1][0]
        if is_dragon(t):
            d += 1
        if t == own:
            d += 1
        if t == ROUND_WIND:
            d += 1
    if sum(1 for m in pk if m[2]) >= 3:              # three concealed pong/kong
        d += 1
    if len(drag) == 3:                               # große Drei Drachen
        d += 2
    elif len(drag) == 2 and pair and is_dragon(pair):  # kleine Drei Drachen
        d += 1
    if len(wnd) == 4:                                # große Vier Freuden
        d += 2
    elif len(wnd) == 3 and pair and is_wind(pair):  # kleine Vier Freuden
        d += 1
    return d

def _hand_doublings(melds, pair, fig):
    d = 0
    if not any(m[0] == "chow" for m in melds):
        d += 1                                      # Kein Chi
    if all(m[2] for m in melds):
        d += 1                                      # Alle Figuren verdeckt
    if fig == 0:
        d += 1                                      # Null-Punkte-Hand
    suits, honor = set(), False
    for m in melds:
        for x in m[1]:
            if is_suit(x):
                suits.add(x[0])
            else:
                honor = True
    if pair:
        (suits.add(pair[0]) if is_suit(pair) else None)
        honor = honor or is_honor(pair)
    if len(suits) == 1 and not honor:
        d += 3                                      # nur eine Farbe
    elif len(suits) == 1 and honor:
        d += 1                                      # eine Farbe + Bildziegel
    return d

# ===========================================================================
class GameState:
    def __init__(self):
        self.phase = "deal"          # deal|draw|discard|claim|robkong|terminal
        self.hands = [Counter() for _ in range(4)]
        self.melds = [[] for _ in range(4)]         # exposed / declared sets
        self.discards = [[] for _ in range(4)]
        self.pool = Counter({t: 4 for t in TYPES})  # unseen tiles (wall + dead wall)
        self.wall = 0                # drawable tiles left in the living wall
        self.deal_count = 0
        self.drawer = None           # who receives the pending chance draw
        self.kong_replace = False
        self.current = CHANCE        # decision player for player phases
        self.last_discard = None     # (player, tile)
        self.claim_stage = None      # 'A' mahjong, 'B' pong/kong, 'C' chi
        self.claim_players = []      # remaining seats to decide in this stage
        self.claim_tile = None
        self.claim_from = None       # discarder
        self.rob = None              # (player, tile, meld_index) for kong robbing
        self.winner = None
        self.washout = False

    def clone(self):
        s = GameState.__new__(GameState)
        s.phase = self.phase
        s.hands = [h.copy() for h in self.hands]
        s.melds = [list(m) for m in self.melds]
        s.discards = [list(d) for d in self.discards]
        s.pool = self.pool.copy()
        s.wall = self.wall
        s.deal_count = self.deal_count
        s.drawer = self.drawer
        s.kong_replace = self.kong_replace
        s.current = self.current
        s.last_discard = self.last_discard
        s.claim_stage = self.claim_stage
        s.claim_players = list(self.claim_players)
        s.claim_tile = self.claim_tile
        s.claim_from = self.claim_from
        s.rob = self.rob
        s.winner = self.winner
        s.washout = self.washout
        return s


class Game:
    num_players = 4

    # -- lifecycle ----------------------------------------------------------
    def initial_state(self):
        return GameState()

    def current_player(self, state):
        if state.phase == "terminal":
            return TERMINAL
        if state.phase in ("deal", "draw"):
            return CHANCE
        return state.current

    def is_terminal(self, state):
        return state.phase == "terminal"

    # -- chance -------------------------------------------------------------
    def chance_outcomes(self, state):
        prefix = "Deal:" if state.phase == "deal" else "Draw:"
        total = sum(state.pool.values())
        out = []
        for t in TYPES:
            if state.pool[t] > 0:
                out.append((prefix + CODE2NAME[t], state.pool[t] / total))
        return out

    # -- legal actions ------------------------------------------------------
    def legal_actions(self, state):
        ph = state.phase
        if ph == "terminal":
            return []
        if ph in ("deal", "draw"):
            return sorted(a for a, _ in self.chance_outcomes(state))
        if ph == "discard":
            return self._discard_actions(state, state.current)
        if ph == "robkong":
            return ["Mahjong", "Pass"]
        if ph == "claim":
            cur = state.claim_players[0]
            t = state.claim_tile
            nm = CODE2NAME[t]
            if state.claim_stage == "A":
                return ["Mahjong", "Pass"]
            if state.claim_stage == "B":
                acts = []
                if state.hands[cur][t] >= 3:
                    acts.append("Kong:" + nm)
                if state.hands[cur][t] >= 2:
                    acts.append("Pong:" + nm)
                acts.append("Pass")
                return sorted(acts)
            # stage C: chi by right neighbour
            acts = ["Chi:" + "+".join(CODE2NAME[x] for x in seq)
                    for seq in _chi_options(state.hands[cur], t)]
            acts.append("Pass")
            return sorted(acts)
        return []

    def _discard_actions(self, state, p):
        hand, melds = state.hands[p], state.melds[p]
        acts = ["Discard:" + CODE2NAME[t] for t in hand if hand[t] > 0]
        if is_winning(hand, melds):
            acts.append("Mahjong")
        for t in hand:
            if hand[t] == 4:
                acts.append("ConcealedKong:" + CODE2NAME[t])
        for m in melds:
            if m[0] == "pong" and hand.get(m[1][0], 0) >= 1:
                acts.append("AddedKong:" + CODE2NAME[m[1][0]])
        return sorted(set(acts))

    # -- transitions --------------------------------------------------------
    def apply_action(self, state, action):
        if action not in self.legal_actions(state):
            raise ValueError("illegal action: %r" % (action,))
        s = state.clone()
        ph = s.phase
        if ph == "deal":
            self._apply_deal(s, action)
        elif ph == "draw":
            self._apply_draw(s, action)
        elif ph == "discard":
            self._apply_discard(s, action)
        elif ph == "claim":
            self._apply_claim(s, action)
        elif ph == "robkong":
            self._apply_robkong(s, action)
        else:
            raise ValueError("no actions in terminal state")
        return s

    def _apply_deal(self, s, action):
        t = NAME2CODE[action[len("Deal:"):]]
        s.pool[t] -= 1
        s.hands[s.deal_count // 13][t] += 1
        s.deal_count += 1
        if s.deal_count == 52:
            s.wall = sum(s.pool.values()) - 14      # reserve 14-tile dead wall
            self._to_draw(s, 0, False)

    def _apply_draw(self, s, action):
        t = NAME2CODE[action[len("Draw:"):]]
        s.pool[t] -= 1
        s.wall -= 1
        s.hands[s.drawer][t] += 1
        s.kong_replace = False
        s.phase = "discard"
        s.current = s.drawer

    def _apply_discard(self, s, action):
        p = s.current
        if action == "Mahjong":                      # self-draw win
            self._win(s, p)
            return
        if action.startswith("Discard:"):
            t = NAME2CODE[action[len("Discard:"):]]
            s.hands[p][t] -= 1
            s.discards[p].append(t)
            s.last_discard = (p, t)
            self._enter_claim(s, p, t)
            return
        if action.startswith("ConcealedKong:"):
            t = NAME2CODE[action[len("ConcealedKong:"):]]
            s.hands[p][t] -= 4
            s.melds[p].append(("kong", (t, t, t, t), True))
            self._to_draw(s, p, True)
            return
        if action.startswith("AddedKong:"):
            t = NAME2CODE[action[len("AddedKong:"):]]
            idx = next(i for i, m in enumerate(s.melds[p])
                       if m == ("pong", (t, t, t), False))
            s.melds[p][idx] = ("kong", (t, t, t, t), False)
            s.hands[p][t] -= 1
            order = [(p + 1) % 4, (p + 2) % 4, (p + 3) % 4]
            cands = [q for q in order if _complete_win(s.hands[q], s.melds[q], t)]
            if cands:                                # robbing the kong window
                s.phase = "robkong"
                s.rob = (p, t, idx)
                s.claim_players = cands
                s.current = cands[0]
            else:
                self._to_draw(s, p, True)
            return

    def _apply_claim(self, s, action):
        cur = s.claim_players[0]
        t = s.claim_tile
        disc = s.claim_from
        if action == "Pass":
            s.claim_players.pop(0)
            if s.claim_players:
                s.current = s.claim_players[0]
            else:
                self._advance_stage(s)
            return
        if action == "Mahjong":
            s.hands[cur][t] += 1
            s.discards[disc].remove(t)
            self._win(s, cur)
            return
        if action.startswith("Pong:"):
            s.hands[cur][t] -= 2
            s.melds[cur].append(("pong", (t, t, t), False))
            s.discards[disc].remove(t)
            s.last_discard = None
            s.phase = "discard"
            s.current = cur
            return
        if action.startswith("Kong:"):
            s.hands[cur][t] -= 3
            s.melds[cur].append(("kong", (t, t, t, t), False))
            s.discards[disc].remove(t)
            s.last_discard = None
            self._to_draw(s, cur, True)
            return
        if action.startswith("Chi:"):
            seq = tuple(NAME2CODE[x] for x in action[len("Chi:"):].split("+"))
            for x in seq:
                if x != t:
                    s.hands[cur][x] -= 1
            s.melds[cur].append(("chow", seq, False))
            s.discards[disc].remove(t)
            s.last_discard = None
            s.phase = "discard"
            s.current = cur
            return

    def _apply_robkong(self, s, action):
        cur = s.claim_players[0]
        robp, t, idx = s.rob
        if action == "Mahjong":
            s.melds[robp][idx] = ("pong", (t, t, t), False)   # robbed: left with a pong
            s.hands[cur][t] += 1
            self._win(s, cur)
            return
        s.claim_players.pop(0)
        if s.claim_players:
            s.current = s.claim_players[0]
        else:
            s.rob = None
            self._to_draw(s, robp, True)

    # -- claim staging ------------------------------------------------------
    def _enter_claim(self, s, disc, t):
        s.claim_tile = t
        s.claim_from = disc
        order = [(disc + 1) % 4, (disc + 2) % 4, (disc + 3) % 4]
        a = [q for q in order if _complete_win(s.hands[q], s.melds[q], t)]
        if a:
            s.phase = "claim"; s.claim_stage = "A"; s.claim_players = a
            s.current = a[0]; return
        self._stage_bc(s, disc, t, "A")

    def _advance_stage(self, s):
        self._stage_bc(s, s.claim_from, s.claim_tile, s.claim_stage)

    def _stage_bc(self, s, disc, t, from_stage):
        order = [(disc + 1) % 4, (disc + 2) % 4, (disc + 3) % 4]
        if from_stage in ("A",):
            b = [q for q in order if s.hands[q][t] >= 2]
            if b:
                s.phase = "claim"; s.claim_stage = "B"; s.claim_players = b
                s.current = b[0]; return
            from_stage = "B"
        if from_stage in ("A", "B"):
            right = (disc + 1) % 4
            if _can_chi(s.hands[right], t):
                s.phase = "claim"; s.claim_stage = "C"; s.claim_players = [right]
                s.current = right; return
        # nobody claimed: discard is dead, right neighbour draws
        s.claim_stage = None
        s.last_discard = None
        self._to_draw(s, (disc + 1) % 4, False)

    def _to_draw(self, s, player, kong_replace):
        if s.wall == 0:                              # living wall exhausted -> washout
            s.phase = "terminal"
            s.washout = True
            s.winner = None
            return
        s.phase = "draw"
        s.drawer = player
        s.kong_replace = kong_replace

    def _win(self, s, p):
        s.phase = "terminal"
        s.winner = p
        s.washout = False

    # -- returns / scoring --------------------------------------------------
    def returns(self, state):
        if state.phase != "terminal" or state.winner is None:
            return [0, 0, 0, 0]
        w = state.winner
        V = [self._value(state, p, p == w) for p in range(4)]
        net = [0, 0, 0, 0]
        for p in range(4):                           # everyone pays the winner
            if p == w:
                continue
            pay = V[w] * (2 if (p == 0 or w == 0) else 1)  # East pays/receives double
            net[p] -= pay
            net[w] += pay
        nonw = [p for p in range(4) if p != w]       # non-winners settle pairwise
        for i in range(len(nonw)):
            for j in range(i + 1, len(nonw)):
                a, b = nonw[i], nonw[j]
                if V[a] == V[b]:
                    continue
                diff = abs(V[a] - V[b]) * (2 if (a == 0 or b == 0) else 1)
                hi, lo = (a, b) if V[a] > V[b] else (b, a)
                net[hi] += diff
                net[lo] -= diff
        return net

    def _value(self, state, p, is_winner):
        hand = state.hands[p]
        exposed = state.melds[p]
        own = WINDS_TILE[p]
        if is_winner:
            if not exposed and is_seven_pairs(hand):
                return LIMIT // 2                    # Paariges Spiel: halbes Limit
            if not exposed and is_thirteen_orphans(hand):
                return LIMIT
            allt = [x for x in hand.elements()] + [x for m in exposed for x in m[1]]
            if allt and all(is_honor(x) for x in allt):
                return LIMIT                         # Reine Bildziegel-Hand
            if allt and all(is_terminal_tile(x) for x in allt):
                return LIMIT                         # Köpfe und Schwänze
        b, melds_c, pair = _best_decomp(hand, own)
        exp_pts = sum(meld_pts(m, own) for m in exposed)
        melds_full = list(exposed) + melds_c
        fig = exp_pts + b
        base = fig + (20 if is_winner else 0)        # Mah-Jongg-Ruf
        d = _set_doublings(melds_full, pair, own)
        if is_winner:
            d += _hand_doublings(melds_full, pair, fig)
        val = base * (2 ** d)
        return LIMIT if val > LIMIT else val

    # -- presentation -------------------------------------------------------
    def render(self, state):
        # NOTE: full-truth debug view; reveals concealed hands (not player-visible).
        out = ["phase=%s wall=%d round=%s" % (state.phase, state.wall,
                                              WIND_NAME[ROUND_WIND])]
        if state.last_discard:
            dp, dt = state.last_discard
            out.append("last_discard=P%d:%s" % (dp, CODE2NAME[dt]))
        cur = self.current_player(state)
        for p in range(4):
            hand = " ".join(sorted((t for t in state.hands[p].elements()),
                                   key=lambda x: TIDX[x]))
            melds = " ".join(self._meld_str(m) for m in state.melds[p]) or "-"
            disc = " ".join(state.discards[p]) or "-"
            mark = "*" if cur == p else " "
            out.append("%sP%d(%s) hand[%s] melds[%s] disc[%s]" %
                       (mark, p, WIND_NAME[WINDS_TILE[p]], hand, melds, disc))
        if state.phase == "terminal":
            out.append("winner=%s returns=%s" %
                       ("washout" if state.winner is None else "P%d" % state.winner,
                        self.returns(state)))
        return "\n".join(out)

    def _meld_str(self, m):
        kind, tiles, concealed = m
        body = ",".join(tiles)
        return "%s(%s%s)" % (kind, body, ",v" if concealed else "")

    def information_state(self, state, player):
        hand = " ".join(sorted((t for t in state.hands[player].elements()),
                               key=lambda x: TIDX[x]))
        lines = ["view for P%d (%s) phase=%s wall=%d" %
                 (player, WIND_NAME[WINDS_TILE[player]], state.phase, state.wall),
                 "your_hand[%s]" % hand]
        for p in range(4):
            melds = " ".join(self._meld_str(m) for m in state.melds[p]) or "-"
            disc = " ".join(state.discards[p]) or "-"
            hidden = "" if p == player else " hidden=%d" % sum(state.hands[p].values())
            lines.append("P%d melds[%s] disc[%s]%s" % (p, melds, disc, hidden))
        return "\n".join(lines)

    # -- action names (strings are already canonical => identity round-trip) -
    def action_to_name(self, action):
        return action

    def name_to_action(self, name):
        return name


# --- deterministic smoke test (no interactive input, bounded) --------------
if __name__ == "__main__":
    g = Game()
    s = g.initial_state()
    steps = 0
    while not g.is_terminal(s) and steps < 20000:
        acts = g.legal_actions(s)
        s = g.apply_action(s, acts[0])   # first legal / first chance outcome
        steps += 1
    assert g.legal_actions(s) == []
    r = g.returns(s)
    assert len(r) == 4 and sum(r) == 0   # zero-sum settlement
    print(g.render(s))
    print("steps=%d returns=%s" % (steps, r))
```
