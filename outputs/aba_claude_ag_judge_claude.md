# 1. Score

- `score: 0.85`
- `confidence: medium`

This is a faithful and notably complete reading of the supplied rules. Every verifiable mechanic — 1/2/3-ball inline and broadside moves in all six directions, the three Sumito types via strict majority with a free/edge cell behind, implicit Patt handling, edge capture, and win at six pushed off — is implemented correctly, and the action interface round-trips with readable labels. Confidence is held to medium because the most consequential setup facts (61-cell board, 14-ball symmetric layout) are read off *Abbildung 1*, which is referenced but not present in the text packet, so they cannot be confirmed from the provided artifacts. The only invented rule is a documented ply-cap draw, which the rulebook does not contain.

# 2. Top findings

**Starting position and board size are figure-derived and unverifiable from the packet** — *question*
- Evidence: `BLACK_START`/`WHITE_START` hard-code the standard 14-ball layout (rows A, B, central C3–C5 and the mirror); `BOARD_RADIUS = 4` yields the 5,6,7,8,9,8,7,6,5 hex. The code states these were "read off Abbildung 1," but only the rule *text* is in the packet — the figure image is not.
- Why it matters: setup is foundational; a wrong layout silently invalidates every downstream result. The 14-ball/6-to-lose ratio is internally consistent and matches the universal Abalone start, so risk is low, but it is asserted, not provable from the given text.
- Next action: confirm the layout against the actual Abbildung 1 before treating as benchmark-ready.

**Ply-cap draw is an invented termination/scoring rule** — *minor*
- Evidence: `DEFAULT_MAX_MOVES = 400`; `is_terminal` returns true at `ply >= max_moves`; `returns` then yields `[0.0, 0.0]`. The rulebook gives no draw and uses a chess clock ("Gegen die Zeit"), which is real-time, not a discrete rule.
- Why it matters: introduces a terminal/return outcome the rules do not define; 400 plies could also truncate a legitimate long game as a draw.
- Next action: keep it as a clearly-flagged safeguard (it is documented), but expose it and confirm a draw return is acceptable for the benchmark, or make the cap configurable to non-terminating.

**No handling for a stuck-but-non-terminal state / no pass** — *minor*
- Evidence: comment assumes "a player always has at least one legal move"; there is no pass action and no terminal branch for `legal_actions == []` when not at six captures.
- Why it matters: would violate the "non-terminal states have legal actions" invariant if it ever occurred. Practically unreachable on a 61-cell board with 8–14 balls, so low risk.
- Next action: add a defensive assertion or document the invariant is relied upon.

**`legal_actions` scans the entire global move table each call** — *minor*
- Evidence: `legal_actions` iterates all `ID_TO_MOVE` entries and filters with `_legal`. Correct, but O(total enumerated moves) per call.
- Why it matters: purely performance; no correctness impact. Acceptable for a reference implementation.
- Next action: none required; optionally index moves by occupied own-cell groups.

# 3. Rule coverage review

| rule area | status | evidence | notes |
|---|---|---|---|
| Setup / board / components | partially covered | `BLACK_START`/`WHITE_START`, `_build_cells`, `BOARD_RADIUS=4` | Standard 61-cell hex and 14-ball layout, but sourced from an unseen figure. |
| Player count & turn order | covered correctly | `NUM_PLAYERS=2`, `initial_state` sets `BLACK` to move, `apply_action` flips `to_move` | "Schwarz fängt immer an", strict alternation. |
| Legal actions (move types) | covered correctly | `_enumerate_moves` builds singletons, 2/3 inline (fwd+back) and 4 broadside dirs per axis | All six directions, groups ≤3 enforced by construction ("nicht mehr als drei Kugeln"). |
| Inline slide into free hollow | covered correctly | `_legal` inline branch: `occ is None -> True` | "angrenzende Mulde frei". |
| Broadside (no push) | covered correctly | broadside branch requires every destination empty and on-board | Matches "nur durch Bewegung in gerader Linie" for pushing. |
| Sumito (2-1, 3-1, 3-2) | covered correctly | `len(group) > m and (end off-board or empty)`; adjacency via `front == opp` | Strict majority, contiguous, free/edge behind — matches Abb. 4 and Abb. 5 cases 1–3. |
| Patt (1-1/2-2/3-3, 4↔3) | covered correctly (implicit) | `k > m` strict; group capped at 3 | "Um ein Patt aufzulösen … andere Gerade" is emergent (other lines stay legal); no special code needed. |
| Capture / Hinausschieben | covered correctly | `apply_action` push branch: `dst not in CELLSET -> ns.off[opp] += 1`; only the rearmost ball can exit | One capture per push, correct. |
| Terminal conditions | covered correctly (+ extra) | `off >= CAPTURE_TARGET` (=6); plus invented ply cap | Win condition faithful; cap is an addition. |
| Scoring / returns | covered correctly | `[1,-1]`/`[-1,1]`/`[0,0]`, length 2 | One value per player; draw only at cap. |
| Rendering / action names | covered correctly | `render` compact hex with header; names `move:C3+C4+C5:E` | Deterministic, label-based, round-trips (`name_to_action(action_to_name(a)) == a`). |
| Chance / hidden / simultaneous | n/a (correctly omitted) | none | Perfect-information sequential game; color draw ("Auslosen") is pre-game and not modeled. |

# 4. Unsupported assumptions or invented rules

- **Coordinate labels A–I + column numbers** — harmless convention; rulebook defines no labels. Used only for names/render.
- **400-ply cap → draw `[0,0]`** — *invented*; not in the rulebook. Documented; reasonable anti-infinite-game safeguard but it manufactures a non-rulebook terminal outcome.
- **"Always has a legal move; no pass"** — assumption; reasonable for reachable positions but not stated.
- **Standard 14-ball symmetric start and 61-cell board** — asserted from Abbildung 1; standard for the game but unverifiable from the text portion provided.
- **Only one ball can be pushed off per move** — correctly emergent from the geometry/`m`-shift logic, consistent with the rules (not an invented rule, noted for clarity).

# 5. Missing scenario tests

The file only ships an opening render + round-trip smoke check. Suggested deterministic tests (action-name based where possible):

- **2-vs-1 edge capture**: construct a position, apply a `move:<own2>:<dir>` that pushes one opponent off; assert `off[opp]` increments and, after six, `returns == [1,-1]`.
- **3-vs-2 edge capture**: confirm exactly one ball exits and the rear opponent advances to the edge.
- **Patt is not pushable**: a 3-vs-3 inline alignment; assert the corresponding push move is absent from `legal_actions`.
- **Gap rule (Abb. 5 case 2)**: empty cell between own and opponent; assert the move resolves as a slide (or push not offered), never a capture.
- **Blocked-behind (Abb. 5 case 1)**: opponent with an occupied cell behind; assert push is illegal.
- **Broadside never pushes**: place an opponent ball on a broadside destination; assert that broadside is not legal.
- **Row split**: 4-in-a-row; assert the front-3 inline slide and a 2-ball broadside split are legal while moving the back-3 forward is not.
- **Round-trip on a push and a broadside name** specifically (not just opening singletons).

# 6. Open questions for the human

- Does the actual *Abbildung 1* confirm the 14-ball-per-side standard layout and 61-cell board encoded here?
- Is a synthetic draw acceptable, or should games be unbounded (the rulebook has no draw; termination is by clock)? If a cap is kept, is 400 plies appropriate?

# 7. Machine-readable summary

```text
score: 0.85
confidence: medium
critical_issues: 0
major_issues: 0
minor_issues: 4
needs_rulebook_clarification: true
needs_code_change: false
needs_more_tests: true
```
