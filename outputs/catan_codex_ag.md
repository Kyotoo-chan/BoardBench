# Attempt 1

Open material assumptions:

- Strict roll → trade → build sequence selected.
- Victory checked after each committed active-player action.
- Longest Road is not automatically awarded because branching-path resolution is underspecified.

Files changed:

- `implementation.py`
- `rule_coverage.md`
- `assumptions.json`

Validation:

- `python -m py_compile implementation.py` — passed
- `python agentic_self_check.py` — passed: `states=300 actions=2816`
- `python profile_fixture_self_check.py` — passed: `catan-v2-profile-fixture-self-check OK`
