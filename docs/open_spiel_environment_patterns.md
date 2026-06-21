# OpenSpiel environment patterns for BoardBench

This note summarizes the OpenSpiel environment structure inspected from the sibling clone at `../open_spiel` and translates it into the smaller BoardBench workflow.

It is not a request to generate real `pyspiel` games. BoardBench generated games should remain self-contained Python files using the standard library. OpenSpiel is used here as an interface and testing model.

## Sources inspected

- `../open_spiel/docs/concepts.md`
- `../open_spiel/docs/api_reference.md`
- `../open_spiel/docs/developer_guide.md`
- `../open_spiel/open_spiel/python/examples/example.py`
- `../open_spiel/open_spiel/python/games/tic_tac_toe.py`
- `../open_spiel/open_spiel/python/games/kuhn_poker.py`
- `../open_spiel/open_spiel/python/games/iterated_prisoners_dilemma.py`
- `../open_spiel/open_spiel/python/games/tic_tac_toe_test.py`
- `../open_spiel/open_spiel/games/tic_tac_toe/tic_tac_toe.{h,cc,test.cc}`

The most useful OpenSpiel idea is the split between:

- `Game`: static rule description and factory for initial states
- `State`: one node in a trajectory/game tree
- `Action`: one transition from one state to the next

OpenSpiel treats every playthrough as a tree of states. A state can be a player decision node, a chance node, a simultaneous-move node, or a terminal node.

## Correct names for the files

For this repository, the clearest terms are:

- **prompt backbone**: reusable context inserted into an LLM prompt
- **implementation scaffold**: a code-shaped skeleton the model can fill
- **interface contract**: required API and invariants that checks can enforce
- **game-type profile**: an additional backbone for a family of games

`Hook` should be reserved for executable callback/integration points. These new files are not hooks yet; they are prompt backbones/scaffolds.

## Blueprint strategy for games outside OpenSpiel

For games that are not in OpenSpiel, the best use of OpenSpiel is as a **blueprint for environment shape**, not as a source of game rules.

The blueprint is:

1. classify the game type from the rulebook
2. define explicit state fields
3. define legal action grammar and canonical action names
4. define deterministic state transitions
5. define terminal/scoring logic
6. define player-visible information if hidden information exists
7. run generic smoke tests and rulebook-derived scenario tests

The backbone files are the reusable prompt version of this blueprint. The base backbone gives the invariant interface; the game-type profiles add only the extra structure needed for chance, hidden information, simultaneous moves, multiplayer scoring, or repeated rounds.

This should help unseen games because it forces the model to build a state-transition system instead of writing ad-hoc procedural code. It does not guarantee correctness: for unfamiliar games, rulebook-derived scenario tests become more important than OpenSpiel comparison.

## `pyspiel` dependency policy

Do not ask generated BoardBench files to import `pyspiel`.

Reasons:

- the current BoardBench workflow should stay self-contained and standard-library only
- many target games will not exist in OpenSpiel
- a real `pyspiel.Game` implementation adds boilerplate and build/import constraints that distract from rule extraction
- using `pyspiel` would make outputs less portable and harder to inspect manually

It is still useful to give the LLM OpenSpiel-inspired context: `Game`, `State`, `current_player`, `legal_actions`, `apply_action`, `chance_outcomes`, `information_state`, `returns`, and action string conventions. In other words: copy the **interface discipline**, not the dependency.

## Calibration vs transfer risk

Testing the workflow first on OpenSpiel games is the right calibration step because it gives a reference implementation for action matching, terminal timing, and returns. But this can overestimate quality on new games:

- popular OpenSpiel games may be memorized by the model
- reference-game rules are often cleaner than real rulebooks
- canonical action names may be easier for known games
- hidden corner cases in unfamiliar games may be missed by random rollouts

To reduce this risk, later experiments should include at least three tiers:

1. **OpenSpiel reference games**: validate the scaffold and comparison tooling.
2. **OpenSpiel-adjacent variants**: modify board sizes, scoring options, or rule variants from the rulebook to test abstraction rather than memorization.
3. **Non-OpenSpiel games**: evaluate only against rulebook-derived checks, scenario tests, and manual inspection.

For non-OpenSpiel games, the benchmark should rely less on exact reference comparison and more on invariant tests plus hand-authored scenarios from examples in the rulebook.

An LLM-as-judge review fits best after deterministic checks have run. It should inspect the rulebook, implementation brief, generated code, and check output for likely missing rules or logic errors. It should not replace deterministic checks or become a hidden source of game rules.

## OpenSpiel structure to preserve conceptually

### Game metadata

OpenSpiel games declare metadata similar to:

- dynamics: sequential or simultaneous
- chance mode: deterministic or stochastic
- information: perfect or imperfect information
- utility: zero-sum, constant-sum, identical-interest, or general-sum
- reward model: terminal-only returns or step rewards
- player count, action count, utility range, maximum game length

BoardBench does not need the full `pyspiel.GameType`, but generated games should still make these properties explicit in comments or lightweight constants when they are known from the rulebook.

### Game object

OpenSpiel `Game` objects mainly provide:

- `new_initial_state()`
- player count
- action-name helpers
- utility bounds and maximum game length
- optional observer creation

BoardBench adapts this to the existing minimal API:

- `initial_state(self)`
- `current_player(self, state)`
- `legal_actions(self, state)`
- `apply_action(self, state, action)`
- `is_terminal(self, state)`
- `returns(self, state)`
- `render(self, state)`
- `action_to_name(self, action)`
- `name_to_action(self, name)`

### State object

OpenSpiel `State` objects provide the mechanics:

- current player or a special node type
- legal actions
- applying an action in place
- chance outcome distributions
- terminal detection
- cumulative returns and optional step rewards
- string rendering
- observations/information states for hidden-information games
- cloning/serialization support for search and testing

BoardBench generated states can be plain dataclasses. Prefer immutable or copy-on-apply behavior unless in-place mutation is documented clearly.

### Action representation

OpenSpiel often uses integer action IDs internally and a separate `action_to_string`. For BoardBench, actions may be tuples or small dataclasses, but action names are crucial because later comparison checks can match generated-game moves to OpenSpiel moves by canonical names.

Good action names are:

- deterministic
- human-readable
- unique among legal actions in a state
- reversible through `name_to_action`
- based on rulebook labels, not only raw internal indices

Examples:

- `place:a1`
- `move:b2->b3`
- `capture:c4`
- `bid:3`
- `p0:cooperate|p1:defect` for joint simultaneous actions
- `chance:deal:KH` or `chance:roll:5` for explicit chance outcomes

## Core invariants to enforce

1. `initial_state()` always returns a fresh usable state.
2. `render(state)` is deterministic and compact.
3. `legal_actions(state)` returns only actions accepted by `apply_action`.
4. Terminal states return no legal actions.
5. Non-terminal player states return at least one legal action, unless the game has an explicit pass/stalemate rule.
6. `apply_action` either returns a new state or clearly mutates in place; BoardBench should prefer returning a new state.
7. `returns(state)` always has one numeric value per player and is stable at terminal states.
8. `action_to_name` and `name_to_action` round-trip exactly for sampled legal actions.
9. Chance probabilities, when present, are non-negative and sum to 1.
10. Hidden-information helpers must not leak private data to the wrong player.
11. If the game has a maximum length or repetition rule, encode it directly to avoid endless rollouts.

## Testing implications copied from OpenSpiel

OpenSpiel tests emphasize:

- load/create game and initial state
- random simulations without crashes
- no chance outcomes for deterministic games
- clone/serialization consistency where available
- playthrough/regression files for stable trajectories
- consistency tests when two implementations of the same game exist

BoardBench already has checks for import, syntax, required API, action-name roundtrip, and random rollouts. Useful next extensions are:

- chance-aware rollout sampling from `chance_outcomes`
- simultaneous-aware rollout sampling for joint actions
- hidden-information leakage checks for `information_state`
- scenario/regression tests from rulebook examples
- manual LLM-as-judge review for rule coverage and likely logic errors
- optional OpenSpiel comparison by canonical action names when an OpenSpiel reference exists

## Do we need multiple backbone files?

No. One OpenSpiel-inspired backbone file is enough for now.

Use one stable **OpenSpiel backbone** for all generated games. It contains the base interface plus short game-type add-ons that should be applied only when the rulebook requires them. This avoids contradictory prompts while still covering important OpenSpiel distinctions:

- deterministic sequential perfect-information games
- stochastic/chance games
- hidden-information games
- simultaneous-move games
- multiplayer/team/general-sum games
- repeated/scoring games with step rewards

The ready-to-use file is:

- `prompts/open_spiel_backbone.md`
