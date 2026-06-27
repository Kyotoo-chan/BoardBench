"""Exploding Kittens (NSFW Edition) -- self-contained OpenSpiel-style engine.

Source of truth: the provided rulebook text/pages only. Standard library only.

WHAT THE RULEBOOK SAYS (and how it is modelled here)
----------------------------------------------------
Players 2-5, 56 cards. Card counts (from the "Schlachtplan" card reference and
the "beispielzug" tally):
    Exploding Kitten 4, Entschaerfung/Defuse 6, Noe!/Nope 5, Angriff/Attack 4,
    Hops!/Skip 4, Wunsch/Favor 4, Mischen/Shuffle 4, Blick in die Zukunft/
    See-the-Future 5, Katzen-Karten/Cat cards 5 kinds x 4 = 20.   (sum = 56)

Setup (Spielaufbau): set aside all 4 EK and all 6 Defuse. Shuffle the rest (46
cards) and deal 7 face down to each player. Give each player 1 Defuse -> 8 cards.
Shuffle (#players - 1) Exploding Kittens into the draw pile. Shuffle the
remaining Defuse cards into the draw pile ("alle uebrigen"). For the explicit
2-player variant box: shuffle only 2 Defuse into the pile, rest to the box.
    => Defuse in draw pile: n==2 -> 2, otherwise 6-n. EK in pile: n-1.

Turn (Spielzug): "Passen oder spielen, dann ziehen." You may play any number of
cards (each face up to the discard, following its instruction) and you END your
turn by drawing the top card. Passing = drawing without playing. Drawing an
Exploding Kitten kills you unless you play a Defuse. Play proceeds clockwise.

Cards:
  See-the-Future: look at the top 3 cards (private), keep their order.
  Attack: end your turn without drawing; the NEXT player must take two turns.
          If that victim plays Attack, they take none and the next player takes
          two (base behaviour: it does not accumulate to four).
  Skip: end your turn immediately without drawing. Against an Attack it only
        ends ONE of the two turns.
  Nope: cancel another played card/combo and its effect (NOT EK, NOT Defuse).
        Playable out of turn. A Nope on a Nope ("Doch!") re-enables the card.
  Shuffle: shuffle the draw pile.
  Favor: choose a player; THEY choose a card to give you.
  Defuse: when you draw an EK, play it instead of dying and secretly reinsert
          the EK anywhere in the draw pile.
  Combos (Kombinationen) -- card instructions do NOT apply when comboed:
    Pair  (2 same title): steal a RANDOM card from a chosen player.
    Triple(3 same title): name a card; if the target has it they must give it.
    Five  (5 different titles): take any one card from the discard pile.

Win (Spielende): the last player who has not exploded wins.

KEY MODELLING DECISIONS / ASSUMPTIONS  (see "Open questions / assumptions")
---------------------------------------------------------------------------
* num_players is a constructor argument (2..5, default 4). Default start player
  is seat 0 (the rulebook lets players pick one arbitrarily).
* All randomness is expressed as explicit CHANCE nodes (no hidden RNG): dealing
  hands, ordering the draw pile, re-ordering on Shuffle, and the random steal of
  a Pair. The draw pile is kept as a concrete ordered list (the hidden truth) so
  that See-the-Future, Shuffle and Defuse-reinsertion are meaningful; drawing is
  then a deterministic pop of the known top.  render() prints this truth and is
  therefore a debug view, NOT what a player can see -- use information_state().
* The five cat-card titles are not all spelled out in the rulebook, so they are
  labelled cat_a..cat_e. Only "same title" / "different title" matters.
* Nope timing: after a nope-able card/combo is played a reaction window opens.
  Eligible opponents (alive, holding a Nope) are polled clockwise; a Nope flips
  the pending parity and reopens the window (so Nopes can be countered). When a
  full pass happens the action resolves iff an even number of Nopes were played.
  This terminates because every Nope discards a card (<=5 in play).
* Actions are canonical strings (they ARE their own names); action_to_name /
  name_to_action are the identity, so they round-trip exactly.
* returns(): +1 for the surviving winner, -1 for every eliminated player.
"""

import copy
from itertools import combinations

# ---- sentinels -------------------------------------------------------------
TERMINAL = -1
CHANCE = -2

# ---- cards -----------------------------------------------------------------
CARD_TYPES = [
    'exploding_kitten', 'defuse', 'nope', 'attack', 'skip', 'favor',
    'shuffle', 'see_future', 'cat_a', 'cat_b', 'cat_c', 'cat_d', 'cat_e',
]
CARD_ORDER = {c: i for i, c in enumerate(CARD_TYPES)}
CAT_TYPES = ['cat_a', 'cat_b', 'cat_c', 'cat_d', 'cat_e']
WANTED_TYPES = [c for c in CARD_TYPES if c != 'exploding_kitten']
SINGLE_EFFECT = ['skip', 'attack', 'shuffle', 'see_future']  # playable alone (favor needs a target)

# non-EK, non-Defuse pool that is dealt / forms most of the draw pile (46 cards)
INITIAL_POOL = {
    'nope': 5, 'attack': 4, 'skip': 4, 'favor': 4, 'shuffle': 4,
    'see_future': 5, 'cat_a': 4, 'cat_b': 4, 'cat_c': 4, 'cat_d': 4, 'cat_e': 4,
}

# ---- phases ----------------------------------------------------------------
PH_DEAL = 'DEAL'        # chance: deal hands
PH_BUILD = 'BUILD'      # chance: order the draw pile (setup) or re-order (shuffle)
PH_PLAY = 'PLAY'        # the active player's decision
PH_NOPE = 'NOPE'        # a reaction window
PH_FAVOR = 'FAVOR'      # the favor target chooses a card to give
PH_DEFUSE = 'DEFUSE'    # the player who drew an EK chooses where to reinsert it
PH_STEAL = 'STEAL'      # chance: random card stolen by a Pair
PH_DONE = 'DONE'        # terminal


def _counts(cards):
    d = {}
    for c in cards:
        d[c] = d.get(c, 0) + 1
    return d


def _comp_keys(comp):
    return [c for c in CARD_TYPES if comp.get(c, 0) > 0]


def _fmt_counts(cards):
    d = _counts(cards)
    out = ', '.join('%s x%d' % (c, d[c]) for c in CARD_TYPES if d.get(c, 0) > 0)
    return out or '(empty)'


class GameState:
    """Full (hidden) truth of one game. Treated as a value object; apply_action
    returns a fresh clone and never mutates the input state."""

    __slots__ = (
        'n', 'phase', 'hands', 'deck', 'discard', 'alive', 'current',
        'turns_remaining', 'pending', 'peeks', 'pool', 'build_pool',
        'build_mode', 'build_actor', 'to_deal', 'start_player',
    )

    def __init__(self, n):
        self.n = n
        self.phase = PH_DEAL
        self.hands = [[] for _ in range(n)]     # concrete cards per seat (hidden)
        self.deck = []                          # index 0 == top of draw pile (hidden)
        self.discard = []                       # face up, public
        self.alive = [True] * n
        self.current = 0                        # active seat in PLAY/DEFUSE
        self.turns_remaining = 1                # turn-instances the active seat must finish
        self.pending = None                     # dict describing an in-flight action
        self.peeks = {}                         # seat -> tuple(top cards) from See-the-Future
        self.pool = dict(INITIAL_POOL)          # remaining undealt pool during DEAL
        self.build_pool = {}                    # composition still to be ordered during BUILD
        self.build_mode = None                  # 'setup' | 'shuffle'
        self.build_actor = 0                    # who resumes after a Shuffle build
        self.to_deal = 7 * n                    # cards still to deal during DEAL
        self.start_player = 0

    def clone(self):
        return copy.deepcopy(self)


class Game:
    def __init__(self, num_players=4):
        if not (2 <= num_players <= 5):
            raise ValueError('Exploding Kittens supports 2..5 players')
        self.num_players = num_players

    # ---- core API ----------------------------------------------------------
    def initial_state(self):
        return GameState(self.num_players)

    def current_player(self, s):
        if s.phase == PH_DONE:
            return TERMINAL
        if s.phase in (PH_DEAL, PH_BUILD, PH_STEAL):
            return CHANCE
        if s.phase == PH_NOPE:
            return s.pending['reactor']
        if s.phase == PH_FAVOR:
            return s.pending['target']
        return s.current  # PLAY, DEFUSE

    def is_terminal(self, s):
        return s.phase == PH_DONE

    def returns(self, s):
        if s.phase != PH_DONE:
            return [0.0] * s.n
        return [1.0 if s.alive[i] else -1.0 for i in range(s.n)]

    def legal_actions(self, s):
        ph = s.phase
        if ph == PH_DONE:
            return []
        if ph == PH_DEAL:
            return ['chance:deal:%s' % c for c in _comp_keys(s.pool)]
        if ph == PH_BUILD:
            return ['chance:order:%s' % c for c in _comp_keys(s.build_pool)]
        if ph == PH_STEAL:
            t = s.pending['target']
            return ['chance:steal:%s' % c for c in _comp_keys(_counts(s.hands[t]))]
        if ph == PH_NOPE:
            return ['nope', 'pass']
        if ph == PH_FAVOR:
            t = s.pending['target']
            return ['give:%s' % c for c in _comp_keys(_counts(s.hands[t]))]
        if ph == PH_DEFUSE:
            return ['insert_ek:%d' % i for i in range(len(s.deck) + 1)]
        if ph == PH_PLAY:
            return self._play_actions(s)
        return []

    def chance_outcomes(self, s):
        ph = s.phase
        if ph == PH_DEAL:
            comp, tot = s.pool, sum(s.pool.values())
            return [('chance:deal:%s' % c, comp[c] / tot) for c in _comp_keys(comp)]
        if ph == PH_BUILD:
            comp, tot = s.build_pool, sum(s.build_pool.values())
            return [('chance:order:%s' % c, comp[c] / tot) for c in _comp_keys(comp)]
        if ph == PH_STEAL:
            t = s.pending['target']
            comp = _counts(s.hands[t])
            tot = sum(comp.values())
            return [('chance:steal:%s' % c, comp[c] / tot) for c in _comp_keys(comp)]
        return []

    def apply_action(self, state, action):
        if state.phase == PH_DONE:
            raise ValueError('no actions in a terminal state')
        s = state.clone()
        ph = s.phase
        if ph == PH_DEAL:
            self._apply_deal(s, action)
        elif ph == PH_BUILD:
            self._apply_build(s, action)
        elif ph == PH_STEAL:
            self._apply_steal(s, action)
        elif ph == PH_NOPE:
            self._apply_nope(s, action)
        elif ph == PH_FAVOR:
            self._apply_favor(s, action)
        elif ph == PH_DEFUSE:
            self._apply_defuse(s, action)
        elif ph == PH_PLAY:
            self._apply_play(s, action)
        else:
            raise ValueError('unknown phase %r' % ph)
        return s

    def action_to_name(self, action):
        if not isinstance(action, str):
            raise ValueError('action must be a canonical name string')
        return action

    def name_to_action(self, name):
        if not isinstance(name, str):
            raise ValueError('name must be a string')
        return name

    # ---- rendering / views -------------------------------------------------
    def render(self, s):
        cp = self.current_player(s)
        cstr = 'TERMINAL' if cp == TERMINAL else ('CHANCE' if cp == CHANCE else 'P%d' % cp)
        lines = ['=== Exploding Kittens (players=%d) ===' % s.n,
                 'phase=%s current=%s turns_remaining=%d' % (s.phase, cstr, s.turns_remaining),
                 'alive=%s' % (' '.join('P%d' % i for i in range(s.n) if s.alive[i]) or '(none)')]
        for p in range(s.n):
            tag = 'alive' if s.alive[p] else 'dead'
            lines.append('  P%d[%s] hand: %s' % (p, tag, _fmt_counts(s.hands[p])))
        lines.append('deck(top->bottom)[%d]: %s' % (len(s.deck), ','.join(s.deck) if s.deck else '(empty)'))
        lines.append('discard[%d]: %s' % (len(s.discard), _fmt_counts(s.discard)))
        if s.pending:
            lines.append('pending: kind=%s actor=%s target=%s nopes=%s' % (
                s.pending.get('kind'), s.pending.get('actor'),
                s.pending.get('target'), s.pending.get('nopes')))
        if cp == TERMINAL:
            lines.append('returns=%s' % self.returns(s))
        return '\n'.join(lines)

    def information_state(self, s, player):
        """Player-visible view. Never reveals other hands or the draw-pile order;
        deck size, discard pile and per-player hand sizes are public per the
        rulebook ('Du darfst die Anzahl der uebrigen Karten jederzeit nachzaehlen')."""
        cp = self.current_player(s)
        cstr = 'TERMINAL' if cp == TERMINAL else ('CHANCE' if cp == CHANCE else 'P%d' % cp)
        L = ['view_of=P%d phase=%s current=%s turns_remaining=%d' % (player, s.phase, cstr, s.turns_remaining),
             'alive=%s' % (' '.join('P%d' % i for i in range(s.n) if s.alive[i]) or '(none)'),
             'your_hand: %s' % _fmt_counts(s.hands[player])]
        if s.peeks.get(player):
            L.append('you_peeked_top: %s' % ','.join(s.peeks[player]))
        L.append('hand_sizes: %s' % ' '.join('P%d:%d' % (i, len(s.hands[i])) for i in range(s.n)))
        L.append('deck_size=%d' % len(s.deck))
        L.append('discard: %s' % _fmt_counts(s.discard))
        if s.phase == PH_NOPE and s.pending:
            L.append('on_table: %s by P%s (nopes=%d)%s' % (
                s.pending.get('kind'), s.pending.get('actor'), s.pending.get('nopes'),
                ' you_may_nope' if cp == player else ''))
        return '\n'.join(L)

    # ---- PLAY-phase action enumeration ------------------------------------
    def _play_actions(self, s):
        me = s.current
        cnt = _counts(s.hands[me])
        acts = ['draw']
        others = [k for k in range(s.n) if k != me and s.alive[k]]
        others_with_cards = [k for k in others if s.hands[k]]
        for c in SINGLE_EFFECT:
            if cnt.get(c, 0) >= 1:
                acts.append('play:%s' % c)
        if cnt.get('favor', 0) >= 1:
            for k in others_with_cards:
                acts.append('play:favor->P%d' % k)
        for t in CARD_TYPES:
            if cnt.get(t, 0) >= 2:
                for k in others_with_cards:
                    acts.append('pair:%s->P%d' % (t, k))
        for t in CARD_TYPES:
            if cnt.get(t, 0) >= 3:
                for k in others:
                    for w in WANTED_TYPES:
                        acts.append('triple:%s:%s->P%d' % (t, w, k))
        distinct = [t for t in CARD_TYPES if cnt.get(t, 0) >= 1]
        if len(distinct) >= 5 and s.discard:
            dtypes = [d for d in CARD_TYPES if d in set(s.discard)]
            for combo in combinations(distinct, 5):
                key = '-'.join(combo)
                for w in dtypes:
                    acts.append('five:%s:%s' % (key, w))
        return acts

    # ---- chance / setup transitions ---------------------------------------
    def _apply_deal(self, s, action):
        parts = action.split(':')
        if len(parts) != 3 or parts[0] != 'chance' or parts[1] != 'deal':
            raise ValueError('bad deal action %r' % action)
        card = parts[2]
        if s.pool.get(card, 0) <= 0:
            raise ValueError('illegal deal %r' % action)
        recipient = (7 * s.n - s.to_deal) // 7
        s.hands[recipient].append(card)
        s.pool[card] -= 1
        s.to_deal -= 1
        if s.to_deal == 0:
            for p in range(s.n):
                s.hands[p].append('defuse')
            bp = {k: v for k, v in s.pool.items() if v > 0}
            bp['exploding_kitten'] = s.n - 1
            dd = 2 if s.n == 2 else 6 - s.n
            if dd > 0:
                bp['defuse'] = bp.get('defuse', 0) + dd
            s.build_pool = bp
            s.build_mode = 'setup'
            s.deck = []
            s.phase = PH_BUILD

    def _apply_build(self, s, action):
        parts = action.split(':')
        if len(parts) != 3 or parts[0] != 'chance' or parts[1] != 'order':
            raise ValueError('bad order action %r' % action)
        card = parts[2]
        if s.build_pool.get(card, 0) <= 0:
            raise ValueError('illegal order %r' % action)
        s.deck.append(card)               # first ordered card becomes the top (index 0)
        s.build_pool[card] -= 1
        if sum(s.build_pool.values()) == 0:
            self._finish_build(s)

    def _finish_build(self, s):
        s.peeks = {}
        if s.build_mode == 'setup':
            s.phase = PH_PLAY
            s.current = s.start_player
            s.turns_remaining = 1
        else:  # shuffle
            s.phase = PH_PLAY
            s.current = s.build_actor
        s.build_mode = None
        s.build_pool = {}

    def _apply_steal(self, s, action):
        parts = action.split(':')
        if len(parts) != 3 or parts[1] != 'steal':
            raise ValueError('bad steal action %r' % action)
        card = parts[2]
        t, actor = s.pending['target'], s.pending['actor']
        if card not in s.hands[t]:
            raise ValueError('illegal steal %r' % action)
        s.hands[t].remove(card)
        s.hands[actor].append(card)
        s.pending = None
        s.phase = PH_PLAY
        s.current = actor

    # ---- reaction window ---------------------------------------------------
    def _open_nope(self, s, start_after, protected):
        q = []
        for d in range(1, s.n):
            c = (start_after + d) % s.n
            if s.alive[c] and c != protected and 'nope' in s.hands[c]:
                q.append(c)
        if not q:
            self._resolve_pending(s)
        else:
            s.pending['queue'] = q
            s.pending['reactor'] = q[0]
            s.phase = PH_NOPE

    def _apply_nope(self, s, action):
        if action not in ('nope', 'pass'):
            raise ValueError('bad reaction %r' % action)
        p = s.pending
        if action == 'pass':
            p['queue'].pop(0)
            if p['queue']:
                p['reactor'] = p['queue'][0]
            else:
                self._resolve_pending(s)
        else:
            r = p['reactor']
            if 'nope' not in s.hands[r]:
                raise ValueError('reactor has no nope')
            s.hands[r].remove('nope')
            s.discard.append('nope')
            p['nopes'] += 1
            p['protected'] = r
            self._open_nope(s, r, r)

    def _resolve_pending(self, s):
        p = s.pending
        kind, actor = p['kind'], p['actor']
        if p['nopes'] % 2 == 1:           # odd number of Nopes -> the action fizzles
            s.pending = None
            s.phase = PH_PLAY
            s.current = actor
            return
        s.pending = None
        if kind == 'skip':
            s.current = actor
            self._complete_instance(s)
        elif kind == 'attack':
            s.current = self._next_alive(s, actor)
            s.turns_remaining = 2
            s.phase = PH_PLAY
        elif kind == 'shuffle':
            self._start_shuffle(s, actor)
        elif kind == 'see_future':
            s.peeks[actor] = tuple(s.deck[:3])
            s.current = actor
            s.phase = PH_PLAY
        elif kind == 'favor':
            t = p['target']
            if s.hands[t]:
                s.pending = {'kind': 'favor', 'actor': actor, 'target': t}
                s.phase = PH_FAVOR
            else:
                s.current = actor
                s.phase = PH_PLAY
        elif kind == 'pair':
            t = p['target']
            if s.hands[t]:
                s.pending = {'kind': 'pair', 'actor': actor, 'target': t}
                s.phase = PH_STEAL
            else:
                s.current = actor
                s.phase = PH_PLAY
        elif kind == 'triple':
            t, w = p['target'], p['wanted']
            if w in s.hands[t]:
                s.hands[t].remove(w)
                s.hands[actor].append(w)
            s.current = actor
            s.phase = PH_PLAY
        elif kind == 'five':
            w = p['wanted']
            if w in s.discard:
                s.discard.remove(w)
                s.hands[actor].append(w)
            s.current = actor
            s.phase = PH_PLAY
        else:
            s.current = actor
            s.phase = PH_PLAY

    def _start_shuffle(self, s, actor):
        pool = {}
        for c in s.deck:
            pool[c] = pool.get(c, 0) + 1
        s.build_pool = pool
        s.deck = []
        s.build_mode = 'shuffle'
        s.build_actor = actor
        s.pending = None
        s.phase = PH_BUILD

    # ---- favor / defuse ----------------------------------------------------
    def _apply_favor(self, s, action):
        parts = action.split(':', 1)
        if parts[0] != 'give' or len(parts) != 2:
            raise ValueError('bad give %r' % action)
        card = parts[1]
        t, actor = s.pending['target'], s.pending['actor']
        if card not in s.hands[t]:
            raise ValueError('illegal give %r' % action)
        s.hands[t].remove(card)
        s.hands[actor].append(card)
        s.pending = None
        s.phase = PH_PLAY
        s.current = actor

    def _apply_defuse(self, s, action):
        parts = action.split(':')
        if parts[0] != 'insert_ek' or len(parts) != 2:
            raise ValueError('bad defuse %r' % action)
        i = int(parts[1])
        if not (0 <= i <= len(s.deck)):
            raise ValueError('bad insert index %d' % i)
        s.deck.insert(i, 'exploding_kitten')
        s.peeks = {}
        s.pending = None
        s.phase = PH_PLAY
        self._complete_instance(s)        # the draw is what ends the turn

    # ---- main play ---------------------------------------------------------
    def _apply_play(self, s, action):
        me = s.current
        cnt = _counts(s.hands[me])
        if action == 'draw':
            self._resolve_draw(s)
            return
        if action.startswith('play:'):
            rest = action[5:]
            if rest in SINGLE_EFFECT:
                if cnt.get(rest, 0) < 1:
                    raise ValueError('no %s in hand' % rest)
                self._start_action(s, rest, [rest], {})
                return
            if rest.startswith('favor->P'):
                k = int(rest[len('favor->P'):])
                if cnt.get('favor', 0) < 1 or not (0 <= k < s.n) or k == me \
                        or not s.alive[k] or not s.hands[k]:
                    raise ValueError('illegal favor %r' % action)
                self._start_action(s, 'favor', ['favor'], {'target': k})
                return
            raise ValueError('bad play %r' % action)
        if action.startswith('pair:'):
            t, kp = action[5:].split('->P')
            k = int(kp)
            if cnt.get(t, 0) < 2 or not (0 <= k < s.n) or k == me \
                    or not s.alive[k] or not s.hands[k]:
                raise ValueError('illegal pair %r' % action)
            self._start_action(s, 'pair', [t, t], {'target': k})
            return
        if action.startswith('triple:'):
            left, kp = action[7:].split('->P')
            k = int(kp)
            t, w = left.split(':')
            if cnt.get(t, 0) < 3 or w not in WANTED_TYPES or not (0 <= k < s.n) \
                    or k == me or not s.alive[k]:
                raise ValueError('illegal triple %r' % action)
            self._start_action(s, 'triple', [t, t, t], {'target': k, 'wanted': w})
            return
        if action.startswith('five:'):
            key, w = action[5:].rsplit(':', 1)
            titles = key.split('-')
            if len(titles) != 5 or len(set(titles)) != 5 \
                    or any(cnt.get(t, 0) < 1 for t in titles) or w not in set(s.discard):
                raise ValueError('illegal five %r' % action)
            self._start_action(s, 'five', list(titles), {'wanted': w})
            return
        raise ValueError('unknown action %r' % action)

    def _start_action(self, s, kind, cards, params):
        me = s.current
        for c in cards:
            s.hands[me].remove(c)
        s.discard.extend(cards)
        s.pending = {'kind': kind, 'actor': me, 'nopes': 0, 'protected': me}
        s.pending.update(params)
        self._open_nope(s, me, me)

    def _resolve_draw(self, s):
        me = s.current
        if not s.deck:                    # per rulebook the pile never empties; guard anyway
            self._complete_instance(s)
            return
        card = s.deck.pop(0)
        s.peeks = {}
        if card == 'exploding_kitten':
            if 'defuse' in s.hands[me]:
                s.hands[me].remove('defuse')
                s.discard.append('defuse')
                s.pending = None
                s.phase = PH_DEFUSE
            else:
                self._explode(s, me)
        else:
            s.hands[me].append(card)
            self._complete_instance(s)

    def _explode(self, s, me):
        s.discard.extend(s.hands[me])
        s.hands[me] = []
        s.discard.append('exploding_kitten')
        s.alive[me] = False
        s.pending = None
        if sum(s.alive) == 1:
            s.phase = PH_DONE
            return
        s.current = self._next_alive(s, me)
        s.turns_remaining = 1
        s.phase = PH_PLAY

    def _complete_instance(self, s):
        s.turns_remaining -= 1
        if s.turns_remaining <= 0:
            s.current = self._next_alive(s, s.current)
            s.turns_remaining = 1
        s.phase = PH_PLAY

    def _next_alive(self, s, seat):
        for d in range(1, s.n + 1):
            c = (seat + d) % s.n
            if s.alive[c]:
                return c
        return seat


if __name__ == '__main__':
    g = Game(4)
    st = g.initial_state()
    print(g.render(st))
    print('initial current_player:', g.current_player(st), '(CHANCE=%d)' % CHANCE)
    print('chance outcomes:', g.chance_outcomes(st)[:3], '...')
