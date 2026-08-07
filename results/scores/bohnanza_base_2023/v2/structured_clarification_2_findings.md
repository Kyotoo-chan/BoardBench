# Bohnanza V2 structured clarification 2 — exact replicate

- Exact pre-registered replication of structured clarification 1; no best-of replacement.
- Initial model packet is byte-identical to replicate 1.
- Agentic gate: PASS after one pre-evaluation contract repair.
- Technical gate: 4/4.
- Robustness: 100/100.
- Interface: 1,395,514/1,395,514.
- Player counts: 5/5.
- Clear-basis scenarios: 35/38.
- Human-decision-basis scenarios: 3/4.
- Evaluated coverage: 42/42.
- Neutral Judges: 0.47 / 0.55 / 0.55; mean 0.523, sample SD 0.046.

## Scored defects

1. `R04` (Clear, CRASH): bounded play becomes computationally intractable because `legal_actions()` materializes every non-empty offered subset against every requested subset. The frozen full-suite process exceeded 1,800 seconds and froze the host. In isolated low-priority compatibility execution, Original and structured replicate 1 pass R04 in 0.17/0.30 seconds; replicate 2 still exceeds 15 seconds.
2. `R10` (Clear, FAIL): declining the optional second hand planting remains in `plant_second` instead of advancing to reveal.
3. `R14` (Clear, FAIL): after the four-phase sequence, the implementation remains in `plant_received` instead of reaching draw.
4. `R23` (Human Decision, FAIL): the approved free phase-three player order also remains stuck in `plant_received` instead of reaching draw.

All other scenario groups pass, including the multi-card trade and arbitrary staged-card selection cases that failed in replicate 1.

## Independent review

The three official medium-thinking Judges converge on:

- exponential trade-action materialization, rated Critical by all;
- depletion/recycling detected one draw too late;
- leakage of deeper opponent hand identities through legal trade actions;
- inability of a non-active player to give a one-way gift to the active player.

The first low-thinking judge invocation was an evaluator-setting error. Its three reviews remain archived and unscored; the frozen medium-thinking judge setting was rerun without changing the implementation.

## Interpretation

Replicate 2 improves scenario Clear pass rate over both Original and structured replicate 1, but introduces a severe action-space performance failure and receives a substantially lower Judge signal. Thus a second run is not inherently “cooked”; fresh generation variance can improve covered cases while worsening an uncovered or weakly bounded implementation property. With only two structured runs, this is descriptive evidence rather than a causal estimate.
