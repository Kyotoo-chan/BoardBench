## Review result

**score: 0.86 — confidence: high**

The movement, Sumito, forced-pass, terminal, return, and public-state logic closely follows the approved facts and human decisions. The material defect is that every new game starts with only 13 marbles per player instead of 14.

## Findings

### Major — Initial setup omits one marble from each full six-marble row

- Canonical facts: `ABAL-C-SETUP-FIGURE`, `ABAL-C-SETUP-COUNTS`, `ABAL-C-SETUP-ROWS`
- Evidence type: `rule_quote`
- Source: `ABALONE-RULES-SCHMIDT-4P`
- Stable locator: PDF page 1, Figure 1
- Exact evidence: “Setzen Sie die Kugeln wie in Abb. 1 gezeigt in ihre Startpositionen.” Figure 1 establishes the approved rows `BBBBB / BBBBBB / ..BBB.. / empty / empty / empty / ..WWW.. / WWWWWW / WWWWW`.
- Conflicting symbol: `Game.initial_state`
- Implemented transition:
  - Black’s second row uses `range(-1, 4)`, producing five marbles and omitting `(4, -3)`.
  - White’s second row uses `range(-3, 2)`, producing five marbles and omitting `(-4, 3)`.
- Expected: 14 black, 14 white, 33 empty pits.
- Implemented: 13 black, 13 white, 35 empty pits.
- Impact: This affects every normal game from setup onward and can materially change mobility, board balance, and eventual winner.

### Question — No draw, repetition, or move-limit termination

- Canonical fact: `ABAL-G-DRAW`
- The publisher rulebook provides no draw, repetition, or move-limit result. The implementation consequently permits indefinite non-winning play.
- This is not scored as a contradiction. A human decision is required only if deterministic bounded termination is desired.

No critical or minor contradictions were found.

## Rule-area coverage

| Rule area | Result | Relevant facts |
|---|---|---|
| Two-player configuration and player/color mapping | Pass | `ABAL-C-PLAYERS`, `ABAL-G-PLAYER-MAPPING` decision |
| Board geometry | Pass: 61 valid axial cells | `ABAL-C-BOARD-61` |
| Initial placement and counts | **Fail** | `ABAL-C-SETUP-FIGURE`, `ABAL-C-SETUP-COUNTS`, `ABAL-C-SETUP-ROWS` |
| Turn order and one movement | Pass | `ABAL-C-TURN-ORDER`, `ABAL-C-ONE-MOVE` |
| One-step, six-direction, groups of 1–3 | Pass | `ABAL-C-ONE-STEP`, `ABAL-C-SIX-DIRECTIONS`, `ABAL-C-GROUP-SIZE`, `ABAL-C-MAX-THREE` |
| Straight contiguous groups and longer-row subsets | Pass | `ABAL-C-STRAIGHT-CONTIGUOUS`, `ABAL-C-SUBSET-LONG-ROW` |
| Inline and broadside movement | Pass | `ABAL-C-INLINE`, `ABAL-C-BROADSIDE`, `ABAL-G-BROADSIDE-DESTINATIONS` decision |
| Sumito strength and geometry | Pass | `ABAL-C-SUMITO-SUPERIOR` through `ABAL-C-SUMITO-COLLINEAR` |
| Patt, withdrawal, and crossing attacks | Pass | `ABAL-C-PATT-EQUAL` through `ABAL-C-PATT-CROSSING` |
| Edge ejection | Pass | `ABAL-C-EJECTION`, `ABAL-C-EDGE-EXCEPTION` |
| Sixth-ejection terminal transition | Pass | `ABAL-C-SIXTH-WINS`, `ABAL-G-TERMINAL-API` decision |
| Forced pass | Pass | `ABAL-G-PASS` decision |
| Returns and public information | Pass | `ABAL-G-RETURNS`, `ABAL-G-PUBLIC-STATE` decisions |
| Unique serialized legal actions | Pass | `ABAL-G-ACTION-UNIQUE` decision |
| Chance/private information | Pass: none required; state is public | Approved public-state decision |
| Optional clocks | Correctly omitted from play | `ABAL-C-CLOCK-OPTIONAL`, `ABAL-G-CLOCK` |

## Missing deterministic scenarios

Recommended scenarios not evidenced within the permitted review packet:

1. Assert all nine initial row strings and exact `14/14/33` counts. This directly catches the identified defect.
2. Assert ordinary inline and broadside moves for groups of one, two, and three, including edge-side broadside rejection.
3. Exercise every Sumito strength pattern: legal `2v1`, `3v1`, `3v2`; illegal `1v1`, `2v2`, `3v3`, and `4v3`.
4. Reject pushes with a gap, non-collinear defenders, or an occupied pit behind defenders.
5. Verify Patt withdrawal, broadside escape, and crossing-angle Sumito.
6. Verify fifth versus sixth ejection, immediate terminal state, empty terminal actions, winner-retained `current_player`, and `[+1,-1]` returns.
7. Verify forced pass is the sole legal action only when no movement exists, and that voluntary pass is rejected otherwise.
8. Round-trip every public action/state field and confirm one serialized action per physical movement.

## Material questions for a human

- Should a draw, repetition rule, or move limit be added to guarantee bounded games? The supplied rulebook does not decide this (`ABAL-G-DRAW`).
- No clarification is needed for forced pass, terminal API behavior, returns, player mapping, public state, or action uniqueness; those are already resolved by approved human decisions.

```text
score: 0.86
confidence: high
critical_issues: 0
major_issues: 1
minor_issues: 0
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```