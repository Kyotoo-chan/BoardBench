Task: Turn the provided board-game rules into a single Python module.

Inputs you will receive:
- Game name
- Attached PDF or pasted rule text

Instructions:
1. Read only the provided rules.
2. Create one self-contained Python module that models the game.
3. Use standard library only.
4. If possible, follow this lightweight interface:
   - `GameState`
   - `Game`
   - `initial_state(self)`
   - `current_player(self, state)`
   - `legal_actions(self, state)`
   - `apply_action(self, state, action)`
   - `is_terminal(self, state)`
   - `returns(self, state)` or `winner(self, state)`
   - `render(self, state)`
5. If rules are ambiguous, incomplete, or contradictory, add an `ASSUMPTIONS` section as Python comments at the top of the file.
6. Do not invent advanced features that are not supported by the provided rules.
7. Avoid TODO placeholders if a minimal implementation is possible.

Output format:
- First: a short section called `Open questions / assumptions`
- Then: exactly one fenced `python` code block containing the full file

Manual template to paste into a chat:

Game name: <replace_me>

Please use the attached PDF or the pasted rule text as the only source of truth.
Generate the Python module now.
