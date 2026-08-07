# Bohnanza Base Game 2023 V2 — source-delivery comparison

## Conditions

1. **Original:** unchanged publisher PDF only.
2. **Clear-rule emphasis 1:** four already-clear Original defect groups repeated.
3. **Clear-rule emphasis 2:** exact retained repeat of condition 2.
4. **Structured clarification 1:** adapted successor with four approved digital decisions and a balanced whole-game checklist.
5. **Structured clarification 2:** exact pre-registered fresh replication of condition 4.

All prior runs remain reported; there is no best-of selection. The two structured runs have byte-identical initial model packets, model/thinking, prompt, contract, profile and frozen scenario content.

| Evidence | Original | Emphasis 1 | Emphasis 2 | Structured 1 | Structured 2 |
|---|---:|---:|---:|---:|---:|
| Agentic gate | PASS | PASS | PASS | PASS | PASS, 1 repair |
| Technical checks 01–04 | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 |
| Random rollouts | 100/100 | 100/100 | 100/100 | 100/100 | 100/100 |
| Action-language | 800,371/800,371 | 1,523,314/1,523,314 | 976,727/976,727 | 847,456/847,456 | 1,395,514/1,395,514 |
| Player-count probes | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| Scenario PASS / FAIL / CRASH | 37/5/0 | 33/9/0 | 32/10/0 | 36/6/0 | 38/3/1 |
| Clear-basis scenarios | 33/38 | 30/38 | 30/38 | 33/38 | **35/38** |
| Human-decision-basis | 4/4 | 3/4 | 2/4 | 3/4 | 3/4 |
| Scenario evaluated coverage | 42/42 | 42/42 | 42/42 | 42/42 | 42/42 |
| Clear claim mapping | 80/81 + 1 exception | same | same | same | same |
| Neutral Judges, mean (SD) | 0.643 (0.081) | not run | 0.423 (0.038) | **0.713 (0.031)** | 0.523 (0.046) |

Evidence groups are not combined into one correctness score.

## Original versus the exact structured replications

- **Original:** 33/38 Clear, 4/4 Human Decision, Judge mean 0.643.
- **Structured 1:** 33/38 Clear, 3/4 Human Decision, Judge mean 0.713.
- **Structured 2:** 35/38 Clear, 3/4 Human Decision, Judge mean 0.523, plus one severe bounded-play crash.

Structured 2 fixes replicate 1's missing multi-card trade and staged-card-order scenarios. It retains `R10`, newly fails `R14`, again fails human-decision `R23`, and makes `R04` computationally intractable through exponential trade-action enumeration.

## Evaluator compatibility record

The unchanged full-suite process exceeded 1,800 seconds and froze the host at `R04`. The implementation remained frozen. A documented compatibility replay executed each unchanged scenario through `run_scenario_v4` in a separate below-normal-priority, one-CPU process with a 15-second timeout. Original and structured 1 pass R04 in 0.17/0.30 seconds; structured 2 times out and is scored CRASH. The first low-thinking judge invocation and a legacy-contract technical invocation are retained but unscored; official judges use the frozen medium setting.

## Conclusion

The second run is not systematically worse or “cooked.” Under an identical packet it improves the covered Clear scenario rate from 33/38 to 35/38, while producing a severe performance defect and a lower Judge signal. The two exact structured runs therefore demonstrate generation variance and metric-specific trade-offs, not a stable monotonic improvement. At `n=2`, the comparison remains descriptive and supports no causal claim.
