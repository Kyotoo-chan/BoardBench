# Attempt 1

1. Open question/material assumption: the rulebook does not specify the initial dealer; implementation selects player 0.

2. Files changed:

- `implementation.py`
- `rule_coverage.md`
- `assumptions.json`

3. Validation:

- `python -m py_compile implementation.py` — passed
- `python agentic_self_check.py` — passed: `agentic-self-check OK states=300 actions=1074`
- Additional contract check: `profile-fixture-self-check OK`
