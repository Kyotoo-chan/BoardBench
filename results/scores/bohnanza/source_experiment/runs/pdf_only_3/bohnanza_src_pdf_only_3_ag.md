Open material assumptions:

- Trades use atomic one-card offers with recipient acceptance; repeated offers represent unequal multi-card trades.
- Shuffling is reproducible via a configurable seed because the required API provides no randomness interface.

Files changed:

- `implementation.py`
- `rule_coverage.md`
- `assumptions.json`

Validation:

- `python -m py_compile implementation.py` — passed
- `python agentic_self_check.py` — passed: `agentic-self-check OK states=300 actions=3142`