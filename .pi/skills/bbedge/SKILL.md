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

Require exactly one primary `inputs/game_rules.pdf` or `.txt`. If that primary explicitly delegates rules to an official companion, optionally accept one matching `inputs/game_almanac.pdf` or `.txt`; verify edition/article/title markers before assigning it and never silently mix editions. Optionally accept one user-authored `inputs/game_components.pdf`, `.txt`, or `.json` that only identifies and inventories physical components. Ask for a short slug if `game=` is missing. Use only the assigned supplied sources; render PDF pages freshly and preserve stable JSON Pointers for JSON evidence.

Record the primary as `publisher_rulebook`, an assigned matching companion as `publisher_companion`, and the appendix as `user_observation`. A companion is part of a publisher-only condition only when its match and explicit dependency are recorded. A user appendix makes the condition visibly augmented and may support hard component inventory/setup expectations, but it may not silently define or override gameplay rules.

## Process

1. Hash and archive each assigned source separately at `inputs/games/<slug>/game_rules.<ext>`, optional `game_almanac.<ext>`, and optional `game_components.<ext>`. If an existing file has another hash, ask for an edition label instead of overwriting it. Record a source register with ID, role, authorship, hash, edition-match evidence, and condition label; retain rejected candidates under explicit non-assigned labels.
2. Read `inputs/prompts/rulebook_to_scenarios.md` and `checks/scenarios/README.md`.
3. When subagents are enabled, launch `ruleanalyst` and `edgereviewer` in parallel background calls in one turn. Their prompts must be self-contained and read-only.
4. Build a cited rule/assumption register in `rulefacts.md`. Every citation names its source ID. Classify every item as `clear`, `human_decision`, `ambiguous`, or `not_testable`. For every card game, record the cited total and per-type card inventory and require a setup scenario that checks those exact counts wherever observable.
5. Compare the sources explicitly. Surface every contradiction with both quotes/pages, explain why they conflict, and ask the user to choose the interpretation and rationale; no source has automatic precedence.
6. Ask the user through `ask_user_question` only about **material** assumptions: choices that alter component inventory, legal actions, state transitions, private information, elimination, terminal results, or scoring. For each question show the evidence, alternatives, recommended interpretation, and affected scenarios. Never silently choose.
7. Stop at an approval gate. Do not write a hard expected result for an unresolved material assumption.
8. After agreement, write `inputs/games/<slug>/rulefacts.md` with `status: approved`, stable fact IDs, the source register and hashes, dated decisions with rationale, corrections, conflicts, and unresolved questions.
9. Write version-3 cases to `checks/scenarios/<slug>.json`. Every scored case needs fact IDs, source ID, a positive PDF `page` or RFC 6901 `json_pointer`, direct source evidence in `quote`, basis (`clear` or `human_decision`), exact starting state or public trace, selected action, expected observable transition, and whether it is deterministic or exploratory. When an expectation genuinely combines pages or assigned sources, add validated `supporting_sources` objects instead of pretending one citation proves the whole result.
10. Add an evaluator-only `checks/scenario_adapters/<slug>.py` when rare states cannot be reached reliably through the public API. The adapter may construct and observe state but must not contain the expected rule result.
11. Review temporal boundaries explicitly: pending reactions, intermediate choice phases, chance resolution, and the point at which an expectation is checked. `UNREACHED` and `UNTESTABLE` are never hard failures.
12. Show the complete assumption and scenario matrix to the user before scoring. Record hashes for run provenance; later corrections update the current workflow while Git preserves prior results.

Do not implement game code. End with approved facts, unresolved decisions, current paths/hashes, subagent model/thinking actually used, and the next `/bbimpl` command.
