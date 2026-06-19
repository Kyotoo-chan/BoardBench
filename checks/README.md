# Checks

This folder contains small checks for the generated game result, not for the input workflow.

Run the normal result checks from the `Generated result checks` cell in `evaluation.ipynb`, or from the repository root:

```bash
python checks/run_checks.py --game antichess --code-path outputs/antichess.py
```

The normal checks verify that:

1. a generated result file exists
2. the result is Python syntax in a `.py` file
3. the game can be imported and started
4. the required minimal API is present
5. 100 random-agent rollouts run without crashes or invalid dead states

The random rollout check is capped by `--max-steps`; reaching that cap is not a failure if no state crashed.

Run one check by name:

```bash
python checks/run_checks.py --check check_05_random_rollouts
```

Run the optional final OpenSpiel comparison:

```bash
python checks/run_checks.py --include-final
```

The final comparison alternates between OpenSpiel-driven and generated-game-driven random rollouts, matching actions by canonical action names where possible.
