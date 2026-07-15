# Original-PDF agentic rerun

This diagnostic reruns the unchanged canonical PDF after hardening generation. It does **not** replace or rewrite experiment 01. The original remains a historical pilot; the rerun is experiment 07 (`1cd9a33`). With one run per protocol, differences cannot be attributed uniquely to agentic validation rather than ordinary generation variance.

## Why the original was not replaced

Experiment 01 was launched through agentic-capable Codex infrastructure, but its event log shows only a directory listing and `ast.parse('x=1')`. The 610-line final module was not written, compiled, executed, or repaired inside the agent session. Replacing that commit would erase evidence needed to diagnose the workflow.

The rerun required the agent to create `implementation.py`, run the actual compiler and evaluator-neutral action-closure self-check, and pass the same gate independently. The command log confirms:

```text
python -m py_compile implementation.py
python agentic_self_check.py
agentic-self-check OK states=300 actions=1237
```

The agent additionally ran multi-player/seed rollouts. No repair call was needed.

## Comparison

| Evidence | Original PDF pilot | Agentic PDF rerun |
|---|---:|---:|
| Technical 01–04 | pass | pass |
| Runtime robustness | 0.000 | 1.000 |
| Interface | 0.972 | 1.000 |
| Clear printed rules | 7/10 | 9/10 |
| Human decisions | 5/7 | 6/7 |
| Scenario coverage | 17/17 | 17/17 |
| Judge mean (n=3) | 0.567 | 0.760 |
| Judge SD | 0.023 | 0.020 |
| Code lines | 610 | 386 |
| Proven in-agent self-check | no | yes: 300 states / 1,237 actions |

The rerun removes the Cat-title action parser crash and passes all technical, robustness, and interface checks.

## Remaining rerun findings

All three fresh corrected judges independently identified the same two issues, and evaluator `expl-v2.1` reproduces both:

1. **R10, human decision:** the implementation explicitly allows a player to decline Defuse. The printed German uses “kannst”; BoardBench's mandatory-use behavior is an approved human adjudication, so this is an adjudication mismatch rather than a contradiction of an unambiguous printed rule.
2. **R12, clear/action-order result:** a five-card combination is unavailable when the discard was initially empty, so it cannot retrieve one of its own newly discarded components. This is a remaining implementation defect.

Final deterministic result:

```text
PASS=15 FAIL=2 CRASH=0 UNREACHED=0 UNTESTABLE=0
clear rules:      9/10
human decisions:  6/7
coverage:          100%
```

## Evaluator adaptation discovered during the rerun

The first evaluator pass could score only R01–R02 because the new implementation used an immutable tuple-based `GameState`, while the Exploding-Kittens fixture adapter supported only mutable list-based hands. This was an evaluator limitation, not an implementation failure.

Both stages are retained:

- `outputs/*_scenarios_initial.*` in experiment 07 records the original `2 PASS / 15 UNTESTABLE` result against evaluator snapshot `16c93b2`.
- `expl_pdf_r2_scenarios_v2_1.json` records the generalized immutable-state adapter result.

The adapter now constructs equivalent list-, counter-, tuple-, mutable-, and frozen-dataclass states without embedding expected rule outcomes. Scenario results also retain suite, adapter, and code hashes.

## Workflow changes retained for future runs

- An actual workspace file is mandatory; a fenced final code block is insufficient.
- `py_compile` and action-closure self-check commands must appear in raw agent events.
- The harness independently repeats both gates.
- At most two blind technical repair rounds are allowed; cited scenarios remain hidden.
- Future agents must produce `rule_coverage.md`, mapping every supplied section and named rule/card/combination to code, a source-only probe, and assumptions. This addresses the rerun's remaining unreported five-card gap without revealing benchmark expectations.
- Windows Codex `workspace-write` degraded to read-only. The failed three-call attempt is preserved under `failed_readonly_attempt/`; subsequent implementation workspaces are ephemeral and outside the repository.

## Interpretation

The rerun supports three limited conclusions:

1. The original parser crash was not inevitable and is consistent with inadequate in-agent validation or generation variance.
2. Real agentic compilation/action probes materially improve technical confidence but do not prove rule fidelity.
3. Static judges and deterministic fixtures are still required: the agent passed 1,237 generic action transitions while retaining a rule-level five-card omission.

A format claim still requires at least three newly generated PDF and three newly generated faithful-TXT implementations under one frozen final protocol.

## Resources

The successful rerun used four calls (one implementation and three judges): 651,429 input tokens, 504,832 cached input tokens, 24,531 output tokens, 12,649 reasoning tokens, and 770.376 summed provider seconds. The failed read-only infrastructure attempt is reported separately in `metrics.json` and is not part of the experiment score.
