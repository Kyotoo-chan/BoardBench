# Bohnanza Base 2023 — fresh original-PDF run v4

## Status

One fresh isolated publisher-PDF-only generation completed with no repair calls. It was evaluated against the same 41-case comparison-v4 rubric as the clarified condition and reviewed by three neutral Judges.

## Evidence groups

- Technical checks 01–04: **4/4 pass**
- Random rollouts: **100/100 pass** in 34.67 s
- Action-language roundtrips: **1,473,350/1,473,350 pass** in 33.66 s
- Scenarios: **34 PASS, 7 FAIL, 0 CRASH, 0 UNREACHED, 0 UNTESTABLE**
- Evaluated coverage: **41/41**
- Judge scores: **0.28, 0.28, 0.40**
- Judge mean: **0.32**, sample SD **0.069**, n=3

These groups are not combined into one correctness score.

## Deterministic failures

- Third depletion does not terminate correctly on phase-four draw positions one, two, or three.
- Two Garden beans use the wrong payout.
- Phase three does not advance to a non-active recipient for their planting choices.
- Both mandatory-final-harvest cases fail: fields are harvested, but remaining hand cards are incorrectly converted into coins and removed.

## Repeated Judge findings

The neutral reviews repeatedly identify illegal terminal hand scoring, exponential trade-action enumeration, incomplete non-active phase-three planting, unchecked externally constructed actions, and missing harvesting opportunities at approved stable boundaries.

## Provenance

- Generation: `gpt-5.6-sol`, thinking `low`, repairs 0
- Judges: `gpt-5.6-sol`, thinking `medium`, n=3
- Implementation SHA-256: `f5b8cf96e66e14d25f0aa1ebd94f3b5486060ad17e4919b9d3dd9c3939f34991`
- Rubric: `bohnanza-base-2023-comparison-v4-2026-07-23`
- Rubric SHA-256: `afd123f6f5c4143169a38621206ac8bdab56427f666b6f56198233f005763d9e`
