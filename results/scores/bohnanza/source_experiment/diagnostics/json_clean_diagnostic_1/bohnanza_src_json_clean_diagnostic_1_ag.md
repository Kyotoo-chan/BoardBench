Open material assumptions: four-player default; unavailable Variant 1 text; atomic consensual trades; game ends after completing the draw round on third deck exhaustion.

Files changed:

- `implementation.py`
- `rule_coverage.md`
- `assumptions.json`

Validation:

- `python -m py_compile implementation.py` — passed
- `python agentic_self_check.py` — passed: `agentic-self-check OK states=300 actions=1418`