## Assessment

**score: 0.68 — confidence: high.** Source hashes match `SOURCE_MANIFEST.json`, and all 92 canonical claims were traced statically. Setup, harvesting, depletion, final scoring, and most phase transitions are faithful. Three material action/information defects remain; none prevents ordinary games from completing.

## Findings

### Major — Trade actions disclose every opponent’s deeper hand

- **Canonical fact:** `BOHN-M-OBS-DEEPER-HAND`, resolved by approved clarification.
- **Evidence type:** `human_decision`
- **Source:** `BOHN-V3-STRUCTURED-CLARIFICATION`
- **Locator:** `canonical_supplement.md`, “Clarified digital decisions,” item 4.
- **Exact evidence:** “For each opponent expose hand size and the source-visible front card, but hide deeper card identities. Legal-action data must not leak those deeper identities.”
- **Code:** `Game.legal_actions`, [implementation.py](C:/Users/benti/AppData/Local/Temp/.ctx-mode-JkRj5D/boardbench_bohnanza_base_2023_codex_ag_judge_2_6ga15ckq/implementation.py:123), lines 123–130.
- **Expected:** Trade-action data may expose an opponent’s size and front card, but not enumerate identities and positions of deeper cards.
- **Implemented:** `requested` is built from every card in each partner’s hand, including `{index, bean}` for all deeper positions. Thus the active player can recover every opponent hand from legal actions.

This is an adjudication-dependent contradiction of the approved privacy decision, not a contradiction of publisher text alone.

### Major — Advertised legal actions omit unequal multi-card trades

- **Canonical fact:** `BOHN-C-TRADE-UNEQUAL`
- **Evidence type:** `rule_quote`
- **Source:** `BOHN-BASE-2023-RULES`
- **Locator:** PDF page 2.
- **Exact evidence:** “Ihr dürft mit einer unterschiedlichen Kartenanzahl handeln, z. B. zwei blaue Bohnen gegen eine Gartenbohne.”
- **Code:** `Game.legal_actions`, lines 114–133; `Game.apply_action`, lines 209–212.
- **Expected:** A 2-for-1 trade, and other positive unequal bundles, must be available as legal choices.
- **Implemented:** The advertised set contains only one-card gifts and 1-for-1 trades. Hand-constructed multi-card proposals are specially accepted by `apply_action`, but are absent from `legal_actions`; the comment claiming “full-zone choices” is not implemented.

This materially restricts agents that select actions from the environment’s declared legal-action set.

### Major — Owners cannot choose the order of all their staged cards

- **Canonical fact:** `BOHN-C-PLANT-OWNER-ORDER`
- **Evidence type:** `rule_quote`
- **Source:** `BOHN-BASE-2023-RULES`
- **Locator:** PDF page 2.
- **Exact evidence:** “Jede Person darf selbst entscheiden, in welcher Reihenfolge sie die neuen Bohnenkarten anbaut.”
- **Code:** `Game.legal_actions`, lines 137–142.
- **Expected:** Each affected owner can select any of their remaining staged cards as the next card to plant. The approved inter-player decision still permits any affected owner to act next.
- **Implemented:** Only `pending_received[owner][0]` and `revealed[0]` are offered. Cards within each queue are therefore fixed in transfer/reveal order. Observations also expose only staged-card counts, so an owner cannot inspect and choose among all staged cards.

The implementation correctly allows different affected owners to act in any order, but not each owner’s required internal card choice.

### Minor — Invalid trade partners are not rejected safely

`Game._validate_proposal` checks that the partner differs from the active player but does not validate type or range. Because every `trade_propose` bypasses legal-set membership, an offered-only gift can install an invalid partner; acceptance may then crash, use Python negative indexing, or corrupt recipient agency. This is localized to malformed, hand-constructed actions rather than ordinary advertised play.

### Question — Insufficient discard supply during an early recycle

- **Canonical fact:** `BOHN-M-EMPTY-DISCARD-RECYCLE`
- The approved inventory explicitly says the packet does not specify behavior when a first/second recycle has insufficient discard cards.
- `_draw_one` returns `None`; during phase four, `apply_action` then invokes `_finish` even if fewer than three depletions occurred. During phase-two reveal, it instead proceeds with fewer revealed cards.

This is not scored as a rule contradiction because the packet deliberately leaves it undecided.

## Rule-area coverage

| Rule area | Result | Notes |
|---|---|---|
| Setup, inventory, fields | Pass | Correct 3–5 validation, 104-card inventory, five-card hands, field counts and seeded start |
| Hand order and phase one | Pass | Mandatory front, optional second, no third, separate harvest decision |
| Reveal and turn sequence | Pass | Correct normal phase ordering and clockwise advance |
| Trading | Major gaps | Consent and staging work; privacy and legal bundle advertisement do not |
| Phase-three planting | Major gap | All cards remain mandatory, but owner-selected order is restricted |
| Harvesting | Pass | Off-turn boundaries, singleton protection, conservation and all meters match |
| Recycling and termination | Pass/question | Printed first/second and third-depletion cases match; insufficient discard is unresolved |
| Final scoring and returns | Pass | Final harvest, ignored hands, highest coins and fixed-start tiebreak are correct |
| Private information | Major gap | Observation hand view is sound, but generated trade actions leak deeper hands |
| Input robustness | Minor gap | Invalid trade partner/reference shapes can escape validation |

## Missing deterministic scenarios

Scenarios needed to cover the identified boundaries:

1. A 2-for-1 trade appears through the supported legal-action interface and transfers all three cards atomically.
2. Legal-action data for each observer reveals opponent front cards but no deeper identities.
3. One owner has three differently typed staged cards and can choose the second or third one first.
4. The active player can choose freely between several received cards and several untraded revealed cards.
5. A multi-card trade preserves every transferred card while allowing later arbitrary planting order.
6. Invalid partners such as `-1`, `num_players`, strings, and missing partner fields are rejected before installing a pending proposal.
7. First/second depletion with sufficient discard continues both a two-card reveal and a three-card draw.
8. Third depletion is separately covered during phase-two reveal and phase-four draw.
9. Once a human ruling exists, insufficient-discard recycling needs a deterministic boundary scenario.

## Material questions for a human

- What should happen if a first or second depletion has no, or too few, discard cards to continue the interrupted reveal/draw?
- Should arbitrary trade bundles be fully enumerated, or should the interface expose a privacy-preserving parameterized trade builder? Either design must advertise 2-for-1 and larger legal trades without publishing deeper opponent hands.

```text
score: 0.68
confidence: high
critical_issues: 0
major_issues: 3
minor_issues: 1
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```