# Wizard V2 scenario matrix

- Source-clear material claims: 50
- Scenarios: 34
- Claim-to-scenario mapping coverage: 50/50
- User approval: 2026-07-26
- Diagnostic replay of frozen v1: 32 PASS, 2 FAIL (`WIZ-R14`, `WIZ-R28`)

| Scenario | Basis | Atomic claims |
|---|---|---|
| `WIZ-R01-cited-card-totals` | `clear` | `WIZ-C-INV-TOTAL` — The playing-card inventory contains 60 character cards.<br>`WIZ-C-INV-SUITS` — Ordinary cards use exactly the four named suits.<br>`WIZ-C-INV-WIZARDS` — The deck contains four Wizard cards.<br>`WIZ-C-INV-JESTERS` — The deck contains four Jester cards. |
| `WIZ-R02-exact-suit-rank-inventory` | `human_decision` | `WIZ-G-EXACT-INVENTORY` — The text does not enumerate one card of every rank 1-13 in every suit. |
| `WIZ-R03-round-count-by-player-count` | `clear` | `WIZ-C-PLAYERS-SUPPORTED` — Three, four, five, and six players are supported.<br>`WIZ-C-END-3P` — Three players finish after round 20.<br>`WIZ-C-END-4P` — Four players finish after round 15.<br>`WIZ-C-END-5P` — Five players finish after round 12.<br>`WIZ-C-END-6P` — Six players finish after round 10. |
| `WIZ-R04-first-round-deal-and-start` | `human_decision` | `WIZ-G-FIRST-DEALER-RESET` — The first deterministic dealer identity and exact collect/reshuffle reset are unspecified. |
| `WIZ-R05-revealed-wizard-requires-color` | `human_decision` | `WIZ-G-WIZARD-CHOICE-MANDATORY` — The source does not say whether the dealer may decline to choose trump after revealing a Wizard. |
| `WIZ-R06-prediction-domain` | `human_decision` | `WIZ-G-BID-DOMAIN` — The executable integer prediction domain is not stated. |
| `WIZ-R07-base-bids-may-equal-trick-count` | `human_decision` | `WIZ-G-BID-SUM` — The base rules do not explicitly state whether total predictions may equal available tricks; the prohibition appears only in an excluded variant. |
| `WIZ-R08-follow-suit-with-special-exceptions` | `clear` | `WIZ-C-FOLLOW-SUIT` — A player holding the led ordinary suit must follow it.<br>`WIZ-C-WIZARD-ALWAYS-LEGAL` — A Wizard is legal even while holding the led suit.<br>`WIZ-C-JESTER-ALWAYS-LEGAL` — A Jester is legal even while holding the led suit. |
| `WIZ-R09-void-player-may-discard-or-trump` | `clear` | `WIZ-C-VOID-DISCARD` — A player void in the led suit may discard another ordinary suit.<br>`WIZ-C-VOID-TRUMP` — A player void in the led suit may play trump. |
| `WIZ-R10-first-wizard-wins-midgame` | `clear` | `WIZ-C-WIZARD-PRIORITY` — A Wizard has the highest trick priority.<br>`WIZ-C-WIN-FIRST-WIZARD` — The first Wizard played wins the trick.<br>`WIZ-C-TRICK-CREDIT` — The trick winner receives exactly one won trick.<br>`WIZ-C-NEXT-LEADER` — The prior trick winner leads the next trick. |
| `WIZ-R11-first-wizard-also-wins-final-round` | `clear` | `WIZ-C-WIN-FIRST-WIZARD` — The first Wizard played wins the trick. |
| `WIZ-R12-jester-then-ordinary-establishes-suit` | `clear` | `WIZ-C-JESTER-ORDINARY-LEADS` — When the second card after a leading Jester is ordinary, its suit becomes the led suit. |
| `WIZ-R13-leading-jesters-wait-for-first-color` | `human_decision` | `WIZ-G-JESTER-CHAIN` — Multiple leading Jesters are not fully resolved. |
| `WIZ-R14-jester-wizard-keeps-trick-colorless` | `human_decision` | `WIZ-G-JESTER-WIZARD` — A Wizard before the first ordinary card does not have an explicit led-suit rule. |
| `WIZ-R15-all-jesters-first-wins` | `clear` | `WIZ-C-ALL-JESTERS-FIRST` — If all cards are Jesters, the first Jester wins.<br>`WIZ-C-TRICK-CREDIT` — The trick winner receives exactly one won trick. |
| `WIZ-R16-highest-trump-wins-without-wizard` | `clear` | `WIZ-C-WIN-HIGHEST-TRUMP` — Without a Wizard, the highest trump wins.<br>`WIZ-C-JESTER-NOT-TRUMP` — A Jester has no trump priority. |
| `WIZ-R17-highest-led-color-wins-without-trump` | `clear` | `WIZ-C-WIN-HIGHEST-LED` — Without Wizard or trump, the highest card of the led suit wins. |
| `WIZ-R18-final-round-scoring-and-winner` | `clear` | `WIZ-C-SCORE-EXACT-BONUS` — An exact prediction earns a 20-point bonus.<br>`WIZ-C-SCORE-EXACT-TRICKS` — An exact prediction additionally earns 10 points per won trick.<br>`WIZ-C-SCORE-OVER` — Taking more tricks than predicted loses 10 points per difference.<br>`WIZ-C-SCORE-UNDER` — Taking fewer tricks than predicted loses 10 points per difference.<br>`WIZ-C-END-SCORE-FIRST` — The final round is scored before termination.<br>`WIZ-C-END-HIGHEST-WINS` — The player with the highest cumulative score wins. |
| `WIZ-R19-joint-winners-on-equal-high-score` | `human_decision` | `WIZ-G-TIE` — Equal highest final scores are not resolved. |
| `WIZ-R20-private-hands-in-base-game` | `human_decision` | `WIZ-G-PRIVACY` — The machine-readable boundary for private hands and public information is not explicit. |
| `WIZ-R21-round-reset-deal-and-dealer-rotation` | `human_decision` | `WIZ-G-FIRST-DEALER-RESET` — The first deterministic dealer identity and exact collect/reshuffle reset are unspecified. |
| `WIZ-R22-player-count-setup-boundaries` | `clear` | `WIZ-C-PLAYERS-SUPPORTED` — Three, four, five, and six players are supported.<br>`WIZ-C-PLAYERS-REJECT` — Counts outside three through six are outside the supported game.<br>`WIZ-C-DEAL-ROUND` — Round number equals cards dealt to each player.<br>`WIZ-C-DEAL-REMAINDER` — Undealt cards form the face-down center stack.<br>`WIZ-C-END-3P` — Three players finish after round 20.<br>`WIZ-C-END-4P` — Four players finish after round 15.<br>`WIZ-C-END-5P` — Five players finish after round 12.<br>`WIZ-C-END-6P` — Six players finish after round 10. |
| `WIZ-R23-complete-game-final-round-by-count` | `clear` | `WIZ-C-FINAL-NO-TRUMP` — The final round has no center stack, revealed card, or trump.<br>`WIZ-C-END-3P` — Three players finish after round 20.<br>`WIZ-C-END-4P` — Four players finish after round 15.<br>`WIZ-C-END-5P` — Five players finish after round 12.<br>`WIZ-C-END-6P` — Six players finish after round 10.<br>`WIZ-C-END-ALL-DEALT` — All 60 cards are dealt in the final round.<br>`WIZ-C-END-SCORE-FIRST` — The final round is scored before termination. |
| `WIZ-R24-revealed-card-trump-rules` | `clear` | `WIZ-C-TRUMP-REVEAL` — After a non-final deal, exactly one remaining-stack card is face-up as the revealed trump card.<br>`WIZ-C-TRUMP-ORDINARY` — An ordinary revealed card sets its suit as trump.<br>`WIZ-C-TRUMP-JESTER` — A revealed Jester creates a no-trump round.<br>`WIZ-C-TRUMP-WIZARD-DEALER` — When a Wizard is revealed, the dealer is the player allowed to choose trump.<br>`WIZ-C-TRUMP-AFTER-HAND` — The dealer receives/views their hand before choosing trump. |
| `WIZ-R25-complete-bid-order-and-first-leader` | `clear` | `WIZ-C-BID-REQUIRED` — Every player must make one prediction for the round.<br>`WIZ-C-BID-SEQUENTIAL` — Predictions are made sequentially.<br>`WIZ-C-BID-FIRST` — The dealer's left neighbor predicts first.<br>`WIZ-C-BID-RECORDED` — Predictions remain recorded for scoring.<br>`WIZ-C-FIRST-LEADER` — The dealer's left neighbor leads the first trick. |
| `WIZ-R26-clockwise-play-and-next-leader` | `clear` | `WIZ-C-TURN-CLOCKWISE` — Cards are played clockwise.<br>`WIZ-C-TRICK-CREDIT` — The trick winner receives exactly one won trick.<br>`WIZ-C-NEXT-LEADER` — The prior trick winner leads the next trick. |
| `WIZ-R27-rank-endpoints-and-jester-no-priority` | `clear` | `WIZ-C-RANK-HIGH` — Rank 13 is strongest within an ordinary suit.<br>`WIZ-C-RANK-LOW` — Rank 1 is weakest within an ordinary suit.<br>`WIZ-C-JESTER-NOT-TRUMP` — A Jester has no trump priority.<br>`WIZ-C-WIN-HIGHEST-LED` — Without Wizard or trump, the highest card of the led suit wins. |
| `WIZ-R28-wizard-lead-keeps-all-cards-legal` | `clear` | `WIZ-C-WIZARD-LEAD-FREE` — After a Wizard lead, every following card remains legal and no led-suit obligation arises. |
| `WIZ-R29-jester-second-card-free-then-follow-suit` | `clear` | `WIZ-C-JESTER-SECOND-FREE` — After one leading Jester, every card is legal as the second card.<br>`WIZ-C-JESTER-ORDINARY-LEADS` — When the second card after a leading Jester is ordinary, its suit becomes the led suit.<br>`WIZ-C-FOLLOW-SUIT` — A player holding the led ordinary suit must follow it. |
| `WIZ-R30-jester-does-not-remove-existing-suit` | `clear` | `WIZ-C-FOLLOW-SUIT` — A player holding the led ordinary suit must follow it.<br>`WIZ-C-JESTER-ALWAYS-LEGAL` — A Jester is legal even while holding the led suit. |
| `WIZ-R31-midtrick-wizard-wins-without-erasing-suit` | `clear` | `WIZ-C-FOLLOW-SUIT` — A player holding the led ordinary suit must follow it.<br>`WIZ-C-WIN-FIRST-WIZARD` — The first Wizard played wins the trick. |
| `WIZ-R32-cumulative-scoring-boundaries` | `clear` | `WIZ-C-SCORE-EXACT-BONUS` — An exact prediction earns a 20-point bonus.<br>`WIZ-C-SCORE-EXACT-TRICKS` — An exact prediction additionally earns 10 points per won trick.<br>`WIZ-C-SCORE-OVER` — Taking more tricks than predicted loses 10 points per difference.<br>`WIZ-C-SCORE-UNDER` — Taking fewer tricks than predicted loses 10 points per difference. |
| `WIZ-R33-expanded-private-observations` | `human_decision` | `WIZ-G-PRIVACY` — The machine-readable boundary for private hands and public information is not explicit. |
| `WIZ-R34-clear-dealer-rotation-and-next-deal` | `clear` | `WIZ-C-DEALER-ROTATES` — Dealer responsibility rotates one player clockwise after each round.<br>`WIZ-C-DEAL-ROUND` — Round number equals cards dealt to each player. |

## Approval

- Seven source-gap resolutions may be reused only as separately attributed clarification claims; base-game scope lives in the run config.
- No clarification may weaken `WIZ-C-WIZARD-LEAD-FREE`: after a Wizard opens a trick, every later card remains legal and no led suit may arise.
- `WIZ-G-JESTER-WIZARD` extends the approved colorless handling to Jester→Wizard; it does not override the clear Wizard-led rule.
