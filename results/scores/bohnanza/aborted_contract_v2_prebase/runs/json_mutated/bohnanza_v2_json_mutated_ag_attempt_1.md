Open question/material assumption: Variant 2 references omitted Variant-1 pages. The implementation applies the visible Variant-1 rules and otherwise follows the base-game flow, documented as A-01.

Files changed:

- `implementation.py`
- `rule_coverage.md`
- `assumptions.json`

Validation:

- `python -m py_compile implementation.py` — passed
- `python agentic_self_check.py` — passed: `agentic-self-check OK states=300 actions=2762`