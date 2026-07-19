score: 0.52 — confidence: high. The module covers much of the basic turn structure, inventory, hand order, harvesting, and scoring, but has one winner-affecting terminal defect and three material rule contradictions.

## Findings

### Critical

1. Third depletion is detected one draw too late and can permit an extra turn

- Canonical facts: `BASE-END-01`, `BASE-END-02`, and adjudication `D-BASE-END`
- Evidence types: `rule_quote`; separately, `human_decision`
- Source: `BOHN-BASE-RULES`, PDF p. 2
- Exact evidence: “Ziehst du die letzte Karte vom Nachziehstapel, dann mische die Karten des Ablagestapels.” and “Das Spiel endet, sobald der Nachziehstapel zum dritten Mal leer wird.”
- Human decision locator: `approved_rulefacts.md` → “Approved evaluator decisions” → item 1
- Exact decision: “Interpret ‘endet, sobald’ as immediate termination when the third emptying occurs outside phase two. Do not recycle the discard and do not require remaining phase-four draws.”
- Conflicting symbols: `Game._draw_one`, the `draw` transition in `Game.apply_action`
- Expected: Emptying occurs when the last card is drawn. On the third emptying outside phase two, the game ends immediately.
- Implemented: `_draw_one` increments `depletions` only when called while the deck is already empty. If phase four begins with exactly three cards, all three are drawn, the next player enters `plant_first`, and depletion is not recognized until a later draw attempt. That player may plant cards before termination, potentially changing final payouts and the winner.
- Classification note: The immediate-termination requirement depends on the explicit human adjudication; the underlying “last card empties the pile” timing is printed.

### Major

2. Phase three handles only the active player and restricts planting order

- Canonical fact: `BASE-PHASE3-01`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-RULES`, PDF p. 2
- Exact evidence: “Alle, die Karten quer neben ihren Feldern liegen haben, müssen diese nun anbauen. … Jede Person darf selbst entscheiden, in welcher Reihenfolge sie die neuen Bohnenkarten anbaut.”
- Conflicting symbols: `Game.legal_actions` branch `phase == "plant_received"`, `Game._plant_actions`, `end_trade` transition
- Expected: Every player plants all received cards, and each affected player chooses the order of their own new cards. The active player additionally plants untraded revealed cards.
- Implemented: Phase-three actions always use `active_player`. Cards staged in another player’s `pending_received` list can never be planted. `_plant_actions` also exposes only element zero of each source, preventing the full player-chosen ordering required by the rule.

3. Legal trade bundles are artificially capped

- Canonical fact: `BASE-TRADE-03`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-RULES`, PDF p. 2
- Exact evidence: “Ihr dürft mit euren Handkarten handeln.” and “Ihr dürft mit einer unterschiedlichen Kartenanzahl handeln, z. B. zwei blaue Bohnen gegen eine Gartenbohne.”
- Conflicting symbol: trade action generation in `Game.legal_actions`, especially `offers = ... for n in (1, 2)` and single-element `requested`
- Expected: Trades may use arbitrary hand positions and unequal quantities without the illustrated 2-for-1 example becoming a cap.
- Implemented: The active side may offer only one or two cards, while the partner may provide only one. Legal exchanges such as one-for-two or three-for-one cannot be represented.

4. Gartenbohne payouts are shifted downward

- Canonical fact: `BASE-PAY-01`
- Evidence type: `rule_quote` (graphical Bohnometer transcription)
- Source: `BOHN-BASE-RULES`, PDF p. 1, Gartenbohne Bohnometer
- Exact evidence: Garten minimum sizes for 1/2/3/4 coins are `-/2/3/-`.
- Conflicting symbols: `METERS["gartenbohne"] = (2, 3)` and the threshold-counting expressions in harvest and `_finish`
- Expected: Two Gartenbohnen pay two coins; three or more pay three.
- Implemented: Counting satisfied thresholds makes two cards pay one coin and three or more pay two. This affects ordinary harvests, final harvests, and winner determination.

No supported minor findings.

## Coverage

| Rule area | Result | Notes |
|---|---|---|
| Inventory/setup | Mostly covered | Counts, hand size, and field counts match; starting player is fixed to player 0 |
| Hand order/phase 1 | Covered | Mandatory first, optional second, no third, empty-hand skip |
| Reveal/trading | Partial | Reveal and consent work; trade quantities are restricted |
| Phase-three planting | Contradicted | Non-active recipients cannot plant; ordering is restricted |
| Drawing/chance | Partial | Three-card append works; empty-pile event timing is wrong |
| Harvest legality | Covered | Off-turn access, singleton protection, and field clearing are represented |
| Payouts | Partial | Seven curves match; Gartenbohne is wrong |
| Terminal/scoring | Contradicted | Delayed third depletion can change final fields and winner |
| Tie-break/returns | Covered | Farthest-clockwise tied player is selected |
| Private information | Acceptable | Consistent with `D-BASE-OBS`; privacy is not scored |

## Missing deterministic scenarios

- Third depletion when phase four starts with exactly three cards: termination must occur before the next player’s phase one.
- First or second depletion caused by drawing exactly the final card, verifying the discard snapshot is recycled immediately.
- Third depletion when phase-two reveal draws exactly the last two cards: finish phases two and three, with no phase-four decision boundary.
- A trade giving multiple cards to a non-active player, followed by that player planting all of them.
- Phase-three choices where planting the second received or revealed card first matters.
- Legal one-for-two and three-for-one trades.
- Gartenbohne harvests at field sizes one, two, and three, both during play and at final scoring.

## Material questions

- `BASE-TRADE-07` establishes consensual gifts but does not expressly state their direction. Must the interface support a non-active player gifting cards to the active player, or only gifts initiated from the active player’s cards?
- Does “Bestimmt, wer beginnt” require an exposed setup choice, or is deterministic player relabeling with player 0 as the starter acceptable? No penalty was applied.

score: 0.52
confidence: high
critical_issues: 1
major_issues: 3
minor_issues: 0
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true