Open material assumptions:

- Third deck depletion during phase 4 ends the game immediately.
- A non-active player may harvest only when forced to plant an otherwise unplantable card during phase 3.

Files changed:

- [implementation.py](C:/Users/benti/AppData/Local/Temp/.ctx-mode-1jKKyF/boardbench_source_packet_xn3c6umx/implementation.py)
- [rule_coverage.md](C:/Users/benti/AppData/Local/Temp/.ctx-mode-1jKKyF/boardbench_source_packet_xn3c6umx/rule_coverage.md)
- [assumptions.json](C:/Users/benti/AppData/Local/Temp/.ctx-mode-1jKKyF/boardbench_source_packet_xn3c6umx/assumptions.json)

Validation:

- `python -m py_compile implementation.py` — passed
- `python agentic_self_check.py` — passed: `agentic-self-check OK states=300 actions=2612`