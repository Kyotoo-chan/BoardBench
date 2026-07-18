Open material assumptions:

- Player 0 is the starting player because the selection method is unspecified.
- Trading uses atomic one-for-one exchanges and one-card gifts; unrestricted negotiated bundles are not modeled.

Files changed:

- `implementation.py`
- `rule_coverage.md`
- `assumptions.json`

Validation:

- `python -m py_compile implementation.py` — passed
- `python agentic_self_check.py` — passed: `agentic-self-check OK states=300 actions=1968`