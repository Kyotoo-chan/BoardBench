score: 0.20  
confidence: high

The implementation contains a reasonably developed base-game skeleton, but it cannot initialize the assigned 4–5-player Ackerbohne condition at all. Several independent phase, depletion, agency, and information-flow contradictions would remain after enabling that variant.

## Findings

### Critical

1. **The assigned Ackerbohne condition cannot be started**

   - Canonical facts:
     - `INV-03`
       - Evidence type: `rule_quote`
       - Source: `RULES`, PDF page 10
       - Exact evidence: “alle Bohnensorten aus dem Grundspiel sowie die Ackerbohnen und die Weinbrandbohnen”
     - `INV-04`
       - Evidence type: `user_observation`
       - Source: `COMPONENTS`, JSON Pointers `/bohnen/9/anzahl_karten` and `/bohnen/11/anzahl_karten`
       - Exact evidence: Weinbrandbohne `"anzahl_karten": 22`; Ackerbohne `"anzahl_karten": 3`
     - `ACKER-01`
       - Evidence type: `rule_quote`
       - Source: `RULES`, PDF page 11
       - Exact evidence: “Erntest du ein Feld mit zwei Ackerbohnen, erhältst du ein drittes Bohnenfeld.”
   - Conflicting symbols: `Game.initial_state`, `BASE_COUNTS`, `METERS`, `_harvest`
   - Expected: A 129-card deck containing the eight base beans, 22 Weinbrandbohnen, and three Ackerbohnen; Ackerbohne harvesting must support the third-field reward and its special outcomes.
   - Implemented: `initial_state()` raises `ValueError` for every variant except `"base"`. The claim that the Weinbrand count and meter are unavailable is contradicted by `COMPONENTS`. No Weinbrand cards/meter or Ackerbohne third-field mechanism is implemented.
   - Impact: The core game under the assigned source condition cannot begin.

### Major

2. **Phase 4 uses the base-game three-card draw instead of the selected variant’s distributed draw**

   - Canonical fact: `P4-01`
   - Evidence type: `rule_quote`
   - Source: `RULES`, PDF page 10
   - Exact evidence: “Anders als im Grundspiel zieht jeder von euch eine Karte vom Nachziehstapel und steckt sie hinter seine letzte Handkarte. Hierbei beginnt der aktive Spieler, die Mitspieler folgen im Uhrzeigersinn.”
   - Conflicting transition: `apply_action`, branch `draw_phase4`
   - Expected: Each player draws exactly one card, beginning with the active player and proceeding clockwise.
   - Implemented: A loop draws three cards, all into `s.hands[s.active]`.
   - Impact: Hand sizes, private information, deck consumption, depletion timing, and future mandatory plants are materially wrong.

3. **Pile depletion is detected one draw too late**

   - Canonical facts:
     - `DECK-01`
       - Evidence type: `human_decision`
       - Source: `RULES`, PDF page 9
       - Exact evidence: “Ziehst du die letzte Karte vom Nachziehstapel, dann mische die Karten des Ablagestapels.”
       - Approved resolution: first/second depletion immediately reshuffles discard and continues any owed draw.
     - `END-01`
       - Evidence type: `rule_quote`
       - Source: `RULES`, PDF page 9
       - Exact evidence: “Das Spiel endet, sobald der Nachziehstapel zum dritten Mal leer wird.”
   - Conflicting symbols: `_draw_one`, `_begin_trade`, `apply_action("draw_phase4")`
   - Expected: Depletion occurs when the last card is drawn. First/second depletion immediately fixes which discard cards enter the reshuffle; third depletion triggers the approved phase-specific ending transition.
   - Implemented: `exhaustions` increments only when a later draw is attempted while `deck` is already empty. If the last card satisfies the final owed draw, play advances without recording depletion.
   - Impact: Cards discarded or harvested during the unintended interval can enter a reshuffle they should have missed. Exact-card-boundary third depletion can permit further actions or another turn before termination.

4. **Players cannot choose the planting order of received and retained revealed cards**

   - Canonical fact: `P3-02`
   - Evidence type: `rule_quote`
   - Source: `RULES`, PDF page 7
   - Exact evidence: “Jeder darf selbst entscheiden, in welcher Reihenfolge er die neuen Karten anbaut.”
   - Conflicting symbols: `end_trade` construction of `s.pending`; `legal_actions` in `phase3`; `apply_action("plant")`
   - Expected: Each recipient explicitly chooses which of their pending cards to plant next, including before a necessary harvest.
   - Implemented: Only `s.pending[0]` can be planted. The order is imposed by player index, trade history, descending removal indices, and finally the retained reveals.
   - Impact: Planting order can decide which field must be harvested and therefore change scoring.

5. **The acting player can harvest another player’s fields**

   - Canonical fact: `HARV-01`
   - Evidence type: `human_decision`
   - Source: `RULES`, PDF page 7
   - Exact evidence: “Du darfst jederzeit im Spiel deine Bohnenfelder abernten, auch wenn du nicht der aktive Spieler bist.”
   - Conflicting symbols: `_harvest_actions`, `legal_actions`, `current_player`
   - Expected: A field’s owner may elect to harvest it between atomic steps.
   - Implemented: `_harvest_actions` exposes harvest actions for every player’s fields to whichever player `current_player()` identifies. The action includes an arbitrary player index and has no ownership check.
   - Impact: An active player or trade responder can force another player to lose a valuable field.

6. **No compliant private observation is provided; `render` exposes every ordered hand**

   - Canonical fact: `HAND-03`
   - Evidence type: `human_decision`
   - Source: `RULES`, PDF page 3
   - Exact source evidence: “Die erste verteilte Karte auf deiner Hand ist die vorderste Karte. Sie ist komplett sichtbar. Jede weitere steckt dahinter.”
   - Approved resolution: An owner sees their entire ordered hand; opponents see only its count.
   - Conflicting symbol: `render`
   - Expected: Observer-specific state exposing the requesting player’s hand and only opponent hand counts.
   - Implemented: `render()` serializes `"hands": s.hands`, revealing every player’s complete ordered hand. There is no observer-specific alternative.
   - Impact: Hidden information central to trading and planting decisions is lost.

### Minor

7. **The 14-card base bean is misidentified**

   - Canonical facts: `INV-02`, `GOLD-04`
   - Source: `RULES` page 2 and `COMPONENTS` pointer `/bohnen/3`
   - Expected: `Brechbohne`, 14 cards.
   - Implemented: `"Grüne Bohne"` with Brechbohne’s count and meter.
   - Impact: The arithmetic is internally consistent, but the component identity and player-facing trade information contradict the supplied condition.

8. **Terminal returns use an undocumented `1/0` scheme**

   - Approved executable convention: terminal returns may use winner-based `+1/-1` or a documented score-based equivalent.
   - Conflicting symbol: `returns`
   - Implemented: Winner receives `1`, all others `0`, with no documentation that this is the intended equivalent.
   - Raw coin totals and `winners` remain available, so this is localized rather than a winner-calculation failure.

## Rule-area coverage

| Rule area | Status | Notes |
|---|---|---|
| Selected setup/inventory | Fail | Ackerbohne variant rejected; 129-card deck absent |
| Deal and hand order | Partial | Five ordered cards dealt; private observation fails |
| Phase 1 planting | Largely correct | Mandatory first and optional second represented |
| Reveal/trading | Largely correct | Public reveals, bilateral consent, unequal trades supported |
| Phase 3 planting | Fail | Mandatory cards exist, but planting-order choice is absent |
| Variant phase 4 | Fail | Three cards to active player instead of one per player |
| Harvesting | Partial | Normal meters/protection mostly represented; ownership and Acker rules fail |
| Reshuffle/depletion | Fail | Empty pile recognized only on the following draw attempt |
| Terminal scoring | Partial | Final harvest and tie-break implemented; triggering can be late |
| Returns | Partial | Winner correct when reached; undocumented `1/0` payoff |
| Chance/private information | Fail | Deterministic shuffle exists, but all hands are exposed |

## Missing deterministic scenarios

- Initialize four- and five-player Ackerbohne games; verify exactly 129 cards before dealing and correct type counts.
- Phase 4 with four and five players, verifying one clockwise draw per player and append-only hand order.
- Phase 4 third depletion on each possible player’s draw, verifying immediate termination before the next player draws.
- First, second, and third depletion where the last deck card is exactly the final owed card.
- Harvest between emptying the pile and the next draw, proving newly discarded cards do not enter an already-required reshuffle.
- Third depletion on the first versus second reveal, followed by completion of trading and phase 3 but no phase 4.
- Phase 3 with multiple differently ordered pending cards whose planting orders require different harvests.
- Attempts by the active player, trade partner, and pending-card owner to harvest another player’s field.
- Observer views for owner versus each opponent.
- Ackerbohne harvests of one; two without field 3; two with field 3; and exactly three.
- Terminal tie-break with a nonzero original start-player seat.
- Conservation scenario tracking deck, discard, fields, hands, pending cards, reveals, and coin cards through harvest and reshuffle.

## Material questions for a human

- Is `render()` intended as a player-visible observation or only as an omniscient administrative/debug representation? If administrative only, the module still needs a player-specific observation API.
- Is seat 0 intentionally defined as the already-chosen start player by relabeling seats? If not, start-player configuration is also missing.
- No supplied gameplay ambiguity requires further rulebook adjudication; the material issues above are code contradictions or omissions.

```text
score: 0.20
confidence: high
critical_issues: 1
major_issues: 5
minor_issues: 2
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true
```