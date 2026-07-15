### Open questions / assumptions

- `NÖ!` reactions proceed clockwise until all living players pass consecutively.
- Players may decline `Entschärfung`.
- Unlabeled cat artworks use stable names `Katzen-Karte Art 1`–`5`.
- Empty-handed players cannot be targeted by `Wunsch` or `Pärchen`.

### Files changed

- [implementation.py](C:\Users\benti\AppData\Local\Temp\.ctx-mode-AibPJz\boardbench_expl_pdf_r2__ltcvj8v\implementation.py)

### Validation

- `python -m py_compile implementation.py` — passed, exit code 0.
- `python agentic_self_check.py` — passed: `agentic-self-check OK states=300 actions=1237`.