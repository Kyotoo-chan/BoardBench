## Assessment

`score: 0.28`, `confidence: high`.

The module captures much of setup, ordinary planting, trading, recycling, and tie-breaking. However, final scoring can select the wrong winner, legal-action generation becomes intractable as hands grow, and phase-three planting omits non-active recipients.

## Findings

### Critical

1. Hand cards are incorrectly converted into coins at game end.

   - Canonical fact: `BASE-SCORE-01`
   - Evidence type: `rule_quote`
   - Source: `BOHN-BASE-RULES`, PDF p. 2, “Die Karten auf der Hand zählen nicht mehr.”
   - Conflicting code: `Game._finish`, specifically `p["coins"] += len(p["hand"])`
   - Expected: harvest every field, ignore all remaining hand cards, and determine scores solely from coin-pile cards.
   - Implemented: every remaining hand card adds one coin. This can fundamentally change scores, ties, and the winner returned by `returns()`.

2. Trade-action enumeration can make an otherwise legal game practically unable to continue.

   - Canonical fact: `BASE-TRADE-03`
   - Evidence type: `rule_quote`
   - Source: `BOHN-BASE-RULES`, PDF p. 2, “Ihr dürft mit all euren Handkarten handeln. Dabei spielt es keine Rolle, wo sich die Karten auf der Hand befinden.” Also: “Ihr dürft mit einer unterschiedlichen Kartenanzahl handeln …”
   - Conflicting code: `Game.legal_actions`, nested `omask` and `rmask` loops over every nonempty subset of both hands.
   - Expected: arbitrary legal card combinations remain representable as hands grow.
   - Implemented: eagerly constructs roughly `(2^own − 1) × (2^partner − 1)` offers per partner. Since drawing three and planting at most two allows normal hand growth, this reaches millions or billions of `Action` objects in legal play, causing severe memory/time failure before a choice can be made.

### Major

3. Non-active players never plant cards they receive in trades.

   - Canonical fact: `BASE-PHASE3-01`
   - Evidence type: `rule_quote`
   - Source: `BOHN-BASE-RULES`, PDF p. 2, “Alle, die Karten quer neben ihren Feldern liegen haben, müssen diese nun anbauen. … Jede Person darf selbst entscheiden, in welcher Reihenfolge sie die neuen Bohnenkarten anbaut.”
   - Conflicting code: `Game.legal_actions` and `Game.apply_action` in phase `plant_received`; both operate only on `active_player`.
   - Expected: every trade recipient plants all staged cards, in an order chosen by that recipient; afterward the active player also plants untraded revealed cards.
   - Implemented: only the active player receives planting actions. Other players’ `pending_received` cards are ignored indefinitely, and play can advance to drawing without planting them.

4. Gartenbohne payouts are one coin too low.

   - Canonical fact: `BASE-PAY-01`
   - Evidence type: `rule_quote`
   - Source: `BOHN-BASE-RULES`, PDF pp. 1–2, graphical Gartenbohne Bohnometer: `–/2/3/–` for the 1/2/3/4-coin positions.
   - Conflicting code: `PAY["gartenbohne"] = ((2, 1), (3, 2))`
   - Expected: two Gartenbohnen pay two coins and three or more pay three coins.
   - Implemented: two pay one coin and three or more pay two. This affects harvesting, final scores, and winners.

5. `apply_action` accepts actions that contradict core legality rules.

   - Canonical fact: `BASE-PLANT-01`
   - Evidence type: `rule_quote`
   - Source: `BOHN-BASE-RULES`, PDF p. 1, “Auf einem Feld darfst du nur Bohnen der gleichen Sorte anbauen.”
   - Conflicting code: `Game.apply_action`, `plant` branch; no verification that the submitted action belongs to `legal_actions`, matches the current phase/actor, or targets an empty/same-type field.
   - Expected: an illegal plant, wrong-phase action, wrong actor, or protected harvest is rejected without changing state.
   - Implemented: a constructed `Action("plant", …)` directly pops and appends a card. It can plant mixed bean types, plant additional cards outside the permitted phase, or use another actor. Similar unchecked paths exist for harvesting, drawing, passing, and trade responses.

6. Approved off-turn harvest opportunities are missing at several stable decision boundaries.

   - Canonical decision: `D-BASE-INTERRUPT`
   - Evidence type: `human_decision`
   - Source: `approved_rulefacts.md`, “Approved evaluator decisions,” item 3: “Represent ‘jederzeit’ harvesting at every stable player decision boundary, including off-turn, but not as an interrupt inside one atomic draw, shuffle, transfer, or planting transition.”
   - Conflicting code: `Game.legal_actions` for `trade_response`, `draw`, and empty-hand `plant_first`.
   - Expected: eligible players may harvest before the responder accepts/rejects, before the atomic draw action begins, and at other stable boundaries.
   - Implemented: those phases return only response/draw/pass actions. This is an adjudication-dependent deviation from the approved interface decision, separate from printed-rule contradictions.

### Minor

7. An empty hand requires two passes instead of immediately entering reveal/trade.

   - Canonical fact: `BASE-PLANT-03`
   - Evidence type: `rule_quote`
   - Source: `BOHN-BASE-RULES`, PDF p. 1, “Hast du zu Beginn der 1. Phase keine Karten auf der Hand, gehst du gleich zur 2. Phase über.”
   - Conflicting transition: `pass` from `plant_first` moves to `plant_second`; another pass is then needed to reach `reveal`.
   - Expected: immediately skip the entire hand-planting phase.
   - Implemented: enters an unusable optional-second-card state first. This normally adds only a redundant decision.

### Question

8. Can a non-active player give cards to the active player as a gift?

   The approved facts establish that gifts are special trades requiring recipient consent, but do not explicitly identify whether either participant may be the donor. `legal_actions` supports only gifts from the active player to another player. This should not be penalized without a human interpretation.

## Rule-area coverage

| Rule area | Status | Notes |
|---|---|---|
| Inventory and player count | Covered | Correct 104-card distribution and 3–5 players |
| Initial fields/deal/start card | Covered | Correct field counts and five-card hands; seat 0 canonically represents the chosen starter |
| Hand order | Covered | Front-card removal and append-only draws preserve order |
| Phase-one planting | Mostly covered | Mandatory first, optional second, no enumerated third; empty-hand transition is redundant |
| Field constraints/forced harvest | Partially covered | Enumerated actions respect fields, but direct actions bypass legality |
| Reveal and trade | Mostly covered | Two revealed cards, active-only bilateral trade, consent, unequal quantities, staging |
| Phase-three planting | Incorrect | Non-active recipients cannot plant |
| Drawing/recycling | Covered | Three sequential draws; first two depletions recycle |
| Harvesting | Partially covered | Singleton protection and most payouts work; Garten payout and approved interrupt points do not |
| Terminal flow | Mostly covered | Third-depletion phase-two exception is represented |
| Final scoring/winner | Incorrect | Hands become coins; Garten payout may also alter results |
| Private information | Not scored | Observation follows the approved privacy decision sufficiently for fidelity scoring |
| Returns/tie-break | Covered conditionally | Tie-break is correct once coin totals are correct |

## Missing deterministic scenarios

- Final state with unequal hand sizes proving that hands add zero score.
- A final-score case where the erroneous hand conversion changes the winner.
- Two- and three-card Gartenbohne harvests, including final harvesting.
- A trade giving cards to a non-active player, followed by recipient-selected planting order.
- Multiple non-active recipients in the same trading phase.
- Direct submission of a mixed-type plant, third hand plant, wrong-actor action, protected singleton harvest, and wrong-phase draw.
- Harvest availability before trade response, before drawing, and when the active hand is empty.
- Empty-hand phase-one start reaching reveal in one transition.
- Legal-action generation with steadily growing hands, with a deterministic resource bound or lazy/parameterized trade representation.
- Gift from non-active player to active player, once donor direction is adjudicated.

## Material questions for a human

- Does the gift rule permit a non-active player to give one or more hand cards to the active player? The current approved statement does not explicitly settle donor direction.
- If so, should the action interface represent this as a requested-only proposal, or as a distinct gift proposal initiated by the active player on behalf of the prospective donor?

```text
score: 0.28
confidence: high
critical_issues: 2
major_issues: 4
minor_issues: 1
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```