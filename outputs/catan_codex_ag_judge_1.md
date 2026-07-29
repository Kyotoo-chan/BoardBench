## 1. Score

`score: 0.62` — `confidence: high`

Most setup, production, robber, trade ratios, construction costs, development cards, privacy observations, and strict phase transitions match the approved facts. However, Longest Road is entirely unimplemented, so two public points are never awarded or transferred and valid games can produce the wrong winner. Two further decision/material issues affect Road Building stock and termination of domestic-offer construction.

## 2. Findings

### Critical — Longest Road is never calculated or awarded

- Canonical facts: `CAT-C-LR-THRESHOLD`, `CAT-C-LR-BRANCH`, `CAT-C-LR-OPP-BLOCK`, `CAT-C-LR-OWN-NOT-BLOCK`, `CAT-C-LR-TRANSFER`, `CAT-C-LR-HOLDER-TIE`, `CAT-C-LR-VACANT-TIE`, `CAT-C-SCORE-AWARDS`
- Evidence type: `rule_quote`
- Sources and evidence:
  - `CATAN22-RULES`, PDF p.3: “Wer zuerst eine durchgehende Straße aus mindestens 5 Einzelstraßen besitzt”
  - `CATAN22-RULES`, PDF p.3: “Abzweigungen zählen nicht.”
  - `CATAN22-RULES`, PDF p.3: “Sobald ein anderer Spieler eine längere Straße besitzt”
  - `CATAN22-ALMANAC`, PDF p.8: “Eigene Siedlungen und Städte unterbrechen die eigene Straße nicht.”
- Conflicting symbols/transitions: `special_cards.longest_road_owner`, `special_cards.longest_road_length`, `_score`, `build_road`, `place_free_road`, `build_settlement`.
- Expected: after every relevant road or settlement change, compute the approved maximum edge-simple trail, apply opponent-building interruptions and tie rules, update ownership immediately, and score the card as two points.
- Implemented: the fields initialize to `None` and `0` and are never updated. `_score` can count Longest Road only if some external mutation assigns it. Consequently, the award cannot be earned, transferred, lost after a split, or trigger immediate victory.

This is critical because it can directly suppress a valid two-point win or declare a different winner.

### Major — Road Building ignores the player’s remaining road stock

- Canonical fact: `CAT-C-BUILD-STOCK`
- Evidence type: `rule_quote`
- Source: `CATAN22-ALMANAC`, PDF p.6.
- Exact evidence: “Sind keine entsprechenden Figuren mehr im Vorrat, kann nicht gebaut werden.”
- Conflicting symbols/transitions: `_road_actions(d, p, free=True)` and the `place_free_road` transition.
- Expected: Road Building places at most the number of normally legal roads still present in the player’s supply. With zero roads, it resolves without placement; with one, it places at most one.
- Implemented: the stock check is guarded by `if not free`, so free-road actions remain legal at zero stock. Each placement then decrements `pieces["roads"]`, allowing negative stock and more physical roads than the color owns.

### Major — Domestic-offer construction is not finite

This is an adjudication-dependent deviation, not a contradiction of a clear printed rule.

- Canonical fact: `CAT-M-TRADE-PROTOCOL`
- Evidence type: `human_decision`
- Source: `CATAN22-V2-RULEFACTS`, “Approved decisions,” item 5.
- Exact evidence: “Domestic trade: finite bilateral offer builder, one partner, positive bundles on both sides, explicit accept/reject, atomic transfer only on acceptance.”
- Conflicting symbols/transitions: `legal_actions` in `trade_offer`, `add_trade_item`, and `propose_domestic_trade`.
- Expected: offer construction must have a finite state/action bound while retaining positive bilateral bundles and explicit consent.
- Implemented: `add_trade_item` is always available for every resource and can increment either bundle without limit. A player can remain forever in an unbounded sequence of distinct offer states. There is also no decrement/edit operation short of cancelling the whole offer.

## 3. Rule-area coverage

| Rule area | Result | Notes |
|---|---|---|
| Scope/player count | Pass | Restricts construction to three or four players |
| Illustrated setup | Pass | Board, colors, pieces, initial resources, robber, bank, and deck represented |
| Turn order/phases | Pass | Oldest seat designated as player 0; strict roll → trade → build |
| Production/bank shortage | Pass | Additive settlement/city production; per-resource all-or-none shortage |
| Seven/discards/robber | Pass | Correct threshold, floor-half discard, sequencing, move, and blind resource transfer |
| Domestic trade | Partial | Bilateral acceptance and atomic transfer work; offer builder is unbounded |
| Maritime trade | Pass | 4:1, 3:1, specialized 2:1, bank availability, harbor access |
| Construction | Partial | Costs, distance, connection, blocking, city replacement work; free-road stock fails |
| Longest Road | Fail | No calculation, ownership maintenance, tie handling, or scoring |
| Development cards | Partial | Timing and effects largely correct; Road Building stock fails |
| Largest Army | Pass | Threshold, public count, strict transfer |
| Private information | Pass/question | Observations hide identities; see interface question below |
| Victory/terminal | Partial | Immediate active-player victory works except for missing Longest Road points |
| Returns | Question | Winner mapping works, but `+1/-1` utility convention is not source-defined |

## 4. Deterministic scenarios needed

Without inspecting any existing scenario files, the following deterministic cases are necessary:

1. A fifth continuous road immediately awards Longest Road and can end the game at ten.
2. A strictly longer route transfers the award.
3. An opponent settlement splits the incumbent route:
   - incumbent remains in a leading tie;
   - leading tie excludes incumbent, making the card unowned;
   - a unique qualifying leader receives it.
4. Own settlements do not split a route; branches are not summed.
5. Road Building with road supply of zero, one, and two.
6. Road Building reaches ten on its first placement and cancels its unfinished second placement.
7. Domestic offer construction has a demonstrable finite bound and still supports multi-card bundles, rejection, and atomic acceptance.
8. Illustrated setup assertions for both three- and four-player configurations, including every initial road and settlement coordinate.

## 5. Material questions for a human

- What utility convention should `returns()` use? The packet determines the winner but does not decide whether losers receive `-1`, `0`, or another framework-specific payoff.
- Is the global `legal_actions()` result exposed to the currently forced responder? During discard or trade consent it includes the active player’s playable development-card types, which could reveal private development identities if shown to that responder. If action enumeration remains engine-private or actor-filtered, there is no leak.

```text
score: 0.62
confidence: high
critical_issues: 1
major_issues: 2
minor_issues: 0
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```