# Per-rulebook result profile

Each concrete rulebook/edition/condition receives one `result.json` and one derived `result.md`. A clarified appendix is a separate condition. JSON and raw run artifacts are authoritative.

## Evidence groups

Never combine these into one correctness score:

1. identity and hashes;
2. source diagnosis and material assumptions;
3. agentic/technical gate pass rates;
4. runtime robustness;
5. interface quality;
6. clear cited scenarios;
7. approved human-decision scenarios;
8. three neutral blind judges;
9. separate persona findings;
10. tokens, time, calls, repairs, exact cost when available, and code size.

For comparable repeated runs report raw values, arithmetic mean, and sample SD. `UNREACHED` and `UNTESTABLE` affect coverage, not the fidelity denominator. Missing monetary cost is `null`, never estimated.

## Input specification

`generation/result_card.py` consumes a JSON spec whose relative paths are resolved beside that spec:

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

The collector rejects source-hash mismatches and mixed scenario/adapter hashes. Persona reviews remain references with hashes and never enter the neutral Judge mean. Generation and judge model/thinking settings are recorded separately; defaults are `gpt-5.6-sol:low` for generation and `gpt-5.6-sol:medium` for judges.

## Material assumptions

Future `agentic-v2.2` implementations emit `assumptions.json`. Include only choices affecting legal actions, transitions, private information, elimination, terminal results, or scoring. Keep human-approved, implementation-declared, behavior-inferred, and unresolved assumptions distinct. Raw counts are not comparable across games of different complexity; repeated-run interpretation agreement is meaningful.

## Headline

Use a categorical sentence, for example:

> Technically executable; high clear-rule fidelity; two ambiguity-sensitive outcomes; full evaluated coverage.

The headline summarizes; it does not replace the evidence table.

## Plots

Keep plots optional and compact. `generation/plot_result.py` accepts one or two result profiles and writes one PNG under `results/plots/<game>/<run>/`. It shows the separated evidence groups, run count, gate rates, and the actual generation/judge settings. Comparisons with more than two rulebook conditions are calibration-only and should use tables rather than a crowded main-study plot.
