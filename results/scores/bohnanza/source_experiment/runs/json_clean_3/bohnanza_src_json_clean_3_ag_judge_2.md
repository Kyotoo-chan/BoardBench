## Review result

`score: 0.63`  
`confidence: high`

The implementation gets most of the game’s machinery right: selected inventory, setup, ordered hands internally, four-phase turns, planting, harvest protection and payouts, Ackerbohne behavior, reshuffling, clockwise turns, scoring, and tie-breaking. Four material deviations remain, principally in trading, private observations, and the phase-2 third-depletion transition. None appears to prevent ordinary games from completing, so I found no critical issue.

## Findings

### Major 1 — Third depletion during phase 2 does not terminate immediately after phase 3

- Canonical facts: `END-02`, with `END-01`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 9
- Exact evidence: “Sollte dies beim Aufdecken der Karten in der 2. Phase „Bohnenkarten aufdecken und handeln“ passieren … spielt ihr die 2. und die 3. Phase noch zu Ende.”
- Conflicting transition: `apply_action()` → `finish_received` always transitions to `phase="draw_round"`; termination occurs only after a subsequent `draw_one` sees `empty_count >= 3`.
- Expected: When the third depletion occurs during the reveal, complete trading and mandatory planting, then score without entering phase 4.
- Implemented: The state enters phase 4 and requires an extra `draw_one` action before `_finish_game()`. This also exposes an additional between-actions harvesting window.

### Major 2 — Trades cannot identify a hand position or distinguish a hand card from an identical reveal

- Canonical fact: `TRADE-02`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 5
- Exact evidence: “Ihr dürft alle mit euren Handkarten handeln. Dabei spielt es keine Rolle, wo sich die Karten auf der Hand befinden.” Also: “Als aktiver Spieler darfst du auch mit den zwei aufgedeckten Karten handeln.”
- Conflicting symbols: `legal_actions()` actions `add_give(bean)` and `add_ask(bean)`; `accept_offer`; `_remove_multiset`.
- Expected: A player may select a card from any particular hand position without changing the order of the remaining cards, and the active player can choose whether an identical offered bean comes from hand or from the face-up area.
- Implemented: Offers specify only bean type. `_remove_multiset` removes the first matching hand occurrence, while `accept_offer` consumes matching face-up cards before hand cards. For hands such as `(A, X, A)`, trading the later `A` cannot be represented and can produce a different remaining front card.

### Major 3 — A partner cannot give a bean to the active player as a gift

- Canonical facts: `TRADE-07`, `TRADE-01`
- Evidence type: `rule_quote`
- Sources:
  - `RULES`, PDF page 6: “Als besondere Form des Handelns dürft ihr euch auch Bohnenkarten schenken. Der beschenkte Mitspieler muss dem Geschenk aber zustimmen.”
  - `RULES`, PDF page 5: “Nur du als aktiver Spieler darfst mit anderen Spielern handeln.”
- Conflicting symbol: `legal_actions()` only emits `propose_offer` when `s.offer_give` is nonempty.
- Expected: A consensual nonempty gift is legal with the active player as one participant, including an inactive player gifting cards to the active player.
- Implemented: An offer with empty active-player `give` and nonempty partner `ask` cannot be proposed. Gifts only work in the active-to-partner direction.

### Major 4 — Public rendering exposes every ordered hand

This is an adjudication-dependent deviation from an approved human decision, not a contradiction of explicit printed privacy language.

- Canonical fact: `HAND-03`
- Evidence type: `human_decision`
- Source: `RULES`, PDF page 3
- Exact source evidence: “Die erste verteilte Karte auf deiner Hand ist die vorderste Karte. Sie ist komplett sichtbar.”
- Approved decision: “Owner sees the whole hand; opponents see only its count unless players voluntarily communicate.”
- Conflicting symbol: `render()`, especially `"hands": [list(h) for h in s.hands]`.
- Expected: A player-specific observation reveals that player’s ordered hand and only opponent hand counts.
- Implemented: The sole rendered observation exposes all players’ complete ordered hands. No player-specific observation method is provided.

## Rule-area coverage

| Rule area | Status | Notes |
|---|---|---|
| Setup and inventory | Pass | 4–5 players, 129 correct bean cards, five-card deal, two fields |
| Hand ordering | Partial | Planting preserves order; position-specific trades do not |
| Turn and phase order | Partial | Normal order works; phase-2 third-depletion boundary is late |
| Phase-1 planting | Pass | Mandatory first, optional second, no third, forced harvest choices |
| Reveal and trade | Partial | Consent and received-card isolation work; selection and gift direction do not |
| Mandatory planting | Pass | All received/retained reveals planted with selectable order |
| Variant draw round | Pass | Active player first, then clockwise, one card each |
| Harvesting and payouts | Pass | Protection, tables, discard, coins, and field clearing align |
| Ackerbohne | Pass | One/two/three-card outcomes and third-field persistence align |
| Deck depletion | Partial | Reshuffles and phase-4 ending align; phase-2 ending is delayed |
| Private information | Fail | `render()` reveals all hands |
| Terminal scoring/returns | Pass | Final harvest, hand exclusion, coin winner, and tie-break align |
| Elimination | Pass | None implemented |

## Needed deterministic scenarios

- Third depletion on each of the two phase-2 reveal draws; after all phase-3 planting, the state must already be terminal and expose no `draw_one`.
- Accepted and rejected gifts in both directions between the active player and a partner.
- Trading the first versus later occurrence of the same bean from `(A, X, A)`, verifying the resulting front card.
- Offering a bean type present both in the active hand and face-up area, independently selecting each source.
- Player-specific observations verifying own ordered hand visibility and opponent count-only visibility.
- First and second depletion during the first of two owed reveals, verifying reshuffle and completion of the second reveal.
- Third depletion during each seat of phase 4, verifying immediate termination before later seats draw.
- Ackerbohne harvests of one, two without field 3, two with field 3, and three.

## Material questions for a human

- Is `render()` intended as a privileged debugging serialization rather than the player observation API? If so, a separate player-specific observation entry point still needs to be identified or implemented to satisfy `HAND-03`.
- Is player 0 deliberately the configured start player through seat relabeling? The implementation provides no constructor option for a different starting seat, but this is not penalized because seat relabeling can faithfully represent the chosen start player.

```text
score: 0.63
confidence: high
critical_issues: 0
major_issues: 4
minor_issues: 0
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true
```