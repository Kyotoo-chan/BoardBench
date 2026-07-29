# Bohnanza Base Game 2023 — result profile

> Exact retained repeat: technical gate 4/4; robustness 100/100; 30/38 clear-basis and 2/4 human-decision-basis scenarios passed; all 42 scenarios evaluated.

## Identity

- Condition: v2_clear_rule_emphasis_2
- Format: pdf+clear-rule-emphasis
- SHA-256: `e59f7a7d77ed2f052cdf46403b797a1d418996664dc1e3ae9baf7e498b727655`
- Runs: 1
- Generation: gpt-5.6-sol · thinking low
- Neutral judges: gpt-5.6-sol · thinking medium
- Response verbosity: low

## Evidence

| Group | Mean | Sample SD |
|---|---:|---:|
| Robustness | 1.000 | n/a |
| Interface | 1.000 | n/a |
| Clear-basis scenarios | 0.789 | n/a |
| Human-decision-basis scenarios | 0.500 | n/a |
| Scenario evaluated coverage | 1.000 | n/a |
| Neutral judges | 0.423 | 0.038 |

Scenario rows are pass rates over evaluated scenarios, not complete rule-fact coverage. Coverage measures only whether configured scenarios reached an evaluated outcome.

## Assumptions

- Structured material declarations: 3

## Efficiency per run

| Measure | Mean | Sample SD |
|---|---:|---:|
| calls | 4.000 | n/a |
| provider_seconds | 1365.451 | n/a |
| input_tokens | 1564559.000 | n/a |
| cached_input_tokens | 1347840.000 | n/a |
| output_tokens | 40287.000 | n/a |
| reasoning_tokens | 17985.000 | n/a |
| api_equivalent_usd | 2.966 | n/a |
| code_lines | 417.000 | n/a |

Sample SD measures variation across repeated runs; `n/a` means only one run is available.
The USD value is an API-equivalent estimate for gpt-5.6-sol from the recorded tokens and versioned public list price; actual Codex OAuth subscription cost is unavailable.
Persona reviews and raw per-run evidence remain in `result.json`.
