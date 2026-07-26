# abalone — result profile

> Technically executable; 33/33 configured clear-basis and 4/5 human-decision-basis scenarios passed; all configured scenarios evaluated.

## Identity

- Condition: setup_emphasis_v2
- Format: pdf+clear-rule-emphasis
- SHA-256: `c293ed5d319ccb4fa5725921613f4a05ba2453074d2b2dcdc11cdeb9f8570550`
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
| Neutral judges | 0.893 | 0.081 |

Scenario rows are pass rates over evaluated scenarios, not complete rule-fact coverage. Coverage measures only whether configured scenarios reached an evaluated outcome.

## Assumptions

- Structured material declarations: 2

## Efficiency per run

| Measure | Mean | Sample SD |
|---|---:|---:|
| calls | 4.000 | n/a |
| provider_seconds | 662.597 | n/a |
| input_tokens | 944830.000 | n/a |
| cached_input_tokens | 747264.000 | n/a |
| output_tokens | 21111.000 | n/a |
| reasoning_tokens | 8197.000 | n/a |
| api_equivalent_usd | 1.995 | n/a |
| code_lines | 344.000 | n/a |

Sample SD measures variation across repeated runs; `n/a` means only one run is available.
The USD value is an API-equivalent estimate for gpt-5.6-sol from the recorded tokens and versioned public list price; actual Codex OAuth subscription cost is unavailable.
Persona reviews and raw per-run evidence remain in `result.json`.
