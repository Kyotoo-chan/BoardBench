# bohnanza — result profile

> Three frozen runs; evidence groups remain separate and are compared cross-condition.

## Identity

- Condition: json_clean
- Format: pdf+json
- SHA-256: `11150c4cdc6aec22655f89a317ad4aa235f751a4e64baad967ce16995723731d`
- Source RULES (publisher_rulebook): `11150c4cdc6aec22655f89a317ad4aa235f751a4e64baad967ce16995723731d`
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
| Clear rules | 0.126 | 0.109 |
| Human decisions | 0.236 | 0.206 |
| Coverage | 0.910 | 0.068 |
| Neutral judges | 0.421 | 0.112 |

## Assumptions

- Structured material declarations: 8

## Efficiency per run

| Measure | Mean | Sample SD |
|---|---:|---:|
| calls | 4.000 | 0.000 |
| provider_seconds | 882.350 | 129.180 |
| input_tokens | 542084.000 | 110005.127 |
| cached_input_tokens | 420522.667 | 87371.166 |
| output_tokens | 26663.333 | 1860.190 |
| reasoning_tokens | 12502.000 | 774.048 |
| api_equivalent_usd | 1.618 | 0.190 |
| code_lines | 226.667 | 34.122 |

Sample SD measures variation across repeated runs; `n/a` means only one run is available.
The USD value is an API-equivalent estimate for gpt-5.6-sol from the recorded tokens and versioned public list price; actual Codex OAuth subscription cost is unavailable.
Persona reviews and raw per-run evidence remain in `result.json`.
