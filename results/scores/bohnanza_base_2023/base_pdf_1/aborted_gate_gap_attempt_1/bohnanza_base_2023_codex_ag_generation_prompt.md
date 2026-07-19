You are the sole implementation agent in an isolated BoardBench workspace.

Read `SOURCE_MANIFEST.md` and `IMPLEMENTATION_TASK.txt` completely, then inspect every supplied source and all attached fresh PDF page images. Implement the complete assigned 4-5-player source condition.

Use only files in this workspace as game-rule evidence. Do not use remembered rules, web knowledge, benchmark scenarios, evaluator facts, prior implementations, or assumptions from the game title.

Create the actual files `implementation.py`, `rule_coverage.md`, and schema-valid `assumptions.json`. Audit every supplied section and named bean/rule into coverage. Run exactly:

python -m py_compile implementation.py
python agentic_self_check.py

Repair every failure. Do not modify `agentic_self_check.py`.


This packet also contains `profile_fixture_self_check.py`. Run it after `agentic_self_check.py`; it checks representation-only complete fixtures and contains no rule expectations.
