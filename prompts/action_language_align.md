# Action language alignment

You receive a generated BoardBench Python game file and the BoardBench action normalizer.

Your only job is to make `action_to_name` and `name_to_action` emit a stable, unambiguous comparison language for the optional OpenSpiel reference comparison. This step runs only when that comparison is enabled.

## Hard constraints

- Change action naming only.
- Do not add, remove, or alter legal moves.
- Do not change game rules, state transitions, scoring, turn order, chance logic, or API behavior outside action naming.
- Do not change what objects `legal_actions` returns.
- `action_to_name(action)` and `name_to_action(name)` must still round-trip exactly for every legal action in sampled states.
- Every legal action in a state must keep a distinct raw name and a distinct normalized comparison key.
- Two different legal actions must not normalize to the same key.
- Prefer simple explicit names such as `place:<target>`, `move:<source>-><target>`, `remove:<target>`, `pass`, or `chance:<kind>:<value>`.
- Avoid coordinate formats that collide after normalization, for example signed `q+1,r-6` and `q-1,r-6` both becoming the same key; use explicit sign words such as `pos`/`neg` or `p`/`n`.
- If the rule text, code, or provided reference context already defines board labels, use those labels consistently.

## Allowed edits

- `action_to_name`
- `name_to_action`
- small private helpers used only for action naming and parsing
- comments that document naming assumptions

## Forbidden edits

- changing `legal_actions`, `apply_action`, win detection, board setup, or player turn logic
- inventing new actions or dropping existing ones
- replacing the whole file with a different implementation

## Output

1. A short `Action naming changes` section listing what you renamed and why.
2. One fenced `python` code block with the full updated file.
