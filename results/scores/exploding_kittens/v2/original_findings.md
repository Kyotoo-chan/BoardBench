# Exploding Kittens V2.2 original-condition findings

- Agentic gate: PASS (`v2_original_2`, one generation call, no repairs).
- Technical gate 01–04: 4/4 PASS.
- Runtime robustness: 98/100; three reproduced stalls entered `favor_give` after Favor targeted an empty hand.
- Interface: 12,436/12,436 action-name roundtrips PASS.
- Player counts: 2, 3, 4, 5 playable; 1 and 6 rejected (6/6).
- Clear-basis scenarios: 32/34.
- Human-decision-basis scenarios: 3/4.
- Evaluated coverage: 38/38; clear claim mapping/evaluation 65/65.
- Neutral Judges: 0.80 / 0.82 / 0.82; mean 0.813, sample SD 0.012.

Confirmed defects:

1. `EXPL-R11` and `EXPL-R12` expose one clear-rule defect: an exploding player is eliminated and the Kitten is discarded, but the player’s remaining hand is neither emptied nor moved to discard. The PDF explicitly requires all remaining cards and the Kitten to enter discard.
2. `EXPL-R27` exposes one approved human-decision deviation: Favor and Pair can target an empty hand. Favor then enters a nonterminal `favor_give` phase with no legal action, causing the robustness failures.

All three neutral Judges independently identify both defects. The empty-target behavior is tied to a genuine source underspecification resolved only in evaluator decisions; the elimination-discard behavior contradicts clear publisher text and is not a source-gap clarification target.
