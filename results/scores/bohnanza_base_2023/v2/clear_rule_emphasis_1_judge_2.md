score: 0.56
confidence: high

## Assessment

`score: 0.56` — `confidence: high`

Most setup, planting, harvesting, recycling, phase sequencing, observation, and third-depletion behavior match the approved facts. However, ordinary play can become computationally nonviable during trading, and three clear printed rules are contradicted: Red Bean payouts, phase-three planting order, and the final tiebreak.

## Findings

### Critical

1. Trade action generation grows exponentially and can prevent normal games from completing reliably.

- Canonical facts: `BOHN-C-TRADE-ANY-HAND-POSITION`, `BOHN-C-TRADE-UNEQUAL`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2
- Exact evidence: “Ihr dürft alle mit euren Handkarten handeln. Dabei spielt es keine Rolle, wo sich die Karten auf der Hand befinden.” and “Ihr dürft mit einer unterschiedlichen Kartenanzahl handeln.”
- Conflicting code: `Game.legal_actions`, `_nonempty_subsets`, especially eager `offers = list(...)` and the nested offered/requested subset loops at implementation lines 141–154.
- Expected: Legal multi-card, unequal trades remain available from arbitrary hand positions throughout a practical complete game.
- Implemented: Every nonempty subset on one side is crossed with every nonempty subset on the other. This produces approximately `(2^m−1)(2^n−1)` proposals per partner. Since hands commonly grow when three cards are drawn after only one is planted, later calls can allocate millions or billions of `Action` objects, effectively hanging or exhausting memory.

This is a reliability defect, not a penalty for supporting source-legal multi-card trades. The implementation correctly permits unequal bundles and does not reduce them to single-card trades.

### Major

2. The Red Bean payout curve is materially wrong.

- Canonical fact: `BOHN-C-PAYOUT-ROT`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 1, Red Bean Bohnometer
- Exact evidence: “Red: thresholds 2/3/4/5 pay 1/2/3/4.”
- Conflicting code: `METERS["rote_bohne"]` at line 13: `((3, 1), (6, 2), (7, 3), (8, 4))`
- Expected: 2, 3, 4, and 5 or more Red Beans pay 1, 2, 3, and 4 coins respectively.
- Implemented: Those payouts begin at 3, 6, 7, and 8 cards. This changes harvest values and can change the winner.

The emphasized Garden and Soy curves are implemented correctly.

3. Owners cannot choose the order of multiple received cards.

- Canonical fact: `BOHN-C-PLANT-OWNER-ORDER`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2
- Exact evidence: “Jede Person darf selbst entscheiden, in welcher Reihenfolge sie die neuen Bohnenkarten anbaut.”
- Conflicting code: `Game.legal_actions` uses only `cards[0]` for each owner at lines 161–166; `trade_accept` creates a fixed receipt order through its sorted transfer loop at lines 295–302.
- Expected: Each owner can select any of their staged new cards as the next card they plant.
- Implemented: The first element of `pending_received[owner]` must always be planted next. The order is determined by internal reference sorting rather than by the owner.

The separate approved human decision concerning inter-player order is honored: different owners with staged cards may act next in any order.

4. The tiebreak can incorrectly select the Start-card holder.

- Canonical fact: `BOHN-C-TIEBREAK`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2
- Exact evidence: “Bei einem Gleichstand gewinnt die Person, die im Uhrzeigersinn am weitesten weg von der Person mit der Start-Karte sitzt.”
- Conflicting code: `Game._finish`, lines 221–223:
  `order = [(start_player + i) % n for i in range(1, n + 1)]`, followed by selection from `reversed(order)`.
- Expected: Among tied leaders, choose the tied player at the greatest clockwise distance from the Start-card holder.
- Implemented: The generated order ends with the Start-card holder and is then reversed, so the holder is selected first whenever tied. For example, an all-player tie always awards the game to the Start-card holder.

### Minor

None identified.

### Questions—not scored as printed-rule contradictions

1. `BOHN-M-EMPTY-DISCARD-RECYCLE`: the source does not decide what happens if the first or second depletion occurs with an empty or insufficient discard pile. `_draw_one` leaves the deck empty and subsequent requested draws return `None`. A human policy is needed before this behavior can be judged.

2. `BOHN-M-OBS-DEEPER-HAND`: `observation_to_data` correctly follows the approved observation decision by hiding deeper opponent cards. However, trade actions themselves contain exact bean identities and indices from opponents’ deeper hands. Whether agent-facing legal-action enumeration is allowed to reveal those references is not decided by the printed rule or the observation decision.

## Coverage

| Rule area | Result | Notes |
|---|---|---|
| Setup and player counts | Pass | 3–5 players, field counts, 104-card inventory, five-card hands |
| Hand order and visibility | Pass/question | Ordered hands and public fronts work; trade-action leakage needs a decision |
| Phase-one planting | Pass | Mandatory first, optional second, no third |
| Reveal and phase sequence | Pass | Two-card reveal and four-phase progression represented |
| Trading and gifts | Critical reliability issue | Consent, atomic transfer, unequal bundles, staging present |
| Phase-three planting | Fail | All cards are forced, but owner-selected order is missing |
| Harvest legality | Pass | Off-turn harvesting and singleton protection represented |
| Payouts | Fail | Red Bean curve wrong; seven other curves match |
| Recycling/chance | Pass/question | First/second recycling works when discard is available |
| Third depletion | Pass | Phase-two continuation ends after phase three; other depletion ends immediately |
| Final scoring/winner | Fail | Final harvest and highest score work; tiebreak is wrong |
| Returns | Partial | Correct one-hot form when winner selection is correct; inherits tiebreak defect |

## Missing deterministic scenarios

- Red Bean fields at sizes 2 through 8, asserting every threshold and plateau.
- Multiple received cards whose two planting orders lead to different forced harvests.
- Ties involving the Start-card holder, all players, and nonadjacent tied leaders for 3, 4, and 5 players.
- Trade legal-action generation at progressively growing hand sizes, with a bounded runtime/action-representation expectation.
- First/second depletion with zero, one, and sufficient discard cards.
- Private observation plus legal-action exposure for a proposed trade involving a deeper opponent card.
- Third depletion during phase-two reveal with only one card available, confirming no phase-four draw is required.

## Material questions for a human

- What deterministic behavior should apply when a nonterminal recycle has insufficient discard cards?
- Are legal actions part of a player’s information boundary, and if so, how should trades involving hidden deeper opponent cards be represented without revealing their identities?
- Should legal trades be represented parametrically or through a proposal-building transition to avoid exhaustive subset enumeration?

```text
score: 0.56
confidence: high
critical_issues: 1
major_issues: 3
minor_issues: 0
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```