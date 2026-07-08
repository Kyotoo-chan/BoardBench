### 1. Score

- score: 0.55
- confidence: medium

The implementation is playable and captures the basic two-player placement structure, Red-first turn order, empty-cell legality, and plausible versions of the three win concepts. However, the actual board geometry, finite board size, conical topology, edge division, and formal surround/loop detection are largely assumed rather than derived from the provided rule text. These assumptions affect core gameplay and make the environment not benchmark-ready without clarification.

### 2. Top findings

1. **severity: major**  
   **evidence:** Rulebook describes Conect as played “on the curved surface of a cone” with boards formed by rolling a hexagonally tessellated rhombus; code uses a flat axial hex board with configurable `board_radius=3`.  
   **why it matters:** Legal cells, adjacencies, edge topology, and surround/loop detection may differ substantially from the intended conical board.  
   **suggested next action:** Define the exact board cell set and adjacency graph from the rulebook figures or an explicit coordinate specification.

2. **severity: major**  
   **evidence:** Rulebook says the edge is divided into red and blue parts with two shared edge cells; code arbitrarily splits the perimeter halfway using `split = 3 * board_radius`.  
   **why it matters:** Edge ownership directly determines all three win conditions.  
   **suggested next action:** Encode the official red/blue/shared edge cells explicitly.

3. **severity: major**  
   **evidence:** Code implements surrounding via `_center_cut_off_by_barrier` flood fill and edge-loop wins via a component plus an assumed edge segment. Rulebook gives visual/qualitative descriptions but no formal algorithm in the text.  
   **why it matters:** The implementation may produce false positives or false negatives for Figures 1–3, especially on the intended cone topology.  
   **suggested next action:** Add deterministic tests matching the three illustrated win examples.

4. **severity: minor**  
   **evidence:** Code declares a draw when the board is full and returns `[0.0, 0.0]`; the rulebook does not specify draws or numeric scoring.  
   **why it matters:** Necessary for an API, but it is an invented convention.  
   **suggested next action:** Confirm whether full-board no-win states are possible and what returns should be.

5. **severity: minor**  
   **evidence:** Action names and rendering use invented axial coordinate labels.  
   **why it matters:** Stable and usable, but not tied to rulebook labels or diagrams.  
   **suggested next action:** Replace or supplement with official cell labels if available.

### 3. Rule coverage review

| rule area | covered correctly / partially covered / missing / unclear | evidence | notes |
|---|---|---|---|
| setup / board | partially covered | Initially empty board is implemented; board is flat radius-3 hex by default | Exact Conect cone board is not implemented or specified |
| player count and turn order | covered correctly | `num_players = 2`, Red starts, turn alternates | Matches rulebook |
| legal actions | covered correctly for assumed board | Legal actions are empty cells only | Matches “placing onto unoccupied cells” |
| state transitions | mostly covered | `apply_action` places one stone and switches player | Good for deterministic placement game |
| terminal conditions | partially covered | Implements three win checks plus full-board draw | Win checks depend on assumed geometry and interpretation |
| scoring / returns | partially covered / unclear | Win gives `+1/-1`, draw `0/0` | Rulebook does not specify numeric returns |
| rendering / action names | mostly covered | Stable `place:q..._r...` names and compact render | Labels are invented but human-readable |
| chance / hidden information / simultaneous moves | covered correctly | None implemented | Rulebook describes perfect-information alternating play |

### 4. Unsupported assumptions or invented rules

**Risky assumptions:**
- Uses a flat ordinary hex board rather than an explicit conical/rhombus-derived topology.
- Defaults to `board_radius=3`; no board size is specified in the provided text.
- Splits the perimeter into two equal arcs and chooses two shared cells mechanically.
- Treats axial `(0, 0)` as the center cell.
- Defines “surrounds the center” by flood-fill separation from perimeter cells.
- Defines edge-loop wins using an assumed ordered edge path segment.
- Ignores any possible wide-vs-narrow board distinction from the conical board discussion.

**Mostly harmless conventions:**
- Uses numeric returns `+1/-1/0`.
- Uses invented coordinate-based action names.
- Declares a full-board no-win state as a draw, though this should be confirmed.

### 5. Missing scenario tests

Suggested deterministic tests:

1. **Initial state / placement**
   - Initial player is Red.
   - `place:qzero_rzero` is legal.
   - After Red places there, Blue to move and the same action is illegal.

2. **Center-path Red win**
   - `place:qneg3_rzero`
   - `place:qpos3_rzero`
   - `place:qneg2_rzero`
   - `place:qpos2_rpos1`
   - `place:qneg1_rzero`
   - `place:qpos1_rpos2`
   - `place:qzero_rzero`
   - Expected: Red terminal win by center-path.

3. **Shared edge usable by Blue**
   - Build a Blue path from a shared edge cell to center and verify Blue wins.

4. **Surrounding-group win on the assumed board**
   - Test a Red ring around center plus a connection to a Red edge cell.
   - Expected: Red terminal win by surrounding-group.

5. **Figure-based tests**
   - Translate Figures 1, 2, and 3 into exact action-name sequences once official cell labels/geometry are known.
   - Verify each triggers the intended specific win condition.

6. **Terminal stability**
   - After any win, `legal_actions` should be empty and `returns` stable.

### 6. Open questions for the human

- What exact board geometry and cell adjacency should be used: wide cone, narrow cone, both, or another standard board?
- What are the official red-edge, blue-edge, and shared-edge cells?
- How should “surrounds the center” be formalized on the conical surface?
- Are draws possible, and what scoring convention should BoardBench use?

### 7. Machine-readable summary

```text
score: 0.55
confidence: medium
critical_issues: 0
major_issues: 3
minor_issues: 2
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```
