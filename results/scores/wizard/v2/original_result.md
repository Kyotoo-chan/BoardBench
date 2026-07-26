# wizard — result profile

> Technically executable; 22/23 configured clear-basis and 9/11 human-decision-basis scenarios passed; all configured scenarios evaluated.

## Identity

- Condition: original_v2_successor
- Format: pdf
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
| Clear-basis scenarios | 0.957 | n/a |
| Human-decision-basis scenarios | 0.818 | n/a |
| Scenario evaluated coverage | 1.000 | n/a |
| Neutral judges | 0.740 | 0.035 |

Scenario rows are pass rates over evaluated scenarios, not complete rule-fact coverage. Coverage measures only whether configured scenarios reached an evaluated outcome.

## Assumptions

- Structured material declarations: 3

## Efficiency per run

| Measure | Mean | Sample SD |
|---|---:|---:|
| calls | 4.000 | n/a |
| provider_seconds | 892.778 | n/a |
| input_tokens | 1174314.000 | n/a |
| cached_input_tokens | 968192.000 | n/a |
| output_tokens | 26421.000 | n/a |
| reasoning_tokens | 10215.000 | n/a |
| api_equivalent_usd | 2.307 | n/a |
| code_lines | 331.000 | n/a |

Sample SD measures variation across repeated runs; `n/a` means only one run is available.
The USD value is an API-equivalent estimate for gpt-5.6-sol from the recorded tokens and versioned public list price; actual Codex OAuth subscription cost is unavailable.
Persona reviews and raw per-run evidence remain in `result.json`.
