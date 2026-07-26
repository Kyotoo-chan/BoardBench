# Abalone V2 claim/scenario matrix

- Source-clear claims: 36
- Material deterministic clear claims requiring hard mapping: 33
- Source-gap or ambiguous claims: 10
- Configured scenarios: 38
- Approved decisions: 2026-07-26
- Complete matrix approved by user: 2026-07-26
- Scope: two-player untimed base game; optional clock excluded

| Claim | Class | Material/testable | Scenario mapping |
|---|---|---|---|
| `ABAL-C-PLAYERS` | clear | true/true | `ABAL-R24-player-count-and-bounded-playability` |
| `ABAL-C-SETUP-FIGURE` | clear | true/true | `ABAL-R01-exact-initial-setup` |
| `ABAL-C-BOARD-61` | clear | true/true | `ABAL-R01-exact-initial-setup` |
| `ABAL-C-SETUP-COUNTS` | clear | true/true | `ABAL-R01-exact-initial-setup` |
| `ABAL-C-SETUP-ROWS` | clear | true/true | `ABAL-R01-exact-initial-setup` |
| `ABAL-C-COLOR-LOTTERY` | clear | false/false | exception: A deterministic environment cannot reproduce a social lottery; player-to-color mapping is an interface convention. |
| `ABAL-C-TURN-ORDER` | clear | true/true | `ABAL-R02-single-marble-one-step-and-turn` |
| `ABAL-C-ONE-MOVE` | clear | true/true | `ABAL-R02-single-marble-one-step-and-turn` |
| `ABAL-C-ONE-STEP` | clear | true/true | `ABAL-R02-single-marble-one-step-and-turn`, `ABAL-R25-single-step-e`, `ABAL-R26-single-step-ne`, `ABAL-R27-single-step-nw`, `ABAL-R28-single-step-w`, `ABAL-R29-single-step-sw`, `ABAL-R30-single-step-se` |
| `ABAL-C-SIX-DIRECTIONS` | clear | true/true | `ABAL-R02-single-marble-one-step-and-turn`, `ABAL-R25-single-step-e`, `ABAL-R26-single-step-ne`, `ABAL-R27-single-step-nw`, `ABAL-R28-single-step-w`, `ABAL-R29-single-step-sw`, `ABAL-R30-single-step-se` |
| `ABAL-C-GROUP-SIZE` | clear | true/true | `ABAL-R03-two-marble-inline`, `ABAL-R04-three-marble-broadside`, `ABAL-R05-four-marble-move-illegal`, `ABAL-R20-three-marble-inline`, `ABAL-R31-invalid-group-and-destination-boundaries` |
| `ABAL-C-SAME-DIRECTION` | clear | true/true | `ABAL-R03-two-marble-inline`, `ABAL-R04-three-marble-broadside` |
| `ABAL-C-STRAIGHT-CONTIGUOUS` | clear | true/true | `ABAL-R03-two-marble-inline`, `ABAL-R04-three-marble-broadside`, `ABAL-R20-three-marble-inline`, `ABAL-R21-two-broadside-from-longer-row`, `ABAL-R31-invalid-group-and-destination-boundaries` |
| `ABAL-C-INLINE` | clear | true/true | `ABAL-R03-two-marble-inline`, `ABAL-R20-three-marble-inline` |
| `ABAL-C-BROADSIDE` | clear | true/true | `ABAL-R04-three-marble-broadside`, `ABAL-R09-broadside-push-illegal`, `ABAL-R21-two-broadside-from-longer-row`, `ABAL-R33-patt-broadside-withdrawal` |
| `ABAL-C-EMPTY-DESTINATION` | clear | true/true | `ABAL-R04-three-marble-broadside`, `ABAL-R09-broadside-push-illegal`, `ABAL-R31-invalid-group-and-destination-boundaries` |
| `ABAL-C-MAX-THREE` | clear | true/true | `ABAL-R05-four-marble-move-illegal`, `ABAL-R11-four-v-three-still-patt` |
| `ABAL-C-SUBSET-LONG-ROW` | clear | true/true | `ABAL-R21-two-broadside-from-longer-row` |
| `ABAL-C-MOVE-FINAL` | clear | true/false | exception: The public contract has no undo or revision operation; turn advancement is tested under ABAL-C-TURN-ORDER. |
| `ABAL-C-SUMITO-SUPERIOR` | clear | true/true | `ABAL-R06-two-v-one-sumito`, `ABAL-R07-three-v-one-sumito`, `ABAL-R08-three-v-two-sumito`, `ABAL-R15-edge-ejection` |
| `ABAL-C-SUMITO-PATTERNS` | clear | true/true | `ABAL-R06-two-v-one-sumito`, `ABAL-R07-three-v-one-sumito`, `ABAL-R08-three-v-two-sumito`, `ABAL-R35-three-v-two-edge-ejects-one` |
| `ABAL-C-SUMITO-INLINE` | clear | true/true | `ABAL-R06-two-v-one-sumito`, `ABAL-R09-broadside-push-illegal`, `ABAL-R14-non-collinear-push-illegal`, `ABAL-R31-invalid-group-and-destination-boundaries` |
| `ABAL-C-SUMITO-ADJACENT` | clear | true/true | `ABAL-R06-two-v-one-sumito`, `ABAL-R13-gap-does-not-push` |
| `ABAL-C-SUMITO-FREE-BEHIND` | clear | true/true | `ABAL-R06-two-v-one-sumito`, `ABAL-R12-blocked-sumito-illegal` |
| `ABAL-C-SUMITO-BLOCKED` | clear | true/true | `ABAL-R12-blocked-sumito-illegal` |
| `ABAL-C-SUMITO-GAP` | clear | true/true | `ABAL-R13-gap-does-not-push` |
| `ABAL-C-SUMITO-COLLINEAR` | clear | true/true | `ABAL-R14-non-collinear-push-illegal` |
| `ABAL-C-SUMITO-OPTIONAL` | clear | true/true | `ABAL-R17-sumito-is-optional` |
| `ABAL-C-PATT-EQUAL` | clear | true/true | `ABAL-R10-equal-strength-pushes-illegal`, `ABAL-R18-patt-may-withdraw`, `ABAL-R22-one-v-one-patt`, `ABAL-R23-two-v-two-patt`, `ABAL-R34-crossing-angle-breaks-patt` |
| `ABAL-C-PATT-FOUR-THREE` | clear | true/true | `ABAL-R11-four-v-three-still-patt` |
| `ABAL-C-PATT-WITHDRAW` | clear | true/true | `ABAL-R18-patt-may-withdraw`, `ABAL-R33-patt-broadside-withdrawal` |
| `ABAL-C-PATT-CROSSING` | clear | true/true | `ABAL-R34-crossing-angle-breaks-patt` |
| `ABAL-C-EJECTION` | clear | true/true | `ABAL-R15-edge-ejection`, `ABAL-R16-sixth-ejection-wins`, `ABAL-R35-three-v-two-edge-ejects-one` |
| `ABAL-C-EDGE-EXCEPTION` | clear | true/true | `ABAL-R15-edge-ejection`, `ABAL-R35-three-v-two-edge-ejects-one` |
| `ABAL-C-SIXTH-WINS` | clear | true/true | `ABAL-R16-sixth-ejection-wins` |
| `ABAL-C-CLOCK-OPTIONAL` | clear | false/false | exception: Clock operation and timeout outcomes are unspecified and excluded from the base environment. |
| `ABAL-G-BROADSIDE-DESTINATIONS` | ambiguous | true/true | `ABAL-R32-broadside-blocked-and-offboard` |
| `ABAL-G-PASS` | missing | true/true | `ABAL-R19-forced-pass-only-with-no-move` |
| `ABAL-G-DRAW` | missing | true/false | exception: unscored |
| `ABAL-G-CLOCK` | missing | false/false | exception: unscored |
| `ABAL-G-BOX-INVENTORY` | missing | false/false | exception: unscored |
| `ABAL-G-TERMINAL-API` | missing | true/true | `ABAL-R36-terminal-api-and-returns` |
| `ABAL-G-RETURNS` | missing | true/true | `ABAL-R36-terminal-api-and-returns` |
| `ABAL-G-ACTION-UNIQUE` | missing | true/true | `ABAL-R37-action-serialization-is-unique` |
| `ABAL-G-PUBLIC-STATE` | missing | true/true | `ABAL-R38-public-contract-observability` |
| `ABAL-G-PLAYER-MAPPING` | missing | true/true | `ABAL-R38-public-contract-observability` |

## Approval guardrails

- Clear rules remain clear even when an implementation fails them.
- Forced pass, broadside destination quantification, terminal API/returns, action uniqueness, public state, and player-ID mapping remain separately attributed human decisions.
- Draw/repetition, box inventory, and clock-expiration behavior remain unscored.
- V4 adapters use only the canonical public contract and keep expected outcomes in scenario JSON.
- Historical 100% coverage means configured V3 scenario coverage only.
