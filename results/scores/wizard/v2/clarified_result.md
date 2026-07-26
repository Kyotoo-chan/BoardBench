# wizard — result profile

> Technically executable; 23/23 configured clear-basis and 10/11 human-decision-basis scenarios passed; all configured scenarios evaluated.

## Identity

- Condition: clarified_v2_successor
- Format: pdf+experimenter_clarification
- SHA-256: `167254a64b0866266746833c0b98836db51c08171b5b96e25f7461d5bf3dee79`
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
| Human-decision-basis scenarios | 0.909 | n/a |
| Scenario evaluated coverage | 1.000 | n/a |
| Neutral judges | 0.897 | 0.015 |

Scenario rows are pass rates over evaluated scenarios, not complete rule-fact coverage. Coverage measures only whether configured scenarios reached an evaluated outcome.

## Assumptions

- Structured material declarations: 2

## Efficiency per run

| Measure | Mean | Sample SD |
|---|---:|---:|
| calls | 4.000 | n/a |
| provider_seconds | 904.204 | n/a |
| input_tokens | 1326930.000 | n/a |
| cached_input_tokens | 1132800.000 | n/a |
| output_tokens | 29168.000 | n/a |
| reasoning_tokens | 13446.000 | n/a |
| api_equivalent_usd | 2.412 | n/a |
| code_lines | 477.000 | n/a |

Sample SD measures variation across repeated runs; `n/a` means only one run is available.
The USD value is an API-equivalent estimate for gpt-5.6-sol from the recorded tokens and versioned public list price; actual Codex OAuth subscription cost is unavailable.
Persona reviews and raw per-run evidence remain in `result.json`.
