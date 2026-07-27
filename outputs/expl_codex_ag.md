# Attempt 1

Open material assumptions: NÖ! reaction order, chained Angriff behavior, eliminated-card destination, empty-hand Wunsch resolution, and numeric returns. All are documented in `assumptions.json`.

Files changed:

- `implementation.py`
- `rule_coverage.md`
- `assumptions.json`

Validation:

- `python -m py_compile implementation.py` — passed
- `python agentic_self_check.py` — passed: `states=300 actions=1375`
- `python profile_fixture_self_check.py` — passed: `profile-fixture-self-check OK`
