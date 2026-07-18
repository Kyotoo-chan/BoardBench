Material assumptions:

- Trades use explicit propose → accept/reject sequencing.
- Score ties select the highest player index as nearest clockwise before the start player.
- Card shuffling uses a reproducible fixed seed.

Files changed:

- `implementation.py`
- `rule_coverage.md`
- `assumptions.json`

Validation:

- `python -m py_compile implementation.py` — passed
- `python agentic_self_check.py` — passed: `agentic-self-check OK states=300 actions=2039`