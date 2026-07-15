# AGENTS.md

## Purpose

BoardBench is a bachelor-thesis workflow inspired by PaperBench:

1. start from one board-game rulebook,
2. turn its rules and edge cases into explicit, cited expectations,
3. let an LLM agent implement a Python game environment,
4. evaluate technical quality and rule fidelity as separate evidence groups.

The thesis asks which problems appear when an LLM translates a board-game rulebook into an executable environment and which problems are reduced when detected gaps are explicitly clarified before a fresh generation. This original-versus-clarified intervention helps distinguish source-specification effects from model and evaluator failures; a code failure alone is not proof that the rulebook is bad.

## Current direction

- Use **agentic generation** for new runs. One-shot remains historical pilot data.
- Parent default: `openai-codex/gpt-5.6-sol`, thinking `low`.
- Workflow commands accept `subagents=on|off|auto`, `submodel=...`, and `subthinking=...`.
- Without an explicit child setting, the parent chooses equal or demonstrably weaker capability. A child must never receive a stronger model or higher thinking than its parent; if uncertain, inherit by omitting both fields.
- Optimize the workflow before redesigning plots or aggregate scores.

Subagents are provided by `npm:@tintinweb/pi-subagents`. Project roles live in `.pi/agents/` and intentionally do not pin model or thinking.

Project-local workflow skills:

- `/bb` — status/router
- `/bbedge` — rule facts, ambiguities, edge cases
- `/bbimpl` — isolated agentic implementation
- `/bbeval` — grouped evaluation

## Minimal workflow

1. User places exactly one active rulebook at `inputs/game_rules.pdf` or `.txt`.
2. `bbedge` archives and hashes it, then rule facts and edge cases are discussed with the user.
3. Approved facts live at `inputs/games/<slug>/rulefacts.md`; executable cases live at `checks/scenarios/<slug>.json`.
4. `bbimpl` generates one agentic implementation in an isolated workspace that cannot see evaluator scenarios.
5. `bbeval` reports technical, robustness, interface, scenario, and judge evidence separately.

Do not continue past material ambiguities without user approval.

## Scientific rules

- Use only the supplied rulebook for game rules; no remembered or web rules unless an experiment explicitly tests extra context.
- Every hard scenario expectation needs rulebook edition/hash, page, and direct quote.
- Keep ambiguous and untestable rules visible instead of scoring them as failures.
- Judges are fallible signals. Critical/major findings need quote, page, code location, and expected/actual behaviour.
- Do not combine smoke checks, rollouts, action naming, judges, and scenarios into one claim of correctness.
- Keep raw generations, raw reviews, code, logs, model/thinking settings, and timings.
- Never silently rewrite old experimental results after methodology changes.

## Evaluation groups

1. **Technical gate:** checks 01–04.
2. **Runtime robustness:** check 05.
3. **Interface:** check 06.
4. **Rule fidelity:** cited scenarios.
5. **Independent review:** LLM judges with uncertainty.

Run Python and checks through the `boardbench` Conda environment. In Git Bash use:

```bash
/c/ProgramData/miniconda3/Scripts/conda.exe run -n boardbench ...
```

Do not run a full evaluation unless the user asks for it.

## Repository and artifacts

Keep the repository simple: `inputs/`, `outputs/`, `checks/`, `generation/`, `docs/`, and `results/`. Model prompts live under `inputs/prompts/`. Store score data under `results/scores/<game>/<run>/` and images only under `results/plots/<game>/<run>/`; plotting code belongs in `generation/`.

New agentic run stem:

```text
<game>_<backend>_ag
```

Standard artifacts:

- `<stem>.md` — raw generation
- `<stem>.py` — generated module
- `<stem>_checks.txt` — grouped check log
- `<stem>_judge_<label>.md` — raw judge review

`outputs/` is flat. Do not gitignore generated thesis artifacts. Temporary workspaces and judge packets are not committed.

Do not delete or rewrite `QUESTIONS.txt`; it is user-maintained. Preserve meeting notes and historical pilot artifacts.

## Code style

Prefer plain Python, standard library, explicit state, small functions, and readable assumptions. Avoid provider frameworks, large abstractions, hidden automation, or RL infrastructure unless requested.

## Git

This is currently a solo repository: commit directly on `main` when the user requests commits. Follow the global `/skill:gc` workflow. Prefer large coherent commits, short clear lowercase messages, no co-author trailers, and no pushes unless requested.
