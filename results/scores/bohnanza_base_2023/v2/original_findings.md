# Bohnanza Base Game 2023 V2 original-condition findings

- Agentic gate: PASS (`v2_original_1`, one generation call, no repairs).
- Technical gate 01–04: 4/4 PASS.
- Runtime robustness: 100/100.
- Interface: 800,371/800,371 action-name roundtrips PASS.
- Player counts: 3, 4 and 5 playable; 2 and 6 rejected (5/5).
- Clear-basis scenarios: 33/38.
- Human-decision-basis scenarios: 4/4.
- Evaluated coverage: 42/42.
- Clear claim mapping/evaluation: 80/81 plus the explicit `BOHN-C-HARVEST-ANYTIME` coverage exception.
- Neutral Judges: 0.68 / 0.70 / 0.55; mean 0.643, sample SD 0.081.

Confirmed scored defects:

1. `BOHN-R16` and `BOHN-R17` expose one clear trade defect: legal unequal multi-card bundles cannot be proposed atomically; the implementation emits only single-card offers and requests.
2. `BOHN-R30` exposes a clear Garden-bean payout defect: two Garden beans pay one coin instead of the printed two.
3. `BOHN-R33` exposes a clear Soy-bean payout defect: three Soy beans pay two coins instead of one.
4. `BOHN-R40` exposes a clear end-timing defect: after the third depletion in phase-two reveal and completion of phases two and three, the implementation remains nonterminal until a forbidden phase-four draw action is taken.

Judge-only regression candidates (not added retroactively to the frozen score):

- all three Judges also identify delayed first/second discard recycling when the final requested card empties the pile;
- one Judge identifies deeper opponent hand identities leaked through generated trade actions despite the observation payload hiding them;
- imported-state strictness and phase-three decision metadata receive minor findings.

All five scored failures concern publisher-clear rules. Every approved human decision passes, so the scored evidence does not identify a source-gap clarification target. A second condition, if requested, must be labelled a clear-rule emphasis rather than a gap clarification.
