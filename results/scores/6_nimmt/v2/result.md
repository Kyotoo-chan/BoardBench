# 6 nimmt! Version 2.3 — result profile

> Technically executable; all 24 clear-basis and 9 human-decision-basis configured scenarios pass, while Judges and an unscored deterministic replay identify a joint-reveal information defect.

## Identity

- Condition: v2_original_augmented_1 under evaluator r2
- Format: publisher-pdf+user-observation
- SHA-256: `b200ae0558c283ba86f331037402d9150675958ac6a6dc3e5df188435626539d`
- Source 6NIMMT-V23-RULES (publisher_rulebook): `b200ae0558c283ba86f331037402d9150675958ac6a6dc3e5df188435626539d`
- Source 6NIMMT-V2-COMPONENTS (user_observation): `01e8f5dbe0cdca5ea514e628da3e5ed71ceb17729bbd22ac3a309c44cb2da950`
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
| Human-decision-basis scenarios | 1.000 | n/a |
| Scenario evaluated coverage | 1.000 | n/a |
| Neutral judges | 0.847 | 0.031 |

Scenario rows are pass rates over evaluated scenarios, not complete rule-fact coverage. Coverage measures only whether configured scenarios reached an evaluated outcome.

## Assumptions

- Structured material declarations: 4

## Efficiency per run

| Measure | Mean | Sample SD |
|---|---:|---:|
| calls | 9.000 | n/a |
| provider_seconds | 1791.648 | n/a |
| input_tokens | 2561820.000 | n/a |
| cached_input_tokens | 2115840.000 | n/a |
| output_tokens | 56099.000 | n/a |
| reasoning_tokens | 21455.000 | n/a |
| api_equivalent_usd | 4.971 | n/a |
| code_lines | 377.000 | n/a |

Sample SD measures variation across repeated runs; `n/a` means only one run is available.
The USD value is an API-equivalent estimate for gpt-5.6-sol from the recorded tokens and versioned public list price; actual Codex OAuth subscription cost is unavailable.
Persona reviews and raw per-run evidence remain in `result.json`.
