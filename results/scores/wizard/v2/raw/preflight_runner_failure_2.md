# Attempt 1

Open material assumptions: fixed starting dealer (player 0), clockwise numeric seating, and first ordinary card establishing suit after Fool-led colorless specials.

Files changed:

- `implementation.py`
- `rule_coverage.md`
- `assumptions.json`

Validation:

- `python -m py_compile implementation.py` — passed
- `python agentic_self_check.py` — passed: `states=300 actions=1090`
- `python profile_fixture_self_check.py` — passed: `profile-fixture-self-check OK`
