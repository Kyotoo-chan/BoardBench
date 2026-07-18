## Assessment

**Score: 0.38 — confidence: high.**

The inventory, initial deal, field counts, meters, basic four-phase structure, Ackerbohne rewards, and ordinary harvesting are largely grounded correctly. However, terminal handling can fail to end the game, tied winners are not resolved, and several material planting/trading choices are implemented incorrectly.

## Findings

### Critical

1. **Third depletion during phase 4 does not end the game**

- Canonical fact: `END-05`
- Evidence type: `human_decision`
- Source: `RULES`, PDF page 9
- Exact evidence: “Das Spiel endet, sobald der Nachziehstapel zum dritten Mal leer wird.”
- Approved adjudication: If third depletion occurs during variant phase 4, stop immediately after the draw that empties it; no remaining players draw.
- Conflicting transition: `Game._draw` and `Game._finish_turn`
- Expected: The draw emptying the pile for the third time immediately triggers final harvesting and scoring.
- Implemented: `_draw` records depletion only when another draw is attempted against an already-empty deck. `_finish_turn` checks `empty_count` only before the phase-4 draw loop and never checks it afterward. It can therefore continue attempting later players’ draws and then advance to another turn with `empty_count >= 3`.
- Impact: The game does not reliably terminate at its required endpoint.

2. **The prescribed tied winner is never determined**

- Canonical fact: `END-04`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 9
- Exact evidence: “Bei einem Gleichstand gewinnt der Spieler, der im Uhrzeigersinn am weitesten weg vom Startspieler sitzt.”
- Conflicting symbols: `GameState`, `Game.returns`, `Game._finish_turn`
- Expected: Coin ties produce a unique winner using clockwise distance from the original start player.
- Implemented: The original start player is not retained separately, and `returns()` returns identical raw coin totals for tied players. No winner or tie-break result is computed.
- Impact: A valid terminal position can report the fundamentally wrong game result.

### Major

3. **Phase 1 permits a third and unlimited additional hand cards**

- Canonical fact: `P1-02`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 4
- Exact evidence: “Danach darfst du eine weitere … Eine dritte Bohne darfst du nicht anbauen.”
- Conflicting transition: `Game.apply_action`, `plant_hand`
- Expected: Plant the first card, optionally the second, then phase 1 must end.
- Implemented: Every `plant_hand` action sets `phase="plant_second"`, including the second planting. Consequently, another `plant_hand` remains legal repeatedly until the player chooses `finish_plant` or empties the hand.

4. **Unequal multi-card trades cannot be resolved atomically**

- Canonical fact: `TRADE-04`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 5
- Exact evidence: “Ihr dürft mit einer unterschiedlichen Kartenanzahl handeln, z. B. zwei Blaue Bohnen gegen eine Gartenbohne.”
- Conflicting symbols: `legal_actions`, `offer_trade`, `pending`
- Expected: An accepted proposal may atomically exchange different nonzero quantities, such as two cards for one.
- Implemented: `pending` stores only one offered card and at most one wanted card. Gifts provide only a one-for-zero transfer. Multiple accepted offers are separate transactions and cannot model one consensual, atomic two-for-one exchange.

5. **Accepted trades may remove different cards from those proposed**

- Canonical fact: `TRADE-02`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 5
- Exact evidence: “Dabei spielt es keine Rolle, wo sich die Karten auf der Hand befinden.”
- Conflicting symbols: `legal_actions`, `offer_gift`, `offer_trade`, `apply_action("accept")`
- Expected: The exact selected hand position or revealed card transfers, while the order of all remaining hand cards is preserved.
- Implemented: Although actions contain source and index fields, acceptance ignores them and removes by bean value using `list.remove`. If duplicate bean types exist, it removes the first matching hand card rather than the selected position. If an identically named revealed card exists, it removes that reveal even when the offer designated a hand card.
- Impact: Remaining hand order and the ownership of revealed versus private cards can change incorrectly.

6. **Mandatory acquired cards cannot be planted in a chosen order**

- Canonical fact: `P3-02`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 7
- Exact evidence: “Jeder darf selbst entscheiden, in welcher Reihenfolge er die neuen Bohnenkarten anbaut.”
- Conflicting symbols: `legal_actions`, `plant_acquired`
- Expected: Each recipient selects which acquired card to plant next, including before choosing necessary harvests.
- Implemented: Only `s.acquired[p][0]` can be planted. Cards must follow acquisition-list order, with no action for selecting another card.

7. **Non-acting owners cannot exercise the approved harvest timing**

- Canonical fact: `HARV-01`
- Evidence type: `human_decision`
- Source: `RULES`, PDF page 7
- Exact evidence: “Du darfst jederzeit im Spiel deine Bohnenfelder abernten, auch wenn du nicht der aktive Spieler bist.”
- Approved adjudication: An owner may harvest between individual game steps, including during another player’s turn, but not inside an executing atomic draw or transfer.
- Conflicting symbols: `Game.current_player`, `Game.legal_actions`
- Expected: At eligible boundaries, any field owner can choose a legal harvest.
- Implemented: Harvest actions are generated only for `s.actor`. Other players have no interrupt or boundary action by which to harvest during another player’s turn.

### Minor

8. **Final harvesting changes scores but does not actually empty fields**

- Canonical fact: `END-03`
- Source: `RULES`, PDF page 9
- Evidence: “Alle Spieler ernten noch ihre Bohnenfelder.”
- Conflicting transition: `Game._finish_turn`
- The method adds field values to `coins` but leaves all field cards in place and does not move discarded or coin-side cards. This does not change the computed normal-bean total, but leaves a terminal state inconsistent with having completed the final harvest.

## Rule-area coverage

| Rule area | Status | Notes |
|---|---|---|
| Setup and inventory | Mostly correct | Correct 4–5 players, 129-card deck, five-card ordered deal, and two initial fields |
| Start player | Partial | Seat 0 is implicitly first; no explicit chosen-start marker |
| Phase order | Partial | Four phases exist, but phase-1 planting limit is broken |
| Field legality/forced harvest | Mostly correct | Same-type fields and pre-plant harvest mechanism represented |
| Reveal | Correct with terminal caveat | Two draws attempted; depletion boundary is defective |
| Trading | Material defects | Consent exists, but quantities and exact-card identity are wrong |
| Mandatory planting | Material defect | All acquired cards are planted, but not in player-chosen order |
| Variant drawing | Partial | One per player clockwise, except incorrect third-depletion handling |
| Ordinary harvesting/meters | Mostly correct | Protection and supplied meters are represented |
| Ackerbohne | Correct | One/two/three-card approved outcomes are represented |
| Private information | Partial | Acting player’s hand is shown; observation contract remains unclear |
| Terminal scoring | Material defects | Final values computed, but phase-4 termination and tie-break fail |
| Returns | Partial | Nonterminal zero and raw terminal coins; no resolved tied winner |
| Elimination | Correct | No elimination mechanism |

## Missing deterministic scenarios

- Phase 1: after exactly two successful hand plantings, verify a third `plant_hand` is illegal.
- Third depletion during phase 4 with one card remaining: verify only that card is drawn and the state immediately becomes terminal.
- Third depletion occurring exactly on the final reveal draw: verify phases 2 and 3 finish and phase 4 is skipped.
- Terminal coin tie with several tied seats: verify the farthest clockwise seat from the original starter is the sole winner.
- Atomic two-for-one and one-for-two accepted trades.
- Trade a later duplicate from a hand such as `[Red, Blue, Red]`; verify the selected duplicate is removed and the remaining order is `[Red, Blue]`.
- Offer a hand card whose bean type also appears among the reveals; verify the declared source is honored.
- Mandatory planting with two acquired bean types where reversing their order changes the necessary harvest.
- Legal harvest by a non-active, non-responding player between two atomic steps.
- Final scoring verifies all fields are empty after final harvest.
- Ackerbohne harvests at one, two without field 3, two with field 3, and exactly three.

## Material questions for a human

- Is player index 0 contractually defined as the externally chosen start player? If not, setup needs an explicit start-player input and persistent marker.
- Is `render()` the authoritative observation interface? If so, accepted/rejected decisions need the pending proposal displayed, and publicly waiting acquired cards likely need representation. The approved packet does not fully specify the renderer contract, so this is not scored.
- Should terminal state fidelity require harvested fields and associated cards to be structurally cleared, or are final scores alone sufficient for the host interface?

score: 0.38
confidence: high
critical_issues: 2
major_issues: 5
minor_issues: 1
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true