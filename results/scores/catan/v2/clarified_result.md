# CATAN 2022 — result profile

> Source-gap clarification: 32/40 clear-basis and 11/15 human-decision-basis scenarios; valid rendered-PDF Judges 0.85/0.78/0.84.

## Identity

- Condition: v2_clarified_1
- Format: pdf+matching-publisher-companion
- SHA-256: `e0673fa93040f5b43908b215f52573878f586d26827d3a4f07c2ef8f8a947cf3`
- Runs: 1
- Generation: gpt-5.6-sol · thinking low
- Neutral judges: gpt-5.6-sol · thinking medium
- Response verbosity: low

## Evidence

| Group | Mean | Sample SD |
|---|---:|---:|
| Robustness | 1.000 | n/a |
| Interface | 1.000 | n/a |
| Clear-basis scenarios | 0.800 | n/a |
| Human-decision-basis scenarios | 0.733 | n/a |
| Scenario evaluated coverage | 1.000 | n/a |
| Neutral judges | 0.823 | 0.038 |

Scenario rows are pass rates over evaluated scenarios, not complete rule-fact coverage. Coverage measures only whether configured scenarios reached an evaluated outcome.

## Assumptions

- Structured material declarations: 0

## Efficiency per run

| Measure | Mean | Sample SD |
|---|---:|---:|
| calls | 4.000 | n/a |
| provider_seconds | 2055.594 | n/a |
| input_tokens | 3551441.000 | n/a |
| cached_input_tokens | 2854144.000 | n/a |
| output_tokens | 40131.000 | n/a |
| reasoning_tokens | 20256.000 | n/a |
| api_equivalent_usd | 6.117 | n/a |
| code_lines | 489.000 | n/a |

Sample SD measures variation across repeated runs; `n/a` means only one run is available.
The USD value is an API-equivalent estimate for gpt-5.6-sol from the recorded tokens and versioned public list price; actual Codex OAuth subscription cost is unavailable.
Persona reviews and raw per-run evidence remain in `result.json`.
