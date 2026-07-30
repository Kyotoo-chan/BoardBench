## Review result

**score: 0.89 — confidence: high.** The module implements nearly all clear printed rules: fixed 3/4-player setup, strict phases, production, trading, construction, robber resolution, development cards, Longest Road/Largest Army, private hands, and immediate victory. Two approved digital-protocol failures can corrupt resource holdings when development-card interrupts occur during pending decisions.

## Findings

### Major — domestic-trade acceptance is not revalidated after an interrupt

- Canonical fact ID: `CAT-M-TRADE-PROTOCOL`
- Evidence type: `human_decision`
- Source: `CATAN22-V2-RULEFACTS`
- Stable locator: `canonical_rulefacts.md`, “Approved decisions,” items 5 and 7
- Exact evidence:
  - “atomic transfer only on acceptance.”
  - “acceptance validates actual holdings.”
  - “an eligible card may interrupt pending … trade-consent decisions”
- Conflicting code:
  - `_dev_actions` / `legal_actions` expose active-player development cards while consent is pending ([implementation.py](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-jEvcwB/boardbench_clear_rule_emphasis_r2_judge_2_abwmayc3/implementation.py:246), lines 273–274).
  - `accept_domestic_trade` transfers the stored bundles without validating current holdings (lines 371–376).
- Expected: after an interrupt, acceptance must atomically verify that both players still possess their promised bundles; otherwise acceptance must be unavailable or rejected without transfer.
- Implemented: an intervening Monopoly can remove resources promised by the partner, but acceptance subsequently subtracts the original bundle anyway, producing negative resource counts.
- Impact: materially invalid trade and resource state; later costs, discards, production, and scoring play from corrupted holdings.

### Major — submitted discard cards are not escrowed against interrupts

- Canonical fact ID: `CAT-M-DISCARD-ESCROW`
- Evidence type: `human_decision`
- Source: `CATAN22-V2-RULEFACTS`
- Stable locator: `canonical_rulefacts.md`, “Approved decisions,” items 7 and 10
- Exact evidence:
  - “submitted private selections are unavailable to interrupts”
  - “settle together after every required submission.”
- Conflicting code:
  - `_submit_discard` records only `submitted_players`; selected cards remain in the player’s resource hand until everybody submits (lines 426–433).
  - Development-card interrupts remain exposed during `discard` (lines 273–274).
  - Monopoly takes all matching cards directly from those still-unchanged hands (lines 492–495).
- Expected: once submitted, selected cards must be reserved privately and excluded from Monopoly, theft, trade, and other intervening effects; all escrowed selections then settle together.
- Implemented: a submitted selection remains available to Monopoly. Final discard settlement can subtract the same cards again and create negative holdings.
- Impact: corrupts a mandatory seven-resolution transition and can alter later legal actions and resource availability.

No critical or minor contradictions were identified.

## Rule-area coverage

| Rule area | Status | Representative facts |
|---|---|---|
| Fixed 3/4-player setup and inventory | Covered | `CAT-C-SETUP-*`, `CAT-C-INV-*` |
| Starting player and clockwise turns | Covered | `CAT-C-START-OLDEST`, `CAT-C-CLOCKWISE` |
| Strict roll → trade → build | Covered | `CAT-C-TURN-PHASES`, `CAT-C-TURN-STRICT` |
| Production and bank shortages | Covered | `CAT-C-PROD-*`, approved shortage decision |
| Domestic trade | Partial: interrupt revalidation defect | `CAT-C-TRADE-*`, `CAT-M-TRADE-PROTOCOL` |
| Maritime trade and harbors | Covered | `CAT-C-MARITIME-*`, `CAT-C-HARBOR-*` |
| Costs, stock, roads, settlements, cities | Covered | `CAT-C-COST-*`, `CAT-C-BUILD-STOCK`, graph-legality facts |
| Seven, discards, robber and theft | Partial: escrow defect | `CAT-C-SEVEN-*`, `CAT-C-DISCARD-*`, `CAT-M-DISCARD-ESCROW` |
| Development cards | Covered apart from interaction above | `CAT-C-DEV-*`, `CAT-C-ROAD-BUILDING`, `CAT-C-YOP`, `CAT-C-MONOPOLY` |
| Longest Road | Covered by inspection | `CAT-C-LR-*`, `CAT-A-LR-CYCLE`, `CATAN-EMPH-LONGEST-ROAD` |
| Largest Army | Covered | `CAT-C-ARMY-*` |
| Private information | Covered | `CAT-C-INFO-*` |
| Scoring and terminal conditions | Covered | `CAT-C-SCORE-*`, `CAT-C-WIN-*`, `CAT-C-VP-WIN-EXCEPTION` |
| Returns and serialization | Adequate; no printed-rule contradiction | N/A |

## Missing deterministic scenarios

1. Partner promises a resource, active player interrupts consent with Monopoly taking that resource, then partner attempts acceptance.
2. The same interrupted offer followed by rejection, confirming no bundle transfer.
3. A player submits a mixed discard selection; active player then plays Monopoly for one selected type before all submissions complete.
4. Multiple submitted discard escrows followed by Monopoly, verifying escrow secrecy, unavailability, and simultaneous settlement.
5. Interrupt-induced Longest Road victory while trade consent or discards remain pending, confirming immediate terminal cancellation.
6. Longest Road branch, loop, opponent interruption, incumbent tie, vacant tie, and strictly longer transfer.
7. Road Building with zero, one, and two remaining road pieces and with connectivity becoming exhausted after the first placement.
8. Observation checks confirming opponents cannot see discard selections while the selecting player can still track their own pending choice.

## Material questions for a human

- Should `bank.played_development` be interpreted solely as public history/removed-card tracking? If it is a live pile, progress cards would conflict with `CAT-C-PROGRESS-REMOVED`; the present code does not explicitly distinguish removed progress cards from face-up Knights.
- Should a player observation include that player’s own in-progress discard selection? `observation_to_data` removes `selected` for every viewer. This preserves secrecy from opponents but leaves the acting player unable to reconstruct the current private selection from a fresh observation alone.

```text
score: 0.89
confidence: high
critical_issues: 0
major_issues: 2
minor_issues: 0
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true
```