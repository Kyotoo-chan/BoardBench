# Bohnanza Base Game 2023 V2 — source-delivery comparison

## Conditions

1. **Original:** unchanged publisher PDF only.
2. **Clear-rule emphasis 1:** four already-clear Original defect groups repeated.
3. **Clear-rule emphasis 2:** exact retained repeat of condition 2.
4. **Structured clarification 1:** adapted successor with four approved digital decisions and a balanced whole-game checklist.
5. **Structured clarification 2:** exact pre-registered fresh replication of condition 4.
6. **Structured clarification 3:** final pre-registered exact fresh replication of condition 4.

All runs remain reported; there is no best-of selection. The three structured generations have byte-identical initial model packets, model/thinking, prompt, contract, profile and scenario content.

| Evidence | Original | Emphasis 1 | Emphasis 2 | Structured 1 | Structured 2 | Structured 3 |
|---|---:|---:|---:|---:|---:|---:|
| Agentic gate | PASS | PASS | PASS | PASS | PASS, 1 repair | PASS |
| Technical checks 01–04 | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 |
| Random rollouts | 100/100 | 100/100 | 100/100 | 100/100 | 100/100 | 100/100 |
| Action-language | 800,371/800,371 | 1,523,314/1,523,314 | 976,727/976,727 | 847,456/847,456 | 1,395,514/1,395,514 | 563,753/563,753 |
| Player-count probes | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| Scenario PASS / FAIL / CRASH | 37/5/0 | 33/9/0 | 32/10/0 | 36/6/0 | 38/3/1 | 36/6/0 |
| Clear-basis scenarios | 33/38 | 30/38 | 30/38 | 33/38 | **35/38** | 33/38 |
| Human-decision-basis | **4/4** | 3/4 | 2/4 | 3/4 | 3/4 | 3/4 |
| Scenario evaluated coverage | 42/42 | 42/42 | 42/42 | 42/42 | 42/42 | 42/42 |
| Clear claim mapping | 80/81 + 1 exception | same | same | same | same | same |
| Neutral Judges, mean (SD) | 0.643 (0.081) | not run | 0.423 (0.038) | **0.713 (0.031)** | 0.523 (0.046) | 0.617 (0.006) |

Evidence groups are not combined into one correctness score.

## Original versus the exact structured replications

- **Original:** 33/38 Clear, 4/4 Human Decision, Judge mean 0.643.
- **Structured 1:** 33/38 Clear, 3/4 Human Decision, Judge mean 0.713.
- **Structured 2:** 35/38 Clear, 3/4 Human Decision, Judge mean 0.523, plus one severe bounded-play crash.
- **Structured 3:** 33/38 Clear, 3/4 Human Decision, Judge mean 0.617, no crash.

Structured 3 reproduces Structured 1's exact scored defect set: `R10`, `R16`, `R17`, `R22`, `R23`, and `R24`. It avoids Structured 2's exponential action-space crash but again omits multi-card trade proposals and free staged-card ordering. Its explicit material assumption chooses one-card offers despite the supplement requiring any positive number of traded cards.

## Evaluator compatibility record

Structured 2's unchanged full-suite process exceeded 1,800 seconds and froze the host at `R04`. The implementation remained frozen. Resource-isolated execution invokes every unchanged scenario through `run_scenario_v4` in a separate below-normal-priority, one-CPU process with a 15-second timeout. Structured 3 used this documented evaluator mode from the beginning; all 42 scenarios completed and `R04` passed in 0.20 seconds.

## Conclusion

No structured run dominates all evidence groups. Structured 2 has the most Clear passes but also the only crash and lowest structured Judge signal. Structured 1 has the strongest Judge signal. Structured 3 avoids the crash but returns to Structured 1's scenario defects, with an intermediate Judge mean.

Across three exact structured generations, Clear results are 33/38, 35/38, and 33/38; Human Decision is 3/4 every time. This is descriptive evidence of generation variance and metric-specific trade-offs, not a causal estimate or a reason to retain only the best-looking run.
