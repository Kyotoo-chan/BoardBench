# Bohnanza Base 2023 — replacement comparison v4

## Design

Both prior current-condition runs were replaced by fresh isolated generations. Git retains the earlier experiment. The original condition received only the publisher PDF; the clarified condition received the byte-identical PDF plus the unchanged four-item `clarifications.json`. Model, thinking, prompt, Contract-v2 profile, technical checks, 41-scenario v4 rubric, and three-neutral-Judge protocol were held constant.

The proposed rarity-based trade-fairness heuristic was **not** enforced and was not supplied to either implementation. It is strategy, not a publisher gameplay rule.

## Evidence groups

| Evidence | Original PDF only | PDF + clarification |
|---|---:|---:|
| Technical checks 01–04 | 4/4 | 4/4 |
| Random rollouts | 100/100 | 100/100 |
| Action-language check | 1,473,350/1,473,350 | 1,373,753/1,373,753 |
| Comparison scenarios | 34 PASS / 7 FAIL | 39 PASS / 2 FAIL |
| Scenario coverage | 41/41 | 41/41 |
| Generation repairs | 0 | 0 |
| Neutral Judges | 0.32 mean, SD 0.069, n=3 | 0.60 mean, SD 0.035, n=3 |

Do not combine these groups into one score.

## Differences under the identical rubric

Five expectations changed from failure to pass:

1. immediate termination when the third depletion occurs on the first phase-four draw;
2. the Garden-bean payout curve;
3. immediate termination when the third depletion occurs on the third phase-four draw;
4. phase three advancing to a non-active recipient with their own planting choice;
5. immediate termination when the third depletion occurs on the second phase-four draw.

Both implementations passed the first/second-depletion continuation case and the 1-for-2 and 3-for-1 trade-representability cases. This fresh pair therefore does not show an intervention effect for trade bundle legality, although the clarification still removes the possible 2-for-1-cap interpretation.

## Mandatory final harvest: shared scenario failures

Both new final-harvest cases fail in both conditions:

- `BASE-R45-final-harvest-after-phase4-depletion`
- `BASE-R46-final-harvest-after-phase2-continuation`

The defects differ:

- **Original:** it clears/harvests fields but also converts remaining hand cards into coins and clears the hand. This violates “Die Karten auf der Hand zählen nicht mehr” and can change the winner.
- **Clarified:** it marks the state terminal without harvesting or clearing fields. `returns()` computes hypothetical field values dynamically, so the winner can look correct while the required final harvest never occurs observably.

This is exactly why final harvesting must be tested as a state transition, not inferred only from terminal return values.

## Independent Judge evidence

### Original: mean 0.32, sample SD 0.069, n=3

Scores: 0.28, 0.28, 0.40; all high confidence. Repeated findings include illegal hand-card scoring, exponential trade enumeration, incomplete non-active phase-three planting, unchecked direct actions, and missing harvest opportunities at approved stable boundaries.

### Clarified: mean 0.60, sample SD 0.035, n=3

Scores: 0.56, 0.62, 0.62; all high confidence. All three Judges identify exponential trade enumeration as critical and missing partner-to-active gifts as major. However, all three describe final scoring as correct and miss that fields are never actually harvested. The deterministic transition cases therefore provide evidence the Judges did not.

## Interpretation

The clarified condition improves from 34/41 to 39/41 and has the higher three-Judge mean. It fixes all observed temporal-boundary, Garden-payout, and non-active phase-three differences in this fresh pair. It does **not** solve mandatory final harvesting, and both conditions retain serious action-space or legality concerns.

The defensible conclusion is: clarification again reduces targeted executable-translation errors, while the expanded evaluator exposes a shared terminal-transition gap and an important blind spot in otherwise consistent LLM reviews.
