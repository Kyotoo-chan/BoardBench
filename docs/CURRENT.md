# Current state

BoardBench is preparing the first fixed four-player CATAN 2022 stress case. The assigned publisher packet is the matching German Spielanleitung plus the explicitly referenced 2022 Almanach; older candidate almanacs are archived but excluded. Rules, approved material decisions, a canonical data profile, and cited scenarios are prepared before implementation generation.

Bohnanza Base Game 2023 remains workflow-calibration evidence: the current replacement comparison scored 34/41 for the publisher-PDF run and 39/41 for the clarified run. It is no longer in the active shared input slots.

## Source of truth

- `inputs/game_rules.pdf` and `inputs/game_almanac.pdf` — active CATAN sources.
- `inputs/games/catan/` — archived assigned sources, approved facts, profile, and local fixture self-check.
- `checks/scenarios/catan.json` and `checks/scenario_adapters/catan.py` — current cited evaluator packet.
- `inputs/games/bohnanza_base_2023*/` and `results/scores/bohnanza_base_2023/` — retained calibration evidence.
- `inputs/prompts/`, `generation/`, and `.pi/skills/` — implementation/judge prompts and isolated workflow tooling.

## Current settings

- new generations are agentic; one-shot runs are historical pilots;
- implementation default: `gpt-5.6-sol:low`;
- judges: `gpt-5.6-sol:medium`, three independent reviews per run;
- CATAN condition: fixed beginner board, four players, strict roll → trade → build;
- no CATAN implementation or evaluation run has started.

Every run records exact source, prompt, profile, suite, adapter, runner, model/thinking, and artifact hashes locally. Git preserves superseded evidence.
