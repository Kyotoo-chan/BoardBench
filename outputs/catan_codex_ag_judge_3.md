Score: **0.61**, confidence: **high**. The module implements most ordinary turn mechanics, but Longest Road is entirely inactive and three additional state-transition defects materially affect legal play. No code was edited.

## Findings

### Major

1. Longest Road is never calculated or awarded

- Canonical facts: `CAT-C-LR-THRESHOLD`, `CAT-C-LR-TRANSFER`, `CAT-C-LR-HOLDER-TIE`, `CAT-C-LR-VACANT-TIE`.
- Evidence type: `rule_quote`.
- Sources:
  - `CATAN22-RULES`, PDF p.3; `canonical_claims.json` `/claims/57`: “Wer zuerst eine durchgehende Straße aus mindestens 5 Einzelstraßen besitzt”
  - `CATAN22-RULES`, PDF p.3; `/claims/61`: “Sobald ein anderer Spieler eine längere Straße besitzt”
  - `CATAN22-ALMANAC`, PDF p.8; `/claims/62`: “Ist der Spieler, der die Sonderkarte ‚Längste Handelsstraße‘ besitzt, am Gleichstand beteiligt, so behält er diese.”
  - `CATAN22-ALMANAC`, PDF p.8; `/claims/63`: “Ist der Spieler, der die Sonderkarte ‚Längste Handelsstraße‘ besitzt, nicht am Gleichstand beteiligt, so wird diese beiseite gelegt.”
- Conflicting code: `build_road`, `place_free_road`, and `build_settlement` transitions; `_score`; `special_cards.longest_road_owner`.
- Expected: road placement and interruption must recompute the approved maximum route, award/transfer/vacate the card under the printed tie rules, and immediately apply its two points.
- Implemented: `longest_road_owner` is initialized to `None` and never changed; `longest_road_length` is also never updated. Legitimate wins can therefore be delayed or awarded to the wrong player.

2. Road Building ignores the player’s remaining road stock

- Canonical facts: `CAT-C-BUILD-STOCK`, `CAT-C-ROAD-BUILDING`.
- Evidence type: `rule_quote`.
- Sources:
  - `CATAN22-ALMANAC`, PDF p.6; `/claims/49`: “Sind keine entsprechenden Figuren mehr im Vorrat, kann nicht gebaut werden.”
  - `CATAN22-ALMANAC`, PDF p.6; `/claims/73`: “2 Straßen bauen, ohne Rohstoffe zu zahlen”; the complete rule continues: “Hierbei müssen die üblichen Regeln für den Bau von Straßen beachtet werden.”
- Conflicting code: `_road_actions(d, p, free=True)` at lines 114–117 and `place_free_road` at lines 296–301.
- Expected: Road Building places at most the feasible number up to two, including the normal piece-stock restriction.
- Implemented: the `free=True` branch bypasses the road-stock test. A player with zero or one road remaining can place two roads and drive `pieces["roads"]` negative.

3. Committed discards are unsafe under approved development-card interrupts

- Canonical facts: `CAT-M-DISCARD-PROTOCOL`, `CAT-M-DEV-BOUNDARY`.
- Evidence type: `human_decision`.
- Source: `CATAN22-V2-RULEFACTS`, `canonical_rulefacts.md`, “Approved decisions,” items 4 and 7:
  - “seven discards are private and simultaneous”
  - “an eligible card may interrupt pending discard … resolve it on a pending-state stack, then resume unless terminal.”
- Conflicting code: `submit_discard`/`_next_discard` at lines 202–209, interrupt exposure at lines 187–189, and `play_monopoly` at lines 321–324.
- Expected: a submitted private discard must remain valid when an interrupt resolves, and the discard sequence must resume without invalid card counts.
- Implemented: submitted cards are only recorded, not removed, until every player submits. During a later player’s discard, the active player can interrupt with Monopoly or Knight and remove a resource already committed by an earlier submitter. Final settlement blindly subtracts the old selection, potentially creating negative resource counts.

4. Empty-handed adjacent players are offered as robbery victims

- Canonical facts: `CAT-C-ROBBER-CHOOSE`, `CAT-C-ROBBER-STEAL`.
- Evidence type: `rule_quote`.
- Sources:
  - `CATAN22-ALMANAC`, PDF p.9; `/claims/69`: “darf er sich aussuchen, wen er beraubt”
  - `CATAN22-RULES`, PDF p.4; `/claims/70`: “zieht ... 1 Rohstoffkarte”
- Conflicting code: `move_robber` victim construction at lines 261–265 and `steal_resource` at lines 267–273.
- Expected: victim choices comprise adjacent eligible opponents from whom a resource can be stolen; if none is eligible, the approved no-victim decision performs no transfer.
- Implemented: every adjacent opponent with a building is listed, regardless of resource count. When both an empty opponent and a resource-holding opponent are adjacent, selecting the empty opponent improperly avoids the transfer.

### Minor

5. A permitted same-resource 4:1 maritime exchange is omitted

`CAT-C-MARITIME-4` permits four identical cards to retrieve one resource “seiner Wahl”; this includes retrieving the same resource just returned, for a five-card exchange with net loss of three. `legal_actions` line 164 excludes every `receive == give` action at all ratios. The 3:1 and 2:1 Almanac wording expressly requires an “andere” resource, so this finding is limited to 4:1.

6. Played progress cards remain in `development_hand`

Under `CAT-C-PROGRESS-REMOVED`, “Fortschrittskarten kommen aus dem Spiel.” `_play_card` marks the card revealed and appends another record to `played_development`, but leaves the original card in the player’s development hand. It cannot be replayed, so this is primarily a zone/inventory-model discrepancy.

7. The approved finite trade-offer builder is unbounded

The human decision requires a “finite bilateral offer builder.” `add_trade_item` can increment either bundle indefinitely without a holding-based bound or decrement action. Acceptance is correctly atomic and availability-checked, but the offer-construction state space itself is unbounded.

### Question

8. May a player decline a Knight robbery?

`CAT-C-KNIGHT-STEAL` quotes “Dann darf er … 1 Rohstoffkarte rauben.” The implementation provides no skip action when at least one adjacent owner exists. The word “darf” grants the robbery but the packet does not explicitly state whether declining it is legal; this should not be scored without a human interpretation.

## Rule-area coverage

| Rule area | Status | Notes |
|---|---|---|
| Beginner setup, 3/4 players | Covered | Illustrated board, colors, pieces, starting resources, bank and deck represented |
| Turn order and phases | Covered | Clockwise strict roll → trade → build |
| Production and shortages | Covered | Settlement/city production, robber blocking, all-or-none shortage decision |
| Domestic/maritime trade | Partial | Consent and harbor ratios work; 4:1 same-resource action absent; builder unbounded |
| Normal construction | Covered | Costs, connectivity, distance rule, city replacement and stock |
| Longest Road | Missing | No calculation, ownership, interruption, tie handling, or scoring |
| Largest Army | Covered | Three-Knight threshold and strictly larger transfer |
| Seven/discards/robber | Partial | Base sequence works; interrupt corruption and victim eligibility defects |
| Development cards | Partial | Effects and timing mostly covered; free-road stock and removed-zone issues |
| Chance/private information | Covered | Seeded dice/deck/theft and private observations represented |
| Scoring, victory, returns | Partial | Immediate active-player victory works, but Longest Road points never exist |
| Serialization/actions | Covered | Named and structured action/state/observation conversions supplied |

## Missing deterministic scenarios

- Gain Longest Road at five, transfer it to a strictly longer route, and resolve both incumbent and non-incumbent interruption ties.
- Play Road Building with zero and one road left; assert maximum feasible placement and nonnegative stock.
- Submit a discard, interrupt a later discard with Monopoly and Knight, then verify the committed selection and resource invariants.
- Move the robber beside one empty and one nonempty opponent; only the resource-holding opponent should be eligible. Also cover all-empty adjacency.
- Execute a 4:1 same-resource maritime trade and verify the net three-card reduction; separately reject same-resource 3:1 and 2:1 trades.
- Verify progress cards leave the active development-hand zone after play.
- Bound trade-offer construction and test cancellation, rejection, changed holdings, and atomic acceptance.

## Material questions for a human

- Does “darf … rauben” permit explicitly declining a Knight robbery?
- What exact resource-based cap should the approved finite domestic-offer builder impose: current holdings, total physical bank inventory, or another fixed bound?
- Should a played progress card be physically moved to a removed zone, or is retaining an inert revealed record in `development_hand` acceptable for the state contract?

```text
score: 0.61
confidence: high
critical_issues: 0
major_issues: 4
minor_issues: 3
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```