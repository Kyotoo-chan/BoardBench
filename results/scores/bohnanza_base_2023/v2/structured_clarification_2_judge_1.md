score: 0.47  
confidence: high

The module implements most setup, planting, harvesting, scoring, and ordinary turn rules accurately. However, draw-pile depletion is detected at the wrong time, exhaustive trade generation becomes intractable during normal play, and private hand identities leak through legal actions. These defects can prevent reliable completion or materially alter the winner.

## Findings

### Critical

1. Third depletion is not detected when the final card is drawn

- Canonical facts: `BOHN-C-END-THIRD`, `BOHN-C-END-PHASE2-CONTINUE`, `BOHN-C-END-OUTSIDE-PHASE2-IMMEDIATE`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2
- Exact evidence: “Das Spiel endet, sobald der Nachziehstapel zum dritten Mal leer wird. Sollte dies beim Aufdecken der Karten in der 2. Phase passieren … werden die 2. und die 3. Phase noch zu Ende gespielt.”
- Conflicting code: `_draw_one`, lines 204–214; phase-two `reveal`, lines 250–257; phase-four `draw`, lines 282–294.
- Expected: Depletion occurs as soon as drawing the last card empties the pile. Outside phase two, final scoring begins immediately. During phase-two reveal, phases two and three finish and phase four is skipped.
- Implemented: `depletions` increments only when a later draw is attempted while the deck is already empty. If a reveal begins with exactly two cards, both are drawn without registering depletion. The code then incorrectly permits phase four. If phase four begins with exactly three cards, the code draws all three, advances to the next player, and allows another turn to start before detecting the third depletion.
- Impact: Extra planting, harvesting, trading, or revealing can occur and alter final scores and the winner.

2. Exhaustive trade-action materialization becomes intractable during ordinary play

- Canonical facts: `BOHN-C-TRADE-ANY-HAND-POSITION`, `BOHN-C-TRADE-UNEQUAL`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2
- Exact evidence: “Ihr dürft alle mit euren Handkarten handeln. Dabei spielt es keine Rolle, wo sich die Karten auf der Hand befinden.” Also: “Ihr dürft mit einer unterschiedlichen Kartenanzahl handeln.”
- Conflicting code: `_nonempty_subsets` and `legal_actions`, lines 135–139 and 167–178; `apply_action` membership validation, line 228.
- Expected: Arbitrary legal bundles remain usable throughout a complete game.
- Implemented: Every subset of the active player’s hand plus revealed cards is crossed with every subset of each partner’s hand and instantiated as an `Action`. With ten active cards, two revealed cards, and ten partner cards, this produces roughly 4.2 million proposals per partner. Hands naturally grow because players can plant one card and draw three. `apply_action` regenerates the entire list merely to validate membership.
- Impact: Memory or runtime exhaustion is likely well before a normal game finishes, creating a common effective deadlock.

### Major

3. First and second depletion recycling is delayed and can include cards discarded too late

- Canonical facts: `BOHN-C-RECYCLE-FIRST-SECOND`, `BOHN-C-RECYCLE-CONTINUES-DRAW`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2
- Exact evidence: “Ziehst du die letzte Karte vom Nachziehstapel, mische die Karten des Ablagestapels. Danach legst du sie als neuen Nachziehstapel wieder verdeckt in die Tischmitte.”
- Conflicting code: `_draw_one`, lines 204–214.
- Expected: Immediately after the last card is drawn, the then-current discard pile becomes the new shuffled draw pile.
- Implemented: Recycling waits until another draw is requested. When the final requested reveal card empties the deck, trading, planting, and harvesting may happen before recycling. Cards discarded during those later actions are consequently added to a recycle for which they were not yet eligible.
- Impact: The composition and chance distribution of the next draw pile are materially wrong.

4. Legal-action data reveals every opponent’s deeper hand identities

- Canonical fact: `BOHN-M-OBS-DEEPER-HAND`, resolved by the approved private-information decision
- Evidence type: `human_decision`
- Source: `BOHN-V3-STRUCTURED-CLARIFICATION`, “Clarified digital decisions,” item 4
- Exact evidence: “For each opponent expose hand size and the source-visible front card, but hide deeper card identities. Legal-action data must not leak those deeper identities.”
- Conflicting code: `_refs` and trade action generation, lines 131–133 and 167–177.
- Expected: An opponent’s front card and hand size are visible; deeper identities remain hidden, including in legal-action data.
- Implemented: `requested_refs` is built from every partner hand card and includes its `bean` value. All combinations are returned in `trade_propose` actions, revealing the partner’s complete ordered hand to the active player.
- Impact: Private information central to trading decisions is exposed.

5. A non-active player cannot give a one-way gift to the active player

- Canonical fact: `BOHN-C-GIFT-CONSENT`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2
- Exact evidence: “Als besondere Form des Handels dürft ihr euch auch Bohnenkarten schenken. Die beschenkte Person muss dem Geschenk aber zustimmen. Lehnt sie ab, kommt der Handel nicht zustande.”
- Conflicting code: `legal_actions`, lines 167–177.
- Expected: A gift between the active player and another player transfers cards in either direction, subject to the recipient’s consent.
- Implemented: Every proposal must contain at least one card offered by the active player. Only active-to-partner one-way gifts are generated; a proposal with an empty active offer and a nonempty partner gift is impossible.
- Impact: A source-legal material trade option is absent.

### Minor

6. Phase four is never represented as the live phase

- Canonical fact: `BOHN-C-PHASES`
- Source: `BOHN-BASE-2023-RULES`, PDF page 1
- Code: `legal_actions`, lines 179–193; `apply_action`, lines 280–294.
- Expected: State proceeds from phase three to phase four before the three-card draw.
- Implemented: Once staged cards are exhausted, a `draw` action is emitted while `state.phase` remains `plant_received`. The declared `"draw"` phase is unreachable through normal transitions.
- Impact: The observation reports the wrong phase at a localized boundary, although the draw itself otherwise occurs.

### Question

7. Empty or insufficient discard supply can count repeated depletions without drawing cards

- Canonical fact: `BOHN-M-EMPTY-DISCARD-RECYCLE`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2
- Evidence: The rule instructs players to shuffle the discard pile after drawing the last card but does not specify what happens when it contains too few cards.
- Code: `_draw_one`, lines 204–214. An empty recycle returns `(None, False)`; another iteration may immediately increment `depletions` again.
- The packet expressly leaves this case undecided. A human decision is required before determining the correct transition.

## Rule-area coverage

| Rule area | Status | Notes |
|---|---|---|
| Player counts and setup | Pass | Correct 3–5 validation, 104-card inventory, deal sizes, fields, seeded start |
| Hand order and phase one | Pass | Mandatory first, optional second, no third, separate forced harvest |
| Reveal and trading | Partial | Consent and atomic staging work; gift direction missing; exponential enumeration |
| Phase-three planting | Pass | All staged cards required; owner and inter-player ordering supported |
| Phase-four draw | Partial | Sequential append works; phase label and depletion timing do not |
| Harvesting | Pass | Off-turn boundaries, singleton protection, conservation by count, and meters correct |
| Chance and recycling | Fail | Recycling occurs one attempted draw late |
| Private information | Fail | Observation is filtered, but legal actions expose deeper hands |
| Terminal conditions | Fail | Exact-boundary third depletion can permit extra play |
| Final scoring and returns | Pass | Final harvest, ignored hands, highest coins, and clockwise tiebreak are correct |

## Deterministic scenarios to add

- Third depletion during phase-two reveal with exactly two cards remaining: complete phases two and three, never phase four.
- Third depletion during phase-four draw with exactly three cards remaining: finish immediately after the third card, without advancing players.
- First and second depletion where the final requested card empties the pile: snapshot the discard contents before later harvesting can add cards.
- Trade legal-action inspection proving that no deeper opponent identity appears.
- A one-way gift from a non-active player to the active player, including acceptance and rejection.
- Large-hand trade validation using a compact proposal representation, without enumerating the complete power set.
- Explicit phase transition from `plant_received` to `draw`.

## Material questions for a human

- What should happen when a first or second depletion has an empty or insufficient discard pile?
- Is `render()` explicitly privileged/debug-only? It prints every complete hand and would violate the approved privacy policy if exposed to a player.

```text
score: 0.47
confidence: high
critical_issues: 2
major_issues: 3
minor_issues: 1
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```