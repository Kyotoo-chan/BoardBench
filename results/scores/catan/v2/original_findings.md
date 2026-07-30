# CATAN 2022 V2 Original findings

- Condition: byte-identical 2022 German publisher rulebook plus matching 2022 publisher Almanac; no clarification artifact.
- Scope: illustrated beginner setup for 3 and 4 players, strict roll → trade → build.
- Model: `gpt-5.6-sol`, thinking `low`.
- Agentic gate: PASS; one generation call; no repairs.
- Technical gate: 4/4.
- Robustness: 100/100.
- Interface: 8,883,707/8,883,707.
- Player counts: 4/4 (3 and 4 supported; 2 and 5 rejected).
- Clear-basis scenarios: 37/40.
- Human-decision-basis scenarios: 8/11.
- Evaluated coverage: 51/51 scenarios and 107/107 named cases under evaluator revision r2.
- Historical Judge packet r1 (method-invalid because Almanac pages were not rendered): 0.62 / 0.66 / 0.61.
- Valid Judge packet r2: 0.66 / 0.72 / 0.58; mean 0.653, sample SD 0.070.

## Scored failures

All three clear-basis failures are one implementation defect group:

1. **Longest Road is never calculated.** `longest_road_owner` and `longest_road_length` are initialized but never updated. Consequently threshold/branch (`R18`), interruption (`R19`) and transfer/tie behavior (`R20`) fail.

Human-decision failures:

2. **Longest Road cycle semantics (`R21`)** fail for the same missing implementation, not because the selected edge-simple-trail decision is separately contradicted.
3. **Road Building ignores remaining road stock (`R40`).** The free-road action generator bypasses the stock check, permitting a second placement after stock reaches zero.
4. **Immediate victory during Road Building (`R43`)** does not occur because the missing Longest Road award never supplies the winning two points; pending-effect cancellation itself is not independently disproven.

## Judge-only findings

The valid r2 Judges independently identify Longest Road as the dominant major omission and Road Building stock as major. They also identify an unbounded domestic-offer builder: each state has a finite add-one-resource action set, but offer counts can grow without a source/profile-defined cap. This is a genuine digital-protocol clarification candidate, not a publisher-clear defect score.

One Judge identifies a real unscored robustness risk: a player may privately submit discards, after which a permitted development-card interrupt can alter those resources before simultaneous settlement, potentially producing negative counts. This needs a new evaluator version or clarification before being scored.

Other Judge comments require caution:

- Empty-handed adjacent robbery victims are intentionally selectable under the approved human decision, so that finding conflicts with the frozen condition.
- Progress-card physical storage is representation-sensitive; r2 scores non-replayability and public played-card evidence rather than an undeclared list destination.
- Same-resource maritime exchange and optional Knight robbery remain source-interpretation questions, not scored defects.

## Evaluator history

The first scenario replay was invalid because three inherited expectations imposed undeclared representation details. It was never judged or scored and is retained under `raw/invalid_evaluator_replay_1.tar.gz`. The implementation was not changed. Evaluator revision r2 corrected only those neutral issues; its manifest is `inputs/games/catan/evaluator_revision_v2_r2.json`.
