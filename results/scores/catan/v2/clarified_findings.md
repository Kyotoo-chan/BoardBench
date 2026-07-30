# CATAN V2 source-gap clarification findings

- Independent post-Original source-gap intervention; it did not receive the clear-rule-emphasis artifact.
- Same publisher PDFs, model/thinking, prompt, contract and profile as Original.
- Added only four user-approved digital decisions: finite offer totals, submitted-discard escrow, mandatory adjacent victim choice, and different-resource maritime exchange.
- Agentic gate: PASS; one generation call; no repairs.
- Technical 4/4; robustness 100/100; interface 798,680/798,680; player counts 4/4.
- Evaluator r3: Clear 32/40; Human Decision 11/15; 55/55 scenarios and 113/113 named cases evaluated.
- Valid neutral-judge packet r2: 0.85 / 0.78 / 0.84; mean 0.823, sample SD 0.038.

## Intervention-target effects

1. **Finite trade bound (`R44`) passes.** Offer totals are capped by each side's public resource-hand size without using the partner's private resource identities.
2. **Submitted discard escrow (`R45`) passes.** A submitted resource is protected from Monopoly while the simultaneous discard remains pending.
3. **Different-resource maritime exchange (`R47`) passes.** Same-resource 4:1, 3:1 and 2:1 actions are absent.
4. **Mandatory Knight victim (`R46`) is not reached cleanly.** The implementation cannot play a development card before rolling, so the scenario fails before the clarified victim-choice behavior can be credited.

A valid Judge identifies a narrower escrow defect not covered by r3: `_available` reserves tentative selections before `submit_discard`, although only submitted selections should become escrow. This remains judge-only evidence and must not be retroactively added to this score.

## Clear regressions and defects

Eight clear scenarios fail in three main groups:

1. **Development cards cannot be played during the roll phase.** The legal-action interrupt branch excludes `phase == "roll"`. This single clear defect drives `R09`, `R24`, `R28`, `R31` and `R32`, and also contributes to human-decision failures `R40` and `R46`.
2. **Domestic-trade acceptance validates the proposer against the responder's holdings.** During `awaiting_response`, `p` is the partner, but the give-side affordability check also uses `p`. Valid offers therefore lack an accept action (`R10`, and human-decision `R11`).
3. **Opponent settlement construction does not recompute Longest Road.** Road placement recalculates it, but a newly built blocking settlement does not, causing `R19` and `R20`.

`R42` additionally exposes incorrect pending-stack resumption around development-card interrupts.

## Interpretation

The clarified run improves two previously failing targets (`R44`, `R45`), retains the already-passing different-resource behavior (`R47`), and cannot establish the Knight-victim target because a clear pre-roll defect blocks `R46`. It produces the strongest valid Judge mean but does **not** improve global deterministic fidelity. Compared on evaluator r3, Clear falls from Original 37/40 to 32/40 while Human Decision rises only from 10/15 to 11/15. Because this is one fresh generation rather than a patch or replicate, the differences are observed associations and do not isolate intervention effect from generation variance.
