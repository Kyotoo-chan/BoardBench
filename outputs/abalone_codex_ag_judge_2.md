Score: **0.93**, confidence: **high**. The implementation accurately models setup, ordinary movement, Sumito/Patt restrictions, ejection, victory, terminal handling, and returns. The principal defect is the missing mandatory forced-pass action.

## Findings

### Major — No forced pass when the active player has no legal movement

- Canonical fact ID: `ABAL-G-PASS`
- Evidence type: `human_decision`
- Source ID: `ABALONE-V2-RULEFACTS`
- Locator: `canonical_rulefacts.md`, “Approved human decisions,” item 2
- Exact evidence: “Exactly one forced pass exists only when no legal movement exists; no voluntary pass exists.”
- Conflicting code: `Game.legal_actions`
- Implemented behavior: when no movement succeeds, `legal_actions()` returns `[]`. Although pass actions can be parsed and serialized, they are never legal, and `apply_action()` therefore always rejects them.
- Expected behavior: a nonterminal state with no legal movement must expose exactly one pass action for the current player; applying it must advance the turn without changing the board or captures. Pass must remain unavailable whenever at least one movement exists.
- Impact: a qualifying nonterminal position deadlocks because no action can advance the game.

### Question — Serialized states are not checked for semantic consistency

Canonical facts `ABAL-G-PUBLIC-STATE`, `ABAL-G-TERMINAL-API`, and `ABAL-G-RETURNS` establish the public fields and their intended terminal behavior, but do not explicitly define deserialization-validation requirements.

`Game.state_from_data` accepts contradictory combinations such as:

- `terminal=True`, `winner=None`, `phase="play"`
- `terminal=False`, `winner=0`, `phase="terminal"`
- six or more captures while remaining nonterminal

It also does not reconcile board inventory with capture counts. A human should decide whether external state payloads must be semantically valid or whether callers are trusted to provide reachable states. This is not scored as a rules contradiction.

## Rule-area coverage

| Rule area | Status | Review result |
|---|---|---|
| Scope and players | Covered | Exactly two players; untimed base variant |
| Initial board/setup | Covered | 61 cells; Figure-1 rows and 14/14/33 counts |
| Turn order | Covered | Black/player 0 begins; successful nonterminal moves alternate |
| Ordinary movement | Covered | One step, six directions, groups of 1–3, contiguous straight subsets |
| Inline/broadside movement | Covered | Empty-destination and on-board broadside requirements enforced |
| Sumito | Covered | Inline only; strict superiority; 2v1, 3v1, 3v2; gap/blocking rules |
| Patt | Covered | Equal-strength and 4v3 pushes blocked; withdrawal and crossing attacks remain possible |
| Forced pass | **Contradicted** | Required pass is absent |
| Ejection and victory | Covered | Edge removal and immediate sixth-ejection victory |
| Terminal API and returns | Covered | No terminal actions, winner retains turn, `[+1,-1]`; preterminal `[0,0]` |
| Chance/private information | Covered | No gameplay chance or private information; social color lottery properly excluded |
| Draw/clock rules | Unscored | Not specified or outside declared scope |

## Missing deterministic scenarios

Without inspecting any scenario artifacts, the following are necessary coverage cases:

1. A nonterminal state with zero movement actions produces exactly one forced pass; applying it changes only the current player and move number.
2. A state with at least one movement exposes no voluntary pass.
3. All three legal Sumito patterns—2v1, 3v1, and 3v2—both on-board and at the edge.
4. Equal Patt cases plus 4v3, including legal withdrawal/broadside and crossing-angle resolution.
5. Sixth ejection verifies immediate terminal state, empty legal actions, retained winner as current player, and player-ordered returns.
6. Broadside rejection when any corresponding destination is occupied or off-board.
7. Canonical action round-trips demonstrate one generated serialized action per physical movement.
8. If semantic state validation is required, contradictory terminal/winner/phase/capture payloads must be rejected.

## Material questions for a human

- Must `state_from_data` reject semantically inconsistent or unreachable states, or is it only a structural decoder?
- Should structurally valid pass actions remain parseable outside forced-pass positions, provided they are rejected by legality checking?

```text
score: 0.93
confidence: high
critical_issues: 0
major_issues: 1
minor_issues: 0
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```