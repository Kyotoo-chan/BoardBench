## Review result

**Score: 0.78 — confidence: high.** The base-game engine is largely complete: dealing, trump selection, bidding, trick resolution, scoring, round progression, terminal scoring, and privacy boundaries are substantially correct. Three material deviations remain, two caused by the same colorless-trick transition defect.

### Findings

#### Major 1 — Wizard-led tricks incorrectly acquire a led suit

- **Canonical fact:** `WIZ-C-WIZARD-LEAD-FREE`
- **Evidence type:** `rule_quote`
- **Source:** `WIZARD-RULES-V1.0`
- **Stable locator:** PDF page 2; `canonical_claims.json#/claims/35`
- **Exact evidence:** “Wird ein Stich mit einer Zaubererkarte eröffnet, dann dürfen die folgenden Lehrlinge beliebige Karten abwerfen, einschließlich weiterer Zauberer- und Narrenkarten.”
- **Conflicting code:** `Game.apply_action`, lines 162–163; `Game.legal_actions`, lines 132–136.
- **Expected:** Once a Wizard leads, every subsequent card remains legal for the entire trick; no ordinary suit becomes led.
- **Implemented:** The Wizard initially leaves `led_suit` unset, but the first later ordinary card assigns its suit to `led_suit`. Subsequent players holding that suit are then restricted to it or a special card.
- **Impact:** Materially rejects legal actions in a central special-card case. Trick completion and the first-Wizard winner rule remain correct.

#### Major 2 — Jester → Wizard resolution does not remain colorless

This is adjudication-dependent and separate from the clear printed-rule contradiction above.

- **Canonical fact:** `WIZ-G-JESTER-WIZARD`; approved decision `WIZ-DEC-JESTER`
- **Evidence type:** `human_decision`
- **Gap provenance:** `WIZARD-V2-CLAIMS`, `canonical_claims.json#/claims/56`
- **Underlying rule locator:** PDF page 2
- **Exact underlying evidence:** “Erst die zweite Karte bestimmt die Farbe, die bedient werden muss.”
- **Decision source:** `WIZARD-V2-RULEFACTS`, approved gap-resolution item 6
- **Exact decision evidence:** “a Wizard before that card keeps the trick colorless, allows all later cards, and the first Wizard wins.”
- **Conflicting code:** `Game.apply_action`, lines 162–163; `Game.legal_actions`, lines 132–136.
- **Expected:** Leading Jesters stay colorless; if a Wizard occurs before the first ordinary card, the whole trick stays colorless, all remaining cards are legal, and the first Wizard wins.
- **Implemented:** Jesters remain colorless and the first Wizard wins, but a later ordinary card sets `led_suit`, constraining still-later players.
- **Complete-fact verification:** Jester chains without a Wizard work, and first-Wizard priority works. Only the “colorless/all later cards legal” component fails.

#### Major 3 — First dealer is randomized instead of player 0

- **Canonical fact:** `WIZ-G-FIRST-DEALER-RESET`; approved decision `WIZ-DEC-FLOW`
- **Evidence type:** `human_decision`
- **Gap provenance:** `WIZARD-V2-CLAIMS`, `canonical_claims.json#/claims/51`
- **Underlying rule locator:** PDF page 1
- **Exact underlying evidence:** “Ein Spieler wird zum Vertrauten der Lehrlinge ernannt.” The printed source does not determine that player’s identity.
- **Decision source:** `WIZARD-V2-RULEFACTS`, approved gap-resolution item 2
- **Exact decision evidence:** “player 0 is the first dealer/scorekeeper; collect and reshuffle all 60 cards between rounds; rotate dealer clockwise.”
- **Conflicting code:** `Game.initial_state`, lines 104–108, particularly `dealer = rng.randrange(self.num_players)`.
- **Expected:** Player 0 is always the first dealer.
- **Implemented:** The first dealer is selected pseudo-randomly from the seed.
- **Complete-fact verification:** A fresh 60-card deck is shuffled each round and the dealer subsequently rotates clockwise. Only initial dealer identity fails.

No critical or minor findings were identified.

### Rule-area coverage

| Rule area | Result | Notes |
|---|---|---|
| Scope and players | Pass | Base game only; accepts 3–6 players |
| Card inventory | Pass | 52 ordinary cards, four Wizards, four Jesters |
| Initial setup | Partial | First dealer contradicts `WIZ-DEC-FLOW` |
| Round dealing/reset | Pass | Hand size equals round; fresh 60-card shuffle |
| Trump determination | Pass | Ordinary, Jester, Wizard, and final-round branches |
| Predictions | Pass | Correct domain, order, and unrestricted total |
| Ordinary follow-suit | Pass | Specials remain legal while holding led suit |
| Wizard-led legality | Fail | Later ordinary card wrongly creates led suit |
| Jester special flow | Partial | Jester chains work; Jester → Wizard continuation fails |
| Trick winner/leader | Pass | First Wizard, highest trump/led suit, all-Jester case |
| Scoring | Pass | Exact bonus and over/under penalties accumulate |
| Terminal/winner | Pass | Final round is scored; returned scores identify top and joint-top players |
| Private/public information | Pass | Own hand private; hand sizes, bids, trump, and current played cards public |
| Serialization | Partial | Supports round-trip data, but structural validation does not prove full deck conservation |

### Missing deterministic scenarios

These are recommended scenarios, not claims about the unseen test suite:

1. Wizard leads, an ordinary card follows, and a later player holds both that ordinary suit and another suit; assert every card remains legal.
2. Jester → Wizard → ordinary → later player with multiple suits; assert every remaining card is legal and the first Wizard wins.
3. Across several seeds and every supported player count, assert player 0 is always the initial dealer.
4. Assert dealer rotation and full-deck reshuffling independently after correcting initial dealer selection.
5. Terminal tied-high scores: assert equal maximum returned scores represent joint winners.
6. Serialized-state conservation scenario covering exactly 60 cards across hands, deck, revealed card, active trick, and completed tricks.

### Material questions for a human

None. The approved fact register resolves the material printed-source gaps relevant to these findings.

```text
score: 0.78
confidence: high
critical_issues: 0
major_issues: 3
minor_issues: 0
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true
```