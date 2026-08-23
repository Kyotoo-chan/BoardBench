# Abalone v3 findings

Evaluator revision only. Implementations are the frozen v2 modules.

Confirmed scored defect under v3:

- **Original:** `ABAL-R01` still fails. Figure 1 requires 14 black and 14 white marbles; the environment starts with 13 of each.

Both setup-emphasis implementations pass every configured v3 scenario (33/33 clear, 4/4 human-decision).

Unscored under v3:

- `ABAL-R19` / `ABAL-G-PASS`. Missing publisher rule. Constructed no-move fixture. Retained as a v2 historical fail for both emphasis runs.

Unscored parser aliases from emphasis replicate 2 remain as in v2.
