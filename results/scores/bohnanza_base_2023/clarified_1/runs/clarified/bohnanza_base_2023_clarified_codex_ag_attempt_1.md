1. Open material assumptions: player 0 starts; cards are dealt clockwise one-at-a-time; tie-break distance is measured clockwise after the start player. Narrow packet clarifications were applied as documented.

2. Files changed:

- `implementation.py`
- `rule_coverage.md`
- `assumptions.json`

3. Validation:

- `python -m py_compile implementation.py` — passed
- `python agentic_self_check.py` — passed: `states=300 actions=11441`
- `python profile_fixture_self_check.py` — passed: `profile-fixture-self-check OK`