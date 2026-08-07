## Assessment

`score: 0.62`  
`confidence: high`

The module correctly implements setup, ordered hand planting, harvesting restrictions, all eight beanometers, final harvesting, scoring, and the tiebreak. However, four material defects affect trade legality, phase-three choice, private information, and depletion/game-end timing. No issue appears critical because games can generally progress and eventually terminate.

## Findings

### Major — Unequal multi-card trades cannot be represented atomically

- Canonical fact: `BOHN-C-TRADE-UNEQUAL`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2
- Exact evidence: “Ihr dürft mit einer unterschiedlichen Kartenanzahl handeln, z. B. zwei blaue Bohnen gegen eine Gartenbohne.”
- Conflicting code: [`Game.legal_actions()`](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-FwgQ6h/boardbench_bohnanza_base_2023_codex_ag_judge_1_dxc0l_nn/implementation.py:76), especially lines 84–88.
- Expected: A proposal can atomically exchange unequal bundles, including the printed two-for-one example.
- Implemented: Every proposal contains exactly one offered card and either zero or one requested card. Repeated 1:1 trades plus a gift are not equivalent because each transfer has separate consent and can be rejected independently.

### Major — Owners cannot choose the planting order of staged cards

- Canonical fact: `BOHN-C-PLANT-OWNER-ORDER`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2
- Exact evidence: “Jede Person darf selbst entscheiden, in welcher Reihenfolge sie die neuen Bohnenkarten anbaut.”
- Conflicting code: [`Game._plants()`](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-FwgQ6h/boardbench_bohnanza_base_2023_codex_ag_judge_1_dxc0l_nn/implementation.py:55) and `legal_actions()` lines 92–94.
- Expected: Each owner chooses any of their remaining received/revealed cards as the next card to plant.
- Implemented: Received and revealed planting always uses `index=0`. The owner can choose only the destination field, not which staged card goes next. This can force avoidable harvests and change payouts.

### Major — Depletion is detected one draw too late

- Canonical facts: `BOHN-C-RECYCLE-FIRST-SECOND`, `BOHN-C-END-THIRD`, `BOHN-C-END-OUTSIDE-PHASE2-IMMEDIATE`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2
- Exact evidence:
  - “Ziehst du die letzte Karte vom Nachziehstapel, mische die Karten des Ablagestapels.”
  - “Das Spiel endet, sobald der Nachziehstapel zum dritten Mal leer wird.”
- Conflicting code: [`Game._draw_one()`](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-FwgQ6h/boardbench_bohnanza_base_2023_codex_ag_judge_1_dxc0l_nn/implementation.py:100), plus `draw` lines 155–161.
- Expected: Drawing the last card constitutes depletion. The first two depletions recycle immediately; the third immediately triggers the applicable end rule.
- Implemented: `_draw_one()` increments `depletions` only when the deck is already empty before a draw. If the last card is also the final card requested by an action, the depletion remains unnoticed until a later action.
- Consequences:
  - A first/second recycle may incorrectly include cards discarded after the pile actually emptied.
  - An exact-boundary third depletion can permit another player’s planting, trading, or harvesting decisions before termination.
  - If phase-two reveal draws exactly the final two cards, the required end after phase three is instead deferred to a phase-four `draw` action.

### Major — Approved private-information mapping is violated

This is an approved-clarification deviation, separate from printed-rule contradictions.

- Canonical fact: `BOHN-M-OBS-DEEPER-HAND`, resolved by approved decision 4
- Evidence type: `human_decision`
- Source: `BOHN-V3-STRUCTURED-CLARIFICATION`
- Provenance locator: `SOURCE_MANIFEST.json#/sources/3`; evidence locator: `canonical_supplement.md`, “Clarified digital decisions,” item 4
- Exact evidence: “For each opponent expose hand size and the source-visible front card, but hide deeper card identities. Legal-action data must not leak those deeper identities.”
- Conflicting code:
  - [`Game.legal_actions()`](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-FwgQ6h/boardbench_bohnanza_base_2023_codex_ag_judge_1_dxc0l_nn/implementation.py:68), lines 86–88
  - [`Game.observation_to_data()`](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-FwgQ6h/boardbench_bohnanza_base_2023_codex_ag_judge_1_dxc0l_nn/implementation.py:185), line 189
- Expected: Opponents’ deeper cards remain unidentified in both observations and legal-action data.
- Implemented: Trade actions enumerate every position of every partner’s hand and embed its exact `bean`. A pending proposal containing such a reference is then copied into every player’s observation. The active player—and potentially all observers—can therefore learn deeper opponent cards.

No critical or minor findings.

## Rule-area coverage

| Rule area | Result | Notes |
|---|---|---|
| Setup and deck | Pass | Correct 3–5 players, fields, five-card hands, 104-card inventory and seeded start |
| Hand order / phase one | Pass | Mandatory front, optional second, no third, separate forced harvest |
| Reveal and trade | Major issue | Consent/staging work, but atomic unequal bundles are absent |
| Phase-three planting | Major issue | All cards remain mandatory, but owner-selected order is absent |
| Phase-four draw / turns | Partial | Sequential append and clockwise advance work; depletion boundary is wrong |
| Harvesting | Pass | Off-turn actions, singleton rule, zero-value harvest and conservation work |
| Beanometers | Pass | All eight printed payout curves match |
| Chance and privacy | Major issue | Seeded shuffle is reproducible; legal actions leak deeper hands |
| Terminal and scoring | Partial | Final harvest, ignored hands, winner and tiebreak work once termination occurs |
| Serialization / returns | Pass with assumption | One-hot return matches the implementation’s uniquely resolved winner |

## Missing deterministic scenarios

Because checks were out of scope, these are scenarios the module needs, not claims about an unseen test suite:

1. Atomic 2-for-1 and larger unequal trades, including acceptance/rejection without partial transfer.
2. Phase-three choice where planting the second staged card before the first changes whether a harvest is required.
3. Legal-action and pending-proposal privacy from every player’s viewpoint, with multiple deeper opponent cards.
4. First/second depletion when the last card is exactly the final reveal or draw requested; verify immediate recycle membership.
5. Third depletion with exactly one, two, and three cards remaining, both during phase-two reveal and outside phase two.
6. Reverse-direction gifts between the active and non-active participant, with recipient acceptance and rejection.
7. Public/owner visibility of multiple staged received cards.
8. Final-harvest tiebreak after an exact-boundary third depletion.
9. Deterministic checks for all beanometer thresholds plus singleton-protected off-turn harvests.
10. Exact setup and bounded play for 3, 4, and 5 players, plus rejection of 2 and 6.

## Material questions for a human

- `BOHN-M-EMPTY-DISCARD-RECYCLE`: What should happen when the first or second depletion occurs with an empty or insufficient discard pile?
- `BOHN-M-TRADE-REFERENCE-STABILITY`: Should pending proposals use immutable card identities, or should numeric references be revalidated if the representation later permits hand-affecting interrupts?
- `BOHN-M-DEAL-DIRECTION`: Is the implementation’s round-robin deal order an accepted representation profile, or must seeded states be portable across implementations?
- Should `state_to_data()` be treated as trusted omniscient serialization only? If it is player-facing, it additionally exposes every hand and the complete draw pile.

```text
score: 0.62
confidence: high
critical_issues: 0
major_issues: 4
minor_issues: 0
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```