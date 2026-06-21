# OpenSpiel-inspired BoardBench backbone

Use this as extra context with `prompts/rulebook_to_python.txt` and the rulebook.

This is an interface/backbone, not a dependency. Generated code must stay one self-contained standard-library Python file. Do not import `pyspiel`, `open_spiel`, external frameworks, files, network, subprocesses, or API keys.

Use OpenSpiel only for structure: explicit state, legal actions, deterministic transitions, optional chance nodes, optional information states, stable action names, and numeric returns. The rulebook is always the source of truth.

## Required shape

Implement:

```python
class GameState:
    ...

class Game:
    def initial_state(self): ...
    def current_player(self, state): ...
    def legal_actions(self, state): ...
    def apply_action(self, state, action): ...
    def is_terminal(self, state): ...
    def returns(self, state): ...
    def render(self, state): ...
    def action_to_name(self, action): ...
    def name_to_action(self, name): ...
```

Optional only if the rulebook needs them:

```python
def chance_outcomes(self, state): ...        # [(action, probability), ...]
def information_state(self, state, player): ...
def observation(self, state, player): ...
def rewards(self, state): ...               # latest step rewards if separate from returns
```

Suggested sentinel constants:

```python
TERMINAL = -1
CHANCE = -2
SIMULTANEOUS = -3
```

`current_player(state)` should return a player index, `TERMINAL`, `CHANCE`, or `SIMULTANEOUS`.

## Implementation recipe

1. Classify the game from the rulebook: player count, turn structure, chance, hidden information, scoring type.
2. Define `GameState` fields first: public state, private state, phase, current player, scores/returns, history.
3. Define action objects and canonical action names before transition logic.
4. Implement `legal_actions` as a pure deterministic function of state.
5. Implement `apply_action` by validating the action, updating state, switching player/phase, and updating terminal/returns.
6. Keep scoring and terminal rules separate enough to inspect and test.
7. Make `render` compact, deterministic, and useful for side-by-side comparison.
8. Document assumptions exactly where the rulebook is unclear.

Prefer returning a fresh state from `apply_action`. If mutating in place, document it clearly.

## Invariants

- `initial_state()` returns a fresh state.
- terminal states have no legal actions.
- non-terminal player states have legal actions unless the rulebook explicitly allows a dead state.
- `legal_actions` lists only actions accepted by `apply_action`.
- `returns` always has one numeric value per player.
- `render` is deterministic for the same state.
- `action_to_name` and `name_to_action` round-trip for legal actions.
- chance probabilities, if present, are non-negative and sum to 1.
- hidden-information views, if present, do not reveal private data to the wrong player.
- max length / repetition / pass rules are encoded when needed to avoid accidental infinite games.

## Action names

Use rulebook labels whenever available. Otherwise use explicit names:

- `place:<target>`
- `move:<source>-><target>`
- `remove:<target>`
- `claim:<item>`
- `bid:<amount>`
- `pass`
- `chance:deal:<card>`
- `chance:roll:<value>`
- `p0:<a0>|p1:<a1>` for simultaneous joint actions

Avoid names that only expose internal indices unless the rulebook itself uses those indices.

## Game-type add-ons

### Sequential perfect-information games

Use when exactly one player acts and all relevant state is public.

- no `chance_outcomes` or `information_state` needed
- switch the current player after each normal action unless the rules say otherwise
- test wins/draws, blocked/illegal moves, and terminal no-actions behavior

### Chance/stochastic games

Use when cards, dice, random setup, or random events affect play.

- model randomness as explicit chance actions, never hidden calls to `random`
- `current_player` returns `CHANCE` at chance nodes
- `chance_outcomes(state)` returns probabilities for the same chance actions that `legal_actions(state)` returns without probabilities
- `apply_action` consumes the selected chance action deterministically

### Hidden-information games

Use when hands, cards, objectives, or other facts are private.

- keep full truth in `GameState` for correctness
- expose player-visible data through `information_state(state, player)`
- `render(state)` may be full debug state, but document that it is not player-visible
- action names must not leak hidden data unless the action legally reveals it

### Simultaneous-move games

Use when players commit actions before seeing others' choices.

```python
def legal_actions(self, state, player=None): ...
def legal_joint_actions(self, state): ...
def apply_actions(self, state, actions_by_player): ...
```

For simple BoardBench rollouts, `legal_actions(state)` at a simultaneous node should return joint actions that `apply_action(state, joint_action)` can resolve. Name joint actions as `p0:<a0>|p1:<a1>`.

### Multiplayer, teams, or general-sum scoring

- set `num_players` from the rulebook
- `returns(state)` length must equal `num_players`
- map team scores to each individual player explicitly
- handle skipped/eliminated players in turn order

### Repeated rounds or step rewards

- keep cumulative returns separate from latest `rewards(state)` if step rewards matter
- reset round-local state without losing cumulative scores
- encode round limits, target score, or other stop rules

### Games with OpenSpiel references

If comparing against OpenSpiel later:

- prefer rulebook-compatible action names that canonicalize well against OpenSpiel action strings
- keep `render` compact enough for side-by-side inspection
- document deliberate mismatches caused by incomplete rulebook text
