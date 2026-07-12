---
name: bbeval
description: Evaluate an agentic BoardBench implementation in separate evidence groups, optionally with requested reviewer subagents and model settings.
---

# BoardBench evaluation

Example:

```text
/skill:bbeval game=conect subagents=on submodel=openai-codex/gpt-5.6-sol subthinking=low
```

Use the argument and subagent policy from `/skill:bb`.

## Process

1. Resolve one matching `outputs/<slug>_*_ag.py` and verify the archived rulebook hash.
2. Run technical 01–04, robustness 05, interface 06, and cited scenarios in the `boardbench` Conda environment.
3. Read `prompts/llm_judge_review.md`.
4. When subagents are enabled, launch fresh read-only `rulereviewer` Agents. Pass explicit child settings exactly; otherwise inherit or choose only demonstrably weaker settings. Reviewers receive rulebook, approved facts, and code, but no prior reviews or scores.
5. Require page, quote, code location, expected behaviour, and actual behaviour for major/critical findings.
6. Save raw reviews as `outputs/<stem>_judge_<label>.md` and grouped results as `outputs/<stem>_checks.txt`.
7. Report agreement, disagreement, uncertainty, and uncovered rules separately.

Run OpenSpiel only with explicit `openspiel=true`; label it secondary reference agreement. Do not create plots or aggregate unlike evidence.

End with confirmed defects, disputed findings, new regression scenarios, and parent/child model and thinking actually used.
