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
2. Read `prompts/rulebook_to_scenarios.md`.
3. When subagents are enabled, launch `ruleanalyst` and `edgereviewer` in parallel background calls in one turn. Their prompts must be self-contained and read-only.
4. Synthesize and classify each item as `clear`, `ambiguous`, or `not testable`.
5. Discuss only material ambiguities with the user; never silently choose.
6. After agreement, write `inputs/games/<slug>/rulefacts.md` with `status: approved`, rulebook hash, decisions, and unresolved questions.
7. Write 5–10 strong public-API cases to `checks/scenarios/<slug>.json`, each with page and quote.

Do not implement code. End with approved facts, unresolved decisions, paths, subagent model/thinking actually used, and the next `/bbimpl` command.
