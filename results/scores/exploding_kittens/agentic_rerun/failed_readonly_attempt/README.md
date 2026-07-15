# Failed agentic PDF rerun attempt

This is infrastructure-failure evidence, not an implementation experiment.

On 2026-07-15, Codex was launched with `workspace-write` on the Windows host. The current Codex sandbox degraded to read-only: all three calls could inspect the task but were denied permission to create `implementation.py` or run the required validation commands. The independent gate correctly rejected the run and no implementation was produced.

The raw responses, JSONL events, prompts, and usage records are preserved here rather than silently discarded. Totals: 3 calls, 486,377 input tokens, 389,888 cached input tokens, 21,343 output tokens, 5,148 reasoning tokens, and 507.751 provider seconds.

The follow-up protocol creates the implementation workspace outside the repository and uses Codex `danger-full-access`; the workspace contains only the assigned source, rendered pages, and evaluator-neutral self-check and is deleted afterward. Repository checks and cited scenarios remain unavailable to the implementer.
