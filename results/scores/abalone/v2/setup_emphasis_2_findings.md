# Abalone V2 setup-emphasis replicate 2 findings

- Exact pre-registered replicate of `v2_setup_emphasis_1`; model-facing packet hashes are byte-identical.
- Generation: `gpt-5.6-sol`, thinking `low`; one call, no repairs.
- Agentic gate, technical gate, robustness, interface and player counts: PASS.
- Technical checks: 4/4.
- Robustness: 100/100.
- Interface: 5,704,536/5,704,536.
- Player counts: 3/3.
- Clear-basis scenarios: 33/33.
- Human-decision-basis scenarios: 4/5.
- Evaluated coverage: 38/38.
- Clear claim mapping/evaluation: 33/33.
- Neutral Judges: 0.90 / 0.87 / 0.84; mean 0.870, sample SD 0.030.

Evidence groups are not combined into a correctness score.

## Scored failure

`ABAL-R19-forced-pass-only-with-no-move` fails exactly as in setup-emphasis replicate 1: a nonterminal state with no legal movement exposes zero actions instead of the approved single forced pass.

The generated assumptions make the omission explicit. Assumption `A-03` selects: “Do not implement passing, repetition draws, turn limits, or clocks; play ends only when a player has pushed out six opposing marbles.” The publisher packet does not decide forced pass, and the approved Human Decision remained hidden from both emphasis generations. Thus the repeated failure is an implementation/decision mismatch under the evaluator, not a publisher-clear contradiction.

## Confirmed unscored Judge candidate

All three neutral Judges also identify group-order aliases at the public action parsers. A post-judge deterministic replay confirms that:

- one legal two-marble action serializes group `[-1,-3; 0,-4]`;
- reversing that group produces a different serialized action;
- both actions are accepted;
- both produce the identical successor state.

`ABAL-R37` still passes because the frozen scenario checks uniqueness among emitted `legal_actions`; it does not probe parser-created aliases. The replay is stored at `raw/setup_emphasis_2_judge_candidate_replays.json`. Because it was proposed after the frozen suite ran, it remains unscored and does not retroactively change 4/5 Human-Decision scenarios.

## Replication interpretation

Both exact setup-emphasis generations produce the same configured outcome:

- Figure-1 setup: PASS;
- clear basis: 33/33;
- Human-Decision basis: 4/5;
- forced pass: FAIL.

This recurrence makes the first regression less plausibly a one-run anomaly, but `n=2` still cannot establish that setup emphasis causes the omission. The original PDF-only run independently invented a forced-pass assumption; both emphasis runs independently omitted or rejected it even though no condition showed the approved Human Decision to the model.

Replicate 1 is retained. Replicate 2 is the pre-declared final successor, not a best-of replacement.
