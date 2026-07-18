# Artifact and isolation audit

## Completed valid corpus

- 12/12 valid generations completed in the frozen round-robin order.
- 36/36 neutral judges completed afterward, three per run.
- 228/228 expected raw run artifacts existed before aggregation: 120 generation/evaluation artifacts and 108 judge artifacts; none were missing, extra, or empty.
- All 108 JSON files and 48 completed-run JSONL logs parsed successfully.
- All 12 agentic evidence records report protocol `agentic-v2.2`, `gpt-5.6-sol`, low generation thinking, self-check execution, independent-gate success, and matching implementation hashes.
- All 36 judges used `gpt-5.6-sol`, medium thinking, low verbosity, read-only mode, and exited successfully.
- Generation calls used `danger-full-access` inside opaque temporary packets after the documented Windows `workspace-write` protocol failure.

## Isolation audit

After path normalization and case folding, the 48 valid generation/judge event logs contain zero occurrences of the absolute BoardBench repository path. The preflight canary is the deliberate exception outside the valid corpus because its prompt explicitly supplied that path.

This is evidence of clean disclosed tool use, not proof of hard filesystem isolation. The canary demonstrated that undisclosed external reads remained technically possible.

## Frozen evaluator

All 12 scenario results agree on:

- rubric `bohnanza-source-experiment-2026-07-18`;
- 37 scenarios;
- suite SHA-256 `b4379824582b08eba24b3262ab593d01fdb078dbd6a483963ac36bdf2e1f7265`;
- adapter SHA-256 `e480e6ffa83602745c860ab7f821ddf1996c82af0dc7397ec32d3c36bdcc66bb`.

These and the seven other frozen source/prompt hashes match `checks/mutations/bohnanza_source_experiment.json` and the current files.

## Evaluation completeness

- Technical checks 01–04: 12/12 pass.
- Robustness check 05: 11/12 pass; `json_mutated_1` scored 0.630 after a `list index out of range` crash.
- Interface check 06: 11/12 pass; the same run failed execution despite a rounded action-language score of 1.000.
- Across 444 scenario outcomes: 49 PASS, 164 FAIL, 106 CRASH, 0 UNREACHED, and 125 UNTESTABLE.
- All 36 judge reports contain parseable terminal scores from 0.10 to 0.63 with high confidence. Seventeen used the requested code fence; 19 supplied the same fields unfenced.

## Preserved excluded protocol attempts

`aborted_workspace_write/` preserves the condition-independent instrumentation failure that occurred immediately after Go: all 12 calls were prevented from writing by Windows Codex despite requesting `workspace-write`. It contains 80 raw/error artifacts plus the original progress snapshot. Eleven calls have complete event/usage bundles; the first was cleaned by the initial runner bug and is represented only by its recorded error and empty output. None is aggregated as a valid repetition.

## Residual risks

1. Hard read isolation was not achieved.
2. Generic check logs do not embed their own code hash; scenario JSON does.
3. Presence, hashes, and schemas were audited, but every natural-language coverage claim was not independently re-adjudicated.
4. Downstream judge parsing must accept both fenced and unfenced terminal blocks.
