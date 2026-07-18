---
name: bbimpl
description: Generate one isolated game implementation.
---

# BoardBench implementation

Example:

```text
/bbimpl game=conect subagents=on submodel=openai-codex/gpt-5.6-sol subthinking=low
```

Use the argument and subagent policy from `/bb`.

## Preconditions

Require the archived source condition (primary rulebook plus optional component appendix), `inputs/games/<slug>/rulefacts.md` with `status: approved`, and `checks/scenarios/<slug>.json`. Return to `bbedge` for material unresolved rules or source conflicts.

## Implementation

1. Read `inputs/prompts/rulebook_to_python.txt`.
2. Create an isolated temporary workspace containing every document in the assigned source condition, a short source manifest identifying publisher versus user-authored material, the prompt, and `generation/agentic_self_check.py`. Approved evaluator facts, repository checks, and scenario expectations remain hidden from the implementer.
3. Native Codex implementation generation defaults to `gpt-5.6-sol:low`. If Pi subagents are enabled, launch one `implementer` Agent as the only writer. Pass explicit child model/thinking exactly. Otherwise omit those fields so it inherits, or choose only a demonstrably weaker setting than the parent.
4. Require the Agent to create `implementation.py`, audit every supplied rulebook section/named rule into `rule_coverage.md`, and run `python -m py_compile implementation.py` plus `python agentic_self_check.py` against the actual file. New main-study runs use the versioned protocol that also requires schema-valid `assumptions.json` containing only material source assumptions, their alternatives, selected behavior, and affected mechanics. A model setting named `agentic` is not evidence by itself.
5. Independently rerun the same self-check and validate required audit artifacts without comparing them to hidden evaluator expectations. If it fails, return only evaluator-neutral technical output to the same isolated implementation workflow for at most two repair rounds. Never reveal cited scenarios.
6. Preserve every raw response/event/usage record, `rule_coverage.md`, any required `assumptions.json`, and an agentic-evidence JSON file containing protocol, commands, repair count, and final gate status. Copy `implementation.py` to the requested output path.
7. Remove the workspace.

## Checks

Run through the `boardbench` Conda environment and keep groups separate:

1. technical 01–04;
2. robustness 05;
3. interface 06;
4. rulebook scenarios.

Do not combine them into a correctness score. Only technical/API/self-check defects may enter the blind repair loop. Changed rule interpretations return to the user. Do not call a run agentic unless the actual implementation file was written, tested, and passed the independent gate.

End with paths, grouped results, parent and child model/thinking, assumptions, and the next `/bbeval` command.
