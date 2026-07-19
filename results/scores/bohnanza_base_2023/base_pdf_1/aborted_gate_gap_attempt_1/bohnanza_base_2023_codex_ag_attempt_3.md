Repaired `assumptions.json` by adding all canonical required fields to each assumption. No gameplay implementation or protected files were changed.

Validation passed:

```text
python -m py_compile implementation.py
PASS

python agentic_self_check.py
agentic-self-check OK states=300 actions=5323

python profile_fixture_self_check.py
profile-fixture-self-check OK
```