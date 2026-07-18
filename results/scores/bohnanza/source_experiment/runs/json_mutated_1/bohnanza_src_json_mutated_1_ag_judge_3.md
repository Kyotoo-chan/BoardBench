score: 0.52  
confidence: high

The setup, inventory, ordered-hand planting, most trading constraints, ordinary harvest tables, turn order, and winner tie-break are substantially represented. However, six material contradictions affect the selected variant, trade resolution, harvesting rights, deck timing, and terminal scoring visibility.

## Findings

### Major — two Ackerbohnen incorrectly award two coins

- Canonical fact: `ACKER-01`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 11
- Exact evidence: “Erntest du ein Feld mit zwei Ackerbohnen, erhältst du ein drittes Bohnenfeld. Die dazu gehörende Bohnenfeld-Ablage legst du auf die Seite mit drei Bohnenfeldern. Die geernteten Ackerbohnen legst du auf den Ablagestapel.”
- Conflicting symbol: `Game._harvest`
- Expected: Exactly two Ackerbohnen unlock the third field, if absent, and both cards are discarded; they award zero coins.
- Implemented: `value = 2` when the player has two fields, so the player both unlocks field 3 and receives two coins. Those two cards are consequently withheld from the discard pile as coin cards.
- Impact: This directly changes scores and can change the winner in the defining Ackerbohne variant.

### Major — traded cards received by inactive players are never planted

- Canonical fact: `P3-01`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 7
- Exact evidence: “Alle Spieler, die Karten quer neben ihren Feldern liegen haben, müssen diese nun anbauen.”
- Conflicting symbols/transitions: `current_player`, `legal_actions` in phase `plant_incoming`, and `finish_incoming`
- Expected: Every player must plant all cards received in trades; each recipient controls their planting order and necessary harvest choices.
- Implemented: During `plant_incoming`, `current_player` always returns `s.active`. Only the active player can plant `incoming`. `finish_incoming` then advances directly to `draw_each`, leaving every other recipient’s traded cards permanently stranded.
- Impact: Accepted trades routinely fail to resolve their mandatory planting consequences.

### Major — draw-pile depletion is detected one draw too late

- Canonical facts: `DECK-01`, `END-01`, `END-05`
- Evidence type: `human_decision`
- Source: `RULES`, PDF page 9
- Exact evidence: “Ziehst du die letzte Karte vom Nachziehstapel, dann mische die Karten des Ablagestapels.” and “Das Spiel endet, sobald der Nachziehstapel zum dritten Mal leer wird.”
- Conflicting symbol: `Game._draw`
- Expected: Depletion occurs when a draw removes the final card. On the first two depletions, the then-current discard pile is reshuffled immediately; on the third, the specified end timing begins immediately.
- Implemented: `empty_count` increases only when `_draw` starts with an already-empty deck. Popping the last card does not register depletion.
- Impact:

  - A phase-4 draw that empties the deck can incorrectly allow another player or another turn to proceed.
  - Discards added after the pile actually emptied can be included in a delayed reshuffle, changing the chance state.
  - A second reveal that removes the final card can fail to set `terminal_pending`.

### Major — Weinbrandbohne uses the wrong Bohnometer

- Canonical fact: `GOLD-09`
- Evidence type: `user_observation`
- Source: `COMPONENTS`, JSON Pointer `/bohnen/9/ernte`
- Exact evidence: `4→1, 7→2, 9→3, 11→4`
- Conflicting symbol: `BEANS["Weinbrandbohne"]`
- Expected: Zero below 4; then 1/2/3/4 coins at 4/7/9/11+.
- Implemented: 1/2/3/4 coins at 2/4/6/8+.
- Impact: A common 22-card bean type is substantially overvalued throughout the game.

### Major — most non-active players cannot exercise the approved harvest timing

- Canonical fact: `HARV-01`
- Evidence type: `human_decision`
- Source: `RULES`, PDF page 7
- Exact evidence: “Du darfst jederzeit im Spiel deine Bohnenfelder abernten, auch wenn du nicht der aktive Spieler bist.”
- Conflicting symbols: `legal_actions`, `current_player`, `_harvest_actions`
- Expected: A field owner may explicitly harvest between atomic steps during another player’s turn.
- Implemented: Harvest actions are generated only for `current_player(s)`. Ordinarily that is the active player; during a submitted offer it is only the offer target, and during phase 4 it is only the next player drawing.
- Impact: Legal defensive or preparatory harvests by other owners are absent.
- Provenance note: The precise “between atomic steps” boundary is an approved human adjudication, so this deviation is separate from contradictions of unambiguous printed mechanics.

### Major — terminal raw coin totals are not exposed

- Canonical fact: `END-03`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 9
- Exact evidence: “Alle Spieler ernten noch ihre Bohnenfelder und erhalten gegebenenfalls dafür Bohnentaler. Die Karten auf der Hand zählen nicht mehr. Jeder zählt die Karten in seinem Talerstapel.”
- Conflicting symbols: `returns`, `render`
- Expected: Final fields are harvested, hands score zero, and raw final coin totals remain observable.
- Implemented: `returns` harvests only a private deep copy and exposes winner-based `+1/-1`. The terminal state and `render(s)` retain pre-final fields and pre-final coin totals, with no public final-score result.
- Impact: The winner can be returned, but consumers cannot directly observe or audit the required final coin totals.

No critical or minor findings were identified.

## Rule-area coverage

| Rule area | Status | Notes |
|---|---|---|
| Setup and inventory | Covered | 4–5 players, five cards, two fields, and the 129-card selected deck are correct. |
| Ordered private hands | Mostly covered | Ordered hands and append-only draws work; observer-specific rendering remains an interface question. |
| Phase 1 planting | Covered | Mandatory first, optional second, no third; explicit harvest can clear space. |
| Reveal and trading | Mostly covered | Active-player-only, consensual, unequal trades and gifts are supported. |
| Mandatory phase-3 planting | Contradicted | Only the active player plants received cards. |
| Phase-4 drawing | Mostly covered | One clockwise draw each is modeled; depletion timing is wrong. |
| Ordinary harvesting | Mostly covered | Protection and most payout tables are correct; Weinbrand and non-active timing are not. |
| Ackerbohne | Contradicted | Two-card harvest incorrectly awards two coins. |
| Terminal conditions | Contradicted | Third depletion is registered late. |
| Results and tie-break | Partial | Tie-break works for start seat 0; raw final totals are unavailable. |
| Returns | Covered except observability | Nonterminal zero and terminal winner returns are supported. |

## Missing deterministic scenarios

- Harvest exactly two Ackerbohnen both before and after field 3 has been unlocked.
- Verify Ackerbohne harvests of one, two, and three cards for coins, discard contents, and field count.
- Accept a trade that gives cards to an inactive player, then require that player to plant every received card.
- Give incoming cards to multiple inactive recipients in one trading phase.
- Exercise every Weinbrand threshold: 3, 4, 6, 7, 8, 9, 10, and 11 cards.
- Empty the deck on the first versus second reveal card at each depletion count.
- Empty the deck on each participant’s phase-4 draw, especially before the last participant.
- Confirm that only the discard existing at first/second depletion enters the reshuffle.
- Allow each non-active owner to harvest between atomic actions.
- Verify terminal observable coin totals, final harvests, hand exclusion, and tied-winner selection.

## Material questions for a human

- Is assigning the chosen start player to seat 0 an accepted calling convention, or must `Game` expose an explicit start-player parameter?
- Is `render` intended as the complete observation API? If so, it has no viewer argument and cannot give every player their own hand while masking it from opponents.
- Should terminal scoring mutate or expose a derived terminal state, or is a separate public `scores()`-style result acceptable? The current interface provides neither.

```text
score: 0.52
confidence: high
critical_issues: 0
major_issues: 6
minor_issues: 0
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true
```