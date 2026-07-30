# CATAN 2022 V2: detailed study record

[← Summary](README.md) · [Condition comparison](v2/COMPARISON.md)

## Design

- Canonical sources: German publisher rulebook 2022 and edition-matched publisher Almanac 2022.
- Scope: illustrated beginner setup for 3 and 4 players; strict roll → trade → build.
- Excluded: variable setup, experienced merged phases, app and expansions.
- Evaluator r3: 125 visible claims (104 clear, 17 missing, 2 ambiguous, 1 conflicting, 1 untestable), 99 required executable clear claims, 55 scenarios and 113 named cases.
- Generation: `gpt-5.6-sol`, low thinking, one call per condition, zero repairs.
- Valid Judges: same model, medium thinking, three mutually blind reviews per condition.

## Conditions

### Original compatibility replay

The implementation is byte-identical to the previously scored Original. Evaluator r3 adds four approved human-decision cases without rewriting the r2 result.

- Clear 37/40; Human Decision 10/15.
- Main defect: Longest Road is never calculated.
- Other defects: Road Building can exceed stock; submitted discard is mutable; trade builder unbounded.
- Valid Judges r2: 0.66 / 0.72 / 0.58, mean 0.653.

### Clear-rule emphasis

Model-facing addition: a separately attributed experimenter artifact repeating publisher-clear Longest Road and physical road-stock requirements. It contains no source-gap decisions.

- Clear 38/40; Human Decision 13/15.
- Target success: all Longest Road and edge-simple-cycle scenarios pass; one-road stock handling passes.
- Remaining target edge: with zero roads, Road Building is made unplayable instead of resolving with zero placements.
- Regressions: missing explicit red-color removal in three-player setup; no immediate win when a ten-point player becomes active.
- Valid Judges r2: 0.80 / 0.89 / 0.76, mean 0.817.

### Source-gap clarification

Model-facing addition: only four user-approved decisions:

1. offer totals capped by public hand sizes;
2. submitted private discards become interrupt-safe escrow;
3. an adjacent Knight victim must be selected, with empty hands still selectable;
4. maritime receive type must differ from give type.

- Clear 32/40; Human Decision 11/15.
- Direct target passes: finite offer bound, submitted escrow against Monopoly, different-resource maritime exchange.
- Mandatory victim behavior is masked by a clear pre-roll development-card defect.
- Major regressions: development cards unavailable before rolling; valid domestic offers cannot be accepted; settlement interruption does not recompute Longest Road; some interrupt resumptions are wrong.
- Valid Judges r2: 0.85 / 0.78 / 0.84, mean 0.823.

## Root-cause groups

### Original

1. Longest Road state initialized but never updated.
2. Free-road generation bypasses physical stock.
3. No finite cumulative trade-offer bound.
4. Submitted selections remain available to effects.

### Clear emphasis

1. Zero-stock Road Building precondition is too strict.
2. Three-player removed-color record regresses.
3. Turn-start immediate victory check regresses.
4. Untargeted submitted-discard and interrupt issues remain.

### Clarification

1. Legal development interrupts omit the roll phase, causing five clear scenario failures plus dependent human-decision failures.
2. Awaiting trade acceptance checks the proposer's give bundle against the responder because `current_player` has changed.
3. Longest Road recomputation occurs after road placement but not after an opponent settlement.
4. `_available` reserves tentative discard choices before submission; r3 verifies submitted escrow but a valid Judge detects this narrower over-reservation.

## Evaluator history

The first Original scenario replay was invalid due to three neutral representation assumptions and remains archived unscored. Evaluator r2 corrected them without changing code. Evaluator r3 was frozen before either intervention and adds four approved gap decisions; it replayed unchanged Original code for comparison.

## Judge history

The initial Original and clear-emphasis Judge packets copied the publisher companion PDF but rendered only the primary PDF. This violates the full-page-image policy. Those reviews and result cards remain historical but are method-invalid. Judge packet r2:

- renders the complete rulebook and complete Almanac independently at 150 DPI;
- includes both PDFs and their separate provenance;
- attributes an optional intervention separately;
- reruns all three conditions.

Manifest: `inputs/games/catan/judge_packet_revision_v2_r2.json`.

## Scientific interpretation

The runs show local target associations: two previously failing clarification cases pass with the added decisions, and every tested Longest Road case passes with emphasis. They do not establish causal effects or monotonic global improvement because each condition has only one fresh generation. Unrelated regressions can outweigh target gains, and scenario evidence and Judge evidence rank the conditions differently; both remain separate rather than being averaged.
