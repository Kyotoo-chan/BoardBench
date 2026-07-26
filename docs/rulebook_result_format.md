# Per-rulebook result profile

Each concrete rulebook/edition/condition receives one `result.json` and one derived `result.md`. A clarified appendix is a separate condition. JSON and raw run artifacts are authoritative.

## Evidence groups

Never combine these into one correctness score:

1. identity and hashes;
2. source diagnosis and material assumptions;
3. agentic/technical gate pass rates;
4. runtime robustness;
5. interface quality;
6. clear-basis cited scenarios;
7. human-decision-basis cited scenarios;
8. three neutral blind judges;
9. separate persona findings;
10. tokens, time, calls, repairs, exact cost when available, and code size.

For comparable repeated runs report raw values, arithmetic mean, and sample SD. Sample SD is unavailable for `n=1` because variation requires at least two runs. `UNREACHED` and `UNTESTABLE` affect scenario evaluated coverage, not the scenario pass-rate denominator. A basis score is a pass rate over configured evaluated scenarios; it is not fact coverage or proof that every material clause of a cited fact was asserted. Do not report the runner's mixed clear-plus-human pass rate as a correctness score.

Actual Codex OAuth subscription cost remains `null` when the provider does not expose it. A separate API-equivalent USD estimate may be calculated from measured tokens and the dated public rates in `generation/model_prices.json`; it must never be presented as the amount charged. Persona usage is included when matching persona usage artifacts are present.

## Input specification

`result_spec.json` is a small manifest, not another result file. It has three jobs:

1. identify and hash the source condition;
2. provide presentation labels (`game`, `condition`, `source_format`, `headline`, `source_diagnosis`);
3. point to the raw artifacts that the collector must parse.

Each run requires `stem`, `agentic_evidence`, `checks`, `scenarios`, `usage`, `code`, and exactly three `neutral_reviews`. Current full evaluations also include `assumptions` and the three named `personas`. Model, protocol, thinking, verbosity, and judge settings do **not** belong in the spec: they are read from raw agentic/usage artifacts so the manifest cannot silently override experimental evidence.

`generation/result_card.py` resolves relative paths beside the spec:

```json
{
  "identity": {
    "game": "game",
    "condition": "canonical",
    "source_path": "rules.pdf",
    "source_format": "pdf",
    "source_sha256": "full sha256"
  },
  "source_diagnosis": {
    "clear": 0,
    "human_decision": 0,
    "ambiguous": 0,
    "not_testable": 0
  },
  "headline": "Technically executable; interpret evidence groups separately.",
  "runs": [
    {
      "stem": "game_run1",
      "agentic_evidence": "artifacts/game_run1_agentic_evidence.json",
      "checks": "artifacts/game_run1_checks.txt",
      "scenarios": "artifacts/game_run1_scenarios.json",
      "usage": "artifacts/game_run1_usage.json",
      "code": "artifacts/game_run1.py",
      "assumptions": "artifacts/game_run1_assumptions.json",
      "neutral_reviews": ["artifacts/judge1.md", "artifacts/judge2.md", "artifacts/judge3.md"],
      "personas": {
        "rule_fidelity": "artifacts/persona_rule_fidelity.md",
        "ambiguity": "artifacts/persona_ambiguity.md",
        "executable_systems": "artifacts/persona_executable_systems.md"
      }
    }
  ]
}
```

Run:

```text
python generation/result_card.py --spec result_spec.json --output-dir results/scores/<game>/<run>
```

The collector rejects source-hash mismatches and mixed scenario/adapter hashes. Persona reviews remain references with hashes and never enter the neutral Judge mean. Generation and judge model/thinking settings are recorded separately; defaults are `gpt-5.6-sol:low` for generation and `gpt-5.6-sol:medium` for judges. Future native calls also record an explicit response verbosity of `low`.

## Material assumptions

Future `agentic-v2.2` implementations emit `assumptions.json`. Include only choices affecting legal actions, transitions, private information, elimination, terminal results, or scoring. Keep human-approved, implementation-declared, behavior-inferred, and unresolved assumptions distinct. Raw counts are not comparable across games of different complexity; repeated-run interpretation agreement is meaningful.

## Headline

Use a categorical sentence, for example:

> Technically executable; high pass rate among configured clear-basis scenarios; two decision-sensitive outcomes; all configured scenarios evaluated.

The headline summarizes; it does not replace the evidence table.

## Plots

Keep plots optional and compact. `generation/plot_result.py` accepts one or two result profiles and writes one PNG under `results/plots/<game>/<run>/`. It shows clear-basis scenario pass rate, human-decision-basis scenario pass rate, and neutral-Judge evidence; unchanged technical, robustness, interface, and scenario evaluated coverage values remain separate controls. Comparisons with more than two rulebook conditions are calibration-only and should use tables rather than a crowded main-study plot. Schema-1 result files retain their historical field names; schema 2 uses `clear_basis_scenarios`, `human_decision_basis_scenarios`, and `scenario_evaluated_coverage`.
