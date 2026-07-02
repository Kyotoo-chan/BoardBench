Could not write `outputs/abalone_oneshot_judge.md` because the session filesystem is read-only. Judge report:

### 1. Score

- `score: 0.62`
- `confidence: medium`

The implementation captures much of the turn structure, one-step movement, 1-3 marble movement, side/inline moves, Sumito superiority, Patt blocking, off-board pushes, and six-marble win condition. The main benchmark risk is that setup and board geometry are invented because the provided text references Abb. 1 but does not include the actual diagram contents. That makes the game playable, but not clearly faithful or benchmark-ready.

### 2. Top findings

1. **severity: major**  
   **evidence:** Rulebook says setup follows “Abb. 1”; code says `_default_start`: “Placeholder only: the real start diagram was referenced but not provided,” and uses `radius=3` with six marbles per player.  
   **why it matters:** Initial board shape and marble count strongly affect all legal actions and game length.  
   **suggested next action:** Add the actual diagram-derived setup or mark this implementation as a reduced placeholder variant.

2. **severity: major**  
   **evidence:** Rulebook describes the physical board only through figures and “Mulden”; code invents axial coordinates and a radius-3 hex board.  
   **why it matters:** Legal movement and off-board pushes depend on board boundaries.  
   **suggested next action:** Confirm board coordinate system and radius from provided page images before scoring as faithful.

3. **severity: minor**  
   **evidence:** `off_black` / `off_white` records marbles of that color pushed out, while winner is the opponent.  
   **why it matters:** Rendering is deterministic but could be misread during side-by-side inspection.  
   **suggested next action:** Rename/render as `black_removed` and `white_removed`, or add captured-by-player counts.

4. **severity: minor**  
   **evidence:** No maximum turn limit, repetition rule, draw, or clock handling. Rulebook mentions optional timed play only.  
   **why it matters:** Rollouts could theoretically run long, though no draw rule is specified.  
   **suggested next action:** Leave clock unimplemented, but consider a documented rollout cap outside game rules.

### 3. Rule coverage review

| rule area | covered correctly / partially covered / missing / unclear | evidence | notes |
|---|---|---|---|
| setup | partially covered | Rulebook: setup as in Abb. 1; code uses placeholder default start | Most important fidelity gap |
| player count and turn order | covered correctly | `num_players = 2`; black starts; alternates after action | Matches “Schwarz fängt immer an” |
| legal actions | mostly covered | 1, 2, or 3 own marbles; six directions; inline and side moves | Core movement appears implemented |
| state transitions | mostly covered | `apply_action` moves groups, pushes opponents, switches player | Fresh immutable state returned |
| Sumito | mostly covered | Allows stronger inline pushes: 2v1, 3v1, 3v2; blocks equal or stronger opponent runs | Matches described Sumito/Patt structure |
| Patt | mostly covered | Equal-length opponent runs cannot be pushed; max moved group is 3 | 4v3 effectively treated as 3v3 because only three own marbles move |
| terminal conditions | covered correctly | first side with six marbles of its color pushed out loses | Matches “zuerst sechs Kugeln des Gegners” |
| scoring/returns | covered correctly | winner gets `1.0`, loser `-1.0` | Reasonable zero-sum BoardBench convention |
| rendering/action names | partially covered | Stable coordinate labels and action names | Human-readable, but not rulebook labels from diagrams |
| chance/hidden/simultaneous | covered correctly as not relevant | No such rules in provided text | No extra APIs needed |
| clock/timed play | missing but acceptable | Rulebook presents timed play as optional | Not necessary for base environment |

### 4. Unsupported assumptions or invented rules

- **Risky:** Radius-3 hex board geometry is invented from absent diagrams.
- **Risky:** Default setup uses exactly six marbles per player, derived from the win target rather than stated setup text.
- **Risky:** Coordinate labels are invented because no board labels are provided in the text.
- **Harmless convention:** Returns use `[1.0, -1.0]` for winner/loser; the rulebook gives only win/loss.
- **Harmless convention:** Black is player `0`, white is player `1`.
- **Harmless convention:** Timed play is omitted because the rulebook frames it as optional.

### 5. Missing scenario tests

- Initial state: black to move, two players, non-terminal, stable render.
- Single marble move into an adjacent empty hole is legal and moves exactly one step.
- Single marble move into occupied or off-board hole is illegal.
- Two-marble inline move into an empty front hole moves both marbles one step.
- Two-marble side move requires both destination holes empty.
- Three-marble side move requires all three destination holes empty.
- 2-to-1 Sumito into an empty hole pushes the opponent one hole.
- 3-to-2 Sumito into an empty hole pushes both opponent marbles.
- Sumito off board increments the pushed color’s off count.
- Sixth pushed-out opponent marble makes the state terminal and returns winner/loser.
- 1-to-1, 2-to-2, and 3-to-3 Patt pushes are illegal.
- A push is illegal when there is an empty gap between own and opponent marbles.
- A push is illegal when the opponent group has an occupied hole behind it.
- A longer own row can be split by moving only one, two, or three selected contiguous marbles.
- `action_to_name(name_to_action(name)) == name` for sampled legal actions.

### 6. Open questions for the human

1. Should the actual Abb. 1 starting position and full board shape be available as rendered page images for this judge step?
2. Is this intended to be a reduced Abalone-like environment, or should it match the rulebook’s illustrated physical setup exactly?
3. Should rendered/action coordinate labels later be aligned to diagram labels, if any exist in the source images?

### 7. Machine-readable summary

```text
score: 0.62
confidence: medium
critical_issues: 0
major_issues: 2
minor_issues: 2
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```