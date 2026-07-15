# Exploding Kittens: six input variants

The six implementations remain exactly as committed in experiments 01–06. Evaluator v2 re-runs those frozen modules with corrected facts, deterministic fixtures, explicit outcome classes, and three fresh corrected judges. These runs are now treated as workflow/evaluator pilots: experiment 07 repeats the original PDF with enforced in-agent file validation and is reported separately in `../agentic_rerun/README.md`.

This is a **post-hoc evaluator revision**, not preregistered evidence. The original checks and reviews remain in the numbered experiment commits; v2 artifacts live in `evaluation_v2/` with their own manifest and hashes.

## Evidence groups

The groups answer different questions and are never added into one correctness score.

| Group | Evidence | Meaning |
|---|---|---|
| Technical gate | Checks 01–04 | File, syntax, startup, and required API exist. |
| Runtime robustness | Check 05 | 100 sampled public-action rollouts avoid crashes/dead ends. |
| Interface | Check 06 | Sampled action names are unique, stable, and reversible. |
| Clear-rule scenarios | 10 deterministic cited cases | Expectations follow clear printed rules. |
| Human-decision scenarios | 7 deterministic cited cases | Expectations depend on approved adjudications. |
| Judge mean (n=3) | Three fresh blind corrected reviews | Same-model review signal, not ground truth. |

`PASS`, `FAIL`, `CRASH`, `UNREACHED`, and `UNTESTABLE` are distinct. Scenario fidelity is computed only over `PASS+FAIL+CRASH`; evaluated coverage is reported separately. Evaluator v2 reached and evaluated all 17 cases for all six implementations.

## What changed from evaluator v1

1. The five-card rule was corrected: the five components enter the discard before retrieval, so one may be retrieved immediately.
2. Random reachability was replaced with exact evaluator-only state fixtures for material interactions.
3. Source labels and semantic aliases replace brittle normalized-substring assumptions.
4. Pending NÖ!/reaction and donation phases are resolved before checking the post-effect player.
5. Scenario output natively distinguishes failure, crash, unreached, and untestable.
6. Every v3 scenario records fact IDs and whether its basis is `clear` or `human_decision`.
7. Three fresh judges received the corrected PDF/facts and no check logs, other reviews, scores, or variants.

The old R05–R07 failures were largely evaluator timing errors: several correct implementations were inspected during their intermediate reaction phase. The old anonymized `UNREACHED` results were naming failures even though actions such as `play:preview`, `play:reorder`, and `play:choice` existed.

## Evaluator-v2 scenarios

| ID | Basis | Deterministic expectation |
|---|---|---|
| R01 | clear | Two-player initial state is nonterminal with player 0 and zero returns. |
| R02 | clear | A normal turn exposes a draw/pass action. |
| R03 | clear | Attack moves to the next player with exactly two owed turns. |
| R04 | clear | Two Skips consume two attacked turns one at a time. |
| R05 | clear | Future resolves, reactions close, and the current turn continues. |
| R06 | clear | Shuffle resolves, reactions close, and the current turn continues. |
| R07 | clear | Favor and donation resolve, then the current turn continues. |
| R08 | clear | Drawing a Kitten without Defuse eliminates the player and ends a two-player game. |
| R09 | human decision | Chained Attack replaces remaining debt with exactly two turns. |
| R10 | human decision | A held Defuse cannot be declined. |
| R11 | human decision | Defuse ends only one currently owed turn. |
| R12 | clear | A five-card combination may retrieve one of its five components. |
| R13 | human decision | A discarded Kitten can be retrieved safely into the hand. |
| R14 | human decision | Favor cannot target an empty-handed player. |
| R15 | human decision | Pair theft cannot target an empty-handed player. |
| R16 | human decision | A triple may request a safely held Kitten. |
| R17 | clear | A legal Cat-title pair action is executable and transfers a card. |

### Complete outcome matrix

| Input | R01 | R02 | R03 | R04 | R05 | R06 | R07 | R08 | R09 | R10 | R11 | R12 | R13 | R14 | R15 | R16 | R17 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Original PDF | PASS | PASS | PASS | FAIL | PASS | PASS | PASS | PASS | PASS | PASS | PASS | FAIL | PASS | FAIL | FAIL | PASS | CRASH |
| Faithful TXT | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | FAIL | FAIL | PASS | PASS | FAIL | FAIL | PASS | PASS |
| Anonymized | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | FAIL | FAIL | PASS | PASS | FAIL | FAIL | FAIL | PASS |
| Omissions | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | FAIL | PASS | FAIL | FAIL | PASS | PASS | FAIL | PASS |
| False rules | PASS | PASS | FAIL | FAIL | PASS | PASS | PASS | PASS | FAIL | FAIL | FAIL | PASS | FAIL | FAIL | FAIL | FAIL | PASS |
| Vague rules | PASS | PASS | FAIL | FAIL | FAIL | FAIL | FAIL | PASS | FAIL | PASS | PASS | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL |

## Result overview

The two scenario columns remain separate because one is direct printed-rule evidence and the other depends on human adjudication.

| Input | Technical | Robustness | Interface | Clear rules | Human decisions | Judge mean (n=3) | Judge SD |
|---|---:|---:|---:|---:|---:|---:|---:|
| Original PDF | pass | 0.000 | 0.972 | 7/10 | 5/7 | 0.567 | 0.023 |
| Faithful TXT | pass | 1.000 | 1.000 | 10/10 | 3/7 | 0.773 | 0.031 |
| Anonymized | pass | 1.000 | 1.000 | 10/10 | 2/7 | 0.753 | 0.047 |
| Omissions | pass | 1.000 | 1.000 | 9/10 | 4/7 | 0.727 | 0.012 |
| False rules | pass | 1.000 | 1.000 | 8/10 | 0/7 | 0.480 | 0.053 |
| Vague rules | pass | 1.000 | 1.000 | 3/10 | 2/7 | 0.733 | 0.046 |

### Judge replicates

Main reporting uses only the arithmetic `Judge mean (n=3)`. Individual values remain audit evidence.

| Input | Review 1 | Review 2 | Review 3 |
|---|---:|---:|---:|
| Original PDF | 0.58 | 0.58 | 0.54 |
| Faithful TXT | 0.74 | 0.78 | 0.80 |
| Anonymized | 0.77 | 0.70 | 0.79 |
| Omissions | 0.72 | 0.72 | 0.74 |
| False rules | 0.42 | 0.52 | 0.50 |
| Vague rules | 0.76 | 0.68 | 0.76 |

## Confirmed findings

| Input | Deterministic and review evidence |
|---|---|
| Original PDF | One Skip fails to consume one attacked turn; five-card combination is unavailable with an initially empty discard; empty-handed Favor/pair targets; Cat-title pair parser crashes on its own legal action. |
| Faithful TXT | Defuse may be declined; Defuse under Attack does not consume exactly one owed turn; empty-handed Favor/pair targets. |
| Anonymized | Same Defuse and empty-target deviations; triple cannot request a held Kitten. |
| Omissions | Five-card combination/retrieval is absent as expected from the omitted input; optional Defuse and missing Kitten request remain. |
| False rules | Planted Attack, Skip, and retrieved-Kitten errors are caught; all seven adjudication-dependent scenarios fail. |
| Vague rules | Attack/Skip, named-card turn continuation, five-card behavior, target legality, Kitten request, and Cat-pair continuation fail deterministically. |

The Original-PDF parser failure is now reproduced by R17 rather than discovered only by random rollout:

```text
combo:pair:cat:taco:target:player1
ValueError: invalid literal for int() with base 10: 'target'
```

## What the revised workflow shows

- The previous `3/8–5/8` scenario totals were not reliable rule-fidelity measurements.
- Deterministic state construction removes all current `UNREACHED` cases and exposes the deliberately modified Attack/Skip/Kitten behavior.
- Separating clear rules from human decisions shows why TXT and anonymized implementations can be perfect on clear cases while disagreeing with approved adjudications.
- Three corrected judges detect many defects, but their high vague-input mean (`0.733`) conflicts with the clear-rule scenario result (`3/10`). Same-model judge consensus therefore remains a fallible signal.
- The false-rules condition is detected by both deterministic scenarios and judges, which is the strongest current evaluator-validation result.
- One implementation per condition still cannot separate input effects from generation variance.

## Sensitive workflow safeguards

Project skills now enforce two gates:

- `/bbedge`: material assumptions must be shown with quote, alternatives, affected scenarios, and explicit user approval before a hard expectation is written.
- `/bbeval`: rubric hashes are versioned; deterministic fixtures are preferred; intermediate phases are settled; unresolved cases are excluded; and only `Judge mean (n=...)` is primary judge reporting.

LLMs may propose seeds, traces, or fixture candidates, but a proposal becomes scored evidence only after deterministic replay, human approval, and a later rubric freeze.

## Remaining work before a main study

1. Validate the evaluator with a frozen mutation set and detection matrix.
2. Add deterministic NÖ!/DOCH!, hidden-information, setup-count, and fewer-than-three-card preview cases.
3. Review and freeze every material assumption and exact scenario before new implementations are generated.
4. Run at least three independent implementations per central input condition.
5. Keep raw and clarified-rulebook generation as separate experimental conditions.

## Files and reproducibility

- `evaluation_v2/manifest.json` — frozen implementation commits and evaluator hashes.
- `evaluation_v2/*_checks.txt` / `*_scenarios.json` — grouped reruns and machine-readable outcomes.
- `evaluation_v2/*_judge_*.md` / events / usage — 18 raw corrected judge calls.
- `metrics.csv` / `metrics.json` — combined v1, v2, resource, and audit data.
- `01_evidence_groups.png` — separate robustness, interface, clear-rule, and human-decision groups.
- `02_judge_scores.png` — `Judge mean (n=3)` with sample SD and faint raw points.
- `03_resource_usage.png` — original implementation/run resources.

The corrected judge rerun used 2,212,428 input tokens, 1,636,864 cached input tokens, 88,475 output tokens, 52,785 reasoning tokens, and 42.0 summed provider minutes. Actual subscription cost is unavailable.

```bash
/c/ProgramData/miniconda3/Scripts/conda.exe run -n boardbench python plots/exploding_kittens/variants/reevaluate.py
/c/ProgramData/miniconda3/Scripts/conda.exe run -n boardbench python plots/exploding_kittens/variants/reevaluate.py --judges
/c/ProgramData/miniconda3/Scripts/conda.exe run -n boardbench python plots/exploding_kittens/variants/make_plots.py
```
