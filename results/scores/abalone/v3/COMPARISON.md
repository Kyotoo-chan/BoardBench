# Abalone v3 compatibility replay

v2 remains the historical scored iteration, including `4/5` human-decision scenarios. v3 is an evaluator revision only: the three frozen implementations were replayed under a suite that does not score `ABAL-R19-forced-pass-only-with-no-move`. No code was regenerated.

## Why R19 is unscored

The publisher rulebook does not say what happens when the active player has no legal movement. The untimed base game has no timeout loss. The R19 fixture is a constructed surround with one black marble, not a reachable deadlock from the 14-marble setup. A pass is not a publisher rule. Tournament practice also does not supply a pass rule for this case.

## Reported v3 scenario scores

| Evidence | Original | Emphasis 1 | Emphasis 2 |
|---|---:|---:|---:|
| Clear basis | 32/33 | 33/33 | 33/33 |
| Human-decision basis | 4/4 | 4/4 | 4/4 |
| Evaluated scenarios | 37/37 | 37/37 | 37/37 |

The only remaining configured failure is the original Figure-1 setup (`13` marbles per color instead of `14`). Both emphasis runs still correct that setup. Under v3 they no longer share a scored human-decision miss.

## Relation to v2

Under v2, both emphasis runs failed R19 (`legal_action_count: expected 1, got 0`) and the original passed it. Those outcomes stay in `results/scores/abalone/v2/`. The second emphasis generation was launched because of that v2 mismatch. v3 does not replace or hide that history.

Judges are unchanged from v2. They may still mention a missing pass. That remains qualitative review evidence, not a v3 scenario failure.

## Hashes

See `inputs/games/abalone/evaluator_revision_v3.json`. Original code SHA-256 is unchanged from v2: `4098c2dfc360915fd2760393907fe107e878c7b9a4ac3d2c4fcebab71b7e4ccd`.
