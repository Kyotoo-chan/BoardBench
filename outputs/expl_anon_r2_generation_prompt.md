You are the sole implementation agent in an isolated BoardBench workspace.

Use only `rulebook.txt` and any attached rendered pages as game-rule evidence. Do not use remembered rules, web knowledge, repository files, evaluator tests, or assumptions from the game title. The interface contract below is not a rule source. If the supplied source is incomplete, contradictory, or vague, make the smallest explicit implementation assumption and list it in the response.

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
- Use only the rulebook and approved rule facts supplied with this task.
- The rulebook wins on conflicts.
- Do not use remembered game knowledge.
- Do not invent missing rules. Keep unresolved gaps explicit in comments.

Implementation rules:
- Standard library only; no files, network, subprocesses, API keys, or input prompts at runtime.
- Keep the code small and readable.
- Model setup, turns/phases, legal actions, transitions, chance/private information, terminal conditions, and returns explicitly when the rulebook requires them.
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

Actions returned by `legal_actions` must be accepted by `apply_action`. Names must be unique, human-readable, stable, and exactly reversible. Preserve the supplied source's card/effect labels rather than inventing or translating synonyms. Use explicit labels such as `place:<target>` or `move:<source>-><target>` rather than state-dependent raw indices.

Work on the actual workspace file `implementation.py`; do not merely draft the module in the final response. Before finishing, run both commands below against the real file and repair every failure:

```text
python -m py_compile implementation.py
python agentic_self_check.py
```

Do not modify `agentic_self_check.py`. It is an evaluator-neutral API/action-closure probe, not a source of game rules.

Final response only:
1. `Open questions / assumptions` (brief)
2. files changed
3. exact validation commands and outcomes

Do not repeat the complete module in the final response.

