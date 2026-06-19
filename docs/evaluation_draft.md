# BoardBench Evaluation Rules and Scoring Draft

This file is a working draft for possible BoardBench evaluation rules.
It is intentionally broader and more detailed than a final benchmark spec.
The purpose is to collect candidate criteria, failure modes, and scoring ideas for later refinement in the thesis.

## 1. Core evaluation idea

BoardBench should evaluate how well an LLM can transform a **board-game rulebook** into a usable **Python game environment**.

The evaluation can happen on multiple levels:

1. **response level** – what the model says before and around the code
2. **artifact level** – what file is actually produced
3. **static code level** – whether the code is valid Python
4. **runtime level** – whether the code can run without crashing
5. **interface level** – whether the code exposes a usable game API
6. **logic level** – whether the implemented game behavior matches the rulebook
7. **robustness level** – whether the environment avoids getting stuck or breaking under normal usage
8. **comparison level** – whether the result aligns with an OpenSpiel reference where one exists
9. **benchmark suitability level** – whether the output can later be used in a reusable evaluation pipeline

## 2. General principles

### 2.1 Source-of-truth principle

The provided rulebook or provided rule text is the only source of truth.

Fail if the model:

- uses outside game knowledge not present in the material
- adds famous rules from memory
- silently resolves contradictions using prior knowledge
- imports hidden assumptions from standard variants of the game

### 2.2 Transparency principle

Unclear, missing, or contradictory rules should be made visible.

Prefer:

- explicit assumptions
- explicit open questions
- comments explaining uncertain implementations

Penalize:

- hidden assumptions
- overconfident hallucinations
- invented detail presented as fact

### 2.3 Reproducibility principle

The workflow should preserve enough artifacts to reproduce and later discuss a run.

At minimum preserve:

- raw model response
- extracted Python file
- prompts used
- input rule text or rulebook version
- important observations from evaluation

### 2.4 Simplicity principle

For early BoardBench stages, simpler outputs are preferable to flashy but brittle ones.

Prefer:

- one self-contained Python module
- standard library only
- explicit state transitions
- readable assumptions and comments

Penalize:

- unnecessary frameworks
- hidden metaprogramming
- external dependencies without need
- code generation inside generated code

## 3. Evaluation object types

A single model run can produce multiple evaluable objects:

1. **full chat answer**
2. **final extracted Python file**
3. **evaluation log**
4. **comparison notes**
5. **OpenSpiel comparison artifact**

Different rules can apply to each.

## 4. Response-level checks before code execution

These checks evaluate the model answer before the Python file is even tested.

### 4.1 Output format compliance

Possible checks:

- is the output mostly in the requested format?
- does it contain a clear assumptions section if requested?
- does it contain exactly one fenced Python block if requested?
- does it avoid extra files if one file was requested?
- is the answer complete or obviously truncated?
- does it avoid replacing code with placeholders such as `TODO` when a minimal implementation was possible?

Possible failure modes:

- no code block at all
- multiple unrelated code blocks
- pseudo-code instead of executable Python
- output in the wrong language, e.g. JavaScript, Java, C++, pseudocode
- notebook JSON instead of a Python module
- answer is mostly prose and no usable code
- answer says it cannot do the task although enough information was provided

### 4.2 Instruction-following before code

Possible checks:

- did the model follow the request to rely only on the rulebook?
- did it keep comments and identifiers in the requested language?
- did it avoid external dependencies?
- did it produce one module rather than a package?
- did it preserve uncertainty where the rulebook was unclear?

Possible failure modes:

- direct violation of “use only provided rules”
- claims based on unstated game knowledge
- introduces NumPy, Pygame, OpenSpiel, or other packages without permission
- produces several files although one file was requested
- omits assumptions even where uncertainty is obvious

### 4.3 Non-code content quality

Possible checks:

- are assumptions sensible and minimal?
- are open questions relevant and specific?
- does the prose contradict the code?
- is the model honest about uncertainty?

Possible failure modes:

- assumptions section says one thing, code does another
- important ambiguity exists but is not mentioned
- fabricated confidence in unclear rules
- large irrelevant explanation before the code

## 5. Static code validity

These checks evaluate the extracted Python file without relying on semantic correctness yet.

### 5.1 Correct language

Binary check:

- is the extracted artifact actually Python?

Fail examples:

- Java, JavaScript, TypeScript, Rust, C++, pseudo-Python, mixed-language output

### 5.2 Parseability

Possible checks:

- `ast.parse()` succeeds
- `py_compile` succeeds
- no syntax errors
- no indentation errors
- no unterminated strings
- no malformed f-strings
- no invalid pattern matching syntax for the selected Python version

Possible failure modes:

- syntax error
- indentation error
- encoding issue
- unmatched brackets
- broken multiline string

### 5.3 Import-level validity

Possible checks:

- module can be imported successfully
- import does not require unavailable packages
- import does not depend on non-existing files
- import does not start interactive input
- import does not start a game loop automatically

Possible failure modes:

- `ModuleNotFoundError`
- `ImportError`
- top-level `input()` call
- top-level file read on a missing path
- top-level code that crashes immediately
- network access or unsupported side effects during import

### 5.4 Self-contained artifact

Possible checks:

- is the file self-contained enough for the intended workflow?
- does it avoid hidden dependencies on additional local files?
- does it avoid requiring manual patching before use?

Possible failure modes:

- requires helper modules that were not generated
- references external config files
- expects images, assets, or data files not provided
- expects environment variables or secrets

## 6. Basic runtime stability

These checks ask whether the code can run in ordinary usage.

### 6.1 Construction and initialization

Possible checks:

- can the `Game` object be instantiated?
- can an initial state be created?
- is the initial state internally consistent?
- can the state be rendered without crashing?

Possible failure modes:

- constructor crash
- missing constructor arguments with no defaults
- invalid initial player index
- missing board dimensions
- invalid piece counts at start
- render crash on initial state

### 6.2 Basic API calls

Possible checks:

- `current_player(state)` runs
- `legal_actions(state)` runs
- `is_terminal(state)` runs
- `returns(state)` or `winner(state)` runs
- `apply_action(state, action)` runs for at least one legal action

Possible failure modes:

- method missing
- wrong signature
- `TypeError`
- state mutation breaks later calls
- action application crashes

### 6.3 Repeated execution stability

Possible checks:

- repeated legal-action application does not crash immediately
- repeated random playouts terminate under a step cap
- no progressive corruption of state
- no memory growth due to obvious leaks in normal use

Possible failure modes:

- crash after a few turns
- state becomes inconsistent only after several transitions
- infinite recursion
- unbounded loop
- non-terminal state with no legal actions
- illegal action generated by `legal_actions`

## 7. Interface completeness and usability

If BoardBench uses a lightweight standard interface, evaluate how well the output matches it.

### 7.1 Presence of expected structures

Possible checks:

- `GameState` exists
- `Game` exists
- `initial_state(self)` exists
- `current_player(self, state)` exists
- `legal_actions(self, state)` exists
- `apply_action(self, state, action)` exists
- `is_terminal(self, state)` exists
- `returns(self, state)` or `winner(self, state)` exists
- `render(self, state)` exists

Possible failure modes:

- missing class
- missing core method
- method present under unrelated names only
- wrong number of parameters

### 7.2 API consistency

Possible checks:

- same state object shape is accepted by all methods
- action format is stable across methods
- player identifiers are consistent
- terminal conditions and return values are compatible
- method names and semantics are not contradictory

Possible failure modes:

- `legal_actions` returns strings but `apply_action` expects tuples
- `current_player` returns players outside the return vector length
- `winner()` and `returns()` imply different outcomes
- `apply_action` returns a new state sometimes and mutates in place other times without consistency

### 7.3 Benchmark usability

Possible checks:

- state can be stepped programmatically
- no human input is required
- no GUI is required
- no hidden random seed dependence unless exposed cleanly
- no top-level CLI flow required to use the module

Possible failure modes:

- environment only works via `while True: input(...)`
- code is a script, not a reusable module
- human-readable rendering exists but stepping interface is missing

## 8. Rulebook fidelity

This is the core logic category.

### 8.1 Setup fidelity

Possible checks:

- board shape matches the rulebook
- pieces/resources/cards/etc. are initialized correctly
- player count assumptions are explicit
- turn order starts correctly
- special setup rules are included or explicitly omitted as assumptions

Possible failure modes:

- wrong board size
- wrong number of pieces
- wrong starting player
- setup phase omitted entirely
- random setup invented without basis

### 8.2 Turn structure fidelity

Possible checks:

- phases inside a turn are modeled correctly
- mandatory steps are included
- optional steps are not forced
- turn passes to the correct next player
- chance or environment events are handled correctly if present

Possible failure modes:

- skips mandatory phase
- allows end turn too early
- wrong player continues indefinitely
- turn order wraps incorrectly
- extra phase invented from outside knowledge

### 8.3 Legal action fidelity

Possible checks:

- only legal actions are returned
- all ordinarily legal actions are represented
- conditional actions appear only when conditions are met
- illegal action handling is sensible

Possible failure modes:

- legal actions missing
- illegal actions included
- actions allowed from impossible board positions
- movement/placement constraints missing
- action list depends on stale state

### 8.4 State transition fidelity

Possible checks:

- applying an action changes the correct parts of the state
- resources are updated correctly
- captured or removed pieces are handled correctly
- phase transitions happen at the right time
- action side effects are neither omitted nor doubled

Possible failure modes:

- piece moves but old position not cleared
- score/resource updated twice
- capture rule missing
- turn counter not updated
- phase flag not changed
- board and inventory disagree

### 8.5 Terminal condition fidelity

Possible checks:

- all end conditions from the rulebook are covered where possible
- game ends when it should
- game does not end too early
- stalemate/draw conditions are handled where relevant

Possible failure modes:

- no terminal state ever reached
- game ends after every move
- draw condition omitted
- win condition checked incorrectly
- tie-break rule missing and silently replaced

### 8.6 Scoring / returns / winner fidelity

Possible checks:

- winner is correct
- returns vector matches outcome semantics
- draws are represented consistently
- point scoring matches rulebook where implemented
- zero-sum assumptions are not invented unless warranted

Possible failure modes:

- wrong winner in standard cases
- draw represented as win
- returns length wrong for player count
- scoring inverted
- score tracked but winner logic ignores it

### 8.7 Hidden information and uncertainty handling

Possible checks:

- does the model explicitly simplify hidden-information games when needed?
- are card/deck/randomness assumptions stated?
- are unrecoverable unknowns surfaced clearly?

Possible failure modes:

- hidden information ignored silently
- deck order invented arbitrarily without disclosure
- private information modeled as public without comment

## 9. Logic error catalogue

This section lists common logic errors worth tracking explicitly.

### 9.1 Wrong-state errors

- initial state impossible under the rules
- board contains illegal overlap
- negative resources
- duplicate ownership of the same piece
- phase markers inconsistent with board state

### 9.2 Turn-order errors

- same player moves forever
- skipped player
- player order reverses incorrectly
- eliminated player still moves
- game asks terminal player to move

### 9.3 Legal-action errors

- empty legal action list in a non-terminal state
- action list contains duplicates
- action list contains impossible actions
- action list omits mandatory forced moves
- action list depends on rendering state or accidental mutation

### 9.4 Transition errors

- action has no effect
- action updates only part of the state
- state becomes impossible after legal move
- board and auxiliary counters diverge
- piece removal/placement mismatch

### 9.5 Scoring errors

- points awarded to wrong player
- score never changes
- score changes when it should not
- score not used for end evaluation
- tie-break ordering reversed

### 9.6 Terminality errors

- terminal state not detected
- non-terminal state wrongly marked terminal
- terminal state still offers actions
- terminal state crashes in render or returns

### 9.7 Randomness errors

- random behavior used where deterministic rules exist
- no seed control where stochasticity matters
- chance outcomes impossible under the rules
- probabilities not normalized or not represented

### 9.8 Aliasing and mutation errors

- `apply_action` mutates shared objects unexpectedly
- old states change after new actions
- copied state still shares nested mutable structures
- undo-by-reference bugs

### 9.9 Infinite or stuck behavior

- infinite loop in turn progression
- recursive rule resolution with no base case
- repeated draw/phase handling with no termination
- terminal false forever under normal play
- state where no legal move exists and no pass/end logic exists

## 10. Non-termination and “getting stuck” checks

This category is especially important.

### 10.1 Hard infinite loops

Possible checks:

- import completes under timeout
- initialization completes under timeout
- repeated playout completes under per-game step cap
- render completes under timeout

Possible failure modes:

- `while True` loop with no exit
- endless turn advancement
- recursion until crash
- loop over legal actions that regenerates forever

### 10.2 Soft stuck states

Possible checks:

- state can progress from non-terminal to next state
- if no legal move exists, rules define pass, loss, or termination
- repeated transitions eventually reach terminal or repeat detection logic

Possible failure modes:

- non-terminal with empty action list
- action application returns same state forever
- state alternates between impossible subphases
- pass action missing where needed

### 10.3 Practical timeout checks

Possible checks:

- max initialization time
- max single-step time
- max render time
- max random playout time

Potential reasons for failure:

- expensive search hidden inside environment logic
- accidental exponential branching inside `legal_actions`
- unbounded deep copy or state reconstruction on every call

## 11. Error classes before code correctness

Some failures happen before meaningful code evaluation even begins.

### 11.1 Task misunderstanding

- model summarizes rules instead of generating code
- model generates a game design instead of the requested game
- model generates a benchmarking framework instead of the environment
- model refuses despite enough information

### 11.2 Wrong abstraction level

- generates only helper functions and no game object
- generates CLI program only
- generates commentary-only artifact
- generates tests without the actual environment

### 11.3 Overengineering

- creates complex package structure
- invents abstract base classes and registries without need
- builds a provider framework instead of a game module
- wraps everything in unnecessary metaclasses or factories

### 11.4 Under-specification masking

- fills unknowns with arbitrary defaults without comments
- silently removes hard rules
- drops major phases because they are inconvenient

## 12. Static quality signals beyond correctness

These are secondary quality indicators.

### 12.1 Readability

Possible checks:

- clear naming
- compact but understandable structure
- comments where rules are ambiguous
- no giant monolithic method if avoidable

### 12.2 Simplicity

Possible checks:

- standard library only
- no unnecessary classes
- no unnecessary inheritance
- logic is inspectable

### 12.3 Traceability to rules

Possible checks:

- assumptions refer to missing or ambiguous rule areas
- comments make it easier to map code to rulebook sections
- difficult special rules are visible in the implementation

## 13. OpenSpiel comparison dimensions

When a reference exists, several comparison dimensions are possible.

### 13.1 Structural comparison

Possible checks:

- same number of players
- same action concept or equivalent abstraction
- same state variables or clearly corresponding ones
- same terminal and return semantics

### 13.2 Behavioral comparison

Possible checks:

- same legal actions in sampled states
- same next-player logic
- same state transitions for selected test actions
- same terminal outcome for selected scenarios
- same returns/winner for selected scenarios

### 13.3 Coverage comparison

Possible checks:

- setup included?
- full turn logic included?
- scoring included?
- special cases included?
- draw and repetition rules included?

### 13.4 Divergence taxonomy

Possible divergence labels:

- superficial difference only
- interface difference but same logic
- partial logic mismatch
- major rule omission
- contradictory game behavior

## 14. Benchmark suitability checks

Even logically decent code may still be poor benchmark material.

### 14.1 Automation suitability

Possible checks:

- module importable without manual steps
- no interactive prompts
- deterministic API surface
- file can be executed repeatedly in a test harness

### 14.2 Environment hygiene

Possible checks:

- no filesystem writes during import or normal stepping
- no network calls
- no subprocesses
- no hidden randomness without control

### 14.3 Output stability

Possible checks:

- render is stable enough for inspection
- method outputs have stable types
- exceptions are not part of normal control flow

### 14.4 Performance sanity

Possible checks:

- no severe slowdown on ordinary states
- no clearly pathological action enumeration
- no avoidable quadratic/exponential work in basic calls

## 15. Candidate binary gate criteria

These are strong pass/fail filters that can be applied before any finer scoring.

A run may be marked **hard fail** if any of these fail:

1. output is not Python
2. extracted file does not parse
3. extracted file cannot be imported
4. output requires forbidden dependencies
5. no usable game environment artifact exists
6. initial state cannot be created
7. standard API methods are mostly missing
8. normal legal move application crashes immediately
9. repeated playout cannot terminate within a reasonable cap
10. code clearly uses outside knowledge despite the source-only rule

Possible softer gate variant:

- require only 1–8 for basic pass
- treat 9–10 as severe but separately flagged

## 16. Candidate weighted scoring scheme (100 points)

### 16.1 Scheme A: balanced 100-point rubric

#### A. Response compliance – 10 points

- follows requested format
- provides one usable Python module
- includes assumptions/open questions where needed

#### B. Static validity – 15 points

- correct language
- parses
- compiles
- imports cleanly
- self-contained enough

#### C. Runtime stability – 15 points

- initializes
- basic methods run
- render works
- no immediate runtime crashes

#### D. Interface completeness – 15 points

- expected classes/methods present
- API consistent
- usable for later benchmarking

#### E. Rulebook fidelity – 25 points

- setup
- turn logic
- legal actions
- transitions
- terminal conditions
- scoring/winner logic

#### F. Robustness and non-stuck behavior – 10 points

- no infinite loops
- no soft-stuck states
- repeated play remains stable

#### G. Transparency of assumptions – 5 points

- ambiguity made visible
- no hidden major assumptions

#### H. OpenSpiel alignment or reference alignment – 5 points

- where available, core behavior aligns with reference

### 16.2 Scheme B: benchmark-oriented 100-point rubric

This puts more weight on actual use in a future benchmark.

- response compliance: 5
- static validity: 15
- runtime stability: 20
- interface completeness: 15
- rulebook fidelity: 25
- robustness/non-stuck: 15
- benchmark suitability: 5

### 16.3 Scheme C: strict gate + score

Use two layers:

1. **mandatory gates**
2. **score only among passing runs**

Example mandatory gates:

- Python artifact exists
- parses
- imports
- initial state works
- legal action application works
- repeated playout terminates under step cap

Then score remaining dimensions from 0–100.

## 17. Candidate severity-based defect scheme

Instead of or in addition to a numeric score, classify defects by severity.

### 17.1 Critical defect

Examples:

- wrong language
- not parseable
- import crash
- no usable initial state
- infinite loop
- non-terminal with no legal actions and no pass/end resolution
- returns shape invalid for player count
- major rule system entirely missing

### 17.2 Major defect

Examples:

- important common rule omitted
- winner logic wrong in standard cases
- legal action generation systematically wrong
- action transition corrupts state
- setup significantly wrong
- hidden assumption changes game behavior materially

### 17.3 Minor defect

Examples:

- small edge-case omission
- comments unclear
- render poor but functional
- naming inconsistent
- assumptions section incomplete but not deceptive

### 17.4 Informational issue

Examples:

- style issue only
- slightly awkward API naming
- extra prose in output but code is usable

## 18. Candidate checklist for manual evaluation

### 18.1 Before extraction

- [ ] raw response saved
- [ ] prompt files saved or referenced
- [ ] input rule text version known
- [ ] output format looks usable

### 18.2 Artifact extraction

- [ ] Python block extracted cleanly
- [ ] one intended file identified
- [ ] assumptions/open questions preserved

### 18.3 Static checks

- [ ] correct language
- [ ] parseable
- [ ] compilable
- [ ] importable
- [ ] standard-library only if required

### 18.4 Runtime checks

- [ ] `Game` instantiates
- [ ] `initial_state()` works
- [ ] `render()` works on initial state
- [ ] `legal_actions()` returns usable output
- [ ] `apply_action()` works on sampled legal move
- [ ] `is_terminal()` works
- [ ] `returns()` or `winner()` works

### 18.5 Robustness checks

- [ ] no immediate crash after several steps
- [ ] no obvious infinite loop
- [ ] no soft-stuck state observed
- [ ] repeated random playout terminates under cap

### 18.6 Logic checks

- [ ] setup matches rulebook
- [ ] player order matches rulebook
- [ ] legal moves match rulebook in sampled states
- [ ] state transitions match rulebook in sampled states
- [ ] terminal conditions match rulebook
- [ ] scoring/winner logic matches rulebook

### 18.7 Transparency checks

- [ ] ambiguities acknowledged
- [ ] assumptions are minimal
- [ ] no obvious outside knowledge inserted

### 18.8 Reference checks

- [ ] comparison to OpenSpiel attempted where available
- [ ] mismatches documented
- [ ] unclear mismatches separated from confirmed mismatches

## 19. Candidate automatic test categories

Later automation could include these categories.

### 19.1 Artifact tests

- file exists
- text extraction succeeded
- Python block count check
- output language detection

### 19.2 Static tests

- `ast.parse`
- `py_compile`
- import test with timeout
- dependency scan

### 19.3 Smoke tests

- instantiate environment
- create initial state
- call basic methods once

### 19.4 Random playout tests

- choose random legal action repeatedly
- stop on terminal or step cap
- record crashes
- record stuck states

### 19.5 Contract tests

- `legal_actions` returns iterable/list-like structure
- all actions returned are accepted by `apply_action`
- terminal states have stable returns/winner behavior
- current player stays in valid range

### 19.6 Reference tests

- compare selected states against OpenSpiel reference
- compare selected outcomes against reference
- compare legal action counts or sets

## 20. Failure catalogue for logging

A future evaluator can log failures under these tags.

### 20.1 Output and extraction

- `wrong_language`
- `missing_code`
- `multiple_files_unexpected`
- `format_noncompliant`
- `truncated_response`
- `assumptions_missing`

### 20.2 Static code

- `syntax_error`
- `compile_error`
- `import_error`
- `external_dependency`
- `not_self_contained`

### 20.3 Runtime

- `constructor_error`
- `initial_state_error`
- `render_error`
- `legal_actions_error`
- `apply_action_error`
- `terminal_check_error`
- `returns_error`

### 20.4 Logic

- `setup_mismatch`
- `turn_order_mismatch`
- `legal_actions_missing`
- `legal_actions_illegal`
- `transition_error`
- `terminal_condition_wrong`
- `winner_logic_wrong`
- `score_logic_wrong`
- `hidden_assumption_major`

### 20.5 Robustness

- `infinite_loop`
- `soft_stuck_state`
- `state_corruption`
- `random_play_crash`
- `performance_pathological`

### 20.6 Reference comparison

- `openspiel_mismatch_structural`
- `openspiel_mismatch_behavioral`
- `openspiel_mismatch_terminal`
- `openspiel_mismatch_returns`

## 21. Candidate evaluation record template

Each run could later be summarized like this:

```text
Game:
Model:
Prompt set:
Input source:

Artifact status:
- raw response saved: yes/no
- python file extracted: yes/no

Gate checks:
- correct language: pass/fail
- parseable: pass/fail
- importable: pass/fail
- initial state works: pass/fail
- basic step works: pass/fail
- random playout under cap: pass/fail

Scores:
- response compliance:
- static validity:
- runtime stability:
- interface completeness:
- rulebook fidelity:
- robustness:
- transparency:
- reference alignment:
- total:

Defects:
- critical:
- major:
- minor:

Notes:
- assumptions:
- likely logic issues:
- comparison observations:
```

## 22. Candidate research questions hidden inside evaluation

The following are not just implementation details; they may become thesis-level decisions.

- how strict should “correctness” be when the rulebook is ambiguous?
- should missing but transparent assumptions score better than wrong but complete implementations?
- should syntax-valid but logically wrong code outperform incomplete but honest code?
- should OpenSpiel alignment count as core score or secondary comparison?
- how much of the score should come from automated checks vs manual rule audit?
- should pilot games be selected for simplicity, diversity, or OpenSpiel availability?
- how should stochastic or hidden-information games be treated?
- how should multi-phase games be compared to simpler single-phase games fairly?

## 23. Suggested early BoardBench evaluation stack

For a first practical version, a good minimal stack could be:

### Level 1: hard gates

- Python output exists
- parseable
- importable
- initial state works
- at least one legal step works
- repeated playout terminates under cap

### Level 2: manual logic audit

- setup
- turn order
- legal actions
- transitions
- terminal conditions
- scoring/winner
- explicit assumptions

### Level 3: reference comparison

- compare against OpenSpiel where available
- document mismatches rather than forcing a single score too early

## 24. Good signs in a model output

These are positive indicators worth noting.

- one clean self-contained Python file
- assumptions explicitly listed
- rule ambiguities commented in code
- standard-library-only implementation
- stable and simple game state representation
- legal action generation and transition logic clearly separated
- no interactive input
- render works but stays lightweight
- repeated random playouts terminate
- code structure is generic enough for later comparison but not overengineered

## 25. Common bad signs in a model output

- huge explanation and tiny unusable code block
- obviously copied generic template unrelated to the game
- famous rules added from memory
- terminal logic missing entirely
- score tracking present but never used
- `legal_actions` returns placeholders
- `apply_action` mutates the wrong player or wrong piece
- uses `while True` control loops inside core environment logic
- requires manual fixes to run
- imports packages not allowed
- code acts like a CLI toy instead of a reusable environment

## 26. Recommendation for later narrowing

This file is intentionally broad.
Later, BoardBench should probably separate:

1. **mandatory gates**
2. **core benchmark score**
3. **reference-comparison notes**
4. **thesis discussion variables**

A final benchmark should be smaller than this draft, but this draft can serve as the source pool for selecting the final criteria.
