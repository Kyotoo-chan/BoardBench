# CATAN 2022 — result profile

> Original: technical gate 4/4; robustness 100/100; 37/40 clear-basis and 8/11 human-decision-basis scenarios passed; all 51 scenarios and 107 named cases evaluated under rubric r2.

## Identity

- Condition: v2_original_1
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
| Clear-basis scenarios | 0.925 | n/a |
| Human-decision-basis scenarios | 0.727 | n/a |
| Scenario evaluated coverage | 1.000 | n/a |
| Neutral judges | 0.630 | 0.026 |

Scenario rows are pass rates over evaluated scenarios, not complete rule-fact coverage. Coverage measures only whether configured scenarios reached an evaluated outcome.

## Assumptions

- Structured material declarations: 3

## Efficiency per run

| Measure | Mean | Sample SD |
|---|---:|---:|
| calls | 4.000 | n/a |
| provider_seconds | 1608.645 | n/a |
| input_tokens | 3221461.000 | n/a |
| cached_input_tokens | 2659584.000 | n/a |
| output_tokens | 45756.000 | n/a |
| reasoning_tokens | 22224.000 | n/a |
| api_equivalent_usd | 5.512 | n/a |
| code_lines | 370.000 | n/a |

Sample SD measures variation across repeated runs; `n/a` means only one run is available.
The USD value is an API-equivalent estimate for gpt-5.6-sol from the recorded tokens and versioned public list price; actual Codex OAuth subscription cost is unavailable.
Persona reviews and raw per-run evidence remain in `result.json`.
