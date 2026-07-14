---
name: bbedge
description: Extract cited rules and agree edge cases.
---

# BoardBench edge cases

Example:

```text
/bbedge game=conect subagents=on submodel=openai-codex/gpt-5.6-sol subthinking=low
```

Use the argument and subagent policy from `/bb`. If child model/thinking is not explicit, omit those `Agent` fields unless choosing a demonstrably weaker setting than the parent.

## Input

Require exactly one active `inputs/game_rules.pdf` or `.txt`. Ask for a short slug if `game=` is missing. Use only this rulebook and fresh rendered pages.

## Process

1. Hash and archive the rulebook at `inputs/games/<slug>/game_rules.<ext>`. If an existing file has another hash, ask for an edition label instead of overwriting it.
2. Read `prompts/rulebook_to_scenarios.md` and `checks/scenarios/README.md`.
3. When subagents are enabled, launch `ruleanalyst` and `edgereviewer` in parallel background calls in one turn. Their prompts must be self-contained and read-only.
4. Build a cited rule/assumption register in `rulefacts.md`. Classify every item as `clear`, `human_decision`, `ambiguous`, or `not_testable`.
5. Ask the user only about **material** assumptions: choices that alter legal actions, state transitions, private information, elimination, terminal results, or scoring. For each question show the quote, alternatives, recommended interpretation, and affected scenarios. Never silently choose.
6. Stop at an approval gate. Do not write a hard expected result for an unresolved material assumption.
7. After agreement, write `inputs/games/<slug>/rulefacts.md` with `status: approved`, stable fact IDs, rulebook hash, dated decisions, corrections, and unresolved questions.
8. Write version-3 cases to `checks/scenarios/<slug>.json`. Every scored case needs fact IDs, page, direct quote, basis (`clear` or `human_decision`), exact starting state or public trace, selected action, expected observable transition, and whether it is deterministic or exploratory.
9. Add an evaluator-only `checks/scenario_adapters/<slug>.py` when rare states cannot be reached reliably through the public API. The adapter may construct and observe state but must not contain the expected rule result.
10. Review temporal boundaries explicitly: pending reactions, intermediate choice phases, chance resolution, and the point at which an expectation is checked. `UNREACHED` and `UNTESTABLE` are never hard failures.
11. Show the complete assumption and scenario matrix to the user and freeze hashes only after approval. Later corrections create a new rubric version; never rewrite historical results.

Do not implement game code. End with approved facts, unresolved decisions, frozen paths/hashes, subagent model/thinking actually used, and the next `/bbimpl` command.
