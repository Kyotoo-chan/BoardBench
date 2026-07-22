# Bohnanza Base 2023 — original versus clarified

## Design

One fresh generation received the byte-identical publisher PDF plus the four user-approved items in `clarifications.json`. The original generation received only the PDF. Model, thinking, prompt, Contract-v2 profile, gates, technical checks, scenario runner, and one-Judge setting were held constant. The 37-scenario comparison rubric was frozen before the clarified generation and replayed identically on both implementations.

## Evidence groups

| Evidence | Original PDF only | PDF + clarification |
|---|---:|---:|
| Technical checks 01–04 | 4/4 | 4/4 |
| Random rollouts | 100/100 | 100/100 |
| Action-language check | pass | pass |
| Comparison scenarios | 31 PASS / 6 FAIL | 37 PASS / 0 FAIL |
| Scenario coverage | 37/37 | 37/37 |
| Generation repairs | 0 | 0 |
| Neutral Judge (n=1) | 0.52 | 0.40 |

Do not combine these groups into one score.

## Effect on the four clarified gaps

All six deterministic expectations derived from the four clarification areas changed from failure to pass:

1. Garden-bean payout: fail → pass.
2. Third depletion on exactly the third phase-four draw: fail → pass.
3. Third depletion on exactly the second phase-two reveal: fail → pass.
4. Phase three advances to a non-active recipient and exposes their card-order choices: fail → pass.
5. One-for-two trade: fail → pass.
6. Three-for-one trade: fail → pass.

For these preregistered targets, the clarification intervention had the intended effect.

## Runtime cost of the trade clarification

The clarified implementation represents arbitrary finite trade bundles by eagerly enumerating card subsets. This passed the fixed robustness checks but substantially increased work:

| Runtime evidence | Original | Clarified |
|---|---:|---:|
| 100 rollouts | 37.43 s | 94.07 s |
| Action roundtrips checked | 666,338 | 2,045,295 |
| Action-language check | 34.73 s | 89.74 s |

The clarified source removed the illegal quantity cap, but the fixed atomic `trade_propose` profile encouraged an exponential implementation. This is a source/contract interaction, not evidence that arbitrary trades are wrong.

## Independent Judge evidence

### Original Judge: 0.52, high confidence

Found delayed third depletion, incomplete all-player phase three, capped trade bundles, and the Garden payout error.

### Clarified Judge: 0.40, high confidence

Confirmed that the clarified implementation now covers depletion timing, all-player phase three, trade quantities, and payouts, but identified:

- mandatory final harvesting is omitted from terminal scoring;
- exhaustive trade enumeration may become impractical as hands grow;
- `apply_action` accepts syntactically valid actions without checking current-phase legality.

The lower clarified Judge score does **not** show that clarification made the implementation less faithful. Each condition has only one Judge, and the clarified Judge found important issues that the original Judge did not inspect. In particular, both implementations' `returns` methods score only existing coins and omit mandatory final field harvests; this shared defect was missed by the original Judge and by the frozen comparison rubric.

The `apply_action` finding is partly a contract question: the packet requires legal action generation but does not explicitly state whether every externally constructed action outside `legal_actions` must be rejected. It should be reported separately from confirmed publisher-rule contradictions.

## Interpretation

The experiment provides positive evidence for the clarification intervention on the targeted gaps: the expanded deterministic rubric improved from 31/37 to 37/37 with no testability failures. It does not establish complete correctness. Clarification shifted the dominant problems:

- **Reduced:** temporal-boundary errors, multi-player phase-three control errors, graphical payout transcription errors, and illegal trade caps.
- **Remaining/shared:** final-harvest scoring was missed by both generations and by the pre-generation scenario set.
- **Introduced/exposed:** arbitrary atomic trade enumeration created a severe scalability risk.
- **Evaluator limitation:** one Judge per condition and incomplete deterministic coverage make Judge scores and 37/37 scenario success insufficient as global fidelity measures.

The defensible conclusion is: explicit clarification improved the mechanics it targeted, while overall implementation quality remained constrained by uncovered rules and the chosen action contract.
