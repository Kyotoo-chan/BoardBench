# Bohnanza Base 2023 corrected packet preflight

Status: **PASSED after rejecting attempts 1 and 2**

- Attempt 1 exposed a missing full-public-API gate (`render`).
- Attempt 2 exposed that the packet contained an obsolete short inline task instead of the frozen implementation prompt and therefore omitted the assumptions schema.
- Both attempts were rejected before judging and remain separately labelled.

The packet now contains the byte-exact frozen `inputs/prompts/rulebook_to_python.txt` content plus the profile-fixture command. A regression test checks that `TASK.txt` contains the required material-assumptions schema, names `profile_fixture_self_check.py`, and does not reference the obsolete task filename.

Corrected validation:

- 34 focused tests pass.
- Full 14-method public/canonical API gate passes the infrastructure probe.
- Complete rare-state fixture gate passes.
- All 31 evaluator fixtures remain representable with zero crash/untestable outcomes.
- Manifest/hash dry run passes.
- No accepted run or Judge exists; `outputs/` remains clean.
