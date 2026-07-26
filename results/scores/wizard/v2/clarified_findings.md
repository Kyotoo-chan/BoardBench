# Wizard V2 clarified-condition evaluation

## Separate evidence groups

- Agentic gate: PASS, 0 repairs in the scored successor.
- Technical gate (01–04): 4/4.
- Runtime robustness (05): 100/100 deterministic-seed rollouts.
- Interface (06): 226148/226148 actions accepted.
- Player counts: supported 3, 4, 5, 6 passed; 2 and 7 rejected.
- Clear-basis scenarios: 23/23 (100%).
- Human-decision-basis scenarios: 10/11 (90.91%).
- Scenario evaluated coverage: 34/34 (100%).
- Clear claim-to-scenario mapping and evaluated-claim coverage: 50/50.
- Neutral judges: 0.91, 0.88, 0.90; mean 0.8967, sample SD 0.0153 (`n=3`).

No mixed clear-plus-human correctness score is reported.

## Confirmed scenario defect

`WIZ-R14` remains a human-decision-basis failure: after Jester → Wizard → ordinary card, the ordinary card incorrectly establishes `led_suit`. The first Wizard wins, but the approved decision requires the trick to remain colorless and all later cards to remain legal.

The original condition's clear Wizard-led defect (`WIZ-R28`) and randomized-first-dealer deviation (`WIZ-R04`) are fixed in this condition.

## Judge evidence

All three judges independently confirmed the remaining Jester → Wizard defect. One judge repeated the completed-played-card observation concern. Because the frozen scenario suite does not assert persistent completed-trick history, it remains an unscored regression candidate rather than a retroactive scenario failure.

Generation used `gpt-5.6-sol:low`; all three neutral judges used `gpt-5.6-sol:medium`. Failed pre-evaluation attempts were not evaluated or scored.
