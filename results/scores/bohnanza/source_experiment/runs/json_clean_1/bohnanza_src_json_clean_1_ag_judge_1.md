## 1. Score

**score: 0.30 — confidence: high**

The inventory, ordinary planting, most harvest yields, hand ordering, and fixed-seat tie-break calculation are substantially represented. However, the selected variant’s phase-4 draw is fundamentally wrong, terminal depletion can be missed, and several material trade, setup, planting-order, information, and harvesting rules are absent or contradicted.

## 2. Findings

### Critical

1. **Phase 4 uses the base-game draw pattern and can continue past the terminal depletion**

   - Canonical facts: `P4-01`, `END-05`, also `DECK-01`
   - Evidence types:
     - `rule_quote` — `RULES`, PDF p.10: “Anders als im Grundspiel zieht jeder von euch eine Karte vom Nachziehstapel und steckt sie hinter seine letzte Handkarte. Hierbei beginnt der aktive Spieler, die Mitspieler folgen im Uhrzeigersinn.”
     - `human_decision` — `RULES`, PDF p.9, `END-05`: “endet, sobald der Nachziehstapel zum dritten Mal leer wird”; approved expectation: during variant phase 4, stop immediately after the draw that empties it.
     - `human_decision` — `RULES`, PDF p.9, `DECK-01`: “Ziehst du die letzte Karte vom Nachziehstapel, dann mische die Karten des Ablagestapels.”
   - Conflicting symbols/transitions: `legal_actions()` returns `("draw_three",)`; `apply_action()` handles it with `for _ in range(3)` and appends every card to `ns.hands[ns.active]`; `_draw_one()` only recognizes depletion on a later call made while `deck` is already empty.
   - Expected: each player draws exactly one, active player first and then clockwise. Third depletion ends immediately after the draw that empties the deck.
   - Implemented: the active player draws up to three cards and nobody else draws. If the third-cycle deck contains exactly three cards, all three go to the active player, depletion is not marked, and another turn begins. This fundamentally changes hands, phase timing, deck consumption, and potentially the winner.

### Major

2. **Empty-hand phase 1 skips phases 2 and 3**

   - Canonical fact: `P1-04`
   - Evidence type: `rule_quote`
   - Source: `RULES`, PDF p.5
   - Exact evidence: “Hast du zu Beginn der 1. Phase keine Karten auf der Hand, gehst du gleich zur 2. Phase über.”
   - Conflicting transition: `legal_actions()` supplies `("advance",)` when the hand is empty; `apply_action()` changes `phase` directly to `"draw"`.
   - Expected: proceed to phase 2, reveal two cards, trade, and plant the retained/received cards.
   - Implemented: proceeds directly to phase 4, omitting reveal, trade, and mandatory planting.

3. **Trades and gifts execute without recipient consent and unequal atomic trades are unavailable**

   - Canonical facts: `TRADE-04`, `TRADE-05`, `TRADE-07`
   - Evidence type: `rule_quote`
   - Source: `RULES`, PDF pp.5–6
   - Exact evidence:
     - “Ihr dürft mit einer unterschiedlichen Kartenanzahl handeln.”
     - “Beide Spieler müssen dem Handel zustimmen.”
     - “Der beschenkte Mitspieler muss dem Geschenk aber zustimmen.”
   - Conflicting symbols: `legal_actions()` creates only one-for-one `trade` actions and one-way `gift` actions; `apply_action()` executes them immediately while `actor` remains the active player. There is no proposal, accept, or reject state.
   - Expected: explicit consensual, atomic trades, including exchanges with differing quantities; gifts require recipient acceptance.
   - Implemented: the active player can unilaterally transfer cards, and the only exchange action is one-for-one. Multiple separate gifts/trades do not supply atomic consent for a single unequal exchange.

4. **Mandatory received-card planting order is fixed**

   - Canonical fact: `P3-02`
   - Evidence type: `rule_quote`
   - Source: `RULES`, PDF p.7
   - Exact evidence: “Jeder darf selbst entscheiden, in welcher Reihenfolge er die neuen Bohnenkarten anbaut.”
   - Conflicting symbol: the `"plant_pending"` transition always uses `s.pending[p][0]`.
   - Expected: each recipient chooses which pending card to plant next and may make necessary legal harvest choices between cards.
   - Implemented: pending cards must be planted in tuple insertion order. Different orders can change which field must be harvested.

5. **A three-Ackerbohne harvest puts the three scored cards into the discard pile**

   - Canonical fact: `ACKER-03`
   - Evidence type: `human_decision`
   - Source: `RULES`, PDF p.11
   - Exact evidence: “Erntest du ein Feld mit drei Ackerbohnen, erhältst du wie gewohnt drei Bohnentaler.”
   - Conflicting symbol: `_harvest()` increments `coins[p]` by three and then executes `discard.extend(field)`.
   - Expected: the three harvested Ackerbohnen become the three coin cards and leave the circulating bean deck.
   - Implemented: they score three coins but also enter the discard pile, allowing all three to be reshuffled and drawn again.

6. **Inactive players cannot exercise the approved between-step harvest right**

   - Canonical fact: `HARV-01`
   - Evidence type: `human_decision` — adjudication-dependent
   - Source: `RULES`, PDF p.7
   - Exact evidence: “Du darfst jederzeit im Spiel deine Bohnenfelder abernten, auch wenn du nicht der aktive Spieler bist.”
   - Conflicting symbol: `legal_actions()` constructs harvest actions only for `p = s.actor`. During trade, `actor` is the active player; other players cannot request a harvest.
   - Expected: any owner may harvest between individual non-atomic steps, including during another player’s turn.
   - Implemented: harvesting is limited to the current actor. Inactive players only gain an opportunity if they later become the phase-3 planting actor.

7. **The complete 4–5-player setup and chosen start player are not supported**

   - Canonical facts: `SET-01`, `SET-03`
   - Evidence type: `rule_quote`
   - Sources:
     - `RULES`, PDF p.10: “VARIANTE 2: DIE ACKERBOHNEN (FÜR 4–5 SPIELER)”
     - `RULES`, PDF p.2: “Bestimmt einen Startspieler. Er erhält die Startspielerkarte.”
   - Conflicting symbols: `Game` is documented as four-player only; state defaults, pending tuples, loops, hands, fields, and returns are hard-coded to four players; `active` starts at zero with no start-player configuration or marker.
   - Expected: selected variant setup for either four or five players, with a configured/chosen original start player retained for turn order and tie-breaking.
   - Implemented: exactly four seats and implicit seat 0 as start player.

8. **Approved private-hand observations are not implemented**

   - Canonical fact: `HAND-03`
   - Evidence type: `human_decision` — adjudication-dependent
   - Source: `RULES`, PDF p.3
   - Exact evidence: “Die erste verteilte Karte auf deiner Hand ist die vorderste Karte. Sie ist komplett sichtbar.” Approved expectation additionally specifies that an owner sees their ordered hand while opponents see only its count.
   - Conflicting symbols: there is no player-specific observation method; `GameState` directly contains every hand, while `render()` exposes only all hand sizes and does not show the viewing player their own ordered hand.
   - Expected: player-relative observations reveal the viewer’s complete ordered hand and only opponents’ counts.
   - Implemented: the raw state exposes all private hands to any consumer, while the sole rendering exposes no player’s own cards.

### Minor

9. **Terminal “harvest all fields” scores fields but leaves them populated**

   - Canonical fact: `END-03`
   - Source: `RULES`, PDF p.9: “Alle Spieler ernten noch ihre Bohnenfelder.”
   - Conflicting symbol: `_finish()` calculates field proceeds but returns the original `fields`.
   - Expected: terminal fields are harvested and empty, with proceeds reflected in coins.
   - Implemented: proceeds are counted correctly, but terminal state still displays the planted cards.

## 3. Rule-area coverage

| Rule area | Coverage | Assessment |
|---|---|---|
| Inventory | Strong | Correct 129-card selected deck and yield tables |
| Setup | Partial | Correct four-player fields/hands; five players and chosen start absent |
| Ordered hands | Partial | Deal and append order correct; observation boundary absent |
| Phase 1 | Partial | Mandatory/optional planting works; empty-hand transition is wrong |
| Reveal | Mostly present | Public reveal exists; depletion detection is delayed in some cases |
| Trade/gifts | Weak | Active-player restriction present; consent and unequal atomic trades absent |
| Phase 3 | Partial | All pending cards must be planted; player cannot choose their order |
| Phase 4 | Incorrect | Three to active instead of one to every player clockwise |
| Harvesting | Partial | Protection and normal yields work; inactive timing and Acker card disposal fail |
| Recycling/chance | Partial | Seeded shuffle exists; empty-deck event is recognized too late |
| Terminal/scoring | Partial | Final proceeds and fixed-seat tie-break work; phase-4 ending can be missed |
| Returns | Mostly correct | Zero nonterminal and winner-based terminal returns; limited by fixed start/seat count |

## 4. Missing deterministic scenarios

- Four-player and five-player phase-4 draw distribution.
- Third-cycle phase 4 with one, two, and three cards remaining.
- Last card appearing as the second phase-2 reveal.
- Empty active hand at the start of phase 1.
- Recipient acceptance and rejection of a trade and a gift.
- Atomic 2-for-1 and other unequal-quantity exchanges.
- Multiple pending bean types whose planting orders require different harvests.
- An inactive player harvesting between two atomic actions.
- Three Ackerbohnen harvested before a recycle, verifying they cannot re-enter the deck.
- Five-player setup and tie-breaking with a nonzero chosen start player.
- Player-relative observation tests for own hand versus opponents’ counts.
- Final scoring verifying that all fields become empty.

## 5. Material questions for a human

- Is a deliberately four-player-only specialization acceptable, despite the requested complete source condition covering both four and five players? If so, that limitation should be explicit in the evaluation contract.
- Which method is intended to provide player-relative observations? No such interface exists, so the approved privacy convention cannot currently be enforced.
- May seat numbering always be normalized so the chosen start player is seat 0? If not, setup and tie-breaking need an explicit original-start field.

These are implementation-contract questions; the supplied rule facts themselves are sufficient to resolve the gameplay discrepancies.

score: 0.30
confidence: high
critical_issues: 1
major_issues: 7
minor_issues: 1
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true