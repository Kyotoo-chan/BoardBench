# Bohnanza Base Game 2023 — result profile

> Adapted structured clarification: technical gate 4/4; robustness 100/100; 33/38 clear-basis and 3/4 human-decision-basis scenarios passed; all 42 scenarios evaluated.

## Identity

- Condition: v2_structured_clarification_1
- Format: pdf+structured-clarification-and-fidelity-guide
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
| Clear-basis scenarios | 0.868 | n/a |
| Human-decision-basis scenarios | 0.750 | n/a |
| Scenario evaluated coverage | 1.000 | n/a |
| Neutral judges | 0.713 | 0.031 |

Scenario rows are pass rates over evaluated scenarios, not complete rule-fact coverage. Coverage measures only whether configured scenarios reached an evaluated outcome.

## Assumptions

- Structured material declarations: 4

## Efficiency per run

| Measure | Mean | Sample SD |
|---|---:|---:|
| calls | 4.000 | n/a |
| provider_seconds | 1193.280 | n/a |
| input_tokens | 1529790.000 | n/a |
| cached_input_tokens | 1296640.000 | n/a |
| output_tokens | 39841.000 | n/a |
| reasoning_tokens | 21154.000 | n/a |
| api_equivalent_usd | 3.009 | n/a |
| code_lines | 385.000 | n/a |

Sample SD measures variation across repeated runs; `n/a` means only one run is available.
The USD value is an API-equivalent estimate for gpt-5.6-sol from the recorded tokens and versioned public list price; actual Codex OAuth subscription cost is unavailable.
Persona reviews and raw per-run evidence remain in `result.json`.
