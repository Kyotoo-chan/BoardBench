# Abalone — result profile

> Compatibility replay under v3: 32/33 configured clear-basis and 4/4 human-decision-basis scenarios passed; the unspecified no-move case is not scored.

## Identity

- Condition: v2_original_1 compatibility replay under evaluator v3
- Format: pdf
- SHA-256: `c293ed5d319ccb4fa5725921613f4a05ba2453074d2b2dcdc11cdeb9f8570550`
- Source ABALONE-RULES-SCHMIDT-4P (publisher_rulebook): `c293ed5d319ccb4fa5725921613f4a05ba2453074d2b2dcdc11cdeb9f8570550`
- Runs: 1
- Generation: gpt-5.6-sol · thinking low
- Neutral judges: gpt-5.6-sol · thinking medium
- Response verbosity: low

## Evidence

| Group | Mean | Sample SD |
|---|---:|---:|
| Robustness | 1.000 | n/a |
| Interface | 1.000 | n/a |
| Clear-basis scenarios | 0.970 | n/a |
| Human-decision-basis scenarios | 1.000 | n/a |
| Scenario evaluated coverage | 1.000 | n/a |
| Neutral judges | 0.867 | 0.031 |

Scenario rows are pass rates over evaluated scenarios, not complete rule-fact coverage. Coverage measures only whether configured scenarios reached an evaluated outcome.

## Assumptions

- Structured material declarations: 2

## Efficiency per run

| Measure | Mean | Sample SD |
|---|---:|---:|
| calls | 4.000 | n/a |
| provider_seconds | 688.769 | n/a |
| input_tokens | 1101308.000 | n/a |
| cached_input_tokens | 910336.000 | n/a |
| output_tokens | 21546.000 | n/a |
| reasoning_tokens | 9444.000 | n/a |
| api_equivalent_usd | 2.056 | n/a |
| code_lines | 245.000 | n/a |

Sample SD measures variation across repeated runs; `n/a` means only one run is available.
The USD value is an API-equivalent estimate for gpt-5.6-sol from the recorded tokens and versioned public list price; actual Codex OAuth subscription cost is unavailable.
