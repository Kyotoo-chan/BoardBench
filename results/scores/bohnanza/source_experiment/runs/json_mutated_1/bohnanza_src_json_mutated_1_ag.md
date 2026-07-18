Open material assumptions:

- Publisher setup overrides the conflicting component observation: 129 base + Weinbrandbohne + Ackerbohne cards are used, not all 157.
- Seat 0 is the unspecified start player.
- Out-of-turn harvesting is represented when a player controls the current decision; no interrupt protocol was supplied.
- Ties go to the highest-numbered tied seat as the clockwise-furthest player.

Files created:

- `implementation.py`
- `rule_coverage.md`
- `assumptions.json`

Validation:

- `python -m py_compile implementation.py` — passed.
- `python agentic_self_check.py` — passed: `agentic-self-check OK states=300 actions=1868`.