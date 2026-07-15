You are the sole implementation agent in an isolated BoardBench workspace.

Use only `rulebook.pdf` and any attached rendered pages as game-rule evidence. Do not use remembered rules, web knowledge, repository files, evaluator tests, or assumptions from the game title. The interface contract below is not a rule source. If the supplied source is incomplete, contradictory, or vague, make the smallest explicit implementation assumption and list it in the response.

# BoardBench public interface contract

This is evaluator-neutral infrastructure, not an additional source of game rules.

- Implement one self-contained standard-library Python module.
- `Game()` defaults to two players and player 0 starts; optional `num_players` and seed parameters are welcome.
- Nonterminal returns are zero for every player. Terminal returns are +1 for the winner and -1 for each loser.
- Provide `GameState` and `Game` with initial_state, current_player, legal_actions, apply_action, is_terminal, returns, render, action_to_name, and name_to_action.
- Terminal states have no legal actions.
- Every legal action must round-trip through a unique, stable, human-readable name. Preserve the supplied source's card/effect labels in action names instead of inventing or translating synonyms.
- Choices required by the source (targets, donated/requested cards, positions, reactions) must be explicit states/actions rather than silently chosen.


Implement the provided rulebook as one self-contained Python module.

Source rules:
- Use only the supplied rulebook as game-rule evidence.
- Do not use remembered or web rules.
- Do not invent missing rules. Keep unresolved gaps explicit.

Implementation rules:
- Standard library only; no files, network, subprocesses, API keys, or input prompts at runtime.
- Keep the code small and readable.
- Model setup, phases, legal actions, transitions, chance/private information, terminal conditions, and returns explicitly when required.
- Terminal states have no legal actions.

Provide `GameState` and `Game` with:
- `initial_state()`
- `current_player(state)`
- `legal_actions(state)`
- `apply_action(state, action)`
- `is_terminal(state)`
- `returns(state)`
- `render(state)`
- `action_to_name(action)`
- `name_to_action(name)`

Every legal action must be accepted by `apply_action`. Action names must be unique, stable, human-readable, reversible, and preserve source labels.

Work on the actual `implementation.py`. Before finishing, run:

```text
python -m py_compile implementation.py
python agentic_self_check.py
```

Do not modify `agentic_self_check.py`.

Create `rule_coverage.md`. Map every supplied section and named rule/card/combination to its implementing symbol, a source-only probe or reason it was not probed, and any assumption.

Create `assumptions.json` with exactly this shape:

```json
{
  "version": 1,
  "assumptions": [
    {
      "id": "A-01",
      "material": true,
      "source_location": "page/section or exact heading",
      "source_basis": "ambiguous",
      "alternatives": ["plausible behavior A", "plausible behavior B"],
      "selected": "implemented behavior",
      "affected_mechanics": ["legal_actions", "state_transition"]
    }
  ]
}
```

Allowed `source_basis` values are `ambiguous`, `missing`, and `contradictory`. Include only material assumptions that affect legal actions, transitions, private information, elimination, terminal results, or scoring. Use an empty list when there are none. This is a source audit, not evaluator access.

Final response only:
1. brief open questions/material assumptions;
2. files changed: `implementation.py`, `rule_coverage.md`, `assumptions.json`;
3. exact validation commands and outcomes.

Do not repeat the complete module in the final response.

