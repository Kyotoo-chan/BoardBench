### Open questions / assumptions

- Three missing cat-card titles use explicit placeholder labels.
- Angriff/Nö! timing follows the overview examples; chained Nö! cards toggle cancellation.
- Wunsch against an empty hand transfers nothing.
- Fünfling is omitted because its rules are explicitly missing.

### Files changed

- [implementation.py](C:\Users\benti\AppData\Local\Temp\.ctx-mode-R4NE2M\boardbench_expl_omit_r2_e10jw1rv\implementation.py)

### Validation

- `python -m py_compile implementation.py` — passed.
- `python agentic_self_check.py` — passed: `agentic-self-check OK states=300 actions=810`.