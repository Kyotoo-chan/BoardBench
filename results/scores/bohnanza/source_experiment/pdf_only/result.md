# bohnanza — result profile

> Three frozen runs; evidence groups remain separate and are compared cross-condition.

## Identity

- Condition: pdf_only
- Format: pdf
- SHA-256: `11150c4cdc6aec22655f89a317ad4aa235f751a4e64baad967ce16995723731d`
- Source RULES (publisher_rulebook): `11150c4cdc6aec22655f89a317ad4aa235f751a4e64baad967ce16995723731d`
- Runs: 3
- Generation: gpt-5.6-sol · thinking low
- Neutral judges: gpt-5.6-sol · thinking medium
- Response verbosity: low

## Evidence

| Group | Mean | Sample SD |
|---|---:|---:|
| Robustness | 1.000 | 0.000 |
| Interface | 1.000 | 0.000 |
| Clear rules | 0.269 | 0.259 |
| Human decisions | 0.362 | 0.405 |
| Coverage | 0.784 | 0.097 |
| Neutral judges | 0.214 | 0.034 |

## Assumptions

- Structured material declarations: 7

## Efficiency per run

| Measure | Mean | Sample SD |
|---|---:|---:|
| calls | 4.000 | 0.000 |
| provider_seconds | 860.294 | 59.335 |
| input_tokens | 573999.667 | 98002.572 |
| cached_input_tokens | 443989.333 | 83454.560 |
| output_tokens | 26898.000 | 949.788 |
| reasoning_tokens | 12164.000 | 145.588 |
| api_equivalent_usd | 1.679 | 0.187 |
| code_lines | 242.000 | 71.757 |

Sample SD measures variation across repeated runs; `n/a` means only one run is available.
The USD value is an API-equivalent estimate for gpt-5.6-sol from the recorded tokens and versioned public list price; actual Codex OAuth subscription cost is unavailable.
Persona reviews and raw per-run evidence remain in `result.json`.
