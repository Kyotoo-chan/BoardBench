# BoardBench canonical environment contract v2

This file defines evaluator infrastructure, not game rules. The supplied rule sources remain authoritative for behavior.

Keep the existing public methods:

```text
initial_state, current_player, legal_actions, apply_action, is_terminal,
returns, render, action_to_name, name_to_action
```

Use a reproducible constructor `Game(num_players=None, seed=None)`. A supplied seed must determine all chance behavior. `GAME_PROFILE.json.player_counts.supported` is the source-approved player-count range: accept every listed count, apply its count-specific setup, and raise `ValueError` for listed unsupported counts.

Add these five methods:

```python
Game.state_to_data(state) -> dict
Game.state_from_data(payload: dict) -> GameState
Game.action_to_data(action) -> dict
Game.action_from_data(payload: dict) -> Action
Game.observation_to_data(state, player: int) -> dict
```

## Universal envelopes

State:

```json
{"schema": "boardbench/<game-slug>/state/1", "data": {}}
```

Action:

```json
{"schema": "boardbench/<game-slug>/action/1", "data": {"type": "stable_action_type"}}
```

Player observation:

```json
{"schema": "boardbench/<game-slug>/observation/1", "data": {}}
```

The root object has exactly `schema` and `data`. `data` is an object. Action `data.type` is a nonempty stable snake-case identifier. Follow the supplied `GAME_PROFILE.json` for the exact game-specific state fields, action vocabulary, types, and ordering.

## Required properties

- Payloads contain only JSON-domain values: `None`, booleans, integers, finite floats, strings, lists, and string-keyed dictionaries. No tuples, sets, enums, bytes, custom objects, NaN, or infinity.
- Returned payloads are detached copies. Mutating them must not mutate the original state or action.
- `state_to_data` exposes the complete privileged evaluator state, including private information and everything that can affect future behavior. It is not a player observation API.
- `observation_to_data` is the player-specific public view. It may expose the selected player's private information but must hide other players' private information according to the source.
- Required profile fields are always present. Reject unknown, missing, wrongly typed, or invalid fields instead of silently filling defaults or accepting aliases.
- `state_from_data` reconstructs every complete, schema-valid profile payload, including evaluator fixtures that are not naturally reached during a rollout. `zones.reserve` holds inventory intentionally removed from active play in such fixtures. Validate schema and types, but do not reject a payload merely because its phase/zones are unusual. It must not merge a sparse patch into `initial_state()`.
- Every legal action has unique canonical action data. `action_from_data` rejects unknown types and invalid parameters.
- Human-readable names remain separate from canonical machine data.

## Round trips

For every checked state and legal action:

```python
state_data = game.state_to_data(state)
rebuilt_state = game.state_from_data(state_data)
assert game.state_to_data(rebuilt_state) == state_data

action_data = game.action_to_data(action)
rebuilt_action = game.action_from_data(action_data)
assert game.action_to_data(rebuilt_action) == action_data
```

The rebuilt state must agree on `current_player`, `is_terminal`, `returns`, canonical legal actions, and sampled successor states. Before finishing, also run `python profile_fixture_self_check.py`; this checks complete phase, pending-decision, zone, third-field, and five-player payloads without exposing rule expectations.
