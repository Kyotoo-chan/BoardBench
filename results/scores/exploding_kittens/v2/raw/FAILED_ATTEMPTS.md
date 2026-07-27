# Exploding Kittens V2 failed pre-evaluation attempts

## `v2_original_1` preflight attempt 1 — 2026-07-27

- The hardened generation produced an implementation and exhausted two evaluator-neutral repair calls.
- Evaluation did not start and this is not a scored condition.
- Root cause was an evaluator fixture-check defect: `profile_fixture_self_check_v2.py` cleared all hands before collecting the full 56-card inventory, so every reconstructed phase falsely appeared 16 cards short.
- The implementation’s own agentic self-check passed. Replaying the corrected fixture check against the retained generated module passed.
- The fixture check was corrected and received a regression test before a fresh same-condition launch.
- Raw canonical artifacts, all three calls and their events are retained in `failed_preflight_1.tar.gz`.

## `v2_original_1` invalid evaluator replay — 2026-07-27

- A fresh one-call generation passed its complete pre-evaluation gate, technical checks, 100/100 rollouts, interface checks, and player-count checks.
- The first scenario replay was invalidated before reporting or judging because the model-facing profile had not defined which end of canonical `zones.deck` was the top. The evaluator fixtures assumed first-item-top while the implementation consistently used final-item-top; this produced six false clear-basis failures and two false human-decision failures. Two further clear-basis failures were evaluator timing errors: one missing NÖ!-pass settle and an unsupported intermediate `current_player` assertion during Favor donation. Thus ten of eleven failures were evaluator-caused; only `EXPL-R27` remained a genuine human-decision deviation in the diagnostic corrected replay.
- The raw 27/38 replay is **not a scored Original condition** and no judges were run.
- V2.1 freezes deck state bottom-to-top, defines reinsertion indexing, removes the unsupported intermediate assertion, and settles the mechanical reaction boundary. Game-rule claims and expected source behavior are unchanged.
- The generated module, raw generation evidence, grouped checks, and invalid scenario replay are retained in `invalid_profile_evaluation_1.tar.gz`.
