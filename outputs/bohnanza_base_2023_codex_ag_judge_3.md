score: 0.61  
confidence: high

The implementation covers setup, planting, harvesting, scoring, and most phase transitions well. Four material discrepancies remain: trade bundles are severely restricted, phase-three planting order is not selectable, legal actions expose private cards, and depletion is detected one draw late.

## Findings

### Major — Multi-card trade bundles cannot be proposed

- Canonical fact ID: `BOHN-C-TRADE-UNEQUAL`
- Evidence type: `human_decision`
- Source: `BOHN-V3-STRUCTURED-CLARIFICATION`
- Locator: `canonical_supplement.md`, “Four-phase turn”, item 2
- Exact evidence: “A proposed trade may contain any positive number of cards on either side, may be unequal, and may use arbitrary hand positions plus the active player's revealed cards.”
- Conflicting code: `Game.legal_actions`, [implementation.py:76](C:/Users/benti/AppData/Local/Temp/.ctx-mode-FwgQ6h/boardbench_bohnanza_base_2023_codex_ag_judge_3_5z_j7vqd/implementation.py:76), especially `offered=[off]` with either `requested=[]` or `requested=[req]`.
- Expected: A proposal can atomically exchange bundles such as two cards for one, three for two, or larger unequal combinations.
- Implemented: Every ordinary trade is exactly one-for-one; gifts transfer exactly one card. Repeated proposals are not equivalent because each accepted card is immediately staged and cannot be retraded. This removes source-legal bargaining outcomes.

### Major — Owners cannot choose the order of their staged cards

- Canonical fact ID: `BOHN-C-PLANT-OWNER-ORDER`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`
- Locator: PDF page 2
- Exact evidence: “Jede Person darf selbst entscheiden, in welcher Reihenfolge sie die neuen Bohnenkarten anbaut.”
- Conflicting code: `Game._plants`, [implementation.py:55](C:/Users/benti/AppData/Local/Temp/.ctx-mode-FwgQ6h/boardbench_bohnanza_base_2023_codex_ag_judge_3_5z_j7vqd/implementation.py:55), fixes `index=0` for both `received` and `revealed` zones.
- Expected: Each owner selects which of their staged cards to plant next.
- Implemented: Only the first card of each zone can be planted. For a non-active recipient, receipt/acceptance order dictates planting order. This can alter forced harvests and resulting fields.

### Major — Legal actions reveal every opponent hand card

- Canonical fact ID: `BOHN-M-OBS-DEEPER-HAND`
- Evidence type: `human_decision`
- Source: `BOHN-V3-STRUCTURED-CLARIFICATION`
- Locator: `canonical_supplement.md`, “Clarified digital decisions”, item 4
- Exact evidence: “For each opponent expose hand size and the source-visible front card, but hide deeper card identities. Legal-action data must not leak those deeper identities.”
- Conflicting code: `Game.legal_actions`, [implementation.py:76](C:/Users/benti/AppData/Local/Temp/.ctx-mode-FwgQ6h/boardbench_bohnanza_base_2023_codex_ag_judge_3_5z_j7vqd/implementation.py:76), iterates through every partner hand position and embeds both `index` and `bean` in each `trade_propose` action.
- Expected: An observer can see only an opponent’s hand size and front card; deeper identities must remain hidden even through action data.
- Implemented: Enumerating legal actions discloses the identity and position of every card in every prospective partner’s hand. The observation payload itself is appropriately redacted, but the legal-action channel defeats that protection.

### Major — Empty-pile depletion is registered one draw too late

- Canonical fact IDs: `BOHN-C-RECYCLE-FIRST-SECOND`, `BOHN-C-END-THIRD`, `BOHN-C-END-PHASE2-CONTINUE`, `BOHN-C-END-OUTSIDE-PHASE2-IMMEDIATE`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`
- Locator: PDF page 2
- Exact evidence:
  - “Ziehst du die letzte Karte vom Nachziehstapel, mische die Karten des Ablagestapels.”
  - “Das Spiel endet, sobald der Nachziehstapel zum dritten Mal leer wird.”
  - “Sollte dies beim Aufdecken der Karten in der 2. Phase passieren … werden die 2. und die 3. Phase noch zu Ende gespielt.”
- Conflicting code: `Game._draw_one`, [implementation.py:100](C:/Users/benti/AppData/Local/Temp/.ctx-mode-FwgQ6h/boardbench_bohnanza_base_2023_codex_ag_judge_3_5z_j7vqd/implementation.py:100), checks whether the deck is empty only before popping the next card.
- Expected: Drawing the last card immediately registers depletion. On the third depletion, the phase-two exception is determined by where that last card was drawn.
- Implemented: Depletion is registered only when a later draw is attempted. Consequences include:
  - If phase four starts with exactly three cards, all three are drawn and the next player begins phase one before game end is detected.
  - If phase-two reveal starts with exactly two cards on the third pass, the state incorrectly enters phase four after phase three and requires a `draw` action to terminate.
  - First/second recycling is likewise delayed when the last required card exactly completes a reveal or draw.

## Rule-area coverage

| Rule area | Result | Notes |
|---|---|---|
| Setup and inventory | Pass | Correct 104-card inventory, player limits, hand sizes, fields, seeded fixed start player |
| Phase-one planting | Pass | Mandatory first, optional second, no third, separate forced harvest |
| Reveal and trade | Fail | Reveal/consent/staging work; arbitrary multi-card bundles do not |
| Phase-three planting | Partial | All staged cards are compulsory, but owner-selected order is missing |
| Phase-four draw | Partial | Three-card append and clockwise advance work; exact exhaustion boundary is wrong |
| Fields and harvesting | Pass | Singleton protection, off-turn boundaries, zero payouts, conservation, all meters |
| Recycling and termination | Fail | Third-depletion timing is wrong on exact exhaustion |
| Private information | Fail | Observation is redacted, but legal actions leak deeper hands |
| Final scoring and returns | Pass | Final harvest, ignored hands, highest coins, clockwise tiebreak; returns are one-hot |
| Serialization | No source conflict found | Strict envelopes are an implementation profile choice |

## Missing deterministic scenarios

These should be added without relying on random bounded play:

1. Accept and reject a two-for-one trade, verifying atomic transfer and unchanged state on rejection.
2. Plant two differently typed received cards in either owner-selected order, with different forced-harvest consequences.
3. Compare legal-action data from every viewer and assert that no deeper opponent identity appears.
4. Begin third-pass phase-two reveal with exactly two deck cards; complete phases two and three, then terminate without exposing phase four.
5. Begin third-pass phase four with exactly three deck cards; terminate before the next player receives a phase-one decision.
6. Exhaust the first or second pile on the final required draw and verify immediate recycling plus correct subsequent draw order.
7. Once clarified, cover nonterminal depletion with an empty or insufficient discard pile.

## Material questions for a human

- `BOHN-M-EMPTY-DISCARD-RECYCLE`: What should happen when the first or second depletion occurs but the discard cannot supply the remaining reveal/draw cards? The approved packet explicitly leaves this undecided. Current code may return no card and can count the same still-empty pile again on a subsequent draw attempt.
- Should gifts be supported in both directions between the active player and a partner? The printed rule requires recipient consent but does not explicitly define digital proposal direction.
- The implementation uses round-robin initial dealing. This is a reasonable profile choice, but `BOHN-M-DEAL-DIRECTION` confirms that exact direction/grouping is not supplied by the rulebook.

score: 0.61
confidence: high
critical_issues: 0
major_issues: 4
minor_issues: 0
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true