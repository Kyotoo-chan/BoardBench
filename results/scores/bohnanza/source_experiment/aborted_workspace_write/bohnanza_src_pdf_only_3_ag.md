1. Open questions/material assumptions: blocked before implementation because the workspace is mounted read-only and approval is disabled.

2. Files changed: none. Creating `implementation.py`, `rule_coverage.md`, and `assumptions.json` was rejected by the sandbox.

3. Validation outcomes:

- `python -m py_compile implementation.py` — not run; file could not be created.
- `python agentic_self_check.py` — not run; implementation could not be created.

Please rerun with workspace write access enabled.