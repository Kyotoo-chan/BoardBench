# BoardBench current workflow

The workflow is deliberately iterative: facts, scenarios, adapters, prompts, and reporting may improve whenever a defect is found. Git preserves earlier states. A SHA-256 recorded in a result identifies the exact bytes used for that run; it is not a lock and does not prevent later changes.

## Current comparison

Exploding Kittens uses two source conditions:

1. the publisher PDF at `inputs/games/expl/game_rules.pdf`;
2. the current clarified text at `inputs/games/expl/variants/expl_clarified.txt`.

Both use the same implementation protocol, evaluator, and reporting code. Native Codex defaults are:

- implementation: `gpt-5.6-sol:low`;
- neutral and persona judges: `gpt-5.6-sol:medium`.

## Evidence

Keep these groups separate:

1. technical gate 01–04;
2. runtime robustness 05;
3. interface 06;
4. cited deterministic scenarios, split into printed rules and approved human decisions;
5. three neutral blind judges;
6. separate rule-fidelity, ambiguity, and executable-systems personas;
7. assumptions, coverage, time, calls, tokens, repairs, and code size.

No combined correctness score is produced. Scenario failures must be attributed as implementation defects, source ambiguity/omission, approved-decision differences, or evaluator defects.

## Artifacts

```text
inputs/                         rulebooks, approved facts, and model prompts
checks/                         executable evaluation logic
generation/                     isolated execution and reporting tools
.pi/skills/                     orchestration instructions only
results/scores/<game>/<run>/    machine-readable and Markdown evidence
results/plots/<game>/<run>/     images only
```

The workflow is improved in place. Existing experimental outputs are never edited to pretend they came from a newer workflow; new evaluations replace the current result view while Git retains the old evidence.
