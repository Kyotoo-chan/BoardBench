## Open questions / assumptions

- Three unnamed cat types required by the 56-card count use explicit `Katzen-Karte (unbenannt N)` placeholders.
- NÖ! reactions begin with the next living player and cycle clockwise through all living players, including the action’s player.
- Rendering uses the current decision-maker’s perspective; other hands are hidden.
- Entschärfung insertion positions are zero-based: `0` is the deck top.

## Files changed

- [implementation.py](C:/Users/benti/AppData/Local/Temp/.ctx-mode-PhsAh5/boardbench_expl_clarified_r1_sxftj61s/implementation.py)
- [rule_coverage.md](C:/Users/benti/AppData/Local/Temp/.ctx-mode-PhsAh5/boardbench_expl_clarified_r1_sxftj61s/rule_coverage.md)

## Validation

- `python -m py_compile implementation.py` — passed, exit code 0.
- `python agentic_self_check.py` — passed, exit code 0: `agentic-self-check OK states=300 actions=781`.