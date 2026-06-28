# Abalone (oneshot) — Judge Review

## 1. Score

- `score: 0.75`
- `confidence: medium`
- Justification: The implementation faithfully encodes the *stated* Abalone mechanics — alternating turns with Black first, 1–3 ball in-line and broadside moves, Sumito with a strict numeric majority (2-1/3-1/3-2), the Patt block on equal counts, the free-space-behind requirement, edge push-offs, and the six-ball win. I traced the hex geometry and the push-resolution logic on representative cases and they hold up, and the API is complete and round-trips. Two things cap the score: the starting layout (Abb. 1) is not in the packet, so the single most fundamental element — positions and ball counts — cannot be verified, and `render()` labels rows with the *opposite* letters from `cell_to_label()`/action names, which breaks the side-by-side inspection the benchmark relies on.

## 2. Top findings

**Finding 1 — Setup cannot be verified (Abb. 1 missing from packet)** · severity: question (high priority)
- Evidence: rulebook says "Setzen Sie die Kugeln wie in Abb. 1 gezeigt," but no figure/image is included. Code comments this honestly: `# ASSUMPTION: standard Abalone opening (Abb. 1 not provided).` It places 14 balls per side (rows I/H + 3 of G for Black; A/B + 3 of C for White).
- Why it matters: the initial position and ball count are the foundation for every legal-action, Sumito, and terminal test. If Abb. 1 differs, the whole environment shifts.
- Suggested action: obtain the Abb. 1 image and confirm placement + total ball count (14 vs 14 is only an assumption here). Per judge rules I mark this uncertain, not wrong.

**Finding 2 — `render()` row letters contradict `cell_to_label()`/action names** · severity: major
- Evidence: `cell_to_label` uses `chr(ord('A') + (8 - row))` → internal row 8 (top) = **A**. `render` uses `letter = chr(ord('A') + row)` → internal row 8 (top) = **I**. Concrete case: Black's corner at internal `(8,0)` is named `move:A1...` but appears in the render row labeled `I`.
- Why it matters: the generation prompt explicitly wants `render` "suitable for side-by-side inspection" and action names consistent with rulebook/label conventions. A human (or a cross-judge alignment step) reading `move:A1A2->E` will look at the render's `A` row (bottom, White's home) while the move actually concerns the top row. Game logic is unaffected (names round-trip internally), but interface fidelity is broken.
- Suggested action: pick one letter convention and use it in both functions; add a test pinning a known cell's letter in both `render` and `action_to_name`.

**Finding 3 — Board geometry / directions / labels are reasonable but not in the rulebook** · severity: minor
- Evidence: `ROW_SIZES = [5,6,7,8,9,8,7,6,5]`, `DIRECTIONS = ['E','W','NE','NW','SE','SW']`, cell labels `A1..`. The rule text states only "sechs mögliche Richtungen" and shows figures; it never states board size, direction names, or a coordinate notation.
- Why it matters: these are load-bearing assumptions for legality/enumeration. The 61-cell hexagon and neighbor math are internally consistent (I verified reversibility across the middle rows 3↔4↔5), so this is a documentation/verification gap, not a logic bug.
- Suggested action: confirm board dimensions and figure orientation once Abb. 1 and Abb. 2/3 are available.

**Finding 4 — Invented finiteness/draw rules** · severity: minor
- Evidence: `MAX_PLIES = 1000` → `[0,0]` draw; "stuck player" (`len(_gen_actions)==0`) → terminal draw. Rulebook defines no ply cap and no draws (real games use a clock, "Gegen die Zeit").
- Why it matters: harmless safeguards that prevent infinite rollouts, but they are terminal conditions not in the rulebook. Both are documented in comments. A stuck state is effectively unreachable in Abalone.
- Suggested action: keep as documented conventions; do not treat clock rules as board rules.

## 3. Rule coverage review

| rule area | status | evidence | notes |
|---|---|---|---|
| setup / components | unclear | `initial_state` ASSUMPTION comment; 14 balls/side | Abb. 1 not in packet; unverifiable but documented |
| player count | covered | "Ein Spiel für 2 Spieler"; `num_players = 2` | correct |
| turn order | covered | "Schwarz fängt immer an"; `to_move` starts 0, alternates | correct |
| legal actions (1–3 balls, one dir, adjacent free) | covered | `_resolve` single/in-line/broadside; `k in 1..3`; `POSITIVE_DIRS` enumeration | matches movement rules |
| splitting a longer row | covered | contiguous 1/2/3 sub-group enumeration in `_gen_actions` | interior in-line splits correctly blocked by own balls |
| Sumito (2-1/3-1/3-2, in-line only, free space behind, optional) | covered | `k <= m → None` (strict majority); broadside never pushes; `beyond` occupied → None; normal slides also offered so attacks are optional | faithfully matches Fig. 5 cases 1/2/3 |
| Patt (equal counts, 4-3 ≡ 3-3) | covered | implicit via `k > m` + 3-ball cap (can't select 4) | no special code needed; behavior correct |
| push-off (Hinausschieben) | covered | lead defender `neighbor` off-board → `off_player = opp`, `off[]+=1` | at most one ball off per move, as intended |
| terminal / win (6 out) | covered | `off >= 6` → terminal | correct |
| scoring / returns | covered | `[1,-1]`/`[-1,1]`; `[0,0]` for ongoing/cap/stuck | draw conventions are additions to the rulebook |
| rendering / action names | partially | round-trips exactly; unique 2-char labels; but render letters ≠ label letters | see Finding 2 |
| chance / hidden / simultaneous | covered (N/A) | perfect-info sequential; color-lot not modeled | correct to omit — the lot doesn't affect play (Black starts regardless) |

## 4. Unsupported assumptions or invented rules

Harmless conventions:
- Direction labels `E/W/NE/NW/SE/SW` and cell labels `A1..I9` (rulebook names neither).
- 61-cell hexagon `[5,6,7,8,9,8,7,6,5]` (geometry verified self-consistent).
- Player mapping `0=Black`, `1=White`, Black = player 0 moves first.
- Concatenated (separator-free) label encoding in action names — deliberate, documented to survive normalization.

Riskier / benchmark-relevant:
- **Starting layout and 14-balls-per-side** — invented because Abb. 1 is absent; central to correctness.
- **`MAX_PLIES = 1000` → draw** — invented terminal condition (documented "not a real rule").
- **Stuck player → draw** — rulebook defines no draw outcome at all.

## 5. Missing scenario tests

Prefer action-name sequences that can become deterministic checks:

- **2-to-1 push off edge**: construct a state with `w` at edge, `b b` behind; assert the in-line move is legal, `off[white]` increments, and after 5 prior removals `is_terminal` and `returns == [1,-1]`.
- **3-to-2 push (no removal)**: `b b b | w w | .` in a line; assert defenders shift, none leave board.
- **Blocked Sumito, no space behind (Fig. 5 #1)**: `b b | w | b`; assert the push is *not* in `legal_actions` and `apply_action` raises.
- **Gap case (Fig. 5 #2)**: `b b | . | w`; assert the in-line move is a *slide* (no `off` change), not a push.
- **Head-on Patt**: `b b | w w` (2-2) and `b b b | w w w` (3-3); assert neither can push.
- **Self-push forbidden**: a ball line at the edge facing outward; assert no in-line/broadside move takes an own ball off-board.
- **Broadside split**: a 4-in-a-row line; assert a 3-ball broadside is legal and leaves the 4th behind.
- **Interface regression (would currently fail)**: pin the letter of internal `(8,0)` in both `action_to_name` and the `render` line labels and assert they agree — this catches Finding 2.
- **Round-trip**: for every action in `legal_actions(initial_state())`, assert `name_to_action(action_to_name(a)) == a`.

## 6. Open questions for the human

1. What is the exact Abb. 1 layout — placement and total balls per side (the code assumes 14/14 in the standard opening)?
2. Is the board the 61-cell hexagon (`5..9..5`), and does the figure orientation match the assumed direction mapping?
3. Should a stuck position (no legal move) be a draw, a loss for the stuck player, or is it treated as unreachable? The rulebook defines no draw outcome.
4. Should there be any move/ply cap, or is finiteness left entirely to the clock ("Gegen die Zeit")?

## 7. Machine-readable summary

```text
score: 0.75
confidence: medium
critical_issues: 0
major_issues: 1
minor_issues: 3
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```
