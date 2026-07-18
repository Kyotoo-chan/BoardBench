## Review result

**Score: 0.24 — confidence: high.**

The module captures several base-game mechanics correctly, including ordered-hand planting, homogeneous fields, standard harvest protection and yield tables, clockwise turns, and the basic third-depletion timing. However, it implements the 104-card base game instead of the selected 129-card Ackerbohne condition. It also materially misimplements phase 4, trade consent/action space, mandatory planting order, and information visibility.

## Findings

### Critical

1. **The selected Ackerbohne game condition is not implemented**

- Canonical facts:
  - `INV-03`
    - Evidence type: `rule_quote`
    - Source: `RULES`, PDF page 10
    - Exact evidence: “alle Bohnensorten aus dem Grundspiel sowie die Ackerbohnen und die Weinbrandbohnen”
  - `INV-04`
    - Evidence type: `user_observation`
    - Source: `COMPONENTS`, JSON Pointers `/bohnen/9/anzahl_karten` and `/bohnen/11/anzahl_karten`
    - Exact evidence: Weinbrandbohne `22`; Ackerbohne `3`
  - `ACKER-01`
    - Evidence type: `rule_quote`
    - Source: `RULES`, PDF page 11
    - Exact evidence: “Feld mit zwei Ackerbohnen, erhältst du ein drittes Bohnenfeld.”
- Conflicting symbols/transitions:
  - `BEANS`
  - `Game.initial_state`
  - Every `range(2)` field loop
  - `Game._harvest`
- Expected: A ten-type, 129-card deck containing 104 base cards, 22 Weinbrandbohnen, and 3 Ackerbohnen; Ackerbohne harvests can unlock a persistent third field or award three coins.
- Implemented: Only the eight base types and 104 cards exist. Every player permanently has exactly two fields. Ackerbohne, Weinbrandbohne, and all special Acker harvest outcomes are absent.
- Impact: This is a fundamentally different supplied game condition, affecting setup, probabilities, legal actions, harvesting, field capacity, scoring, and potentially the winner.

### Major

2. **Variant phase 4 gives three cards to the active player instead of one card to every player**

- Canonical fact: `P4-01`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 10
- Exact evidence: “zieht jeder von euch eine Karte … aktive Spieler … im Uhrzeigersinn”
- Conflicting symbols/transitions:
  - Legal action `"Drei Bohnenkarten nachziehen"`
  - Its `apply_action` branch
- Expected: Every player draws one card, beginning with the active player and continuing clockwise; each card appends to its recipient’s hand.
- Implemented: The active player alone draws up to three cards.
- Impact: Materially changes every player’s hand growth, turn opportunities, deck-depletion timing, and private information.

3. **Trade consent is not represented, and legal unequal exchanges are substantially restricted**

- Canonical facts:
  - `TRADE-04`
    - Evidence type: `rule_quote`
    - Source: `RULES`, PDF page 5
    - Exact evidence: “Ihr dürft mit einer unterschiedlichen Kartenanzahl handeln”
  - `TRADE-05`
    - Evidence type: `rule_quote`
    - Source: `RULES`, PDF page 6
    - Exact evidence: “beide Spieler müssen dem Handel zustimmen”
- Conflicting symbols/transitions:
  - `legal_actions`
  - `"Bohnenhandel"`
  - `"Bohnenhandel 2 gegen 1"`
  - `"Bohnenkarte schenken"`
  - Corresponding immediate-transfer branches in `apply_action`
- Expected: A proposal remains non-mutating until the counterparty explicitly accepts it; rejection must also be representable. Unequal exchanges are legal without the implementation’s fixed one-direction 2-for-1 restriction.
- Implemented: Selecting a trade immediately transfers cards, with no recipient accept/reject transition. Exchanges are limited to 1-for-1 or two active-player cards for one inactive-player card; the reverse unequal direction and larger legal quantities cannot be expressed.
- Impact: Removes a material participant decision and excludes valid trades.

4. **Recipients cannot choose the order of mandatory planting**

- Canonical fact: `P3-02`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 7
- Exact evidence: “Jeder darf selbst entscheiden, in welcher Reihenfolge er die neuen Bohnenkarten anbaut.”
- Conflicting symbols/transitions:
  - `owners[0]`
  - `s.pending[q][0]`
  - `s.exposed[0]`
  - `"Neue Bohnenkarte anbauen"`
- Expected: Each recipient chooses which received or retained revealed card to plant next, including choosing an order that determines which fields must be harvested.
- Implemented: The first card in `pending`, or first retained reveal, is forced. The action exposes only a field choice, not a card choice.
- Impact: Can force different harvests, coin yields, and final field configurations.

5. **The observation/action interface both leaks private hands and hides public reveals**

- Canonical facts:
  - `HAND-03`
    - Evidence type: `human_decision`
    - Source: `RULES`, PDF page 3
    - Exact approved evidence: “Owner sees the whole hand; opponents see only its count unless players voluntarily communicate.”
  - `P2-01`
    - Evidence type: `rule_quote`
    - Source: `RULES`, PDF page 5
    - Exact evidence: “Ziehe die obersten zwei Karten … für alle sichtbar”
- Conflicting symbols:
  - `Game.legal_actions`
  - `Game.render`
- Expected: Observations are perspective-specific: an owner sees their ordered hand, opponents see only its count, and revealed cards are public.
- Implemented:
  - `legal_actions` enumerates every opponent hand card as `(index, bean name)` in trade actions, revealing identities and order automatically.
  - `render` shows a full hand only for the active player, so a non-active observer cannot receive their own private hand through this interface.
  - `render` does not display `s.exposed` at all.
- Impact: Materially violates both private and public information rules and can directly influence trading decisions.

## Rule-area coverage

| Rule area | Status | Notes |
|---|---|---|
| Player count | Pass | Correctly restricts selected condition to 4–5 players. |
| Inventory/setup | Fail | Builds 104-card base deck, not selected 129-card deck. |
| Ordered hands | Partial | Front planting and append behavior work; observations leak order. |
| Phase 1 planting | Pass | First mandatory, second optional, third prohibited. |
| Field compatibility | Partial | Same-type enforcement works, but third field is impossible. |
| Reveal phase | Partial | Reveals up to two and handles phase-2 third depletion; public rendering is absent. |
| Trading | Fail | Consent and much of the legal exchange space are absent. |
| Mandatory planting | Fail | All cards are eventually required, but planting order is forced. |
| Phase 4 drawing | Fail | Three cards to active player instead of one to each player. |
| Standard harvesting | Pass | Protection, field emptying, and eight base yield tables match approved facts. |
| Acker harvesting | Fail | Entire subsystem absent. |
| Reshuffle/depletion | Mostly pass | First/second reshuffle and differentiated phase-2/phase-4 third depletion are represented. |
| Final scoring | Partial | Standard fields and tie-break work for fixed start player 0; selected Acker fields cannot score. |
| Returns | Pass | Nonterminal zero and winner-based terminal returns are permitted. |

## Missing deterministic scenarios

- Initial deck contains exactly 129 cards with the approved ten-type distribution.
- Two Ackerbohnen unlock field 3 while preserving fields 1–2.
- One, two-with-field-3-already-present, and three Ackerbohne harvest outcomes.
- Four- and five-player phase 4: exactly one draw per player in clockwise order.
- Third depletion on an intermediate phase-4 draw stops before the next player draws.
- Trade proposal rejection leaves all zones unchanged.
- Both directions of unequal exchanges, including one active-player card for two inactive-player cards.
- A recipient chooses between differently typed pending cards before planting.
- Planting-order choice changes which legal forced harvest occurs.
- Perspective checks ensuring opponent hands do not leak through legal actions.
- Public observations include both revealed cards.
- Phase-2 third depletion completes trading and all mandatory planting before final scoring.
- Tie-breaking after final harvest with the start player represented explicitly.

## Material questions for a human

- When an owed draw begins with both draw and discard piles empty, should the current phase advance, immediately end, or expose a dedicated no-card transition? The packet intentionally leaves this impossible/constructed-state behavior unresolved.
- Is player index `0` guaranteed by the host interface to represent the configured start player? If not, start-player selection and identity need an explicit state field. This is not scored separately because seat renumbering could satisfy the approved rule.

score: 0.24
confidence: high
critical_issues: 1
major_issues: 4
minor_issues: 0
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true