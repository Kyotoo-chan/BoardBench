Score: **0.68**  
Confidence: **high**

The module implements most setup, planting, harvesting permissions, card conservation, phase-three planting, observation mapping, and winner selection correctly. Four material contradictions remain: two payout schedules, restricted trading, delayed recycling, and an incorrect phase-two third-depletion transition. Static review only; no code was edited or checks/scenarios inspected.

## Findings

### Major 1 — Garden and Soy harvest payouts are wrong

- Canonical facts: `BOHN-C-PAYOUT-GARTEN`, `BOHN-C-PAYOUT-SOJA`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`
- Locators:
  - `canonical_claims.json` JSON Pointer `/claims/56`, PDF page 1
  - `canonical_claims.json` JSON Pointer `/claims/59`, PDF page 1
- Exact evidence:
  - “Garden: size 1 pays 0, size 2 pays 2, size 3 or more pays 3.”
  - “Soy: thresholds 2/4/6/7 pay 1/2/3/4.”
- Conflicting code: `METERS` and `_harvest` in [implementation.py](C:/Users/benti/AppData/Local/Temp/.ctx-mode-rEgjZ1/boardbench_bohnanza_base_2023_codex_ag_judge_1_qq972wgn/implementation.py:13).
- Expected:
  - Garden pays 2 coins at size 2 and 3 coins at size ≥3.
  - Soy uses thresholds 2, 4, 6, 7.
- Implemented:
  - Garden uses `(2,3,4,5)`, paying only 1 at size 2 and eventually 4.
  - Soy uses `(2,3,5,7)`, overpaying at sizes 3 and 5.
- Impact: harvest totals and therefore the winner can be wrong.

### Major 2 — Printed unequal bundle trades cannot be represented atomically

- Canonical facts: `BOHN-C-TRADE-UNEQUAL`, additionally `BOHN-C-TRADE-CONSENT` and `BOHN-C-GIFT-CONSENT`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`
- Locators:
  - `/claims/34`, PDF page 2
  - `/claims/37`, PDF page 2
  - `/claims/40`, PDF page 2
- Exact evidence:
  - “Ihr dürft mit einer unterschiedlichen Kartenanzahl handeln.”
  - “Denn beide beteiligten Personen müssen dem Handel zustimmen.”
  - “Als besondere Form des Handels dürft ihr euch auch Bohnenkarten schenken. Die beschenkte Person muss dem Geschenk aber zustimmen.”
- Conflicting code: `_trade_actions` in [implementation.py](C:/Users/benti/AppData/Local/Temp/.ctx-mode-rEgjZ1/boardbench_bohnanza_base_2023_codex_ag_judge_1_qq972wgn/implementation.py:161).
- Expected: one mutually accepted proposal may exchange unequal bundles, such as two cards for one. A gift may also transfer a card with recipient consent.
- Implemented: every proposal contains exactly one active-player card and either zero or one partner card. Successive one-card trades are separate agreements and cannot preserve conditional bundle consent. A partner-to-active-player gift is also not expressible because every proposal requires an active-player offered card.
- Impact: a material portion of phase-two negotiation is absent.

### Major 3 — First/second depletion recycling can be delayed until a later draw

- Canonical fact: `BOHN-C-RECYCLE-FIRST-SECOND`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`
- Locator: `/claims/64`, PDF page 2
- Exact evidence: “Ziehst du die letzte Karte vom Nachziehstapel, mische die Karten des Ablagestapels. Danach legst du sie als neuen Nachziehstapel wieder verdeckt in die Tischmitte.”
- Conflicting transition: `_draw_one` in [implementation.py](C:/Users/benti/AppData/Local/Temp/.ctx-mode-rEgjZ1/boardbench_bohnanza_base_2023_codex_ag_judge_1_qq972wgn/implementation.py:281).
- Expected: after the last card causes the first or second depletion, the current discard is immediately shuffled into the new draw pile.
- Implemented: depletion is recorded after `pop()`, but recycling happens only at the beginning of a subsequent `_draw_one`. When the last card was also the final card requested by the current reveal/draw action, the state can remain unrecycled through later decisions.
- Impact: cards discarded by intervening harvests can incorrectly enter that recycle, altering chance outcomes and deck composition.

### Major 4 — Third depletion during phase-two reveal incorrectly enters phase four

- Canonical fact: `BOHN-C-END-PHASE2-CONTINUE`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`
- Locator: `/claims/67`, PDF page 2
- Exact evidence: “Sollte dies beim Aufdecken der Karten in der 2. Phase passieren … werden die 2. und die 3. Phase noch zu Ende gespielt.”
- Conflicting transitions:
  - Phase-three `pass` changes the phase to `draw` at [implementation.py](C:/Users/benti/AppData/Local/Temp/.ctx-mode-rEgjZ1/boardbench_bohnanza_base_2023_codex_ag_judge_1_qq972wgn/implementation.py:191).
  - `_finish` is invoked only by the subsequent `draw` action at [implementation.py](C:/Users/benti/AppData/Local/Temp/.ctx-mode-rEgjZ1/boardbench_bohnanza_base_2023_codex_ag_judge_1_qq972wgn/implementation.py:221).
- Expected: after finishing phases two and three, the game ends without phase four.
- Implemented: the game remains nonterminal in `draw` and requires a phase-four action before final harvesting.
- Impact: incorrect terminal timing and an extra decision boundary, including extra opportunities to harvest.

### Minor 1 — Snapshot validation accepts impossible base-game configurations

`_validate_state` checks only the aggregate `cards + coins == 104` invariant. It does not enforce the printed per-bean inventory or the required number of fields per player. Thus `state_from_data` can admit snapshots impossible under `BOHN-C-INV-*`, `BOHN-C-FIELDS-3`, and `BOHN-C-FIELDS-4-5`. Initial setup itself is correct, so this is localized to imported state integrity.

## Rule-area coverage

| Rule area | Result | Notes |
|---|---|---|
| Player count, fields, deck, deal | Pass | Correct 3–5 validation, 104-card inventory, field counts and five-card hands |
| Start player and clockwise order | Pass | Seeded selection matches approved decision; Start-card holder remains fixed |
| Hand order and visibility | Pass/Question | Front/append behavior and observations are correct; see legal-action privacy question |
| Phase-one planting | Pass | Mandatory front, optional second, no third; forced harvest is expressible |
| Reveal and ownership | Pass | Two cards revealed and initially owned by active player |
| Trading | Fail | Unequal bundles and reciprocal gift direction are incomplete |
| Phase-three planting | Pass | All staged/revealed cards must be planted; owner-selected order is available |
| Harvest legality | Pass | Off-turn harvest and singleton protection are implemented |
| Harvest payouts | Fail | Garden and Soy schedules are incorrect |
| Draw/recycle | Fail | Three-card order is correct; some recycling is delayed |
| Terminal flow | Fail | Phase-two third depletion incorrectly proceeds through `draw` |
| Final scoring/tiebreak | Pass subject to payouts | Final harvest, ignored hands, highest coins and clockwise-distance tiebreak are correct |
| Serialization/returns | Partial | Snapshot invariants are incomplete; return-vector meaning is not source-defined |

## Missing deterministic scenarios

- Every breakpoint for all eight beanometers, especially Garden sizes 2–5 and Soy sizes 2–7.
- A final-score case where the Garden or Soy error reverses the winner.
- Atomic 2-for-1 and 1-for-2 trades, including rejection with no transfer.
- A partner gifting a card to the active player.
- First/second depletion on the final card of a two-card reveal, verifying immediate recycle.
- First/second depletion on the third phase-four draw, followed by an intervening harvest; the newly discarded cards must not join the already-created pile.
- Third depletion on both the first and second phase-two reveal card, followed by phase-three completion and immediate termination without a draw action.
- Imported snapshots with incorrect bean multiplicities or wrong field counts.

## Material questions for a human

- `BOHN-M-EMPTY-DISCARD-RECYCLE`: what should happen when a nonterminal depletion has an empty or insufficient discard pile? The publisher packet explicitly leaves this undecided.
- Are `legal_actions` exposed directly to the acting player? `_trade_actions` enumerates bean identities from every opponent hand position. If players receive that list, it conflicts with approved human decision 4, which hides deeper opponent identities.
- Is `state_from_data` intended only for trusted engine-produced snapshots? If not, its missing inventory and structural validation warrants higher severity.
- What utility convention should `returns()` use? The rulebook identifies a winner but does not decide whether non-winners receive 0, −1, score differences, or another framework-specific value.

```text
score: 0.68
confidence: high
critical_issues: 0
major_issues: 4
minor_issues: 1
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```