score: 0.62, confidence: high. The module covers most printed setup and turn structure, including the emphasized Garden/Soy meters, unequal multi-card transfers, and third-depletion phase-two exception. However, eager trade enumeration threatens ordinary game completion, and three clear rules materially affect planting choice, payouts, and tie winners.

## Findings

### Critical

1. Trade action enumeration grows exponentially and can exhaust memory during normal play.

- Canonical facts: `BOHN-C-TRADE-ANY-HAND-POSITION`, `BOHN-C-TRADE-UNEQUAL`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2; JSON Pointers `/claims/32` and `/claims/34`
- Exact evidence:
  - “Ihr dürft alle mit euren Handkarten handeln. Dabei spielt es keine Rolle, wo sich die Karten auf der Hand befinden.”
  - “Ihr dürft mit einer unterschiedlichen Kartenanzahl handeln.”
- Conflicting code: `Game._nonempty_subsets`; `Game.legal_actions`, especially `offers = list(...)` and the nested offered/requested loops at lines 139–156.
- Expected: Legal multi-card and unequal bundles must remain usable as hands grow.
- Implemented: Every subset of the active player’s hand plus revealed cards is eagerly crossed with every subset of each partner’s hand. With 10 hand cards plus two revealed against a 10-card partner, this creates over four million two-sided proposals for that partner alone. Because hands can legally grow, ordinary play can become prohibitively slow or run out of memory.
- This is not a criticism of multi-card trading—the approved facts expressly require it. The failure is the eager enumeration strategy.

### Major

2. Owners cannot choose the planting order of staged cards.

- Canonical fact: `BOHN-C-PLANT-OWNER-ORDER`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2; JSON Pointer `/claims/44`
- Exact evidence: “Jede Person darf selbst entscheiden, in welcher Reihenfolge sie die neuen Bohnenkarten anbaut.”
- Conflicting code: `Game.legal_actions` lines 160–171, `Game.apply_action` lines 245–248, and trade transfer ordering at lines 295–301.
- Expected: Each owner selects which of their own received or untraded revealed cards to plant next.
- Implemented: Only `pending_received[owner][0]` or `revealed[0]` can be planted. Acceptance also imposes a sorting-derived order on transferred cards. No action permits selecting another staged card first.
- Consequence: The forced order can change which field must be harvested and therefore change scores.

3. The Red Bean payout meter is incorrect.

- Canonical fact: `BOHN-C-PAYOUT-ROT`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 1; JSON Pointer `/claims/57`
- Exact evidence: “[Visual transcription of the named card’s Bohnometer, page 1] Red: thresholds 2/3/4/5 pay 1/2/3/4.”
- Conflicting code: `METERS["rote_bohne"]` at line 13.
- Expected: Counts 2, 3, 4, and 5 pay 1, 2, 3, and 4 coins respectively.
- Implemented: Thresholds are 3, 6, 7, and 8. Thus two Red Beans incorrectly pay zero, while many attainable harvest sizes are substantially underpaid.
- The emphasized Garden and Soy meters are correct.

4. The Start-card holder incorrectly wins ties whenever included among the tied leaders.

- Canonical fact: `BOHN-C-TIEBREAK`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2; JSON Pointer `/claims/73`
- Exact evidence: “Bei einem Gleichstand gewinnt die Person, die im Uhrzeigersinn am weitesten weg von der Person mit der Start-Karte sitzt.”
- Conflicting code: `Game._finish`, lines 221–223.
- Expected: Select the tied leader with the greatest clockwise distance from the fixed Start-card holder.
- Implemented: The clockwise order includes the Start-card holder last and is then reversed. Consequently, the Start-card holder is checked first and wins any tie in which they participate.

No separate minor findings.

## Rule-area coverage

| Rule area | Assessment | Notes |
|---|---|---|
| Player counts and setup | Covered | 3–5 validation, correct fields, inventory, five-card hands, seeded start |
| Hand order and phase-one planting | Covered | Mandatory front, optional second, no third |
| Phase-two reveal | Covered | Two sequential cards subject to depletion |
| Trading and gifts | Partial | Atomic consent and multi-card transfers exist; action enumeration is unsafe |
| Phase-three planting | Contradicted | All cards are eventually mandatory, but owner-chosen order is absent |
| Harvesting | Partial | Anytime/off-turn and singleton protection work; Red payout is wrong |
| Draw and recycling | Covered with source gap | Sequential three-card draw and sufficient-discard recycling work |
| Third depletion | Covered | Phase-two continuation and immediate outside-phase-two termination are implemented |
| Final scoring | Partial | Final harvest and highest score work; one tiebreak class is wrong |
| Chance/private information | Mostly covered | Seeded chance and player observations follow the approved hand-visibility mapping |
| Returns | Covered | Winner receives 1; others receive 0 |

## Missing deterministic scenarios

- Reachable hand-growth states that bound `legal_actions` runtime and memory while preserving arbitrary multi-card proposals.
- Red Bean harvests at sizes 1–8, especially exact boundaries 2, 3, 4, and 5.
- Two received cards where choosing their order changes the required harvest.
- Two untraded revealed cards planted in either owner-selected order.
- Tied leaders including the Start-card holder, for 3-, 4-, and 5-player games.
- Ties excluding the Start-card holder, checking the farthest-clockwise tied leader.
- Mixed hand/revealed multi-card trades with unequal bundles, rejection conservation, and acceptance conservation.
- Third depletion on the first versus second phase-two reveal, confirming phase four is never entered.

## Material questions for a human

- `BOHN-M-EMPTY-DISCARD-RECYCLE`: What should happen when the first or second depletion occurs with an empty or insufficient discard pile? The packet explicitly leaves this undecided; `_draw_one` currently returns no further cards and may permit nonterminal turns with an empty deck.
- Should identities of sideways staged cards be included in player observations? The printed layout appears public, but the approved observation decision explicitly settles only hand visibility. The implementation exposes only staged-card counts.
- Is `render()` strictly privileged/debug output? It prints every complete hand, unlike the approved per-player observation mapping. If player-facing, it would leak deeper opponent hand identities.

score: 0.62
confidence: high
critical_issues: 1
major_issues: 3
minor_issues: 0
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true