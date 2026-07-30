# CATAN 2022 — result profile

> Clear-rule emphasis: technical 4/4; robustness 100/100; 38/40 clear and 13/15 human-decision scenarios passed under r3.

## Identity

- Condition: v2_clear_rule_emphasis_1
- Format: pdf+matching-companion+clear-rule-emphasis
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
| Clear-basis scenarios | 0.950 | n/a |
| Human-decision-basis scenarios | 0.867 | n/a |
| Scenario evaluated coverage | 1.000 | n/a |
| Neutral judges | 0.757 | 0.064 |

Scenario rows are pass rates over evaluated scenarios, not complete rule-fact coverage. Coverage measures only whether configured scenarios reached an evaluated outcome.

## Assumptions

- Structured material declarations: 3

## Efficiency per run

| Measure | Mean | Sample SD |
|---|---:|---:|
| calls | 4.000 | n/a |
| provider_seconds | 1504.871 | n/a |
| input_tokens | 2192721.000 | n/a |
| cached_input_tokens | 1820160.000 | n/a |
| output_tokens | 32180.000 | n/a |
| reasoning_tokens | 9236.000 | n/a |
| api_equivalent_usd | 3.738 | n/a |
| code_lines | 639.000 | n/a |

Sample SD measures variation across repeated runs; `n/a` means only one run is available.
The USD value is an API-equivalent estimate for gpt-5.6-sol from the recorded tokens and versioned public list price; actual Codex OAuth subscription cost is unavailable.
Persona reviews and raw per-run evidence remain in `result.json`.
