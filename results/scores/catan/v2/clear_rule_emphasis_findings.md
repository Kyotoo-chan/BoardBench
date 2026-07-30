# CATAN V2 clear-rule-emphasis findings

- Separate post-evaluation clear-rule salience intervention; not a source-gap clarification.
- Same PDF, matching Almanac, model/thinking, prompt, contract and profile as Original.
- Agentic gate: PASS; one call; no repairs.
- Technical 4/4; robustness 100/100; interface 4,342,395/4,342,395; player counts 4/4.
- Clear-basis: 38/40.
- Human-decision-basis: 13/15.
- Judges: 0.72 / 0.72 / 0.83; mean 0.757, sample SD 0.064.

## Target effects

The intervention succeeds on its main target: all Longest Road threshold, branch, interruption, transfer, tie and edge-simple-cycle scenarios (`R18`–`R21`) pass. It also enforces road stock after one remaining free road. Judge reviews no longer report missing Longest Road.

The zero-road Road Building case (`R40`) remains a human-decision failure because the implementation makes the card unplayable rather than resolving the approved maximum-feasible effect with zero placements.

## Regressions

1. `R01A`: three-player setup no longer records red as an explicitly removed color.
2. `R35`: a player already at ten does not win immediately upon becoming active before rolling.

These are unrelated clear regressions and prevent the emphasis run from establishing globally improved clear-rule fidelity despite fixing the dominant Original defect.

## Untargeted source gaps

`R45` fails as expected for a condition that did not receive the later escrow clarification: Monopoly can take a resource already submitted for simultaneous discard.

All Judges add consistent unscored concerns: Knight interrupts resume with the wrong decision actor, and trade acceptance is not safely revalidated after interrupts. Two identify submitted-discard escrow as still mutable. Domestic offer enumeration may reveal private identities or remain unbounded depending on state. These findings motivate the separate source-gap clarification run and are not evidence that the clear-rule emphasis itself contained those decisions.
