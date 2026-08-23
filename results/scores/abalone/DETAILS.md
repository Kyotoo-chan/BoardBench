# Abalone: detailed V2 evaluation

[← Overview](README.md)

**Current presentation:** v3 compatibility replay without scoring `ABAL-R19`. See [`v3/COMPARISON.md`](v3/COMPARISON.md). This file keeps the frozen v2 record.

**Model setup:** all three implementations use `gpt-5.6-sol:low`; each has three neutral `gpt-5.6-sol:medium` Judges. PDF, prompt, Contract-v2 profile and the 38-scenario rubric are unchanged. Both Setup-Emphasis generations use byte-identical model packets.

## Design and sequence

1. The V2 matrix and Human Decisions were approved before generation.
2. Original PDF-only was generated and evaluated: only the clear setup failed.
3. Setup-Emphasis replicate 1 repeated only the clear Figure-1 setup in a separately attributed artifact.
4. After its forced-pass regression, replicate 2 was pre-registered as an exact fresh replication with no best-of replacement.
5. Replicate 1 remains retained; replicate 2 was declared the final successor before launch regardless of outcome.

## Evidence groups

| Evidence | Original | Emphasis 1 | Emphasis 2 |
|---|---:|---:|---:|
| Agentic gate | PASS | PASS | PASS |
| Technical checks | 4/4 | 4/4 | 4/4 |
| Rollouts | 100/100 | 100/100 | 100/100 |
| Interface | 8,888,062/8,888,062 | 8,528,518/8,528,518 | 5,704,536/5,704,536 |
| Player counts | 3/3 | 3/3 | 3/3 |
| Clear basis | 32/33 | 33/33 | 33/33 |
| Human-decision basis | 5/5 | 4/5 | 4/5 |
| Coverage | 38/38 | 38/38 | 38/38 |
| Judges | 0.86 / 0.90 / 0.84 | 0.80 / 0.93 / 0.95 | 0.90 / 0.87 / 0.84 |
| Judge mean (SD) | 0.867 (0.031) | 0.893 (0.081) | 0.870 (0.030) |

## All scenarios

| ID | Basis | Claims | Original | Emphasis 1 | Emphasis 2 |
|---|---|---|---:|---:|---:|
| `ABAL-R01-exact-initial-setup` | clear | `ABAL-C-SETUP-FIGURE`, `ABAL-C-BOARD-61`, `ABAL-C-SETUP-COUNTS`, `ABAL-C-SETUP-ROWS` | **FAIL** | PASS | PASS |
| `ABAL-R02-single-marble-one-step-and-turn` | clear | `ABAL-C-ONE-MOVE`, `ABAL-C-ONE-STEP`, `ABAL-C-SIX-DIRECTIONS`, `ABAL-C-TURN-ORDER` | PASS | PASS | PASS |
| `ABAL-R03-two-marble-inline` | clear | `ABAL-C-GROUP-SIZE`, `ABAL-C-SAME-DIRECTION`, `ABAL-C-STRAIGHT-CONTIGUOUS`, `ABAL-C-INLINE` | PASS | PASS | PASS |
| `ABAL-R04-three-marble-broadside` | clear | `ABAL-C-GROUP-SIZE`, `ABAL-C-SAME-DIRECTION`, `ABAL-C-STRAIGHT-CONTIGUOUS`, `ABAL-C-BROADSIDE`, `ABAL-C-EMPTY-DESTINATION` | PASS | PASS | PASS |
| `ABAL-R05-four-marble-move-illegal` | clear | `ABAL-C-GROUP-SIZE`, `ABAL-C-MAX-THREE` | PASS | PASS | PASS |
| `ABAL-R06-two-v-one-sumito` | clear | `ABAL-C-SUMITO-SUPERIOR`, `ABAL-C-SUMITO-PATTERNS`, `ABAL-C-SUMITO-INLINE`, `ABAL-C-SUMITO-ADJACENT`, `ABAL-C-SUMITO-FREE-BEHIND` | PASS | PASS | PASS |
| `ABAL-R07-three-v-one-sumito` | clear | `ABAL-C-SUMITO-SUPERIOR`, `ABAL-C-SUMITO-PATTERNS` | PASS | PASS | PASS |
| `ABAL-R08-three-v-two-sumito` | clear | `ABAL-C-SUMITO-SUPERIOR`, `ABAL-C-SUMITO-PATTERNS` | PASS | PASS | PASS |
| `ABAL-R09-broadside-push-illegal` | clear | `ABAL-C-SUMITO-INLINE`, `ABAL-C-BROADSIDE`, `ABAL-C-EMPTY-DESTINATION` | PASS | PASS | PASS |
| `ABAL-R10-equal-strength-pushes-illegal` | clear | `ABAL-C-PATT-EQUAL` | PASS | PASS | PASS |
| `ABAL-R11-four-v-three-still-patt` | clear | `ABAL-C-PATT-FOUR-THREE`, `ABAL-C-MAX-THREE` | PASS | PASS | PASS |
| `ABAL-R12-blocked-sumito-illegal` | clear | `ABAL-C-SUMITO-FREE-BEHIND`, `ABAL-C-SUMITO-BLOCKED` | PASS | PASS | PASS |
| `ABAL-R13-gap-does-not-push` | clear | `ABAL-C-SUMITO-ADJACENT`, `ABAL-C-SUMITO-GAP` | PASS | PASS | PASS |
| `ABAL-R14-non-collinear-push-illegal` | clear | `ABAL-C-SUMITO-INLINE`, `ABAL-C-SUMITO-COLLINEAR` | PASS | PASS | PASS |
| `ABAL-R15-edge-ejection` | clear | `ABAL-C-EJECTION`, `ABAL-C-EDGE-EXCEPTION`, `ABAL-C-SUMITO-SUPERIOR` | PASS | PASS | PASS |
| `ABAL-R16-sixth-ejection-wins` | clear | `ABAL-C-SIXTH-WINS`, `ABAL-C-EJECTION` | PASS | PASS | PASS |
| `ABAL-R17-sumito-is-optional` | clear | `ABAL-C-SUMITO-OPTIONAL` | PASS | PASS | PASS |
| `ABAL-R18-patt-may-withdraw` | clear | `ABAL-C-PATT-EQUAL`, `ABAL-C-PATT-WITHDRAW` | PASS | PASS | PASS |
| `ABAL-R20-three-marble-inline` | clear | `ABAL-C-GROUP-SIZE`, `ABAL-C-STRAIGHT-CONTIGUOUS`, `ABAL-C-INLINE` | PASS | PASS | PASS |
| `ABAL-R21-two-broadside-from-longer-row` | clear | `ABAL-C-STRAIGHT-CONTIGUOUS`, `ABAL-C-BROADSIDE`, `ABAL-C-SUBSET-LONG-ROW` | PASS | PASS | PASS |
| `ABAL-R22-one-v-one-patt` | clear | `ABAL-C-PATT-EQUAL` | PASS | PASS | PASS |
| `ABAL-R23-two-v-two-patt` | clear | `ABAL-C-PATT-EQUAL` | PASS | PASS | PASS |
| `ABAL-R19-forced-pass-only-with-no-move` | human_decision | `ABAL-G-PASS` | PASS | **FAIL** | **FAIL** |
| `ABAL-R24-player-count-and-bounded-playability` | clear | `ABAL-C-PLAYERS` | PASS | PASS | PASS |
| `ABAL-R25-single-step-e` | clear | `ABAL-C-ONE-STEP`, `ABAL-C-SIX-DIRECTIONS` | PASS | PASS | PASS |
| `ABAL-R26-single-step-ne` | clear | `ABAL-C-ONE-STEP`, `ABAL-C-SIX-DIRECTIONS` | PASS | PASS | PASS |
| `ABAL-R27-single-step-nw` | clear | `ABAL-C-ONE-STEP`, `ABAL-C-SIX-DIRECTIONS` | PASS | PASS | PASS |
| `ABAL-R28-single-step-w` | clear | `ABAL-C-ONE-STEP`, `ABAL-C-SIX-DIRECTIONS` | PASS | PASS | PASS |
| `ABAL-R29-single-step-sw` | clear | `ABAL-C-ONE-STEP`, `ABAL-C-SIX-DIRECTIONS` | PASS | PASS | PASS |
| `ABAL-R30-single-step-se` | clear | `ABAL-C-ONE-STEP`, `ABAL-C-SIX-DIRECTIONS` | PASS | PASS | PASS |
| `ABAL-R31-invalid-group-and-destination-boundaries` | clear | `ABAL-C-STRAIGHT-CONTIGUOUS`, `ABAL-C-GROUP-SIZE`, `ABAL-C-EMPTY-DESTINATION`, `ABAL-C-SUMITO-INLINE` | PASS | PASS | PASS |
| `ABAL-R32-broadside-blocked-and-offboard` | human_decision | `ABAL-G-BROADSIDE-DESTINATIONS` | PASS | PASS | PASS |
| `ABAL-R33-patt-broadside-withdrawal` | clear | `ABAL-C-PATT-WITHDRAW`, `ABAL-C-BROADSIDE` | PASS | PASS | PASS |
| `ABAL-R34-crossing-angle-breaks-patt` | clear | `ABAL-C-PATT-EQUAL`, `ABAL-C-PATT-CROSSING` | PASS | PASS | PASS |
| `ABAL-R35-three-v-two-edge-ejects-one` | clear | `ABAL-C-SUMITO-PATTERNS`, `ABAL-C-EJECTION`, `ABAL-C-EDGE-EXCEPTION` | PASS | PASS | PASS |
| `ABAL-R36-terminal-api-and-returns` | human_decision | `ABAL-G-TERMINAL-API`, `ABAL-G-RETURNS` | PASS | PASS | PASS |
| `ABAL-R37-action-serialization-is-unique` | human_decision | `ABAL-G-ACTION-UNIQUE` | PASS | PASS | PASS |
| `ABAL-R38-public-contract-observability` | human_decision | `ABAL-G-PUBLIC-STATE`, `ABAL-G-PLAYER-MAPPING` | PASS | PASS | PASS |

## Confirmed defects

- **Original:** `ABAL-R01` — Figure 1 requires 14 black and 14 white marbles; actual 13/13.
- **Setup Emphasis 1:** `ABAL-R19` — no approved forced pass in a no-movement state.
- **Setup Emphasis 2:** the same `ABAL-R19` failure recurs.

## Judge evidence

All three Original Judges confirm the setup defect. All three Judges in each emphasis condition confirm the missing forced pass. In replicate 2 all three additionally report parser-created group-order aliases. A deterministic post-judge replay confirms the alias behavior, but it remains unscored because frozen `ABAL-R37` checks only emitted legal-action uniqueness.

## Assumptions

- Original: 2 declared material assumptions, including forced pass.
- Setup Emphasis 1: 2 declared material assumptions; forced pass is absent.
- Setup Emphasis 2: 3 declared material assumptions; `A-03` explicitly selects no pass.

## Replication interpretation

The two emphasis runs have identical configured scenario outcomes. This makes the first forced-pass regression less plausibly a single-run anomaly, but `n=2` cannot establish causality. The approved forced-pass decision was hidden from all model packets. No run is replaced or selected as best.

## Provenance

- Rulebook SHA-256: `c293ed5d319ccb4fa5725921613f4a05ba2453074d2b2dcdc11cdeb9f8570550`
- Rubric SHA-256: `be0b349288ab099973bf2ead1e6f793a7f7b866756b4be83bae1aba07a973935`
- Adapter SHA-256: `7b83946eb17394320b77b5b2da3925172a14ef8434322243080c498c707141da`
- Original code: `4098c2dfc360915fd2760393907fe107e878c7b9a4ac3d2c4fcebab71b7e4ccd`
- Emphasis 1 code: `e90443a23286c3e13645f0b464b346834db8c7641b66d6db913a4231f5c6f446`
- Emphasis 2 code: `174b4743c056ef578cf38547713ade4260b897762dd7d3fa54cc6fc6695adc9f`

## Artifacts

- Comparison: [`v2/COMPARISON.md`](v2/COMPARISON.md)
- Result profiles: [`v2/original_result.json`](v2/original_result.json) · [`v2/setup_emphasis_result.json`](v2/setup_emphasis_result.json) · [`v2/setup_emphasis_2_result.json`](v2/setup_emphasis_2_result.json)
- Findings: [`v2/original_findings.md`](v2/original_findings.md) · [`v2/setup_emphasis_findings.md`](v2/setup_emphasis_findings.md) · [`v2/setup_emphasis_2_findings.md`](v2/setup_emphasis_2_findings.md)
- Frozen suite: `checks/scenarios/abalone_v2.json`
- Original/Emphasis-1 raw archive: `v2/raw/study_artifacts.tar.gz`
- Emphasis-2 raw archive: `v2/raw/setup_emphasis_2_artifacts.tar.gz`
