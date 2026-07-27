# Attempt 1

1. Material assumptions: deterministic player-0 start; Attack replaces owed turns with two; clockwise NÖ! response windows with parity-based cancellation.

2. Files changed: `implementation.py`, `rule_coverage.md`, `assumptions.json`.

3. Validation:

- `python -m py_compile implementation.py` — passed.
- `python agentic_self_check.py` — failed because the check requires schema suffix `/1`, while `GAME_PROFILE.json` explicitly requires `/2`.
- Additional `python profile_fixture_self_check.py` — passed.

# Attempt 2

Open assumptions remain A-01 through A-03: NÖ! response timing, stacked Angriff behavior, and deterministic starting player.

Files:

- `implementation.py` — tightened state/action contract validation.
- `rule_coverage.md` — unchanged.
- `assumptions.json` — unchanged.
- No packet files modified.

Validation:

- `python -m py_compile implementation.py` — passed.
- `python profile_fixture_self_check.py` — `profile-fixture-self-check OK`.
- Negative contract checks — passed.
- `python agentic_self_check.py` — fails because it hard-codes `/1`; `GAME_PROFILE.json` requires `/2`. The `/2` public contract was preserved.

# Attempt 3

Open questions/material assumptions: A-01 through A-03 remain documented; no new game-rule assumptions were introduced. The generic self-check has a contract conflict: it requires `/1` schemas while `GAME_PROFILE.json` requires `/2`.

Files:

- `implementation.py` — tightened JSON-domain validation, prevented invalid empty-deck draws, restored source-label action names.
- `rule_coverage.md` — retained.
- `assumptions.json` — retained.

Validation:

- `python -m py_compile implementation.py` — PASS
- `python profile_fixture_self_check.py` — PASS (`profile-fixture-self-check OK`)
- Strict contract probe — PASS
- `python agentic_self_check.py` — FAIL at its hardcoded `/1` schema assertion; the implementation correctly emits the profile-required `/2` schemas.
