# Pair action language alignment

You receive **two** generated BoardBench Python implementations of the same game (`left` and `right`, e.g. oneshot vs agentic) and the BoardBench action normalizer.

Your job is to rewrite **both** files so they expose the **same comparison language** for lockstep benchmark checks. Internal per-file consistency is already tested elsewhere; here the point is **cross-variant agreement**.

## Goal

For the same game state, the same semantic legal move must:

- exist in both implementations (same count of legal actions when rules match)
- normalize to the **same** comparison key in both files after `normalize_action_name(action_to_name(...))`
- use matching raw names where possible, or at least matching normalized keys

Pick one shared naming scheme (prefer the clearer of the two, or a simple neutral scheme) and apply it to **both** files.

## Hard constraints

- Change action naming only (`action_to_name`, `name_to_action`, naming helpers).
- Do not add, remove, or alter legal moves, rules, state transitions, scoring, turn order, or chance logic.
- Do not change what objects `legal_actions` returns.
- Round-trip must still work in **each** file independently.
- No two different legal actions in the same state may share a normalized key within one file.
- The same semantic move in left vs right must not diverge in normalized key after your edit.

## Allowed edits

- `action_to_name`, `name_to_action`, small private naming/parsing helpers, naming comments

## Forbidden edits

- `legal_actions`, `apply_action`, win detection, setup, player logic
- inventing actions or dropping existing ones
- replacing either file with a different implementation

## Output

1. Short `Pair action naming changes` section: shared convention and main renames.
2. **Exactly two** fenced `python` code blocks, in this order:
   - first block: full updated **left** file
   - second block: full updated **right** file

Do not output a single combined file. Do not swap the order.
