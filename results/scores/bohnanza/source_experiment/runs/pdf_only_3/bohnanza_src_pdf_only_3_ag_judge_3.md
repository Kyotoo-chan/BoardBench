1. **Score: 0.27 — confidence: high.** The module models much of the base planting/trading loop, but it omits the selected Ackerbohne condition, implements the variant draw phase incorrectly, mishandles terminal timing, and has several material action, scoring, information, and winner errors.

## Findings

### Critical

1. **Third-depletion detection can extend the game and change the winner.**

   - Fact IDs: `END-01`, `END-02`, `END-05`
   - Evidence:
     - `rule_quote`, `RULES`, PDF p.9: “Das Spiel endet, sobald der Nachziehstapel zum dritten Mal leer wird.”
     - `rule_quote`, `RULES`, PDF p.9: “Sollte dies beim Aufdecken der Karten in der 2. Phase … passieren … spielt ihr die 2. und die 3. Phase noch zu Ende.”
     - `human_decision`, `RULES`, PDF p.9, “endet, sobald”: third depletion during variant phase 4 is terminal immediately after the draw that empties the pile.
   - Conflicting symbols/transitions: `Game._draw`, `Game._reveal`, `finish_building`.
   - Expected: depletion is registered when the last card is drawn. A phase-2 depletion finishes phases 2–3 and skips phase 4; a phase-4 depletion stops immediately before any further draw or turn.
   - Implemented: `_draw` increments `empty_deck_count` only when a later draw is attempted against an already-empty deck. `finish_building` then continues its three-iteration draw loop, advances `active`, and does not finalize until a later turn completes phase 3. A pile emptied by the second reveal is therefore misclassified as a phase-4 depletion, while a phase-4 depletion can permit another turn’s planting/trading. Those extra actions can change final coins and winner.

### Major

2. **The selected 129-card Ackerbohne deck is replaced by the 104-card base deck.**

   - Fact IDs: `INV-03`, `INV-04`
   - Evidence:
     - `rule_quote`, `RULES`, PDF p.10: “alle Bohnensorten aus dem Grundspiel sowie die Ackerbohnen und die Weinbrandbohnen.”
     - `user_observation`, `COMPONENTS`, JSON Pointers `/bohnen/9/anzahl_karten` and `/bohnen/11/anzahl_karten`: Weinbrandbohne `22`; Ackerbohne `3`.
   - Conflicting symbols: `BEANS`, `COUNTS`, `Game.initial_state`.
   - Expected: ten bean types and 129 cards: 104 base + 22 Weinbrandbohnen + 3 Ackerbohnen.
   - Implemented: only the eight base types and 104 cards are constructed.

3. **Ackerbohne harvesting and the unlockable third field are absent.**

   - Fact IDs: `ACKER-01`, `ACKER-02`, `ACKER-03`, `ACKER-04`
   - Evidence:
     - `rule_quote`, `RULES`, PDF p.11: “Feld mit zwei Ackerbohnen, erhältst du ein drittes Bohnenfeld.”
     - `human_decision`, `RULES`, PDF p.11: “bereits ein drittes Bohnenfeld … erhältst du … nichts.”
     - `human_decision`, `RULES`, PDF p.11: “drei Ackerbohnen … drei Bohnentaler.”
     - `human_decision`, `RULES`, PDF p.11: the source provides no one-card reward; an allowed singleton harvest yields zero and is discarded.
   - Conflicting symbols: `initial_state` field construction, `METERS`, `_harvest`, `_harvestable`, `_finalize`, and the `range(2)` field loops.
   - Expected: players can unlock and retain field 3 by harvesting exactly two Ackerbohnen; Acker harvests of one, two, and three follow their special outcomes.
   - Implemented: players permanently have exactly two fields, Ackerbohne is not recognized, and all harvest logic assumes normal coin meters.

4. **Variant phase 4 draws the wrong number of cards for the wrong players.**

   - Fact ID: `P4-01`
   - Evidence type: `rule_quote`
   - Source: `RULES`, PDF p.10
   - Exact evidence: “zieht jeder von euch eine Karte vom Nachziehstapel … aktive Spieler, die Mitspieler folgen im Uhrzeigersinn.”
   - Conflicting transition: `finish_building`.
   - Expected: every player draws one card, active player first and then clockwise, each appending to their own hand.
   - Implemented: three cards are drawn and appended exclusively to the active player’s hand.

5. **Inactive players generally cannot exercise their harvest right.**

   - Fact ID: `HARV-01`
   - Evidence type: `human_decision`
   - Source: `RULES`, PDF p.7
   - Exact evidence: “Du darfst jederzeit im Spiel deine Bohnenfelder abernten, auch wenn du nicht der aktive Spieler bist.”
   - Conflicting symbols: `current_player`, `legal_actions`.
   - Expected: any field owner may harvest between individual atomic steps, including during another player’s turn.
   - Implemented: harvest actions are generated only for `current_player(s)`: normally the active player, the trade recipient while a proposal is pending, or one selected incoming-card owner during phase 3. All other owners are blocked.

6. **Legal multi-card and reverse-direction gift trades cannot be expressed.**

   - Fact IDs: `TRADE-04`, `TRADE-07`
   - Evidence:
     - `rule_quote`, `RULES`, PDF p.5: “Ihr dürft mit einer unterschiedlichen Kartenanzahl handeln, z. B. zwei Blaue Bohnen gegen eine Gartenbohne.”
     - `rule_quote`, `RULES`, PDF p.6: “Bohnenkarten schenken … Der beschenkte Mitspieler muss dem Geschenk aber zustimmen.”
   - Conflicting symbols: trade-action generation in `legal_actions`; `offer_trade`/`accept_trade`.
   - Expected: consensual trades can transfer multiple cards with unequal quantities, including the printed two-for-one example; a player can consensually gift cards to the active player.
   - Implemented: every proposal transfers exactly one active-player card and at most one target-player card. Only active-to-target gifts are representable.

7. **Mandatory phase-3 planting order is forced rather than chosen.**

   - Fact ID: `P3-02`
   - Evidence type: `rule_quote`
   - Source: `RULES`, PDF p.7
   - Exact evidence: “Jeder darf selbst entscheiden, in welcher Reihenfolge er die neuen Bohnenkarten anbaut.”
   - Conflicting symbols: `legal_actions` build branch and `plant_incoming`.
   - Expected: each recipient chooses the next received/retained card to plant and may make necessary harvest choices between cards.
   - Implemented: only `incoming[owner][0]` may be planted. Receipt order is mandatory, and the active player’s retained reveals are appended behind earlier incoming cards.

8. **Gartenbohne harvests award one coin too few.**

   - Fact ID: `GOLD-08`
   - Evidence type: `user_observation`
   - Source: `COMPONENTS`, JSON Pointer `/bohnen/7/ernte`
   - Exact evidence: `{"ab_bohnen": 2, "gold": 2}` and `{"ab_bohnen": 3, "gold": 3}`.
   - Conflicting symbols: `METERS["Gartenbohne"]`, `_harvest`.
   - Expected: one card yields 0, two cards yield 2, and three or more yield 3 coins.
   - Implemented: `(2, 3, None, None)` is enumerated as the one-coin and two-coin thresholds, producing only 1 and 2 coins.

9. **The terminal tie-break is reversed and not applied by `returns`.**

   - Fact ID: `END-04`
   - Evidence type: `rule_quote`
   - Source: `RULES`, PDF p.9
   - Exact evidence: “Bei einem Gleichstand gewinnt der Spieler, der im Uhrzeigersinn am weitesten weg vom Startspieler sitzt.”
   - Conflicting symbols: `_finalize`, `returns`.
   - Expected: among tied coin leaders, the player farthest clockwise from the original start player is the winner.
   - Implemented: `winner_order` sorts clockwise distance ascending, favoring the start player or nearest tied seat. Independently, `returns` awards `1` to every player tied on coins, ignoring the tie-break completely.

10. **Private ordered hands are exposed to every observer.**

   - Fact ID: `HAND-03`
   - Evidence type: `human_decision`
   - Source: `RULES`, PDF p.3
   - Exact evidence: “Die erste verteilte Karte auf deiner Hand ist die vorderste Karte.” The approved decision adds that the owner sees the whole ordered hand and opponents see only its count.
   - Conflicting symbol: `render`, plus the absence of an observer-specific state view.
   - Expected: an observer receives their own ordered hand but only opponents’ hand counts.
   - Implemented: `render` prints `hands={s.hands}`, exposing every card and its order to everyone.

No separate minor findings.

## Rule-area coverage

| Rule area | Status | Notes |
|---|---|---|
| Player count/setup | Partial | Correct 4–5 players and two initial fields; wrong deck and no chosen-start interface |
| Inventory | Failed | Ackerbohne and Weinbrandbohne absent |
| Ordered hands | Partial | Deal, front planting, removal, and append behavior mostly correct; privacy absent |
| Phase 1 planting | Mostly covered | Mandatory first and optional second implemented |
| Reveal | Partial | Two draws implemented; depletion boundary incorrect |
| Trading | Partial | Active-player consent model works; multi-card trades and reverse gifts absent |
| Phase 3 planting | Partial | All queued cards are planted, but order is forced |
| Variant phase 4 | Failed | Three cards to active instead of one to every player |
| Harvest legality | Partial | Protection rule modeled; inactive timing and third field absent |
| Harvest rewards | Partial | Most base meters correct; Garten and all Acker outcomes wrong/absent |
| Reshuffle/depletion | Partial | Reshuffle continuation exists; depletion is detected too late |
| Terminal/scoring | Failed | End timing and tie winner are materially wrong |
| Returns | Partial | Nonterminal zeros and coin totals exist; terminal ties ignore the winner rule |

## Missing deterministic scenarios

- Initial deck contains exactly 129 cards before dealing, with all ten selected types and exact counts.
- Each phase-4 seat draws exactly once in active-first clockwise order.
- First, second, and third depletion when the last card is:
  - the first reveal,
  - the second reveal,
  - each player’s phase-4 draw.
- Third depletion in phase 2 finishes only phases 2–3; third depletion in phase 4 permits no later action.
- Acker harvests of one, two, and three cards, both before and after field 3 is unlocked.
- Field 3 persists while fields 1–2 retain their existing contents.
- Inactive-player harvests between planting steps, trade decisions, and different players’ phase-4 draws.
- Consensual two-for-one trade, active-player gift, and gift to the active player.
- Recipient-selected planting order where different orders require different intervening harvests.
- Gartenbohne harvests at field sizes 1, 2, 3, and 4.
- Coin ties involving the start player and multiple clockwise seats.
- Per-observer hand visibility.
- Hand order after trading a middle card and after each player’s phase-4 append.

## Material questions for a human

- Is player index `0` intentionally the configured/chosen start player, or must the API expose start-player selection?
- What observer-aware API should enforce `HAND-03`, since `render` currently has no observer argument?
- Should terminal returns be exactly winner `+1` / losers `-1`, or is another documented encoding acceptable? The current `+1/0` encoding is undocumented.
- The approved facts do not determine the cross-player order for resolving phase-3 incoming cards. Should that order be explicit, while preserving each owner’s choice of their own planting order?

These are interface/adjudication questions; the cited gameplay contradictions do not require further rulebook clarification.

score: 0.27
confidence: high
critical_issues: 1
major_issues: 9
minor_issues: 0
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true