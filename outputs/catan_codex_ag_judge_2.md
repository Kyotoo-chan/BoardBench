## Assessment

`score: 0.66`  
`confidence: high`

The implementation gets most setup, turn flow, production, trading ratios, building costs, robber handling, development effects, privacy, and ordinary victory accounting right. The score is materially reduced because Longest Road is entirely inert, which can produce the wrong winner or delay a valid win. Static review only; the implementation was not executed.

## Findings

### Critical — Longest Road is never calculated, awarded, transferred, or removed

- Canonical facts:
  - `CAT-C-LR-THRESHOLD` (`CATAN22-V2-CLAIMS`, JSON Pointer `/claims/57`)
  - `CAT-C-LR-TRANSFER` (`/claims/61`)
  - `CAT-C-SCORE-AWARDS` (`/claims/85`)
- Evidence type: `rule_quote`
- Source evidence:
  - `CATAN22-RULES`, PDF p.3: “Wer zuerst eine durchgehende Straße aus mindestens 5 Einzelstraßen besitzt”
  - `CATAN22-RULES`, PDF p.3: “Sobald ein anderer Spieler eine längere Straße besitzt”
  - `CATAN22-ALMANAC`, PDF p.10: “Größte Rittermacht und Längste Handelsstraße je 2 Siegpunkte”
- Conflicting symbols/transitions:
  - `special_cards.longest_road_owner` and `longest_road_length` are initialized but never updated at [implementation.py:93](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-Kh4mJ2/boardbench_catan_codex_ag_judge_2_6105381d/implementation.py:93).
  - `_score()` merely reads the permanently unset owner at [implementation.py:215](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-Kh4mJ2/boardbench_catan_codex_ag_judge_2_6105381d/implementation.py:215).
  - `build_road`, `place_free_road`, and `build_settlement` perform no road recomputation at [implementation.py:296](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-Kh4mJ2/boardbench_catan_codex_ag_judge_2_6105381d/implementation.py:296).
- Expected: qualifying routes receive the two-point card immediately; longer routes transfer it, and opponent settlements can alter ownership under the approved tie rules.
- Implemented: the award remains permanently unowned during ordinary play. A player reaching ten through Longest Road is not declared the winner, and another player may consequently win instead.

### Major — Road Building can place roads after the player’s road supply is exhausted

- Canonical facts:
  - `CAT-C-BUILD-STOCK` (`CATAN22-V2-CLAIMS`, `/claims/49`)
  - `CAT-C-ROAD-BUILDING` (`/claims/73`)
- Evidence type: `rule_quote`
- Source evidence:
  - `CATAN22-ALMANAC`, PDF p.6: “Sind keine entsprechenden Figuren mehr im Vorrat, kann nicht gebaut werden.”
  - `CATAN22-ALMANAC`, PDF p.6: “2 Straßen bauen, ohne Rohstoffe zu zahlen”
  - The approved fact completes the latter as: “Road Building places two free roads subject to normal road rules.”
- Conflicting symbols/transitions:
  - `_road_actions(..., free=True)` bypasses the road-piece check at [implementation.py:114](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-Kh4mJ2/boardbench_catan_codex_ag_judge_2_6105381d/implementation.py:114).
  - `place_free_road` then decrements the supply unconditionally at [implementation.py:296](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-Kh4mJ2/boardbench_catan_codex_ag_judge_2_6105381d/implementation.py:296).
- Expected: no road may be placed with zero road pieces. Under approved shortage adjudication, Road Building places the maximum feasible number up to two.
- Implemented: with zero or one road remaining, the action generator can still offer two placements, driving the supply negative.

### Major — Domestic-trade offer construction is unbounded

This is adjudication-dependent, not a contradiction of a clear printed protocol.

- Canonical fact: `CAT-M-TRADE-PROTOCOL` (`CATAN22-V2-CLAIMS`, `/claims/99`)
- Evidence type: `human_decision`
- Source evidence:
  - `CATAN22-V2-RULEFACTS`, “Approved decisions,” item 5: “Domestic trade: finite bilateral offer builder, one partner, positive bundles on both sides, explicit accept/reject, atomic transfer only on acceptance.”
  - The underlying publisher gap is recorded at `/claims/99`: “The sources do not define a finite offer/consent protocol.”
- Conflicting symbols/transitions:
  - The building state always offers another `add_trade_item` for every resource and direction at [implementation.py:166](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-Kh4mJ2/boardbench_catan_codex_ag_judge_2_6105381d/implementation.py:166).
  - `add_trade_item` increments without a holding-based or finite cap at [implementation.py:274](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-Kh4mJ2/boardbench_catan_codex_ag_judge_2_6105381d/implementation.py:274).
- Expected: a finite bilateral offer can be proposed, accepted/rejected, or cancelled.
- Implemented: either bundle can be increased forever, producing an unbounded sequence of distinct offer states. Consent and atomic transfer are otherwise present.

### Minor — Played progress cards remain represented in the development hand

- Canonical fact: `CAT-C-PROGRESS-REMOVED` (`CATAN22-V2-CLAIMS`, `/claims/76`)
- `CATAN22-RULES`, PDF p.4: “Fortschrittskarten kommen aus dem Spiel.”
- `_play_card()` marks the card revealed but leaves it in `development_hand`, while also adding a played-card record at [implementation.py:227](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-Kh4mJ2/boardbench_catan_codex_ag_judge_2_6105381d/implementation.py:227).
- The card no longer enables play and does not score, so this is primarily a zone/inventory representation error rather than a core-flow defect.

## Rule-area coverage

| Rule area | Coverage | Result |
|---|---|---|
| Illustrated 3/4-player setup | Terrain, numbers, harbors, pieces, starting hands, robber, bank and deck | Conforming |
| Turn order and phases | Oldest-designated seat, clockwise order, strict roll→trade→build | Conforming |
| Production and shortages | Settlement/city production, robber blocking, all-or-none bank shortage | Conforming |
| Domestic/maritime trade | Ratios, harbor access, consent, atomic exchange | Partial: offer builder unbounded |
| Building legality | Costs, paid stock, distance, connectivity, city replacement | Partial: free-road stock violation |
| Longest Road | Threshold, route calculation, interruption, ties, transfer, scoring | Absent |
| Seven and robber | Discards, different hex, victim choice, blind seeded theft, resume | Conforming |
| Development cards | Timing, one-card limit, age restriction, effects, Largest Army | Mostly conforming; progress-zone defect |
| Private information/chance | Private identities, aggregate counts, seeded dice/deck/theft | Conforming to approved decisions |
| Victory and terminal state | Active-player immediate victory, VP cards, terminal returns | Partial: Longest Road points omitted |
| Serialization/returns | State/action envelopes and winner returns | Conforming on valid generated states |

## Missing deterministic scenarios

- Fifth connected road awards Longest Road and its two points.
- Longest Road causes an immediate tenth-point victory.
- A strictly longer road transfers the award.
- Opponent settlement splits a route, covering incumbent tie retention and vacant leading tie.
- Own settlement does not split a route; branches are not summed.
- Road Building with exactly zero, one, and two road pieces remaining.
- Road Building with fewer than two legal edges, followed by correct resumption.
- Trade offers cannot grow beyond a finite representable bundle; accept, reject, cancel, and repeated trades remain available.
- Each progress-card type leaves the development hand and enters an out-of-play representation.

## Material questions for a human

None. The source gaps relevant to these findings are already resolved by the approved human decisions. In particular, the approved maximum-edge-simple-trail decision resolves the publisher ambiguity around complex Longest Road loops, and the finite-offer decision resolves digital trade protocol.

```text
score: 0.66
confidence: high
critical_issues: 1
major_issues: 2
minor_issues: 1
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true
```