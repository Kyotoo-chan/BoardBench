Open material assumptions:

- “NÖ!” uses explicit reaction rounds; each played NÖ! toggles cancellation and restarts responses.
- “Angriff” replaces the next player’s obligation with exactly two turns; “Hops!” removes one.
- Unreadable cat-card titles are represented as five distinct `Katze-1`–`Katze-5` categories.

Files changed:

- `implementation.py`
- `rule_coverage.md`
- `assumptions.json`

Validation:

- `python -m py_compile implementation.py` — passed.
- `python agentic_self_check.py` — passed: `agentic-self-check OK states=300 actions=631`.