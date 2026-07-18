Open material assumptions:

- Player 0 is the start player; the deck uses a reproducible seed-0 shuffle.
- If the draw pile empties during reveal, the current trade and planting phases finish before final scoring.

Files changed:

- `implementation.py`
- `rule_coverage.md`
- `assumptions.json`

Validation:

- `python -m py_compile implementation.py` — passed
- `python agentic_self_check.py` — passed: `agentic-self-check OK states=300 actions=1454`