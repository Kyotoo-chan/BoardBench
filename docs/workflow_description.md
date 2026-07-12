# BoardBench agentic workflow

Project-local pi skills are the primary interface. One-shot and pair-comparison tooling has been removed from the working tree; its pilot history remains in Git.

## Start

Place one rulebook at `inputs/game_rules.pdf` or `.txt`, then run:

```text
/skill:bbedge game=<slug>
/skill:bbimpl game=<slug>
/skill:bbeval game=<slug>
```

Use `/skill:bb status game=<slug>` when the next phase is unclear.

## Subagents

BoardBench uses `npm:@tintinweb/pi-subagents` with project roles in `.pi/agents/`:

- `ruleanalyst`
- `edgereviewer`
- `implementer`
- `rulereviewer`

Control them explicitly:

```text
subagents=on|off|auto
submodel=<provider/model>
subthinking=off|minimal|low|medium|high|xhigh
```

Example:

```text
/skill:bbedge game=conect subagents=on submodel=openai-codex/gpt-5.6-sol subthinking=low
```

`model=` and `thinking=` remain accepted aliases.

If child settings are omitted, the parent decides. It may inherit its own configuration or choose a demonstrably weaker one. It must never assign a stronger model or higher thinking than itself. If model strength is unclear, inherit. Explicit user settings override this cap.

## Phases

### Edge cases

`bbedge` archives and hashes the rulebook. When enabled, two read-only agents independently extract cited facts and challenge edge cases. Material ambiguities are decided with the user before `rulefacts.md` is marked approved.

### Implementation

`bbimpl` gives one writer agent an isolated workspace containing the rulebook, approved facts, and short prompt. Evaluator scenarios and repository checks are withheld. The raw response and module are saved under `outputs/<slug>_<backend>_ag.*`.

### Evaluation

`bbeval` keeps evidence separate:

1. technical checks 01–04,
2. runtime robustness 05,
3. interface 06,
4. cited rulebook scenarios,
5. independent rule review,
6. optional OpenSpiel reference when explicitly requested.

OpenSpiel is secondary because the final method must work without a reference implementation.

## Thinking

The parent currently defaults to `openai-codex/gpt-5.6-sol:low`. Good prompts reduce procedural uncertainty, but not genuine rule ambiguity. Escalate only for a documented conflict or failed low-thinking attempt; treat the escalation as a separate experimental condition.

## Manual fallback

`evaluation.ipynb` is agentic-only and defaults to Pi/Sol Low. It remains a transparent manual fallback. The preferred workflow is skill-driven.

## Git

Use global `/skill:gc`. BoardBench is solo, so requested commits go directly to `main`, with large coherent commits, short lowercase messages, no co-author trailers, and no push unless requested.
