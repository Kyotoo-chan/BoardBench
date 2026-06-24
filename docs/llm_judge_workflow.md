# LLM-as-judge scoring workflow

This workflow adds a qualitative score to BoardBench. The notebook can call pi manually/subscription-first and save the raw review output; `checks/90_llm_judge.py` then parses the score format.

## Purpose

The normal checks are good at finding mechanical failures:

- missing files
- syntax/import errors
- missing API methods
- broken action round-trips
- random rollout crashes or dead states
- optional OpenSpiel action/terminal mismatches

The LLM judge complements these checks by scoring likely rule fidelity:

- missing rulebook mechanics
- contradictory assumptions
- incorrect phase/turn/scoring logic
- hidden-information leakage
- chance modeled incorrectly
- weak or missing scenario tests
- places where the implementation looks plausible but does not follow the rulebook

The judge is a reviewer/scoring signal, not ground truth and not an automatic pass/fail gate.

## Where it fits

Recommended order:

1. Create or update `inputs/game_rules.txt` or `inputs/game_rules.pdf`.
2. Optionally run `prompts/rulebook_to_implementation_brief.md` to produce an implementation brief.
3. Generate code with `prompts/rulebook_to_python.txt`, `prompts/open_spiel_backbone.md`, and the implementation brief if available.
4. Save the raw model response and extracted `.py` in `outputs/`.
5. Run normal checks with `python checks/run_checks.py`.
6. Run the LLM judge using `prompts/llm_judge_review.md`.
7. Save the raw judge response in `outputs/`, for example `outputs/<game>_<variant>_judge.md`.
8. Parse it with `python checks/run_checks.py --include-judge --judge-path outputs/<game>_<variant>_judge.md`.

## What to give the judge

Give the judge the same rule source as generation:

- original rulebook text, or the same rendered/attached rulebook page images for scanned PDFs
- implementation brief, if one was created
- generation prompt/backbones used
- generated Python code

Do not include deterministic check logs by default. Otherwise the judge tends to repeat mechanical check failures instead of independently scoring rulebook-vs-code fidelity. For non-OpenSpiel games, never provide unrelated OpenSpiel source code as if it were game rules.

## Score format

The judge must end with a machine-readable block containing:

```text
score: <0.0-1.0>
confidence: low|medium|high
critical_issues: <number>
major_issues: <number>
minor_issues: <number>
needs_rulebook_clarification: true|false
needs_code_change: true|false
needs_more_tests: true|false
```

`checks/90_llm_judge.py` fails only if this format is missing or invalid. A low score is recorded as data, not treated as a runner failure.

## Limits and mitigations

LLM judges can hallucinate, miss edge cases, or over-penalize reasonable assumptions. Mitigate this by:

- preserving raw judge outputs
- using the score as a triage signal, not ground truth
- asking for evidence and severity
- using multiple judges for important final evaluations
- converting repeated judge findings into deterministic scenario tests

## Best use for OpenSpiel and non-OpenSpiel games

For games with OpenSpiel references:

- use the optional OpenSpiel comparison to calibrate legal actions, turn order, transitions, and terminal returns
- keep OpenSpiel-specific mapping inside `99_openspiel_compare.py`, not in the general checks

For games outside OpenSpiel:

- rely more heavily on the implementation brief and rulebook-derived scenario tests
- use the judge to find missing rules and ambiguous assumptions
- do not expect exact reference comparison
