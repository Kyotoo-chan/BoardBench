score: 0.44  
confidence: high

The module implements much of the ordinary turn structure, inventory, hand-order rules, and most beanometers correctly. However, final scoring can select the wrong winner, and several material setup, action, chance, and information rules are contradicted.

## Findings

### Critical — Final harvest is omitted, so the winner can be fundamentally wrong

- Canonical facts: `BOHN-C-FINAL-HARVEST`, `BOHN-C-HIGHEST-WINS`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2
- Exact evidence: “Jede Person erntet noch ihre Bohnenfelder und erhält gegebenenfalls dafür Bohnentaler. … Wer die meisten Taler besitzt, gewinnt.”
- Conflicting code: `Game._finish`; it immediately computes `best = max(p["coins"] ...)` without harvesting any fields.
- Expected: Harvest every player’s fields using the applicable beanometers, add those coins, ignore hands, and then determine the highest final total.
- Implemented: The winner is determined solely from coins earned before termination. Valuable planted fields are neither scored nor emptied, so ordinary end states can produce the wrong winner.

### Major — Three-player games receive only two fields per player

- Canonical fact: `BOHN-C-FIELDS-3`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 1
- Exact evidence: “Spielt ihr zu dritt, legt ihr die Seite mit den drei Bohnenfeldern vor euch ab.”
- Conflicting code: `Game.initial_state`, player construction with `"fields": [[], []]` for every player count.
- Expected: Three fields per player at three players; two at four or five.
- Implemented: Always two fields, materially changing planting and forced-harvest decisions in the three-player game.

### Major — The Garden Bean meter is underpaid

- Canonical fact: `BOHN-C-PAYOUT-GARTEN`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 1, Garden Bean card beanometer
- Exact evidence: canonical visual transcription: “Garden: size 1 pays 0, size 2 pays 2, size 3 or more pays 3.”
- Conflicting code: `METERS["gartenbohne"] = ((2, 1), (3, 2))`.
- Expected: Two Garden Beans pay 2 coins; three or more pay 3.
- Implemented: They pay 1 and 2 respectively, directly affecting scores and winners.

### Major — Legal trades are capped at two cards per side

- Canonical fact: `BOHN-C-TRADE-UNEQUAL`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2
- Exact evidence: “Ihr dürft mit einer unterschiedlichen Kartenanzahl handeln.”
- Conflicting code: `Game._trade_proposals`, documented and implemented as “one or two cards each side.”
- Expected: Complete mutually agreed unequal bundles are legal; the approved fact imposes no two-card ceiling.
- Implemented: Only singleton and two-card combinations are generated. A legal bundle containing three or more cards on either side cannot be proposed.

### Major — Owners cannot choose the planting order of staged cards

- Canonical fact: `BOHN-C-PLANT-OWNER-ORDER`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2
- Exact evidence: “Jede Person darf selbst entscheiden, in welcher Reihenfolge sie die neuen Bohnenkarten anbaut.”
- Conflicting code: `Game.legal_actions` in `plant_received`, which always sets `bean = cards[0]`; `trade_accept` also imposes an index-derived staging order.
- Expected: Each owner may select any of their staged received/revealed cards as the next card to plant.
- Implemented: Only the first stored card can be planted. The active player is additionally forced to exhaust `pending_received` before choosing untraded revealed cards.

### Major — First and second recycling can be delayed past the depletion event

- Canonical fact: `BOHN-C-RECYCLE-FIRST-SECOND`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2
- Exact evidence: “Ziehst du die letzte Karte vom Nachziehstapel, mische die Karten des Ablagestapels. Danach legst du sie als neuen Nachziehstapel wieder verdeckt in die Tischmitte.”
- Conflicting code: `Game._draw_one` and `Game._recycle_or_end`.
- Expected: Drawing the last card on the first or second depletion immediately fixes and shuffles the then-current discard into the replacement pile.
- Implemented: Recycling is checked only before the next draw. If the last card was the last required card of a reveal/draw action, trading, planting, and harvesting may happen before recycling, improperly adding later discards to that recycle.

### Major — Off-turn harvesting is unavailable at most approved decision boundaries

This is an adjudication-dependent deviation, separate from a direct printed-rule contradiction.

- Canonical facts: `BOHN-C-HARVEST-ANYTIME`, `BOHN-A-HARVEST-INTERRUPT`
- Evidence type: `human_decision`
- Source: `BOHN-BASE-2023-V2-RULEFACTS`, “Approved human decisions,” item 3
- Exact evidence: “expose off-turn harvesting at stable player decision boundaries, not inside one atomic draw, shuffle, transfer or planting transition.”
- Conflicting code: `Game.legal_actions`, which generates harvest actions only for `current_player`.
- Expected: At stable boundaries, eligible non-active owners must be able to harvest their own fields.
- Implemented: During most active-player decisions, every other player is excluded. Off-turn harvest happens only incidentally when that player is already `current_player`, such as a trade respondent or selected phase-three planter.

### Major — Phase-three inter-player order is fixed rather than selectable

This is also an adjudication-dependent deviation.

- Canonical fact: `BOHN-M-PHASE3-INTERPLAYER-ORDER`
- Evidence type: `human_decision`
- Source: `BOHN-BASE-2023-V2-RULEFACTS`, “Approved human decisions,” item 2
- Exact evidence: “any affected owner with staged cards may plant next; all staged cards must finish before phase four.”
- Conflicting code: `Game._next_phase3_actor`, selecting `min(..., key=lambda i: (i-ap) % n)`.
- Expected: Any currently affected owner may be chosen next.
- Implemented: The active player is always preferred, followed by a fixed clockwise order, with no legal choice of another affected owner.

### Major — Legal-action enumeration reveals deeper opponent hand identities

This is an adjudication-dependent information-policy deviation.

- Canonical fact: `BOHN-M-OBS-DEEPER-HAND`
- Evidence type: `human_decision`
- Source: `BOHN-BASE-2023-V2-RULEFACTS`, “Approved human decisions,” item 4
- Exact evidence: “expose the selected player's complete ordered hand and every opponent's size plus publisher-visible front card; hide only deeper opponent identities.”
- Conflicting code: `Game._trade_proposals` calls `_refs(d, partner, "hand")`; each returned action embeds every opponent card’s `bean` and index.
- Expected: An acting player may see an opponent’s hand size and front card, but not deeper identities.
- Implemented: Inspecting legal trade proposals reveals the identity and position of every deeper opponent card, bypassing the otherwise-correct observation filtering.

No minor findings.

## Rule-area coverage

| Rule area | Result | Notes |
|---|---|---|
| Player range and inventory | Pass | Supports 3–5; 104-card eight-bean inventory is correct |
| Setup | Fail | Three-player field count is wrong |
| Hand order and phase-one planting | Pass | Front planting, optional second planting, append order |
| Reveal and ordinary phase flow | Mostly pass | Two-card reveal and four-phase structure represented |
| Trading | Partial | Consent and atomic transfer exist; bundle ceiling is wrong |
| Phase-three planting | Fail | Owner order and affected-player choice are missing |
| Harvesting | Partial | Protection and most meters work; Garden meter and timing fail |
| Recycling/chance | Partial | Seeded shuffle exists; first/second recycle timing is wrong |
| Private information | Fail | Trade-action side channel exposes deeper hands |
| Terminal scoring | Fail | Final harvest is absent; winner can be wrong |
| Returns | Partial | One-hot winner returns are coherent, but inherit wrong scoring |

## Missing deterministic scenarios

- Three-player setup with all players receiving exactly three usable fields.
- Garden harvests at sizes 1, 2, 3, and greater than 3.
- A final harvest that changes the pre-terminal leader and winner.
- Final harvest producing a tie resolved clockwise from the fixed start player.
- A legal 3-to-1 or larger unequal trade, using arbitrary hand positions, with no transfer before consent.
- Multiple staged cards where planting them in different owner-selected orders changes which field must be harvested.
- Active-player received cards mixed with untraded revealed cards, allowing either category to be selected next.
- Multiple affected phase-three owners with each available as the next actor.
- Off-turn harvest by a player who is neither active nor the current trade/plant actor.
- First or second depletion on the final required draw, proving recycling occurs before later discards are created.
- Legal-action inspection proving deeper opponent hand identities remain hidden.

## Material questions for a human

- `BOHN-M-EMPTY-DISCARD-RECYCLE`: The packet does not decide what happens when a first or second depletion has an empty or insufficient discard. `_recycle_or_end` currently terminates the game, but that behavior is unsupported rather than a scored printed-rule contradiction. A human policy is needed.
- `BOHN-A-HARVEST-INTERRUPT`: Stable-boundary availability is decided, but priority remains unspecified if several off-turn players request harvests at the same boundary. The action protocol needs a deterministic scheduling policy.

score: 0.44
confidence: high
critical_issues: 1
major_issues: 8
minor_issues: 0
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true