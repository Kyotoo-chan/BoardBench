---
name: bbimpl
description: Implement one BoardBench game agentically from approved rule facts, optionally using a requested subagent model and thinking level.
---

# BoardBench implementation

Example:

```text
/skill:bbimpl game=conect subagents=on submodel=openai-codex/gpt-5.6-sol subthinking=low
```

Use the argument and subagent policy from `/skill:bb`.

## Preconditions

Require archived rulebook, `inputs/games/<slug>/rulefacts.md` with `status: approved`, and `checks/scenarios/<slug>.json`. Return to `bbedge` for material unresolved rules.

## Implementation

1. Read `prompts/rulebook_to_python.txt`.
2. Create an isolated temporary workspace containing only the rulebook, approved facts, prompt, and empty output directory. Do not expose repository checks or scenario expectations.
3. If subagents are enabled, launch one `implementer` Agent as the only writer. Pass explicit child model/thinking exactly. Otherwise omit those fields so it inherits, or choose only a demonstrably weaker setting than the parent.
4. Preserve its raw response and copy the final module to `outputs/<slug>_<backend>_ag.py`; save the response as the matching `.md`.
5. Remove the workspace.

## Checks

Run through the `boardbench` Conda environment and keep groups separate:

1. technical 01–04;
2. robustness 05;
3. interface 06;
4. rulebook scenarios.

Do not combine them into a correctness score. Do not run OpenSpiel unless requested. Implementation defects may return to the same Agent; changed rule interpretations return to the user.

End with paths, grouped results, parent and child model/thinking, assumptions, and the next `/skill:bbeval` command.
