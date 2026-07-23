## 1. Score

`score: 0.56` — `confidence: high`

The implementation captures most printed rules accurately, including inventory, field counts, ordered hands, planting, payouts, depletion timing, phase-three planting, harvesting, and tie-breaking. However, legal trade generation grows exponentially and can make ordinary midgame states impractical, while gifts are implemented in only one direction.

## 2. Findings

### Critical — Eager trade enumeration can make the core game unusable

- Canonical fact ID: `CLAR-TRADE-01`
- Evidence type: `human_decision`
- Source: `BOHN-BASE-CLARIFY`, JSON Pointer `/clarifications/2/text`
- Exact evidence: “Jede endliche Anzahl zulässiger eigener Hand- oder Aufdeckkarten darf gegen jede endliche Anzahl zulässiger Handkarten der anderen beteiligten Person angeboten werden, begrenzt nur durch vorhandene Karten und beiderseitige Zustimmung.”
- Conflicting symbols: `Game._trade_actions`, `Game._nonempty_subsets`, `Game.legal_actions`, `Game.apply_action`
- Expected: All finite eligible bundles must remain representable without making normal turns effectively stall.
- Implemented: `_trade_actions` eagerly materializes every nonempty subset of the active player’s eligible cards crossed with every nonempty subset of each partner’s hand. For hand sizes `a` and `b`, this produces roughly `(2^a−1)(2^b−1)` exchanges per partner, plus gifts. `apply_action` then calls `legal_actions` again for membership validation, repeating the enumeration.
- Impact: Hands can grow naturally when players plant one card and draw three. At ten eligible cards on each side, one partner alone produces over one million exchange proposals. Memory and runtime rise exponentially, creating a credible common midgame hang or exhaustion risk.

### Major — A partner cannot give cards to the active player as a gift

- Canonical fact ID: `BASE-TRADE-07`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-RULES`, PDF page 2
- Exact evidence: “Auch als besondere Form des Handels dürft ihr euch auch Bohnenkarten schenken. Die beschenkte Person muss dem Geschenk aber zustimmen. Lehnt sie ab, kommt der Handel nicht zustande.”
- Conflicting symbols: `Game._trade_actions`, `Game._validate_action_args`
- Expected: Within the permitted active-player/non-active-player relationship, either participant can be the donor; the recipient must consent.
- Implemented: Every proposal requires a nonempty `offered` bundle owned by the active player. A gift is rigidly defined as active player → partner with an empty `requested` bundle. A proposal with an empty active offer and a nonempty partner bundle is rejected.
- Impact: Legal partner → active-player gifts cannot be represented. Bidirectional exchanges and active-player gifts otherwise support arbitrary bundle sizes.

### Minor — Deserialization does not preserve setup constraints

- Canonical facts: `BASE-SETUP-01` and the rulebook’s 3–5-player condition
- Source: `BOHN-BASE-RULES`, PDF page 1
- Conflicting symbols: `Game.state_from_data`, `Game._validate_state`
- Expected: Loaded states should retain three fields for three players and two fields for four or five players.
- Implemented: `_validate_state` accepts any integer player count and any number of fields per player. Thus two-player states, six-player states, or incorrect field counts can be loaded even though `Game.__init__` correctly rejects such configurations.
- Impact: This affects malformed/imported states, not normally initialized games.

## 3. Rule-area coverage

| Rule area | Coverage | Assessment |
|---|---:|---|
| Inventory and initial deal | Complete | Correct 104-card distribution and five-card hands |
| Player/field setup | Partial | Normal setup correct; state loader permits invalid configurations |
| Hand order | Complete | Front-only planting, indexed trades, removals, and appends preserve order |
| Phase-one planting | Complete | Mandatory first, optional second, no third, empty-hand skip |
| Field constraints | Complete | Same-type planting and harvesting to create space work |
| Reveal and ordinary trades | Partial | Two-card reveal, bilateral consent, arbitrary positions and unequal bundles are modeled |
| Gifts | Incomplete | Only active-player-to-partner gifts exist |
| Phase-three planting | Complete | Every affected player plants all staged cards in self-chosen order |
| Drawing and turn rotation | Complete | Three sequential cards appended; clockwise rotation |
| Harvesting and payouts | Complete | Off-turn boundaries, singleton protection, zero payout, and all curves match |
| Recycling and depletion | Complete | First/second recycling and clarified third-depletion timing match |
| Terminal scoring | Complete | Final field values, ignored hands, winner, and tie-break match |
| Private observations | Complete/unscored | Canonical observation hides opponent hands as directed |
| Operational playability | Defective | Trade action enumeration is exponential |

## 4. Missing deterministic scenarios

- A partner gives one or several hand cards to the active player for nothing, followed by active-player consent.
- Gifts in both directions, including rejection with no transferred cards.
- Trade phases with steadily growing hands, measuring legal-action construction and proposal application at 8, 10, and 12 eligible cards per participant.
- Serialization rejection for two or six players and for incorrect per-player field counts.
- Third depletion on the first versus second phase-two reveal.
- Third depletion on the first, second, or third phase-four draw.
- Phase three with multiple recipients, active-player received cards, and remaining untraded revealed cards.
- Forced harvest when all fields are occupied, including singleton protection.
- Boundary checks for every payout threshold, especially Garden beans at two and three cards.

## 5. Material questions for a human

- Must `legal_actions` explicitly enumerate every bundle, or may the environment expose a parameterized/lazy trade action? The sources require representability, but do not prescribe action-list construction.
- Should `state_from_data` reject every rule-invalid state or only ensure structural validity? The current loader treats several setup invariants as structural nonrequirements.
- Are exact trade proposal contents public to uninvolved players? The approved observation decision does not explicitly settle this, and the implementation hides them from nonparticipants.

```text
score: 0.56
confidence: high
critical_issues: 1
major_issues: 1
minor_issues: 1
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```