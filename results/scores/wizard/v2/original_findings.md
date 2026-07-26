# Wizard V2 original-condition evaluation

## Status

This is the successful adapted successor `v2_original_2`. The predecessor `v2_original_1` exhausted its three pre-evaluation attempts at the assumptions-schema gate and remains archived as `original_failed_1`; it was not evaluated or scored. The adaptation only aligned the model-facing assumptions schema with the pre-existing validator.

## Separate evidence groups

- Agentic gate: PASS, 0 repairs in this successor.
- Technical gate (01–04): 4/4.
- Runtime robustness (05): 100/100 deterministic-seed rollouts.
- Interface (06): 226118/226118 actions accepted by the language check.
- Player counts: supported 3, 4, 5, 6 passed; 2 and 7 rejected.
- Clear-basis scenarios: 22/23 (95.65%).
- Human-decision-basis scenarios: 9/11 (81.82%).
- Scenario evaluated coverage: 34/34 (100%).
- Clear claim-to-scenario mapping: 50/50; evaluated-claim coverage: 50/50. Mapping is not assertion completeness.
- Neutral judges: 0.78, 0.72, 0.72; mean 0.74, sample SD 0.0346 (`n=3`, all high confidence).

No mixed clear-plus-human correctness score is reported.

## Confirmed scenario defects

1. **Clear printed rule — `WIZ-C-WIZARD-LEAD-FREE` (`WIZ-R28`)**: after a Wizard opens a trick, a later ordinary card incorrectly sets `led_suit`; subsequent cards are therefore not all legal. Expected `led_suit=None`, actual ordinary suit. This is one clear-rule implementation defect.
2. **Human decision — `WIZ-G-JESTER-WIZARD` (`WIZ-R14`)**: Jester → Wizard → ordinary card has the same root defect. The first Wizard still wins, but the trick does not remain colorless/unrestricted.
3. **Human decision — `WIZ-G-FIRST-DEALER-RESET` (`WIZ-R04`)**: the implementation chooses the initial dealer pseudo-randomly; the approved deterministic evaluator decision expects player 0. Fresh-deck reset and later clockwise dealer rotation pass.

## Judge evidence and adjudication

All three neutral judges independently confirmed the Wizard-led defect and initial-dealer deviation. Two judges additionally reported that completed played-card identities disappear from observations even though `WIZ-DEC-PRIVACY` says played cards are public. The frozen scenario suite does not deterministically assert persistent completed-trick history, so this remains a **new regression candidate**, not a retroactively scored failure. The judges also treated dealing direction/order as unresolved rather than a printed-rule contradiction.

## Frozen evaluator identity

- Suite SHA-256: `9b3963cf9e220f707ed43fdda2719950794639be4c3c0f177eb8beaff79f01c5`
- Adapter SHA-256: `8fea7418ea86340b5d5bbec7baeb8a8f7e34fa688e615b655f9e8ab0fe52473a`
- V4 runner SHA-256: `002f9c000cba5993633c4af2fab10ced464603b0f16c6d16a251ae76f67f2aac`
- Implementation SHA-256: `5d4871a25452f59af2f9fe5e28206cb3ca156e2ab61dbe922a676dd74edc9063`
- Rulebook SHA-256: `167254a64b0866266746833c0b98836db51c08171b5b96e25f7461d5bf3dee79`

Generation used `gpt-5.6-sol:low`; the three native neutral judges used `gpt-5.6-sol:medium`. Actual OAuth subscription cost is unavailable; the result card keeps the dated API-equivalent estimate separate.
