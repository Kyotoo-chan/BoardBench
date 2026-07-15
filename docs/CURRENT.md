# Current state

BoardBench currently focuses on one clean Exploding Kittens comparison: publisher PDF versus a clarified text condition.

## Source of truth

- `inputs/games/expl/` — rule sources and approved cited facts.
- `inputs/prompts/` — text sent to implementation and judge models.
- `checks/` — executable checks and scenario expectations. A skill cannot make a scenario pass or fail.
- `generation/` — isolated Codex execution, result collection, and plotting.
- `.pi/skills/` — user-facing orchestration instructions; they call the workflow but contain no hidden scoring logic.
- `results/scores/exploding_kittens/<condition>/` — current evidence and raw artifacts.
- `results/plots/exploding_kittens/<comparison>/` — presentation images only.

## Current settings

- implementation generation: `gpt-5.6-sol:low`;
- neutral and persona judges: `gpt-5.6-sol:medium`;
- no OpenSpiel or one-shot comparison;
- one canonical and at most one clarified source condition.

SHA-256 values identify the exact source/evaluator bytes used in a run. They are lightweight provenance, not workflow locks.
