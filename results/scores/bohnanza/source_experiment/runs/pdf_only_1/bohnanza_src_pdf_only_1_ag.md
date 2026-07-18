Open material assumptions:

- Trades are modeled as atomic, mutually accepted actions.
- If both draw and discard piles are empty, the draw yields no card.

Files changed:

- [implementation.py](C:/Users/benti/AppData/Local/Temp/.ctx-mode-AN3uxQ/boardbench_source_packet__rjqju51/implementation.py)
- [rule_coverage.md](C:/Users/benti/AppData/Local/Temp/.ctx-mode-AN3uxQ/boardbench_source_packet__rjqju51/rule_coverage.md)
- [assumptions.json](C:/Users/benti/AppData/Local/Temp/.ctx-mode-AN3uxQ/boardbench_source_packet__rjqju51/assumptions.json)

Validation:

- `python -m py_compile implementation.py` — passed.
- `python agentic_self_check.py` — passed: `agentic-self-check OK states=300 actions=2011`.