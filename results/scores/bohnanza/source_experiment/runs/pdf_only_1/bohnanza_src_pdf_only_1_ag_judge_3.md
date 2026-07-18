## Review result

**Score: 0.20 — confidence: high.** The module is executable and preserves basic ordered hands, planting, normal harvest values, depletion counting, and final tie-breaking for a fixed seat-zero start. However, it models the 104-card base game rather than the required 129-card Ackerbohne condition. It also materially changes phase 4, restricts legal trading, removes planting-order choices, and lacks a valid per-player private observation interface.

## Findings

### Critical — Required Ackerbohne condition is not implemented

- Canonical facts: `INV-03`, `INV-04`, `ACKER-01`, `ACKER-02`, `ACKER-03`, `ACKER-04`
- Evidence types: `rule_quote`, `user_observation`, `human_decision`
- Sources and exact evidence:
  - `RULES`, PDF page 10: “alle Bohnensorten aus dem Grundspiel sowie die Ackerbohnen und die Weinbrandbohnen”
  - `COMPONENTS`, `/bohnen/9/anzahl_karten`: Weinbrandbohne `22`
  - `COMPONENTS`, `/bohnen/11/anzahl_karten`: Ackerbohne `3`
  - `RULES`, PDF page 11: “Feld mit zwei Ackerbohnen, erhältst du ein drittes Bohnenfeld.”
  - `RULES`, PDF page 11: “bereits ein drittes Bohnenfeld … erhältst du … nichts”
  - `RULES`, PDF page 11: “drei Ackerbohnen … drei Bohnentaler”
- Conflicting code:
  - `BEANS`
  - `Game.initial_state`
  - `Game.legal_actions`
  - `Game._harvest`
  - `Game._finish`
  - Every field iteration using `range(2)`
- Expected: A 129-card deck containing the eight base types, 22 Weinbrandbohnen, and 3 Ackerbohnen. Harvesting exactly two Ackerbohnen can unlock a persistent third field; exactly three award three coins; one is a legal zero-value harvest when protection allows.
- Implemented: Only the eight base types and 104 cards exist. Players permanently have two fields. Weinbrandbohne and Ackerbohne cannot be drawn, planted, or harvested. Injecting either type into a field would also cause `BEANS[cards[0]]` to fail.
- Impact: This is a different game condition, with different duration, planting pressure, available actions, and potentially a different winner.

### Major — Variant phase 4 uses the base-game draw rule

- Canonical fact: `P4-01`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 10
- Exact evidence: “zieht jeder von euch eine Karte … aktive Spieler … im Uhrzeigersinn”
- Conflicting code:
  - `Game.legal_actions`: `("Drei Bohnenkarten nachziehen",)`
  - `Game.apply_action`, transition for `"Drei Bohnenkarten nachziehen"`
- Expected: Each player draws one card, beginning with the active player and continuing clockwise. Each card appends to its recipient’s hand.
- Implemented: The active player alone draws three cards.
- Impact: Materially changes every turn’s hand distribution, private information, depletion timing, and player options.

### Major — Legal unequal trades and inbound gifts are missing

- Canonical facts: `TRADE-04`, `TRADE-07`
- Evidence type: `rule_quote`
- Sources:
  - `RULES`, PDF page 5: “Ihr dürft mit einer unterschiedlichen Kartenanzahl handeln, z. B. zwei Blaue Bohnen gegen eine Gartenbohne.”
  - `RULES`, PDF page 6: “Bohnenkarten schenken … muss dem Geschenk aber zustimmen.”
- Conflicting code:
  - `Game.legal_actions`
  - `"Bohnenkarte schenken"`
  - `"Bohnenhandel"`
  - `"Bohnenhandel 2 gegen 1"`
- Expected: Consensual unequal exchanges are legal regardless of which participant supplies the larger group, and a nonempty gift may flow in either direction between the active player and another player.
- Implemented: Only 1-for-1 and two-active-player-cards-for-one-other-player-card are represented. Gifts only flow from the active player to another player. For example, an inactive player cannot give the active player a card, nor offer two cards for one active-player card.
- Impact: Removes materially useful trading options from the central negotiation phase.

### Major — Recipients cannot choose mandatory planting order

- Canonical fact: `P3-02`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 7
- Exact evidence: “Jeder darf selbst entscheiden, in welcher Reihenfolge er die neuen Bohnenkarten anbaut.”
- Conflicting code:
  - `Game.legal_actions`, phase 3
  - `Game.apply_action`, `"Neue Bohnenkarte anbauen"`
- Expected: Each recipient chooses which received or retained revealed card to plant next, including choosing legal harvests between individual plantings.
- Implemented: The next card is forced to `pending[q][0]`; for the active player, all pending cards are forced before retained `exposed[0]`. Only the destination field is selectable.
- Impact: Planting order can determine which field must be harvested and therefore coin yield.

### Major — The active-player API can harvest another player’s field

- Canonical fact: `HARV-01`
- Evidence type: `human_decision`
- Source: `RULES`, PDF page 7
- Exact evidence: “Du darfst jederzeit im Spiel deine Bohnenfelder abernten, auch wenn du nicht der aktive Spieler bist.”
- Conflicting code:
  - `Game.current_player` always returns `state.active`
  - `Game.legal_actions` adds `("Ernten", p, f)` for every player
  - `Game.apply_action` performs the selected harvest without owner authorization
- Expected: A field’s owner chooses whether and when to harvest it, including during another player’s turn.
- Implemented: Under the module’s sole actor indicator, the active player receives actions that harvest any player’s eligible field. No actor or consent parameter establishes that the owner selected the action.
- Impact: Allows one player to force another player’s harvest unless an undocumented external dispatcher supplies ownership semantics.

### Major — Private observations are relative to the active player, not the observer

- Canonical fact: `HAND-03`
- Evidence type: `human_decision`
- Source: `RULES`, PDF page 3
- Exact evidence: “Die Reihenfolge der Karten auf deiner Hand darfst du während des gesamten Spiels nicht ändern … Du darfst die Karten nicht sortieren.”
- Approved complete expectation: “Owner sees the whole hand; opponents see only its count unless players voluntarily communicate.”
- Conflicting code: `Game.render`
- Expected: Every player can observe their own complete ordered hand regardless of whose turn it is, while seeing only opponents’ hand counts.
- Implemented: `render` exposes only the active player’s hand and hides every inactive player’s hand. It has no observer argument.
- Impact: Inactive players cannot inspect their own cards while evaluating trades or planning their actions.

## Rule-area coverage

| Rule area | Status | Notes |
|---|---|---|
| Setup and inventory | Failed | Correct player count and five-card hands; wrong 104-card deck and missing variant types |
| Ordered hands | Mostly covered | Front planting and append behavior present |
| Turn phases | Partial | Phase sequence present; phase 4 is materially wrong |
| Field planting | Partial | Same-type restriction present; no third field |
| Reveal and trading | Partial | Public reveal and some trades present; legal trade space restricted |
| Mandatory planting | Failed | All cards eventually plant, but recipient order choice is absent |
| Harvesting | Partial | Base yields/protection mostly correct; ownership and Acker rewards fail |
| Depletion and terminal timing | Mostly covered | Three-depletion structure and phase-2 deferral present |
| Final scoring and returns | Mostly covered | Final field harvest and winner returns present; fixed seat-zero convention |
| Private information | Failed | No observer-relative rendering |
| Elimination | Covered | None implemented |
| Action serialization | Covered | Tuple/JSON round trip appears consistent |

## Missing deterministic scenarios

- Initial deck contains exactly 129 cards before dealing, including 22 Weinbrandbohnen and 3 Ackerbohnen.
- Phase 4 distributes one card to every player clockwise, including depletion on an intermediate player’s draw.
- Two Ackerbohnen unlock a third field while preserving fields one and two.
- Two Ackerbohnen with an existing third field yield nothing and empty the harvested field.
- One- and three-card Ackerbohne harvest outcomes.
- Inactive player gives two cards for one active-player card, and gives a consensual gift to the active player.
- Recipient chooses between multiple pending cards whose planting orders lead to different forced harvests.
- Only a field’s owner can initiate its harvest during another player’s turn.
- Observer-relative rendering for every seat during another player’s turn.
- Third depletion during phase 4 stops before the next clockwise player draws.

## Material questions for a human

- Does the host framework have an undocumented mechanism that assigns global `"Ernten"` actions to the named field owner? If not, this is an authorization defect.
- Is `render` supplemented by an external observer-specific state filter? No such interface appears in the supplied implementation.
- No supplied rulebook issue requires clarification; the material deviations above are decided by approved facts.

score: 0.20
confidence: high
critical_issues: 1
major_issues: 5
minor_issues: 0
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true