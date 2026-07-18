## Review result

**Score: 0.39 — confidence: high.**

Setup, inventory, planting constraints, harvest rewards, Ackerbohne handling, ordinary clockwise turns, final scoring, and tie-breaking are substantially represented. However, the selected variant’s draw phase is materially wrong, third depletion is detected late, trading lacks explicit consent and unequal atomic exchanges, mandatory planting order is forced, voluntary harvesting is largely unavailable, and private hands are exposed.

## Findings

### Critical

1. **Third deck depletion is detected one draw request too late**

- Canonical facts: `END-01`, `END-02`, `END-05`
- Evidence type: `rule_quote` for `END-01`/`END-02`; `human_decision` for `END-05`
- Source: `RULES`, PDF page 9
- Exact evidence:
  - “Das Spiel endet, sobald der Nachziehstapel zum dritten Mal leer wird.”
  - “Sollte dies beim Aufdecken der Karten in der 2. Phase … passieren … spielt ihr die 2. und die 3. Phase noch zu Ende.”
- Conflicting symbols/transitions: `Game._draw_one`, `draw_face_up`, `draw_to_hand`
- Expected: Drawing the last card empties the pile and immediately records the depletion. A third depletion in phase 2 schedules termination after phase 3; a third depletion in phase 4 terminates immediately after that last card is drawn.
- Implemented: `_draw_one` increments `exhaustions` only when a later draw begins with an already-empty deck. Consequently, a last-card draw is not recognized as a depletion at that time.
- Impact: If a phase-4 draw consumes the last card and also completes `draw_remaining`, the game can advance to another player. That player may plant cards before the next draw request finally detects the third depletion, changing final fields and scores. This can produce the wrong winner.

### Major

2. **Variant phase 4 gives three cards to the active player instead of one card to every player**

- Canonical fact: `P4-01`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 10
- Exact evidence: “Anders als im Grundspiel zieht jeder von euch eine Karte vom Nachziehstapel und steckt sie hinter seine letzte Handkarte. Hierbei beginnt der aktive Spieler, die Mitspieler folgen im Uhrzeigersinn.”
- Conflicting symbols/transitions: `finish_phase3`, `draw_remaining = 3`, `draw_to_hand`
- Expected: Four or five draws, depending on player count; one card per player, beginning with the active player and proceeding clockwise.
- Implemented: Exactly three draws are scheduled, and every drawn card is appended to `s.players[s.active].hand`.
- Impact: Hand sizes, card distribution, deck timing, depletion timing, and later decisions all diverge every turn.

3. **Trades and gifts resolve without explicit consent, and unequal exchanges cannot be atomic**

- Canonical facts: `TRADE-04`, `TRADE-05`, `TRADE-07`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF pages 5–6
- Exact evidence:
  - “Ihr dürft mit einer unterschiedlichen Kartenanzahl handeln.”
  - “Beide Spieler müssen dem Handel zustimmen.”
  - “Der beschenkte Mitspieler muss dem Geschenk aber zustimmen.”
- Conflicting symbols/transitions: `legal_actions`, `gift`, `trade`, `apply_action`
- Expected: A proposal is followed by an explicit accept/reject choice. Accepted transfers resolve atomically. Exchanges may contain unequal numbers of cards.
- Implemented: Selecting `gift` or `trade` immediately moves cards. There is no proposal state or accept/reject action. A `trade` always exchanges exactly one card for one card.
- Impact: The active player can unilaterally transfer cards, including taking a card from an inactive player, and legal multi-card bargains such as two-for-one cannot be represented as one consensual exchange.

4. **Voluntary harvesting is unavailable at most legal timing boundaries**

- Canonical fact: `HARV-01`
- Evidence type: `human_decision`
- Source: `RULES`, PDF page 7
- Exact evidence: “Du darfst jederzeit im Spiel deine Bohnenfelder abernten, auch wenn du nicht der aktive Spieler bist.”
- Conflicting symbol: `Game.legal_actions`
- Expected: A field owner may harvest between individual game steps, including during another player’s turn, subject to protection and atomic-action boundaries.
- Implemented: `harvest` is offered only when the currently mandatory bean has no planting destination in phases 1 or 3. It is not offered voluntarily before a compatible planting, during trading boundaries, during phase 4, or to inactive owners.
- Impact: Players cannot perform strategic harvests permitted by the approved timing convention, potentially forcing different crops and rewards.

5. **Recipients cannot choose the order in which pending cards are planted**

- Canonical fact: `P3-02`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 7
- Exact evidence: “Jeder darf selbst entscheiden, in welcher Reihenfolge er die neuen Bohnenkarten anbaut.”
- Conflicting symbols: `pending`, `legal_actions` phase-3 branch, `plant_pending`
- Expected: Each recipient chooses any remaining received or revealed card as the next card to plant and may make necessary legal harvest choices between cards.
- Implemented: Only `q.pending[0]` may be planted. Cards must be planted in transfer/insertion order.
- Impact: Planting order can determine which fields must be harvested and thus materially affect coins and crop preservation.

6. **Opponent hand identities are exposed**

- Canonical fact: `HAND-03`
- Evidence type: `human_decision`
- Source: `RULES`, PDF page 3
- Exact source evidence: “Die Reihenfolge der Karten auf deiner Hand darfst du während des gesamten Spiels nicht ändern. Die erste verteilte Karte auf deiner Hand ist die vorderste Karte.”
- Approved expectation: The owner sees the full ordered hand; opponents see only its count unless information is voluntarily communicated.
- Conflicting symbols: `Game.render`, `Game.legal_actions`
- Expected: Player-relative observations conceal opponent card identities.
- Implemented:
  - `render` prints every player’s complete ordered hand.
  - During trading, `legal_actions` iterates over every opponent card and includes its bean identity in generated action arguments.
- Impact: Private information that materially guides trade and planting decisions is disclosed automatically.

## Rule-area coverage

| Rule area | Status | Notes |
|---|---|---|
| Player count/setup | Covered | Supports 4–5; two initial fields; five cards each |
| Inventory | Covered | Correct selected 129-card, ten-type deck |
| Hand order | Partly covered | Draws append and removals preserve relative order; privacy fails |
| Phase 1 planting | Covered | Mandatory first, optional second, no third |
| Reveal phase | Mostly covered | Two-step reveal represented; depletion timing is wrong |
| Trading | Contradicted | No consent state; only atomic one-for-one exchange |
| Phase 3 planting | Contradicted | All pending cards plant, but order is forced |
| Variant phase 4 | Contradicted | Three cards to active player |
| Harvest legality | Partly covered | Protection and forced harvest work; voluntary timing absent |
| Harvest rewards | Covered | Normal and Ackerbohne rewards match approved facts |
| Deck recycling | Partly covered | Reshuffling exists; depletion is registered late |
| Terminal timing | Contradicted | Late third-depletion detection can permit extra actions |
| Scoring/ties/returns | Covered | Final harvest, coins, unique clockwise tie winner, ±1 returns |
| Elimination | Covered | None implemented |

## Missing deterministic scenarios

- Third depletion caused by:
  - the first phase-2 reveal;
  - the second phase-2 reveal;
  - each player position in variant phase 4;
  - the final scheduled phase-4 draw.
- Four-player and five-player phase-4 distribution, verifying one appended card per player clockwise.
- Proposed trade accepted and rejected without premature card movement.
- Gift accepted and rejected.
- Atomic two-for-one and one-for-two trades.
- Recipient choosing different pending-card planting orders that produce different forced harvests.
- Voluntary harvest before compatible planting, between pending-card plants, and during another player’s turn.
- Player-relative observations verifying own ordered hand and opponent counts only.
- Legal five-card combinations, including retrieving one of their own newly discarded components, if such a combination mechanic is expected elsewhere; no contrary behavior was inferred here.

## Material questions for a human

- What player-facing observation API is expected? `render` and `legal_actions` currently disclose private hands, but no separate observation method exists.
- Should trade proposals identify hidden cards only after their owner voluntarily offers them, or should the interface represent offers using owner-selected indices/tokens?
- Should voluntary harvest be exposed as an interrupt-style action or as an explicit option inserted at every approved between-step boundary?

score: 0.39
confidence: high
critical_issues: 1
major_issues: 5
minor_issues: 0
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true