# Abalone V2 — Original and exact Setup-Emphasis replication

## Design

The Original received only the four-page publisher PDF. Its sole configured failure was the clear Figure-1 setup: 13 instead of 14 marbles per color. Setup-Emphasis replicate 1 received the same PDF plus a separately attributed repetition of that clear setup rule.

Before replicate 2 launched, it was pre-registered as an **exact fresh replication**: identical model-facing packet hashes, model/thinking, prompt, contract, profile and evaluator. Replicate 1 remains reported regardless of replicate 2. This is Clear-Rule Emphasis, not source-gap clarification and not best-of selection.

## Evidence groups

| Evidence | Original PDF | Setup emphasis 1 | Setup emphasis 2 |
|---|---:|---:|---:|
| Generation calls / repairs | 1 / 0 | 1 / 0 | 1 / 0 |
| Technical checks 01–04 | 4/4 | 4/4 | 4/4 |
| Random rollouts | 100/100 | 100/100 | 100/100 |
| Action language | 8,888,062/8,888,062 | 8,528,518/8,528,518 | 5,704,536/5,704,536 |
| Player-count probes | 3/3 | 3/3 | 3/3 |
| Clear-basis scenarios | **32/33** | **33/33** | **33/33** |
| Human-decision-basis scenarios | **5/5** | **4/5** | **4/5** |
| Scenario evaluated coverage | 38/38 | 38/38 | 38/38 |
| Clear claims mapped/evaluated | 33/33 | 33/33 | 33/33 |
| Neutral Judges | 0.86 / 0.90 / 0.84 | 0.80 / 0.93 / 0.95 | 0.90 / 0.87 / 0.84 |
| Judge mean (sample SD) | **0.867** (0.031) | **0.893** (0.081) | **0.870** (0.030) |

These groups are not combined into a total score.

## What replicated

Both setup-emphasis generations:

1. correct `ABAL-R01` to 14 black and 14 white marbles;
2. pass all 33 configured clear-basis scenarios;
3. fail only `ABAL-R19` among the five configured Human Decisions;
4. expose no forced pass when no movement exists.

The recurrence answers the exploratory question descriptively: the first forced-pass regression was not unique to one emphasis generation. It does **not** establish a causal effect at `n=2`, because the approved pass decision was hidden from all model packets and the runs remain stochastic syntheses.

The Original declared and selected a forced-pass assumption. Emphasis replicate 1 omitted that gap and focused its assumptions on setup/Sumito. Replicate 2 explicitly selected an assumption that does not implement passing. The added setup text itself says nothing about pass behavior.

## Judge-only and post-judge evidence

- All three replicate-2 Judges confirm the forced-pass mismatch.
- All three also report parser-created group-order aliases. A deterministic post-judge replay confirms two distinct serialized actions with reversed groups produce the same successor state.
- The frozen `ABAL-R37` scenario still passes because it tests emitted legal-action uniqueness, not parser aliases. The candidate remains unscored and is retained for a future evaluator revision.

## Exact-replicate variation

Across the two setup-emphasis runs, configured scenario scores are identical: Clear 1.000 and Human Decision 0.800 in both, so their run-level sample SD is 0 for these finite suites. The two neutral-Judge run means are 0.893 and 0.870; their mean is 0.882 with run-level sample SD 0.016. With only two generations this is descriptive, not an estimate of expected intervention effect.

## Conclusion

- The setup emphasis reliably corrected the targeted setup in both observed runs.
- The forced-pass Human Decision failed in both observed emphasis runs but passed in the Original.
- No prior run is replaced or hidden.
- The result supports discussing generation variance and attention redistribution, not claiming that clear-rule emphasis causes regressions.
