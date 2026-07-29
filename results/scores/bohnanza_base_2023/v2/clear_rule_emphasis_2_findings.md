# Bohnanza V2 clear-rule-emphasis run 2 — exact retained repeat

- Exact committed repeat of run 1: same PDF and emphasis bytes, model/thinking, prompt, contract, profile and evaluator.
- Agentic gate: PASS; one generation call; no repairs.
- Technical gate: 4/4.
- Robustness: 100/100.
- Interface: 976,727/976,727.
- Player counts: 5/5.
- Clear-basis scenarios: 30/38.
- Human-decision-basis scenarios: 2/4.
- Evaluated coverage: 42/42.
- Neutral Judges: 0.38 / 0.45 / 0.44; mean 0.423, sample SD 0.038.

The repeat is not evidence that run 1 was an isolated fluke. It again passes only 30/38 clear scenarios and performs worse on human decisions.

Targeted effects:

- unequal two-for-one multi-card trade scenarios `R16`/`R17`: PASS, although all Judges find an unscored cap at two cards per side;
- Soy payout `R33`: PASS;
- Garden payout `R30`: still FAIL (two Garden beans pay one instead of two);
- phase-two third-depletion transition reaches terminal automatically, but final harvest is omitted, so `R40` remains FAIL.

Confirmed scored defect groups:

1. three-player setup gives two fields instead of three (`R01`);
2. owners cannot choose their staged/revealed planting order (`R22`, `R23`, `R24`);
3. off-turn harvesting is unavailable at required stable boundaries (`R26`, `R27`);
4. Garden payout is wrong (`R30`);
5. terminal final harvest/scoring is omitted or wrong (`R40`, `R41`, `R42`).

All three Judges independently classify omitted final harvest as critical and confirm setup, Garden payout, capped trades, planting-order and off-turn-harvest defects. Judge-only repeated candidates include delayed recycling and private opponent-hand identities leaked through legal trade actions.
