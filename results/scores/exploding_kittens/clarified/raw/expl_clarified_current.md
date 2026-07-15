1. Material assumptions/open questions:

- Three cat-card titles are missing from the supplied text. They are explicitly represented as `Katzen-Karte (unbenannte Art 3/4/5)` to satisfy the stated 56-card total and five-player setup.
- Private `Blick in die Zukunft` previews are cleared after deck changes or the individual turn ends.

2. Files changed:

- `implementation.py`
- `rule_coverage.md`
- `assumptions.json`

3. Validation:

- `python -m py_compile implementation.py` — passed.
- `python agentic_self_check.py` — passed: `agentic-self-check OK states=300 actions=1495`.
- Additional setup/JSON probe for 2–5 players — passed.