# Wizard Version 1.0 — v2 atomic rule and gap register

- **status:** approved by user (2026-07-26)
- **condition:** publisher PDF only; base game only
- **source:** `WIZARD-RULES`, `inputs/games/wizard/game_rules.pdf`
- **SHA-256:** `167254a64b0866266746833c0b98836db51c08171b5b96e25f7461d5bf3dee79`
- **atomic inventory:** `inputs/games/wizard/claims_v2.json`
- **scenario suite:** `checks/scenarios/wizard_v2.json`
- **scope:** the separately headed page-2 variants remain visible but excluded

## V2 classification

The v2 inventory separates 50 deterministic material clear claims, nine material source gaps, and three non-material untestable physical/advisory claims. Every material clear claim maps to at least one non-empty hard scenario. Mapping coverage is not presented as assertion completeness.

The prior Wizard-led defect is a clear-rule implementation failure, not a source gap:

> “Wird ein Stich mit einer Zaubererkarte eröffnet, dann dürfen die folgenden Lehrlinge beliebige Karten abwerfen ...” (p. 2)

`WIZ-R28-wizard-lead-keeps-all-cards-legal` now checks the complete legal-card set after a Wizard lead. The older `WIZ-R14` remains a human-decision-basis manifestation of the same root defect under the Jester→Wizard gap resolution.

## Material source gaps and proposed clarification decisions

These seven gap resolutions were approved for v1 on 2026-07-25 and explicitly re-approved for v2 on 2026-07-26, provided that none weakens the clear Wizard-led unrestricted-play rule. They remain user decisions and are not attributed to the publisher. Base-game-only scope is recorded separately in the run config, not presented as a source-gap clarification:

1. **`WIZ-G-EXACT-INVENTORY` / `WIZ-DEC-INV`:** model one rank 1–13 in each of four suits, four Wizards, and four Jesters; “Magier” and “Zauberer” denote one type.
2. **`WIZ-G-FIRST-DEALER-RESET` / `WIZ-DEC-FLOW`:** player 0 is the first dealer/scorekeeper; collect and reshuffle all 60 cards between rounds; rotate dealer clockwise.
3. **`WIZ-G-WIZARD-CHOICE-MANDATORY` / `WIZ-DEC-TRUMP`:** a revealed Wizard requires the dealer to choose exactly one of the four suits after seeing the hand; declining is not legal.
4. **`WIZ-G-BID-DOMAIN` / `WIZ-DEC-BID`:** predictions are integers from zero through current hand size, clockwise from dealer-left.
5. **`WIZ-G-BID-SUM` / `WIZ-DEC-BID`:** the base game imposes no restriction on the sum of predictions.
6. **`WIZ-G-JESTER-CHAIN` and `WIZ-G-JESTER-WIZARD` / `WIZ-DEC-JESTER`:** leading Jesters remain colorless until the first ordinary card; a Wizard before that card keeps the trick colorless, allows all later cards, and the first Wizard wins.
7. **`WIZ-G-TIE` / `WIZ-DEC-TIE`:** equal highest final scores produce joint winners.
8. **`WIZ-G-PRIVACY` / `WIZ-DEC-PRIVACY`:** each player observes their own cards and opponents’ hand sizes; predictions, revealed trump, and played cards are public.

No new material decision was found. Invalid physical inputs beyond the required player-count boundary are interface policy, not publisher rules.

## Expanded hard evidence

The 34-case v2 suite adds:

- construction, setup, bounded play, and final-round completion for 3, 4, 5, and 6 players plus rejection of 2 and 7;
- ordinary, Jester, and Wizard reveal branches;
- complete prediction order and first leader;
- clockwise card order and next-trick leadership;
- rank endpoints and Jester priority;
- direct Wizard-led unrestricted legality;
- Jester→ordinary follow-suit enforcement;
- ordinary→Jester and ordinary→Wizard obligation persistence;
- cumulative scoring boundaries;
- expanded private observations;
- clear dealer rotation separate from the executable reshuffle decision.

A diagnostic replay against the frozen v1 implementation evaluates all 34 scenarios and fails exactly `WIZ-R14` and `WIZ-R28`, both exposing the known colorless-trick root defect. This replay is not a replacement score.
