# Attempt 1

Open material assumptions:

- Starting coordinates interpreted from Figure 1’s 14-marble layout.
- Collinear group and Sumito geometry inferred from diagrams and text.
- No pass, repetition draw, move limit, or clock termination was added.

Files changed:

- `implementation.py`
- `rule_coverage.md`
- `assumptions.json`

Validation:

- `python -m py_compile implementation.py` — passed
- `python agentic_self_check.py` — passed: `agentic-self-check OK states=300 actions=20209`
- `python profile_fixture_self_check.py` — passed: `profile-fixture-self-check OK`
