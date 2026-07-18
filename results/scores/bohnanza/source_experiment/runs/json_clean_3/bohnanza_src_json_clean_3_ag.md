Open material assumptions:

- Variant 2 uses all eight base beans plus Ackerbohne and Weinbrandbohne.
- Only the supplied visible Variant-1 draw/end changes were inherited.
- `returns()` uses +1 for the winner and −1 for others.

Files changed:

- `implementation.py`
- `rule_coverage.md`
- `assumptions.json`

Validation:

- `python -m py_compile implementation.py` — passed
- `python agentic_self_check.py` — passed: `agentic-self-check OK states=300 actions=1442`