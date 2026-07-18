# bohnanza — result profile

> Three frozen runs; evidence groups remain separate and are compared cross-condition.

## Identity

- Condition: pdf_mutated
- Format: pdf+json
- SHA-256: `224d2bdd529f6bc712e2ef9e8edfc42a9f53900f7974f535d4c7ca59c4f31b8c`
- Source RULES (publisher_rulebook): `224d2bdd529f6bc712e2ef9e8edfc42a9f53900f7974f535d4c7ca59c4f31b8c`
- Source COMPONENTS (user_observation): `52ff2e99097389173165badc8176b64c35b11c83b8c9d4f0ee854d61e6ee0f46`
- Runs: 3
- Generation: gpt-5.6-sol · thinking low
- Neutral judges: gpt-5.6-sol · thinking medium
- Response verbosity: low

## Evidence

| Group | Mean | Sample SD |
|---|---:|---:|
| Robustness | 1.000 | 0.000 |
| Interface | 1.000 | 0.000 |
| Clear rules | 0.078 | 0.068 |
| Human decisions | 0.000 | 0.000 |
| Coverage | 0.685 | 0.338 |
| Neutral judges | 0.370 | 0.027 |

## Assumptions

- Structured material declarations: 7

## Efficiency per run

| Measure | Mean | Sample SD |
|---|---:|---:|
| calls | 4.000 | 0.000 |
| provider_seconds | 907.172 | 87.751 |
| input_tokens | 586515.667 | 145030.925 |
| cached_input_tokens | 453717.333 | 129105.583 |
| output_tokens | 26414.667 | 858.288 |
| reasoning_tokens | 12322.667 | 844.920 |
| api_equivalent_usd | 1.683 | 0.155 |
| code_lines | 243.000 | 11.358 |

Sample SD measures variation across repeated runs; `n/a` means only one run is available.
The USD value is an API-equivalent estimate for gpt-5.6-sol from the recorded tokens and versioned public list price; actual Codex OAuth subscription cost is unavailable.
Persona reviews and raw per-run evidence remain in `result.json`.
