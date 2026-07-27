# Exploding Kittens — result profile

> Technical gate 4/4; robustness 100/100; 33/34 configured clear-basis and 4/4 human-decision-basis scenarios passed; all 38 scenarios evaluated.

## Identity

- Condition: v2_clarified_1
- Format: pdf+experimenter_clarification
- SHA-256: `f15c85be6345ff0101d01059509bc07e4989896f4f1927ace4248bba4ce1e853`
- Runs: 1
- Generation: gpt-5.6-sol · thinking low
- Neutral judges: gpt-5.6-sol · thinking medium
- Response verbosity: low

## Evidence

| Group | Mean | Sample SD |
|---|---:|---:|
| Robustness | 1.000 | n/a |
| Interface | 1.000 | n/a |
| Clear-basis scenarios | 0.971 | n/a |
| Human-decision-basis scenarios | 1.000 | n/a |
| Scenario evaluated coverage | 1.000 | n/a |
| Neutral judges | 0.907 | 0.012 |

Scenario rows are pass rates over evaluated scenarios, not complete rule-fact coverage. Coverage measures only whether configured scenarios reached an evaluated outcome.

## Assumptions

- Structured material declarations: 3

## Efficiency per run

| Measure | Mean | Sample SD |
|---|---:|---:|
| calls | 5.000 | n/a |
| provider_seconds | 856.884 | n/a |
| input_tokens | 1857484.000 | n/a |
| cached_input_tokens | 1587712.000 | n/a |
| output_tokens | 31738.000 | n/a |
| reasoning_tokens | 12726.000 | n/a |
| api_equivalent_usd | 3.095 | n/a |
| code_lines | 486.000 | n/a |

Sample SD measures variation across repeated runs; `n/a` means only one run is available.
The USD value is an API-equivalent estimate for gpt-5.6-sol from the recorded tokens and versioned public list price; actual Codex OAuth subscription cost is unavailable.
Persona reviews and raw per-run evidence remain in `result.json`.
