score: 0.40  
confidence: high

The inventory, ordinary planting, Bohnometers, Ackerbohne rewards, basic harvest accounting, final harvesting, scoring, and tie-break are substantially correct. However, phase 4 is fundamentally misimplemented, depletion is detected late, trading lacks required consent and unequal exchanges, mandatory planting order is constrained incorrectly, approved harvest timing is absent, and private hands are exposed.

## Findings

### Major

1. **Variant phase 4 draws the wrong number of cards and gives them all to the active player.**

   - Canonical fact: `P4-01`
   - Evidence type: `rule_quote`
   - Source: `RULES`, PDF page 10
   - Exact evidence: “zieht jeder von euch eine Karte … aktive Spieler … im Uhrzeigersinn”
   - Code: `finish_phase3` sets `draw_remaining = 3`; `draw_to_hand` always appends to `s.players[s.active].hand`.
   - Expected: Every player draws exactly one card, active player first and then clockwise—four total draws in a four-player game or five in a five-player game.
   - Implemented: Exactly three draws are attempted, all for the active player. This materially changes every turn’s hand economy and information distribution.

2. **Deck depletion and game-end timing are detected one draw too late.**

   - Canonical facts: `END-01`, `END-02`, `END-05`, `DECK-01`
   - Evidence types: `rule_quote` for `END-01`/`END-02`; `human_decision` for `END-05`/`DECK-01`
   - Source: `RULES`, PDF page 9
   - Exact evidence: “endet, sobald der Nachziehstapel zum dritten Mal leer wird”; “beim Aufdecken … spielt ihr die 2. und die 3. Phase noch zu Ende”; “Ziehst du die letzte Karte … mische die Karten des Ablagestapels.”
   - Code: `_draw_one()` increments `exhaustions` only when the deck is already empty before a draw. Popping the final card leaves the deck empty without recording depletion.
   - Expected: Drawing the last card causes depletion immediately. First/second depletion immediately reshuffles the current discard; third depletion follows the approved phase-2 or phase-4 terminal boundary.
   - Implemented: Depletion is recorded only on a later attempted draw. This can wrongly include subsequently discarded cards in a reshuffle and can allow phase 4 or later actions after the third depletion should already have controlled the transition.

3. **Trades and gifts resolve without explicit consent.**

   - Canonical facts: `TRADE-05`, `TRADE-07`
   - Evidence type: `rule_quote`
   - Source: `RULES`, PDF page 6
   - Exact evidence: “beide Spieler müssen dem Handel zustimmen”; “Bohnenkarten schenken … muss … zustimmen”
   - Code: `legal_actions()` lists completed `trade` and `gift` actions for the active player; `current_player()` remains the active player during `phase2_trade`; `apply_action()` immediately removes and transfers the cards.
   - Expected: A proposal and an explicit accept/reject choice, with cards staying in place until acceptance.
   - Implemented: The active player can unilaterally execute a trade, give a card to another player, or take a “gift” from another player’s hand. No recipient or counterparty decision exists.

4. **Unequal multi-card exchanges cannot be represented atomically.**

   - Canonical facts: `TRADE-04`, `TRADE-05`
   - Evidence type: `rule_quote`
   - Source: `RULES`, PDF pages 5–6
   - Exact evidence: “Mit Karten, die ihr nach einem Handel bekommt, dürft ihr nicht weiterhandeln”; “mit einer unterschiedlichen Kartenanzahl handeln”; “beide Spieler müssen dem Handel zustimmen”
   - Code: `Action("trade", ...)` contains exactly one offered card and one received card. `gift` transfers only one card.
   - Expected: A consensual atomic exchange may contain different nonzero quantities on the two sides.
   - Implemented: Only one-for-one trades and individual gifts exist. Chaining them is not equivalent because each transfer commits separately and received cards cannot be retraded.

5. **Each player is forced to plant pending cards in acquisition order.**

   - Canonical fact: `P3-02`
   - Evidence type: `rule_quote`
   - Source: `RULES`, PDF page 7
   - Exact evidence: “Jeder darf selbst entscheiden, in welcher Reihenfolge er die neuen Bohnenkarten anbaut.”
   - Code: `legal_actions()` always selects `bean = q.pending[0]`; `plant_pending` always performs `p.pending.pop(0)`.
   - Expected: The recipient chooses any remaining received/retained card as the next card to plant, including choosing harvests between individual plantings where necessary.
   - Implemented: Only the first pending card can be planted, potentially forcing harvests that a different legal planting order would avoid.

6. **Approved between-step harvesting is unavailable through most of the turn.**

   - Canonical fact: `HARV-01`
   - Evidence type: `human_decision`
   - Source: `RULES`, PDF page 7
   - Exact evidence: “Du darfst jederzeit im Spiel deine Bohnenfelder abernten, auch wenn du nicht der aktive Spieler bist.”
   - Code: `legal_actions()` exposes `harvest` only when the next mandatory phase-1 or phase-3 card has no planting destination.
   - Expected: A field owner may explicitly harvest between individual game steps, including during another player’s turn, subject to the approved atomic-action boundaries.
   - Implemented: Voluntary harvests, inactive-player harvests, and harvests between otherwise compatible mandatory plantings are absent.
   - Provenance note: This is a deviation from the approved human timing decision, not merely from an exhaustively printed timing procedure.

7. **The supplied state/render interface exposes every ordered private hand.**

   - Canonical fact: `HAND-03`
   - Evidence type: `human_decision`
   - Source: `RULES`, PDF page 3
   - Exact evidence: “Die erste verteilte Karte auf deiner Hand ist die vorderste Karte.”
   - Approved expectation: The owner sees the whole ordered hand; opponents see only its count unless information is voluntarily communicated.
   - Code: `GameState.players[*].hand` is universally accessible, and `render()` prints `hand={p.hand}` for every player. No player-relative observation method or masking layer is supplied.
   - Expected: Player-relative observations reveal only the observing player’s ordered hand and opponents’ hand counts.
   - Implemented: The only rendered observation reveals all private cards and their order.
   - Provenance note: The opponent-visibility boundary is an approved human decision.

No critical or minor findings were identified.

## Rule-area coverage

| Rule area | Status | Review result |
|---|---|---|
| Setup and inventory | Pass | Four/five players, two starting fields, five ordered cards, and the 129-card selected deck are correct. Seat 0 is implicitly used as start player. |
| Phase 1 planting | Pass | Mandatory front card, optional second card, and forced legal harvest logic are represented. |
| Reveal | Pass with terminal defect | Two public draws are modeled, but depletion timing is late. |
| Trading | Major defects | Active-player involvement and card sources are represented; consent and unequal atomic exchanges are not. |
| Phase 3 planting | Major defect | All pending cards must eventually be planted, but their legal order choice is lost. |
| Phase 4 drawing | Major defect | Wrong draw count and wrong recipients. |
| Harvesting | Major timing defect | Protection, ordinary rewards, discard handling, and emptying fields are correct; general timing is absent. |
| Bohnometers | Pass | All nine ordinary bean schedules match approved facts. |
| Ackerbohne | Pass | One-, two-, and three-card outcomes, including existing field 3, match the approved decisions. |
| Depletion/reshuffle | Major defect | Exhaustion is registered on the next attempted draw rather than when the last card is drawn. |
| End/scoring | Pass after trigger | Final harvest, hand exclusion, coin scoring, winner selection, and tie-break are correct once `_finish_game()` is reached. |
| Private information | Major defect | No compliant player-relative observation is supplied. |
| Returns | Pass | Nonterminal zero and terminal winner-based `+1/-1` conform to the executable convention. |

## Missing deterministic scenarios

- Four- and five-player phase 4: verify one draw per player in clockwise order.
- First and second depletion caused by drawing the final card, including immediate reshuffle before an owed second reveal.
- Third depletion on each of the two phase-2 reveals, followed by trading and phase 3 but no phase 4.
- Third depletion on each clockwise phase-4 recipient, with immediate termination before another player draws.
- Proposed trade/gift rejection and acceptance without pre-acceptance mutation.
- Atomic unequal exchanges such as two cards for one and one for several.
- Pending cards planted in two different chosen orders, where the orders require different harvest decisions.
- Voluntary active- and inactive-player harvests at each approved between-step boundary.
- Player-relative observations confirming own ordered hand and opponent counts only.

## Material questions for a human

- Is seat 0 intentionally the externally configured/chosen start player, or should construction accept an explicit `start_player`? The packet requires a chosen/configured player but does not prescribe the API.
- Is `render()` intended strictly as privileged debugging output? If so, a separate compliant player-relative observation interface is still needed.

```text
score: 0.40
confidence: high
critical_issues: 0
major_issues: 7
minor_issues: 0
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true
```