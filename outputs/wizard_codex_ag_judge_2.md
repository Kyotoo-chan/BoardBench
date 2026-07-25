score: 0.86
confidence: high

The module implements most approved base-game rules correctly, including deck construction, dealing, trump selection, bidding, scoring, privacy, dealer rotation, and termination. One material legal-play error can alter later tricks, scores, and the final winner.

## Findings

### Major — A Wizard-led trick can incorrectly acquire a led suit

- Canonical fact ID: `WIZ-WIN-02`
- Evidence type: `rule_quote`
- Source ID: `WIZARD-RULES`
- Stable locator: PDF page 2, “Spezielle Rechte der Zauberer und Narren”
- Exact evidence: “Wird ein Stich mit einer Zaubererkarte eröffnet, dann dürfen die folgenden Lehrlinge beliebige Karten abwerfen, einschließlich weiterer Zauberer- und Narrenkarten. Der Stich geht in jedem Fall an den ersten Zauberer.”
- Conflicting symbols:
  - `Game.apply_action`
  - `Game.legal_actions`
  - Transition: `if d["led_suit"] is None and action.arg not in SPECIALS: d["led_suit"] = _suit(action.arg)`
- Expected: Once a Wizard leads, the trick remains colorless and every remaining player may play any card.
- Implemented: The first later ordinary card sets `led_suit`. Subsequent players holding that suit are then restricted to the suit or a special card.
- Impact: Players may be denied legal discards. Their retained cards can change later trick winners, scoring, and the overall winner. The code still correctly awards the current trick to the first Wizard.

The same transition also conflicts with approved decision `WIZ-DEC-JESTER` when one or more leading Jesters are followed by a Wizard before any ordinary card: that trick must likewise remain colorless.

### Question — Imported-state trust boundary is unspecified

`Game._validate_state` checks shape and basic types but accepts impossible states, including invalid card multiplicities, negative predictions or trick counts, out-of-range participant references, inconsistent phases, and incorrect round limits. `state_from_data` can therefore admit states that produce rule-invalid transitions or scores.

The packet does not establish whether serialized states are trusted internal snapshots or externally supplied input, so this is not scored as a printed-rule contradiction. If the interface is untrusted, stronger invariant validation is materially necessary.

## Rule-area coverage

| Rule area | Result | Notes |
|---|---|---|
| Players and deck | Pass | Supports 3–6 players; correct 60-card composition |
| Initial setup | Pass | Player 0 begins as dealer; hands are private |
| Round dealing | Pass | Round number equals cards per player |
| Collection and shuffle | Pass | All cards are recollected and freshly shuffled |
| Dealer rotation | Pass | Rotates clockwise after every round |
| Trump | Pass | Ordinary, Jester, Wizard, and final-round cases handled |
| Predictions | Pass | Public, clockwise, 0 through hand size |
| Follow-suit legality | Major issue | Incorrect after a Wizard establishes a colorless trick |
| Trick winner | Pass | First Wizard, highest trump, led color, and all-Jester cases |
| Scoring | Pass | Exact and missed predictions score correctly |
| Terminal condition | Pass | Correct final rounds for all supported player counts |
| Returns and ties | Pass | Scores permit highest-score and joint-winner comparison |
| Variant exclusion | Pass | No page-2 variant restrictions or actions included |

## Missing deterministic scenarios

Without inspecting the prohibited scenario suite, these cases should be covered:

1. A Wizard leads, an ordinary card follows, and a later player holding that ordinary suit may still play an off-suit card.
2. One or more Jesters lead, then a Wizard, then an ordinary card; all remaining players must retain unrestricted choice.
3. In both sequences, verify that the first Wizard wins.
4. Verify that unrestricted discards can affect later tricks without corrupting card conservation.
5. Round-trip a valid state through serialization at every phase.
6. If imported states are untrusted, reject impossible inventories, negative counters, invalid participant references, and phase/turn inconsistencies.
7. Complete games for 3, 4, 5, and 6 players, including final-round scoring and tied winners.

## Material question for a human

Is `state_from_data` intended only for trusted snapshots previously produced by `state_to_data`, or must it reject arbitrary rule-invalid external states? The answer determines whether the validation gap should remain an interface question or become a major issue.

score: 0.86
confidence: high
critical_issues: 0
major_issues: 1
minor_issues: 0
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true