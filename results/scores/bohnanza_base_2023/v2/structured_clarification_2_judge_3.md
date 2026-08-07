Score: **0.55**, confidence: **high**. Most setup, planting, harvesting, scoring, and ordinary phase sequencing match the approved facts. However, trade action generation will predictably become intractable, depletion timing can change game termination and winners, private hand identities leak, and one direction of gifting is absent.

## Findings

### Critical — Trade action enumeration grows exponentially and can make normal games unusable

- Canonical facts: `BOHN-C-TRADE-ANY-HAND-POSITION`, `BOHN-C-TRADE-UNEQUAL`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2
- Exact evidence: “Ihr dürft alle mit euren Handkarten handeln. Dabei spielt es keine Rolle, wo sich die Karten auf der Hand befinden.” Also: “Ihr dürft mit einer unterschiedlichen Kartenanzahl handeln, z. B. zwei blaue Bohnen gegen eine Gartenbohne.”
- Conflicting code: `Game.legal_actions`, `_nonempty_subsets`; the nested `offered`/`requested` loops eagerly construct every pair of nonempty subsets for every partner.
- Expected: Arbitrary legal bundles must remain usable throughout a complete game.
- Implemented: For offered and requested pools of sizes \(n\) and \(m\), it creates approximately `(2**n - 1) * (2**m - 1)` proposals per partner. On the ordinary no-trade path, hands grow by about two cards per personal turn when only one card is planted. Within several rounds this reaches millions of deeply structured `Action` objects, making `legal_actions` likely to hang or exhaust memory. This prevents reliable completion of a common legal game path.

### Major — Depletion occurs one draw too late

- Canonical facts: `BOHN-C-RECYCLE-FIRST-SECOND`, `BOHN-C-END-THIRD`, `BOHN-C-END-PHASE2-CONTINUE`, `BOHN-C-END-OUTSIDE-PHASE2-IMMEDIATE`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2
- Exact evidence: “Ziehst du die letzte Karte vom Nachziehstapel, mische die Karten des Ablagestapels.” Also: “Das Spiel endet, sobald der Nachziehstapel zum dritten Mal leer wird.”
- Conflicting code: `Game._draw_one`; depletion is incremented only when `_draw_one` begins with an already-empty deck. `Game.apply_action` stops after the prescribed two or three draws without checking whether the final draw emptied it.
- Expected: Drawing the last card immediately triggers the first/second recycle or the third-depletion end rule.
- Implemented: If the last card is exactly the second revealed card or third phase-four card, depletion is not registered. A first/second recycle is postponed until a later draw and can incorrectly include cards harvested in the interim. A third depletion can permit phase four or another player’s turn, changing fields, coins, and potentially the winner.

### Major — Legal trade actions reveal every opponent’s deeper hand cards

This is an adjudication-dependent deviation from the approved digital privacy decision, separate from printed-rule contradictions.

- Canonical fact: `BOHN-M-OBS-DEEPER-HAND`
- Evidence type: `human_decision`
- Source: `BOHN-V3-STRUCTURED-CLARIFICATION`, “Clarified digital decisions,” item 4
- Exact evidence: “For each opponent expose hand size and the source-visible front card, but hide deeper card identities. Legal-action data must not leak those deeper identities.”
- Conflicting code: `Game.legal_actions`, `_refs`; `requested_refs` is built from the partner’s complete hand and every returned reference includes its `bean`.
- Expected: An active player can see an opponent’s hand size and front card, while legal-action data conceals all deeper identities.
- Implemented: Every deeper card’s bean identity and exact index appears in generated `trade_propose` actions. `observation_to_data` itself applies the decision correctly, but legal actions bypass that protection. `render` also prints every complete hand if used as player-visible output.

### Major — A non-active player cannot give a card to the active player

- Canonical fact: `BOHN-C-GIFT-CONSENT`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2
- Exact evidence: “Als besondere Form des Handels dürft ihr euch auch Bohnenkarten schenken. Die beschenkte Person muss dem Geschenk aber zustimmen.”
- Conflicting code: `Game.legal_actions` trade-phase transition; every proposal requires a nonempty `offered` subset owned by the active player. `requested` may be empty, but `offered` cannot be empty.
- Expected: A one-way gift may go to either participant and requires the recipient’s consent.
- Implemented: The active player may give cards to a partner, but cannot accept a pure gift from that partner because every proposal must include at least one active-player card.

### Question — Empty or insufficient discard during recycling remains unresolved

- Canonical fact: `BOHN-M-EMPTY-DISCARD-RECYCLE`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2
- Exact evidence: “Ziehst du die letzte Karte vom Nachziehstapel, mische die Karten des Ablagestapels.”
- Code concern: `_draw_one` returns `(None, False)` after a nonterminal empty recycle. A second call in the same reveal/draw can count another depletion despite no intervening card being drawn.
- The approved inventory explicitly says the source does not decide insufficient-discard behavior, so this is not scored as a contradiction. A human decision is needed before specifying the correct transition.

## Coverage

| Rule area | Result | Notes |
|---|---|---|
| Setup and inventory | Covered | Counts, player range, five-card hands, field counts, seeded start |
| Hand order and planting | Covered | Mandatory first, optional second, no third, separate forced harvest |
| Reveal and trade | Failing | Exponential enumeration, privacy leak, reverse gift missing |
| Staged-card planting | Covered | All owners may act; own ordering and forced harvest represented |
| Harvesting | Covered | Anytime/off-turn boundaries, singleton protection, conservation, all meters |
| Draw and recycling | Failing | Sequential draws work, but depletion is registered late |
| Private information | Partial | Observations are filtered; legal actions and possibly `render` leak |
| Game end and scoring | Partial | Final harvest, hands ignored, winner and tiebreak work once termination occurs |
| Returns/serialization | Covered | Terminal winner utilities and schema round-trip are represented |

## Missing deterministic scenarios

- No-trade progression through several personal turns, with a bounded-time/bounded-memory assertion for `legal_actions`.
- First and second depletion where the last card is exactly the final requested reveal/draw card.
- Third depletion on exactly the second phase-two reveal, followed by phases two and three but no phase four.
- Third depletion on exactly the third phase-four draw, asserting immediate final scoring without advancing active player.
- Legal-action privacy with distinctive identities in every deeper opponent hand position.
- A non-active player gifting one card to the active player, covering both acceptance and rejection.
- After a human ruling, recycling with zero or fewer discard cards than the interrupted draw requires.

## Material questions for a human

- When a first or second recycle has no cards—or too few cards—to continue the current multi-card operation, should the operation stop, should another depletion be counted, or should some other transition occur?
- Is `render()` explicitly privileged/debug-only? If it can be shown to a player, its complete-hand output also violates the approved privacy decision.

```text
score: 0.55
confidence: high
critical_issues: 1
major_issues: 3
minor_issues: 0
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```