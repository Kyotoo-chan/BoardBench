Open blocker: the workspace is mounted read-only. The sandbox rejected creating `implementation.py`, `rule_coverage.md`, and `assumptions.json`; no files were changed.

Validation attempts:

- `python -m py_compile implementation.py` — blocked by sandbox policy.
- `python agentic_self_check.py` — blocked by sandbox policy.

A writable workspace and executable Python permission are required to complete the implementation.