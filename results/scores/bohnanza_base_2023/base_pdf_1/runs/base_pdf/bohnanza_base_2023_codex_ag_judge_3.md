score: 0.40  
confidence: high

The inventory, setup, payout curves, ordinary planting, recycling, tie-break, and much of trading are accurately represented. However, final scoring can select the wrong winner, and legal trade enumeration becomes computationally infeasible as hands grow.

## Findings

### Critical

1. Hand cards are incorrectly converted into coins at game end.

   - Canonical fact: `BASE-SCORE-01`
   - Evidence type: `rule_quote`
   - Source: `BOHN-BASE-RULES`, PDF page 2
   - Exact evidence: “Die Karten auf der Hand zählen nicht mehr.”
   - Conflicting code: `Game._finish`; `p["coins"] += len(p["hand"])`
   - Expected: Harvest every field, ignore all remaining hand cards, then compare coin piles.
   - Implemented: Every hand card awards one coin.
   - Impact: Common end states receive substantially wrong scores and can produce the wrong winner.

2. Legal trade generation has exponential, practically unbounded growth.

   - Canonical facts: `BASE-PLANT-02`, `BASE-TRADE-03`, `BASE-DRAW-01`
   - Evidence type: `rule_quote`
   - Source: `BOHN-BASE-RULES`, PDF pages 1–2
   - Exact evidence:
     - “Danach darfst du eine weitere Bohnenkarte … anbauen.” The second planting is optional.
     - “Ihr dürft mit all euren Handkarten handeln.”
     - “Ziehe als aktive Person nacheinander drei Karten vom Nachziehstapel.”
   - Conflicting code: `Game.legal_actions`, nested `omask` and `rmask` loops over every nonempty subset of both hands.
   - Expected: Arbitrary legal offers remain representable as hands grow through repeated three-card draws.
   - Implemented: For each partner, the method eagerly constructs approximately `(2^own − 1) × (2^partner − 1)` trades. Two 15-card hands alone produce over one billion combinations.
   - Impact: Normal hand growth can make the core decision interface hang or exhaust memory, preventing reliable completion.

### Major

3. Non-active recipients do not plant traded cards during the current phase three.

   - Canonical fact: `BASE-PHASE3-01`
   - Evidence type: `rule_quote`
   - Source: `BOHN-BASE-RULES`, PDF page 2
   - Exact evidence: “Alle, die Karten quer neben ihren Feldern liegen haben, müssen diese nun anbauen. Als aktive Person musst du auch die aufgedeckten Karten anbauen …”
   - Conflicting code: `legal_actions` and `apply_action` handling of `plant_received`
   - Expected: Every recipient plants all cards received in this trading phase, choosing their own planting order, before phase four.
   - Implemented: Only `pending_received[active_player]` is processed. Other players’ cards remain staged until a later turn and may be ignored entirely if the game ends first.
   - Impact: Materially changes forced harvests, field composition, timing, and final scoring.

4. `apply_action` accepts actions outside their legal phase or actor.

   - Canonical facts: `BASE-TURN-01`, `BASE-DRAW-01`
   - Evidence type: `rule_quote`
   - Source: `BOHN-BASE-RULES`, PDF pages 1–2
   - Exact evidence:
     - “Als aktive Person führst du nacheinander vier Phasen durch …”
     - “Ziehe als aktive Person nacheinander drei Karten … Danach ist die Person links von dir am Zug.”
   - Conflicting code: `Game.apply_action`
   - Expected: Only the current phase’s legal action by its permitted actor can transition state.
   - Implemented: There is no membership or phase/actor validation. A public `Action("draw", actor)` can draw and advance the turn from another phase; similarly, forged planting or harvesting arguments bypass field and singleton legality.
   - Impact: Material phase, actor, and planting constraints are bypassable through the module’s transition API.

5. Harvesting is unavailable at two stable decision boundaries.

   - Canonical fact: `D-BASE-INTERRUPT`, grounded in `BASE-HARVEST-01`
   - Evidence type: `human_decision`
   - Source: `BOHN-BASE-RULES`; `approved_rulefacts.md`, “Approved evaluator decisions,” item 3; publisher rule on PDF page 2
   - Exact evidence:
     - Rule quote: “Du darfst jederzeit im Spiel deine Bohnenfelder abernten, auch wenn du nicht die aktive Person bist.”
     - Decision: “Represent ‘jederzeit’ harvesting at every stable player decision boundary, including off-turn, but not as an interrupt inside one atomic draw, shuffle, transfer, or planting transition.”
   - Conflicting code: `Game.legal_actions` branches for `trade_response` and `draw`
   - Expected: Eligible harvest actions are available before responding to a trade and before beginning the atomic draw action.
   - Implemented: Trade response exposes only accept/reject; draw exposes only draw.
   - Impact: Players lose explicitly approved harvest opportunities that can affect trades, field availability, and payouts.

### Minor

6. An empty hand takes an extra phase-one pass transition.

   - Canonical fact: `BASE-PLANT-03`
   - Source: `BOHN-BASE-RULES`, PDF page 1
   - Expected: If the hand is empty at phase-one start, proceed directly to phase two/reveal.
   - Implemented: The first `pass` enters `plant_second`; a second `pass` is required to reach reveal.
   - Impact: Usually only an extra no-op, although it also creates an unintended additional stable boundary.

## Rule-area coverage

| Rule area | Status | Notes |
|---|---|---|
| Inventory/setup | Covered | Correct 104 cards, counts, five-card hands, and 3-versus-2 fields |
| Hand ordering | Mostly covered | Front card and append ordering correct; empty-hand transition wrong |
| Phase-one planting | Covered | Mandatory first, optional second, no third, field matching |
| Reveal/trading | Partial | Two-card reveal and bilateral consent represented; severe enumeration issue |
| Phase-three planting | Incorrect | Only active player’s staged cards are processed |
| Drawing/recycling | Mostly covered | Three ordered draws and first/second recycle represented |
| Harvest/payouts | Partial | Curves and singleton protection correct; two boundaries omit harvesting |
| Terminal handling | Incorrect | Third depletion structure mostly correct, but hand cards become coins |
| Scoring/tie-break | Partial | Tie-break is correct; underlying coin totals are wrong |
| Private information | Covered for scored scope | Own hands and opponent hand sizes follow `D-BASE-OBS` |
| Transition legality | Incorrect | Direct calls bypass phase, actor, and argument legality |

## Missing deterministic scenarios

- Final scoring where a player with fewer real coins has more hand cards.
- Final scoring confirming every remaining hand card contributes zero.
- A trade giving cards to multiple non-active players, followed by immediate phase-three planting for each recipient.
- Third depletion during reveal followed by non-active recipients planting before termination.
- Large but reachable hands to verify trade-offer representation remains usable.
- Out-of-phase draw, wrong-actor draw, mismatched-field plant, and protected-singleton harvest rejection.
- Harvest immediately before trade acceptance/rejection.
- Harvest immediately before the atomic phase-four draw.
- Empty hand at phase-one start transitioning directly to reveal.

## Material questions for a human

- `BASE-TRADE-07` establishes consensual gifts but does not explicitly state their permitted direction. The implementation requires a nonempty offer from the active player, so it cannot represent a pure gift from a non-active player to the active player. Should gifts be legal in both directions during the active player’s trading phase?

score: 0.40
confidence: high
critical_issues: 2
major_issues: 3
minor_issues: 1
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true