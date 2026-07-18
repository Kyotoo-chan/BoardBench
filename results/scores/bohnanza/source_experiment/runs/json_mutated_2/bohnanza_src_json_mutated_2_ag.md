Open material assumptions are documented in `assumptions.json`: the 129-vs-157-card source conflict, asynchronous harvest timing, and deterministic seeded shuffling.

Files changed:

- `implementation.py`
- `rule_coverage.md`
- `assumptions.json`

Validation:

- `python -m py_compile implementation.py` — passed
- `python agentic_self_check.py` — passed: `agentic-self-check OK states=300 actions=2854`