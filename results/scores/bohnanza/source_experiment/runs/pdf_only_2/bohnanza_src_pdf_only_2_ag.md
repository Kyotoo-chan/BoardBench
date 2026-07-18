1. Open questions/material assumptions: third deck-exhaustion handling, off-turn harvest timing, and missing variant component data are documented in `assumptions.json`. The complete 4–5-player base condition is playable; incomplete variants fail explicitly.

2. Files changed:

- `implementation.py`
- `rule_coverage.md`
- `assumptions.json`

3. Validation:

- `python -m py_compile implementation.py` — passed
- `python agentic_self_check.py` — passed: `agentic-self-check OK states=300 actions=1556`