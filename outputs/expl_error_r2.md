1. Open questions / assumptions

- Three missing cat-family labels use explicit placeholders.
- `Angriff` assigns two turns; stacking passes two turns onward.
- `Entschärfung` permits reinsertion at any deck position.
- `Blick in die Zukunft` reveals three cards without reordering.
- `Nö!` reactions proceed clockwise until all living players pass.

2. Files changed

- [implementation.py](C:\Users\benti\AppData\Local\Temp\.ctx-mode-7aZKmc\boardbench_expl_error_r2_p7muqvg5\implementation.py)

3. Validation

- `python -m py_compile implementation.py` — passed, exit code 0.
- `python agentic_self_check.py` — passed, `agentic-self-check OK states=300 actions=1093`.