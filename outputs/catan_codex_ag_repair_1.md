Changed files:

- `assumptions.json` — removed A-01.
- `rule_coverage.md` — marked different-resource maritime exchange as source-clear.

Outcomes:

- `python -m py_compile implementation.py` — passed
- `python agentic_self_check.py` — passed; 300 states, 2,959 actions
- `python profile_fixture_self_check.py` — passed