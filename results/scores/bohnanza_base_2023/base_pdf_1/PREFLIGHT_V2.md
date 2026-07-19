# Bohnanza Base 2023 corrected preflight

Status: **SUPERSEDED after rejected attempt 2**

Attempt 1 was rejected before judging because the previous neutral gate omitted the required `render` method. Its raw artifacts are preserved under `aborted_gate_gap_attempt_1/` and are not scored.

The corrected `agentic_self_check.py` now enforces all 14 required public and canonical methods, including `render`, and verifies that `render` returns text. The exact infrastructure was rehashed in the frozen manifest before another model call.

Validation after correction:

- 34 focused regression tests pass, including a missing-`render` rejection test.
- Reachable-state infrastructure probe: 300 states / 5400 actions, pass.
- Complete profile-fixture probe: pass.
- 31/31 scenario fixtures execute with zero crashes and zero untestable outcomes through the infrastructure probe.
- Frozen packet/hash dry run: pass.
- No accepted run, Judge, or `outputs/` artifact existed.

## Discovered packet gap

Attempt 2 revealed that the runner wrote its obsolete short inline prompt to `TASK.txt` rather than the frozen `inputs/prompts/rulebook_to_python.txt`. The model therefore never received the required assumptions schema. The attempt was rejected before judging and preserved under `aborted_prompt_mismatch_attempt_2/`. The packet test now checks the actual task contents.
