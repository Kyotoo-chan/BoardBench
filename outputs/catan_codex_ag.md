1. Open questions/material assumptions: three source gaps are documented—same-resource maritime trades, insufficient bank resources during production, and random selection of stolen concealed resources.

2. Files changed:
   - `implementation.py`
   - `rule_coverage.md`
   - `assumptions.json`

3. Validation:
   - `python -m py_compile implementation.py` — passed
   - `python agentic_self_check.py` — passed: `states=300 actions=2959`
   - `python profile_fixture_self_check.py` — passed: `catan-profile-fixture-self-check OK`