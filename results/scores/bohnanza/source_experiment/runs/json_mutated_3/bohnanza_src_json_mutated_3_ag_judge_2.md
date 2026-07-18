## Assessment

Score: **0.10**  
Confidence: **high**

The module implements a recognizable 104-card base game, but the assigned condition is the 129-card Ackerbohne variant. It omits both variant bean types, the third-field mechanic, and the variant draw phase. It also has material errors in depletion timing, trading, harvesting access, and private-information handling.

## Findings

### Critical

1. **Pile depletion is detected one draw too late**

- Classification: printed-rule contradiction.
- Canonical facts: `DECK-01`, `END-01`, `END-02`, `END-05`.
- Evidence:
  - `rule_quote`; source `RULES`, PDF p.9: “Ziehst du die letzte Karte vom Nachziehstapel, dann mische die Karten des Ablagestapels.”
  - `rule_quote`; source `RULES`, PDF p.9: “Das Spiel endet, sobald der Nachziehstapel zum dritten Mal leer wird.”
  - `human_decision`; source `RULES`, PDF p.9, stable locator p.9, exact evidence “endet, sobald”; approved expectation: a third depletion in phase 4 is immediately terminal after the draw that empties the pile.
- Conflicting code: `Game._draw_one`, especially the pre-draw `if not deck` check followed by `card = deck.pop()` without checking whether that pop emptied the pile.
- Expected: drawing the last card immediately records depletion, reshuffles after the first two depletions, or triggers the specified third-depletion boundary.
- Implemented: depletion is recorded only when a later draw is attempted against an already-empty tuple. If the last card is the final draw of an action, another phase or turn can begin before depletion is recognized. This can permit extra planting and changes which discard cards enter the next shuffle, and can delay game end.

### Major

2. **The assigned Ackerbohne deck and its harvesting mechanics are absent**

- Classification: printed-rule and user-observation contradiction.
- Canonical facts: `INV-03`, `INV-04`, `ACKER-01`–`ACKER-04`.
- Evidence:
  - `rule_quote`; source `RULES`, PDF p.10: “alle Bohnensorten aus dem Grundspiel sowie die Ackerbohnen und die Weinbrandbohnen.”
  - `user_observation`; source `COMPONENTS`, JSON Pointers `/bohnen/9/anzahl_karten` and `/bohnen/11/anzahl_karten`: Weinbrandbohne `22`; Ackerbohne `3`.
  - `rule_quote`; source `RULES`, PDF p.11: “Feld mit zwei Ackerbohnen, erhältst du ein drittes Bohnenfeld.”
  - `human_decision`; source `RULES`, PDF p.11: “bereits ein drittes Bohnenfeld … erhältst du … nichts.”
  - `human_decision`; source `RULES`, PDF p.11: “drei Ackerbohnen … drei Bohnentaler.”
  - `human_decision`; source `RULES`, PDF p.11: the source specifies no one-card reward; the approved result is a legal zero-value harvest when protection permits.
- Conflicting code: `BEANS`, `METER`, `initial_state`, the fixed two-field `GameState.fields` shape, `_harvest_actions`, `_can_plant`, and `_do_harvest`.
- Expected: a 129-card deck containing the eight base types, 22 Weinbrandbohnen, and 3 Ackerbohnen; Acker harvests must implement the approved one-, two-, and three-card results and potentially add a persistent third field.
- Implemented: only the eight base types and 104 cards exist. Every player permanently has exactly two fields, and normal meters are the only harvest behavior.

3. **Phase 4 uses the base-game draw rule instead of the assigned variant rule**

- Classification: printed-rule contradiction.
- Canonical fact: `P4-01`.
- Evidence: `rule_quote`; source `RULES`, PDF p.10: “zieht jeder von euch eine Karte … aktive Spieler … im Uhrzeigersinn.”
- Conflicting code: phase `"draw_three"`, action `("draw_three", p)`, and `apply_action`’s three-iteration loop.
- Expected: every player draws one card, active player first and then clockwise, each card appended to that player’s hand.
- Implemented: only the active player acts and draws up to three cards.

4. **Trades cannot exchange unequal nonzero quantities**

- Classification: printed-rule contradiction.
- Canonical fact: `TRADE-04`.
- Evidence: `rule_quote`; source `RULES`, PDF p.5: “Ihr dürft mit einer unterschiedlichen Kartenanzahl handeln, z. B. zwei Blaue Bohnen gegen eine Gartenbohne.”
- Conflicting code: `legal_actions` emits only `propose_trade(active, target, give, receive)` with one card on each side, or a one-card gift; `_accept` transfers at most one card each way.
- Expected: consensual exchanges may contain differing quantities, such as two cards for one.
- Implemented: only one-for-one trades and one-card gifts are representable.

5. **Non-acting players cannot harvest between steps**

- Classification: adjudication-dependent deviation.
- Canonical fact: `HARV-01`.
- Evidence: `human_decision`; source `RULES`, PDF p.7: “Du darfst jederzeit im Spiel deine Bohnenfelder abernten, auch wenn du nicht der aktive Spieler bist.”
- Conflicting code: `_harvest_actions` generates harvests exclusively for `state.actor`; most phases keep `actor` as the active player or current mandatory planter.
- Expected: any field owner may harvest between atomic steps, including during another player’s turn.
- Implemented: only the current actor can harvest. Other players have no action window except when temporarily made actor for a proposal or mandatory planting.

6. **Legal-action enumeration leaks opponents’ private hand contents**

- Classification: adjudication-dependent deviation.
- Canonical fact: `HAND-03`.
- Evidence: `human_decision`; source `RULES`, PDF p.3: “Die erste verteilte Karte auf deiner Hand ist die vorderste Karte. Sie ist komplett sichtbar.” The approved privacy decision states that the owner sees the whole ordered hand while opponents see only its count unless players voluntarily communicate.
- Conflicting code: during `"trade"`, `legal_actions` iterates `dict.fromkeys(state.hands[target])` and places each opponent bean identity into public `propose_trade` actions.
- Expected: absent voluntary communication, the active player can observe only each opponent’s hand count.
- Implemented: enumerating legal actions reveals every distinct bean type held by every opponent, even though `render` hides those hands.

7. **Forced harvesting is folded into planting rather than being an explicit prior transition**

- Classification: printed-rule/convention contradiction.
- Canonical fact: `P1-03`, reinforced by the approved executable and temporal conventions.
- Evidence: `rule_quote`; source `RULES`, PDF p.5: “Musst du eine Bohnensorte anbauen, hast aber kein Feld dafür zur Verfügung, musst du zuerst ein Feld abernten.”
- Conflicting code: `_can_plant` treats a mismatching field as plantable when `_harvest_allowed` is true; `_plant` then calls `_do_harvest` and plants within the same `plant_hand` or `plant_acquired` transition.
- Expected: the owner explicitly chooses and completes a legal harvest before performing the mandatory planting step.
- Implemented: a planting action can silently harvest its target field and plant the new bean atomically.

8. **The start player cannot be chosen or configured**

- Classification: printed-rule contradiction.
- Canonical fact: `SET-03`.
- Evidence: `rule_quote`; source `RULES`, PDF p.2: “Bestimmt einen Startspieler. Er erhält die Startspielerkarte.”
- Conflicting code: `Game.__init__` has no start-player argument; `initial_state` always sets `active=0`, `actor=0`; terminal tie-breaking assumes player 0 was the original start player.
- Expected: one configured/chosen player starts and permanently owns the start-player marker used for the tie-break.
- Implemented: seat 0 is unconditionally selected.

### Minor

9. **Final coin totals are calculated transiently but are not observable**

- Canonical fact: `END-03`, plus the explicit executable convention that raw terminal coin totals remain observable.
- Conflicting code: `returns` adds final harvest proceeds only to a local `scores` list. `state.coins` and `render(state)` continue to show pre-final-harvest totals.
- Impact: winner returns may incorporate normal final harvests, but consumers cannot inspect the actual final scores. This is localized relative to the larger missing Acker scoring behavior.

## Rule-area coverage

| Rule area | Status | Notes |
|---|---|---|
| Player count / initial fields | Partial | Correctly restricts to 4–5 and starts with two fields |
| Assigned inventory | Incorrect | Uses 104 base cards instead of the 129-card variant |
| Initial hands / order | Mostly correct | Five cards dealt singly; draws append |
| Turn order | Partial | Clockwise turns, but start player is fixed |
| Phase 1 planting | Partial | Mandatory/optional front cards present; forced harvest is atomic |
| Reveal | Partial | Two public cards, but depletion timing is wrong |
| Trading | Incorrect | Consent works; unequal multi-card exchanges are absent |
| Mandatory planting | Mostly correct | Received and retained reveals are planted in chosen type order |
| Variant phase 4 | Incorrect | Active player draws three instead of everyone drawing one |
| Normal harvesting | Partial | Meters/protection work; out-of-turn access is absent |
| Acker harvesting / field 3 | Absent | No Acker cards or third-field state |
| Private information | Incorrect | Legal actions disclose opponent bean types |
| Terminal timing | Incorrect | Emptying is registered on the following draw attempt |
| Final scoring / tie-break | Partial | Normal fields and fixed-seat tie-break calculated; totals hidden |

## Missing deterministic scenarios

- Initial deck composition is exactly 129 cards with 22 Weinbrand and 3 Acker cards.
- Two Ackerbohnen unlock a third field and discard both cards.
- Two Ackerbohnen with field 3 already present yield nothing.
- Three Ackerbohnen yield exactly three coins and do not unlock a field.
- One legally harvestable Ackerbohne yields zero.
- Phase 4 gives one card to every player in active-first clockwise order.
- First and second depletion are recorded when the last card is drawn and immediately reshuffle only the then-current discard.
- Third depletion on the last phase-4 draw terminates before another player draws.
- Third depletion during reveal finishes trading and mandatory planting but skips phase 4.
- A two-for-one trade transfers all three selected cards atomically after consent.
- An inactive player harvests between another player’s atomic steps.
- Legal-action observation does not reveal uncommunicated opponent bean identities.
- Forced planting exposes a distinct harvest choice before the planting action.
- Nonzero configured start players act first and control the final tie-break.
- Terminal observation exposes final raw coin totals after all fields are harvested.

## Material questions for a human

None. The approved facts resolve the material discrepancies identified above; no additional rulebook adjudication is needed.

score: 0.10
confidence: high
critical_issues: 1
major_issues: 7
minor_issues: 1
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true