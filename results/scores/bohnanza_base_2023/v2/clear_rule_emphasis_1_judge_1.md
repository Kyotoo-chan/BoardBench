Score: **0.50**, confidence: **high**. Most setup, planting, trade-consent, harvest, depletion, and end-phase structure is faithful. However, ordinary trading can become computationally unusable, and three clear rules materially affecting scoring or player choice are contradicted.

## Findings

### Critical — Trade action generation grows exponentially and can prevent normal play

- Canonical facts: `BOHN-C-TRADE-ANY-HAND-POSITION`, `BOHN-C-TRADE-UNEQUAL`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2
- Exact evidence:
  - “Ihr dürft alle mit euren Handkarten handeln. Dabei spielt es keine Rolle, wo sich die Karten auf der Hand befinden.”
  - “Ihr dürft mit einer unterschiedlichen Kartenanzahl handeln.”
- Conflicting symbols: `Game._nonempty_subsets`, `Game.legal_actions` trade branch, and `Game.apply_action`
- Expected: Arbitrary-position, unequal multi-card bundles must remain practically usable as hands grow.
- Implemented: `legal_actions` eagerly materializes every offered subset and every requested subset, then their Cartesian product. For active/revealed pool size `a` and partner hand size `b`, this is approximately `2^(a+b)` proposals per partner. Even `end_trade` is validated by rebuilding this entire list because `apply_action` calls `legal_actions`.
- Impact: Hands naturally grow when three cards are drawn but only one or two are planted. Modest hands can produce millions of `Action` objects, causing severe latency or memory exhaustion in a core phase. Proposal validation should be direct or lazily represented.

### Major — Red Bean payout meter is wrong

- Canonical fact: `BOHN-C-PAYOUT-ROT`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 1, Red Bean Bohnometer
- Exact evidence: “[Visual transcription of the named card’s Bohnometer, page 1] Red: thresholds 2/3/4/5 pay 1/2/3/4.”
- Conflicting symbol: `METERS["rote_bohne"]`
- Expected: 2, 3, 4, and 5 Red Beans pay 1, 2, 3, and 4 coins.
- Implemented: Thresholds are 3, 6, 7, and 8.
- Impact: Nearly every Red Bean harvest scores incorrectly, including final harvests.

### Major — Owners cannot choose the order of all phase-three cards

- Canonical fact: `BOHN-C-PLANT-OWNER-ORDER`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2, phase 3
- Exact evidence: “Jede Person darf selbst entscheiden, in welcher Reihenfolge sie die neuen Bohnenkarten anbaut.”
- Conflicting transition: `Game.legal_actions`, `phase == "plant_received"`
- Expected: Each owner may choose any of their remaining received/revealed cards as the next card they plant.
- Implemented: Only `pending_received[owner][0]` and `revealed[0]` are selectable. Acceptance also establishes list order mechanically rather than preserving a later player choice.
- Impact: Planting order can determine which field must be harvested and therefore change scores.

### Major — Ties involving the Start-card holder select the wrong winner

- Canonical fact: `BOHN-C-TIEBREAK`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2, “Ende des Spiels”
- Exact evidence: “Bei einem Gleichstand gewinnt die Person, die im Uhrzeigersinn am weitesten weg von der Person mit der Start-Karte sitzt.”
- Conflicting symbol: `Game._finish`, especially `next(i for i in reversed(order) if i in tied)`
- Expected: The tied leader with the greatest clockwise distance from the fixed Start-card holder wins.
- Implemented: `order` ends with the Start-card holder and is then reversed, so the Start-card holder is checked first. If that player is tied for the lead, the code declares them winner.
- Impact: The official winner is wrong for a material class of tied endings; `returns()` then propagates the error.

No minor findings.

## Rule-area coverage

| Rule area | Assessment |
|---|---|
| Player counts, fields, deck inventory, five-card deal | Pass |
| Start selection/card and clockwise turns | Pass |
| Hand order and phase-one planting | Pass |
| Field compatibility and forced harvest | Pass |
| Reveal and trade permissions/consent/atomic transfer | Functionally represented, but critically unscalable |
| Unequal and multi-card trades | Semantically supported |
| Phase-three mandatory planting | Partial; owner-selected order fails |
| Harvest timing and singleton protection | Pass |
| Beanometers | Fail for Red Bean; other seven match |
| Recycling and third depletion | Pass for publisher-decided cases |
| Final harvest and ignored hands | Pass |
| Winner and returns | Fail for ties involving Start-card holder |
| Private information | Observation mostly conforms; action-interface exposure needs confirmation |

## Deterministic scenarios to add

- Red Bean fields of sizes 1–8, including both ordinary and final harvests.
- Phase-three received bundles in which reversing two unlike cards changes the forced harvest.
- Active player choosing among multiple untraded revealed cards and received cards.
- Two-way and multi-way ties that include the Start-card holder.
- Bounded-time `end_trade` and proposal application with 8–12 cards per hand.
- Observation/action exposure checks for deeper opponent cards during trade proposals.
- Third depletion on the first versus second phase-two reveal, confirming phase four is never entered.

## Material questions for a human

- `BOHN-M-EMPTY-DISCARD-RECYCLE`: The packet does not specify what happens when the first or second depletion has no sufficient discard supply. `_draw_one` can leave an empty deck without advancing toward the third depletion, potentially stalling future draws. A policy is needed before scoring this behavior.
- Does the player-facing interface expose `legal_actions` or only `observation_to_data`? `legal_actions` embeds every opponent hand card’s bean and index in requested trade references. If player-visible, this contradicts approved human decision 4’s requirement to hide deeper opponent identities.
- Should a publicly announced pending proposal reveal its complete referenced-card identities to uninvolved players? The approved observation decision and the physical negotiation model do not explicitly settle that boundary.

score: 0.50
confidence: high
critical_issues: 1
major_issues: 3
minor_issues: 0
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true