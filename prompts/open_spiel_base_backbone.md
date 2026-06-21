# OpenSpiel-inspired base backbone for BoardBench generated games

Use this as additional LLM context together with the rulebook and `prompts/rulebook_to_python.txt`.

This is a **prompt backbone / interface contract**, not a real OpenSpiel dependency. The generated result must still be one self-contained Python file using only the standard library.

Do not import `pyspiel`, `open_spiel`, or any external framework. Use OpenSpiel only as design inspiration for clean environment structure: explicit state, legal actions, deterministic transitions, chance nodes, information states, returns, and stable action strings.

When the game is not in OpenSpiel, use the same interface discipline but derive all mechanics only from the provided rulebook. Do not fill gaps with remembered OpenSpiel implementations or outside game knowledge.

## Target shape

Implement the game as two main objects:

- `GameState`: all data needed to describe one point in a playthrough
- `Game`: static rules plus methods that create, inspect, and advance states

Prefer returning a new state from `apply_action`. If mutation is used, document it explicitly.

## Required API

The generated file should define:

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

Optional only when the rulebook requires it:

```python
def chance_outcomes(self, state): ...       # list of (action, probability)
def information_state(self, state, player): ...
def observation(self, state, player): ...
def rewards(self, state): ...              # step rewards, if distinct from returns
```

For chance games, `legal_actions(state)` should return the legal chance actions at chance nodes, while `chance_outcomes(state)` adds probabilities for those same actions. This keeps simple random rollouts usable.

For simultaneous-move games, also add one clear joint-action interface:

```python
def legal_actions(self, state, player=None): ...
def legal_joint_actions(self, state): ...
def apply_actions(self, state, actions_by_player): ...
```

If the existing BoardBench checks call `legal_actions(state)` without a player, make it return joint actions at simultaneous nodes so `apply_action(state, joint_action)` can still run a random rollout.

## Suggested constants

Use explicit sentinel values instead of importing `pyspiel`:

```python
TERMINAL = -1
CHANCE = -2
SIMULTANEOUS = -3
```

`current_player(state)` should return:

- a player index such as `0` or `1` for normal turn-based states
- `TERMINAL` for terminal states
- `CHANCE` for explicit stochastic states
- `SIMULTANEOUS` for simultaneous-move states

## Minimal scaffold

Replace the TODO fields and logic with rulebook-derived mechanics.

```python
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

TERMINAL = -1
CHANCE = -2
SIMULTANEOUS = -3


@dataclass(frozen=True)
class GameState:
    current_player_id: int = 0
    terminal: bool = False
    history: tuple[Any, ...] = ()
    returns_so_far: tuple[float, ...] = (0.0, 0.0)
    # TODO: add rulebook-specific public fields, board, hands, scores, decks, etc.


class Game:
    num_players = 2

    def initial_state(self) -> GameState:
        return GameState()

    def current_player(self, state: GameState) -> int:
        if state.terminal:
            return TERMINAL
        return state.current_player_id

    def legal_actions(self, state: GameState):
        if self.is_terminal(state):
            return []
        # TODO: compute all legal actions from state and rulebook.
        raise NotImplementedError

    def apply_action(self, state: GameState, action):
        if action not in self.legal_actions(state):
            raise ValueError(f"illegal action: {self.action_to_name(action)}")
        # TODO: apply the full rule transition and return a fresh state.
        raise NotImplementedError

    def is_terminal(self, state: GameState) -> bool:
        return state.terminal

    def returns(self, state: GameState):
        return state.returns_so_far

    def render(self, state: GameState) -> str:
        # TODO: deterministic compact representation, no decorative prose.
        return str(state)

    def action_to_name(self, action) -> str:
        # TODO: stable, unique, human-readable, rulebook-label-based name.
        return str(action)

    def name_to_action(self, name: str):
        # TODO: reverse action_to_name exactly.
        raise NotImplementedError
```

## Implementation recipe

1. Identify from the rulebook:
   - number of players
   - public state
   - private state, if any
   - turn order or simultaneous phases
   - chance events, if any
   - legal move grammar
   - terminal conditions
   - scoring/utility rules
2. Define `GameState` fields before writing mechanics.
3. Define action representation and canonical action names before `apply_action`.
4. Implement `legal_actions` as a pure deterministic function of the state.
5. Implement `apply_action` by validating the action, updating all state fields, switching player/phase, and setting terminal/returns when needed.
6. Implement terminal and scoring logic separately enough to test it directly.
7. Implement `render` as stable state data for side-by-side inspection.
8. Add assumptions as comments exactly where the rulebook is incomplete.

## Required invariants

- `initial_state()` returns a fresh state.
- `legal_actions` must only list actions accepted by `apply_action`.
- Terminal states have no legal actions.
- Non-terminal player states should not be dead ends unless the rulebook defines one.
- `returns` always has one numeric value per player.
- `render` must be deterministic for the same state.
- `action_to_name` and `name_to_action` must round-trip for legal actions.
- If chance exists, `chance_outcomes` must return probabilities summing to 1.
- If hidden information exists, `information_state(state, player)` must not reveal other players' private data.

## Action naming guidance

Use the board/rulebook notation whenever available. Otherwise use explicit names like:

- `place:<target>`
- `move:<source>-><target>`
- `remove:<target>`
- `claim:<item>`
- `bid:<amount>`
- `pass`
- `chance:deal:<card>`
- `chance:roll:<value>`
- `p0:<a0>|p1:<a1>` for simultaneous joint actions

Avoid names that only expose internal indices, such as `17`, unless the rulebook itself numbers actions that way.
