# Abalone: Original PDF and Setup-Emphasis replication

## Current presentation (v3)

v3 is a compatibility replay of the frozen v2 implementations. It does not score the unspecified no-move forced-pass case. v2 scores, including the emphasis `4/5` human-decision result, remain in [`v2/`](v2/).

| Evidence group | Original | Emphasis 1 | Emphasis 2 |
|---|---:|---:|---:|
| Agentic gate | PASS | PASS | PASS |
| Technical checks | 4/4 | 4/4 | 4/4 |
| Robustness | 100/100 | 100/100 | 100/100 |
| Player counts | 3/3 | 3/3 | 3/3 |
| Clear basis | 32/33 | 33/33 | 33/33 |
| Human-decision basis | 4/4 | 4/4 | 4/4 |
| Evaluated scenarios | 37/37 | 37/37 | 37/37 |
| Neutral Judge mean (SD) | 0.867 (0.031) | 0.893 (0.081) | 0.870 (0.030) |

The only configured v3 failure is the original Figure-1 setup. See [`v3/COMPARISON.md`](v3/COMPARISON.md).

## Historical v2 scores

The Original misses only the clear Figure-1 setup and otherwise passes every configured v2 scenario. Two exact fresh Setup-Emphasis generations both fix the setup and both independently omit the approved forced pass.

| Evidence group | Original | Emphasis 1 | Emphasis 2 |
|---|---:|---:|---:|
| Agentic gate | PASS | PASS | PASS |
| Technical checks | 4/4 | 4/4 | 4/4 |
| Robustness | 100/100 | 100/100 | 100/100 |
| Player counts | 3/3 | 3/3 | 3/3 |
| Clear basis | 32/33 | 33/33 | 33/33 |
| Human-decision basis | 5/5 | 4/5 | 4/5 |
| Evaluated scenarios | 38/38 | 38/38 | 38/38 |
| Neutral Judge mean (SD) | 0.867 (0.031) | 0.893 (0.081) | 0.870 (0.030) |

Evidence groups are not combined. The two emphasis runs used byte-identical model packets and are both retained; this is not best-of selection.

Replicate 2 additionally has a confirmed but unscored post-judge action-alias candidate. See [`DETAILS.md`](DETAILS.md), [`v2/COMPARISON.md`](v2/COMPARISON.md), and [`v2/setup_emphasis_2_findings.md`](v2/setup_emphasis_2_findings.md).
