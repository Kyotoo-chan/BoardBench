Score: **0.45**, confidence: **high**. Most basic four-phase mechanics exist, but terminal scoring is fundamentally incorrect and several material setup, trading, timing, ordering, and information rules are contradicted.

## Findings

### Critical — Final harvest is omitted, so scores and winners are frequently wrong

- Canonical facts: `BOHN-C-FINAL-HARVEST`, `BOHN-C-HIGHEST-WINS`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2; `canonical_claims.json#/claims/68` and `/claims/71`
- Exact evidence: “Jede Person erntet noch ihre Bohnenfelder und erhält gegebenenfalls dafür Bohnentaler. … Wer die meisten Taler besitzt, gewinnt.”
- Conflicting code: `_finish()` lines 200–208.
- Expected: harvest every player’s fields using the relevant beanometers, add those coins, then determine the highest score and apply the tiebreak.
- Implemented: `_finish()` compares only coins earned before termination. It never harvests or clears fields. A player whose winning points remain planted can therefore lose.

Severity is critical because the mandated final scoring operation is absent and the reported winner can be fundamentally wrong.

### Major — Three-player games receive only two fields per player

- Canonical fact: `BOHN-C-FIELDS-3`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 1; `canonical_claims.json#/claims/1`
- Exact evidence: “Spielt ihr zu dritt, legt ihr die Seite mit den drei Bohnenfeldern vor euch ab.”
- Conflicting code: `Game.initial_state()`, lines 72–73.
- Expected: three fields for every player when `num_players == 3`.
- Implemented: `[[], []]` gives two fields for all player counts.

### Major — Garden Bean payouts are incorrect

- Canonical fact: `BOHN-C-PAYOUT-GARTEN`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 1; `canonical_claims.json#/claims/56`
- Exact evidence: “[Garden Bohnometer] size 1 pays 0, size 2 pays 2, size 3 or more pays 3.”
- Additional emphasis: `BOHN-V2-CLEAR-RULE-EMPHASIS`, `canonical_supplement.json#/emphasis/1`: “2 Garden Beans pay 2 coins; 3 or more Garden Beans pay 3 coins. There is no 1-coin Garden payout.”
- Conflicting code: `METERS["gartenbohne"]`, line 12.
- Expected: thresholds `(2,2)` and `(3,3)`.
- Implemented: `(2,1)` and `(3,2)`, underpaying every scoring Garden harvest.

### Major — Legal trades are arbitrarily capped at two cards per side

- Canonical facts: `BOHN-C-TRADE-ANY-HAND-POSITION`, `BOHN-C-TRADE-UNEQUAL`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2; `canonical_claims.json#/claims/32` and `/claims/34`
- Exact evidence: “Ihr dürft alle mit euren Handkarten handeln. Dabei spielt es keine Rolle, wo sich die Karten auf der Hand befinden.” and “Ihr dürft mit einer unterschiedlichen Kartenanzahl handeln.”
- Additional emphasis: `BOHN-V2-CLEAR-RULE-EMPHASIS`, `canonical_supplement.json#/emphasis/0`: “Represent the complete proposed bundles atomically … Do not reduce source-legal multi-card bundles…”
- Conflicting code: `_trade_proposals()`, lines 153–175, especially construction of only one- and two-card `offers` and `requests`.
- Expected: complete mutually agreed multi-card bundles, including unequal bundles beyond two cards, transfer atomically upon acceptance.
- Implemented: no proposal can contain more than two cards from either participant.

### Major — General off-turn harvesting is unavailable

- Canonical facts: `BOHN-C-HARVEST-OFFTURN`, `BOHN-C-HARVEST-ANYTIME`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2; `canonical_claims.json#/claims/48` and `/claims/90`
- Exact evidence: “Du darfst jederzeit im Spiel deine Bohnenfelder abernten, auch wenn du nicht die aktive Person bist.”
- Approved boundary decision, evidence type `human_decision`: `BOHN-BASE-2023-V2-RULEFACTS`, `canonical_rulefacts.md`, “Approved human decisions,” item 3: “expose off-turn harvesting at stable player decision boundaries.”
- Conflicting code: `legal_actions()`, lines 107–112.
- Expected: each owner can harvest at stable decision boundaries, including an otherwise uninvolved non-active player.
- Implemented: harvest actions are generated only for `current_player`. Players who are neither the current phase actor nor trade respondent cannot exercise the approved off-turn permission.

### Major — Phase-three planting order is improperly forced

- Canonical fact: `BOHN-C-PLANT-OWNER-ORDER`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2; `canonical_claims.json#/claims/44`
- Exact evidence: “Jede Person darf selbst entscheiden, in welcher Reihenfolge sie die neuen Bohnenkarten anbaut.”
- Conflicting code: `legal_actions()` lines 132–143 and planting lines 242–245.
- Expected: each owner selects any of their staged cards next, including choosing between received and untraded revealed cards.
- Implemented: only index `0` is offered; the active player must exhaust `pending_received` before accessing `revealed`.

There is also a separate adjudication-dependent deviation:

- Canonical fact: `BOHN-M-PHASE3-INTERPLAYER-ORDER`
- Evidence type: `human_decision`
- Source: `BOHN-BASE-2023-V2-RULEFACTS`, `canonical_rulefacts.md`, “Approved human decisions,” item 2; claim locator `canonical_claims.json#/claims/74`
- Exact evidence: “any affected owner with staged cards may plant next.”
- Conflicting code: `_next_phase3_actor()`, lines 210–217.
- Expected: any affected owner may be selected next.
- Implemented: the next owner is forced by clockwise distance from the active player.

### Major — First and second depletion recycling occurs too late

- Canonical fact: `BOHN-C-RECYCLE-FIRST-SECOND`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2; `canonical_claims.json#/claims/64`
- Exact evidence: “Ziehst du die letzte Karte vom Nachziehstapel, mische die Karten des Ablagestapels. Danach legst du sie als neuen Nachziehstapel wieder verdeckt in die Tischmitte.”
- Conflicting code: `_recycle_or_end()` and `_draw_one()`, lines 177–198.
- Expected: drawing the last card immediately triggers the first/second discard recycle.
- Implemented: recycling happens only before a later attempted draw. If the last card completes a reveal or three-card draw, harvesting and other actions may add new discards before recycling, incorrectly changing the recycled pile.

### Major — Legal-action enumeration exposes deeper opponent hand identities

- Canonical fact: `BOHN-M-OBS-DEEPER-HAND`
- Evidence type: `human_decision`
- Source: `BOHN-BASE-2023-V2-RULEFACTS`, “Approved human decisions,” item 4; claim locator `canonical_claims.json#/claims/76`
- Exact evidence: “expose the selected player's complete ordered hand and every opponent's size plus publisher-visible front card; hide only deeper opponent identities.”
- Conflicting code: `_refs()` and `_trade_proposals()`, lines 148–175.
- Expected: deeper opponent cards remain hidden; trade interaction must not reveal their identities through the action interface.
- Implemented: every opponent hand position and bean identity is embedded in generated `trade_propose` actions. This bypasses the otherwise-correct redaction in `observation_to_data()`.

This is an approved digital-observation decision rather than a contradiction of an independently complete printed privacy policy.

### Question — Empty-discard recycling has an unsupported terminal behavior

- Canonical fact: `BOHN-M-EMPTY-DISCARD-RECYCLE`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2; `canonical_claims.json#/claims/78`
- Exact evidence: “Ziehst du die letzte Karte … mische die Karten des Ablagestapels.”
- Code: `_recycle_or_end()`, lines 187–189, calls `_finish()` when a first/second recycle produces an empty deck.
- Packet status: explicitly missing—the supplied sources do not decide what happens with an empty or insufficient discard during a nonterminal recycle.
- Human decision needed: define whether this terminates, pauses, skips remaining draws, or uses another deterministic convention. This was not scored as a contradiction.

## Coverage

| Rule area | Result | Notes |
|---|---|---|
| Inventory and dealing | Pass | 104 cards, correct varieties/counts, five cards each |
| Player count and fields | Fail | Three-player field count wrong |
| Hand order and phase-one planting | Pass | Front-only mandatory plant, optional second, no third |
| Reveal and trade consent | Partial | Reveal, consent, staging work; bundles capped |
| Phase-three planting | Fail | Owner and inter-player ordering constrained |
| Harvesting | Partial | Singleton rule and most meters work; Garden and off-turn access fail |
| Draw/recycle/chance | Partial | Ordered draw works; first/second recycle timing wrong |
| Private information | Fail | Deeper hands leak through legal actions |
| Third depletion | Partial | Phase-two continuation exists; final resolution is wrong |
| Final scoring/winner/returns | Fail | Final harvest absent; returns inherit wrong winner |

## Missing deterministic scenarios

- Three-player setup asserting three fields and an 89-card draw pile.
- Garden harvests at sizes 1, 2, and 3.
- Final harvest that changes the winner, plus a post-final-harvest tiebreak case.
- Accepted and rejected trades with three or more cards on one or both sides.
- Uninvolved non-active player harvesting at representative stable boundaries.
- Active player choosing revealed before received cards, and arbitrary order within staged cards.
- Multiple affected phase-three owners choosing who plants next.
- First/second depletion on the final requested reveal or phase-four draw, verifying the immediate recycle snapshot.
- Third depletion on the first phase-two reveal, followed by phases two and three, final harvest, and no phase four.
- Observation plus legal-action inspection proving deeper opponent cards remain hidden.

## Material question for a human

What deterministic behavior should apply when the first or second depletion requires recycling but the discard pile is empty or insufficient to complete the current multi-card draw? The source packet deliberately leaves this undecided.

score: 0.45
confidence: high
critical_issues: 1
major_issues: 7
minor_issues: 0
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true