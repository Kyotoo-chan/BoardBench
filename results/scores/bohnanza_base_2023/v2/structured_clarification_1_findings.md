# Bohnanza V2 structured clarification 1 — adapted successor

- Post-evaluation methodology adaptation, not an independent replicate and not a best-of replacement.
- Packet: byte-identical publisher PDF plus one user-approved experimenter supplement containing four digital gap decisions and a balanced whole-game source-derived checklist. No claims, scenarios or prior results were model-visible.
- Model/prompt/contract/profile remain identical to the prior V2 conditions.
- Agentic gate: PASS; one generation call; no repairs.
- Technical gate: 4/4.
- Robustness: 100/100.
- Interface: 847,456/847,456.
- Player counts: 5/5.
- Clear-basis scenarios: 33/38.
- Human-decision-basis scenarios: 3/4.
- Evaluated coverage: 42/42.
- Neutral Judges: 0.74 / 0.68 / 0.72; mean 0.713, sample SD 0.031.

The broader delivery materially improves on both narrow-emphasis runs (30/38 Clear and at most 3/4 Human Decision) and removes their scoring/setup/end-game failures. It returns to the Original's 33/38 Clear rate while producing a different defect set and a higher Judge signal than the Original (0.713 versus 0.643).

Remaining scored defects:

1. `R10`: after declining a second optional hand planting, the implementation remains in `plant_second` instead of advancing to reveal;
2. `R16`, `R17`: legal-action enumeration still omits unequal multi-card trades, despite internal transition code accepting some handcrafted proposals;
3. `R22`, `R24`: only the first staged/revealed card can be selected, so owners cannot choose planting order;
4. `R23`: the same planting-order defect prevents the approved free inter-player phase-three order case.

All three Judges independently confirm three Major groups: missing multi-card trades in the enumerated action surface, no owner-selected staged-card order, and deeper opponent hand identities leaked through legal trade actions. Invalid partner handling is a repeated Minor finding.

Interpretation: explicit balanced context helps more than narrow post-hoc emphasis, but context alone does not guarantee contract-complete implementation. The remaining errors are implementation/action-enumeration failures despite explicit source-derived guidance, not evidence that those rules were absent.
