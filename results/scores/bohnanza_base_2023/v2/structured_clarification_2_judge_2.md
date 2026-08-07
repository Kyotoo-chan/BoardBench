## Review result

`score: 0.55`, `confidence: high`

Most setup, planting, harvesting, payout, scoring, and ordinary phase transitions match the approved packet. The score is reduced by a terminal-boundary error that can change the winner, an exponentially large trade action space that makes longer games unreliable, and two material trade/information defects.

## Findings

### Critical 1 — Depletion is detected one draw too late

- Canonical facts: `BOHN-C-RECYCLE-FIRST-SECOND`, `BOHN-C-END-THIRD`, `BOHN-C-END-PHASE2-CONTINUE`, `BOHN-C-END-OUTSIDE-PHASE2-IMMEDIATE`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2
- Exact evidence:
  - “Ziehst du die letzte Karte vom Nachziehstapel, mische die Karten des Ablagestapels.”
  - “Das Spiel endet, sobald der Nachziehstapel zum dritten Mal leer wird.”
  - “Sollte dies beim Aufdecken der Karten in der 2. Phase passieren … werden die 2. und die 3. Phase noch zu Ende gespielt.”
- Conflicting code: `Game._draw_one`, especially lines 204–214; callers at `apply_action` lines 250–257 and 282–294.
- Expected: depletion occurs when the last card is drawn. The first two depletions recycle immediately; the third ends immediately unless it occurs during the phase-two reveal.
- Implemented: `depletions` increments only when a later call begins with an already empty deck.
- Consequences:
  - If phase-four’s third draw takes the last card on the third depletion, the game advances to the next player and permits phase-one actions before ending. Those extra plantings or harvests can change final scores and the winner.
  - If the last card is the final card of a reveal/draw on the first or second depletion, recycling is postponed. Harvested cards added to discard in the interim can incorrectly enter that recycle.
  - A third depletion on the second reveal card is not recorded as a phase-two depletion; finishing requires an erroneous phase-four `draw` action.

### Critical 2 — Trade action generation becomes exponentially inoperable

- Canonical facts: `BOHN-C-TRADE-ANY-HAND-POSITION`, `BOHN-C-TRADE-UNEQUAL`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2
- Exact evidence:
  - “Ihr dürft alle mit euren Handkarten handeln. Dabei spielt es keine Rolle, wo sich die Karten auf der Hand befinden.”
  - “Ihr dürft mit einer unterschiedlichen Kartenanzahl handeln.”
- Conflicting code: `Game._nonempty_subsets` and `Game.legal_actions`, lines 135–177.
- Expected: trades using arbitrary positions and bundle sizes remain usable throughout a complete game.
- Implemented: every subset of the active player’s hand/revealed cards is crossed with every subset of every partner’s hand and eagerly accumulated into one list.
- Impact: for 14 active-side references and a partner with 12 cards, one partner alone produces `(2^14−1) × 2^12 = 67,104,768` proposals. Such hand sizes are reachable because draws can exceed phase-one planting. `legal_actions()` can therefore exhaust memory or stall well before the game ends.

This is an operational core failure rather than a disagreement about which trade combinations the rule permits.

### Major 1 — Legal trade actions reveal private opponent cards

This is a deviation from the approved digital information decision, not a contradiction of otherwise explicit publisher privacy text.

- Canonical fact: `BOHN-M-OBS-DEEPER-HAND`, resolved by the approved observation decision
- Evidence type: `human_decision`
- Source: `BOHN-V3-STRUCTURED-CLARIFICATION`, `canonical_supplement.md`, “Clarified digital decisions,” item 4
- Exact evidence: “For each opponent expose hand size and the source-visible front card, but hide deeper card identities. Legal-action data must not leak those deeper identities.”
- Conflicting code: `Game.legal_actions` lines 171–177, `_refs` lines 130–133, and `action_to_data` lines 322–326.
- Expected: the active player’s legal-action representation must not disclose identities below an opponent’s visible front card.
- Implemented: `requested_refs` is constructed from the partner’s complete hand and every generated action includes each referenced card’s `bean`. Serialization preserves those identities.
- Impact: merely requesting legal actions exposes every opponent’s ordered hand.

`observation_to_data` itself correctly hides deeper opponent cards, but the legal-action channel defeats that protection.

### Major 2 — A non-active player cannot give a card to the active player

- Canonical facts: `BOHN-C-GIFT-CONSENT`, read with `BOHN-C-TRADE-ACTIVE-ONLY`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2
- Exact evidence:
  - “Als besondere Form des Handels dürft ihr euch auch Bohnenkarten schenken.”
  - “Die beschenkte Person muss dem Geschenk aber zustimmen.”
  - “Nur du als aktive Person darfst mit anderen handeln.”
- Conflicting code: `Game.legal_actions` lines 166–177 and `trade_accept` lines 265–278.
- Expected: a gift is a one-way trade involving the active player; either participant may be donor, with recipient consent.
- Implemented: every proposal requires a nonempty `offered` bundle owned by the active player. Empty active-side offers are never generated, so the partner cannot give cards to the active player without receiving an active-player card.
- Impact: a material source-permitted negotiation action is absent.

## Rule-area coverage

| Rule area | Result | Notes |
|---|---|---|
| Player counts, deck, deal, fields | Pass | 3–5 players, 104-card inventory, five cards, and field counts match. |
| Start player and clockwise order | Pass | Seed-selected fixed start holder and clockwise advancement implemented. |
| Hand order and phase-one planting | Pass | Mandatory front, optional second, no third, and separate harvest choice represented. |
| Reveal and ordinary trades | Partial | Reveal, consent, staging, arbitrary positions, unequal bundles, and atomic transfer exist; privacy, reverse gifts, and scalability fail. |
| Phase-three planting | Partial | All staged cards are mandatory and owner card order is selectable; decision-player routing is questionable. |
| Harvesting and beanometers | Pass | Off-turn choices, singleton rule, zero payout, conservation, and all eight curves match. |
| Draw and recycling | Fail | Card order is preserved, but empty-deck recognition is delayed. |
| Terminal and scoring | Partial | Final harvest, ignored hands, coin totals, winner, and tiebreak are correct once `_finish` runs; invocation timing is wrong. |
| Private information | Fail | Observation hides deeper hands, but legal actions reveal them. |
| Returns/API | Question | Winner utilities are supplied, but the packet does not specify whether returns should be win/loss or coin-based. |

## Missing deterministic scenarios

The following deterministic scenarios are needed:

1. Phase four starts with three cards and `depletions == 2`; drawing the third card must terminate immediately without advancing the player.
2. Phase-two reveal starts with two cards and `depletions == 2`; drawing the second card must complete phases two and three, then terminate without a phase-four action.
3. First/second depletion occurs on the final card of a reveal or draw; verify that only the discard existing at that instant is recycled.
4. Compare legal-action serialization for two states differing only in an opponent’s deeper hand cards; the acting player’s visible legal-action data must be indistinguishable.
5. A non-active player gives one hand card to the active player for nothing; verify recipient consent, atomic transfer, and staging.
6. Trade enumeration with realistically grown hands; verify bounded generation or a compact parameterized action representation.
7. Phase three with staged cards owned only by a non-active player; verify that the owner, not the active player, controls planting order.
8. Third depletion with a tied score where an incorrectly permitted extra planting would change the tiebreak or winner.

## Material questions for a human

- `BOHN-M-EMPTY-DISCARD-RECYCLE`: what should happen when the first or second depletion has no—or insufficient—discard cards? The implementation repeatedly counts empty draw attempts as further depletions, but the packet deliberately leaves this unresolved.
- During phase three, is `current_player` contractually the decision-maker? The code leaves it set to the active player while exposing actions whose actors are other owners. If callers route decisions through `current_player()`, owner choice is not preserved.
- Is `render()` considered player-visible? It prints every complete hand, unlike the approved observation mapping.
- Should terminal `returns()` encode only winner/loser utility, or actual coin totals? The supplied rules determine the winner but not this API convention.

```text
score: 0.55
confidence: high
critical_issues: 2
major_issues: 2
minor_issues: 0
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```