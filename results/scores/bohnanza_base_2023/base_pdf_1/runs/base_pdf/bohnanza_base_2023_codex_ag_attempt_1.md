Open questions/material assumptions:

- Player 0 is the starting player because the rulebook does not specify selection.
- Trade proposals support one- or two-card offers and zero- or one-card requests.
- Terminal returns use winner-takes-1 utility, including the rulebook’s clockwise tie-break.

Files changed:

- `implementation.py`
- `rule_coverage.md`
- `assumptions.json`

Validation:

- `python -m py_compile implementation.py` — passed
- `python agentic_self_check.py` — passed: `agentic-self-check OK states=300 actions=2107`
- `python profile_fixture_self_check.py` — passed: `profile-fixture-self-check OK`