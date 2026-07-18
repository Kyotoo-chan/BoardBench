1. Open material assumptions:

- Full “Variante 1” rules were absent; only supplied page-10 changes were implemented.
- Trading uses repeated consensual atomic exchanges/gifts to represent unequal multi-card deals.

2. Files changed:

- `implementation.py`
- `rule_coverage.md`
- `assumptions.json`

3. Validation:

- `python -m py_compile implementation.py` — passed
- `python agentic_self_check.py` — passed: `agentic-self-check OK states=300 actions=1383`