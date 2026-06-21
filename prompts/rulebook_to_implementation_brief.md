# Rulebook to implementation brief

Use this before code generation when the rulebook is long, unfamiliar, or not represented in OpenSpiel.

Use only the provided rulebook text. Do not use outside game knowledge, remembered rules, or OpenSpiel implementations. If something is unclear or missing, write `not specified` and list it as an open question.

Do not write code. Produce an implementation brief that can be given to a later coding model together with the rulebook and BoardBench backbones.

## Output format

### 1. Game classification

- number of players
- sequential, simultaneous, or mixed turn structure
- deterministic or chance/stochastic
- perfect information or hidden/private information
- zero-sum, constant-sum, team-based, identical-interest, or general-sum scoring
- terminal-only scoring or repeated/step scoring
- matching BoardBench game-type profiles from `open_spiel_game_type_backbones.md`

### 2. Rulebook-grounded entities and labels

List the named objects that should appear in state, actions, and render output, such as:

- board spaces / coordinates / regions
- pieces / cards / tiles / tokens / dice
- player resources / scores / hands
- phases / rounds / turns
- special markers or status effects

Use labels exactly as the rulebook gives them where possible.

### 3. Proposed `GameState` fields

Describe the state fields needed to implement the rules. Separate:

- public state
- private state per player, if any
- chance/setup state, if any
- derived values that should be computed instead of stored
- history fields needed for repetition, undo-like rules, or information states

### 4. Turn, phase, and chance flow

Describe how play advances:

- initial setup
- current player selection
- phase changes
- simultaneous commitment/resolution, if any
- chance nodes and their probability distributions, if any
- skipped turns, forced passes, eliminations, or end-of-round transitions

### 5. Legal action grammar

Define the action shapes the implementation should use and their canonical names.

Examples:

- `place:<target>`
- `move:<source>-><target>`
- `remove:<target>`
- `bid:<amount>`
- `pass`
- `chance:deal:<card>`
- `p0:<a0>|p1:<a1>` for joint simultaneous actions

Also list how `name_to_action` can reverse each action name.

### 6. State transition rules

For each action type, describe exactly what changes in the state:

- validation conditions
- board/resource/private-state changes
- captures/removals/rewards
- phase and current-player updates
- history updates
- terminal/scoring updates

### 7. Terminal conditions and returns

List all game-ending conditions and the return vector for each case. If returns before terminal should be zero, say so. If scores accumulate during play, explain how cumulative returns relate to score.

### 8. Rendering and player-visible information

Describe what `render(state)` should show for debugging and side-by-side inspection.

If hidden information exists, separately describe what `information_state(state, player)` may show and what it must hide.

### 9. Minimal scenario tests

Extract concrete test scenarios from the rulebook whenever possible. Include:

- initial legal actions
- one normal move/action
- one illegal action edge case
- one scoring or terminal example
- one chance/hidden/simultaneous example if relevant

If the rulebook has no examples, propose small rulebook-derived scenarios without inventing extra rules.

### 10. Open questions / assumptions

List every ambiguity that would affect implementation correctness. Do not silently resolve it unless the user explicitly asks for assumptions.

### 11. Implementation risks

List the most likely ways a generated implementation could be wrong, such as:

- incomplete legal move generation
- wrong phase transition
- hidden information leakage
- chance sampled internally instead of explicitly modeled
- terminal state with remaining legal actions
- action names that cannot round-trip
