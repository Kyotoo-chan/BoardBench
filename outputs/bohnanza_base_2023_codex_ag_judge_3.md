score: 0.72
confidence: high

Most setup, harvesting, depletion, scoring, and turn-order rules are implemented correctly. Three material defects remain: incomplete trade-action enumeration, loss of owner-controlled phase-three card order, and a clarification-dependent private-information leak. No normal-play critical failure was found.

## Findings

### Major — unequal multi-card trades are absent from the legal-action surface

- Canonical fact: `BOHN-C-TRADE-UNEQUAL`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2
- Exact evidence: “Ihr dürft mit einer unterschiedlichen Kartenanzahl handeln, z. B. zwei blaue Bohnen gegen eine Gartenbohne.”
- Conflicting code: `Game.legal_actions`, lines 112–133; `Game.apply_action`, lines 209–212
- Expected: Legal actions include exchanges such as two cards for one, with arbitrary positive bundle sizes on both sides.
- Implemented: `legal_actions` enumerates only one-for-one exchanges and one-way single-card gifts. Handcrafted multi-card proposals are accepted through a special `apply_action` bypass, but are missing from the authoritative discovery interface. An agent restricted to returned legal actions cannot make a printed-rule two-for-one trade.

### Major — owners cannot choose the planting order of their staged cards

- Canonical fact: `BOHN-C-PLANT-OWNER-ORDER`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2
- Exact evidence: “Jede Person darf selbst entscheiden, in welcher Reihenfolge sie die neuen Bohnenkarten anbaut.”
- Conflicting code: `Game.legal_actions`, lines 137–142; `Game._remove_refs`, lines 191–204
- Expected: During phase three, each owner may select any of their remaining received/revealed cards as their next card to plant.
- Implemented: Only `cards[0]` from each received list and `revealed[0]` are actionable. Moreover, multi-card transfers are staged in reverse source-index order by `_remove_refs`. The owner cannot override that imposed order.

### Major — legal-action data reveals every opponent’s deeper hand

This is an adjudication-dependent deviation from the approved supplement, separate from printed-rule contradictions.

- Canonical fact: `BOHN-M-OBS-DEEPER-HAND`
- Evidence type: `human_decision`
- Source: `BOHN-V3-STRUCTURED-CLARIFICATION`, `canonical_supplement.md`, “Clarified digital decisions,” item 4
- Exact evidence: “For each opponent expose hand size and the source-visible front card, but hide deeper card identities. Legal-action data must not leak those deeper identities.”
- Conflicting code: `Game.legal_actions`, lines 123–130
- Expected: Opponents’ deeper hand identities remain hidden in both observations and legal-action data.
- Implemented: Trade proposals are generated with every opponent hand index and its exact `bean` identity. Calling `legal_actions` therefore reveals the complete ordered hand of every possible partner, despite `observation_to_data` correctly hiding it.

### Minor — deserialized states need not obey basic game invariants

`Game.state_from_data`, lines 347–367, checks only that card names are recognized and that total cards plus coins equal 104. It does not enforce exact per-bean inventory (`BOHN-C-INV-*`), the correct number of fields (`BOHN-C-FIELDS-3`, `BOHN-C-FIELDS-4-5`), or one bean type per field (`BOHN-C-FIELD-ONE-TYPE`). Normal `initial_state` setup is correct, so this primarily affects externally supplied states.

### Minor — invalid trade partners can enter a broken pending state

`apply_action` exempts every `trade_propose` from legal-action membership, while `_validate_proposal` never checks that `partner` is an existing player. An offered-only gift to an out-of-range partner can be accepted into `trade_response`; later acceptance indexes a nonexistent `pending_received` entry. This is an invalid-input robustness defect rather than a legal-play failure.

### Question — empty discard during a nonterminal depletion

- Canonical fact: `BOHN-M-EMPTY-DISCARD-RECYCLE`
- Source: `BOHN-BASE-2023-RULES`, PDF page 2
- Evidence: “Ziehst du die letzte Karte vom Nachziehstapel, mische die Karten des Ablagestapels.”
- Packet status: explicitly missing/undecided.
- Code behavior: `_draw_one` leaves the deck empty when the discard is empty; a later phase-four draw calls `_finish` even when fewer than three depletions occurred.
- Human decision needed: Specify whether play waits for discard supply, terminates, or follows another deterministic fallback. This was not scored as a contradiction.

### Question — visibility of staged sideways cards

`observation_to_data` exposes only `pending_received_counts`, not the staged cards’ identities. `BOHN-C-RECEIVED-STAGED` says they are placed sideways beside the recipient’s fields, but the approved packet does not expressly define their digital visibility. A human should decide whether these identities are public.

## Rule-area coverage

| Rule area | Result | Notes |
|---|---|---|
| Setup and inventory | Covered | Correct player range, deck composition, hand sizes, fields, seeded start |
| Hand order and phase one | Covered | Mandatory front card, optional second card, forced harvest supported |
| Reveal and trading | Partial | Consent and atomic transfers work; legal-action enumeration is incomplete |
| Phase-three planting | Material defect | All cards are mandatory, but owners cannot choose their own order |
| Fields and harvesting | Covered | Singleton protection, zero payouts, conservation, all meters correct |
| Chance and depletion | Covered with question | First/second recycling and third-depletion exception work when discard supply exists |
| Private information | Material deviation | Observation is mostly correct; legal actions leak deeper hands |
| Terminal scoring | Covered | Final harvest, ignored hands, highest coins, and clockwise tiebreak are correct |
| Returns | Covered | One-hot return corresponds to the correctly selected winner |
| Serialization/validation | Partial | Round-trip structure exists but accepts rule-invalid states |

## Missing deterministic scenarios

Recommended deterministic scenarios:

1. `BOHN-C-TRADE-UNEQUAL`: verify a two-for-one exchange is present in the legal-action interface and transfers atomically after consent.
2. `BOHN-C-PLANT-OWNER-ORDER`: give one owner three differently typed staged cards and verify each can be selected first.
3. `BOHN-M-OBS-DEEPER-HAND`: inspect legal-action data from every player perspective and assert that only opponent hand sizes/front cards are exposed.
4. Multi-owner phase three: verify either affected owner may act next while each independently chooses their card order.
5. Invalid out-of-range trade partner: require clean rejection without state mutation or runtime indexing failure.
6. Imported-state invariants: reject wrong bean multiplicities, field counts, and mixed-type fields.
7. Once clarified, deterministic first/second depletion with an empty or insufficient discard pile.
8. Once clarified, observation visibility for staged sideways cards.

## Material questions for a human

- What deterministic behavior should replace the implementation’s early finish when a first/second depletion has no sufficient discard supply?
- Are staged sideways cards public by identity to every player, or should observations expose only their counts?
- Should `legal_actions` be exhaustive, or is the undocumented handcrafted-action path considered part of the supported action protocol? If exhaustive—as normally expected—the multi-card trade omission requires correction.

```text
score: 0.72
confidence: high
critical_issues: 0
major_issues: 3
minor_issues: 2
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```