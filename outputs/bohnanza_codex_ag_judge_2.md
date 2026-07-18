score: 0.76
confidence: high

The implementation accurately models most inventory, planting, trade transfer, yield, reshuffle, terminal, scoring, and hand-order rules. Two material gaps remain: inactive-player harvest timing and visibility of pending trade terms.

## Findings

### Major — Inactive players cannot harvest during another player’s turn

- Canonical fact ID: `HARV-01`
- Evidence type: `human_decision`
- Source: `RULES`, PDF page 7, “Die Bohnenernte”: “jederzeit … auch wenn du nicht der aktive Spieler bist”
- Conflicting symbols: `current_player()`, `legal_actions()`, `_harvest_actions()`
- Expected: Between atomic steps, any player may become the decision-maker to harvest one of their own legal fields, including during another player’s turn.
- Implemented: Harvest actions are generated only for `state.decision`. Ordinarily that is the active player; during trade consent or phase 3 it is the currently assigned partner/planter. Other players have no way to request an allowed interrupting harvest.
- Impact: Players can be prevented from harvesting at strategically relevant times, including between mandatory plantings or before later draw/transfer steps.

### Major — A trade partner cannot observe the proposed trade before consenting

- Canonical fact ID: `TRADE-05`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 6, highlighted trade note: “beide Spieler müssen dem Handel zustimmen”
- Conflicting symbols: `TradeDraft`, `Game.render()`, transition `"Handel vorschlagen"` → `"Handel annehmen"`
- Expected: The partner’s accept/reject decision must expose the proposed cards and quantities so consent applies to an identifiable atomic transfer.
- Implemented: `render()` omits `state.trade` entirely. When control passes to the partner, the observation does not identify which active-player hand cards or revealed cards are offered, nor which cards from the partner are requested. The only trade actions are blind accept/reject.
- Impact: Consensual trading cannot be reliably evaluated through the module’s private-information observation interface.

### Minor — Final harvesting of exactly two Ackerbohnen omits the field-unlock effect

- Canonical fact ID: `ACKER-01`
- Source: `RULES`, PDF page 11: “Feld mit zwei Ackerbohnen, erhältst du ein drittes Bohnenfeld.”
- Conflicting symbol: `_finish()`
- Expected: Harvesting exactly two Ackerbohnen unlocks field 3 when absent, including as part of the final harvest.
- Implemented: `_finish()` scores two Ackerbohnen as zero but does not set `third_field` or append the field.
- Impact: Terminal state is inaccurate, although this occurs after play and cannot affect the winner.

### Question — Fixed start player

`GameState.active` always starts at seat 0, and `_finish()` assumes seat 0 for the tie-break. This is valid if seat numbering canonically assigns the chosen start player to seat 0. If callers are expected to retain independently assigned player identities, `SET-03` requires a configurable start seat.

### Question — Random state is external to `GameState`

Discard reshuffles consume the mutable `Game._rng`. Applying the same action to identical copied states may therefore produce different successors depending on earlier branch evaluation. The supplied rules require random reshuffling but do not establish whether transitions must be reproducible solely from `GameState`.

## Rule-area coverage

| Rule area | Result | Notes |
|---|---|---|
| Setup and inventory | Pass | 4–5 players, five ordered cards, two fields, exact 129-card deck |
| Turn and phase order | Pass | Four phases and clockwise advancement represented |
| Phase-1 planting | Pass | Mandatory first card, optional second, forced harvest support |
| Reveal and trading | Major gap | Transfers are atomic, but proposal terms are absent from partner observation |
| Mandatory planting | Pass | All received and retained revealed cards enter an order-selectable queue |
| Harvest timing | Major gap | No general inactive-player interrupt |
| Yields and Ackerbohne | Pass with minor terminal issue | Approved normal yields and special 1/2/3-card effects otherwise match |
| Draw and depletion | Pass | Variant draws, reshuffles, and third-depletion boundaries match approved facts |
| Private information | Pass except trade terms | Own ordered hand and opponent counts are appropriately separated |
| Terminal and returns | Pass | Final harvest, hand exclusion, coin scoring, tie-break, and returns represented |
| Elimination | Pass | None implemented |

## Missing deterministic scenarios

- An inactive player harvests between two atomic steps of another player’s turn.
- Different owners harvest between consecutive phase-3 mandatory plantings.
- A trade partner’s rendered observation identifies all offered and requested cards before accept/reject.
- A rejected trade leaves all hands, reveals, and sideways areas unchanged.
- Final harvest of exactly two Ackerbohnen when field 3 is absent.
- Third depletion on the first phase-2 reveal, followed by trading, mandatory planting, and terminal scoring without phase 4.
- Third depletion during phase 4, verifying that remaining players do not draw.
- Seeded branching around a discard reshuffle, verifying the intended chance-state reproducibility contract.
- Tie scoring with a nonzero configured start seat, if seat 0 is not an accepted canonicalization.

## Material questions for a human

- Is assigning the chosen start player to seat 0 an accepted API convention, or must the constructor accept a start-player seat?
- Must `apply_action` be a reproducible function of `GameState` and action, or may reshuffle outcomes depend on mutable game-object RNG history?
- Should the terminal state preserve mechanically irrelevant Ackerbohne field unlocks, or is winner-equivalent terminal normalization acceptable?

score: 0.76
confidence: high
critical_issues: 0
major_issues: 2
minor_issues: 1
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true
