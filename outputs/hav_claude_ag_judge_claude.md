# Havannah judge review — `hav_claude_ag.py`

> Scope note: I evaluated this against the rule text embedded/paraphrased in the packet (the file's rule docstring) and the packet's OpenSpiel anchor `havannah(board_size=8)`. In this non‑interactive step I could not independently read the rendered rulebook page images, so items that depend on wording I cannot see are marked as **questions** rather than defects, and confidence is capped at medium.

## 1. Score

- `score: 0.85`
- `confidence: medium`
- Justification: The core Havannah engine is faithful and well‑reasoned — correct 169‑point hexagon (side 8), placement‑only play with Red first, and all three victory figures (bridge, fork, ring) with a topologically sound ring test via boundary flood‑fill. Deductions are for unverifiable rulebook specifics (possible swap rule, an official point notation) and a couple of documented modeling assumptions (draw‑by‑stone‑exhaustion), none of which I could confirm as actual errors. It is close to benchmark‑ready; remaining risk is rulebook‑confirmation, not visible logic bugs.

## 2. Top findings

**Finding 1 — Swap/pie rule not modeled (severity: question, potentially major)**
- Evidence: `legal_actions` returns every empty cell on every turn; there is no special move‑2 swap option. Havannah is frequently played with a swap rule to offset first‑player advantage.
- Why it matters: If the rulebook specifies a swap/pie rule, the legal action set on the second move is wrong and win‑rate benchmarks would be biased.
- Next action: Confirm from the rulebook whether a swap rule exists. If absent (common for basic rulebooks), current behavior is correct.

**Finding 2 — Ring detection is sound (severity: positive / minor edge case)**
- Evidence: `_has_ring` BFS‑floods all non‑component cells reachable from the hex outline; any unreached non‑component cell is enclosed → ring. Hex adjacency avoids the square‑grid diagonal‑leak problem, so this is clean.
- Edge case: an enclosed cell that is the *same colour and adjacent to the loop* is folded into the component and not reported. I believe this is correct (that is a solid blob, not a ring) and moot in play (a genuine hole would have won earlier); genuine enclosures of empty, enemy, or *disconnected* same‑colour stones are all detected. Worth a dedicated test rather than a code change.
- Next action: Add targeted ring tests (see §5).

**Finding 3 — Draw by stone exhaustion is an assumption, not a stated rule (severity: minor)**
- Evidence: `STONES_PER_PLAYER = 55` derived from "box contents"; `apply_action` declares `DRAW` when the next player has no stones or the board fills. The docstring flags this as an assumption.
- Why it matters: It creates a well‑defined bounded terminal (good for benchmarking) but invents a draw condition the rulebook may not state; the exact cap (55) also depends on component text I can't verify. Practically unreachable (110 stones on 169 points), so low gameplay impact.
- Next action: Confirm whether the rulebook defines any draw; if the game is "always won," document the branch explicitly as a safety bound only.

**Finding 4 — Invented coordinate naming for actions (severity: minor)**
- Evidence: `action_to_name` emits `place:q<coord>_r<coord>` with `p`/`n`/`0` sign encoding (e.g. `place:qp1_rn6`). Round‑trips exactly and keeps mirror cells (`qp1` vs `qn1`) distinct under punctuation normalization — meets the prompt's naming constraints well.
- Why it matters: If the rulebook prints an official point notation (letter/number hex labels), action names should use it for side‑by‑side fidelity; the axial q/r scheme is an internal convention.
- Next action: Check the rulebook/board diagram for a labeled coordinate system.

**Finding 5 — Win check only inspects the moved stone's component (severity: positive)**
- Evidence: `_is_win(ns.board, action, p)` uses `_component(...action...)`. Since a placement can only extend the mover's own group, any newly completed figure must include the new stone — this is correct and efficient, and a win only occurs on the mover's own turn.

## 3. Rule coverage review

| Rule area | Status | Evidence | Notes |
|---|---|---|---|
| Setup / board & components | covered correctly | `_gen_cells`, `N==169`, `sum(CORNER)==6`, side/boundary classification | 169‑pt hexagon side 8 matches "169 Schnittpunkte" and OpenSpiel `board_size=8`; empty start |
| Player count & turn order | covered correctly | `NUM_PLAYERS=2`, `RED=0` first, strict `to_move = 1-p` alternation | "Rot fängt an"; no capture/move ("nicht geschlagen … nicht gezogen") |
| Legal actions | covered correctly | `legal_actions` = all empty cells; no pass | Placement‑only; empties only |
| State transitions | covered correctly | `apply_action` places, decrements stones, sets `last_move`, switches player, returns fresh state | Fresh‑state (immutable) transition per backbone |
| Terminal conditions | covered correctly (+ assumption) | `_is_win` bridge/fork/ring; draw on exhaustion | Bridge ≥2 corners; fork ≥3 sides (corners excluded); ring via flood‑fill. Draw is an assumption (Finding 3) |
| Scoring / returns | covered correctly | `returns`: +1/−1 win, 0/0 draw & ongoing | One numeric value per player; stable at terminal |
| Rendering / action names | covered (naming invented) | `render` compact hex ASCII + header; `place:q_r` round‑trips | Deterministic; naming is an internal convention (Finding 4) |
| Chance / hidden / simultaneous | not applicable | none present | Correctly omitted for a sequential perfect‑info game |
| Invariants | covered correctly | terminal ⇒ `legal_actions == []`; no non‑terminal state hands control to a 0‑stone player | Draw is set in the same `apply_action` that would exhaust the next player |

## 4. Unsupported assumptions or invented rules

- **Board = regular hexagon, side 8 (radius 7).** Reasonable derivation from "169 points"; corroborated by the packet's OpenSpiel reference. *Harmless.*
- **55 stones/player cap ⇒ draw on exhaustion.** Draw condition and exact count derived from component list, not a stated game rule. *Low‑risk bound, flag for confirmation.*
- **No swap/pie rule.** Assumes plain alternation on move 2. *Risky only if the rulebook specifies swap (Finding 1).*
- **Axial q/r action names (`place:qp1_rn6`).** Invented notation because no rulebook labels were used. *Harmless convention; supersede if the rulebook defines point labels.*
- **Draw returns `[0,0]` identical to "ongoing."** Standard convention; fine because `is_terminal` disambiguates.

## 5. Missing scenario tests

Suggested deterministic action‑name sequences (each should assert winner/returns and that terminal states have no legal actions):

- **Bridge win:** connect two corners (e.g. path from `place:qp7_r0` toward `place:q0_rp7`); assert Red wins, `returns == [1,-1]`.
- **Fork win:** connect three different sides (`q+`, `r+`, `s+`); assert win.
- **Ring around empty cell:** six stones surrounding one empty point; assert ring win *on the closing move only*.
- **Ring around enemy stone:** enclose a single opponent stone; assert ring win (rulebook: enclosed colour irrelevant).
- **Ring around disconnected same‑colour stone:** own stone floating in the loop interior (not touching the loop); assert ring win — this specifically exercises the component/enclosure boundary of Finding 2.
- **Filled hexagon (7 own stones, no hole):** assert **no** ring — confirms the intended non‑detection.
- **Edge‑hugging arc (edge to edge, no interior hole):** assert **no** ring (boundary cells remain reachable).
- **Line across the board:** assert not a ring (may still be bridge/fork if it hits corners/sides — pick coordinates that hit neither).
- **Naming round‑trip:** `name_to_action(action_to_name(a)) == a` for a corner, an edge cell, the center `place:q0_r0`, and a normalized `p0/n0` variant; assert `apply_action` rejects an occupied cell and an off‑board name.
- **Exhaustion draw (if kept):** a scripted 110‑move game with no figure ⇒ `DRAW`, `[0,0]`, empty legal actions.

## 6. Open questions for the human

1. Does the rulebook define a **swap/pie rule**? (Directly changes move‑2 legal actions.)
2. Does the rulebook define an **official point/coordinate notation** that action names and `render` should adopt?
3. Does the rulebook define any **draw** condition, or is Havannah stated as always decisive? (Governs the stone‑exhaustion branch.)
4. Is **55 stones per colour** the correct component count, and is the board size fixed at side 8 (no alternate sizes)?

## 7. Machine-readable summary

```text
score: 0.85
confidence: medium
critical_issues: 0
major_issues: 0
minor_issues: 2
needs_rulebook_clarification: true
needs_code_change: false
needs_more_tests: true
```
