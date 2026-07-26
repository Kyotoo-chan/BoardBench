## 1. Score

**score: 0.72 — confidence: high**

The engine correctly implements most base-game mechanics: inventory, dealing, trump branches, bidding, ordinary follow-suit, winner resolution, scoring, round progression, termination, and score returns. Four material deviations remain: one clear printed-rule contradiction and three violations of approved human decisions. Provenance hashes match the supplied manifests.

## 2. Findings

### Major — Wizard-led tricks incorrectly acquire a led suit

- Canonical fact ID: `WIZ-C-WIZARD-LEAD-FREE`
- Evidence type: `rule_quote`
- Source ID: `WIZARD-RULES`
- Locator: `canonical_claims.json`, JSON Pointer `/claims/35`; PDF page 2
- Exact evidence: “Wird ein Stich mit einer Zaubererkarte eröffnet, dann dürfen die folgenden Lehrlinge beliebige Karten abwerfen”
- Conflicting code: `Game.apply_action`, `if state.led_suit is None and _suit(card) is not None` at `implementation.py:162`, followed by `Game.legal_actions` at lines 132–137.
- Expected: Once a Wizard leads, every subsequent card remains legal for the entire trick; no led-suit obligation may arise.
- Implemented: The first later ordinary card assigns `state.led_suit`. Later players holding that suit are then prevented from playing other ordinary suits.
- Impact: Materially wrong legal-action set in a common trick transition, though the game can still complete.

### Major — Jester → Wizard decision is only partially implemented

- Canonical fact IDs: `WIZ-G-JESTER-WIZARD`, resolved by `WIZ-DEC-JESTER`
- Evidence type: `human_decision`
- Source ID: `WIZARD-V2-RULEFACTS`
- Locator: `canonical_rulefacts.md`, “Material source gaps and proposed clarification decisions,” item 6
- Exact evidence: “a Wizard before that card keeps the trick colorless, allows all later cards, and the first Wizard wins.”
- Conflicting code: `Game.apply_action` at `implementation.py:162` and `Game.legal_actions` at lines 132–137.
- Expected: After leading Jester(s), a Wizard played before any ordinary card keeps the trick colorless; all remaining cards are legal, and the first Wizard wins.
- Implemented: The first-Wizard winner rule is correct, but a later ordinary card sets `led_suit` and can restrict subsequent players.
- Impact: Adjudication-dependent legality error for four- through six-player tricks. This is separate from the printed Wizard-lead contradiction above.

### Major — First dealer is randomized instead of player 0

- Canonical fact ID: `WIZ-G-FIRST-DEALER-RESET`, resolved by `WIZ-DEC-FLOW`
- Evidence type: `human_decision`
- Source ID: `WIZARD-V2-RULEFACTS`
- Locator: `canonical_rulefacts.md`, “Material source gaps and proposed clarification decisions,” item 2
- Exact evidence: “player 0 is the first dealer/scorekeeper; collect and reshuffle all 60 cards between rounds; rotate dealer clockwise.”
- Conflicting code: `Game.initial_state`, `dealer = rng.randrange(self.num_players)` at `implementation.py:105`.
- Expected: Player 0 is always the first dealer.
- Implemented: The initial dealer depends on the seed-derived RNG.
- Impact: Changes initial bidding, leadership, trump-choice authority, and subsequent dealer rotation. Collection, reshuffling, and clockwise rotation themselves are implemented correctly.

### Major — Completed played cards cease to be public

- Canonical fact ID: `WIZ-G-PRIVACY`, resolved by `WIZ-DEC-PRIVACY`
- Evidence type: `human_decision`
- Source ID: `WIZARD-V2-RULEFACTS`
- Locator: `canonical_rulefacts.md`, “Material source gaps and proposed clarification decisions,” item 8
- Exact evidence: “each player observes their own cards and opponents’ hand sizes; predictions, revealed trump, and played cards are public.”
- Conflicting code: `Game.observation_to_data` at `implementation.py:271–272`.
- Expected: Observations expose played cards publicly, including cards already moved into completed tricks.
- Implemented: The current trick is exposed, but completed tricks are represented only by `completed_trick_count`; their cards are hidden.
- Impact: Material loss of approved public information after each trick finishes.

No critical or minor findings identified.

## 3. Rule-area coverage

| Rule area | Result |
|---|---|
| Scope/provenance | Pass; base variant declared and supplied hashes match |
| Players and inventory | Pass |
| Initial setup | Major: wrong first dealer |
| Round deal/reset/dealer rotation | Pass apart from initial dealer |
| Trump reveal and choice | Pass |
| Predictions | Pass |
| Clockwise turn flow and leadership | Pass |
| Ordinary follow-suit and specials | Major: Wizard-colorless transitions |
| Trick winner and credit | Pass |
| Scoring | Pass |
| Final round and termination | Pass |
| Returns/joint winners | Pass; raw scores preserve all equal highest scorers |
| Private/public observations | Major: completed played cards omitted |
| Excluded variants | Pass; no variant behavior observed |

## 4. Missing deterministic scenarios

These behaviors require deterministic coverage:

1. Wizard leads, an ordinary card follows, and a later player holds that ordinary suit plus another ordinary suit; both must remain legal.
2. Jester → Wizard → ordinary card in a four-or-more-player trick; every remaining card must stay legal and the first Wizard must win.
3. Across multiple seeds and every supported player count, the initial dealer must always be player 0.
4. After a trick completes, every player’s observation must expose the completed trick’s played cards while keeping opponents’ unplayed cards private.
5. A regression pairing ordinary lead → Wizard with Wizard lead → ordinary, confirming that only the former retains the original ordinary follow-suit obligation.

## 5. Material questions for a human

None. The supplied approved decisions resolve all identified material source gaps. The page-2 variants remain excluded.

```text
score: 0.72
confidence: high
critical_issues: 0
major_issues: 4
minor_issues: 0
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true
```