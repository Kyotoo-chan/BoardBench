# Exploding Kittens: paired agentic-v2 reruns

Each of the six original input conditions was generated once more with frozen protocol `agentic-v2`. Display names use `r2`; sequential experiment numbers 07–12 are only Git artifact snapshots. No pilot commit was replaced or rewritten.

All twelve frozen implementations were re-evaluated under the same post-hoc rubric `expl-v2.2`. Every scenario was evaluated for every implementation:

```text
UNREACHED=0
UNTESTABLE=0
coverage=100%
```

## What agentic-v2 guarantees

The implementation agent must create `implementation.py` in its isolated workspace and run:

```text
python -m py_compile implementation.py
python agentic_self_check.py
```

The harness repeats both checks independently and records commands, failures, and repairs. The self-check applies every legal action from 300 sampled states to a deep-copied state and checks API/action-name invariants. Cited rule scenarios remain hidden.

All six r2 runs passed the agentic gate on their first implementation call; none required a repair call. This is materially different from the pilot PDF call, which emitted code without running the generated module.

## Paired results

Clear printed-rule and human-decision scenarios remain separate evidence groups. Judge values are arithmetic means of three blind corrected reviews.

| Condition | Robustness pilot→r2 | Interface pilot→r2 | Clear rules pilot→r2 | Human decisions pilot→r2 | Judge mean pilot→r2 | Lines pilot→r2 |
|---|---:|---:|---:|---:|---:|---:|
| Original PDF | 0.000→1.000 | 0.973→1.000 | 7/10→9/10 | 5/7→6/7 | 0.567→0.760 | 610→386 |
| Faithful TXT | 1.000→1.000 | 1.000→1.000 | 10/10→8/10 | 4/7→3/7 | 0.773→0.693 | 656→365 |
| Anonymized | 1.000→1.000 | 1.000→1.000 | 10/10→10/10 | 3/7→1/7 | 0.753→0.890 | 692→333 |
| Omissions | 1.000→1.000 | 1.000→1.000 | 9/10→9/10 | 4/7→2/7 | 0.727→0.647 | 508→360 |
| False rules | 1.000→1.000 | 1.000→1.000 | 8/10→8/10 | 0/7→3/7 | 0.480→0.550 | 555→337 |
| Vague rules | 1.000→1.000 | 1.000→1.000 | 3/10→8/10 | 2/7→3/7 | 0.733→0.433 | 565→360 |

### Means across the six conditions

| Measure | Pilot mean | r2 mean | Relative change |
|---|---:|---:|---:|
| Runtime robustness | 0.833 | 1.000 | +20.0% |
| Interface | 0.996 | 1.000 | +0.4% |
| Clear-rule scenarios | 0.783 | 0.867 | +10.6% |
| Human-decision scenarios | 0.429 | 0.429 | 0.0% |
| Judge mean | 0.672 | 0.662 | −1.5% |
| Python lines | 597.7 | 356.8 | −40.3% |

The mean robustness improvement is entirely the removal of the original PDF parser crash; the other five pilots were already robust. Clear-rule fidelity improves on average, but not uniformly: PDF and vague improve strongly, faithful TXT becomes worse, and three conditions are unchanged. This is not evidence that agentic-v2 always improves rule fidelity.

## What became better

1. **Technical closure:** all six r2 modules pass 100/100 rollouts and every sampled action-name check.
2. **Compactness:** every r2 module is shorter; mean size falls from 598 to 357 lines.
3. **Clear-rule mean:** rises from 0.783 to 0.867.
4. **Original PDF:** the colon-bearing Cat action crash disappears and the deterministic clear-rule result improves from 7/10 to 9/10.
5. **Vague input:** clear-rule scenarios improve from 3/10 to 8/10, showing that the pilot was not a stable estimate of what the model can infer from that input.

## What did not become reliably better

- Human-adjudication fidelity is unchanged on average and moves in both directions.
- Judge means do not improve overall.
- Faithful TXT loses two clear scenarios in r2: Attack debt and chained Attack.
- All six r2 implementations permit declining Defuse, which conflicts with the approved human decision but is understandable from the printed “kannst”.
- Five of six r2 implementations fail the newly corrected five-card self-retrieval case.
- Five of six permit empty-handed Favor/pair targets; PDF r2 is the exception.

The generic self-check therefore does what it is designed to do—prevent crashes and API/action inconsistencies—but cannot certify game rules.

## Judge limitations remain visible

Two examples show why the judge mean cannot replace deterministic scenarios:

- Anonymized r2 receives `0.890` despite passing only `1/7` approved human-decision scenarios.
- Vague r2 receives a lower judge mean (`0.433`) than its pilot (`0.733`) even though clear deterministic scenarios improve from `3/10` to `8/10`.

The groups measure different evidence and remain unaggregated.

## Scenario patterns in r2

| Scenario area | r2 failures |
|---|---:|
| Mandatory Defuse (human decision) | 6/6 |
| Five-card retrieval of a newly discarded component | 5/6 |
| Empty-handed Favor target | 5/6 |
| Empty-handed pair target | 5/6 |
| Safe discard-Kitten handling | 4/6 |
| Kitten request by triple | 3/6 |
| Attack/debt clear-rule cases | condition-specific |

The false-rules r2 implementation still follows important planted errors, so the canonical evaluator continues to distinguish source-induced deviations from technical robustness.

## Evaluator revision during analysis

Early r2 scenario logs exposed additional adapter assumptions: new modules used immutable tuples, new anonymized labels, individually named Cat constants, and some implementations drew after an incorrect effect into a one-card fixture deck. Rubric `expl-v2.2` generalizes only state construction/observation and pads safe fixture decks so a wrong turn transition becomes `FAIL` rather than an incidental empty-deck crash. It does not encode the expected rule outcome.

This is still post-hoc evaluator development. The paired table is diagnostic evidence, not a preregistered main-study result.

## Code size and efficiency

Shorter code did not simply mean less model use:

| Resource mean | Pilot | r2 | Change |
|---|---:|---:|---:|
| Input tokens | 488,303 | 550,483 | +12.7% |
| Output tokens | 28,272 | 24,085 | −14.8% |
| Reasoning tokens | 13,278 | 12,508 | −5.8% |
| Provider seconds | 778.3 | 738.2 | −5.2% |

Successful r2 experiments total 3,302,896 input tokens, 2,621,952 cached input tokens, 144,509 output tokens, 75,046 reasoning tokens, and 4,428.983 summed provider seconds. The earlier Windows read-only failure and one retained capacity failure are reported separately from successful experimental calls.

## Interpretation and next protocol

These six pairs support a limited workflow conclusion:

> Enforced in-agent execution strongly improves technical confidence and produces much smaller modules, while rule-fidelity effects remain heterogeneous and need deterministic evaluation.

They do not isolate a causal protocol effect because each cell still contains only one pilot and one r2 generation. A main comparison needs at least three independent implementations per central condition.

Protocol `agentic-v2.1` adds a source-only `rule_coverage.md` audit for every section, named card, and combination. It was deliberately not mixed into this r2 series; all six r2 conditions use the exact frozen v2 prompt. A later repeated series can test whether the coverage audit reduces recurrent five-card and target-legality omissions.

## Files

- `r2_metrics.csv` / `r2_metrics.json` — all twelve paired rows and per-scenario statuses.
- `evaluation_v2_2/` — grouped check logs and machine-readable scenarios for all twelve implementations.
- `04_r2_rule_evidence.png` — paired clear/human scenario evidence.
- `05_r2_judge_means.png` — paired three-review means.
- `06_r2_code_lines.png` — paired module sizes.
- `pdf_rerun_metrics.json` — earlier PDF-only diagnostic snapshot.
- `failed_readonly_attempt/` — preserved infrastructure failure, not an experiment.
