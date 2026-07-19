# Bohnanza post-hoc evaluator-v2 replay

The frozen original results remain unchanged. V2 removes representation-dependent card flattening/hash failures, uses broader phase/container aliases, and classifies unsupported evaluator reconstruction as UNTESTABLE rather than implementation CRASH.

| Condition | Runs | Original P/F/C/U | V2 P/F/C/U | Original pass / coverage | V2 pass / coverage |
|---|---:|---:|---:|---:|---:|
| `json_clean` | 3 | 16/52/33/10 | 61/33/0/17 | 0.158 / 0.910 | 0.649 / 0.847 |
| `json_mutated` | 3 | 2/3/50/56 | 26/7/0/78 | 0.036 / 0.495 | 0.788 / 0.297 |
| `pdf_mutated` | 3 | 6/58/12/35 | 20/45/0/46 | 0.079 / 0.685 | 0.308 / 0.586 |
| `pdf_only` | 3 | 25/51/11/24 | 42/17/0/52 | 0.287 / 0.784 | 0.712 / 0.532 |
| `diagnostic` | 1 | 0/2/35/0 | 29/7/0/1 | 0.000 / 1.000 | 0.806 / 0.973 |

## Per run

| Run | Original P/F/C/U | V2 P/F/C/U | Original pass / coverage | V2 pass / coverage |
|---|---:|---:|---:|---:|
| `json_clean_1` | 0/4/27/6 | 22/9/0/6 | 0.000 / 0.838 | 0.710 / 0.838 |
| `json_clean_2` | 8/24/2/3 | 25/5/0/7 | 0.235 / 0.919 | 0.833 / 0.811 |
| `json_clean_3` | 8/24/4/1 | 14/19/0/4 | 0.222 / 0.973 | 0.424 / 0.892 |
| `json_mutated_1` | 0/1/12/24 | 3/0/0/34 | 0.000 / 0.351 | 1.000 / 0.081 |
| `json_mutated_2` | 2/0/11/24 | 4/0/0/33 | 0.154 / 0.351 | 1.000 / 0.108 |
| `json_mutated_3` | 0/2/27/8 | 19/7/0/11 | 0.000 / 0.784 | 0.731 / 0.703 |
| `pdf_mutated_1` | 3/29/2/3 | 11/23/0/3 | 0.088 / 0.919 | 0.324 / 0.919 |
| `pdf_mutated_2` | 0/1/10/26 | 1/0/0/36 | 0.000 / 0.297 | 1.000 / 0.027 |
| `pdf_mutated_3` | 3/28/0/6 | 8/22/0/7 | 0.097 / 0.838 | 0.267 / 0.811 |
| `pdf_only_1` | 17/9/2/9 | 2/2/0/33 | 0.607 / 0.757 | 0.500 / 0.108 |
| `pdf_only_2` | 6/21/6/4 | 24/7/0/6 | 0.182 / 0.892 | 0.774 / 0.838 |
| `pdf_only_3` | 2/21/3/11 | 16/8/0/13 | 0.077 / 0.703 | 0.667 / 0.649 |
| `json_clean_diagnostic_1` | 0/2/35/0 | 29/7/0/1 | 0.000 / 1.000 | 0.806 / 0.973 |

## Boundary

V2 is still a legacy compatibility adapter over heterogeneous implementations. It is more representation-safe, but only future implementations generated against the canonical BoardBench state/action data contract can eliminate heuristic introspection. V2 outcomes are post-hoc diagnostic evidence and must not replace the preregistered frozen scores.
