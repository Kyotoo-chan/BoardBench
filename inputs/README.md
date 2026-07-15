# Inputs

```text
inputs/games/<slug>/             canonical rulebook and approved facts
inputs/games/<slug>/variants/    optional current comparison source
inputs/prompts/                  prompts sent to models
```

Use the publisher's native PDF or TXT as the canonical source. A clarified text is a separate condition and must visibly label its additions.

## Why SHA-256 is retained

SHA-256 is a short fingerprint of file bytes. It lets a result prove which exact rulebook or evaluator file it used and catches accidental changes. It uses Python's standard library and adds no runtime cost worth measuring. It does **not** freeze a file: the workflow may change at any time, after which a new run records the new fingerprint while Git retains the previous state.

The current Exploding Kittens comparison uses only:

- `inputs/games/expl/game_rules.pdf`;
- `inputs/games/expl/variants/expl_clarified.txt`.
