---
name: bbeval
description: Evaluate technical quality and rule fidelity separately.
---

# BoardBench evaluation

Example:

```text
/bbeval game=conect subagents=on submodel=openai-codex/gpt-5.6-sol subthinking=low
```

Use the argument and subagent policy from `/bb`.

## Process

1. Read `checks/scenarios/README.md`, resolve one matching generated module, and verify the archived rulebook plus frozen rubric hashes. A changed fact, scenario, adapter, runner, or judge prompt is a new evaluator version.
2. Run technical 01–04, robustness 05, interface 06, and cited scenarios in the `boardbench` Conda environment.
3. Scenario results must be reported as `PASS`, confirmed `FAIL`, `CRASH`, `UNREACHED`, or `UNTESTABLE`. Compute fidelity only over `PASS+FAIL+CRASH` and report evaluated coverage separately. Never convert `UNREACHED` or `UNTESTABLE` into failure.
4. Prefer deterministic approved fixtures for material or rare rules. Random/search scenarios are exploratory unless they save and replay a deterministic trace. Resolve reaction and choice phases before checking a post-effect expectation.
5. Read `prompts/llm_judge_review.md`. Native neutral and persona Codex judges default to `gpt-5.6-sol:medium`; keep this separate from any advisory Pi subagent setting.
6. When subagents are enabled, launch exactly the requested fresh read-only `rulereviewer` Agents. Reviewers receive rulebook, approved facts, and code, but no checks, prior reviews, scores, or variants.
7. Require fact ID, evidence type (`rule_quote` or `human_decision`), page, quote, code location, expected behaviour, and actual behaviour for major/critical findings. Unsupported issues are questions, not penalties.
8. Save every raw review. Main reporting uses three neutral blind reviews and one `Judge mean (n=3)`; keep individual scores and sample SD as audit evidence. Optional rule-fidelity, ambiguity, and executable-systems persona reviews are separate cited evidence and are never averaged into the neutral mean or each other. Never combine judge evidence with technical, robustness, interface, or scenario evidence.
9. Repeated judge or persona findings are scenario candidates only. An LLM may propose a seed, trace, or fixture, but it does not decide deterministic pass/fail; replay, human approval, and a later rubric freeze are required first.
10. Report confirmed defects, evaluator failures, adjudication-dependent deviations, material assumptions, disagreement, uncertainty, and uncovered rule areas separately.
11. For repeated comparable runs, generate the per-rulebook JSON/Markdown result profile defined in `docs/rulebook_result_format.md` under `results/scores/<game>/<run>/`. Put optional images only under `results/plots/<game>/<run>/`. Report raw values, mean, sample SD, and coverage; never emit a combined correctness score.

Run OpenSpiel only with explicit `openspiel=true`; label it secondary reference agreement. Do not aggregate unlike evidence.

End with evaluator version/hashes, confirmed defects, disputed findings, new regression candidates, coverage, `Judge mean (n=...)`, and parent/child model and thinking actually used.
