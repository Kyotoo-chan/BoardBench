## 1. Score

`score: 0.40` — `confidence: high`

The implementation gets the 129-card inventory, ordered hands, core planting constraints, bean yields, Ackerbohne rewards, and basic scoring mostly right. However, it contradicts several material phase and action rules: five-player setup is absent, phase 4 is fundamentally misimplemented, empty-hand planting skips phases 2–3, trades lack required consent and unequal quantities, mandatory planting order is fixed, harvesting is restricted to the current actor, and depletion is detected late.

## 2. Findings

### Major

1. Five-player play is unsupported.

- Canonical fact: `SET-01`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF pages 2 and 10
- Exact evidence: “GRUNDSPIEL (3–5 SPIELER)” and “Die Ackerbohnen könnt ihr im Spiel zu viert oder fünft einsetzen.”
- Code: `Game.initial_state`, hard-coded `range(4)`; `GameState.pending` has exactly four entries; several transitions use `% 4`.
- Expected: The selected Ackerbohne condition supports four or five players.
- Implemented: Exactly four players are representable.

2. An empty hand skips the reveal/trade and mandatory-planting phases.

- Canonical fact: `P1-04`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 5
- Exact evidence: “Hast du zu Beginn der 1. Phase keine Karten auf der Hand, gehst du gleich zur 2. Phase über.”
- Code: `legal_actions` returns `("advance",)` when the hand is empty in either `plant1` or `plant2`; `apply_action("advance")` sets `phase="draw"`.
- Expected: Proceed directly to phase 2, reveal up to two cards, trade, and plant the resulting cards.
- Implemented: Jumps directly to phase 4. This also happens when planting the mandatory first card empties the hand.

3. Phase 4 gives three cards to the active player instead of one card to every player.

- Canonical fact: `P4-01`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 10
- Exact evidence: “Anders als im Grundspiel zieht jeder von euch eine Karte vom Nachziehstapel und steckt sie hinter seine letzte Handkarte. Hierbei beginnt der aktive Spieler, die Mitspieler folgen im Uhrzeigersinn.”
- Code: `legal_actions` exposes `("draw_three",)`; `apply_action` performs three `_draw_one` calls and appends every card to `hands[ns.active]`.
- Expected: Each player draws exactly one card, active player first and then clockwise.
- Implemented: The active player alone draws three. This materially changes hands, depletion timing, and likely the winner.

4. Trading omits unequal exchanges and explicit consent.

- Canonical facts: `TRADE-04`, `TRADE-05`
- Evidence type: `rule_quote`
- Sources:
  - `RULES`, PDF page 5: “Ihr dürft mit einer unterschiedlichen Kartenanzahl handeln, z. B. zwei Blaue Bohnen gegen eine Gartenbohne.”
  - `RULES`, PDF page 6: “Beide Spieler müssen dem Handel zustimmen.”
- Code: `legal_actions` generates only one-card-for-one-card `trade` actions and single-card gifts; `apply_action` immediately removes and transfers cards. There are no proposal, acceptance, or rejection states.
- Expected: Differing nonzero quantities are legal, and a proposed exchange or gift changes no cards until the other player accepts.
- Implemented: Only 1-for-1 exchanges and one-card gifts exist, and the active actor can execute them unilaterally.

5. Players cannot choose the planting order of received cards.

- Canonical fact: `P3-02`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 7
- Exact evidence: “Jeder darf selbst entscheiden, in welcher Reihenfolge er die neuen Bohnenkarten anbaut.”
- Code: `legal_actions` and `apply_action("plant_pending")` always select `pending[p][0]`.
- Expected: Each recipient chooses which pending card to plant next, including choices that affect intervening harvests.
- Implemented: Acquisition order is mandatory.

6. Nonactive owners cannot harvest between many game steps.

- Canonical fact: `HARV-01`
- Evidence type: `human_decision`
- Source: `RULES`, PDF page 7
- Exact evidence: “Du darfst jederzeit im Spiel deine Bohnenfelder abernten, auch wenn du nicht der aktive Spieler bist.”
- Approved expectation: Owners may harvest between individual steps, including during another player’s turn, but not inside an atomic draw or transfer.
- Code: `legal_actions` constructs harvest actions only for `p = s.actor`.
- Expected: At an eligible boundary, every player may harvest their own legal field.
- Implemented: Only the current phase actor can harvest. During trade this is only the active player; during pending planting it is only the current recipient.

7. Deck depletion is detected one draw too late.

- Canonical facts: `DECK-01`, `END-01`, `END-05`
- Evidence types:
  - `DECK-01`: `human_decision`
  - `END-01`: `rule_quote`
  - `END-05`: `human_decision`
- Source: `RULES`, PDF page 9
- Exact evidence: “Ziehst du die letzte Karte vom Nachziehstapel, dann mische die Karten des Ablagestapels.” and “Das Spiel endet, sobald der Nachziehstapel zum dritten Mal leer wird.”
- Code: `_draw_one` removes and returns the last card without recording depletion. Recycling or ending occurs only on a subsequent `_draw_one` call when `deck` was already empty.
- Expected: Taking the final card immediately triggers first/second recycling or third-depletion termination. During phase 4, third depletion ends immediately after that draw.
- Implemented: A phase or even part of the next turn can proceed before depletion is recognized. Intervening discards may also be incorrectly included in a later reshuffle.

### Minor

1. Final scoring does not actually empty harvested fields.

- Canonical facts: `END-03`, `HARV-02`
- Source: `RULES`, PDF pages 8–9
- Code: `_finish` adds field yields to integer coin totals but leaves `fields` unchanged.
- Expected: Final harvest empties every field and disposes of the harvested bean cards according to harvest rules.
- Implemented: Scores are calculated, but terminal observations still show planted fields. This usually does not alter the winner.

### Questions

1. Is `GameState` intended to be an externally visible observation?

The approved `HAND-03` human decision requires an owner to see their full ordered hand while opponents see only its count. `render` exposes only counts, but callers receive a `GameState` containing all hands, and there is no player-specific observation API. If `GameState` is public game information, this is a material private-information defect; if it is trusted engine-internal state, it may be acceptable.

## 3. Rule-area coverage

| Rule area | Status | Notes |
|---|---|---|
| Inventory | Pass | Correct ten bean types and 129 cards |
| Setup | Partial | Correct four-player deal and two fields; no five-player mode |
| Ordered hands | Pass | Front planting and append-on-draw representation are correct |
| Phase 1 planting | Partial | Core first/optional-second logic works; empty-hand transition is wrong |
| Reveal | Mostly pass | Reveals up to two, subject to late depletion detection |
| Trading | Fail | Only 1-for-1, no explicit consent, immediate mutation |
| Mandatory planting | Partial | All pending cards are planted, but order cannot be chosen |
| Phase 4 draw | Fail | Three to active instead of one to every player |
| Harvest legality | Partial | Protection and yields mostly correct; timing/actor availability is wrong |
| Ackerbohne | Pass | One, two, and three-card outcomes match approved decisions |
| Recycling/depletion | Fail | Detection is delayed until the next draw attempt |
| Terminal scoring | Partial | Coin totals and tie-break work; terminal fields remain populated |
| Private information | Question | Depends on whether raw `GameState` is public |

## 4. Missing deterministic scenarios

- Four- versus five-player initialization, field counts, pending arrays, and clockwise transitions.
- Empty hand at phase-1 entry proceeds to reveal, not draw.
- Mandatory first planting that empties the hand still enters reveal/trade.
- Phase 4 gives one card to each player in exact clockwise order.
- Accepted and rejected trades leave the proper atomic state changes.
- Unequal trades such as 2-for-1, including hand and face-up cards.
- Gifts require recipient acceptance.
- Choosing different pending-card planting orders, including an intervening forced harvest.
- A nonactive player harvesting at each eligible boundary.
- Last-card depletion occurring on the final owed reveal or phase-4 draw.
- First/second depletion immediately fixing the reshuffle contents before later discards.
- Third depletion during reveal versus during each player’s phase-4 draw.
- Terminal harvest empties fields while preserving final coin totals.
- Tie-breaking with a configurable original start player.

## 5. Material questions for a human

- Is raw `GameState` trusted internal state, or must it satisfy the approved player-specific observation boundary?
- If only a four-player specialization was intentionally requested, should five-player support be excluded from the evaluation condition? The supplied approved condition itself includes both four and five players.

score: 0.40
confidence: high
critical_issues: 0
major_issues: 7
minor_issues: 1
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true