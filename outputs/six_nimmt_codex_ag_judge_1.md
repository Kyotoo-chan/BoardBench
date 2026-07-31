Score: **0.84**, confidence: **high**. Core setup, placement, capture, scoring, and match termination are implemented correctly. The main defect is that joint reveals are usually erased before any player-visible state can expose them, materially changing public information.

## Findings

### Major — Jointly revealed cards can disappear before players can observe them

- Canonical fact: `6N-C-JOINT-REVEAL`
- Evidence type: `rule_quote`
- Source: `6NIMMT-V23-RULES`, PDF page 1
- Exact evidence: “Erst dann, wenn der Letzte sich entschieden hat, werden die Karten aufgedeckt.”
- Conflicting transition: `Game.apply_action()` → `Game._continue_resolution()` → `Game._finish_round()`, especially clearing `zones["revealed"]` and `zones["resolved"]`
- Expected: after the last commitment, every committed identity is jointly revealed and available to all players before or while ascending resolution occurs.
- Implemented: the final commitment reveals and resolves every card in one atomic transition. In rounds 1–9, `_finish_round()` then clears both reveal and resolution records before returning. Unless resolution pauses for a low-card row choice, there is no observable state containing the joint reveal.
- Impact: an early played card can be captured by a later card in the same resolution. Its identity is then absent from the rows, hidden from opponents’ captured-card observations, and erased from `revealed`/`resolved`. Players therefore may never learn a card that the printed rules required everyone to see. This materially changes information available for later decisions.

### Minor

None.

### Question — Required strictness of imported states is unspecified

`state_from_data()` validates structure but not canonical reachability. For example, its `card()` accepts any integer, `match_target` may be any integer, four rows are not required, and card uniqueness/inventory is not checked. Such states can contradict `6N-M-CARD-IDENTITIES`, `6N-C-FOUR-ROWS`, and `6N-C-MATCH-THRESHOLD`, or create inconsistent legal-action behavior.

The approved packet defines canonical gameplay but does not explicitly state whether deserialization must reject every semantically impossible payload. I therefore treat this as a `question`, not a scored contradiction.

## Rule-area coverage

| Rule area | Result | Notes |
|---|---|---|
| Player range and setup | Pass | 2–10 players; 104 unique cards; ten-card hands; four rows; correct reserve count |
| Shuffle/chance | Pass | Full-deck deterministic seeded shuffle; successive games reshuffle |
| Hidden commitments | Pass | Seat-ordered submissions conceal opponent identities |
| Joint reveal/public information | **Fail** | Reveal history usually erased before observation |
| Ascending resolution | Pass | Sorted by card value |
| Forced-row placement | Pass | Correct smallest positive difference |
| Sixth-card capture | Pass | Five existing cards captured; played card starts row |
| Low-card choice | Pass | Any of four rows is legal; resolution resumes dynamically |
| Captured piles/scoring | Pass | Captures stay out of hand; bullhead hierarchy is correct |
| Game boundary | Pass | Ten rounds and empty hands |
| Match boundary | Pass | Strictly over 66; exactly 66 continues |
| Winners/returns | Pass | Minimum cumulative score; shared winners; approved +1/−1 returns |
| Serialization | Question | Structural checks do not ensure canonical/reachable state |

## Missing deterministic scenarios

- A non-final round where an early revealed card becomes the fifth card of a row and a later revealed card captures that row. Assert that every player observes the complete joint reveal before identities are hidden.
- Compare an uninterrupted resolution with one paused by a low-card row choice; reveal visibility should not depend on whether a choice happens to interrupt resolution.
- Round-trip imported states plus deliberately schema-valid but semantically invalid states: card 105, duplicate cards, non-66 target, wrong row count, and mismatched player counts.
- End-of-game boundary cases for cumulative totals exactly 66 versus 67, including tied minimum winners.

## Material questions for a human

- Must `state_from_data()` reject all semantically impossible or out-of-scope states, or is it permitted to trust payloads previously produced by `state_to_data()`? The supplied rule packet does not define this API contract.
- Should joint reveal be represented as a dedicated observable phase, or is retained public reveal history after atomic resolution sufficient? Either approach can satisfy `6N-C-JOINT-REVEAL`; the current implementation does neither in ordinary rounds.

```text
score: 0.84
confidence: high
critical_issues: 0
major_issues: 1
minor_issues: 0
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true
```