Score: 0.64, confidence: high. Setup, planting, harvesting, payouts, ordinary trades, final scoring, and tie-breaking are substantially represented. Three material defects remain: depletion is detected one draw too late, private hand identities leak through legal actions, and gifts are only supported in one direction.

## Findings

### Major

1. Third depletion is detected only on a subsequent draw attempt

- Canonical facts: `BOHN-C-END-THIRD`, `BOHN-C-END-OUTSIDE-PHASE2-IMMEDIATE`, also `BOHN-C-RECYCLE-FIRST-SECOND`.
- Evidence type: `rule_quote`.
- Source: `BOHN-BASE-2023-RULES`, PDF page 2.
- Exact evidence: “Das Spiel endet, sobald der Nachziehstapel zum dritten Mal leer wird.” The recycle rule likewise begins: “Ziehst du die letzte Karte vom Nachziehstapel …”
- Conflicting code: `Game._draw_one`, especially the pre-draw empty check at implementation.py lines 204–214; phase-four transition at lines 282–294.
- Expected: drawing the last card empties the pile at that moment. On the third occurrence outside phase-two reveal, the game ends immediately. On the first two occurrences, discard is immediately recycled before another stable decision boundary.
- Implemented: depletion increments only when `_draw_one` is called while the deck is already empty. If the last card is the final card of a three-card draw, the turn advances normally. The next player may plant and trade before termination is detected. First/second recycling is similarly delayed, allowing later harvest discards to enter a recycle that should already have happened.
- Impact: terminal timing, final scores, and recycled deck composition can change.

2. Legal-action enumeration reveals every opponent’s deeper hand

- Canonical fact: `BOHN-M-OBS-DEEPER-HAND`, resolved by the approved private-information decision.
- Evidence type: `human_decision`.
- Source: `BOHN-V3-STRUCTURED-CLARIFICATION`, `canonical_supplement.md`, “Clarified digital decisions” item 4.
- Exact evidence: “For each opponent expose hand size and the source-visible front card, but hide deeper card identities. Legal-action data must not leak those deeper identities.”
- Conflicting code: `Game.legal_actions` / `_refs`, implementation.py lines 131–133 and 166–177.
- Expected: an observer sees an opponent’s hand size and front card only. Legal-action data must use opaque/private-safe references for deeper cards.
- Implemented: `requested_refs = self._refs(partner, "hand", state.players[partner]["hand"])` embeds every card’s index and bean identity in every generated proposal. Anyone receiving the common legal-action list can reconstruct all hands. Accepted proposal data is also exposed unchanged through `observation_to_data.pending`.
- Impact: materially incorrect private information and trading decisions.

3. The active player cannot receive a gift from another player

- Canonical fact: `BOHN-C-GIFT-CONSENT`.
- Evidence type: `rule_quote`.
- Source: `BOHN-BASE-2023-RULES`, PDF page 2.
- Exact evidence: “Als besondere Form des Handels dürft ihr euch auch Bohnenkarten schenken. Die beschenkte Person muss dem Geschenk aber zustimmen.”
- Conflicting code: `Game.legal_actions`, implementation.py lines 166–177; `trade_propose` construction.
- Expected: within a transaction involving the active player, either participant can be the giver, and the recipient must accept.
- Implemented: gift proposals always have nonempty `offered` cards owned by the active player and an empty `requested` bundle. No action represents a partner giving cards to the active player.
- Impact: a material class of permitted phase-two transactions is absent.

### Minor

1. Pending proposals can disclose deeper cards to uninvolved observers

`observation_to_data` returns the complete `pending` structure to every player (lines 360–369). Beyond the legal-action leak above, this exposes referenced deeper cards to players who are not participants. Whether spoken negotiations make every specific offer public is not established by the publisher rulebook, but the approved privacy decision favors redaction.

2. Trade action generation has severe combinatorial growth

`_nonempty_subsets` constructs every subset on both sides and their Cartesian product. Moderate hand sizes can produce hundreds of thousands or millions of actions. This is not itself a printed-rule contradiction, but it may make otherwise legal late-game trade states impractical to operate.

## Rule-area coverage

| Rule area | Status | Notes |
|---|---|---|
| Setup and deck | Covered | Correct 3–5 players, fields, five-card hands, 104-card inventory and seeded start |
| Hand order | Covered | Front planting and append order preserved |
| Four-phase turn | Mostly covered | Normal order and phase-three completion represented |
| Forced planting | Covered | Separate harvest decision is required when no field fits |
| Trading | Partial | Consent, unequal bundles, arbitrary positions and staging work; reverse gifts absent |
| Private information | Incorrect | Observation body is mostly redacted, but legal actions leak full hands |
| Harvesting | Covered | Off-turn actions, singleton protection, zero-value harvests and payouts represented |
| Recycling | Incorrect | Empty-pile event is registered one draw too late |
| Game end | Incorrect | Third depletion can permit an extra partial turn |
| Final scoring | Covered | Final harvest, ignored hands, highest coins and clockwise tie-break implemented |
| Returns | Covered | Single rule-determined winner receives the positive return |

## Missing deterministic scenarios

- Third depletion when the last deck card is exactly the third phase-four draw; assert immediate termination before the next player plants.
- Third depletion when the last card is exactly the second phase-two reveal; assert phases two and three complete, with no phase four.
- First/second depletion on the final requested draw; assert recycling happens before any later harvest boundary.
- Harvest immediately after drawing the last card; assert those newly discarded cards are not retroactively included in the already-required recycle.
- Legal actions viewed by each non-active player; assert no deeper opponent bean identities appear.
- Pending trade observed by a nonparticipant; assert private card identities remain hidden.
- Non-active player gives one or several cards to the active player, with both acceptance and rejection.
- Large-hand trade state to ensure legal-action production remains bounded and usable.

## Material questions for a human

- When a proposal explicitly names a deeper hand card, should its identity become public to everyone, only to the two participants, or remain opaque until acceptance? The supplement clearly forbids pre-proposal legal-action leakage but does not explicitly define proposal visibility.
- For the publisher-unspecified case `BOHN-M-EMPTY-DISCARD-RECYCLE`, what should happen if the first or second depletion occurs with no usable discard pile?
- Should trade actions expose all combinations eagerly, or use a staged bundle-building interface to avoid combinatorial failure? This is an environment representation decision, not a printed rule.

score: 0.64
confidence: high
critical_issues: 0
major_issues: 3
minor_issues: 2
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true