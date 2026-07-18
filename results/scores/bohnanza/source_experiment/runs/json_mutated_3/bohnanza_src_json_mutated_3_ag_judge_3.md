## 1. Score

**score: 0.29 — confidence: high**

The implementation captures much of the ordinary base-game planting and harvesting logic, including hand order, normal Bohnometers, singleton protection, consensual one-card trades, final harvest calculation, and tie-breaking. However, it implements the wrong game condition: an eight-type, 104-card base deck instead of the approved 129-card Ackerbohne variant. It also materially mishandles depletion timing, variant drawing, trade possibilities, and out-of-turn harvesting.

## 2. Findings

### Critical — C1: The selected Ackerbohne condition is not implemented

- Canonical facts: `INV-03`, `INV-04`, `ACKER-01`, `ACKER-03`
- Evidence:
  - Evidence type: `rule_quote`
  - Source: `RULES`, PDF page 10
  - Exact evidence: “alle Bohnensorten aus dem Grundspiel sowie die Ackerbohnen und die Weinbrandbohnen”
  - Evidence type: `user_observation`
  - Source: `COMPONENTS`
  - JSON Pointers: `/bohnen/9/anzahl_karten`, `/bohnen/11/anzahl_karten`
  - Exact evidence: Weinbrandbohne `"anzahl_karten": 22`; Ackerbohne `"anzahl_karten": 3`
  - Evidence type: `rule_quote`
  - Source: `RULES`, PDF page 11
  - Exact evidence: “Feld mit zwei Ackerbohnen, erhältst du ein drittes Bohnenfeld.”
  - Evidence type: `rule_quote`
  - Source: `RULES`, PDF page 11
  - Exact evidence: “drei Ackerbohnen … drei Bohnentaler”
- Conflicting code: `BEANS`, `METER`, `Game.initial_state()`, and the fixed two-field representation in `GameState.fields`.
- Expected: Eight base types plus 22 Weinbrandbohnen and three Ackerbohnen, totaling 129 cards. Two Ackerbohnen can unlock a persistent third field; three produce three coins.
- Implemented: Only the eight base types and 104 cards exist. Every player permanently has exactly two fields. Weinbrandbohne, Ackerbohne, their rewards, and third-field planting are absent.
- Impact: This is fundamentally a different game condition and changes setup, chance distribution, legal planting choices, harvesting, scoring, and likely winners.

### Critical — C2: Depletion is recognized one draw attempt too late

- Canonical facts: `DECK-01`, `END-01`, `END-05`
- Evidence:
  - Evidence type: `human_decision`
  - Source: `RULES`, PDF page 9
  - Exact evidence: “Ziehst du die letzte Karte … mische die Karten des Ablagestapels.”
  - Approved expectation: On first or second depletion, reshuffle immediately and continue any owed draw.
  - Evidence type: `rule_quote`
  - Source: `RULES`, PDF page 9
  - Exact evidence: “endet, sobald der Nachziehstapel zum dritten Mal leer wird”
  - Evidence type: `human_decision`
  - Source: `RULES`, PDF page 9
  - Exact evidence: “endet, sobald”
  - Approved expectation: A phase-four third depletion is immediately terminal after the draw that empties the pile.
- Conflicting code: `Game._draw_one()`, specifically checking `if not deck` only before `deck.pop()`.
- Expected: Drawing the last card immediately records depletion. First/second depletion immediately reshuffles the then-current discard; third depletion triggers the appropriate phase-specific ending boundary.
- Implemented: A last card may be popped without incrementing `empty_count`. Depletion is recorded only when a later draw is attempted.
- Impact:
  - Cards discarded or harvested after the true depletion can incorrectly enter the delayed reshuffle.
  - A third depletion on the final owed draw can permit additional planting/trading before the next draw attempt notices the end.
  - This can alter future card order, available actions, final harvests, and the winner.

### Major — M1: Phase four uses the base-game draw-three rule

- Canonical fact: `P4-01`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 10
- Exact evidence: “zieht jeder von euch eine Karte … aktive Spieler … im Uhrzeigersinn”
- Conflicting code: phase `"draw_three"` and the three-iteration loop in `Game.apply_action()`.
- Expected: Every player draws exactly one card, beginning with the active player and continuing clockwise; every card appends to its recipient’s hand.
- Implemented: Only the active player draws, and that player draws three consecutive cards.
- Impact: Materially wrong chance allocation and private-hand evolution on every turn.

### Major — M2: Material legal trades and gifts cannot be represented

- Canonical facts: `TRADE-02`, `TRADE-04`, `TRADE-07`
- Evidence:
  - Evidence type: `rule_quote`
  - Source: `RULES`, PDF page 5
  - Exact evidence: “mit euren Handkarten handeln … wo sich die Karten auf der Hand befinden”
  - Evidence type: `rule_quote`
  - Source: `RULES`, PDF page 5
  - Exact evidence: “unterschiedlichen Kartenanzahl handeln”
  - Evidence type: `rule_quote`
  - Source: `RULES`, PDF page 6
  - Exact evidence: “Bohnenkarten schenken … muss … zustimmen”
- Conflicting code: `Game.legal_actions()`, `proposal`, `_remove_active_card()`, and `_accept()`.
- Expected: Consensual exchanges may have unequal multi-card quantities; a nonempty consensual gift involving the active player is legal. The active player may choose a particular hand position or a revealed card without changing the order of remaining hand cards.
- Implemented:
  - Exchanges are limited to exactly one card for one card.
  - Gifts are limited to one card from the active player to another player.
  - There is no multi-card offer or a gift from an inactive player to the active player.
  - Cards are identified only by bean name. If the active player has the same type both revealed and in hand, `_remove_active_card()` always removes the revealed copy. Multiple identical cards at different hand positions also cannot be distinguished.
- Impact: Common materially distinct negotiations are absent, and source conflation can change which revealed cards remain mandatory and what ordered hand remains.

### Major — M3: Owners cannot harvest between steps during another player’s turn

- Canonical fact: `HARV-01`
- Evidence type: `human_decision`
- Source: `RULES`, PDF page 7
- Exact evidence: “jederzeit … auch wenn du nicht der aktive Spieler bist”
- Conflicting code: `_harvest_actions()` creates harvests only for `state.actor`; proposal resolution also exposes only accept/reject.
- Expected: Any owner may harvest between atomic game steps, including during another player’s turn.
- Implemented: Only the current decision actor can harvest. Other owners receive no harvest action at most inter-step boundaries.
- Impact: Players can be denied legal harvest timing that affects later forced harvests, field availability, and scoring.
- Provenance note: This is an adjudication-dependent deviation from the approved timing decision, not an additional inference from the printed rule.

### Minor — m1: Final raw coin totals are not materialized or directly observable

- Canonical fact: `END-03`
- Source: `RULES`, PDF page 9
- Exact evidence: “Alle Spieler ernten noch … Karten auf der Hand zählen nicht”
- Conflicting code: `returns()` calculates final scores in a local variable, while `render()` continues to show only pre-final-harvest `state.coins`.
- Expected: Final harvests determine final raw coin totals, and the approved executable convention requires those totals to remain observable.
- Implemented: Winner returns account for ordinary final field rewards, but the calculated final totals are discarded after `returns()` and never exposed directly.
- Impact: Winner determination for the implemented normal beans is generally correct, but terminal score inspection is incomplete.

## 3. Rule-area coverage

| Rule area | Coverage | Assessment |
|---|---|---|
| Player count/start | Partial | Supports 4–5; start player is implicitly fixed to seat 0 |
| Inventory/setup | Fail | Uses 104-card base deck instead of selected 129-card deck |
| Ordered hands | Mostly pass | Five-card deal, front planting, and append-on-draw are represented |
| Phase 1 planting | Pass for two-field base game | Mandatory first and optional second supported |
| Reveal | Mostly pass | Two public cards revealed; affected by depletion timing |
| Trading | Partial/fail | Consent works, but quantities, gift direction, and card identity are restricted |
| Mandatory planting | Mostly pass | Received/retained cards are planted with selectable order |
| Phase 4 draw | Fail | Active draws three instead of every player drawing one |
| Normal harvesting | Pass | Normal meters and singleton protection match approved facts |
| Harvest timing | Fail | No general non-actor harvesting between steps |
| Acker/third field | Fail | Entire subsystem absent |
| Reshuffle/end timing | Fail | Depletion is detected late |
| Final scoring/tie | Partial | Ordinary final rewards and tie-break work; raw final totals are not exposed |
| Private information | Mostly pass | Current actor sees own ordered hand; opponents’ hands appear as counts |

## 4. Missing deterministic scenarios

- Initial deck contains exactly 129 cards before dealing, with 22 Weinbrandbohnen and three Ackerbohnen.
- Two Ackerbohnen unlock field three while preserving fields one and two.
- One, two-with-field-three-already-owned, and three-card Acker harvest outcomes.
- Phase four gives one card to each player in clockwise order, including correct hand appending.
- A legal 2-for-1 or 1-for-2 trade.
- A consensual gift from an inactive player to the active player.
- Trading a hand card when an identical revealed card exists, and selecting between duplicate hand positions.
- A non-active owner harvesting between two atomic steps.
- First/second depletion on the final owed draw, verifying that later discards do not enter that reshuffle.
- Third depletion on the second reveal versus during an individual phase-four draw.
- Terminal observations exposing each player’s final raw coin total.
- Tie-breaking with a nontrivial subset of tied seats.

## 5. Material questions for a human

These are not scored rule contradictions:

- Is player 0 intentionally treated as the externally configured start player, or should the constructor accept an explicit start-player seat?
- Is `render()` intended to be a single current-actor observation API? If observations may be requested by arbitrary players, it needs a viewer parameter to satisfy own-hand visibility consistently.
- Should final score totals be stored in terminal state, or is a separate public score accessor the preferred interface?

```text
score: 0.29
confidence: high
critical_issues: 2
major_issues: 3
minor_issues: 1
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true
```