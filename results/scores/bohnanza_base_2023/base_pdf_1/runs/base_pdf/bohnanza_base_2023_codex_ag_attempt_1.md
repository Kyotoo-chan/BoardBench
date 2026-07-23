Open questions/material assumptions: deterministic player 0 starts; deck depletion is counted when its last card is drawn; third depletion during phase 4 ends immediately. Details are recorded in `assumptions.json`.

Files changed:

- `implementation.py`
- `rule_coverage.md`
- `assumptions.json`

Validation:

- `python -m py_compile implementation.py` — passed
- `python agentic_self_check.py` — passed: `states=300 actions=8980`
- `python profile_fixture_self_check.py` — passed: `profile-fixture-self-check OK`