Open material assumptions are recorded in `assumptions.json`: serialized trade negotiations, seeded shuffling, and sequential planting of received cards.

Files changed:

- `implementation.py`
- `rule_coverage.md`
- `assumptions.json`

Validation:

- `python -m py_compile implementation.py` — passed
- `python agentic_self_check.py` — passed: `agentic-self-check OK states=300 actions=1273`