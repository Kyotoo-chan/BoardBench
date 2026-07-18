# bohnanza — result profile

> Three frozen runs; evidence groups remain separate and are compared cross-condition.

## Identity

- Condition: json_mutated
- Format: pdf+json
- SHA-256: `11150c4cdc6aec22655f89a317ad4aa235f751a4e64baad967ce16995723731d`
- Source RULES (publisher_rulebook): `11150c4cdc6aec22655f89a317ad4aa235f751a4e64baad967ce16995723731d`
- Source COMPONENTS (user_observation): `1d1c5614c689a39a4019057673c1cad77c8ad2dc564dc2c5b4f7bb08c8ae721a`
- Runs: 3
- Generation: gpt-5.6-sol · thinking low
- Neutral judges: gpt-5.6-sol · thinking medium
- Response verbosity: low

## Evidence

| Group | Mean | Sample SD |
|---|---:|---:|
| Robustness | 0.877 | 0.214 |
| Interface | 1.000 | 0.000 |
| Clear rules | 0.056 | 0.096 |
| Human decisions | 0.000 | 0.000 |
| Coverage | 0.495 | 0.250 |
| Neutral judges | 0.352 | 0.118 |

## Assumptions

- Structured material declarations: 10

## Efficiency per run

| Measure | Mean | Sample SD |
|---|---:|---:|
| calls | 4.000 | 0.000 |
| provider_seconds | 983.331 | 46.476 |
| input_tokens | 674921.667 | 58516.357 |
| cached_input_tokens | 527104.000 | 78484.356 |
| output_tokens | 29260.667 | 178.584 |
| reasoning_tokens | 12759.667 | 647.631 |
| api_equivalent_usd | 1.880 | 0.072 |
| code_lines | 282.000 | 11.136 |

Sample SD measures variation across repeated runs; `n/a` means only one run is available.
The USD value is an API-equivalent estimate for gpt-5.6-sol from the recorded tokens and versioned public list price; actual Codex OAuth subscription cost is unavailable.
Persona reviews and raw per-run evidence remain in `result.json`.
