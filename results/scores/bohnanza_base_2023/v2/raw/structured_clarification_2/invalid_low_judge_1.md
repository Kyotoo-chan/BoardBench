Score: **0.66**, confidence: **high**. The implementation covers most ordinary play correctly, but four material discrepancies remain: depletion is detected one draw late, first/second recycling is delayed, legal actions expose private cards, and gifts can move only away from the active player.

## Findings

### Major — Third depletion is detected one draw too late

- Canonical facts: `BOHN-C-END-THIRD`, `BOHN-C-END-PHASE2-CONTINUE`, `BOHN-C-END-OUTSIDE-PHASE2-IMMEDIATE`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2
- Evidence: “Das Spiel endet, sobald der Nachziehstapel zum dritten Mal leer wird. Sollte dies beim Aufdecken der Karten in der 2. Phase passieren … werden die 2. und die 3. Phase noch zu Ende gespielt.”
- Conflicting code: `Game._draw_one`, especially the empty-deck check before `deck.pop()`; callers `apply_action:reveal` and `apply_action:draw`
- Expected: Drawing the last card makes the pile empty and immediately triggers the applicable third-depletion rule.
- Implemented: `depletions` increments only when a later draw is attempted while the deck is already empty.

Consequences include:

- If phase-two reveal consumes exactly the last two cards, the phase-two continuation condition is not recorded at reveal time. A phase-four `draw` action is subsequently exposed before termination.
- If phase four consumes exactly its final requested card, the game advances to the next player and allows phase-one actions before the next attempted draw finally detects depletion.
- Outside phase two, this contradicts the required immediate termination boundary and can change fields, payouts, and the winner.

### Major — First and second recycling occur after, rather than upon, drawing the last card

- Canonical fact: `BOHN-C-RECYCLE-FIRST-SECOND`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2
- Evidence: “Ziehst du die letzte Karte vom Nachziehstapel, mische die Karten des Ablagestapels. Danach legst du sie als neuen Nachziehstapel wieder verdeckt in die Tischmitte.”
- Conflicting code: `Game._draw_one`
- Expected: When the last card is drawn on the first or second depletion, the discard is immediately shuffled into the replacement draw pile.
- Implemented: Recycling waits until the next call to `_draw_one`. Between those calls, state and observations expose an empty deck and an unrecycled discard.

Interrupted multi-card draws usually recover on the next loop iteration, but exact-boundary reveals and draws leave the game in the wrong chance state until a later action.

### Major — Legal actions reveal every deeper opponent hand card

- Canonical fact: `BOHN-M-OBS-DEEPER-HAND`, resolved by approved private-information decision
- Evidence type: `human_decision`
- Source: `BOHN-V3-STRUCTURED-CLARIFICATION`, `canonical_supplement.md`, “Clarified digital decisions,” item 4
- Evidence: “For each opponent expose hand size and the source-visible front card, but hide deeper card identities. Legal-action data must not leak those deeper identities.”
- Conflicting code: `Game.legal_actions`, `_refs`, and the generated `trade_propose` actions
- Expected: A player sees an opponent’s hand size and front card, while deeper identities remain hidden even in legal-action data.
- Implemented: `requested_refs = self._refs(partner, "hand", state.players[partner]["hand"])` embeds every opponent card’s `bean`, position, and owner into the active player’s legal actions.

`observation_to_data` itself correctly redacts deeper identities, but the legal-action channel completely bypasses that protection.

### Major — A non-active player cannot give a card to the active player

- Canonical fact: `BOHN-C-GIFT-CONSENT`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2
- Evidence: “Als besondere Form des Handels dürft ihr euch auch Bohnenkarten schenken. Die beschenkte Person muss dem Geschenk aber zustimmen. Lehnt sie ab, kommt der Handel nicht zustande.”
- Conflicting code: `Game.legal_actions`, `trade_propose` generation
- Expected: A gift may be offered between the active player and another player in either direction, with the recipient accepting or rejecting it.
- Implemented: Every proposal requires a nonempty active-player `offered` bundle. An empty active offer with a nonempty partner bundle is never generated, so the partner cannot gift a card to the active player.

The implemented active-to-partner gift correctly requires consent; only the reverse direction is absent.

## Rule-area coverage

| Rule area | Result | Notes |
|---|---|---|
| Scope and setup | Covered | Rejects non-3–5 counts; correct deck inventory, five-card hands, field counts, seeded start |
| Hand order/information | Partial | Planting and appending preserve order; observation redaction works, but legal actions leak deeper cards |
| Phase-one planting | Covered | Mandatory first, optional second, no third, empty-hand skip, separate harvest action |
| Reveal and trading | Partial | Two-card reveal, consent, atomic transfers, unequal bundles, arbitrary positions, and explicit end present; reverse gifts absent |
| Phase-three planting | Covered | All staged/revealed cards must be planted; owners choose order; affected-player order is flexible |
| Harvesting | Covered | Off-turn actions, singleton protection, zero payout, emptying, discard, and all eight meters |
| Draw and advance | Partial | Sequential three-card append and clockwise advance work except at depletion boundaries |
| Recycling/chance | Incorrect | Depletion and shuffle are detected on the following draw attempt |
| Terminal/scoring | Partial | Final harvest, ignored hands, highest coins, and tiebreak are correct once `_finish` is invoked; invocation can be late |
| Returns | Covered | Unique rulebook winner maps to one positive return |
| State/render privacy | Question | `render()` exposes all hands; the approved decision explicitly governs observations and legal actions, not necessarily debug rendering |

## Missing deterministic scenarios

- Phase-two reveal begins with exactly two cards and causes third depletion.
- Phase-four draw consumes exactly its third and final deck card.
- First/second depletion occurs on the last requested card of a reveal or draw; assert immediate recycle state.
- Legal-action serialization viewed by the active player with known distinct opponent front/deeper cards.
- Legal-action serialization viewed by unrelated players while a proposal is pending.
- Non-active player gifts one hand card to the active player; acceptance and rejection paths.
- Exact-boundary depletion followed by an otherwise legal harvest or planting attempt, proving no extra action is admitted.
- Card-accounting scenario verifying harvested payout cards are represented consistently as coins rather than silently disappearing from card zones.

## Material questions for a human

- `BOHN-M-EMPTY-DISCARD-RECYCLE`: What should happen when a first or second depletion occurs with an empty or insufficient discard pile? The packet explicitly leaves this undecided.
- `BOHN-M-DEAL-DIRECTION`: Should the implementation’s round-robin initial deal be standardized, or remain a representation choice?
- Should the approved deeper-hand privacy rule also apply to `render()`, which currently prints every complete hand?
- Is integer coin accounting an accepted abstraction, or must state preserve explicit coin-pile card identity/conservation?

score: 0.66
confidence: high
critical_issues: 0
major_issues: 4
minor_issues: 0
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true