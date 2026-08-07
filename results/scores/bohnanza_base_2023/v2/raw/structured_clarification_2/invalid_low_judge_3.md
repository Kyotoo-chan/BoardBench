score: 0.61  
confidence: high

The module models most printed mechanics correctly, including setup, hand order, planting limits, harvesting/payouts, phase-three ordering, final harvest, and tiebreaking. Its main weaknesses are exponential trade-action generation, late depletion detection, and private-card leakage.

## Findings

### Critical — Trade action enumeration becomes exponentially intractable

- Canonical facts: `BOHN-C-TRADE-ANY-HAND-POSITION`, `BOHN-C-TRADE-UNEQUAL`
- Evidence type: `human_decision`
- Source: `BOHN-V3-STRUCTURED-CLARIFICATION`, “Balanced whole-game implementation checklist” → “Reveal and trade”
- Exact evidence: “A proposed trade may contain any positive number of cards on either side, may be unequal, and may use arbitrary hand positions plus the active player's revealed cards.”
- Conflicting symbols: `Game._nonempty_subsets`, `Game.legal_actions`, `trade_propose`
- Expected: Arbitrarily sized legal bundles must remain practically selectable throughout a complete game.
- Implemented: `legal_actions()` eagerly materializes every offered subset crossed with every requested subset for every partner. For offer and request pools of sizes `m` and `n`, this produces roughly `(2^m−1)(2^n−1)` proposals per partner, plus gifts. Hands can grow over successive turns, so normal play can reach millions of `Action` objects and become prohibitively slow or exhaust memory.
- Impact: The core game cannot reliably complete as hand sizes increase. Bundle selection needs a compact or parameterized action representation rather than exhaustive Cartesian enumeration.

### Major — Depletion is recorded one draw too late

- Canonical facts: `BOHN-C-RECYCLE-FIRST-SECOND`, `BOHN-C-END-THIRD`, `BOHN-C-END-PHASE2-CONTINUE`, `BOHN-C-END-OUTSIDE-PHASE2-IMMEDIATE`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2
- Exact evidence: “Ziehst du die letzte Karte vom Nachziehstapel, mische die Karten des Ablagestapels.” and “Das Spiel endet, sobald der Nachziehstapel zum dritten Mal leer wird.”
- Conflicting symbols/transitions: `Game._draw_one`; `reveal → trade`; `draw → next plant_first`
- Expected: Drawing the last card immediately constitutes a depletion. The first two depletions recycle immediately; the third ends immediately except for the phase-two continuation through phase three.
- Implemented: `_draw_one()` increments `depletions` only when called while the deck is already empty, not when its pop removes the last card. If the last card is the final card requested by a reveal or three-card draw, the depletion is deferred until a later draw attempt.
- Impact: A third depletion on the third phase-four draw can incorrectly advance to another player’s turn. A third depletion on the second reveal card requires a later artificial `draw` action after phase three before termination instead of ending automatically there. First/second recycling is likewise not immediate at an exact batch boundary.

### Major — Legal actions and observations leak deeper opponent hand identities

- Canonical fact: `BOHN-M-OBS-DEEPER-HAND`, resolved by the approved private-information decision
- Evidence type: `human_decision`
- Source: `BOHN-V3-STRUCTURED-CLARIFICATION`, “Clarified digital decisions,” item 4
- Exact evidence: “For each opponent expose hand size and the source-visible front card, but hide deeper card identities. Legal-action data must not leak those deeper identities.”
- Conflicting symbols: `Game.legal_actions`, `_refs`, `trade_propose`, `observation_to_data`, `render`
- Expected: A viewer sees their own ordered hand and only each opponent’s hand size and front card. Legal-action payloads must not reveal deeper opponent cards.
- Implemented:
  - During trading, `legal_actions()` constructs requested references for every opponent hand card with its `bean` identity.
  - `observation_to_data()` copies `state.pending`, including those references and identities, to every observer.
  - `render()` prints every complete hand.
- Impact: Private strategic information is exposed whenever trade actions, a pending proposal, or the general render are visible to a player. The ordinary `opponents` observation summary itself is correctly redacted.

## Minor findings

None established from the approved packet.

## Questions

1. Gift direction: the rulebook says players may give each other bean cards, but the implementation only generates proposals where the active player gives at least one card. It cannot represent a non-active player giving a card to the active player with nothing returned. `BOHN-C-GIFT-CONSENT` establishes consent but does not atomically state which participant may be the giver. A human should confirm whether active-recipient gifts are required.

2. The publisher packet does not define behavior when a first/second depletion has an empty or insufficient discard pile (`BOHN-M-EMPTY-DISCARD-RECYCLE`). `_draw_one()` returns no card and allows the enclosing phase to continue. This is an explicit source gap, not scored as a contradiction.

3. `returns()` assigns `+1` to the winner and `-1` to everyone else rather than returning coin totals. The rules decide the winner but do not prescribe an environment reward convention. Confirm the intended BoardBench return contract before treating this as a defect.

## Coverage

| Rule area | Status | Notes |
|---|---|---|
| Player counts and setup | Covered | Correct 3–5 validation, fields, five-card hands, 104-card inventory |
| Start player | Covered | Reproducible seed selection; fixed holder retained |
| Hand order/information | Partial | Plant/draw ordering correct; private identities leak through actions/pending/render |
| Phase-one planting | Covered | Mandatory first, optional second, no third; separate harvest decisions |
| Reveal and trading | Partial | Consent, staging, unequal bundles, and arbitrary positions modeled; action space is not scalable |
| Phase-three planting | Covered | Any affected owner may act; owner chooses card order; all staged cards required |
| Phase-four draw/advance | Partial | Sequential append and clockwise advance correct; depletion boundary is late |
| Harvesting and payouts | Covered | Off-turn boundaries, singleton protection, zero-value harvests, all meters |
| Recycling and termination | Incorrect | Exact-last-card depletion is deferred |
| Final scoring/tiebreak | Covered | Final fields harvested, hands ignored, highest coins and clockwise tiebreak |
| Serialization/returns | Mostly covered | Reward convention is source-undecided |

## Missing deterministic scenarios

- Third depletion caused by exactly the third card of phase-four draw: game must end before another turn starts.
- Third depletion caused by exactly the second phase-two reveal: phases two and three finish, then termination occurs without a phase-four action.
- First and second depletion on the exact final card of a reveal/draw batch, verifying immediate recycling state.
- Trade legality/performance with realistically accumulated hands of 10–15 cards.
- Observer-specific inspection of all trade actions, ensuring only the viewer’s own deeper cards are identified.
- Pending proposal containing a deeper hand card, observed by the active player, partner, and uninvolved player.
- Public render privacy test.
- If human-approved, a non-active player gifting a card to the active player for no return.
- Empty-discard recycle behavior after a human policy decision.

score: 0.61
confidence: high
critical_issues: 1
major_issues: 2
minor_issues: 0
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true