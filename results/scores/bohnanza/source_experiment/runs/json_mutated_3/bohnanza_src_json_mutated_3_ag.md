1. Material assumptions: third deck exhaustion timing, tie-break reference point, and serialized handling of non-active harvesting. Details are recorded in `assumptions.json`.

2. Files changed:
   - `implementation.py`
   - `rule_coverage.md`
   - `assumptions.json`

3. Validation:
   - `python -m py_compile implementation.py` — passed
   - `python agentic_self_check.py` — passed: `agentic-self-check OK states=300 actions=1804`