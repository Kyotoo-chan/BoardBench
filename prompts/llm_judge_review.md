# LLM judge review prompt

Use this as a manual qualitative test after a game implementation has been generated and the normal BoardBench checks have run.

The judge is not the source of truth. Its job is to find likely rule coverage gaps, logic errors, unsupported assumptions, and missing tests that deterministic checks may miss.

## Inputs to provide

Give the judge these artifacts, when available:

1. the original rulebook text
2. the implementation brief, if one was created
3. the generation prompt/backbones used
4. the generated Python file
5. normal check output from `python checks/run_checks.py`
6. optional OpenSpiel comparison output, only when the game has an OpenSpiel reference

## Judge instructions

Use only the provided artifacts. Do not use outside game knowledge, remembered rules, or internet knowledge. If the code differs from a rule that is not explicitly present in the provided rulebook, mark it as uncertain rather than wrong.

Review the generated game as a BoardBench environment, not as a polished application. Prioritize rule fidelity, state-transition correctness, action legality, terminal/scoring behavior, and testability over style.

Do not rewrite the full implementation. Suggest small targeted fixes or new tests only where useful.

## Required output format

### 1. Verdict

Choose one:

- `pass`: no important issues found
- `provisional pass`: only minor issues or unresolved rulebook ambiguities
- `revise`: likely correctness issues that should be fixed before benchmarking
- `fail`: major missing mechanics, broken API behavior, or unsupported invented rules

Also give a confidence level: low, medium, or high.

### 2. Top findings

List the most important findings first. For each finding include:

- severity: critical / major / minor / question
- evidence from the rulebook, generated code, or check output
- why it matters for gameplay or benchmarking
- suggested next action

### 3. Rule coverage review

Create a table with columns:

- rule area
- covered correctly / partially covered / missing / unclear
- evidence
- notes

Cover at least:

- setup
- player count and turn order
- legal actions
- state transitions
- chance, if any
- hidden information, if any
- simultaneous moves, if any
- terminal conditions
- scoring/returns
- rendering/action names

### 4. BoardBench API and backbone compliance

Check whether the implementation satisfies:

- `GameState` and `Game` exist
- `initial_state`, `current_player`, `legal_actions`, `apply_action`, `is_terminal`, `returns`, `render`, `action_to_name`, `name_to_action`
- terminal states have no legal actions
- `legal_actions` only returns actions accepted by `apply_action`
- `action_to_name` / `name_to_action` round-trip
- chance is explicit, not sampled internally, when chance exists
- hidden information does not leak through `information_state`, when hidden information exists
- no `pyspiel`, OpenSpiel, network, subprocess, file, or non-standard-library dependency

### 5. Logic and invariant review

Look for likely logic mistakes:

- impossible or missing legal actions
- wrong current-player/phase update
- state mutation surprises
- scoring sign errors or wrong return length
- games that can continue forever without a rulebook reason
- terminal states that still allow actions
- non-terminal dead states
- duplicate or non-reversible action names
- render output that hides important public state

### 6. Unsupported assumptions or invented rules

List every place where the implementation appears to decide something not specified by the provided rulebook. Distinguish:

- harmless implementation convention
- necessary assumption that should be documented
- risky invented rule that may change gameplay

### 7. Missing scenario tests

Suggest concrete additional tests. Prefer action-name sequences that could later be turned into deterministic checks.

For each test include:

- test name
- starting state or setup
- action sequence using canonical action names
- expected state/render/returns/legal-actions property
- which rulebook rule it covers

### 8. Open questions for the human

Ask only questions that materially affect implementation correctness or benchmark scoring.

### 9. Machine-readable summary

End with a compact YAML-like block:

```text
verdict: pass|provisional pass|revise|fail
confidence: low|medium|high
critical_issues: <number>
major_issues: <number>
minor_issues: <number>
needs_rulebook_clarification: true|false
needs_code_change: true|false
needs_more_tests: true|false
```
