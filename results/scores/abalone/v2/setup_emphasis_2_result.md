# Abalone — result profile

> Exact setup-emphasis replicate: 33/33 configured clear-basis and 4/5 human-decision-basis scenarios pass; the forced-pass regression recurs and a post-judge replay confirms unscored action aliases.

## Identity

- Condition: v2_setup_emphasis_2 exact replicate
- Format: publisher-pdf+clear-rule-emphasis
- SHA-256: `c293ed5d319ccb4fa5725921613f4a05ba2453074d2b2dcdc11cdeb9f8570550`
- Source ABALONE-RULES-SCHMIDT-4P (publisher_rulebook): `c293ed5d319ccb4fa5725921613f4a05ba2453074d2b2dcdc11cdeb9f8570550`
- Source ABALONE-V2-SETUP-EMPHASIS (experimenter_clarification): `b3a6809451c3088aadcae57b4fa48c78e733ea80846f1b94d57b0f84cd33c20a`
- Runs: 1
- Generation: gpt-5.6-sol · thinking low
- Neutral judges: gpt-5.6-sol · thinking medium
- Response verbosity: low

## Evidence

| Group | Mean | Sample SD |
|---|---:|---:|
| Robustness | 1.000 | n/a |
| Interface | 1.000 | n/a |
| Clear-basis scenarios | 1.000 | n/a |
| Human-decision-basis scenarios | 0.800 | n/a |
| Scenario evaluated coverage | 1.000 | n/a |
| Neutral judges | 0.870 | 0.030 |

Scenario rows are pass rates over evaluated scenarios, not complete rule-fact coverage. Coverage measures only whether configured scenarios reached an evaluated outcome.

## Assumptions

- Structured material declarations: 3

## Efficiency per run

| Measure | Mean | Sample SD |
|---|---:|---:|
| calls | 4.000 | n/a |
| provider_seconds | 683.444 | n/a |
| input_tokens | 931202.000 | n/a |
| cached_input_tokens | 744192.000 | n/a |
| output_tokens | 25237.000 | n/a |
| reasoning_tokens | 10565.000 | n/a |
| api_equivalent_usd | 2.064 | n/a |
| code_lines | 330.000 | n/a |

Sample SD measures variation across repeated runs; `n/a` means only one run is available.
The USD value is an API-equivalent estimate for gpt-5.6-sol from the recorded tokens and versioned public list price; actual Codex OAuth subscription cost is unavailable.
Persona reviews and raw per-run evidence remain in `result.json`.
