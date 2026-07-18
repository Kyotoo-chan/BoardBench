"""Source-bounded Bohnanza model for the supplied 4--5 player Ackerbohne variant.

The engine is deliberately turn/decision based.  Cards are strings, actions are
immutable tuples, and all randomness is confined to ``initial_state`` and discard
reshuffles.  Opponents' ordered hands are hidden by ``render``.
"""
from dataclasses import dataclass, field
import copy
import json
import random
from typing import Optional


BEANS = {
    "Weinbrandbohne": (22, (4, 7, 9, 11)),
    "Blaue Bohne": (20, (4, 6, 8, 10)),
    "Feuerbohne": (18, (3, 6, 8, 9)),
    "Saubohne": (16, (3, 5, 7, 8)),
    "Brechbohne": (14, (3, 5, 6, 7)),
    "Sojabohne": (12, (2, 4, 6, 7)),
    "Augenbohne": (10, (2, 4, 5, 6)),
    "Rote Bohne": (8, (2, 3, 4, 5)),
    "Gartenbohne": (6, (None, 2, 3, None)),
    "Ackerbohne": (3, (None, None, 3, None)),
}


@dataclass
class TradeDraft:
    partner: int
    offered_hand: list[int] = field(default_factory=list)
    offered_revealed: list[int] = field(default_factory=list)
    requested_hand: list[int] = field(default_factory=list)
    awaiting_consent: bool = False


@dataclass
class GameState:
    players: int
    hands: list[list[str]]
    fields: list[list[list[str]]]
    coins: list[int]
    third_field: list[bool]
    deck: list[str]
    discard: list[str]
    active: int = 0
    decision: int = 0
    phase: str = "phase1"
    phase1_planted: int = 0
    revealed: list[str] = field(default_factory=list)
    sideways: list[list[str]] = field(default_factory=list)
    plant_queue: list[tuple[int, str]] = field(default_factory=list)
    trade: Optional[TradeDraft] = None
    draw_order: list[int] = field(default_factory=list)
    depletion_count: int = 0
    end_after_phase3: bool = False
    terminal: bool = False
    winners: list[int] = field(default_factory=list)


class Game:
    """Complete finite decision model of the supplied source condition."""

    def __init__(self, players: int = 4, seed: Optional[int] = 1):
        if players not in (4, 5):
            raise ValueError("Ackerbohnen-Variante: only 4 or 5 players")
        self.players = players
        self.seed = seed
        self._rng = random.Random(seed)

    def initial_state(self) -> GameState:
        deck = [bean for bean, (count, _) in BEANS.items() for _ in range(count)]
        self._rng.shuffle(deck)
        hands = [[] for _ in range(self.players)]
        # Individually deal five; append order is the immutable hand order.
        for _ in range(5):
            for p in range(self.players):
                hands[p].append(deck.pop())
        return GameState(
            self.players, hands, [[[], []] for _ in range(self.players)],
            [0] * self.players, [False] * self.players, deck, [],
            sideways=[[] for _ in range(self.players)],
        )

    def current_player(self, state: GameState) -> int:
        return state.decision

    @staticmethod
    def _harvestable(state: GameState, p: int, f: int) -> bool:
        if f >= len(state.fields[p]) or not state.fields[p][f]:
            return False
        return not (len(state.fields[p][f]) == 1 and
                    any(len(x) > 1 for x in state.fields[p]))

    @staticmethod
    def _plant_fields(state: GameState, p: int, bean: str) -> list[int]:
        return [i for i, cards in enumerate(state.fields[p])
                if not cards or cards[0] == bean]

    def _harvest_actions(self, state: GameState, p: int) -> list[tuple]:
        return [("Abernten", p, f) for f in range(len(state.fields[p]))
                if self._harvestable(state, p, f)]

    def legal_actions(self, state: GameState) -> list[tuple]:
        if state.terminal:
            return []
        p = state.decision
        harvests = self._harvest_actions(state, p)
        if state.phase == "phase1":
            if not state.hands[p]:
                return [("Phase 2 beginnen",)] + harvests
            bean = state.hands[p][0]
            plants = [("Handkarte anbauen", f) for f in self._plant_fields(state, p, bean)]
            if state.phase1_planted == 0:
                return plants or harvests
            return plants + [("Zweite Handkarte nicht anbauen",)] + harvests
        if state.phase == "phase2_draw":
            return [("Zwei Bohnenkarten aufdecken",)] + harvests
        if state.phase == "phase2_trade":
            if state.trade is None:
                acts = [("Handel beginnen", q) for q in range(state.players) if q != state.active]
                return acts + [("Handelsphase beenden",)] + harvests
            t = state.trade
            if t.awaiting_consent:
                return [("Handel annehmen",), ("Handel ablehnen",)] + harvests
            acts = [("Angebot Handkarte hinzufügen", i) for i in range(len(state.hands[state.active]))
                    if i not in t.offered_hand]
            acts += [("Angebot aufgedeckte Karte hinzufügen", i) for i in range(len(state.revealed))
                     if i not in t.offered_revealed]
            acts += [("Forderung Handkarte hinzufügen", i) for i in range(len(state.hands[t.partner]))
                     if i not in t.requested_hand]
            if t.offered_hand or t.offered_revealed or t.requested_hand:
                acts.append(("Handel vorschlagen",))
            acts.append(("Handel abbrechen",))
            return acts + harvests
        if state.phase == "phase3":
            if not state.plant_queue:
                return [("Phase 3 abschließen",)] + harvests
            owners = sorted({owner for owner, _ in state.plant_queue})
            if p not in owners:
                p = owners[0]
            acts = []
            for i, (owner, bean) in enumerate(state.plant_queue):
                if owner == p:
                    acts += [("Querkarte anbauen", i, f)
                             for f in self._plant_fields(state, p, bean)]
            return acts + self._harvest_actions(state, p)
        if state.phase == "phase4":
            return [("Eine Bohnenkarte nachziehen",)] + harvests
        raise RuntimeError(f"unknown phase {state.phase}")

    def _draw_one(self, s: GameState) -> Optional[str]:
        if not s.deck:
            return None
        card = s.deck.pop()
        if not s.deck:
            s.depletion_count += 1
            if s.depletion_count < 3 and s.discard:
                self._rng.shuffle(s.discard)
                s.deck, s.discard = s.discard, []
        return card

    def _harvest(self, s: GameState, p: int, f: int) -> None:
        cards = s.fields[p][f]
        bean, n = cards[0], len(cards)
        if bean == "Ackerbohne" and n == 2:
            if not s.third_field[p]:
                s.third_field[p] = True
                s.fields[p].append([])
            s.discard.extend(cards)
        else:
            if bean == "Ackerbohne":
                earned = 3 if n >= 3 else 0
            elif bean == "Gartenbohne":
                earned = 3 if n >= 3 else (2 if n >= 2 else 0)
            else:
                earned = sum(x is not None and n >= x for x in BEANS[bean][1])
            s.coins[p] += earned
            s.discard.extend(cards[earned:])
        s.fields[p][f] = []

    def _finish(self, s: GameState) -> None:
        for p in range(s.players):
            for f in range(len(s.fields[p])):
                if s.fields[p][f]:
                    # Final harvest follows ordinary yield; protection is irrelevant
                    # because every field is harvested.
                    cards = s.fields[p][f]
                    bean, n = cards[0], len(cards)
                    if bean == "Ackerbohne": earned = 3 if n >= 3 else 0
                    elif bean == "Gartenbohne": earned = 3 if n >= 3 else (2 if n >= 2 else 0)
                    else: earned = sum(x is not None and n >= x for x in BEANS[bean][1])
                    s.coins[p] += earned
                    s.fields[p][f] = []
        best = max(s.coins)
        tied = [p for p, score in enumerate(s.coins) if score == best]
        # Start player is 0; farther clockwise is the larger seat number.
        s.winners = [max(tied)]
        s.terminal = True
        s.phase = "Spielende"

    def apply_action(self, state: GameState, action: tuple) -> GameState:
        if action not in self.legal_actions(state):
            raise ValueError(f"illegal action: {action}")
        s = copy.deepcopy(state)
        tag = action[0]
        if tag == "Abernten":
            self._harvest(s, action[1], action[2]); return s
        if tag == "Handkarte anbauen":
            bean = s.hands[s.active].pop(0); s.fields[s.active][action[1]].append(bean)
            s.phase1_planted += 1
            if s.phase1_planted == 2 or not s.hands[s.active]: s.phase = "phase2_draw"
        elif tag in ("Zweite Handkarte nicht anbauen", "Phase 2 beginnen"):
            s.phase = "phase2_draw"
        elif tag == "Zwei Bohnenkarten aufdecken":
            for _ in range(2):
                card = self._draw_one(s)
                if card is None: break
                s.revealed.append(card)
                if s.depletion_count >= 3: s.end_after_phase3 = True
            s.phase = "phase2_trade"
        elif tag == "Handel beginnen": s.trade = TradeDraft(action[1])
        elif tag == "Angebot Handkarte hinzufügen": s.trade.offered_hand.append(action[1])
        elif tag == "Angebot aufgedeckte Karte hinzufügen": s.trade.offered_revealed.append(action[1])
        elif tag == "Forderung Handkarte hinzufügen": s.trade.requested_hand.append(action[1])
        elif tag == "Handel vorschlagen":
            s.trade.awaiting_consent = True; s.decision = s.trade.partner
        elif tag == "Handel ablehnen":
            s.trade = None; s.decision = s.active
        elif tag == "Handel annehmen":
            t = s.trade; partner = t.partner
            offered = [s.hands[s.active][i] for i in t.offered_hand] + [s.revealed[i] for i in t.offered_revealed]
            requested = [s.hands[partner][i] for i in t.requested_hand]
            for i in sorted(t.offered_hand, reverse=True): s.hands[s.active].pop(i)
            for i in sorted(t.offered_revealed, reverse=True): s.revealed.pop(i)
            for i in sorted(t.requested_hand, reverse=True): s.hands[partner].pop(i)
            s.sideways[partner].extend(offered); s.sideways[s.active].extend(requested)
            s.trade = None; s.decision = s.active
        elif tag == "Handel abbrechen": s.trade = None
        elif tag == "Handelsphase beenden":
            s.plant_queue = [(p, card) for p, cards in enumerate(s.sideways) for card in cards]
            s.plant_queue += [(s.active, card) for card in s.revealed]
            s.sideways = [[] for _ in range(s.players)]; s.revealed = []; s.trade = None
            s.phase = "phase3"
            s.decision = min((p for p, _ in s.plant_queue), default=s.active)
        elif tag == "Querkarte anbauen":
            owner, bean = s.plant_queue.pop(action[1]); s.fields[owner][action[2]].append(bean)
            owners = sorted({p for p, _ in s.plant_queue})
            s.decision = owners[0] if owners else s.active
        elif tag == "Phase 3 abschließen":
            if s.end_after_phase3: self._finish(s)
            else:
                s.phase = "phase4"; s.draw_order = [(s.active + i) % s.players for i in range(s.players)]
                s.decision = s.draw_order[0]
        elif tag == "Eine Bohnenkarte nachziehen":
            p = s.draw_order.pop(0); card = self._draw_one(s)
            if card is not None: s.hands[p].append(card)
            if s.depletion_count >= 3: self._finish(s)
            elif s.draw_order: s.decision = s.draw_order[0]
            else:
                s.active = (s.active + 1) % s.players; s.decision = s.active
                s.phase = "phase1"; s.phase1_planted = 0
        return s

    def is_terminal(self, state: GameState) -> bool:
        return state.terminal

    def returns(self, state: GameState) -> tuple[int, ...]:
        if not state.terminal: return tuple(0 for _ in range(state.players))
        return tuple(1 if p in state.winners else -1 for p in range(state.players))

    def render(self, state: GameState) -> str:
        view = {
            "phase": state.phase, "active_player": state.active,
            "decision_player": state.decision, "depletions": state.depletion_count,
            "deck_count": len(state.deck), "discard_count": len(state.discard),
            "coins": state.coins, "fields": state.fields,
            "hand": state.hands[state.decision],
            "opponent_hand_counts": [len(h) for i, h in enumerate(state.hands) if i != state.decision],
            "revealed": state.revealed, "sideways": state.sideways,
        }
        return json.dumps(view, ensure_ascii=False, indent=2)

    def action_to_name(self, action: tuple) -> str:
        return json.dumps(action, ensure_ascii=False, separators=(",", ":"))

    def name_to_action(self, name: str) -> tuple:
        value = json.loads(name)
        if not isinstance(value, list): raise ValueError("action name must encode a list")
        return tuple(value)
