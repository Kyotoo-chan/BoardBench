# Isolated implementation prompt

Model: `openai-codex/gpt-5.6-sol`
Thinking: `low`
Protocol: `agentic-v2.2`

The implementer received only:

- `game_rules.pdf` and four fresh page renders;
- `TASK.txt` copied from `inputs/prompts/rulebook_to_python.txt`;
- evaluator-neutral `agentic_self_check.py`.

It did not receive approved rule facts, evaluator scenarios, checks, prior reviews, scores, or other repository files.

## Wrapper instruction

Read `TASK.txt` completely and follow it. Use only `game_rules.pdf` and freshly rendered `rulebook-page-1.jpg` through `rulebook-page-4.jpg` as game-rule evidence. Work only inside this workspace. Create the actual files `implementation.py`, `rule_coverage.md`, and schema-valid `assumptions.json`. Audit every supplied section and named rule. Run exactly `python -m py_compile implementation.py` and `python agentic_self_check.py`, repair all failures, and report exact outcomes. Do not modify `agentic_self_check.py`. If the source is incomplete, make only the smallest explicit material assumption and record it in `assumptions.json`.
