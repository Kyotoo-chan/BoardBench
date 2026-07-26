# Attempt 1

1. Material assumptions/open questions:

- Initial dealer is selected using seeded chance.
- Clockwise order uses increasing player IDs modulo player count.
- After leading Fools, the first ordinary card establishes the led suit; a Wizard does not.
- No final-score tiebreak is defined, so returns preserve raw scores and ties.

2. Files changed:

- `implementation.py`
- `rule_coverage.md`
- `assumptions.json`

3. Validation:

- `python -m py_compile implementation.py` — passed.
- `python agentic_self_check.py` — passed: `agentic-self-check OK states=300 actions=1086`.
- Additional contract check: `python profile_fixture_self_check.py` — passed: `profile-fixture-self-check OK`.
