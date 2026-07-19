1. Material assumptions are documented in `assumptions.json`: missing Variant 1 setup text, deck depletion timing ambiguity, and unspecified multi-card trade protocol.

2. Files changed:

- `implementation.py`
- `rule_coverage.md`
- `assumptions.json`

3. Validation:

- `python -m py_compile implementation.py` — passed
- `python agentic_self_check.py` — passed: `agentic-self-check OK states=300 actions=3128`