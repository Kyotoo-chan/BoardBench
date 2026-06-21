# LLM-as-judge workflow

This workflow adds a qualitative check to BoardBench without introducing API-key automation. It is manual/subscription-first for now: copy the prompt and artifacts into the chosen model, save the raw review output, then validate it with `checks/90_llm_judge.py`.

## Purpose

The normal checks are good at finding mechanical failures:

- missing files
- syntax/import errors
- missing API methods
- broken action round-trips
- random rollout crashes or dead states
- optional OpenSpiel action/terminal mismatches

An LLM judge can complement these checks by looking for:

- missing rulebook mechanics
- contradictory assumptions
- incorrect phase/turn/scoring logic
- hidden-information leakage
- chance modeled incorrectly
- weak or missing scenario tests
- places where the implementation looks plausible but does not follow the rulebook

The judge should be treated as a reviewer, not as ground truth.

## Where it fits

Recommended order:

1. Create or update `inputs/game_rules.txt` or `inputs/game_rules.pdf`.
2. Optionally run `prompts/rulebook_to_implementation_brief.md` to produce an implementation brief.
3. Generate code with `prompts/rulebook_to_python.txt`, `prompts/open_spiel_backbone.md`, and the implementation brief if available.
4. Save the raw model response and extracted `.py` in `outputs/`.
5. Run normal checks with `python checks/run_checks.py`.
6. Run the LLM judge using `prompts/llm_judge_review.md`.
7. Save the raw judge response in `outputs/`, for example:
   - `outputs/<game>_judge_<model>.md`
   - `outputs/<game>_judge_<model>_after_checks.md`
8. Validate it with `python checks/run_checks.py --include-judge --judge-path outputs/<game>_judge_<model>.md`.

## What to give the judge

Provide as much of this as available:

- original rulebook text
- implementation brief
- generation prompt/backbones used
- generated Python code
- normal check output
- optional OpenSpiel comparison output if the game has a reference

For non-OpenSpiel games, do not provide unrelated OpenSpiel source code as if it were game rules. The judge should evaluate against the rulebook and BoardBench interface only.

## Good judge behavior

Prefer a different model from the generating model when possible. Ask the judge to:

- cite evidence from the provided rulebook/code/check output
- separate definite failures from uncertain ambiguities
- avoid using outside game knowledge
- propose scenario tests, not just prose criticism
- classify issue severity
- produce a stable verdict format

The prompt in `prompts/llm_judge_review.md` enforces this structure.

## Limits and mitigations

LLM judges can hallucinate, miss edge cases, or over-penalize reasonable assumptions. Mitigate this by:

- preserving raw judge outputs
- using the judge as a triage signal, not an automatic pass/fail oracle
- running deterministic checks first
- asking for evidence and severity
- using multiple judges for important final evaluations
- converting repeated judge findings into deterministic scenario tests

## Best use for OpenSpiel and non-OpenSpiel games

For games with OpenSpiel references:

- use OpenSpiel comparison to calibrate the generated environment
- give the judge the comparison output
- ask it to explain mismatches and suggest targeted tests

For games outside OpenSpiel:

- rely more heavily on the implementation brief and rulebook-derived scenario tests
- use the judge to find missing rules and ambiguous assumptions
- do not expect exact reference comparison

This keeps the workflow useful after moving beyond games that the model may already know or that OpenSpiel already implements.

## Automation boundary

`checks/90_llm_judge.py` only validates the saved review verdict. A later notebook/API cell could run the judge automatically, but do not add that until the workflow really needs it because it would introduce provider/API-key choices that this repository currently avoids.
