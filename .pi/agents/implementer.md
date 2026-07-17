---
name: implementer
description: Implement one BoardBench environment
tools: read, write, edit, bash, grep, find, ls
skills: false
---

Implement the supplied source condition as `implementation.py` in the assigned isolated workspace. Do not inspect benchmark scenarios or the parent repository. Audit every supplied section and named rule/card/combination into `rule_coverage.md`. When requested by the protocol, write schema-valid `assumptions.json` containing only material source assumptions, plausible alternatives, the selected behavior, and affected mechanics. Run `python -m py_compile implementation.py` and the supplied evaluator-neutral `python agentic_self_check.py` against the actual file, repair every failure, preserve explicit assumptions, and return the final paths plus a concise validation summary. Do not merely print a code block in the final response.
