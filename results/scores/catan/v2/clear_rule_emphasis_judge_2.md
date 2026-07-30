Score: **0.72**  
Confidence: **high** — full static review of the 125 approved claims and implementation; no code execution or prohibited artifacts inspected. Core gameplay is substantially implemented, but three approved digital decisions are materially violated.

## Findings

### Major — Domestic offers disclose private resource identities and are not revalidated

- Canonical facts: `CAT-C-INFO-RESOURCE-PRIVATE`, `CAT-M-TRADE-PROTOCOL`, `CAT-M-TRADE-OFFER-BOUND`.
- Evidence type: `rule_quote`.
- Source: `CATAN22-RULES`, PDF page 2.
- Exact evidence: “Rohstoffkarten hält jeder Spieler verdeckt in der Hand.”
- Evidence type: `human_decision`.
- Provenance: `canonical_claims.json` JSON Pointers `/claims/99` and `/claims/121`.
- Source: `CATAN22-V2-RULEFACTS`, Approved decisions items 5 and 9.
- Exact evidence: “give/take totals are capped by each side's public resource-hand size without revealing identities; acceptance validates actual holdings.”
- Conflicting code: [`legal_actions()` and `accept_domestic_trade`](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-LLGCqi/boardbench_catan_codex_ag_judge_2_9prjbws5/implementation.py:299).
- Expected: offer construction may use public total hand sizes but must not reveal which resource types the partner holds; acceptance must atomically verify both bundles.
- Implemented: lines 302–306 expose an `add_trade_item` action only when the partner actually possesses that particular resource, revealing hand identities. Lines 371–376 transfer without revalidation. A permitted development-card interrupt can therefore invalidate an offer and allow negative holdings.

### Major — Knight interrupts resume pending decisions with the wrong actor

- Canonical fact: `CAT-M-DEV-BOUNDARY`.
- Evidence type: `human_decision`.
- Provenance: `canonical_claims.json` JSON Pointer `/claims/118`.
- Source: `CATAN22-V2-RULEFACTS`, Approved decisions item 7.
- Exact evidence: “resolve it on a pending-state stack, then resume unless terminal.”
- Conflicting code: [`_push_robber()`](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-LLGCqi/boardbench_catan_codex_ag_judge_2_9prjbws5/implementation.py:435), [`_finish_pending()`](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-LLGCqi/boardbench_catan_codex_ag_judge_2_9prjbws5/implementation.py:460).
- Expected: after the Knight’s robber sequence, the interrupted discard or trade-consent decision resumes with its original decision-maker.
- Implemented: `_push_robber()` always records `active_player` as `resume_current_player`. If the partner was considering a trade, control returns to the offeror, who can accept or reject their own offer. During sequential discard submission, control likewise returns to the active player instead of the interrupted discarder.

### Major — Submitted discard escrow remains stealable

- Canonical fact: `CAT-M-DISCARD-ESCROW`.
- Evidence type: `human_decision`.
- Provenance: `canonical_claims.json` JSON Pointer `/claims/122`.
- Source: `CATAN22-V2-RULEFACTS`, Approved decisions item 10.
- Exact evidence: “submitted private selections are unavailable to interrupts and settle together after every required submission.”
- Conflicting code: [`_submit_discard()`](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-LLGCqi/boardbench_catan_codex_ag_judge_2_9prjbws5/implementation.py:426), [`_steal()`](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-LLGCqi/boardbench_catan_codex_ag_judge_2_9prjbws5/implementation.py:452), [`_play_development()`](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-LLGCqi/boardbench_catan_codex_ag_judge_2_9prjbws5/implementation.py:478).
- Expected: submitted cards become unavailable immediately, remain private, and return to the bank together after all submissions.
- Implemented: selections remain in each player’s ordinary `resources` until final settlement. An interrupting Knight or Monopoly can take submitted cards; final settlement then subtracts them again, potentially producing negative resource counts.

### Minor — Played progress cards remain in the development hand

- Canonical fact: `CAT-C-PROGRESS-REMOVED`.
- Evidence: `CATAN22-RULES`, PDF page 4: “Fortschrittskarten kommen aus dem Spiel.”
- Conflicting code: [`_play_development()`](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-LLGCqi/boardbench_catan_codex_ag_judge_2_9prjbws5/implementation.py:478).
- The card is marked revealed and copied into `played_development`, but remains in `development_hand` and in the owner’s observation. Replay is prevented, so this is chiefly an incorrect zone/information representation.

## Rule-area coverage

| Rule area | Result |
|---|---|
| 3/4-player illustrated setup and inventories | Conforms |
| Roll → trade → build turn order | Conforms |
| Production, shortages, robber blocking | Conforms |
| Domestic/maritime trade | Major privacy and validation defects |
| Costs, stock, graph legality, city replacement | Conforms |
| Seven, discard, robber, theft | Major escrow defect |
| Development cards and interrupts | Major resume defect; minor removal defect |
| Longest Road and Largest Army | Conforms to approved decisions/emphasis |
| Scoring, immediate victory, returns | Conforms |
| Chance and player observations | Generally conforms; trade actions leak identities |
| Serialization | No material rule contradiction identified |

## Missing deterministic scenarios

Priority scenarios needed to expose or prevent these failures:

- Build a trade request against each possible hidden partner hand and assert identical per-type construction visibility for equal public hand sizes.
- Interrupt a pending trade response with Knight; verify control returns to the partner.
- Interrupt another player’s discard with Knight; verify control returns to that exact discarder.
- Submit an all-one-resource discard, then interrupt with Monopoly or theft; verify escrowed cards cannot transfer and no count becomes negative.
- Mutate holdings between proposal and acceptance; verify acceptance rejects the stale offer atomically.
- Play each progress card and verify it leaves the private development hand and enters an appropriate removed/history representation.
- Retain regression cases for zero/one/two road pieces and all Longest Road interruption/tie outcomes required by `CATAN-EMPH-LONGEST-ROAD` and `CATAN-EMPH-ROAD-STOCK`.

## Material questions for a human

None. The cited deviations are resolved by the approved digital decisions rather than requiring additional rulebook interpretation.

```text
score: 0.72
confidence: high
critical_issues: 0
major_issues: 3
minor_issues: 1
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true
```