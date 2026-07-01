### 1. Score

score: 0.72  
confidence: medium

The implementation is playable and captures the central Abalone mechanics described in the rule text: two players, alternating turns, black first, one-step moves, groups of one to three own balls, broadside moves, inline Sumito pushes, strict majority, Patt blocking, off-board captures, and first to six captures wins. The main weaknesses are that the initial setup, coordinate system, full board geometry, stuck-player draw rule, and ply cap are implementation assumptions rather than rule-text facts from the provided packet.

### 2. Top findings

1. severity: major  
   evidence: code comment says `ASSUMPTION: standard Abalone opening (Abb. 1 not provided)`; rule text only says place balls as shown in Figure 1.  
   why it matters: setup strongly affects all reachable states and benchmark comparison.  
   suggested next action: confirm Figure 1 layout from the rulebook image or mark this as an explicit unresolved assumption.

2. severity: major  
   evidence: `MAX_PLIES = 1000`; `is_terminal` treats ply cap as terminal draw. Rule text only says the first player to push out six opponent balls wins.  
   why it matters: invented terminal conditions can change long games and rollout scores.  
   suggested next action: remove for strict rule fidelity, or keep only as a clearly benchmark-specific safety cap outside rule scoring.

3. severity: minor  
   evidence: `is_terminal` returns true if current player has no legal actions, with comment `rules silent -> draw`.  
   why it matters: rulebook does not define no-move/stalemate resolution.  
   suggested next action: document as benchmark convention or avoid terminalizing stuck states unless needed.

4. severity: minor  
   evidence: rule text says Sumito is allowed when behind attacked balls there is a free hollow; Figure 8 also allows pushing out. Code allows pushing off board when `beyond` is off-board.  
   why it matters: this is probably intended by “Hinausschieben,” but the free-hollow wording and off-board edge case should be tested explicitly.  
   suggested next action: add edge Sumito tests for pushing one ball off the board.

5. severity: minor  
   evidence: action names use invented board labels like `A1`, `I5`, and compressed multi-cell labels such as `move:A1A2->E`.  
   why it matters: stable and round-trippable, but not derived from the rulebook text.  
   suggested next action: keep if no official labels are available, but document the coordinate convention.

### 3. Rule coverage review

| rule area | covered correctly / partially covered / missing / unclear | evidence | notes |
|---|---|---|---|
| setup | partially covered | `initial_state` uses standard assumed opening | Rule text depends on Figure 1, not fully represented in packet text. |
| player count and turn order | covered correctly | `num_players = 2`, black player `0` starts, turns alternate | Matches “Ein Spiel für 2 Spieler” and “Schwarz fängt immer an.” |
| legal actions | mostly covered | `_resolve` supports 1-3 own balls, six directions, one-step moves | Broadside and inline movement are both represented. |
| state transitions | mostly covered | `apply_action` returns fresh state, switches player, increments captures | Captures update only when a ball is pushed off board. |
| Sumito / Patt | mostly covered | strict majority `k > m`; 1v1, 2v2, 3v3 blocked | Captures the key text; tests should confirm all three Sumito and Patt cases. |
| terminal conditions | partially covered | six opponent balls out wins; also ply cap and stuck draw | Extra terminal rules are invented. |
| scoring / returns | covered correctly for wins, partial otherwise | `[1.0, -1.0]`, `[-1.0, 1.0]`, otherwise draw/ongoing zero | Ongoing and drawn states both return zero. |
| rendering / action names | partially covered | deterministic render and round-trip names | Labels are useful but invented. |
| chance | covered correctly | no chance methods | Rulebook has color lottery before play, but gameplay starts with black; no in-game chance needed. |
| hidden information | covered correctly | full public state | Rulebook has no hidden information. |
| simultaneous moves | covered correctly | sequential only | Rulebook says players alternate. |

### 4. Unsupported assumptions or invented rules

- Risky: standard Abalone starting setup is assumed because Figure 1 is not available in the text packet.
- Risky: full hex board geometry and coordinate labels are assumed rather than specified textually.
- Risky: `MAX_PLIES = 1000` creates an artificial draw condition.
- Risky: no-legal-action states are treated as terminal draws, though the rulebook does not define this.
- Harmless convention: player `0` means black and player `1` means white.
- Harmless convention: returns use `1.0/-1.0/0.0`; rulebook only defines winner, not numeric scoring.
- Harmless convention: action names use `move:<cells>-><direction>` because the rulebook gives no formal notation.

### 5. Missing scenario tests

- Initial state has 14 black and 14 white balls, black to move, and no balls out.
- Single ball move into adjacent empty hollow succeeds.
- Single ball move into occupied hollow fails.
- Two-ball inline slide into empty space succeeds.
- Three-ball broadside move succeeds only when all destination hollows are empty.
- Four-ball group cannot be moved.
- 2-to-1 Sumito succeeds when defender has free space behind.
- 3-to-1 Sumito succeeds.
- 3-to-2 Sumito succeeds.
- 1-to-1, 2-to-2, and 3-to-3 Patt pushes fail.
- Sumito fails when there is an empty hollow between attacker and defender.
- Sumito fails when the defender group is blocked by another ball behind it.
- Edge Sumito pushes one opponent ball off board and increments the correct `off` counter.
- Game becomes terminal when one player has pushed out six opponent balls.
- Terminal states have no legal actions and stable returns.
- `action_to_name` / `name_to_action` round-trip for representative single, inline, broadside, and Sumito actions.

### 6. Open questions for the human

- Does Figure 1 match the implementation’s assumed standard starting layout?
- Should benchmark implementations include a ply cap, or should terminality follow only the six-captures win rule?
- Should no-legal-action states be treated as draws, illegal states, or left unspecified?

### 7. Machine-readable summary

```text
score: 0.72
confidence: medium
critical_issues: 0
major_issues: 2
minor_issues: 3
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```