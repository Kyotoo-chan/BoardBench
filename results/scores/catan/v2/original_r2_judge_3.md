score: 0.58  
confidence: high

The module implements most setup, production, trade, construction, development-card, robber, privacy, and immediate-victory mechanics coherently. The score is materially reduced because Longest Road—the major scoring mechanism most dependent on graph transitions—is entirely absent. Three additional issues affect stock safety and approved digital protocols.

## Findings

### Critical

1. Longest Road is never calculated, awarded, transferred, interrupted, or scored

- Canonical facts: `CAT-C-LR-THRESHOLD`, `CAT-C-LR-BRANCH`, `CAT-C-LR-OPP-BLOCK`, `CAT-C-LR-OWN-NOT-BLOCK`, `CAT-C-LR-TRANSFER`, `CAT-C-LR-HOLDER-TIE`, `CAT-C-LR-VACANT-TIE`, `CAT-C-SCORE-AWARDS`, `CAT-C-WIN-IMMEDIATE`.
- Evidence type: `rule_quote`.
- Sources and evidence:
  - `CATAN22-RULES`, PDF p.3; `/claims/57`: “Wer zuerst eine durchgehende Straße aus mindestens 5 Einzelstraßen besitzt”.
  - `CATAN22-RULES`, PDF p.3; `/claims/61`: “Sobald ein anderer Spieler eine längere Straße besitzt”.
  - `CATAN22-ALMANAC`, PDF p.8; `/claims/62`: “... ist der Besitzer ... am Gleichstand beteiligt, so behält er diese.”
  - `CATAN22-ALMANAC`, PDF p.8; `/claims/63`: when the incumbent is excluded from the leading tie, “so wird diese beiseite gelegt.”
  - `CATAN22-ALMANAC`, PDF p.10: “Größte Rittermacht und Längste Handelsstraße je 2 Siegpunkte”.
- Conflicting symbols/transitions:
  - `special_cards.longest_road_owner` and `longest_road_length` are initialized but never changed ([implementation.py](C:/Users/benti/AppData/Local/Temp/.ctx-mode-GnFg5X/boardbench_original_r2_judge_3_smkqd6h_/implementation.py:93)).
  - `build_road`, `place_free_road`, and `build_settlement` never recalculate routes or ownership ([implementation.py](C:/Users/benti/AppData/Local/Temp/.ctx-mode-GnFg5X/boardbench_original_r2_judge_3_smkqd6h_/implementation.py:296)).
  - `_score` can count an owner but no transition can create one ([implementation.py](C:/Users/benti/AppData/Local/Temp/.ctx-mode-GnFg5X/boardbench_original_r2_judge_3_smkqd6h_/implementation.py:215)).
- Expected: determine the approved maximum edge-simple trail after every road or route-interrupting settlement, apply threshold, blocking, incumbent-tie, vacant-tie, and strict-transfer rules, then immediately check victory.
- Implemented: Longest Road remains permanently unowned and worth zero. This can select the wrong winner or prevent an otherwise immediate win.

### Major — printed-rule contradiction

2. Road Building can exceed the player’s road-piece supply

- Canonical facts: `CAT-C-BUILD-STOCK`, `CAT-C-ROAD-BUILDING`.
- Evidence type: `rule_quote`.
- Source: `CATAN22-ALMANAC`, PDF p.6; `/claims/49`.
- Exact evidence: “Sind keine entsprechenden Figuren mehr im Vorrat, kann nicht gebaut werden.”
- Conflicting symbols/transitions:
  - `_road_actions(..., free=True)` bypasses the `pieces["roads"] <= 0` check ([implementation.py](C:/Users/benti/AppData/Local/Temp/.ctx-mode-GnFg5X/boardbench_original_r2_judge_3_smkqd6h_/implementation.py:114)).
  - `place_free_road` unconditionally decrements the reserve ([implementation.py](C:/Users/benti/AppData/Local/Temp/.ctx-mode-GnFg5X/boardbench_original_r2_judge_3_smkqd6h_/implementation.py:296)).
- Expected: Road Building places at most the feasible number of roads, also limited by the physical reserve.
- Implemented: a player with zero roads can still place free roads; a player with one can place two, producing a negative reserve.

### Major — approved human-decision deviation

3. Submitted discard escrow remains stealable and monopolizable

- Canonical fact: `CAT-M-DISCARD-ESCROW`.
- Evidence type: `human_decision`.
- Source: `CATAN22-V2-RULEFACTS`, `canonical_rulefacts.md § Approved decisions`, item 10; associated claim `/claims/122`.
- Exact evidence: “submitted private selections are unavailable to interrupts and settle together after every required submission.”
- Conflicting symbols/transitions:
  - `submit_discard` only records submission; selected resources remain in the player’s ordinary hand ([implementation.py](C:/Users/benti/AppData/Local/Temp/.ctx-mode-GnFg5X/boardbench_original_r2_judge_3_smkqd6h_/implementation.py:202)).
  - Development interrupts remain available during discard ([implementation.py](C:/Users/benti/AppData/Local/Temp/.ctx-mode-GnFg5X/boardbench_original_r2_judge_3_smkqd6h_/implementation.py:187)).
  - Knight theft and Monopoly consume the ordinary hand without excluding escrow ([implementation.py](C:/Users/benti/AppData/Local/Temp/.ctx-mode-GnFg5X/boardbench_original_r2_judge_3_smkqd6h_/implementation.py:267), [implementation.py](C:/Users/benti/AppData/Local/Temp/.ctx-mode-GnFg5X/boardbench_original_r2_judge_3_smkqd6h_/implementation.py:321)).
  - Final settlement later subtracts the original selection ([implementation.py](C:/Users/benti/AppData/Local/Temp/.ctx-mode-GnFg5X/boardbench_original_r2_judge_3_smkqd6h_/implementation.py:205)).
- Expected: submitted cards are escrowed and unavailable until all discards settle simultaneously.
- Implemented: an interrupt can transfer escrowed cards first, after which settlement may drive resource counts negative and break conservation.

4. Domestic offers have no approved finite construction bound

- Canonical fact: `CAT-M-TRADE-OFFER-BOUND`.
- Evidence type: `human_decision`.
- Source: `CATAN22-V2-RULEFACTS`, `canonical_rulefacts.md § Approved decisions`, item 9; associated claim `/claims/121`.
- Exact evidence: “give/take totals are capped by each side's public resource-hand size without revealing identities; acceptance validates actual holdings.”
- Conflicting symbol: `add_trade_item` is always available and increments the selected bundle without a cap ([implementation.py](C:/Users/benti/AppData/Local/Temp/.ctx-mode-GnFg5X/boardbench_original_r2_judge_3_smkqd6h_/implementation.py:168), [implementation.py](C:/Users/benti/AppData/Local/Temp/.ctx-mode-GnFg5X/boardbench_original_r2_judge_3_smkqd6h_/implementation.py:274)).
- Expected: stop additions once the applicable public hand-size total is reached.
- Implemented: arbitrarily large, impossible offers and an unbounded offer-state space can be constructed. Acceptance validation does not cure the missing construction bound.

### Minor

5. Played progress cards remain stored in the player’s development hand

- Canonical fact: `CAT-C-PROGRESS-REMOVED`.
- Evidence: `CATAN22-RULES`, PDF p.4; `/claims/76`: “Fortschrittskarten kommen aus dem Spiel.”
- `_play_card` marks the card revealed and adds a second record to `played_development`, but never removes it from `development_hand`.
- The card cannot be replayed, so the gameplay impact is localized, but serialized private state does not represent the printed destination accurately.

## Rule-area coverage

| Rule area | Coverage | Result |
|---|---|---|
| Scope and 3/4-player setup | Constructor range, colors, illustrated board, pieces, starting hands | No contradiction found |
| Inventories and bank/deck | Resources, development distribution, piece reserves | Pass except free-road stock |
| Turn flow | Roll → trade → build; clockwise; repeated actions | Pass |
| Production | Settlement/city values, additive production, robber blocking, approved shortages | Pass |
| Seven and robber | Threshold, floor-half, move, victim choice, blind theft | Pass except discard escrow |
| Domestic/maritime trade | Ratios, harbor access, consent, repeated trades | Pass except offer bound |
| Construction legality | Costs, distance, connectivity, blocking, city replacement | Pass |
| Development cards | Timing, one-card limit, purchase delay, effects, Largest Army | Mostly pass; progress-zone minor |
| Longest Road | Threshold, graph length, blocking, ties, transfer, scoring | Absent |
| Information/chance | Private identities, public aggregates, seeded chance | No material contradiction found |
| Terminal conditions/returns | Active-player immediate win and winner returns | Direct win logic passes; Longest Road corrupts reachable scores |
| Serialization | Action/state/observation envelopes | No rule-level blocker found |

## Missing deterministic scenarios

- Fifth connected road immediately awards Longest Road and its two points.
- A strictly longer route transfers the award and can immediately win.
- Opponent settlement interruption: incumbent-tied, incumbent-excluded tie, and unique new leader.
- Branch, loop, and figure-eight route measurements under the approved edge-simple-trail decision.
- Road Building with two, one, and zero road pieces remaining.
- Submitted discard followed by deterministic Knight theft of the selected resource.
- Submitted discard followed by Monopoly of a selected resource; verify nonnegative hands and conservation.
- Trade-offer additions at, below, and above each public hand-size cap.
- Played progress card leaves the private development-hand zone and remains non-replayable.
- Longest Road won on the first Road Building subaction immediately cancels the unfinished second placement.

## Material questions for a human

None. The supplied approved decisions resolve the material digital gaps relevant to these findings. In particular, Longest Road loop semantics, discard escrow, finite trade bounds, and immediate subaction victory already have packet-level decisions.

```text
score: 0.58
confidence: high
critical_issues: 1
major_issues: 3
minor_issues: 1
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true
```