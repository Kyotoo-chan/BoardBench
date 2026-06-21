# OpenSpiel-inspired game-type backbones

Use this file after `prompts/open_spiel_base_backbone.md`. Pick only the profiles that match the rulebook. Do not add mechanics that are not supported by the provided rule text.

## Selection rule

Start with the base backbone for every game. Add a game-type profile only when the rulebook requires the corresponding feature:

- chance/stochastic events
- hidden/private information
- simultaneous decisions
- more than two players, teams, or general-sum scoring
- repeated rounds or non-terminal step rewards

If a game is not in OpenSpiel, still use these profiles as a design checklist. Do not copy rules from OpenSpiel examples; use only the provided rulebook. For unfamiliar games, prefer a smaller but explicit implementation with documented assumptions over broad invented coverage.

## Profile A: deterministic sequential perfect-information games

OpenSpiel analogs: Tic-Tac-Toe, Breakthrough, Chess-like board games, Hex, Connect Four.

Use when:

- exactly one player acts at a time
- all game-relevant state is public
- no dice/deck/random setup is needed after the initial state, or setup is fixed by the rulebook

Backbone requirements:

- `current_player(state)` returns the next player index or `TERMINAL`
- `legal_actions(state)` returns ordinary single-player actions
- `apply_action(state, action)` applies one move and switches turn
- no `chance_outcomes` and no `information_state` needed
- `returns(state)` can be all zero before terminal if the game is terminal-scored

Testing focus:

- known opening legal actions
- illegal occupied/blocked destinations rejected
- terminal no legal actions
- win/draw/loss returns stable
- random rollouts do not dead-end

## Profile B: explicit chance or stochastic games

OpenSpiel analogs: Kuhn Poker card deal, Pig dice rolls, Backgammon dice.

Use when:

- cards are dealt randomly
- dice/spinners/bags/random setup affect play
- a stochastic event occurs between player decisions

Backbone additions:

```python
CHANCE = -2

def current_player(self, state):
    if self.is_terminal(state):
        return TERMINAL
    if state.phase == "chance":
        return CHANCE
    return state.current_player_id

def chance_outcomes(self, state):
    # return [(chance_action, probability), ...]
    ...
```

Implementation rules:

- model chance as explicit actions, not hidden calls to `random`
- `legal_actions(state)` at a chance node should return the chance actions from `chance_outcomes(state)` without probabilities
- `apply_action` at a chance node consumes the selected chance action deterministically
- probabilities must be exact enough for testing and sum to 1
- action names should start with `chance:`

Testing focus:

- probabilities sum to 1
- all chance actions are accepted by `apply_action`
- no direct random sampling inside game logic
- seeded rollout code samples chance externally

## Profile C: imperfect-information / hidden-information games

OpenSpiel analogs: Kuhn Poker, Leduc Poker, Liar's Dice, Phantom Tic-Tac-Toe.

Use when:

- players have private hands/cards/tiles/objectives
- some actions or state facts are hidden from some players
- an agent should not see the full true state

Backbone additions:

```python
def information_state(self, state, player):
    # player-visible information sufficient for decision making
    ...

def observation(self, state, player):
    # optional shorter current observation
    ...
```

Implementation rules:

- keep the full true state in `GameState` for rule correctness
- expose only legal player-visible data through `information_state`
- separate `render(state)` for debugging from player-visible observations
- if using `render(state, player=None)` later, document whether `player=None` shows the full state

Testing focus:

- private data of other players is absent from `information_state`
- legal actions depend only on what the rules allow, not on hidden leaked data
- chance deal/setup creates valid hidden state
- canonical action names do not reveal hidden targets unless the action itself legally reveals them

## Profile D: simultaneous-move games

OpenSpiel analogs: Goofspiel, Oshi-Zumo, Iterated Prisoner's Dilemma.

Use when:

- multiple players choose actions before seeing the others' choices
- a round resolves only after all players commit actions

Backbone additions:

```python
SIMULTANEOUS = -3

def current_player(self, state):
    if self.is_terminal(state):
        return TERMINAL
    if state.phase == "simultaneous":
        return SIMULTANEOUS
    return state.current_player_id

def legal_actions(self, state, player=None):
    if player is None and self.current_player(state) == SIMULTANEOUS:
        return self.legal_joint_actions(state)
    ...

def legal_joint_actions(self, state):
    # return tuples such as (action_for_player0, action_for_player1)
    ...

def apply_actions(self, state, actions_by_player):
    # resolve all chosen actions atomically
    ...
```

Implementation rules:

- do not let player 0's choice update public state before player 1's simultaneous choice is known
- represent joint actions explicitly when the simple BoardBench rollout calls `legal_actions(state)`
- name joint actions as `p0:<name>|p1:<name>`
- for large joint spaces, document if exhaustive `legal_joint_actions` is impractical and add a later benchmark adapter

Testing focus:

- every component action is legal for its player
- joint action names are unique and reversible
- resolution is symmetric/atomic when the rules require it
- random rollouts can progress through simultaneous nodes

## Profile E: multiplayer, teams, and general-sum scoring

OpenSpiel analogs: team dominoes, bargaining/auction games, multiplayer card games.

Use when:

- more than two players participate
- teams share payoffs
- the sum of returns is not always zero

Backbone requirements:

- `num_players` matches the rulebook
- `returns(state)` length is exactly `num_players`
- team scoring maps to each individual player's return explicitly
- turn order supports skipped/eliminated players if the rules allow them

Testing focus:

- returns length and numeric type
- correct winner/team payoff mapping
- turn order after eliminated/skipped players
- terminal states for all players, not only the current player

## Profile F: repeated games, rounds, and step rewards

OpenSpiel analogs: Iterated Prisoner's Dilemma and repeated poker variants.

Use when:

- a game is composed of repeated hands/rounds
- points are accumulated before final terminal state
- rewards after each step matter separately from final returns

Backbone additions:

```python
def rewards(self, state):
    # most recent transition reward, one value per player
    ...
```

Implementation rules:

- keep cumulative `returns` separate from most recent `rewards`
- encode max rounds, target score, or repetition-stop conditions
- reset per-round temporary fields without losing cumulative scores

Testing focus:

- round transition resets only round-local data
- cumulative returns equal sum of rewards/scores
- game cannot run forever if the rulebook has a cap or target score

## Profile G: large board/card/deck action spaces

Use when action spaces are large or structured, such as chess-like movement, deck construction, or many card combinations.

Backbone requirements:

- generate legal actions algorithmically from state, not from a static full list when that would be error-prone
- use tuple/dataclass actions internally, but provide canonical names externally
- keep card/square/region labels exactly as in the rulebook
- avoid model-invented shorthand that is not in the rules

Testing focus:

- action-name roundtrip on sampled states
- no duplicate canonical names in one state
- representative edge cases: blocked paths, captures, empty deck, forced pass, promotion/upgrade if applicable

## Profile H: games with OpenSpiel references

Use when the generated game is intended to compare against an OpenSpiel game.

Extra guidance:

- prefer OpenSpiel-like action names where they are human-readable and rulebook-compatible
- keep `render` compact enough for side-by-side state inspection
- add comments for any deliberate mismatch from OpenSpiel caused by incomplete rule text
- if the OpenSpiel game uses integer action IDs, do not copy the raw IDs as the only public action names

Testing focus:

- generated legal action names can be canonicalized to OpenSpiel action strings
- terminal timing matches the reference on sampled trajectories
- returns match on matched trajectories
