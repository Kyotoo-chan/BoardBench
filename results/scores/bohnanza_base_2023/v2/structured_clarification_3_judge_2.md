Score: **0.62**, confidence: **high**. The module implements most setup, field, harvest, payout, final-scoring, and ordinary phase rules correctly. However, late depletion detection can change the winner, while trading, staged-card ordering, and clarified private-information behavior are materially incomplete.

## Findings

### Critical — Draw-pile depletion is detected one draw too late

- Canonical facts: `BOHN-C-RECYCLE-FIRST-SECOND`, `BOHN-C-RECYCLE-CONTINUES-DRAW`, `BOHN-C-END-THIRD`, `BOHN-C-END-OUTSIDE-PHASE2-IMMEDIATE`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2
- Exact evidence:
  - “Ziehst du die letzte Karte vom Nachziehstapel, mische die Karten des Ablagestapels. Danach legst du sie als neuen Nachziehstapel wieder verdeckt in die Tischmitte.”
  - “Das Spiel endet, sobald der Nachziehstapel zum dritten Mal leer wird.”
- Conflicting code: `Game._draw_one`; phase-four `draw` transition in `Game.apply_action`
- Expected: Removing the last card immediately registers depletion. The first two depletions immediately recycle the then-current discard; the third ends immediately outside the phase-two exception.
- Implemented: `_draw_one` checks whether the deck is empty only before `pop()`. If a draw removes the last card, no depletion is registered until a later draw attempt.
- Impact: If phase four draws exactly the final three cards on the third depletion, the game advances to the next player’s phase one. That player may plant or harvest before termination, potentially changing final scores and the winner. First/second recycling can also happen after intervening decisions, allowing newly discarded cards into a recycle that should already have occurred.

### Major — Atomic unequal multi-card trades are not supported

- Canonical facts: `BOHN-C-TRADE-UNEQUAL`, `BOHN-C-TRADE-CONSENT`, `BOHN-C-TRADE-TRANSFER-ON-ACCEPT`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2
- Exact evidence:
  - “Ihr dürft mit einer unterschiedlichen Kartenanzahl handeln, z. B. zwei blaue Bohnen gegen eine Gartenbohne.”
  - “Denn beide beteiligten Personen müssen dem Handel zustimmen.”
- Conflicting code: `Game.legal_actions`, `trade_propose`; `Game.apply_action`, `trade_accept`
- Expected: A proposal can atomically exchange bundles such as two cards for one, with neither bundle transferring until both players accept the entire deal.
- Implemented: Every proposal has exactly one offered card and either zero or one requested card:
  - `offered=[off]`
  - `requested=[]` or `requested=[req]`
- Impact: Repeated proposals are not equivalent: each has separate consent and prior receipts cannot be retraded. In particular, one active-player card for multiple partner cards cannot be expressed.

### Major — Owners cannot choose the order of all staged cards

- Canonical fact: `BOHN-C-PLANT-OWNER-ORDER`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2
- Exact evidence: “Jede Person darf selbst entscheiden, in welcher Reihenfolge sie die neuen Bohnenkarten anbaut.”
- Conflicting code: `Game._plants`; `plant_received` branch in `Game.legal_actions`
- Expected: Each owner may choose any of their received and, for the active player, untraded revealed cards as the next card to plant.
- Implemented: `_plants` hard-codes `idx=0` for both `pending_received` and `revealed`. Players may choose a field or sometimes a source, but cannot select a later card within either staged collection.
- Impact: Forced harvests and field composition can differ materially from the player’s legal chosen ordering.

### Major — Clarified private hand information leaks through legal actions and pending proposals

This is an adjudication-dependent deviation, separate from contradictions of printed rules.

- Canonical fact: `BOHN-M-OBS-DEEPER-HAND`, resolved by approved human decision 4
- Evidence type: `human_decision`
- Source: `BOHN-V3-STRUCTURED-CLARIFICATION`, `canonical_supplement.md#clarified-digital-decisions`, item 4
- Exact evidence: “For each opponent expose hand size and the source-visible front card, but hide deeper card identities. Legal-action data must not leak those deeper identities.”
- Conflicting code: trade branch of `Game.legal_actions`; `Game.observation_to_data` field `pending`
- Expected: Opponent legal-action information exposes only hand size and front card; deeper identities remain hidden.
- Implemented: Trade generation iterates through every partner hand card and embeds its `index` and `bean` identity in `trade_propose` actions. Accepted/rejected pending proposals are also copied into every player’s observation, including those references.
- Impact: The active player—and potentially all observers—can recover every opponent’s ordered hand.

## Rule-area coverage

| Rule area | Result | Notes |
|---|---|---|
| Player counts and setup | Pass | 3–5 validation, field counts, 104-card inventory, five-card hands |
| Starting player and clockwise turns | Pass | Seeded selection and fixed start holder implemented |
| Hand order and phase-one planting | Pass | Front mandatory, second optional, no third; separate harvest available |
| Reveal and trading | Fail | Reveal/consent work; atomic multi-card bundles do not |
| Phase-three planting | Fail | All cards are forced, but owner ordering is restricted |
| Fields and anytime harvesting | Pass | Type matching, off-turn actions, singleton protection, zero payout |
| Beanometers and harvest accounting | Pass | All eight printed payout curves match |
| Draw/recycle chance flow | Fail | Depletion registered only on a later draw attempt |
| Private/public information | Fail | Base observation redacts hands, but action and pending data leak them |
| Game end and scoring | Partial | Final harvest, ignored hands, winner and tiebreak work once `_finish` runs |
| Returns | Pass | Unique tiebreak winner receives the sole positive return |

## Missing deterministic scenarios

- Third depletion when phase four begins with exactly three cards: termination must precede the next player’s phase one.
- First or second depletion caused by the final draw of an atomic draw/reveal: recycle must occur before the next stable harvest boundary.
- Third depletion during phase two with exactly two cards remaining: finish phases two and three, expose no phase-four action.
- Atomic two-for-one and one-for-two trades, including rejection leaving every zone unchanged.
- Three differently typed staged cards planted in multiple owner-selected orders.
- Active player choosing freely between received and untraded revealed cards.
- Legal-action and pending-proposal redaction with distinct deeper opponent cards.
- Winner comparison where the erroneous post-depletion planting would change the tied or leading player.

## Material questions for a human

- `BOHN-M-EMPTY-DISCARD-RECYCLE`: What should occur if a first/second recycle has no or insufficient discard cards?
- `BOHN-M-TRADE-REFERENCE-STABILITY`: Should a proposal snapshot card identities, or be invalidated when numeric references become stale?
- `BOHN-M-CONCURRENT-NEGOTIATION`: Is the implementation’s single pending proposal acceptable, and what priority should simultaneous offers have?
- Should the digital action model explicitly support a non-active player gifting a card to the active player, or only active-player-originated gift proposals? The supplied packet clearly requires consent but does not separately specify proposal direction.

```text
score: 0.62
confidence: high
critical_issues: 1
major_issues: 3
minor_issues: 0
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```