score: 0.84  
confidence: high

The core Abalone rules are implemented consistently: exact setup, movement geometry, Sumito/Patt restrictions, ejection, sixth-capture victory, turn order, returns, and public state. Two approved software-contract decisions are contradicted: forced passing and unique action serialization.

## Findings

### Major — No forced-pass transition

- Canonical fact ID: `ABAL-G-PASS`
- Evidence type: `human_decision`
- Source ID: `ABALONE-V2-RULEFACTS`
- Locator: `canonical_rulefacts.md`, “Approved human decisions,” item 2
- Exact evidence: “Exactly one forced pass exists only when no legal movement exists; no voluntary pass exists.”
- Conflicting code:
  - [`Game.legal_actions()`](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-UksRPP/boardbench_abalone_codex_ag_judge_3_i704dn3k/implementation.py:162) returns an empty list when no movement is available.
  - [`Game._result()`](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-UksRPP/boardbench_abalone_codex_ag_judge_3_i704dn3k/implementation.py:121) rejects every action whose type is not `"move"`.
  - [`Game.apply_action()`](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-UksRPP/boardbench_abalone_codex_ag_judge_3_i704dn3k/implementation.py:179) consequently rejects parsed `"pass"` actions.
- Expected: When there are no legal movements, expose exactly one pass action and allow it to advance the turn; never expose a voluntary pass.
- Implemented: No pass is ever legal. A no-movement state has no legal transition, despite pass serialization being supported.

### Major — Multiple canonical encodings represent the same movement

- Canonical fact ID: `ABAL-G-ACTION-UNIQUE`
- Evidence type: `human_decision`
- Source ID: `ABALONE-V2-RULEFACTS`
- Locator: `canonical_rulefacts.md`, “Approved human decisions,” item 5
- Exact evidence: “Exactly one canonical serialized action represents each physical movement.”
- Conflicting code:
  - [`Game.name_to_action()`](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-UksRPP/boardbench_abalone_codex_ag_judge_3_i704dn3k/implementation.py:213)
  - [`Game.action_from_data()`](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-UksRPP/boardbench_abalone_codex_ag_judge_3_i704dn3k/implementation.py:291)
- Expected: A multi-marble group must have one required coordinate order, with permutations rejected or normalized before canonical validation.
- Implemented: Both parsers preserve and accept arbitrary group order. Thus `group=a;b` and `group=b;a` can encode the same physical movement and both pass the name round-trip “canonical” check. `legal_actions()` emits sorted groups, but the public parsers do not enforce that ordering.

No critical or minor findings.

## Rule-area coverage

| Rule area | Result | Relevant claims |
|---|---|---|
| Players and exact Figure-1 setup | Conforms: 61 cells; 14 black/14 white; correct rows; player 0/black starts | `ABAL-C-PLAYERS`, `ABAL-C-SETUP-FIGURE`, `ABAL-C-BOARD-61`, `ABAL-C-SETUP-COUNTS`, `ABAL-C-SETUP-ROWS`, `ABAL-G-PLAYER-MAPPING` |
| Turn structure | Alternation and one atomic move conform; forced pass missing | `ABAL-C-TURN-ORDER`, `ABAL-C-ONE-MOVE`, `ABAL-G-PASS` |
| Basic movement | Conforms: one step, six directions, groups of 1–3, straight/contiguous, inline/broadside, empty destinations | `ABAL-C-ONE-STEP` through `ABAL-C-SUBSET-LONG-ROW`, `ABAL-G-BROADSIDE-DESTINATIONS` |
| Sumito | Conforms: strict superiority, only 2v1/3v1/3v2, inline adjacency, blocking/gap/collinearity rules | `ABAL-C-SUMITO-SUPERIOR` through `ABAL-C-SUMITO-OPTIONAL` |
| Patt | Conforms: equal groups and 4v3 cannot push; withdrawal, broadside, and crossing attacks remain possible | `ABAL-C-PATT-EQUAL` through `ABAL-C-PATT-CROSSING` |
| Ejection and victory | Conforms: edge exception, removal, immediate sixth-ejection victory, winner retains current-player field | `ABAL-C-EJECTION`, `ABAL-C-EDGE-EXCEPTION`, `ABAL-C-SIXTH-WINS`, `ABAL-G-TERMINAL-API` |
| Returns/public state | Conforms to approved decisions | `ABAL-G-RETURNS`, `ABAL-G-PUBLIC-STATE` |
| Action serialization | Legal-action enumeration is unique, but parsers admit reordered aliases | `ABAL-G-ACTION-UNIQUE` |
| Chance/private information | No private information; deterministic player/color convention is approved; social lottery is exempt | `ABAL-C-COLOR-LOTTERY`, `ABAL-G-PLAYER-MAPPING` |
| Clock/draw rules | Correctly omitted under declared scope; publisher packet does not decide draw or timeout behavior | `ABAL-C-CLOCK-OPTIONAL`, `ABAL-G-DRAW`, `ABAL-G-CLOCK` |

## Missing deterministic scenarios

Without inspecting prohibited scenario files, the following scenarios are needed to expose the identified deviations:

1. A nonterminal state with no legal movement must expose exactly one pass; applying it must advance the turn without changing the board or captures.
2. A state with at least one legal movement must not expose or accept pass.
3. For a two-marble move, reverse the group coordinates in the text serialization; the reordered alias must be rejected as noncanonical.
4. Repeat the reordered-group case through `action_from_data`.
5. Confirm the single canonical encoding round-trips through both text and structured serialization.

## Material questions for a human

None needed to resolve the findings: both behaviors are already fixed by approved human decisions. Draw, repetition, move-limit, and clock-expiration outcomes remain explicitly unspecified and unscored; the implementation should not invent them without a future decision.

score: 0.84
confidence: high
critical_issues: 0
major_issues: 2
minor_issues: 0
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true