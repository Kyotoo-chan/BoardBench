# CATAN 2022 V2 intervention comparison

## Comparable evidence basis

Evaluator r3 was frozen before either intervention generation. It adds four approved human-decision scenarios and replays the unchanged Original code; the Original r2 result remains historical evidence. Neutral-judge packet r2 was then introduced because the earlier runner copied the publisher Almanac PDF without rendering its pages. Prior Judge reviews remain archived but are method-invalid for comparison. The valid packet renders both publisher PDFs completely at 150 DPI and attributes the intervention separately.

| Evidence | Original compatibility | Clear-rule emphasis | Source-gap clarification |
|---|---:|---:|---:|
| Generation calls / repairs | 1 / 0 | 1 / 0 | 1 / 0 |
| Technical gate | 4/4 | 4/4 | 4/4 |
| Robustness | 100/100 | 100/100 | 100/100 |
| Player counts | 4/4 | 4/4 | 4/4 |
| Clear-basis | **37/40** | **38/40** | **32/40** |
| Human-decision-basis | **10/15** | **13/15** | **11/15** |
| Evaluated scenarios | 55/55 | 55/55 | 55/55 |
| Named cases | 113/113 | 113/113 | 113/113 |
| Valid Judges | 0.66 / 0.72 / 0.58 | 0.80 / 0.89 / 0.76 | 0.85 / 0.78 / 0.84 |
| Judge mean (sample SD) | **0.653** (0.070) | **0.817** (0.067) | **0.823** (0.038) |

The evidence groups are not combined into a total score.

## Clear-rule emphasis

The emphasis passes every predeclared tested Longest Road case: threshold, branches, interruption, transfer, ties and edge-simple cycles. Judges no longer report the feature as missing; this finite suite does not establish exhaustive subsystem correctness. It also fixes the one-road Road Building stock case.

It does not produce uniform improvement:

- zero-road Road Building incorrectly makes the card unplayable;
- three-player setup no longer records red as explicitly removed;
- a player already at ten does not win upon becoming active before rolling.

Thus Clear improves only 37/40 → 38/40 despite eliminating the Original's dominant defect group. Human Decision improves 10/15 → 13/15.

## Source-gap clarification

Three targets pass directly: finite public-count offer bounds, submitted-discard protection against Monopoly, and different-resource maritime trade. Mandatory Knight victim selection cannot be credited because the new implementation first violates the clear rule allowing pre-roll development-card play.

The fresh generation introduces broader regressions:

- development cards unavailable before rolling;
- valid domestic trades cannot be accepted due to a proposer/responder indexing error;
- opponent settlements do not trigger Longest Road recomputation;
- some interrupt resumptions use the wrong pending actor.

Consequently Clear drops to 32/40 and Human Decision reaches only 11/15, even though the valid Judge mean is the highest at 0.823. Judges reward the broader architecture and correctly implemented clarification targets but do not replace deterministic scenario evidence.

## Why clarification sometimes helps and sometimes does not

A clarification changes model context; it does not patch the prior implementation. Each condition is one fresh stochastic synthesis. Exploding Kittens' clarified run passed its previously failing empty-target case, while CATAN's additional protocol detail coincided with improvement on two previously failing targets and unrelated publisher-clear regressions. With one generation per condition, these are observed associations rather than an estimate of causal effect or generation variance.

This reproduces the pattern already visible in Bohnanza:

- narrow emphasis can increase local salience while harming whole-game balance;
- a balanced structured clarification can improve Judge assessment without exceeding the Original scenario pass count;
- neither intervention guarantees monotonic improvement.

## Conclusion

- **Best deterministic CATAN successor on the predeclared r3 basis:** clear-rule emphasis.
- **Best valid neutral-Judge signal:** source-gap clarification, by a negligible 0.007 mean over emphasis and with much worse clear scenarios.
- **Observed in these runs:** two previously failing clarification targets pass after receiving the decisions, and all tested Longest Road cases pass after emphasis.
- **Not established:** causal attribution, expected effects across repeated generations, or that more clarification reliably produces a globally better implementation.

No best-of implementation is selected or promoted. Original, emphasis and clarification remain separate adapted runs with all regressions retained.
