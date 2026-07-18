score: 0.22  
confidence: high

The implementation contains a recognizable base-game engine, including ordered hands, consensual trades, harvest thresholds, singleton protection, final harvesting, and tie-breaking. However, it cannot initialize the assigned Ackerbohne condition at all. Several independent phase, authority, information, and terminal-timing rules would remain incorrect after that blocker was removed.

## Findings

### Critical

1. **The assigned Ackerbohne game cannot be initialized**

   - Canonical facts:
     - `INV-03`
       - Evidence type: `rule_quote`
       - Source: `RULES`, PDF page 10
       - Exact evidence: “alle Bohnensorten aus dem Grundspiel sowie die Ackerbohnen und die Weinbrandbohnen”
     - `INV-04`
       - Evidence type: `user_observation`
       - Source: `COMPONENTS`, JSON Pointers `/bohnen/9/anzahl_karten` and `/bohnen/11/anzahl_karten`
       - Exact evidence: Weinbrandbohne `22`; Ackerbohne `3`
   - Conflicting symbols: `Game.__init__`, `Game.initial_state`, `BASE_COUNTS` at lines 63–76.
   - Expected: The selected 4–5-player condition initializes a 129-card deck: 104 base cards, 22 Weinbrandbohnen, and 3 Ackerbohnen.
   - Implemented: The default is `variant="base"`, only the 104 base cards exist, and `initial_state()` raises `ValueError` for `"Ackerbohnen"`.
   - Impact: The required game condition cannot begin.

### Major

2. **Phase 4 uses the base-game three-card draw instead of the selected variant rule**

   - Canonical fact: `P4-01`
   - Evidence type: `rule_quote`
   - Source: `RULES`, PDF page 10
   - Exact evidence: “zieht jeder von euch eine Karte vom Nachziehstapel und steckt sie hinter seine letzte Handkarte. Hierbei beginnt der aktive Spieler, die Mitspieler folgen im Uhrzeigersinn.”
   - Conflicting transition: `apply_action(..., ("draw_phase4",))`, lines 263–273.
   - Expected: Each player draws one card, active player first and then clockwise; each draw appends to that player’s hand.
   - Implemented: One action draws up to three cards, all into the active player’s hand.

3. **The acting player can harvest other players’ fields**

   - Canonical fact: `HARV-01`
   - Evidence type: `human_decision`
   - Source: `RULES`, PDF page 7
   - Exact evidence: “Du darfst jederzeit im Spiel deine Bohnenfelder abernten, auch wenn du nicht der aktive Spieler bist.”
   - Conflicting symbols: `_harvest_actions`, `legal_actions`, and `apply_action`, lines 101–120 and 203–206.
   - Expected: A field’s owner may elect to harvest their own field between atomic steps.
   - Implemented: `_harvest_actions()` adds harvest actions for every player to the current actor’s legal-action list. `apply_action()` accepts the encoded player index without checking ownership against the actor.

4. **Mandatory phase-3 planting order is forced rather than chosen by each recipient**

   - Canonical fact: `P3-02`
   - Evidence type: `rule_quote`
   - Source: `RULES`, PDF page 7
   - Exact evidence: “Jeder darf selbst entscheiden, in welcher Reihenfolge er die neuen Bohnenkarten anbaut.”
   - Conflicting symbols: `end_trade` construction of `s.pending` and the use of `s.pending[0]`, lines 250–257 and 152–157.
   - Expected: Each recipient chooses the order of their received/retained cards, including choices that affect intervening harvests.
   - Implemented: Cards are queued in fixed player/list order, and only the first queued card may be planted.

5. **Third depletion is detected one draw attempt too late**

   - Canonical facts:
     - `END-01`
       - Evidence type: `rule_quote`
       - Source: `RULES`, PDF page 9
       - Exact evidence: “Das Spiel endet, sobald der Nachziehstapel zum dritten Mal leer wird.”
     - `END-05`
       - Evidence type: `human_decision`
       - Source: `RULES`, PDF page 9
       - Exact evidence: “endet, sobald”
   - Conflicting symbols: `_draw_one`, `_begin_trade`, and phase-4 completion, lines 166–174, 190–198, and 263–273.
   - Expected: Depletion occurs when the draw removes the final card. In phase 2, phases 2–3 then finish; in variant phase 4, the game ends immediately after that draw.
   - Implemented: `exhaustions` increments only when a later draw begins with an already-empty deck. If the final owed draw takes the last card, the depletion is not recognized and play can advance incorrectly.

6. **No Ackerbohne two-card field-unlock behavior exists**

   - Canonical fact: `ACKER-01`
   - Evidence type: `rule_quote`
   - Source: `RULES`, PDF page 11
   - Exact evidence: “Erntest du ein Feld mit zwei Ackerbohnen, erhältst du ein drittes Bohnenfeld.”
   - Conflicting symbols: `METERS["Ackerbohne"]`, `_harvest`, and two-field initialization, lines 28, 84, and 183–188.
   - Expected: Harvesting exactly two Ackerbohnen unlocks field 3 when absent, discards both cards, and preserves fields 1–2.
   - Implemented: The only Acker meter entry is three cards for three coins; `_harvest()` has no field-unlock transition, and players always have two fields. This remains defective even if the initialization rejection is removed.

7. **The only rendered state discloses every ordered hand**

   - Canonical fact: `HAND-03`
   - Evidence type: `human_decision`
   - Source: `RULES`, PDF page 3
   - Exact source evidence: “Die erste verteilte Karte auf deiner Hand ist die vorderste Karte.”
   - Approved decision: Owners see their complete ordered hand; opponents see only its count.
   - Conflicting symbol: `render`, lines 293–300.
   - Expected: Player-scoped observations conceal opponents’ card identities and order.
   - Implemented: `"hands": s.hands` exposes every complete ordered hand, with no player-scoped observation alternative.

### Minor

8. **Brechbohne is replaced by the unsupported identity “Grüne Bohne”**

   - Canonical facts: `INV-02`, `GOLD-04`
   - Source: `RULES` page 2 and `COMPONENTS` pointer `/bohnen/3`
   - Expected: The 14-card type is `Brechbohne`.
   - Implemented: `BASE_COUNTS` and `METERS` call it `Grüne Bohne`.
   - The count and thresholds happen to match, so this is primarily a component-identity/rendering defect rather than a distinct mechanical type-count error.

## Rule-area coverage

| Rule area | Status | Notes |
|---|---|---|
| Selected setup/inventory | Fails | Required variant rejected; 129-card deck absent |
| Hand order and phase 1 | Mostly correct | Front-first and optional second planting represented |
| Fields/forced harvest | Partial | Matching-type planting works; harvest authority is wrong |
| Reveal and trade | Mostly correct | Two reveals, active-player trades, consent, gifts, and unequal exchanges represented |
| Mandatory planting | Fails materially | All cards are planted, but planting order is fixed |
| Variant phase 4 | Fails | Three cards to active player instead of one per player |
| Chance/deck recycling | Partial | Reshuffling exists; depletion event is late |
| Private information | Fails | All hands are rendered publicly |
| Harvest values | Mostly correct for base types | Acker special reward absent |
| Terminal scoring | Partial | Final harvest and tie-break work; terminal timing can be late |
| Returns | Acceptable | Nonterminal zero and winner indication; raw coin totals remain rendered |

## Missing deterministic scenarios

- Four- and five-player Ackerbohne initialization with exactly 129 cards and the correct per-type counts.
- Phase 4 verifying one draw per player in clockwise order and immediate append to each hand.
- Owner-only harvesting during both the active player’s and another player’s turn.
- Multiple received/revealed cards planted in every legal player-chosen order.
- Third depletion caused by drawing the exact last card:
  - during the first reveal;
  - during the second reveal;
  - during each player’s variant phase-4 draw.
- Ackerbohne harvests of one, two, and three cards, both before and after field 3 is unlocked.
- Player-scoped observations proving opponents receive only hand counts.
- Correct `Brechbohne` identity through setup, planting, trade, harvesting, and rendering.

## Material questions for a human

- Is `render()` intended as an omniscient debugging representation rather than a player observation? If so, the module still needs a separate player-scoped observation interface to satisfy `HAND-03`.
- Does the host framework independently enforce that the player encoded in a `("harvest", p, i)` action is the submitting actor? Nothing in this implementation enforces it, and `current_player()` generally identifies a different single actor.

```text
score: 0.22
confidence: high
critical_issues: 1
major_issues: 6
minor_issues: 1
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true
```