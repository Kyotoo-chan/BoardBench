Open material assumptions:

- Defaults to 4 players; `players=5` is supported.
- Multi-card bargains are represented as sequential consensual trades/gifts.
- Deck shuffling is internal, with an optional reproducibility seed.

Files changed:

- `implementation.py`
- `rule_coverage.md`
- `assumptions.json`

Validation:

- `python -m py_compile implementation.py` — passed
- `python agentic_self_check.py` — passed: `agentic-self-check OK states=300 actions=2733`