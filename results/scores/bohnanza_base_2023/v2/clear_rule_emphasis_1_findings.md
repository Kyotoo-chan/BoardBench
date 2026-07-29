# Bohnanza V2 clear-rule-emphasis run 1 — retained unjudged repetition evidence

This valid post-evaluation run is retained because it was fully generated and scenario-evaluated before the user predeclared an exact repeat. It is not replaced, repaired, or selected away. Neutral Judges were deliberately not run; therefore no standard Result Card is issued.

- Agentic gate: PASS; one generation call; no repairs.
- Technical gate: 4/4.
- Robustness: 100/100.
- Interface: 1,523,314/1,523,314.
- Player counts: 5/5.
- Clear-basis scenarios: 30/38.
- Human-decision-basis scenarios: 3/4.
- Evaluated coverage: 42/42.

The emphasis corrected every targeted Original mechanism: unequal multi-card trades (`R16`, `R17`), Garden payout (`R30`), Soy payout (`R33`), and the phase-two third-depletion terminal transition. `R40` remained failed only because a newly incorrect Red payout prevented its expected final coin.

Four new defect groups produced nine failed scenarios:

1. planting the optional second hand card does not advance from `plant_second` (`R10`);
2. a mismatched bean may directly trigger an implicit harvest-and-plant instead of requiring a separate harvest (`R12`);
3. received/revealed cards are forced in list order rather than owner-chosen order (`R22`, `R23`, `R24`);
4. the Red Bean meter uses incorrect thresholds, cascading into final harvest, winner and tiebreak failures (`R31`, `R40`, `R41`, `R42`).

This run cannot support a claim that the rulebook alone caused Original failures: its targeted improvements coexist with fresh clear-rule regressions.
