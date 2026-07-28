score: 0.55  
confidence: high

The module implements most setup, planting, ordinary harvesting, turn order, final harvesting, and tiebreak machinery. However, two wrong payout schedules can change scores/winners, legal multi-card trades are absent, recycling occurs at the wrong boundary, the phase-two third-depletion exception requires an illegal phase-four action, and the legal-action surface leaks private hand identities. Provenance hashes for all assigned sources and rendered pages match their manifests.

## Findings

### Major — Garden-bean payouts are wrong

- Canonical fact: `BOHN-C-PAYOUT-GARTEN`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, canonical_rulebook.pdf, page 1
- Exact evidence: “[Visual transcription of the named card’s Bohnometer, page 1] Garden: size 1 pays 0, size 2 pays 2, size 3 or more pays 3.”
- Conflicting code: `METERS["gartenbohne"] = (2, 3, 4, 5)` and `_harvest()` in [implementation.py](C:/Users/benti/AppData/Local/Temp/.ctx-mode-rEgjZ1/boardbench_bohnanza_base_2023_codex_ag_judge_3_azcmm4n_/implementation.py:13).
- Expected: field sizes 1/2/3+ pay 0/2/3.
- Implemented: sizes 1–5 pay 0/1/2/3/4. This underpays sizes 2–3 and can overpay larger fields, directly changing final scores and winners.

### Major — Soy-bean payout thresholds are wrong

- Canonical fact: `BOHN-C-PAYOUT-SOJA`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, canonical_rulebook.pdf, page 1
- Exact evidence: “[Visual transcription of the named card’s Bohnometer, page 1] Soy: thresholds 2/4/6/7 pay 1/2/3/4.”
- Conflicting code: `METERS["sojabohne"] = (2, 3, 5, 7)` and `_harvest()`.
- Expected: thresholds 2/4/6/7.
- Implemented: thresholds 2/3/5/7. Three-card and five-card fields receive an extra coin, potentially changing the winner.

### Major — Legal unequal multi-card trades cannot be proposed atomically

- Canonical fact: `BOHN-C-TRADE-UNEQUAL`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, canonical_rulebook.pdf, page 2
- Exact evidence: “Ihr dürft mit einer unterschiedlichen Kartenanzahl handeln.”
- Conflicting code: `_trade_actions()` only creates one-card gifts or one-for-one trades; see [implementation.py](C:/Users/benti/AppData/Local/Temp/.ctx-mode-rEgjZ1/boardbench_bohnanza_base_2023_codex_ag_judge_3_azcmm4n_/implementation.py:161).
- Expected: bundles such as two cards for one or one for three are one mutually accepted trade.
- Implemented: only `[one offered]/[]` and `[one offered]/[one requested]`. Successive deals are not equivalent: each component can be independently accepted or rejected, so the parties cannot condition consent on the complete bundle. This also limits gifts to active-player-originated offers.

### Major — First and second depletion recycling is delayed

- Canonical fact: `BOHN-C-RECYCLE-FIRST-SECOND`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, canonical_rulebook.pdf, page 2
- Exact evidence: “Ziehst du die letzte Karte vom Nachziehstapel, mische die Karten des Ablagestapels. Danach legst du sie als neuen Nachziehstapel wieder verdeckt in die Tischmitte.”
- Conflicting transition: `_draw_one()` increments `depletions` when the last card is removed but recycles only on a later `_draw_one()` call.
- Expected: the discard is shuffled into the replacement draw pile upon drawing the last card.
- Implemented: if the last required reveal or third draw empties the pile, the state remains with an empty deck until a future draw. Intervening harvests can add cards to the discard that are then incorrectly included in that recycle, altering chance outcomes and visible deck size.

### Major — Third depletion during phase two incorrectly enters phase four

- Canonical fact: `BOHN-C-END-PHASE2-CONTINUE`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, canonical_rulebook.pdf, page 2
- Exact evidence: “Sollte dies beim Aufdecken der Karten in der 2. Phase passieren … werden die 2. und die 3. Phase noch zu Ende gespielt.”
- Conflicting transition: `pass` from `plant_received` always sets `phase = "draw"`; `_finish()` is invoked only after a subsequent `draw` action.
- Expected: after third depletion during reveal, complete phases two and three, skip phase four, and terminate immediately after phase three.
- Implemented: the game remains nonterminal in `draw`, exposes a phase-four action, and terminates only after that action. Although no further card is drawn, this contradicts the prescribed terminal boundary and can stall controllers waiting for the correct terminal state.

### Major — Legal actions expose deeper opponent hand identities

This is adjudication-dependent rather than a direct printed-rule contradiction.

- Canonical fact: `BOHN-M-OBS-DEEPER-HAND`
- Evidence type: `human_decision`
- Source: `BOHN-BASE-2023-V2-RULEFACTS`, “Approved human decisions,” item 4
- Exact evidence: “expose the selected player's complete ordered hand and every opponent's size plus publisher-visible front card; hide only deeper opponent identities.”
- Conflicting code: `_trade_actions()` enumerates every partner hand index and bean name inside `trade_propose` actions.
- Expected: an acting player’s interface must not disclose identities below each opponent’s visible front card.
- Implemented: the legal-action payload reveals every opponent card’s identity and exact position. Conversely, `observation_to_data()` exposes only counts for staged received cards, even to their owner. This materially breaks the approved information boundary during trading and planting.

### Minor — Phase-three decision metadata conflicts with the approved flexible order

- Canonical fact: `BOHN-M-PHASE3-INTERPLAYER-ORDER`
- Evidence type: `human_decision`
- Approved decision: any affected owner with staged cards may plant next.
- `_plant_actions()` correctly emits actions for every affected owner, but `_decision_player()` and `current_player()` always designate the first owner with pending cards. The transition engine accepts other owners’ actions, but orchestration that gates actions by `current_player` would impose a fixed player order.

## Rule-area coverage

| Rule area | Status | Notes |
|---|---|---|
| Scope and setup | Pass | 3–5 players, field counts, deck inventory, five-card hands and seeded start are represented. |
| Hand order and planting | Pass | Front planting, optional second card, no third card, field typing and forced harvest are present. |
| Reveal and phase order | Partial | Normal sequence works; phase-two third-depletion termination is wrong. |
| Trading and gifts | Fail | Consent and staging work, but unequal bundles and correct private-card agency are absent. |
| Phase-three planting | Partial | All staged cards are mandatory; `current_player` conflicts with approved inter-player flexibility. |
| Harvesting | Partial | Timing, singleton protection and conservation work; Garden and Soy payouts are wrong. |
| Chance and recycling | Partial | Sequential draws and seeded shuffles exist; recycling is delayed at some depletion boundaries. |
| Private/public information | Partial | Observation hides deck and deeper hands, but legal trade actions leak those hands. |
| End game and returns | Partial | Final harvest, ignored hands, highest score and tiebreak are implemented; payout and phase-boundary defects can change results. |

## Missing deterministic scenarios

- Garden harvests at sizes 1–6 and Soy harvests at sizes 2–7, including final-harvest winner effects.
- Atomic two-for-one and one-for-two trades, rejection with no movement, and multi-card transfer conservation.
- Redaction of every deeper opponent card from both observations and action names.
- Depletion on the final required reveal/draw, followed by an intervening harvest, verifying which cards enter the recycled pile.
- Third depletion on the first and second phase-two reveal positions, followed through phase three to immediate terminal state without a draw action.
- Phase-three states with staged cards for several owners, exercising each legal choice of next owner and `current_player` integration.
- Gift offered from a non-active player to the active player, if that direction is approved.

## Material questions for a human

- `BOHN-M-EMPTY-DISCARD-RECYCLE`: what should happen when a first/second depletion has an empty or insufficient discard? The code silently returns fewer cards, while the packet deliberately leaves this unresolved.
- Is the legal-action catalog player-visible? If it is strictly engine-private and separately filtered, the private-hand finding may be reduced; no such filtering exists in this module.
- Does `current_player` gate which actor may submit an action? If so, the phase-three ordering issue becomes major.
- Does the reciprocal gift wording require non-active-to-active gifts? The current proposal generator supports only active-to-non-active gifts.
- The implementation uses player-block dealing order. The packet marks exact deal direction/grouping as unspecified; confirm this is an accepted representation choice.

```text
score: 0.55
confidence: high
critical_issues: 0
major_issues: 6
minor_issues: 1
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```