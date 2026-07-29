# Bohnanza Base 2023 V2 invalid evaluator replay

## `v2_original_1` first replay — 2026-07-28

- The final blind one-call implementation passed the complete pre-evaluation gate, technical checks, 100/100 rollouts, interface checks and player-count checks.
- The first 42-case replay was invalidated before judging or reporting because the evaluator adapter rejected canonical bean IDs already used by action payloads, and four artificial phase-boundary fixtures expected automatic transitions where the profile permits an explicit mechanical `pass` action.
- These evaluator defects caused three `UNTESTABLE` results and four false timing failures (`BOHN-R11`, `R14`, `R23`, `R40`).
- The adapter now accepts both human-readable fixture aliases and canonical bean IDs. The affected cases mechanically pass empty phase boundaries before asserting the next rule state. No source expectation, model-facing packet, generated implementation or scored behavior changed.
- The invalid 32 PASS / 7 FAIL / 3 UNTESTABLE replay is retained only in `invalid_evaluator_replay_1.tar.gz`. It receives no Result Card and no Judges.
- A first correction accidentally retained mutually contradictory `draw required` and `draw forbidden` assertions immediately before the explicit phase-three pass in `BOHN-R23`; that intermediate 36 PASS / 6 FAIL replay is retained in `invalid_evaluator_replay_2.tar.gz` and is also unscored and unjudged.
- The final replay after removing that contradictory evaluator assertion is the only eligible Original evidence.

## `v2_clear_rule_emphasis_2` first replay — 2026-07-28

- The exact repeat passed its one-call pre-evaluation gate and all technical groups.
- Its first replay exposed one remaining evaluator overconstraint inherited from accommodating the first two implementations: three phase-three cases required an explicit mechanical `pass` state, although the profile permits an implementation to advance automatically once every required card is planted.
- `BOHN-R14`, `R23`, and `R40` now optionally settle one pass only when all legal actions are pass/harvest; implementations that already advanced to draw or terminal are left unchanged. Source expectations and all post-boundary assertions are unchanged.
- The invalid 31 PASS / 11 FAIL replay is retained in `invalid_emphasis_2_evaluator_replay_1.tar.gz`; it is unscored and unjudged.
