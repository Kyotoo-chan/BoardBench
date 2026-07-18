## Assessment

`score: 0.34` — `confidence: high`

The inventory, ordered-hand mechanics, normal harvest payouts, Ackerbohne rewards, field protection, clockwise turn advancement, and winner calculation are substantially aligned. However, several central phase and action rules are materially wrong: five-player play is unavailable, empty hands skip two phases, variant drawing follows the wrong distribution, trading lacks consent and unequal exchanges, pending-card order is forced, out-of-turn harvesting is unavailable, and depletion is detected late.

## Findings

No critical findings.

### Major 1 — Five-player setup is unsupported

- Canonical fact: `SET-01`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 2
- Exact evidence: “GRUNDSPIEL (3–5 SPIELER)”
- Approved expectation: The selected Ackerbohne condition supports four or five players.
- Conflicting code: `Game` documentation and `initial_state()` lines 51, 59–65; fixed four-element defaults in `GameState.pending`; repeated `range(4)`.
- Expected: Configurable four- or five-player setup, with five hands, fields, coin totals, pending areas, and turn seats when selected.
- Implemented: The state and all transitions are structurally fixed to four players.

### Major 2 — An empty hand skips phases 2 and 3

- Canonical facts: `P1-04`, `TURN-02`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF pages 5 and 4
- Exact evidence: “Hast du zu Beginn der 1. Phase keine Karten auf der Hand, gehst du gleich zur 2. Phase über.”; “führst du nacheinander vier Phasen durch”
- Conflicting transition: `legal_actions()` line 87 returns `("advance",)`; `apply_action()` line 142 changes directly to `phase="draw"`.
- Expected: An empty hand skips only phase-1 planting and proceeds to the two-card reveal/trade phase.
- Implemented: It jumps directly to phase 4, omitting reveal, trade, and mandatory planting. The same error occurs when the mandatory first planting empties the hand before optional planting.

### Major 3 — Variant phase-4 cards all go to the active player

- Canonical fact: `P4-01`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 10
- Exact evidence: “zieht jeder von euch eine Karte vom Nachziehstapel und steckt sie hinter seine letzte Handkarte. Hierbei beginnt der aktive Spieler, die Mitspieler folgen im Uhrzeigersinn.”
- Conflicting code: `legal_actions()` line 114 and `apply_action()` lines 172–177, particularly `draw_three` and `s.hands[ns.active]`.
- Expected: Each player draws one card, active player first and then clockwise, appending to that player’s hand.
- Implemented: Three cards are drawn sequentially and all appended to the active player’s hand. In a five-player game, which is itself unsupported, five one-card draws would be required.

### Major 4 — Trade quantities and consent are not represented

- Canonical facts: `TRADE-04`, `TRADE-05`, `TRADE-07`
- Evidence type: `rule_quote`
- Sources:
  - `RULES`, PDF page 5: “Ihr dürft mit einer unterschiedlichen Kartenanzahl handeln”
  - `RULES`, PDF page 6: “beide Spieler müssen dem Handel zustimmen”
  - `RULES`, PDF page 6: “Bohnenkarten schenken … Der beschenkte Mitspieler muss dem Geschenk aber zustimmen.”
- Conflicting code: `legal_actions()` lines 95–107 and immediate transfer transitions at lines 149–161.
- Expected: A proposal may exchange unequal nonempty quantities, followed by an explicit accept or reject decision; gifts also require recipient consent. Cards remain in place until acceptance.
- Implemented: A trade is limited to exactly one card for one card and executes immediately. Gifts also execute immediately through the active actor, without a recipient decision. Sequencing a 1:1 transfer and gift is not an atomic consensual unequal trade.

### Major 5 — Only the current actor can harvest

- Canonical fact: `HARV-01`
- Evidence type: `human_decision`
- Source: `RULES`, PDF page 7
- Exact evidence: “Du darfst jederzeit im Spiel deine Bohnenfelder abernten, auch wenn du nicht der aktive Spieler bist.”
- Approved human decision: An owner may harvest between individual game steps, including during another player’s turn, but not inside an executing atomic draw or transfer.
- Conflicting code: `legal_actions()` lines 83–85 constructs harvest actions only for `p = s.actor`.
- Expected: At temporal boundaries, every player should be able to harvest their own eligible field.
- Implemented: Only the current planting/trading actor can harvest. Inactive owners cannot exercise the approved out-of-turn action.

This is an adjudication-dependent deviation from the approved timing decision, not solely a contradiction inferred from the printed word “jederzeit.”

### Major 6 — Mandatory planting order is forced

- Canonical fact: `P3-02`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 7
- Exact evidence: “Jeder darf selbst entscheiden, in welcher Reihenfolge er die neuen Bohnenkarten anbaut.”
- Conflicting code: `legal_actions()` lines 111–113 and `apply_action()` lines 165–167 always select and remove `pending[p][0]`.
- Expected: Each recipient explicitly chooses which pending received or retained revealed card to plant next, including before deciding on a necessary harvest.
- Implemented: Cards must be planted in acquisition order.

### Major 7 — Depletion and reshuffling are detected one draw late

- Canonical facts: `DECK-01`, `END-01`, `END-02`, `END-05`
- Evidence types: `human_decision` for `DECK-01`/`END-05`; `rule_quote` for `END-01`/`END-02`
- Sources:
  - `RULES`, PDF page 9: “Ziehst du die letzte Karte vom Nachziehstapel, dann mische die Karten des Ablagestapels.”
  - `RULES`, PDF page 9: “Das Spiel endet, sobald der Nachziehstapel zum dritten Mal leer wird.”
  - `RULES`, PDF page 9: “spielt ihr die 2. und die 3. Phase noch zu Ende”
- Conflicting code: `_draw_one()` lines 191–197 returns the last card without recording depletion; depletion is recognized only on a later call made with an already-empty deck.
- Expected:
  - First and second depletion immediately reshuffle the discard present when the final card is drawn.
  - Third depletion during phase 2 finishes phases 2 and 3 and skips phase 4.
  - Third depletion during phase 4 becomes terminal immediately after the draw that empties the pile.
- Implemented: Reshuffling/ending waits for another requested draw. Intervening harvest discards can incorrectly enter the reshuffle, and terminal state can require a later `draw_three` action even though the third depletion already occurred.

This finding includes approved human timing decisions; the underlying “third time empty” and phase-2 completion requirements are also explicit printed rules.

### Major 8 — The approved private-hand observation model is absent

- Canonical fact: `HAND-03`
- Evidence type: `human_decision`
- Source: `RULES`, PDF page 3
- Exact evidence: “Die erste verteilte Karte auf deiner Hand ist die vorderste Karte. Sie ist komplett sichtbar.”
- Approved human decision: The owner sees their complete ordered hand; opponents see only its count unless voluntarily communicated.
- Conflicting symbols: Public `GameState.hands` at line 33 contains every complete hand; no player-relative observation method exists. `render()` lines 223–224 exposes only counts, including to the owner.
- Expected: A player-relative observation exposing the observer’s ordered hand and only opponent hand counts.
- Implemented: Consumers either receive unrestricted full state or a rendering that withholds even the observing player’s own hand.

This is specifically a deviation from the approved executable information convention.

### Minor 1 — Final harvesting scores fields without emptying them

- Canonical facts: `END-03`, `HARV-02`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF pages 9 and 8
- Exact evidence: “Alle Spieler ernten noch ihre Bohnenfelder”; “Nach einer Ernte ist das abgeerntete Feld immer leer.”
- Conflicting code: `_finish()` lines 199–212 adds field proceeds to `coins` but returns the original `fields`.
- Expected: Final fields are harvested and therefore empty, with remaining bean cards disposed of consistently.
- Implemented: Coin totals are calculated correctly, but terminal state still displays the unharvested fields. This normally does not alter the winner.

## Rule-area coverage

| Rule area | Coverage | Result |
|---|---|---|
| Inventory and selected deck | Complete | Pass: ten bean types, 129 cards |
| Setup | Partial | Four players only; five absent |
| Ordered hands | Partial | Draws append and front planting works; observation model missing |
| Phase-1 planting | Partial | Mandatory/optional limit works; empty-hand transition fails |
| Reveal | Partial | Two-card reveal works; depletion boundary fails |
| Trading and gifts | Incomplete | Active-player restriction works; quantities and consent fail |
| Mandatory planting | Partial | All pending cards plant; player-selected order absent |
| Variant phase 4 | Incorrect | Three cards to active instead of one per player |
| Normal harvesting | Strong | Protection and payout tables align |
| Ackerbohne harvesting | Strong | One/two/three-card outcomes align |
| Turn order | Partial | Four-player clockwise progression works |
| Depletion and terminal timing | Incorrect | Detection is delayed |
| Final scoring and returns | Partial | Coins/tiebreak work for fixed four seats; fields remain populated |
| Private information | Incomplete | No compliant player-relative observation |

## Missing deterministic scenarios

- Four- and five-player initialization, including exact deck size, hand sizes, field counts, and clockwise seats.
- Empty hand at phase-1 entry and a hand emptied by the mandatory first planting; both must enter phase 2.
- Variant phase 4 verifying one appended card per player in active-first clockwise order.
- Unequal trades such as two-for-one with accept and reject paths, plus accepted and rejected gifts.
- Verification that proposed cards remain in place before acceptance.
- Inactive-player harvesting between actions, while disallowing interruption inside an atomic transfer or draw.
- Multiple pending cards planted in either chosen order, with a forced harvest between individual plantings.
- First/second depletion on the exact last draw, verifying the reshuffle uses the discard snapshot at that moment.
- Third depletion on the first or second reveal and on each phase-4 player draw.
- Player-relative observations: own ordered hand visible, opponent hands reduced to counts.
- Terminal final harvest verifying coin totals and emptied fields.
- Tie resolution for every possible original start-player seat and for five players.

## Material questions for a human

None. The packet’s approved facts and explicit executable conventions decide the material issues above; no additional rulebook clarification is needed.

```text
score: 0.34
confidence: high
critical_issues: 0
major_issues: 8
minor_issues: 1
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true
```