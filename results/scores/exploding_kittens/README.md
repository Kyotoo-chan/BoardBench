# Exploding Kittens — current comparison

Two fresh implementations were generated and evaluated with the same current workflow.

| Evidence group | Publisher PDF | Clarified text |
|---|---:|---:|
| Technical gate | 4/4 | 4/4 |
| Runtime robustness | 1.000 | 1.000 |
| Interface | 1.000 | 1.000 |
| Clear-rule scenarios | 11/12 (0.917) | 12/12 (1.000) |
| Approved-decision scenarios | 7/10 (0.700) | 10/10 (1.000) |
| Scenario coverage | 22/22 | 22/22 |
| Neutral Judge mean (n=3) | 0.467 | 0.953 |
| Material assumptions declared | 3 | 2 |
| Python lines | 187 | 320 |

Settings for both conditions:

- implementation: `gpt-5.6-sol:low`;
- three neutral judges: `gpt-5.6-sol:medium`;
- three additional personas: rule fidelity, ambiguity/specification, and executable systems; not included in the neutral mean.

## PDF deviations

- **Clear printed rule:** a five-card combination is unavailable when the discard was initially empty, so a just-played component cannot be retrieved.
- **Approved decisions:** Defuse incorrectly removes all remaining Attack obligations; a Triple does not announce the requested title before reactions; a restored action against a now-empty target does not resolve as the approved no-op.

The clarified implementation passed all 22 deterministic scenarios.

## Separate persona evidence

- For the PDF implementation, rule-fidelity and executable-systems personas additionally flagged elimination discard handling, special-card combinations, hidden Triple requests, stale preview knowledge, and restored empty-target actions. These are review findings and regression candidates, not silently added to the deterministic score.
- For the clarified implementation, the rule-fidelity and executable-systems personas found no supported critical or major defect. The ambiguity persona retained three source questions: single Cat-card play, Triple against an empty hand, and how long unchanged preview information remains displayed.

This is a diagnostic `n=1` comparison, not a variance estimate or proof that every game state is correct.

## Files

- Compact PDF profile: `pdf/result.md`
- Compact clarified profile: `clarified/result.md`
- Machine-readable profiles and raw artifacts: `pdf/` and `clarified/`
- Presentation plot: `../../plots/exploding_kittens/pdf_vs_clarified/evidence_profile.png`
