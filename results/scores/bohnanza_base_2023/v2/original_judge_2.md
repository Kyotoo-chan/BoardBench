## 1. Score

**score: 0.70 — confidence: high**

The module implements most setup, planting, harvesting conservation, recycling, observation, final scoring, and tiebreak rules coherently. However, two beanometer curves are wrong, atomic unequal trades are unavailable, and third depletion during phase two incorrectly transitions through a phase-four action. These defects can materially alter strategy, scores, and winners.

All three canonical source hashes match `SOURCE_MANIFEST.json`. Review was static; the implementation was not executed.

## 2. Findings

### Major — Garden and Soy beanometers are incorrect

- Canonical facts: `BOHN-C-PAYOUT-GARTEN`, `BOHN-C-PAYOUT-SOJA`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 1
- Exact evidence:
  - “Garden: size 1 pays 0, size 2 pays 2, size 3 or more pays 3.”
  - “Soy: thresholds 2/4/6/7 pay 1/2/3/4.”
- Conflicting code: `METERS` and `_harvest()`
  - Garden is encoded as `(2, 3, 4, 5)`.
  - Soy is encoded as `(2, 3, 5, 7)`.
  - `_harvest()` counts satisfied thresholds.
- Expected:
  - Garden: 0/2/3 coins at sizes 1/2/3+, respectively.
  - Soy: thresholds 2/4/6/7.
- Implemented:
  - Garden pays 1 at size 2, 2 at size 3, and can pay 4 at size 5.
  - Soy overpays at sizes 3 and 5.
- Impact: harvest values and the eventual winner can change.

### Major — Unequal multi-card trades cannot be accepted atomically

- Canonical facts: `BOHN-C-TRADE-UNEQUAL`, `BOHN-C-TRADE-CONSENT`, `BOHN-C-TRADE-TRANSFER-ON-ACCEPT`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2
- Exact evidence:
  - “Ihr dürft mit einer unterschiedlichen Kartenanzahl handeln, z. B. zwei blaue Bohnen gegen eine Gartenbohne.”
  - “Ziehe eine Karte erst aus der Hand, sobald der Handel auch wirklich zustande kommt. Denn beide beteiligten Personen müssen dem Handel zustimmen.”
- Conflicting code: `Game._trade_actions()`, especially the fixed `offered=[x]` and either `requested=[]` or `requested=[y]`; `_accept()` transfers each such proposal independently.
- Expected: a two-for-one or other unequal bundle is one mutually accepted deal, with no component transferred before acceptance of the whole bundle.
- Implemented: only one-for-one exchanges and one-card gifts are expressible. Serial one-card deals are not equivalent because the first transfer becomes final before the second deal is accepted or rejected.

### Major — Third depletion during phase-two reveal requires a phase-four `draw` action

- Canonical facts: `BOHN-C-END-PHASE2-CONTINUE`, `BOHN-C-END-THIRD`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2
- Exact evidence: “Sollte dies beim Aufdecken der Karten in der 2. Phase passieren (auch wenn nur eine Karte aufgedeckt werden konnte), werden die 2. und die 3. Phase noch zu Ende gespielt.”
- Conflicting transition:
  - Phase-three completion changes `plant_received → draw`.
  - `legal_actions()` then exposes `draw`.
  - Only that action calls `_finish()` when `depletions >= 3`.
- Expected: after finishing phases two and three, the game ends without performing phase four.
- Implemented: the game remains nonterminal in `draw` and requires an action representing phase four. Although `_draw_one()` returns no cards, this is still an extra required phase/action and a possible integration-level stall point.

### Minor — Imported states need not preserve the printed deck or field configuration

- Canonical facts: `BOHN-C-FIELDS-3`, `BOHN-C-FIELDS-4-5`, `BOHN-C-INV-GARTEN` through `BOHN-C-INV-BLAU`
- Conflicting code: `_validate_state()`
- It checks only that total cards plus coins equal 104. It does not enforce:
  - three fields per player at three players;
  - two fields per player at four or five players;
  - the exact per-variety inventory.
- Consequently, `state_from_data()` accepts states impossible under the base game. This is localized to externally supplied states; ordinary `initial_state()` is correct.

### Question — Who controls globally listed off-turn and phase-three actions?

- Canonical facts/decision: `BOHN-C-PLANT-OWNER-ORDER`, `BOHN-M-PHASE3-INTERPLAYER-ORDER`
- Evidence type: `human_decision`
- Source: `BOHN-BASE-2023-V2-RULEFACTS`, “Approved human decisions”, item 2
- Exact evidence: “any affected owner with staged cards may plant next; all staged cards must finish before phase four, while each owner chooses their own card order.”
- Code concern:
  - `_decision_player()` names only the first owner with staged cards.
  - `legal_actions()` simultaneously returns planting and harvest actions whose `actor` may be another player.
- If `current_player` identifies the sole deciding agent, that agent can select another owner’s placement or harvest. If the host dispatches each action according to `Action.actor`, the representation may be valid. The implementation does not document which interpretation applies.

## 3. Rule-area coverage

| Rule area | Result | Notes |
|---|---|---|
| Setup and inventory | Mostly correct | Initial 104-card distribution, hand sizes, and fields are correct; imported-state validation is incomplete. |
| Hand order and planting | Correct | Front-only mandatory planting, optional second planting, and no third planting are represented. |
| Forced harvesting | Correct | A blocked mandatory planting can proceed after a legal harvest. |
| Reveal and phase order | Mostly correct | Normal flow works; third-depletion continuation has an extra draw transition. |
| Trading and gifts | Material gap | Consent and staging work, but atomic unequal bundles are absent. |
| Phase-three planting | Functionally represented | Owner-order/controller semantics need confirmation. |
| Harvest legality | Mostly correct | Singleton protection, off-turn availability, conservation, and emptying work. |
| Beanometers | Incorrect | Garden and Soy curves are wrong; the other six match approved claims. |
| Recycling/chance | Correct within source bounds | First/second recycling and seeded shuffling work; insufficient discard remains source-unspecified. |
| Private information | Mostly correct | Own hand and opponent size/front visibility follow the approved mapping. |
| Terminal scoring | Mostly correct | Final harvest, ignored hands, highest coins, and tiebreak are correct. |
| Returns | Acceptable | Binary winner utilities are an API choice not resolved by the rulebook. |

## 4. Missing deterministic scenarios

- Garden harvests at every attainable field size, checking payout and card conservation.
- Soy harvests immediately below, at, and above 2/4/6/7.
- Boundary tests for all eight beanometers, not just representative varieties.
- Atomic two-for-one and one-for-two trades, including acceptance and rejection without partial transfer.
- Third depletion on the first versus second phase-two reveal, asserting terminal state immediately after phase three and no `draw` action.
- Third depletion during phase four, asserting immediate final harvest and winner calculation.
- Multiple phase-three owners with different card-order and field-placement choices.
- Off-turn harvest ownership under the actual host/controller dispatch model.
- Deserialization rejection for wrong field counts and wrong per-variety inventories.

## 5. Material human questions

- Does the host treat `current_player` as the exclusive decision-maker, or dispatch globally legal actions using `Action.actor`? This determines whether phase-three planting and off-turn harvesting preserve player agency.
- Must `state_from_data()` reject rule-impossible states, or is it allowed to trust state payloads?
- Should `returns()` expose raw coin totals, winner-only utilities, or another framework convention? The supplied rule sources determine the winner but not the API payoff representation.

```text
score: 0.70
confidence: high
critical_issues: 0
major_issues: 3
minor_issues: 1
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true
```