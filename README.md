# BoardBench

BoardBench is a bachelor-thesis workflow inspired by PaperBench. An LLM agent translates a board-game rulebook into an executable Python environment; cited edge cases and separate evaluator groups show what runs, what matches the rules, and what remains ambiguous.

## Layout

- `inputs/` — active and archived rulebooks plus approved rule facts
- `prompts/` — short generation, scenario, and review prompts
- `outputs/` — raw responses, generated modules, logs, and reviews
- `checks/` — technical checks and rulebook-cited scenarios
- `generation/` — workflow helpers and historical backend runners
- `docs/` — thesis decisions, workflow notes, and historical analysis
- `plots/` — pilot result presentation; redesign currently deferred
- `.pi/skills/` — project-local BoardBench commands
- `.pi/agents/` — project-local rule-analysis, implementation, and review roles

## New default workflow

Place exactly one rulebook at `inputs/game_rules.pdf` or `inputs/game_rules.txt`, then use:

```text
/skill:bbedge game=<slug>
/skill:bbimpl game=<slug>
/skill:bbeval game=<slug>
```

Use `/skill:bb status game=<slug>` when the next phase is unclear.

Default model:

```text
openai-codex/gpt-5.6-sol:low
```

Force and configure child agents per command with:

```text
subagents=on submodel=<provider/model> subthinking=<level>
```

Without explicit child settings, the parent chooses an equal or weaker configuration; children may not exceed the parent model/thinking.

The workflow is agentic-only for new experiments. One-shot notebooks and backend series remain as historical pilot infrastructure.

## Evaluation groups

- technical gate: checks 01–04
- runtime robustness: check 05
- action interface: check 06
- rule fidelity: cited scenarios
- independent LLM review
- optional OpenSpiel reference, treated as secondary

These groups are not interchangeable evidence and should not be collapsed into a claim of complete correctness.

## Documentation

- `AGENTS.md` — concise project rules
- `docs/workflow_description.md` — command and model details
- `docs/projektgespraech_offene_fragen_und_weiterarbeit.md` — thesis direction and priorities
- `docs/thesis_decisions_and_changes.md` — methodological rationale and change record
- `TODO.md` — next concrete work

Run Python commands in the `boardbench` Conda environment.
