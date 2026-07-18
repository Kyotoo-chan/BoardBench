## 1. Assessment

`score: 0.36`  
`confidence: high`

The module models the 129-card Ackerbohne deck, initial hands and fields, basic phase order, bean meters, protection rule, and Ackerbohne rewards reasonably well. However, third-depletion handling can permit an extra turn, and several material rules are missing or contradicted: configurable start player, unequal trades, exact traded-card identity, private information, planting-order choice, out-of-turn harvesting, and tie-break resolution.

## 2. Findings

### Critical — Third depletion does not terminate at the required boundary

- Canonical facts: `END-01`, `END-02`, `END-05`
- Evidence types:
  - `END-01`: `rule_quote`
  - `END-02`: `rule_quote`
  - `END-05`: `human_decision`
- Source: `RULES`, PDF page 9
- Exact evidence:
  - “Das Spiel endet, sobald der Nachziehstapel zum dritten Mal leer wird.”
  - “Sollte dies beim Aufdecken der Karten in der 2. Phase … passieren … spielt ihr die 2. und die 3. Phase noch zu Ende.”
  - Approved `END-05`: if third depletion occurs during phase 4, stop immediately after the draw that empties the pile; no remaining player draws.
- Conflicting code: [`Game._draw` and `Game._finish_turn`](C:/Users/benti/AppData/Local/Temp/.ctx-mode-e049j4/boardbench_judge_packet_b2gaw7cp/implementation.py:162)
- Expected: Detect depletion when a draw removes the final deck card. In phase 2, finish phases 2–3; in phase 4, terminate immediately.
- Implemented: `_draw` increments `empty_count` only when called while the deck is already empty. If a draw removes the final card, depletion is not recognized until the next attempted draw. During phase 4, `_finish_turn` checks terminality only before its draw loop and does not recheck afterward, so it can advance to another turn after the third depletion. That extra turn can change card ownership, fields, and the winner.

### Major — Unequal multi-card trades cannot be represented

- Canonical facts: `TRADE-04`, supported by `TRADE-05`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF pages 5–6
- Exact evidence:
  - “Ihr dürft mit einer unterschiedlichen Kartenanzahl handeln, z. B. zwei Blaue Bohnen gegen eine Gartenbohne.”
  - “Beide Spieler müssen dem Handel zustimmen.”
- Conflicting code: `Game.legal_actions`, `offer_trade`, `pending`, and `Game.apply_action`
- Expected: A single consensual, atomic trade may exchange different nonzero quantities, such as two cards for one.
- Implemented: Every `offer_trade` contains exactly one offered card and one wanted card. Gifts permit 1-for-0, but sequential gifts/trades cannot implement a single atomic 2-for-1 agreement.

### Major — Accepted trades can transfer a different card from the one proposed

- Canonical facts: `TRADE-02`, `TRADE-05`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF pages 5–6
- Exact evidence:
  - “Dabei spielt es keine Rolle, wo sich die Karten auf der Hand befinden.”
  - “Ziehe eine Karte erst aus der Hand, sobald der Handel auch wirklich zustande kommt.”
- Conflicting code: `offer_gift`, `offer_trade`, `pending`, and the `accept` branch
- Expected: The exact selected source and hand position are transferred atomically; removing that card preserves the relative order of all remaining hand cards.
- Implemented: Although proposals contain source and index, `pending` retains only bean names. Acceptance uses:
  - `if offered in s.revealed` before considering its proposed source;
  - `list.remove(bean)` for hands.
  
  Thus a proposed hand card can instead remove an identical revealed card, and selecting a later duplicate in a hand removes the first matching duplicate.

### Major — Acquired-card planting order is forced

- Canonical fact: `P3-02`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 7
- Exact evidence: “Jeder darf selbst entscheiden, in welcher Reihenfolge er die neuen Bohnenkarten anbaut.”
- Conflicting code: `Game.legal_actions` and `plant_acquired`
- Expected: Each player selects which received or retained revealed card to plant next, including before choosing any necessary harvest.
- Implemented: Only `s.acquired[p][0]` can be planted. The implementation fixes the order according to transaction/insertion history.

### Major — Most owners cannot exercise the approved out-of-turn harvest right

- Canonical fact: `HARV-01`
- Evidence type: `human_decision`
- Source: `RULES`, PDF page 7
- Exact evidence: “Du darfst jederzeit im Spiel deine Bohnenfelder abernten, auch wenn du nicht der aktive Spieler bist.”
- Approved expectation: An owner may harvest between individual steps, including during another player’s turn, but not inside an atomic draw or transfer.
- Conflicting code: `Game.current_player`, `Game.legal_actions`, and actor-based harvest generation
- Expected: Any player with a legal field can initiate a harvest at an approved step boundary.
- Implemented: Harvest actions are generated only for `s.actor`. During trade this is the active player or current respondent, and during mandatory planting it is the current recipient. Other owners have no action path to harvest.

This is an adjudication-dependent contradiction of the approved human timing decision, separate from the printed-rule contradictions above.

### Major — Legal actions disclose opponents’ private hands

- Canonical fact: `HAND-03`
- Evidence type: `human_decision`
- Source: `RULES`, PDF page 3
- Exact evidence: “Die erste verteilte Karte auf deiner Hand ist die vorderste Karte. Sie ist komplett sichtbar.”
- Approved expectation: A player sees their own ordered hand; opponents see only its card count unless information is voluntarily communicated.
- Conflicting code: `Game.legal_actions`, especially `for j,w in enumerate(s.hands[target])`
- Expected: Trade negotiation must not automatically reveal every opponent card and its position.
- Implemented: The active player’s legal `offer_trade` actions enumerate the exact bean and index of every card in every target hand. Hiding those hands in `render` does not prevent this action-list leak.

This is also an adjudication-dependent contradiction of an approved human information decision.

### Major — Start-player selection is absent

- Canonical fact: `SET-03`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 2
- Exact evidence: “Bestimmt einen Startspieler. Er erhält die Startspielerkarte.”
- Conflicting code: `Game.__init__`, `GameState.active`, and `Game.initial_state`
- Expected: One configured or chosen player acts first and remains the original marker holder.
- Implemented: Seat 0 is always the start player; neither constructor nor setup state accepts a start-player choice. No marker holder is represented independently.

### Major — Tied games have no implemented winner resolution

- Canonical fact: `END-04`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 9
- Exact evidence: “Bei einem Gleichstand gewinnt der Spieler, der im Uhrzeigersinn am weitesten weg vom Startspieler sitzt.”
- Conflicting code: `Game.returns` and the absence of a winner/result computation
- Expected: Equal coin totals are resolved by greatest clockwise distance from the original start player.
- Implemented: `returns` returns raw coin totals only. No result method or documented return transformation applies the tie-break, so tied players remain indistinguishable as winners.

### Minor — Final harvesting awards coins but leaves fields populated

- Canonical facts: `END-03`, `HARV-02`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF pages 8–9
- Evidence: “Alle Spieler ernten noch ihre Bohnenfelder” and “Nach einer Ernte ist das abgeerntete Feld immer leer.”
- Conflicting code: terminal branch of `Game._finish_turn`
- Expected: Final harvests empty the fields after awarding coins.
- Implemented: Coin totals are increased, but field cards remain in place. This does not usually alter the computed score, but terminal state is inconsistent with a completed harvest.

## 3. Rule-area coverage

| Rule area | Status | Notes |
|---|---|---|
| Player count and inventory | Pass | 4–5 players; correct ten types and 129 cards |
| Initial hands and fields | Partial | Correct five cards/two fields; start player fixed |
| Hand planting | Pass | Mandatory first, optional second, forced harvest available |
| Reveal phase | Partial | Two draws attempted; depletion boundary incorrect |
| Trading | Fail | No unequal quantities; card identity bug |
| Mandatory planting | Fail | All cards planted, but order is forced |
| Phase-4 draws | Fail | Correct nominal order; immediate terminal boundary absent |
| Harvest meters/protection | Pass | Supplied thresholds and singleton protection represented |
| Ackerbohne | Pass | Two unlock field 3; three give three coins |
| Private information | Fail | Opponent hands leak through legal actions |
| End and scoring | Fail | Extra turn possible; tie-break absent |
| Returns | Partial | Nonterminal zero and raw terminal coins, but no winner adjudication |

## 4. Missing deterministic scenarios

Add deterministic scenarios for:

1. Third depletion caused by the second phase-2 reveal.
2. Third depletion caused by an actual phase-4 draw that removes the last card.
3. First/second depletion between two owed reveal draws, including reshuffle and continuation.
4. Atomic 2-for-1 and 1-for-2 trades.
5. Offering a hand card when an identical bean is also revealed.
6. Trading the later of two separated, identical hand cards and verifying remaining order.
7. Choosing acquired cards in two different legal planting orders.
8. A non-actor harvesting between another player’s planting steps.
9. Legal-action observation proving that opponent bean identities remain hidden.
10. Equal final scores resolved by clockwise distance from a nonzero start player.
11. Final harvest verifying both scores and emptied fields.
12. Exactly two Ackerbohnen unlocking field 3, including during final harvest.

## 5. Material questions for a human

- Is an external adapter intended to remap a chosen start player onto internal seat 0? No such adapter is supplied here.
- Is an external result layer intended to apply `END-04` to raw coin returns? The reviewed module itself does not do so.
- Does the execution framework provide viewer-specific legal-action filtering? Without it, opponent hands are disclosed even though `render` masks them.

These are integration questions, not unresolved rulebook questions, and do not introduce additional penalties.

```text
score: 0.36
confidence: high
critical_issues: 1
major_issues: 7
minor_issues: 1
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true
```