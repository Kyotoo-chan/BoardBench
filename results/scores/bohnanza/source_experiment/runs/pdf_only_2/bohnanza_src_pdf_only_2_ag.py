"""Source-bounded implementation of the supplied German Bohnanza rulebook.

The default is the assigned four-player base game.  Five players and the two
four/five-player variants described by the supplied pages are configurable.
"""
from __future__ import annotations

import json
import random


BASE_COUNTS = {
    "Gartenbohne": 6, "Rote Bohne": 8, "Augenbohne": 10,
    "Sojabohne": 12, "Grüne Bohne": 14, "Saubohne": 16,
    "Feuerbohne": 18, "Blaue Bohne": 20,
}
# (minimum cards, talers), read from the printed Bohnometers.
METERS = {
    "Gartenbohne": ((2, 2), (3, 3)),
    "Rote Bohne": ((2, 1), (3, 2), (4, 3), (5, 4)),
    "Augenbohne": ((2, 1), (4, 2), (5, 3), (6, 4)),
    "Sojabohne": ((2, 1), (4, 2), (6, 3), (7, 4)),
    "Grüne Bohne": ((3, 1), (5, 2), (6, 3), (7, 4)),
    "Saubohne": ((3, 1), (5, 2), (7, 3), (8, 4)),
    "Feuerbohne": ((3, 1), (6, 2), (8, 3), (9, 4)),
    "Blaue Bohne": ((4, 1), (6, 2), (8, 3), (10, 4)),
    # Variant meters visible in the supplied material.
    "Ackerbohne": ((3, 3),),
}


class GameState:
    def __init__(self):
        self.hands = []
        self.fields = []
        self.coins = []
        self.deck = []
        self.discard = []
        self.active = 0
        self.start_player = 0
        self.phase = "phase1_first"
        self.revealed = []
        self.received = []
        self.offer_partner = None
        self.offer_active = []
        self.offer_partner_cards = []
        self.pending = []
        self.exhaustions = 0
        self.end_after_phase3 = False
        self.terminal = False
        self.winners = []


class Game:
    """A complete finite state machine for 4 or 5 players.

    ``variant`` may be ``base``, ``three_new`` or ``Ackerbohnen``.  The
    supplied pages omit the component counts/meters for Variante 1 and the
    Weinbrandbohne count/meter for Variante 2, so those configurations reject
    construction rather than inventing cards.  The base condition is complete.
    """

    def __init__(self, num_players=4, seed=1, variant="base"):
        if num_players not in (4, 5):
            raise ValueError("the assigned source condition is 4–5 players")
        if variant not in ("base", "three_new", "Ackerbohnen"):
            raise ValueError("unknown variant")
        self.num_players = num_players
        self.seed = seed
        self.variant = variant

    def initial_state(self):
        if self.variant != "base":
            raise ValueError("supplied pages do not give all variant card counts and Bohnometers")
        s = GameState()
        deck = [bean for bean, count in BASE_COUNTS.items() for _ in range(count)]
        random.Random(self.seed).shuffle(deck)
        s.hands = [[] for _ in range(self.num_players)]
        # Deal individually: the first received remains the visible front.
        for _ in range(5):
            for p in range(self.num_players):
                s.hands[p].append(deck.pop())
        s.deck = deck
        s.fields = [[[] for _ in range(2)] for _ in range(self.num_players)]
        s.coins = [0] * self.num_players
        s.received = [[] for _ in range(self.num_players)]
        return s

    def current_player(self, state):
        if state.terminal:
            return None
        if state.phase == "trade_response":
            return state.offer_partner
        if state.phase == "phase3":
            return state.pending[0][0] if state.pending else state.active
        return state.active

    def is_terminal(self, state):
        return state.terminal

    def _harvest_actions(self, s):
        result = []
        for p, fields in enumerate(s.fields):
            has_multi = any(len(f) > 1 for f in fields)
            for i, field in enumerate(fields):
                if field and not (len(field) == 1 and has_multi):
                    result.append(("harvest", p, i))
        return result

    def _plant_actions(self, s, player, bean, source):
        actions = []
        for i, field in enumerate(s.fields[player]):
            if not field or field[0] == bean:
                actions.append(("plant", player, source, i))
        return actions

    def legal_actions(self, s):
        if s.terminal:
            return []
        actions = self._harvest_actions(s)
        p = s.active
        if s.phase in ("phase1_first", "phase1_second"):
            if not s.hands[p]:
                return actions + [("advance",)]
            actions += self._plant_actions(s, p, s.hands[p][0], "hand")
            if s.phase == "phase1_second":
                actions.append(("advance",))
        elif s.phase == "trade":
            actions.append(("end_trade",))
            for q in range(self.num_players):
                if q != p:
                    actions.append(("start_offer", q))
        elif s.phase == "offer_build":
            actions.append(("cancel_offer",))
            q = s.offer_partner
            used_a = self._used_indices(s.offer_active)
            used_q = self._used_indices(s.offer_partner_cards)
            for i in range(len(s.hands[p])):
                if i not in used_a:
                    actions.append(("offer_active_hand", i))
            for i in range(len(s.revealed)):
                key = 1000 + i
                if key not in used_a:
                    actions.append(("offer_revealed", i))
            for i in range(len(s.hands[q])):
                if i not in used_q:
                    actions.append(("offer_partner_hand", i))
            if s.offer_active or s.offer_partner_cards:
                actions.append(("submit_offer",))
        elif s.phase == "trade_response":
            actions += [("reject_offer",), ("accept_offer",)]
        elif s.phase == "phase3":
            if not s.pending:
                actions.append(("finish_phase3",))
            else:
                owner, bean = s.pending[0]
                actions += self._plant_actions(s, owner, bean, "pending")
        elif s.phase == "phase4":
            actions.append(("draw_phase4",))
        return actions

    @staticmethod
    def _used_indices(entries):
        return {x[0] for x in entries}

    def _draw_one(self, s):
        if not s.deck:
            s.exhaustions += 1
            if s.exhaustions >= 3:
                return None
            s.deck = s.discard
            s.discard = []
            random.Random(self.seed + s.exhaustions).shuffle(s.deck)
        return s.deck.pop() if s.deck else None

    def _coins_for(self, bean, count):
        value = 0
        for minimum, coins in METERS[bean]:
            if count >= minimum:
                value = coins
        return value

    def _harvest(self, s, p, i):
        field = s.fields[p][i]
        earned = self._coins_for(field[0], len(field))
        s.coins[p] += earned
        s.discard.extend(field[earned:])
        s.fields[p][i] = []

    def _begin_trade(self, s):
        s.revealed = []
        for _ in range(2):
            card = self._draw_one(s)
            if card is None:
                s.end_after_phase3 = True
                break
            s.revealed.append(card)
        s.phase = "trade"

    def apply_action(self, s, action):
        if action not in self.legal_actions(s):
            raise ValueError("illegal action")
        kind = action[0]
        if kind == "harvest":
            self._harvest(s, action[1], action[2])
            return s
        if kind == "advance":
            self._begin_trade(s)
        elif kind == "plant":
            p, source, field = action[1:]
            if source == "hand":
                bean = s.hands[p].pop(0)
                s.fields[p][field].append(bean)
                s.phase = "phase1_second" if s.phase == "phase1_first" else "trade"
                if s.phase == "trade":
                    self._begin_trade(s)
            else:
                owner, bean = s.pending.pop(0)
                assert owner == p
                s.fields[p][field].append(bean)
        elif kind == "start_offer":
            s.offer_partner = action[1]
            s.offer_active, s.offer_partner_cards = [], []
            s.phase = "offer_build"
        elif kind == "offer_active_hand":
            s.offer_active.append((action[1], "hand"))
        elif kind == "offer_revealed":
            s.offer_active.append((1000 + action[1], "revealed"))
        elif kind == "offer_partner_hand":
            s.offer_partner_cards.append((action[1], "hand"))
        elif kind == "cancel_offer" or kind == "reject_offer":
            s.offer_partner = None
            s.offer_active, s.offer_partner_cards = [], []
            s.phase = "trade"
        elif kind == "submit_offer":
            s.phase = "trade_response"
        elif kind == "accept_offer":
            q = s.offer_partner
            # Remove descending so original indices remain valid.
            to_q, to_a = [], []
            for idx, source in sorted(s.offer_active, reverse=True):
                to_q.append(s.hands[s.active].pop(idx) if source == "hand" else s.revealed.pop(idx - 1000))
            for idx, _ in sorted(s.offer_partner_cards, reverse=True):
                to_a.append(s.hands[q].pop(idx))
            s.received[q].extend(to_q)
            s.received[s.active].extend(to_a)
            s.offer_partner = None
            s.offer_active, s.offer_partner_cards = [], []
            s.phase = "trade"
        elif kind == "end_trade":
            s.pending = []
            for q in range(self.num_players):
                s.pending.extend((q, b) for b in s.received[q])
                s.received[q] = []
            s.pending.extend((s.active, b) for b in s.revealed)
            s.revealed = []
            s.phase = "phase3"
        elif kind == "finish_phase3":
            if s.end_after_phase3:
                self._finish(s)
            else:
                s.phase = "phase4"
        elif kind == "draw_phase4":
            for _ in range(3):
                card = self._draw_one(s)
                if card is None:
                    break
                s.hands[s.active].append(card)
            if s.exhaustions >= 3:
                self._finish(s)
            else:
                s.active = (s.active + 1) % self.num_players
                s.phase = "phase1_first"
        return s

    def _finish(self, s):
        for p in range(self.num_players):
            for i in range(len(s.fields[p])):
                if s.fields[p][i]:
                    self._harvest(s, p, i)
        best = max(s.coins)
        tied = [p for p, score in enumerate(s.coins) if score == best]
        # Clockwise farthest from start player wins the tie.
        s.winners = [max(tied, key=lambda p: (p - s.start_player) % self.num_players)]
        s.terminal = True
        s.phase = "terminal"

    def returns(self, s):
        if not s.terminal:
            return [0] * self.num_players
        return [1 if p in s.winners else 0 for p in range(self.num_players)]

    def render(self, s):
        return json.dumps({
            "active": s.active, "phase": s.phase, "hands": s.hands,
            "fields": s.fields, "coins": s.coins,
            "revealed": s.revealed, "pending": s.pending,
            "deck_count": len(s.deck), "discard_count": len(s.discard),
            "exhaustions": s.exhaustions, "winners": s.winners,
        }, ensure_ascii=False, sort_keys=True)

    def action_to_name(self, action):
        labels = {
            "harvest": "Bohnenernte", "advance": "Weiter zu Phase 2",
            "plant": "Bohnenkarte anbauen", "end_trade": "Handel beenden",
            "start_offer": "Handel beginnen", "offer_active_hand": "Handkarte anbieten",
            "offer_revealed": "Aufgedeckte Karte anbieten",
            "offer_partner_hand": "Handkarte des Mitspielers erbitten",
            "cancel_offer": "Angebot abbrechen", "submit_offer": "Angebot vorlegen",
            "reject_offer": "Handel ablehnen", "accept_offer": "Handel zustimmen",
            "finish_phase3": "Phase 3 beenden", "draw_phase4": "Bohnenkarten nachziehen",
        }
        return labels[action[0]] + " :: " + json.dumps(action, ensure_ascii=False, separators=(",", ":"))

    def name_to_action(self, name):
        try:
            return tuple(json.loads(name.split(" :: ", 1)[1]))
        except (ValueError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise ValueError("invalid action name") from exc
