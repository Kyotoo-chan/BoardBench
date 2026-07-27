# Exploding Kittens V2 — Original versus targeted clarification

## Design

The eligible Original run received only the complete two-page German NSFW Edition 2018 PDF. After full evaluation, a fresh Clarified run received the byte-identical PDF plus one separately attributed decision: Favor and Pair may target only living opponents with at least one card. The clear publisher rule about discarding an eliminated player's hand was deliberately not included in the clarification.

## Evidence groups

| Evidence | Original | Targeted clarification |
|---|---:|---:|
| Agentic gate | PASS | PASS (1 pre-evaluation repair) |
| Technical checks 01–04 | 4/4 | 4/4 |
| Random rollouts | 98/100 | 100/100 |
| Action-language | 12,436/12,436 | 15,589/15,589 |
| Player-count probes | 6/6 | 6/6 |
| Clear-basis scenarios | 32/34 | 33/34 |
| Human-decision-basis scenarios | 3/4 | 4/4 |
| Scenario evaluated coverage | 38/38 | 38/38 |
| Clear claim mapping/evaluation | 65/65 | 65/65 |
| Neutral Judges | 0.813 (SD 0.012) | 0.907 (SD 0.012) |

These groups are not combined into one correctness score.

## Change

- `EXPL-R27` changes from FAIL to PASS: the clarified implementation rejects empty-hand Favor and Pair targets.
- Random rollout deadlocks disappear because Favor no longer enters an impossible `favor_give` phase against an empty hand.
- `EXPL-R11` and `EXPL-R12` change from FAIL to PASS: eliminated hands are now discarded. This is a clear-rule improvement in a fresh generation, not an attributable clarification effect.
- `EXPL-R18` changes from PASS to FAIL: chained Attack assigns three turns instead of exactly two. This is a new clear-rule regression.

The targeted source-gap intervention therefore fixes its intended behavior and associated runtime failure, while fresh-run variance introduces a separate clear-rule defect. With one implementation per condition, only the targeted `R27` change is directly aligned with the intervention; the other changes must not be presented as causal.
