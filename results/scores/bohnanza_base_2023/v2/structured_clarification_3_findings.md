# Bohnanza V2 structured clarification 3 — exact replicate

- Official pre-registered third exact generation; no best-of replacement.
- Initial model packet is byte-identical to structured replicates 1 and 2.
- Agentic gate: PASS; one call, no repairs.
- Technical gate: 4/4.
- Robustness: 100/100.
- Interface: 563,753/563,753.
- Player counts: 5/5.
- Clear-basis scenarios: 33/38.
- Human-decision-basis scenarios: 3/4.
- Evaluated coverage: 42/42.
- Neutral Judges: 0.62 / 0.62 / 0.61; mean 0.617, sample SD 0.006.

## Scored defects

Replicate 3 reproduces exactly the scored defect set of structured replicate 1:

1. `R10` (Clear): declining the optional second hand planting remains in `plant_second` instead of advancing to reveal;
2. `R16`, `R17` (Clear): unequal multi-card trade bundles cannot be proposed atomically;
3. `R22`, `R24` (Clear): owners cannot select arbitrary planting order for staged/revealed cards;
4. `R23` (Human Decision): the same ordering limitation breaks the approved free phase-three player order.

Unlike replicate 2, `R04` passes in 0.20 seconds and no scenario times out.

## Independent review

All three Judges converge on four major groups:

- missing unequal multi-card trade proposals;
- missing owner-selected staged-card order;
- depletion/recycling detected one draw too late;
- leakage of deeper opponent hand identities through legal actions or pending proposals.

One Judge rates the depletion boundary Critical; the others rate it Major.

## Material assumption

The implementation explicitly records `A-01`: it chooses one-card offers instead of exposing all source-legal multi-card bundles. This contradicts the structured supplement's requirement that a trade may contain any positive number of cards. The failure is therefore model-side, not a remaining source gap.

## Interpretation

Replicate 3 is safer than replicate 2 because it avoids the exponential action-space crash, but it is not a new best result: its scenario result equals replicate 1, and its Judge mean lies between replicates 1 and 2. Across three exact generations, Clear scores are 33/38, 35/38 and 33/38; Human Decision is 3/4 every time. At `n=3`, this remains descriptive evidence of generation variance rather than a causal estimate.
