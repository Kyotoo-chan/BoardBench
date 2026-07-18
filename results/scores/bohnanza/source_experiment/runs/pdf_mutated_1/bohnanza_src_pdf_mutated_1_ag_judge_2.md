Score: **0.36**, confidence: **high**. The module models the selected inventory, ordered hands, basic planting, bean meters, field protection, gifts, and Ackerbohne rewards well. However, variant drawing, depletion timing, final scoring, trade quantities, planting choice, harvesting timing, and private information materially contradict approved facts. Most importantly, terminal winners can be fundamentally wrong.

## Findings

### Critical

1. Final scoring both omits field harvests and scores hand cards

- Canonical fact: `END-03`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 9
- Exact evidence: “Alle Spieler ernten noch ihre Bohnenfelder und erhalten gegebenenfalls dafür Bohnentaler. Die Karten auf der Hand zählen nicht mehr.”
- Conflicting code:
  - `apply_action()` changes directly to `terminal` without harvesting fields.
  - `returns()` calculates `state.coins[p] + len(state.hands[p])`.
- Expected: Automatically harvest every field at game end, then compare coin totals; hand cards are worth zero.
- Implemented: Fields are ignored while every hand card adds one point.
- Impact: This can fundamentally select the wrong winner and makes terminal coin totals inaccurate.

### Major

2. The selected variant’s draw phase uses the base-game draw rule

- Canonical fact: `P4-01`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 10
- Exact evidence: “Anders als im Grundspiel zieht jeder von euch eine Karte vom Nachziehstapel und steckt sie hinter seine letzte Handkarte. Hierbei beginnt der aktive Spieler, die Mitspieler folgen im Uhrzeigersinn.”
- Conflicting code: `legal_actions()` exposes `("draw_three",)`; `apply_action()` draws three cards exclusively into `s.hands[s.active]`.
- Expected: Each player draws exactly one card, beginning with the active player and proceeding clockwise.
- Implemented: The active player alone draws three cards.
- Impact: Materially changes hand distribution, hidden information, deck consumption, and depletion timing every turn.

3. Depletion is detected late and phase-2 termination incorrectly requires phase 4

- Canonical facts: `DECK-01`, `END-01`, `END-02`, `END-05`
- Evidence types:
  - `DECK-01`: `human_decision`
  - `END-01` and `END-02`: `rule_quote`
  - `END-05`: `human_decision`
- Source: `RULES`, PDF page 9
- Exact evidence:
  - “Ziehst du die letzte Karte vom Nachziehstapel, dann mische die Karten des Ablagestapels.”
  - “Das Spiel endet, sobald der Nachziehstapel zum dritten Mal leer wird.”
  - “Sollte dies beim Aufdecken der Karten in der 2. Phase … passieren, spielt ihr die 2. und die 3. Phase noch zu Ende.”
  - “endet, sobald”
- Conflicting code: `_draw()` increments `empty_count` only when called while the deck is already empty. `reveal_two()` merely sets `end_pending`; `finish_planting()` still enters `draw`; only `draw_three()` makes the state terminal.
- Expected:
  - Detect depletion when the last card is drawn.
  - First and second depletion immediately establish the reshuffled pile.
  - Third depletion during phase 2 finishes phases 2 and 3, skips phase 4, and scores.
  - Third depletion during phase 4 stops immediately after the emptying draw.
- Implemented:
  - Depletion is delayed until a subsequent attempted draw.
  - A third depletion during reveal still requires a phase-4 action.
  - If the last card is the last iteration of a draw loop, termination can be delayed into a later turn.
- Impact: Extra draws/actions can occur, and the game can terminate at the wrong boundary.

4. Unequal multi-card trades are absent

- Canonical fact: `TRADE-04`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 5
- Exact evidence: “Ihr dürft mit einer unterschiedlichen Kartenanzahl handeln, z. B. zwei Blaue Bohnen gegen eine Gartenbohne.”
- Conflicting code: `propose_trade` contains one offered index and one requested index; `accept` removes exactly one card from each side.
- Expected: A consensual atomic exchange may contain unequal nonzero quantities, such as two cards for one.
- Implemented: Only one-for-one trades are representable. Separate gifts/trades are not an equivalent atomic agreement.
- Impact: Removes a material class of legal negotiations and exchanges.

5. Mandatory planting order is fixed rather than chosen by each recipient

- Canonical fact: `P3-02`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 7
- Exact evidence: “Jeder darf selbst entscheiden, in welcher Reihenfolge er die neuen Bohnenkarten anbaut.”
- Conflicting code: Accepted cards are appended to `s.planting`; `legal_actions()` and `plant_trade` always operate on `s.planting[0]`.
- Expected: Each recipient chooses the order in which their received/revealed cards are planted, including choices around intervening harvests.
- Implemented: Acceptance order followed by retained-reveal order determines a global FIFO planting sequence.
- Impact: Can force different harvests and field outcomes than a legal chosen ordering.

6. “Harvest at any time” is unavailable to inactive players and across many step boundaries

- Canonical fact: `HARV-01`
- Evidence type: `human_decision`
- Source: `RULES`, PDF page 7
- Exact evidence: “Du darfst jederzeit im Spiel deine Bohnenfelder abernten, auch wenn du nicht der aktive Spieler bist.”
- Conflicting code: `_harvest_actions()` is exposed only for the current `controller` during hand planting or that controller’s queued mandatory planting. It is absent during reveal, trade, response, draw, and for other players.
- Expected: Any owner may explicitly harvest between individual atomic game steps, including during another player’s turn.
- Implemented: Harvest access is phase- and controller-restricted.
- Impact: Players can miss strategically material harvest opportunities.

7. Approved private-hand observations are not implemented

- Canonical fact: `HAND-03`
- Evidence type: `human_decision`
- Source: `RULES`, PDF page 3
- Exact evidence: “Die erste verteilte Karte auf deiner Hand ist die vorderste Karte. Sie ist komplett sichtbar.”
- Approved expectation: An owner observes their complete ordered hand; opponents observe only its count.
- Conflicting code:
  - `GameState.hands` directly contains every player’s complete ordered hand.
  - No player-specific observation method exists.
  - `render()` displays only hand sizes, including to the hand’s owner.
- Expected: Player-relative observations showing the observer’s own hand and only opponent counts.
- Implemented: Direct state access reveals all hands, while the only rendered view reveals no player’s own cards.
- Impact: Depending on how the framework consumes state, this either leaks private information or withholds required information from the owner.

### Minor

None.

### Question — not scored

- Canonical fact: `SET-03`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 2
- Exact evidence: “Bestimmt einen Startspieler. Er erhält die Startspielerkarte.”
- `Game.initial_state()` always selects player 0, and the constructor provides no start-player parameter. Is player 0 defined by the surrounding interface as the already chosen start player? If not, start-player configuration and corresponding generalized tie-breaking are missing.

## Rule-area coverage

| Rule area | Assessment | Notes |
|---|---|---|
| Setup and inventory | Mostly covered | Correct 4–5 players, 129-card deck, ten selected types, five-card hands, and two starting fields. Starter selection is an interface question. |
| Hand order | Covered | Front planting and append-on-draw behavior preserve order. |
| Private information | Failed | No compliant player-relative observation. |
| Phase 1 planting | Covered | Mandatory first, optional second, no third, and forced legal harvest supported. |
| Reveal | Partly covered | Two-card reveal exists; depletion boundary is wrong. |
| Trading | Partly covered | Active-only participation, gifts, consent, and hand/face-up sources work; unequal quantities do not. |
| Mandatory planting | Partly covered | All queued cards must be planted, but order is forced. |
| Variant phase 4 | Failed | Active player draws three instead of every player drawing one. |
| Harvesting/meters | Mostly covered | Protection, normal meters, and Ackerbohne outcomes match approved facts; timing access does not. |
| Deck recycling/end timing | Failed | Empty-pile detection is delayed and phase-specific termination is wrong. |
| Terminal scoring | Failed | No final field harvest and hand cards incorrectly score. |
| Returns | Partly covered | Nonterminal zero and winner-style returns are acceptable, but terminal winner calculation uses invalid scores. |

## Missing deterministic scenarios

- Four- and five-player phase 4: verify one appended card per player in active-first clockwise order.
- First and second depletion where the final card is drawn during reveal, followed by immediate discard reshuffle.
- Third depletion on each of the first and second reveal draws: finish trading and phase-3 planting, then terminate without phase 4.
- Third depletion on each player position during variant phase 4: terminate immediately with no later player drawing.
- Final scoring with valuable fields and large hands: harvest fields and prove hands contribute zero.
- Final scoring tie with multiple seat combinations relative to the original start player.
- Atomic two-for-one and one-for-two trades, including hand and revealed-card offers.
- Multiple received cards whose chosen planting orders cause different forced-harvest outcomes.
- Legal inactive-player harvests between reveal, proposal, response, planting, and draw steps.
- Player-specific observations proving own ordered hand visibility, opponent counts only, and hidden deck order.
- Ackerbohne harvest matrix: one card; two cards before field 3; two after field 3; exactly three cards.

## Material questions for a human

- Does the framework treat player 0 as an externally chosen start player, or must this module expose start-player configuration?
- Is `GameState` guaranteed to remain engine-private behind an observation layer not supplied in this packet? If so, that layer must still provide the approved owner/opponent hand views; otherwise the module itself needs an observation API.

```text
score: 0.36
confidence: high
critical_issues: 1
major_issues: 6
minor_issues: 0
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true
```