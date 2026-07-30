# CATAN 2022 — result profile

> Clear emphasis: 38/40 clear-basis and 13/15 human-decision-basis scenarios; valid rendered-PDF Judges 0.80/0.89/0.76.

## Identity

- Condition: v2_clear_rule_emphasis_1
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
| Clear-basis scenarios | 0.950 | n/a |
| Human-decision-basis scenarios | 0.867 | n/a |
| Scenario evaluated coverage | 1.000 | n/a |
| Neutral judges | 0.817 | 0.067 |

Scenario rows are pass rates over evaluated scenarios, not complete rule-fact coverage. Coverage measures only whether configured scenarios reached an evaluated outcome.

## Assumptions

- Structured material declarations: 3

## Efficiency per run

| Measure | Mean | Sample SD |
|---|---:|---:|
| calls | 4.000 | n/a |
| provider_seconds | 1889.374 | n/a |
| input_tokens | 2949963.000 | n/a |
| cached_input_tokens | 2301952.000 | n/a |
| output_tokens | 39937.000 | n/a |
| reasoning_tokens | 18186.000 | n/a |
| api_equivalent_usd | 5.589 | n/a |
| code_lines | 639.000 | n/a |

Sample SD measures variation across repeated runs; `n/a` means only one run is available.
The USD value is an API-equivalent estimate for gpt-5.6-sol from the recorded tokens and versioned public list price; actual Codex OAuth subscription cost is unavailable.
Persona reviews and raw per-run evidence remain in `result.json`.
