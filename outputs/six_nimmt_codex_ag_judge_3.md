score: 0.82  
confidence: high

The reachable core game logic is largely faithful: setup, placement, captures, scoring, repeated games, threshold, shared winners, and returns are implemented correctly. The main defect is that normal rounds never expose the required joint reveal to observers. A second, less reachable issue allows excluded match targets through deserialization.

## Findings

### Major — Jointly revealed cards disappear before players can observe them

- Canonical fact ID: `6N-C-JOINT-REVEAL`
- Evidence type: `rule_quote`
- Source: `6NIMMT-V23-RULES`, PDF page 1
- Exact evidence: “Erst dann, wenn der Letzte sich entschieden hat, werden die Karten aufgedeckt.”
- Conflicting transition: `Game.apply_action → _continue_resolution → _finish_round`, especially [implementation.py:168](C:/Users/benti/AppData/Local/Temp/.ctx-mode-0736Yf/boardbench_six_nimmt_codex_ag_judge_3_44kyp3st/implementation.py:168) and [implementation.py:141](C:/Users/benti/AppData/Local/Temp/.ctx-mode-0736Yf/boardbench_six_nimmt_codex_ag_judge_3_44kyp3st/implementation.py:141).
- Expected: after everyone commits, all committed identities become jointly observable before or during ordered resolution.
- Implemented: the final commitment reveals and resolves every card inside one transition. If no low-card choice interrupts resolution, `_finish_round` immediately clears both `zones.revealed` and `zones.resolved`. Consequently, no returned state exposes the reveal. This is especially consequential when an early played card is subsequently swept into a face-down capture during the same resolution.
- Required change: introduce an observable reveal/resolution state or preserve the completed round’s revealed cards until the next commitment begins.

### Major — Deserialization admits excluded non-default match targets

- Canonical fact IDs: `6N-C-MATCH-THRESHOLD`, `6N-C-ALTERNATE-TARGET`
- Evidence type: `rule_quote`
- Source: `6NIMMT-V23-RULES`, PDF page 2
- Exact evidence:
  - “Es werden mehrere Spiele durchgeführt, bis ein Spieler insgesamt über 66 Hornochsen eingesammelt hat.”
  - “Vor Beginn der Partie kann natürlich auch eine andere Punktzahl oder Anzahl an Spielen vereinbart werden.”
- Approved scope: the default match over 66 is included; optional targets and game-count variants are excluded.
- Conflicting symbol: `Game.state_from_data`, [implementation.py:286](C:/Users/benti/AppData/Local/Temp/.ctx-mode-0736Yf/boardbench_six_nimmt_codex_ag_judge_3_44kyp3st/implementation.py:286).
- Expected: a deserialized base-game state has `match_target == 66`, or the loader rejects it.
- Implemented: any integer is accepted. `_finish_round` then uses that value for termination, allowing targets such as `0` or `1000` and materially changing match length.
- Required change: require exactly `66` for this base-game schema.

### Minor — Terminal rendering presents an already-added game subtotal beside the cumulative score

- Canonical fact ID: `6N-C-GAME-SCORE`
- Source: `6NIMMT-V23-RULES`, PDF page 2
- Evidence: “Jetzt nimmt jeder seinen Hornochsenstapel und zählt seine Minuspunkte.”
- Symbol: `Game.render`, [implementation.py:196](C:/Users/benti/AppData/Local/Temp/.ctx-mode-0736Yf/boardbench_six_nimmt_codex_ag_judge_3_44kyp3st/implementation.py:196).
- At terminal entry, `_finish_round` has already added `game_bullheads` into `total_bullheads`, but rendering still displays `total+game`. Winner computation remains correct, but the presentation can be read as double-counting.

### Question — What is the trust boundary of `state_from_data`?

The packet does not define malformed-state deserialization behavior. The loader accepts arbitrary integer card values, duplicates, any number of rows, empty rows, a player list inconsistent with `configuration.players`, and inconsistent phase/current-player combinations. Some accepted states can later crash at `row[-1]`.

This is not scored as a printed-rule contradiction because no canonical claim specifies serialized-state rejection. If this is an untrusted public boundary, semantic validation is materially incomplete.

## Rule-area coverage

| Rule area | Status | Notes |
|---|---|---|
| Components and setup | Pass | Cards 1–104, shuffle, ten-card hands, four starters, correct reserve arithmetic |
| Player range | Pass | Rejects values outside 2–10 |
| Hidden commitments | Pass | Seat-ordered protocol hides committed identities |
| Joint reveal | Major issue | Reveal is not observable in uninterrupted rounds |
| Ascending resolution | Pass | Sorted by card value and processed dynamically |
| Ordinary placement | Pass | Correct eligible row and minimum positive difference |
| Sixth-card capture | Pass | Existing five captured; played card becomes starter |
| Low-card choice | Pass | Any of four rows is legal; resolution resumes afterward |
| Captured-card handling | Pass | Kept outside hands and scored correctly |
| Bullhead inventory | Pass | Correct precedence for 55, repeated digits, tens, and fives |
| Game completion | Pass | Ten rounds and empty hands coincide on reachable states |
| Match completion | Pass from initial state | Strictly greater than 66; compromised by imported target |
| Winner and returns | Pass | All minimum-score ties win; approved `+1/-1` returns |
| Private observations | Pass except reveal | Opponent hands and captured identities remain hidden |
| Serialization | Question | Structural checks exist, but semantic invariants are not enforced |

## Missing deterministic scenarios

- An uninterrupted round must expose every committed identity jointly before reveal data is cleared.
- An early revealed card later captured by a sixth card in the same resolution must still have been observable at reveal.
- A low-card interruption followed by another low card should preserve ascending, dynamically updated resolution.
- Deserialization with `match_target` values `65`, `67`, `0`, and a very large integer must be rejected under base scope.
- Exactly 66 after a completed game must start a new game; 67 must terminate.
- Terminal rendering should distinguish previous cumulative score, current-game score, and final cumulative score.
- If deserialization is untrusted: reject empty/wrong-count rows, out-of-range or duplicate cards, mismatched player counts, and inconsistent phase/pending state.

## Material questions for a human

- Is `state_from_data` a trusted round-trip-only mechanism, or must it reject arbitrary externally supplied states?
- Which API state should represent the mandatory joint reveal: a dedicated reveal phase, stepwise resolution, or retained previous-round reveal history?

```text
score: 0.82
confidence: high
critical_issues: 0
major_issues: 2
minor_issues: 1
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true
```