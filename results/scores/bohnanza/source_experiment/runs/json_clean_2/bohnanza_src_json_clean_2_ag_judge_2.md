score: 0.34  
confidence: high

The module gets inventory, setup, bean meters, basic field constraints, trade consent, and much of the four-phase structure right. However, third-depletion handling can prolong the game incorrectly, tied winners are not resolved, phase 1 permits unlimited planting, and several material trade/harvest rules are missing or contradicted.

## Findings

### Critical

1. Third deck depletion does not reliably end the game at the required boundary.

- Canonical facts: `END-01`, `END-02`, `END-05`, `DECK-01`
- Evidence type: `rule_quote` for `END-01`/`END-02`; `human_decision` for `END-05`/`DECK-01`
- Source: `RULES`, PDF page 9
- Exact evidence: “endet, sobald der Nachziehstapel zum dritten Mal leer wird”; “beim Aufdecken … spielt ihr die 2. und die 3. Phase noch zu Ende”; “Ziehst du die letzte Karte … mische die Karten des Ablagestapels.”
- Conflicting symbols: `Game._draw()` lines 162–167; `Game._finish_turn()` lines 169–180
- Expected: Depletion is recognized when the last card is drawn. On third depletion during phase 2, finish phases 2 and 3 and skip phase 4. During phase 4, stop immediately after the exhausting draw, before another player draws. First/second depletion reshuffles immediately.
- Implemented: `empty_count` increases only on a later call made while `deck` is already empty. If a draw pops the last card, the depletion is not yet recorded. In phase 4, the terminal check occurs before the draw loop, so reaching the third depletion inside that loop can still advance to a new turn. Delayed first/second reshuffles may also absorb cards discarded after the actual depletion.

This can add an extra turn and change final scores or the winner.

2. Terminal returns do not implement the mandatory tie-break winner.

- Canonical fact: `END-04`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 9
- Exact evidence: “Bei einem Gleichstand gewinnt der Spieler, der im Uhrzeigersinn am weitesten weg vom Startspieler sitzt.”
- Conflicting symbol: `Game.returns()` lines 63–64
- Expected: Among players tied for most coins, the player farthest clockwise from the original start player is the winner. A score-based return must remain equivalent to that outcome.
- Implemented: Terminal returns are raw coin totals. Tied players receive equal returns, and no other winner or tie-break calculation exists.

Thus the module reports the wrong game outcome whenever the lead is tied.

### Major

3. Phase 1 permits a third and further hand cards to be planted.

- Canonical fact: `P1-02`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 4
- Exact evidence: “Danach darfst du eine weitere … Eine dritte Bohne darfst du nicht anbauen.”
- Conflicting transition: `plant_hand` in `apply_action()` lines 125–127 and phase handling lines 84–89
- Expected: Plant the first card mandatorily, optionally the second, then phase 1 must end.
- Implemented: Every `plant_hand` action sets the phase to `plant_second`. That phase continues offering another `plant_hand`, allowing any number of front cards to be planted.

4. Inactive owners cannot harvest between steps of another player’s turn.

- Canonical fact: `HARV-01`
- Evidence type: `human_decision`
- Source: `RULES`, PDF page 7
- Exact evidence: “jederzeit … auch wenn du nicht der aktive Spieler bist”
- Conflicting symbols: `current_player()` line 61; harvest generation in `legal_actions()` lines 80–83
- Expected: Subject to protection, any owner may harvest between individual game steps, including during another player’s turn, but not inside an atomic draw or transfer.
- Implemented: Harvest actions exist only for `s.actor`. Other owners have no opportunity to harvest unless they independently become the actor.

This is an adjudication-dependent timing deviation, separate from the printed-rule contradictions.

5. Mandatory acquired cards cannot be planted in a player-chosen order.

- Canonical fact: `P3-02`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 7
- Exact evidence: “Jeder darf selbst entscheiden, in welcher Reihenfolge er die neuen Karten anbaut.”
- Conflicting symbols: `legal_actions()` lines 103–108; `plant_acquired` lines 151–153
- Expected: Each player chooses which received or retained-reveal card to plant next and may choose necessary legal harvests between cards.
- Implemented: Only `s.acquired[p][0]` may be planted. Acceptance order and retained-reveal list order therefore dictate planting order.

6. Trades cannot exchange unequal nontrivial quantities.

- Canonical fact: `TRADE-04`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 5
- Exact evidence: “Ihr dürft mit einer unterschiedlichen Kartenanzahl handeln, z. B. zwei Blaue Bohnen gegen eine Gartenbohne.”
- Conflicting symbols: offer construction lines 97–100; `pending` structure line 40; acceptance lines 139–145
- Expected: Consensual trades such as two cards for one are legal; the approved conventions exclude only unsupported contingent, delayed, multi-party, and empty-for-empty exchanges.
- Implemented: An offer contains exactly one offered card and either zero or one requested card. Two-for-one and other unequal multi-card trades are absent.

7. Accepted offers may remove the wrong card or wrong source zone.

- Canonical facts: `HAND-02`, `TRADE-02`
- Evidence type: `rule_quote`
- Sources and locators:
  - `RULES`, PDF page 3: “Die Reihenfolge … darfst du … nicht ändern … Du darfst die Karten nicht sortieren.”
  - `RULES`, PDF page 5: “mit euren Handkarten handeln … wo sich die Karten auf der Hand befinden”
- Conflicting symbols: `pending` line 40; offer recording lines 134–136; acceptance lines 139–145
- Expected: The exact selected hand position or revealed card is transferred, while the order of all remaining hand cards stays intact.
- Implemented: The proposal discards its source and index, retaining only bean names. Acceptance first removes a matching reveal regardless of the offered source; otherwise it uses `list.remove`, which removes the first matching hand bean rather than the selected position. The requested card is likewise removed by name rather than its selected index.

Duplicate bean names can therefore cause a reveal to be transferred instead of a hand card or change the remaining immutable hand order.

8. Legal actions disclose every opponent hand card to the active player.

- Canonical fact: `HAND-03`
- Evidence type: `human_decision`
- Source: `RULES`, PDF page 3
- Exact evidence: “Die erste verteilte Karte … ist die vorderste Karte.”
- Approved complete expectation: The owner sees the whole ordered hand; opponents see only its count unless the owner voluntarily communicates.
- Conflicting symbol: `legal_actions()` lines 95–100
- Expected: Opponent identities remain private unless voluntarily disclosed.
- Implemented: Every `offer_trade` action embeds `w`, the actual bean name at every index of every target’s hand. Enumerating legal actions reconstructs all opponent hands.

This is an adjudication-dependent private-information deviation.

9. The responding player’s rendered observation omits the pending offer.

- Canonical fact: `TRADE-05`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 6
- Exact evidence: “Beide Spieler müssen dem Handel zustimmen.”
- Conflicting symbols: `render()` lines 189–191; `pending` lines 40 and 136
- Expected: Acceptance is informed consent to the proposed transfer.
- Implemented: During `respond`, `render()` shows neither `pending` nor the offered/requested cards. The respondent sees only generic `accept` and `reject` actions unless given direct access to internal state.

10. Harvested three-card Ackerbohne sets are returned to the discard pile despite becoming coins.

- Canonical fact: `ACKER-03`
- Evidence type: `human_decision`
- Source: `RULES`, PDF page 11
- Exact evidence: “Erntest du ein Feld mit drei Ackerbohnen, erhältst du wie gewohnt drei Bohnentaler.”
- Conflicting transition: Acker harvest lines 116–119
- Expected: Exactly three Ackerbohnen become three coin cards and do not unlock field 3.
- Implemented: The player receives three abstract coins, but all three Ackerbohnen are also appended to `discard`.

They can consequently be reshuffled and reused, duplicating their scoring value and potentially allowing later field unlocks.

### Minor

11. Final harvesting scores fields but leaves them populated.

- Canonical facts: `END-03`, `HARV-02`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF pages 8–9
- Evidence: “Alle Spieler ernten noch ihre Bohnenfelder”; “Nach einer Ernte ist das abgeerntete Feld immer leer.”
- Conflicting transition: `_finish_turn()` lines 170–174
- Expected: All fields are harvested and emptied during terminal scoring.
- Implemented: Coin totals are increased, but field lists are not cleared. This appears unlikely to alter the already-terminal winner but leaves an observably contradictory final state.

## Rule-area coverage

| Rule area | Status | Notes |
|---|---|---|
| Setup and inventory | Covered | Correct 4–5 players, 129-card selected deck, five ordered cards, two starting fields |
| Turn order and phases | Partial | Clockwise turns present; phase 1 permits unlimited planting |
| Field legality | Covered | Same-type fields and forced legal harvest path are represented |
| Reveal and trade | Partial | Two reveals and consent present; quantities, exact identity, and information handling are defective |
| Mandatory planting | Partial | All acquired cards are forced, but order is not selectable |
| Variant drawing | Partial | Active-first clockwise one-card draws; depletion boundaries are incorrect |
| Harvest and protection | Partial | Protection and meters mostly correct; inactive timing and Acker coin-card disposition fail |
| Private information | Not conformant | Opponent hands leak through action enumeration; pending offer absent from render |
| Terminal scoring | Not conformant | Depletion timing, tie-break, and final field state are wrong |
| Returns | Not conformant | Nonterminal zeros are correct; terminal outcome omits tie-break |

## Missing deterministic scenarios

- The second phase-2 reveal draws the final card at third depletion: phases 2–3 finish, phase 4 is skipped.
- A phase-4 player draws the final card at third depletion: no later player draws and terminal scoring begins immediately.
- First/second depletion on the last owed reveal, followed by trades and harvests: only the discard existing at depletion is reshuffled.
- Plant first card, plant optional second, then verify that a third hand card is illegal.
- Acquired cards `[A, B]` where order `A→B` and `B→A` require different harvests.
- A two-for-one accepted trade.
- Trade a hand card when an identically named reveal exists.
- Trade the later of two identical hand beans and verify remaining hand order.
- Enumerate active-player legal actions without revealing opponent card identities.
- Render a pending offer from the respondent’s perspective.
- Harvest three Ackerbohnen, reshuffle the discard, and verify those coin cards cannot return.
- Equal top coin totals with multiple clockwise seat distances from the original start player.
- Final scoring verifies all fields are empty and hands do not score.

## Material questions for a human

- Is `render()` the authoritative player observation API, or are consumers expected to inspect `GameState` directly? The latter would expose every hand and all internal state; the former makes trade responses uninformed.
- Is seat 0 intentionally the configured start player for every game? If callers must be able to choose another start player, `SET-03` is not currently exposed by the constructor.

These are interface questions; the supplied rule condition itself is sufficient to decide the scored gameplay findings.

score: 0.34
confidence: high
critical_issues: 2
major_issues: 8
minor_issues: 1
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true