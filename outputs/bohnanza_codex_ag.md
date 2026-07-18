Open material assumptions:

- Missing referenced “Drei neue Bohnensorten” text; implemented only explicitly supplied augmented rules.
- “Harvest anytime” is available whenever that player controls the current decision.
- A draw with no available card draws nothing; depletion counts when the last actual card is drawn.

Files changed:

- [implementation.py](C:/Users/benti/AppData/Local/Temp/boardbench_bohnanza_codex_ag_iP2Tq6/implementation.py)
- [rule_coverage.md](C:/Users/benti/AppData/Local/Temp/boardbench_bohnanza_codex_ag_iP2Tq6/rule_coverage.md)
- [assumptions.json](C:/Users/benti/AppData/Local/Temp/boardbench_bohnanza_codex_ag_iP2Tq6/assumptions.json)

Validation:

- `python -m py_compile implementation.py` — passed.
- `python agentic_self_check.py` — passed: `agentic-self-check OK states=300 actions=1487`.