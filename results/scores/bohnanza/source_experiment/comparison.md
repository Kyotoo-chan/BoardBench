# Bohnanza source-condition comparison

Three fresh valid generations per arm. No combined correctness score.

| Arm | Technical gate | Robustness gate / mean | Interface gate / mean | Scenarios P/F/C/U | Evaluated pass fraction | Coverage mean | Judges mean ± SD |
|---|---:|---:|---:|---:|---:|---:|---:|
| `pdf_only` | 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 25/51/11/24 | 0.287 | 0.784 | 0.214 ± 0.034 |
| `json_clean` | 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 16/52/33/10 | 0.158 | 0.910 | 0.421 ± 0.112 |
| `json_mutated` | 1.000 | 0.667 / 0.877 | 0.667 / 1.000 | 2/3/50/56 | 0.036 | 0.495 | 0.352 ± 0.118 |
| `pdf_mutated` | 1.000 | 1.000 / 1.000 | 1.000 / 1.000 | 6/58/12/35 | 0.079 | 0.685 | 0.370 ± 0.027 |

## Interpretation boundary

These descriptive three-run samples do not establish statistical significance. Scenario failures and crashes are distinct, and untestable cases are not scored as rule failures. See `mutation_audit.md` for preregistered mutation uptake and detector blind spots, and `artifact_audit.md` for completeness and isolation evidence.
