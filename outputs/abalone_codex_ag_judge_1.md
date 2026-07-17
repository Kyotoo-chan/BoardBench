## Review result

**Score: 0.94 — confidence: high.**

The implementation closely matches the approved setup, movement geometry, Sumito, ejection, victory, and return rules. The sole material discrepancy is the missing forced-pass transition required by the approved human decision for a player with no legal movement.

## Findings

### Major — Missing forced pass when no movement exists

- **Canonical fact ID:** `TURN-01`, supplemented by the approved forced-pass human decision
- **Evidence type:** `human_decision`
- **Rulebook quote:** “Die Spieler sind abwechselnd an der Reihe. Schwarz fängt immer an.”
- **Page/section:** Page 1, “Der Spielablauf”
- **Approved decision:** “if and only if a player has no legal movement, expose one forced pass that advances the turn.”
- **Conflicting symbols:** `Game.legal_actions`, `Game.apply_action`
- **Expected:** When the active player has no legal movement, `legal_actions` exposes exactly one forced pass, and applying it advances to the other player without changing the board or ejection totals.
- **Implemented:** `legal_actions` returns an empty tuple, and `apply_action` recognizes only `"move"` actions. Such a state has no executable transition despite remaining nonterminal.
- **Impact:** Material phase/turn-flow omission. It can deadlock the environment in a no-movement state. This is an adjudication-dependent interface deviation, not a contradiction of an explicit printed pass rule.

No critical or minor contradictions were found.

## Rule-area coverage

| Rule area | Result | Notes |
|---|---|---|
| Players/setup | Pass | 61-pit axial board; correct 14/14 Figure-1 placement |
| First player/alternation | Pass except no-move case | Black begins; successful moves alternate |
| Selection geometry | Pass | Contiguous straight groups of 1–3 |
| Ordinary inline movement | Pass | One adjacent pit; destination must be empty |
| Broadside movement | Pass | All translated destinations must be on-board and empty |
| Longer-row subsets | Pass | Legal 1–3 marble subsets are generated |
| Sumito strength | Pass | Supports 2v1, 3v1, and 3v2 only |
| Sumito restrictions | Pass | Inline, adjacent, collinear, and unblocked |
| Patt | Pass | Equal groups and 4+v3 cannot push |
| Edge ejection | Pass | Outermost defender is removed |
| Victory/returns | Pass | Immediate sixth-ejection terminal result; ±1 winner/loser |
| Draw/repetition | Pass | No unsupported terminal rule added |
| Clock | Pass | Correctly excluded |
| Forced pass | **Fail** | Approved no-movement transition is absent |
| Action serialization | Pass | Generated actions round-trip canonically |

## Missing deterministic scenarios

The embedded assertions cover only initial inventory size, existence of an opening action, and action-name round trips. Deterministic coverage should add:

- Exact nine-row Figure-1 setup and 14/14/33 inventory.
- Single, double, and triple inline moves.
- Double and triple broadside moves in each nonparallel direction.
- Moving a legal subset out of a longer row.
- Rejection of disconnected, bent, four-marble, occupied-destination, and off-board ordinary moves.
- Legal 2v1, 3v1, and 3v2 pushes.
- Rejection of 1v1, 2v2, 3v3, 4v3-effective, gap, non-collinear, broadside, and rear-blocked pushes.
- Edge pushes verifying exactly one defender is ejected.
- Fifth ejection remaining nonterminal and sixth ejection becoming immediately terminal with correct returns.
- A no-legal-movement fixture exposing exactly one forced pass and preserving board/ejection state while changing the player.

## Material questions for a human

None for current scoring. The printed rules do not specify no-movement handling, but the approved human decision already resolves that source gap. No rulebook clarification is needed unless that decision is reconsidered.

score: 0.94
confidence: high
critical_issues: 0
major_issues: 1
minor_issues: 0
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true