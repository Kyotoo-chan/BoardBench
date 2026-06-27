"""
Exploding Kittens (NSFW Edition) — BoardBench self-contained engine.

Standard-library only. The rulebook is the source of truth; see the
"Open questions / assumptions" notes accompanying this file for modeling
decisions where the rules were abstracted (deck order, Nope timing, etc.).

Hidden information + chance game:
  - hands and the unknown deck are hidden (information_state / render split)
  - drawing from the unknown deck, dealing, See-the-Future materialization and
    random pair-steals are explicit CHANCE nodes (no hidden RNG in the engine)
"""

import copy
import itertools
from collections import Counter

TERMINAL = -1
CHANCE = -2

# ---- Card type identifiers --------------------------------------------------
EK = "exploding_kitten"
DEFUSE = "defuse"
ATTACK = "attack"
SKIP = "skip"          # Hops!
SHUFFLE = "shuffle"    # Mischen
FUTURE = "see_future"  # Blick in die Zukunft
FAVOR = "favor"        # Wunsch
NOPE = "nope"          # Noe!
CATS = ["cat_a", "cat_b", "cat_c", "cat_d", "cat_e"]  # cat_a = "Augenmampfende Zombiekatze"

FULL_COUNTS = {EK: 4, DEFUSE: 6, ATTACK: 4, SKIP: 4, FAVOR: 4,
               SHUFFLE: 4, FUTURE: 5, NOPE: 5}
for _c in CATS:
    FULL_COUNTS[_c] = 4

# Everything except Exploding Kittens and Defuse forms the shuffled base deck.
BASE_COUNTS = {k: v for k, v in FULL_COUNTS.items() if k not in (EK, DEFUSE)}

CARD_ORDER = [EK, DEFUSE, ATTACK, SKIP, FAVOR, SHUFFLE, FUTURE, NOPE] + CATS
SOLO_PLAYABLE = (ATTACK, SKIP, SHUFFLE, FUTURE)  # Favor handled separately (needs target)
KIND_OF = {ATTACK: "attack", SKIP: "skip", SHUFFLE: "shuffle", FUTURE: "see_future"}
WANTED_TYPES = [c for c in CARD_ORDER if c != EK]  # types a "three" may request


# ---- small formatting / ordering helpers ------------------------------------
def _ordered(d):
    """Distinct card types present in a dict/Counter, in canonical order."""
    return [c for c in CARD_ORDER if d.get(c, 0) > 0]


def _ordered_list(lst):
    cnt = Counter(lst)
    return [c for c in CARD_ORDER if cnt[c] > 0]


def _ms_str(d):
    parts = ["%s:%d" % (c, d.get(c, 0)) for c in CARD_ORDER if d.get(c, 0) > 0]
    return "{" + ", ".join(parts) + "}"


def _hand_str(hand):
    return _ms_str(Counter(hand))


def _count_str(seq):
    return _ms_str(Counter(seq))


# ============================================================================
class GameState:
    def __init__(self, num_players):
        self.num_players = num_players
        self.hands = [[] for _ in range(num_players)]
        self.alive = [True] * num_players
        self.deck_known = []   # top..down, ground-truth ordered, known portion
        self.deck_pool = {}    # card_type -> count, unknown order
        self.discard = []      # public discard pile (list of card types)
        self.phase = "DEAL"
        self.cur = CHANCE      # decision-maker player index for player phases
        self.turn_owner = 0    # whose game-turn it currently is
        self.turns_to_take = 1
        self.next_player_turns = 1
        # dealing
        self.deal_pool = {}
        self.deal_to = 0
        self.deal_remaining = 0
        # nope reaction window
        self.pending = None
        self.nope_count = 0
        self.responders = []
        self.resp_ptr = 0
        # sub-decisions / chance targets
        self.favor_target = None
        self.steal_target = None
        self.ek_player = None
        self.future_need = 0
        # private See-the-Future memory: (player, tuple_of_top_cards)
        self.last_seen = None
        self.winner = None


# ---- internal state transitions (operate on a fresh, cloned state) ----------
def _deck_size(s):
    return len(s.deck_known) + sum(s.deck_pool.values())


def _next_living(s, p):
    n = s.num_players
    i = (p + 1) % n
    while not s.alive[i]:
        i = (i + 1) % n
    return i


def _living_after(s, p):
    """Living players clockwise starting at p+1, excluding p."""
    n, out, i = s.num_players, [], (p + 1) % s.num_players
    while i != p:
        if s.alive[i]:
            out.append(i)
        i = (i + 1) % n
    return out


def _advance_turn(s):
    nxt = _next_living(s, s.turn_owner)
    s.turn_owner = nxt
    s.turns_to_take = s.next_player_turns
    s.next_player_turns = 1
    s.phase = "PLAY"
    s.cur = nxt


def _consume_turn(s):
    """One of the current player's turns has ended (draw/skip/defuse)."""
    s.turns_to_take -= 1
    if s.turns_to_take <= 0:
        _advance_turn(s)
    else:
        s.phase = "PLAY"
        s.cur = s.turn_owner


def _explode(s, p):
    s.discard.extend(s.hands[p])
    s.hands[p] = []
    s.discard.append(EK)
    s.alive[p] = False
    if sum(s.alive) <= 1:
        s.phase = "GAMEOVER"
        living = [i for i in range(s.num_players) if s.alive[i]]
        s.winner = living[0] if living else None
    else:
        s.next_player_turns = 1
        _advance_turn(s)


def _do_draw(s, card):
    owner = s.turn_owner
    s.last_seen = None  # the top of the deck changed
    if card == EK:
        if s.hands[owner].count(DEFUSE) >= 1:
            s.phase = "DEFUSE"
            s.cur = owner
            s.ek_player = owner
        else:
            _explode(s, owner)
    else:
        s.hands[owner].append(card)
        _consume_turn(s)


def _finalize_setup(s):
    np = s.num_players
    for p in range(np):
        s.hands[p].append(DEFUSE)
    pool = {}
    for c, n in s.deal_pool.items():
        pool[c] = pool.get(c, 0) + n
    ek = np - 1
    if ek > 0:
        pool[EK] = pool.get(EK, 0) + ek
    defuse_into_deck = 2 if np == 2 else (6 - np)  # 2-player variant vs. "all remaining"
    if defuse_into_deck > 0:
        pool[DEFUSE] = pool.get(DEFUSE, 0) + defuse_into_deck
    s.deck_pool = pool
    s.deal_pool = {}
    s.phase = "PLAY"
    s.turn_owner = 0
    s.cur = 0
    s.turns_to_take = 1
    s.next_player_turns = 1


def _open_window(s, actor):
    """Open a Nope reaction window for the pending action of `actor`."""
    s.nope_count = 0
    resp = [q for q in _living_after(s, actor) if s.hands[q].count(NOPE) >= 1]
    if not resp:
        _resolve_pending(s)
    else:
        s.phase = "NOPE"
        s.responders = resp
        s.resp_ptr = 0
        s.cur = resp[0]


def _resolve_pending(s):
    p = s.pending
    s.pending = None
    canceled = (s.nope_count % 2 == 1)
    s.nope_count = 0
    s.responders = []
    s.resp_ptr = 0
    owner = s.turn_owner
    s.phase = "PLAY"
    s.cur = owner
    if canceled:
        return  # played cards already on the discard pile; turn continues
    k = p["kind"]
    if k == "attack":
        s.next_player_turns = 2
        _advance_turn(s)
    elif k == "skip":
        _consume_turn(s)
    elif k == "shuffle":
        for c in s.deck_known:
            s.deck_pool[c] = s.deck_pool.get(c, 0) + 1
        s.deck_known = []
        s.last_seen = None
    elif k == "see_future":
        need = min(3, _deck_size(s)) - len(s.deck_known)
        if need > 0 and sum(s.deck_pool.values()) > 0:
            s.future_need = need
            s.phase = "FUTURE_CHANCE"
        else:
            s.last_seen = (owner, tuple(s.deck_known[:3]))
    elif k == "favor":
        t = p["target"]
        if s.alive[t] and s.hands[t]:
            s.phase = "FAVOR_GIVE"
            s.favor_target = t
            s.cur = t
    elif k == "pair":
        t = p["target"]
        if s.alive[t] and s.hands[t]:
            s.phase = "STEAL_CHANCE"
            s.steal_target = t
    elif k == "three":
        t, w = p["target"], p["wanted"]
        if s.alive[t] and w in s.hands[t]:
            s.hands[t].remove(w)
            s.hands[owner].append(w)
    elif k == "five":
        d = p["take"]
        if d in s.discard:
            s.discard.remove(d)
            s.hands[owner].append(d)


def _play_actions(s):
    owner = s.turn_owner
    hand = s.hands[owner]
    cnt = Counter(hand)
    acts = ["draw"]
    opps_nonempty = [q for q in range(s.num_players)
                     if q != owner and s.alive[q] and s.hands[q]]
    for c in SOLO_PLAYABLE:
        if cnt[c] >= 1:
            acts.append("play:" + c)
    if cnt[FAVOR] >= 1:
        for q in opps_nonempty:
            acts.append("play:%s:p%d" % (FAVOR, q))
    for c in _ordered(cnt):
        if cnt[c] >= 2:
            for q in opps_nonempty:
                acts.append("pair:%s:p%d" % (c, q))
    for c in _ordered(cnt):
        if cnt[c] >= 3:
            for q in opps_nonempty:
                for w in WANTED_TYPES:
                    acts.append("three:%s:p%d:%s" % (c, q, w))
    distinct = [c for c in CARD_ORDER if cnt[c] >= 1]
    if len(distinct) >= 5:
        disc_types = [c for c in CARD_ORDER if c != EK and c in s.discard]
        for combo in itertools.combinations(distinct, 5):
            base = "five:" + ":".join(combo) + ":take:"
            for d in disc_types:
                acts.append(base + d)
    return acts


# ============================================================================
class Game:
    def __init__(self, num_players=4):
        if not (2 <= num_players <= 5):
            raise ValueError("Exploding Kittens supports 2-5 players")
        self.num_players = num_players

    # -- core API -----------------------------------------------------------
    def initial_state(self):
        s = GameState(self.num_players)
        s.deal_pool = dict(BASE_COUNTS)
        s.deal_to = 0
        s.deal_remaining = 7 * self.num_players
        s.phase = "DEAL"
        return s

    def current_player(self, state):
        if state.phase == "GAMEOVER":
            return TERMINAL
        if state.phase in ("DEAL", "DRAW_CHANCE", "FUTURE_CHANCE", "STEAL_CHANCE"):
            return CHANCE
        return state.cur

    def is_terminal(self, state):
        return state.phase == "GAMEOVER"

    def legal_actions(self, state):
        ph = state.phase
        if ph == "GAMEOVER":
            return []
        if ph == "DEAL":
            return ["chance:deal:" + c for c in _ordered(state.deal_pool)]
        if ph == "DRAW_CHANCE":
            return ["chance:draw:" + c for c in _ordered(state.deck_pool)]
        if ph == "FUTURE_CHANCE":
            return ["chance:future:" + c for c in _ordered(state.deck_pool)]
        if ph == "STEAL_CHANCE":
            return ["chance:steal:" + c for c in _ordered_list(state.hands[state.steal_target])]
        if ph == "NOPE":
            return ["play_nope", "pass_nope"]
        if ph == "DEFUSE":
            return ["play_defuse", "explode"]
        if ph == "INSERT":
            acts = ["insert:top"]
            for k in range(1, len(state.deck_known) + 1):
                acts.append("insert:pos%d" % k)
            acts.append("insert:random")
            return acts
        if ph == "FAVOR_GIVE":
            return ["give:" + c for c in _ordered_list(state.hands[state.favor_target])]
        if ph == "PLAY":
            return _play_actions(state)
        return []

    def chance_outcomes(self, state):
        ph = state.phase
        if ph == "DEAL":
            tot = sum(state.deal_pool.values())
            return [("chance:deal:" + c, state.deal_pool[c] / tot) for c in _ordered(state.deal_pool)]
        if ph == "DRAW_CHANCE":
            tot = sum(state.deck_pool.values())
            return [("chance:draw:" + c, state.deck_pool[c] / tot) for c in _ordered(state.deck_pool)]
        if ph == "FUTURE_CHANCE":
            tot = sum(state.deck_pool.values())
            return [("chance:future:" + c, state.deck_pool[c] / tot) for c in _ordered(state.deck_pool)]
        if ph == "STEAL_CHANCE":
            h = state.hands[state.steal_target]
            tot = len(h)
            cnt = Counter(h)
            return [("chance:steal:" + c, cnt[c] / tot) for c in _ordered(cnt)]
        return []

    def apply_action(self, state, action):
        s = copy.deepcopy(state)
        ph = s.phase

        if ph == "DEAL":
            card = action.split(":")[2]
            s.deal_pool[card] -= 1
            if s.deal_pool[card] == 0:
                del s.deal_pool[card]
            s.hands[s.deal_to].append(card)
            s.deal_remaining -= 1
            if len(s.hands[s.deal_to]) == 7 and s.deal_to < s.num_players - 1:
                s.deal_to += 1
            if s.deal_remaining == 0:
                _finalize_setup(s)
            return s

        if ph == "DRAW_CHANCE":
            card = action.split(":")[2]
            s.deck_pool[card] -= 1
            if s.deck_pool[card] == 0:
                del s.deck_pool[card]
            _do_draw(s, card)
            return s

        if ph == "FUTURE_CHANCE":
            card = action.split(":")[2]
            s.deck_pool[card] -= 1
            if s.deck_pool[card] == 0:
                del s.deck_pool[card]
            s.deck_known.append(card)
            s.future_need -= 1
            if s.future_need <= 0:
                s.last_seen = (s.turn_owner, tuple(s.deck_known[:3]))
                s.phase = "PLAY"
                s.cur = s.turn_owner
            return s

        if ph == "STEAL_CHANCE":
            card = action.split(":")[2]
            t = s.steal_target
            s.hands[t].remove(card)
            s.hands[s.turn_owner].append(card)
            s.steal_target = None
            s.phase = "PLAY"
            s.cur = s.turn_owner
            return s

        if ph == "NOPE":
            if action == "play_nope":
                noper = s.cur
                s.hands[noper].remove(NOPE)
                s.discard.append(NOPE)
                s.nope_count += 1
                resp = [q for q in _living_after(s, noper) if s.hands[q].count(NOPE) >= 1]
                if not resp:
                    _resolve_pending(s)
                else:
                    s.responders = resp
                    s.resp_ptr = 0
                    s.cur = resp[0]
            elif action == "pass_nope":
                s.resp_ptr += 1
                if s.resp_ptr >= len(s.responders):
                    _resolve_pending(s)
                else:
                    s.cur = s.responders[s.resp_ptr]
            else:
                raise ValueError("illegal NOPE action: %r" % action)
            return s

        if ph == "DEFUSE":
            if action == "play_defuse":
                s.hands[s.ek_player].remove(DEFUSE)
                s.discard.append(DEFUSE)
                s.phase = "INSERT"
                s.cur = s.ek_player
            elif action == "explode":
                _explode(s, s.ek_player)
            else:
                raise ValueError("illegal DEFUSE action: %r" % action)
            return s

        if ph == "INSERT":
            if action == "insert:top":
                s.deck_known.insert(0, EK)
            elif action == "insert:random":
                s.deck_pool[EK] = s.deck_pool.get(EK, 0) + 1
            else:
                k = int(action.split(":")[1][3:])  # "posK"
                s.deck_known.insert(k, EK)
            s.last_seen = None
            s.ek_player = None
            _consume_turn(s)  # drawing the Kitten was this player's draw
            return s

        if ph == "FAVOR_GIVE":
            card = action.split(":")[1]
            t = s.favor_target
            s.hands[t].remove(card)
            s.hands[s.turn_owner].append(card)
            s.favor_target = None
            s.phase = "PLAY"
            s.cur = s.turn_owner
            return s

        if ph == "PLAY":
            owner = s.turn_owner
            if action == "draw":
                if s.deck_known:
                    card = s.deck_known.pop(0)
                    _do_draw(s, card)
                elif sum(s.deck_pool.values()) > 0:
                    s.phase = "DRAW_CHANCE"
                else:
                    _consume_turn(s)  # defensive: deck empty (per rules cannot occur)
                return s
            parts = action.split(":")
            head = parts[0]
            if head == "play":
                sub = parts[1]
                if sub in KIND_OF:
                    s.hands[owner].remove(sub)
                    s.discard.append(sub)
                    s.pending = {"kind": KIND_OF[sub]}
                    _open_window(s, owner)
                elif sub == FAVOR:
                    t = int(parts[2][1:])
                    s.hands[owner].remove(FAVOR)
                    s.discard.append(FAVOR)
                    s.pending = {"kind": "favor", "target": t}
                    _open_window(s, owner)
                else:
                    raise ValueError("illegal play: %r" % action)
                return s
            if head == "pair":
                c = parts[1]
                t = int(parts[2][1:])
                s.hands[owner].remove(c)
                s.hands[owner].remove(c)
                s.discard.extend([c, c])
                s.pending = {"kind": "pair", "target": t}
                _open_window(s, owner)
                return s
            if head == "three":
                c = parts[1]
                t = int(parts[2][1:])
                w = parts[3]
                for _ in range(3):
                    s.hands[owner].remove(c)
                s.discard.extend([c, c, c])
                s.pending = {"kind": "three", "target": t, "wanted": w}
                _open_window(s, owner)
                return s
            if head == "five":
                combo = parts[1:6]
                d = parts[7]
                for c in combo:
                    s.hands[owner].remove(c)
                s.discard.extend(combo)
                s.pending = {"kind": "five", "take": d}
                _open_window(s, owner)
                return s
            raise ValueError("illegal PLAY action: %r" % action)

        raise ValueError("no action accepted in phase %r" % ph)

    def returns(self, state):
        if state.phase != "GAMEOVER":
            return [0.0] * state.num_players
        r = [-1.0] * state.num_players
        if state.winner is not None:
            r[state.winner] = 1.0
        return r

    # -- views --------------------------------------------------------------
    def render(self, state):
        """Full ground-truth debug view (reveals hidden information)."""
        s = state
        lines = ["=== Exploding Kittens (players=%d) ===" % s.num_players,
                 "phase=%s turn_owner=%d cur=%s turns_to_take=%d next_turns=%d" %
                 (s.phase, s.turn_owner, s.cur, s.turns_to_take, s.next_player_turns),
                 "alive=" + ",".join("1" if a else "0" for a in s.alive)]
        for p in range(s.num_players):
            lines.append("hand[%d]=%s" % (p, _hand_str(s.hands[p])))
        lines.append("deck_known(top..)=" + (">".join(s.deck_known) if s.deck_known else "-"))
        lines.append("deck_pool=%s size=%d" % (_ms_str(s.deck_pool), _deck_size(s)))
        lines.append("discard=" + _count_str(s.discard))
        if s.pending is not None:
            lines.append("pending=%s nope_count=%d" % (s.pending, s.nope_count))
        if s.last_seen is not None:
            lines.append("last_seen(p%d)=%s" % (s.last_seen[0], ">".join(s.last_seen[1]) or "-"))
        if s.phase == "GAMEOVER":
            lines.append("winner=%s" % s.winner)
        return "\n".join(lines)

    def information_state(self, state, player):
        """Player-visible view: own hand + public info only."""
        s = state
        lines = ["player=%d" % player,
                 "phase=%s" % s.phase,
                 "turn_owner=%d turns_to_take=%d next_turns=%d" %
                 (s.turn_owner, s.turns_to_take, s.next_player_turns),
                 "alive=" + ",".join("1" if a else "0" for a in s.alive),
                 "my_hand=" + _hand_str(s.hands[player]),
                 "hand_sizes=" + ",".join(str(len(s.hands[q])) for q in range(s.num_players)),
                 "deck_size=%d" % _deck_size(s),
                 "discard=" + _count_str(s.discard),
                 "nope_count=%d" % s.nope_count]
        if s.phase == "NOPE":
            lines.append("nope_responder=%d" % s.cur)
        if s.last_seen is not None and s.last_seen[0] == player:
            lines.append("seen_top=" + (">".join(s.last_seen[1]) or "-"))
        return "\n".join(lines)

    def observation(self, state, player):
        return self.information_state(state, player)

    # -- action naming (actions are already canonical strings) --------------
    def action_to_name(self, action):
        if not isinstance(action, str):
            raise ValueError("action must be a canonical string")
        return action

    def name_to_action(self, name):
        if not isinstance(name, str):
            raise ValueError("name must be a string")
        return name


if __name__ == "__main__":
    # Minimal smoke test: greedy first-legal / first-chance rollout.
    g = Game(4)
    s = g.initial_state()
    steps = 0
    while not g.is_terminal(s) and steps < 200000:
        acts = g.legal_actions(s)
        if not acts:
            break
        # round-trip check on the chosen action name
        a = g.name_to_action(g.action_to_name(acts[0]))
        s = g.apply_action(s, a)
        steps += 1
    r = g.returns(s)
    assert len(r) == g.num_players
    assert g.legal_actions(s) == [] if g.is_terminal(s) else True
    print("terminal=%s steps=%d winner=%s returns=%s" %
          (g.is_terminal(s), steps, s.winner, r))
