## Assessment

Score: **0.86**
Confidence: **high**

The native game path correctly implements setup, round growth, trump selection, bidding, scoring, dealer rotation, final-round timing, and trick-winner priority. One material defect incorrectly restricts legal plays after a Wizard leads. A secondary validation weakness permits impossible card inventories when importing serialized states.

## Findings

### Major — Wizard-led tricks can incorrectly acquire a led suit

- Canonical fact ID: `WIZ-WIN-02`
- Evidence type: `rule_quote`
- Source ID: `WIZARD-RULES`
- Stable locator: PDF page 2, “Spezielle Rechte der Zauberer und Narren”
- Exact evidence: “Wird ein Stich mit einer Zaubererkarte eröffnet, dann dürfen die folgenden Lehrlinge beliebige Karten abwerfen, einschließlich weiterer Zauberer- und Narrenkarten. Der Stich geht in jedem Fall an den ersten Zauberer.”
- Conflicting code:
  - `Game.apply_action`, `implementation.py:150–151`
  - `Game.legal_actions`, `implementation.py:128–131`
- Expected: Once a Wizard opens the trick, every remaining player may play any card. No ordinary card played later may establish a suit-following obligation.
- Implemented: The lead Wizard leaves `led_suit` as `None`; the first subsequent ordinary card then sets `led_suit`. Later players holding that suit are restricted to it or a special card.
- Impact: Legal actions materially contradict the printed special rule. The first Wizard still wins correctly, but some otherwise legal discards are rejected.

The same transition also conflicts with:

- Canonical fact ID: `WIZ-DEC-JESTER`
- Evidence type: `human_decision`
- Source ID: `WIZARD-RULES`, approved decision layer
- Stable locator: PDF page 2 basis; approved fact `WIZ-DEC-JESTER`
- Exact evidence: “If a Wizard appears before any ordinary colored card, the trick remains colorless, all remaining players may play any card, and the first Wizard wins.”
- Conflict: In a Jester → Wizard → ordinary-card sequence, that ordinary card improperly establishes `led_suit`.

### Minor — Imported states need not preserve the approved 60-card inventory

- Canonical fact ID: `WIZ-DEC-INV`
- Evidence type: `human_decision`
- Source ID: `WIZARD-RULES`, approved decision layer
- Stable locator: PDF page 1 basis; approved fact `WIZ-DEC-INV`
- Exact evidence: “The 60-card deck is modeled as exactly one rank 1–13 in each of the four named colors, plus four Wizards and four Jesters.”
- Conflicting code: `Game._validate_state`, beginning at `implementation.py:233`
- Expected: `state_from_data` should reject states whose cards across hands and zones do not form the exact approved multiset.
- Implemented: Validation checks individual card syntax but not total count or multiplicity. It accepts missing cards, duplicated ordinary cards, or excess specials.
- Impact: Native setup is correct, but restored or exchanged states can violate fundamental inventory invariants and produce unsupported games.

## Rule-area coverage

| Rule area | Status | Review result |
|---|---|---|
| Components/setup | Mostly aligned | Correct player range and native 60-card construction; imported inventory is under-validated |
| Dealing/rounds | Aligned | Round-sized hands, undealt stack, fresh collection/shuffle, clockwise dealer rotation |
| Trump | Aligned | Ordinary reveal, Jester no-trump, mandatory dealer choice after Wizard reveal, no final-round trump |
| Predictions | Aligned | Public clockwise bids from dealer’s left, range `0..hand size`, no sum restriction |
| Legal play | Material defect | Ordinary follow-suit and special-card freedom work except after a Wizard has appeared before any ordinary card |
| Trick winner | Aligned | First Wizard, otherwise highest trump, otherwise highest led suit; first Jester wins an all-Jester trick |
| Chance/privacy | Aligned with interface question | Seeded shuffling and private hands are modeled; current public trick is observable |
| Scoring | Aligned | Exact and missed-bid formulas match |
| Terminal/returns | Aligned | Final round is scored before termination; score vector preserves joint highest-score ties |
| Variants | Aligned | No excluded page-2 variant is implemented |

## Needed deterministic scenarios

These are required coverage targets; the prohibited scenario files were not inspected.

1. Wizard leads, second player plays an ordinary card, and a later player holding that suit may still discard a different ordinary suit.
2. Jester → Wizard → ordinary card, verifying that the trick stays colorless and all remaining cards stay legal.
3. Multiple leading Jesters followed by an ordinary card, verifying that the first ordinary card establishes suit only when no Wizard appeared first.
4. Revealed Wizard requires exactly one dealer trump choice after the dealer can observe their hand.
5. Final rounds for 3, 4, 5, and 6 players: all 60 cards dealt, no revealed trump, round scored before terminal.
6. Serialized-state rejection for missing, duplicated, or excess cards and incorrect special-card multiplicities.
7. Equal highest final scores, verifying that all tied players remain joint winners.
8. First Wizard wins when multiple Wizards occur in the same trick.

## Material questions for a human

- Does the BoardBench observation contract provide action/observation history and therefore perfect recall of completed public tricks? `observation_to_data` exposes only `completed_trick_count`, not the completed cards. The supplied rule condition does not decide whether each observation must independently contain that history.
- Are `returns()` values expected to be raw experience-point totals or normalized win/loss utilities? Raw scores preserve the rulebook outcome and ties, but the packet does not state the framework-level convention.

Neither question requires clarification of the printed base-game rules.

```text
score: 0.86
confidence: high
critical_issues: 0
major_issues: 1
minor_issues: 1
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true
```