# Inputs

```text
inputs/game_rules.pdf|txt        active primary rulebook
inputs/game_components.pdf|txt|json  optional user-authored component inventory
inputs/games/<slug>/             archived source condition and approved facts
inputs/games/<slug>/environment_profile.json  frozen evaluator representation profile
inputs/games/<slug>/variants/    optional current comparison source
inputs/prompts/                  prompts sent to models
```

`inputs/prompts/environment_contract.md` plus each game's `environment_profile.json` define only the canonical machine representation used across generated implementations. They are shared unchanged across compared source conditions, hashed with the run, and must not contain hidden scenarios or expected outcomes.

Use the publisher's native PDF or TXT as the canonical rules source. An optional user-authored PDF, TXT, or JSON component inventory makes the input an augmented source condition: hash and cite it separately as `user_observation`, use stable JSON Pointers for JSON facts, and never let it silently override gameplay rules. A clarified text is a separate condition and must visibly label its additions.

## Why SHA-256 is retained

SHA-256 is a short fingerprint of file bytes. It lets a result prove which exact rulebook or evaluator file it used and catches accidental changes. It uses Python's standard library and adds no runtime cost worth measuring. It does **not** freeze a file: the workflow may change at any time, after which a new run records the new fingerprint while Git retains the previous state.

The current Exploding Kittens comparison uses only:

- `inputs/games/expl/game_rules.pdf`;
- `inputs/games/expl/variants/expl_clarified.txt`.
