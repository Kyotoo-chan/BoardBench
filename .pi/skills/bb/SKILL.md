---
name: bb
description: Show status and route the next BoardBench phase.
---

# BoardBench workflow

Arguments:

```text
status | edge | impl | eval
 game=<slug>
 subagents=auto|on|off
 submodel=<provider/model>
 subthinking=off|minimal|low|medium|high|xhigh
```

`model=` and `thinking=` are accepted aliases for `submodel=` and `subthinking=`.

## Subagent policy

- `subagents=on`: use the project agents required by the phase.
- `subagents=off`: do not launch agents.
- `subagents=auto` or omitted: the parent decides.
- Explicit `submodel`/`subthinking` must be passed to `Agent` exactly.
- Without explicit values, the parent may inherit its own model/thinking or choose a demonstrably weaker setting. A child must never receive a stronger model or higher thinking than the parent. If strength is uncertain, inherit the parent by omitting `model` and `thinking`.

Thinking order: `off < minimal < low < medium < high < xhigh`.

## Route

1. Inspect the active rulebook and matching game artifacts.
2. Report the current phase in at most five lines.
3. Load `bbedge`, `bbimpl`, or `bbeval` for the requested phase.
4. For `status`, recommend exactly one next command.

Do not implement before material ambiguities are approved. Do not create plots; presentation remains deferred.
