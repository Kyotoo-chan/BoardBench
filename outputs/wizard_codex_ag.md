Implemented the Wizard Version 1.0 base game. Material assumptions are A-01 (initial dealer/dealing order) and A-02 (`returns` uses cumulative scores), recorded in `assumptions.json`.

Changed files:
- `implementation.py`
- `rule_coverage.md`
- `assumptions.json`

Validation:
- `/c/ProgramData/miniconda3/Scripts/conda.exe run -n boardbench python -m py_compile implementation.py` — passed, no output.
- `/c/ProgramData/miniconda3/Scripts/conda.exe run -n boardbench python agentic_self_check.py` — passed: `agentic-self-check OK states=300 actions=1070`.
- `/c/ProgramData/miniconda3/Scripts/conda.exe run -n boardbench python profile_fixture_self_check.py` — blocked by a defect in the supplied unmodified checker: its loop variable `player` shadows the module-level `player(...)` helper, causing `TypeError: 'dict' object is not callable` at line 124. The implementation had already passed that check's initial-state and all phase fixtures before the checker reached its broken all-zones block.
- `/c/ProgramData/miniconda3/Scripts/conda.exe run -n boardbench python -c "import implementation as m, random; [(lambda g: (lambda s: None)(g.initial_state()))(m.Game(n,1)) for n in range(3,7)]; print('constructors 3-6 OK')"` — passed: `constructors 3-6 OK`.
- `python -c "import json; json.load(open('assumptions.json')); print('assumptions schema JSON parse OK')"` — passed.

Residual risk: the supplied profile fixture check cannot complete without correcting its own name-shadowing bug, which was prohibited because packet/checker files must remain unchanged. Git staging status is not applicable because the isolated workspace is not a Git repository; no staging command was performed.

```acceptance-report
{
  "criteriaSatisfied": [
    {
      "id": "criterion-1",
      "status": "satisfied",
      "evidence": "implementation.py provides the complete requested Game API, canonical serialization methods, base-game transitions, scoring, private observations, seeded chance, default four-player and explicit 3–6-player support; variants remain out of scope."
    },
    {
      "id": "criterion-2",
      "status": "satisfied",
      "evidence": "Rule coverage, explicit material assumptions, exact commands, successful compiler/agentic outputs, and the supplied fixture-checker defect are documented."
    }
  ],
  "changedFiles": [
    "implementation.py",
    "rule_coverage.md",
    "assumptions.json"
  ],
  "testsAddedOrUpdated": [],
  "commandsRun": [
    {
      "command": "/c/ProgramData/miniconda3/Scripts/conda.exe run -n boardbench python -m py_compile implementation.py",
      "result": "passed",
      "summary": "No output; exit code 0."
    },
    {
      "command": "/c/ProgramData/miniconda3/Scripts/conda.exe run -n boardbench python agentic_self_check.py",
      "result": "passed",
      "summary": "agentic-self-check OK states=300 actions=1070"
    },
    {
      "command": "/c/ProgramData/miniconda3/Scripts/conda.exe run -n boardbench python profile_fixture_self_check.py",
      "result": "failed",
      "summary": "Supplied checker shadows its player() helper with a dict loop variable and raises TypeError at line 124; supplied file left unchanged."
    },
    {
      "command": "/c/ProgramData/miniconda3/Scripts/conda.exe run -n boardbench python -c constructor-check",
      "result": "passed",
      "summary": "constructors 3-6 OK"
    },
    {
      "command": "python -c assumptions-json-parse-check",
      "result": "passed",
      "summary": "assumptions schema JSON parse OK"
    }
  ],
  "validationOutput": [
    "Python compilation passed.",
    "Agentic neutral check passed 300 states and 1070 legal-action applications.",
    "Profile checker passed initial and phase fixtures, then stopped in defective supplied checker code."
  ],
  "residualRisks": [
    "The supplied profile_fixture_self_check.py cannot finish until its local variable/helper name collision is corrected outside this implementation task."
  ],
  "noStagedFiles": true,
  "diffSummary": "Added a self-contained standard-library Wizard base-game engine, exact canonical profile serialization/observation support, source-to-code coverage audit, and two explicit source-gap assumptions.",
  "reviewFindings": [
    "no implementation blockers",
    "non-implementation blocker: profile_fixture_self_check.py:124 calls a dict because main() shadows the player helper"
  ],
  "manualNotes": "Workspace is not a Git repository, so no files can be staged. Supplied packet and checker files were not modified."
}
```
