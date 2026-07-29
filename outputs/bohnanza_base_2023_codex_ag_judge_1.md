Score: **0.74**, confidence: **high**. The module implements most base-game mechanics correctly, but three material interface/choice defects can alter play. Review was static only, as required.

## Findings

### Major 1 — Multi-card trades are absent from the enumerated legal-action space

- Canonical fact ID: `BOHN-C-TRADE-UNEQUAL`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2
- Exact evidence: “Ihr dürft mit einer unterschiedlichen Kartenanzahl handeln, z. B. zwei blaue Bohnen gegen eine Gartenbohne.”
- Conflicting code: [`Game.legal_actions()`](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-JkRj5D/boardbench_bohnanza_base_2023_codex_ag_judge_1_6w2zd9xm/implementation.py:114), especially lines 125–133.
- Expected: Legal actions must expose positive, unequal bundles such as a two-card-for-one-card trade.
- Implemented: The enumerated choices contain only one-card gifts and one-for-one trades. Handcrafted multi-card proposals are accepted by `apply_action`, but an agent relying on `legal_actions()` cannot select them.

This materially restricts the normal action interface despite the transition validator accepting arbitrary bundles.

### Major 2 — Legal-action data reveals every deeper opponent hand card

- Canonical fact ID: `BOHN-M-OBS-DEEPER-HAND`
- Evidence type: `human_decision`
- Source: `BOHN-V3-STRUCTURED-CLARIFICATION`, `canonical_supplement.md`, “Clarified digital decisions,” item 4
- Exact evidence: “For each opponent expose hand size and the source-visible front card, but hide deeper card identities. Legal-action data must not leak those deeper identities.”
- Conflicting code: [`Game.legal_actions()`](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-JkRj5D/boardbench_bohnanza_base_2023_codex_ag_judge_1_6w2zd9xm/implementation.py:123).
- Expected: Opponent legal-action references may expose the front card, but deeper identities must remain hidden.
- Implemented: `requested` is built from every opponent hand position and includes each card’s exact `"bean"` value. Those identities appear in returned `trade_propose` actions.

`observation_to_data()` correctly hides deeper cards, but the legal-action channel immediately defeats that privacy policy.

### Major 3 — Owners cannot choose the planting order of their staged cards

- Canonical fact ID: `BOHN-C-PLANT-OWNER-ORDER`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2
- Exact evidence: “Jede Person darf selbst entscheiden, in welcher Reihenfolge sie die neuen Bohnenkarten anbaut.”
- Conflicting code: [`Game.legal_actions()` phase `plant_received`](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-JkRj5D/boardbench_bohnanza_base_2023_codex_ag_judge_1_6w2zd9xm/implementation.py:137).
- Expected: Each affected owner chooses any of their remaining received/revealed cards as the next card to plant.
- Implemented: Only `cards[0]` from each `pending_received` list and `revealed[0]` are selectable. Transfer removal can also impose reverse-index order. Owners choose fields, but not card order.

This can change which field must be harvested and therefore payouts.

### Minor 1 — Phase three requires an extra no-op pass

After the final staged card is planted, lines 228–232 leave the phase as `plant_received`. The active player must subsequently issue `pass` before reaching `draw`. Likewise, an initially empty phase three requires a pass. The printed flow proceeds to phase four once all mandatory planting is complete. This is a localized extra transition rather than a core deadlock.

Relevant facts: `BOHN-C-PHASES`, `BOHN-C-PLANT-ALL-RECEIVED`, `BOHN-C-PLANT-UNTRADED-REVEALED`.

### Minor 2 — Handcrafted proposals can name nonexistent partners

[`_validate_proposal()`](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-JkRj5D/boardbench_bohnanza_base_2023_codex_ag_judge_1_6w2zd9xm/implementation.py:285) does not bounds-check `partner`. Because `trade_propose` bypasses the ordinary legal-action membership check, an offered-only proposal can install a negative or oversized awaiting player and later misroute cards or raise an index error. Generated actions do not trigger this, but externally constructed actions can.

### Question — Empty/insufficient discard during a nonterminal recycle

- Canonical fact ID: `BOHN-M-EMPTY-DISCARD-RECYCLE`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2
- Exact evidence: “Ziehst du die letzte Karte vom Nachziehstapel, mische die Karten des Ablagestapels. Danach legst du sie als neuen Nachziehstapel wieder verdeckt in die Tischmitte.”
- Code: [`_draw_one()`](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-JkRj5D/boardbench_bohnanza_base_2023_codex_ag_judge_1_6w2zd9xm/implementation.py:149) and draw handling at line 269.
- Packet status: explicitly missing/undecided.
- Implemented assumption: If the deck is already empty, `_draw_one()` returns `None`; phase-four draw then calls `_finish()` even if fewer than three depletions occurred.
- Needed decision: Define whether such a state ends the game, pauses the draw, or uses another rule. This is not scored as a printed-rule contradiction.

## Rule-area coverage

| Rule area | Assessment |
|---|---|
| Player count, deck inventory, fields, five-card deal | Correct |
| Seeded fixed starting player | Correct |
| Ordered hands and front planting | Correct |
| Mandatory first/optional second/no third planting | Correct |
| Forced harvest as separate decision | Correct |
| Reveal and explicit trade ending | Correct |
| Trade consent and atomic transfer | Correct |
| Trade bundle action exposure | Major gap |
| Staged-card ownership and no retrading | Correct |
| Phase-three inter-player choice | Supported |
| Phase-three per-owner card order | Major gap |
| Harvest timing and singleton protection | Correct |
| All eight beanometers and card conservation | Correct |
| First/second recycle and interrupted draws | Correct when discard supply exists |
| Third depletion and phase-two exception | Correct |
| Final harvest, ignored hands, winner and tiebreak | Correct |
| Private observations | Observation correct; legal actions leak |
| Returns | Correct one-hot winner return |
| Serialization | Inventory checked; broader semantic state validation is limited |

## Missing deterministic scenarios

These scenarios should be required without inspecting any external test suite:

1. Enumerated two-for-one trade, partner acceptance, atomic removal, and staged receipt (`BOHN-C-TRADE-UNEQUAL`).
2. Two different staged cards for one owner, verifying either card can be planted first (`BOHN-C-PLANT-OWNER-ORDER`).
3. Active player with two untraded revealed cards, verifying either revealed card can be selected first.
4. Legal actions viewed by each player, asserting that only opponent front-card identity is exposed (`BOHN-M-OBS-DEEPER-HAND`).
5. Trade proposal with negative and oversized partner IDs must be rejected without state mutation.
6. Completion of phase three should enter phase four without a redundant decision.
7. First/second depletion with empty or insufficient discard, once a human selects the intended behavior.
8. Third depletion on the first phase-two reveal, followed by trading, all staged planting, final harvest, and no phase four.

## Material questions for a human

- What deterministic behavior should apply when a first/second depletion has no—or too few—discard cards to continue the interrupted reveal/draw? (`BOHN-M-EMPTY-DISCARD-RECYCLE`)
- Must the BoardBench `legal_actions()` result be exhaustive? The implementation treats multi-card trades as constructible but deliberately omits them from enumeration. The current review treats the advertised legal-action interface as authoritative.
- Should staged card identities be exposed in observations to their owner or to everyone? The packet clearly governs deeper hand privacy but does not separately specify digital visibility for sideways staged cards.

score: 0.74
confidence: high
critical_issues: 0
major_issues: 3
minor_issues: 2
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true