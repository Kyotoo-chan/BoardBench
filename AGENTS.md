# AGENTS.md

## Purpose

BoardBench is a bachelor-thesis workflow inspired by PaperBench:

1. start from one publisher rule packet (one primary rulebook and, only when that rulebook explicitly requires it, one matching official companion such as an almanac), optionally with a clearly attributed component appendix,
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

1. User places one active rulebook at `inputs/game_rules.pdf` or `.txt`; when that source explicitly delegates rules to a matching official companion, the user may add it as `inputs/game_almanac.pdf` or `.txt`; the user may also add one user-authored component inventory at `inputs/game_components.pdf`, `.txt`, or `.json`.
2. `bbedge` archives and hashes each assigned source separately, verifies the companion’s edition match instead of mixing editions, records provenance and role, then rule facts, conflicts, and edge cases are discussed with the user.
3. Approved facts live at `inputs/games/<slug>/rulefacts.md`; executable cases live at `checks/scenarios/<slug>.json`.
4. `bbimpl` generates one agentic implementation in an isolated workspace that cannot see evaluator scenarios.
5. `bbeval` reports technical, robustness, interface, scenario, and judge evidence separately.

Do not continue past material ambiguities without user approval.

## Scientific rules

- Use only the supplied source condition for game rules; no remembered or web rules unless an experiment explicitly tests extra context.
- Original PDFs remain the canonical source artifacts. Every model-facing packet that uses a PDF includes that PDF plus freshly rendered images of every page at 150 DPI from `generation/pdf_pages.py`; extracted text is only a derived search aid and never replaces the PDF. Record the PDF hash, renderer/version, DPI, and rendered-page hashes. Never crop a PDF to hide excluded variants; declare the approved scope in the source manifest and model prompt. A clarified condition keeps the same PDF packet and adds a separate attributed, user-approved clarification artifact instead of rewriting the source into normalized text.
- A user-authored component appendix is an augmented source, not part of the publisher rulebook. By default it is `user_observation`: it may support hard component inventory/setup expectations, but may not silently override gameplay rules.
- Hash and cite every source separately. Every hard scenario expectation needs source ID, edition/hash, a stable locator (PDF page or JSON Pointer), and direct source evidence.
- Surface every cross-source conflict with both citations, alternatives, affected behavior, and a user-approved decision; never apply automatic precedence.
- Keep ambiguous and untestable rules visible instead of scoring them as failures.
- New contract-v2 generations must implement the frozen canonical state/action data profile. Scenario evaluators use only that public data contract, never generated attributes, tuple positions, module constants, or guessed aliases. Legacy introspective replays remain separately labelled.
- Judges are fallible signals. Critical/major findings need quote, page, code location, and expected/actual behaviour.
- Do not combine smoke checks, rollouts, action naming, judges, and scenarios into one claim of correctness.
- Keep raw generations, raw reviews, code, logs, model/thinking settings, and timings.
- Each source-condition run produces one final scored implementation. Pre-evaluation crashes, technical/API/self-check failures, or objectively source-required omissions may be repaired or reimplemented only inside the same blind isolated workflow; record every attempt, reason, and repair count, retain its raw evidence, and score only the final gate-passing implementation. Repair attempts are not separate generations. If the bounded repair loop does not pass, record a failed run; never repair after evaluation under the same run ID.
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

Canonical generation artifacts:

- `<stem>.md` — raw generation response
- `<stem>.py` — final generated module
- `<stem>_events.jsonl` — raw generation events
- `<stem>_agentic.json` — consolidated model/usage, source/render manifest, repair, gate, and artifact evidence
- `<stem>_assumptions.json` — material source assumptions
- `<stem>_rule_coverage.md` — source audit
- `<stem>_task.txt` — exact generation task
- `<stem>_checks.txt` — grouped check log
- `<stem>_judge_<label>.md` — raw judge review added during evaluation

`outputs/` is a flat **single-active-run workspace**: never mix games or run stems. Before every new generation, the current output artifacts must already be committed, then `python generation/clean_outputs.py` removes them and `python generation/clean_outputs.py --check-empty` verifies the clean start. The next run commit includes those tracked deletions plus its new artifacts, so Git history retains every prior run. Do not create duplicate response/meta/status/manifest files when their content is already preserved by the canonical artifacts above. Do not gitignore generated thesis artifacts. Temporary workspaces and judge packets are not committed.

Do not delete or rewrite `QUESTIONS.txt`; it is user-maintained. Preserve meeting notes and historical pilot artifacts.

## Code style

Prefer plain Python, standard library, explicit state, small functions, and readable assumptions. Avoid provider frameworks, large abstractions, hidden automation, or RL infrastructure unless requested.

## Git

This is currently a solo repository: commit directly on `main` when the user requests commits. Follow the global `/skill:gc` workflow. Prefer large coherent commits, short clear lowercase messages, no co-author trailers, and no pushes unless requested.
