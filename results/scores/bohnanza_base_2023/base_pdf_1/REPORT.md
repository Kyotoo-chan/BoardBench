# Bohnanza Base 2023 — run report

## Status

One accepted publisher-PDF-only generation and one neutral Judge completed. Two earlier generations were rejected before judging because preflight infrastructure was incomplete; they remain separately labelled and are not scored.

Accepted implementation: `runs/base_pdf/bohnanza_base_2023_codex_ag.py`

## Evidence groups

### Technical gate

- Checks 01–04: **4/4 pass**
- Required API: **9/9 pass**
- Canonical reachable-state and rare-fixture gates: pass
- Generation repairs: **0**

### Runtime robustness

- Random rollouts: **100/100 pass**
- Action-language roundtrips: **666338/666338 pass**

### Preregistered rule scenarios

- PASS: 23
- FAIL: 5
- CRASH: 3
- UNTESTABLE: 0
- Evaluated coverage: 31/31
- Raw pass fraction: 0.742

This preregistered result is retained unchanged, but it is representation-distorted. The adapter assumed a four-player default although `Game()` validly chose three players, checked the obsolete action argument `card` instead of profile field `bean`, treated a legal `pass` transition as invalid for an empty phase-one hand, failed to put a pending gift fixture into `trade_response`, imposed an unsupported received-card order, and ignored the action actor in one trade-authority check.

### Corrected post-hoc scenario replay

Rubric: `bohnanza-base-2023-posthoc-v2-2026-07-19`

- PASS: 30
- FAIL: 1
- CRASH: 0
- UNTESTABLE: 0
- Pass fraction: 0.968
- Coverage: 1.000

The remaining deterministic failure is real: two Gartenbohnen should pay two coins, but the implementation pays one.

### Independent Judge

- Score: **0.52**
- Confidence: high
- Critical: 1
- Major: 3

Judge findings:

1. **Critical:** third depletion is detected one draw too late, allowing an extra phase/turn and potentially changing the winner.
2. **Major:** phase three handles only the active player's received cards and does not permit each affected player to choose the full planting order.
3. **Major:** generated legal trade bundles are artificially capped, excluding valid unequal multi-card trades.
4. **Major:** Gartenbohne payouts are shifted downward.

The Judge therefore identifies serious defects that the corrected 31-scenario suite does not cover. The 30/31 post-hoc pass result must not be interpreted as 97% rule fidelity.

## Method findings

1. The simpler complete rulebook removed the old source-inventory confusion: the accepted implementation and evaluator agree on 104 cards, eight bean types, and 3/4/5-player field counts.
2. Canonical Contract-v2 removed implementation-representation crashes once the evaluator's player-count assumption was corrected.
3. Preflight itself failed twice before the accepted run:
   - attempt 1 exposed that the neutral gate omitted `render`;
   - attempt 2 exposed that the runner supplied the wrong task prompt.
4. The preregistered adapter still contained six evaluator assumptions/errors, despite its infrastructure probe reporting all fixtures representable.
5. The independent Judge found temporal and action-space gaps absent from the scenario suite. Uniform representation solves test access, not scenario completeness.

## Interpretation

For this run, the clean complete base rulebook substantially reduces source ambiguity, but it does not eliminate implementation failures. The dominant remaining issues are model translation errors (depletion timing, multi-player phase-three control, payout encoding), action-space truncation, missing deterministic scenarios, and evaluator workflow defects. This supports keeping source quality, implementation quality, evaluator validity, and coverage as separate evidence groups.
