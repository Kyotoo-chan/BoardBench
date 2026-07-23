score: 0.62, confidence: high. The module accurately implements most setup, planting, harvesting, depletion, scoring, and phase-three rules. However, eager enumeration of every trade bundle makes ordinary legal game states computationally unusable, and gifts are only supported in one direction.

## Findings

### Critical — Trade action generation grows exponentially and can prevent normal games from completing

- Canonical fact ID: `CLAR-TRADE-01`
- Evidence type: `human_decision`
- Source: `BOHN-BASE-CLARIFY`, JSON Pointer `/clarifications/2/text`
- Exact evidence: “Jede endliche Anzahl zulässiger eigener Hand- oder Aufdeckkarten darf gegen jede endliche Anzahl zulässiger Handkarten der anderen beteiligten Person angeboten werden, begrenzt nur durch vorhandene Karten und beiderseitige Zustimmung.”
- Conflicting code: `Game._trade_actions`, `Game._nonempty_subsets`, and `Game.legal_actions`
- Expected: Arbitrarily sized finite bundles must remain representable while the game remains operational.
- Implemented: Every nonempty offered subset is eagerly crossed with every nonempty requested subset for every partner and stored in one list.

With 12 eligible active-player cards and 10 cards in a partner’s hand, one partner alone produces approximately `(2^12−1) × (2^10−1)`, or 4.19 million, non-gift proposals. Hands naturally grow when players plant one card and later draw three, so this is reachable without malformed state or unusual play. Larger hands can exhaust memory or make `legal_actions` effectively hang. A parameterized trade action or lazy decision sequence is needed.

### Major — A non-active participant cannot give a bean to the active player

- Canonical fact ID: `BASE-TRADE-07`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-RULES`, PDF page 2
- Exact evidence: “Als besondere Form des Handelns dürft ihr euch auch Bohnenkarten schenken. Die beschenkte Person muss dem Geschenk aber zustimmen. Lehnt sie ab, kommt der Handel nicht zustande.”
- Conflicting code: `Game._trade_actions` and `_validate_action_args`
- Expected: During the active player’s bilateral trading phase, either participant can be the donor in a gift, with the recipient accepting or rejecting it.
- Implemented: A gift must have a nonempty active-player `offered` bundle and an empty `requested` bundle. The inverse—empty active offer and one or more partner hand cards—is rejected and never generated.

Thus active-to-partner gifts work, but partner-to-active gifts cannot be represented.

### Question — Phase-three player ordering is imposed without source support

- Canonical facts: `BASE-PHASE3-01`, `CLAR-PHASE3-01`
- Evidence: The sources require every affected player to plant all staged cards and let each choose their own card order, but do not specify the ordering between affected players.
- Code: `Game._next_received_player`
- Behavior: The implementation processes the active player first, then affected players clockwise, returning to the active player for untraded revealed cards.
- Assessment: No penalty. This is an unsupported but necessary sequencing choice, and the packet does not establish a conflicting order. Because harvesting is allowed at stable boundaries, a human should confirm whether this imposed ordering is an acceptable representation.

## Rule-area coverage

| Rule area | Assessment |
|---|---|
| Inventory and player counts | Correct: 104 cards, eight types, 3–5 players |
| Initial fields and hands | Correct; starting player canonically fixed to player 0 |
| Hand order | Correctly preserves front-card order and appends draws |
| Turn phases | Correct four-phase progression |
| Hand planting | Correct mandatory first, optional second, no third |
| Field compatibility/forced harvest | Correctly forces a legal harvest when no field fits |
| Reveal | Correctly reveals up to two and handles third depletion |
| Trades | Quantities semantically supported, but eager enumeration is critically unscalable |
| Gifts | Missing partner-to-active gifts |
| Consent/staging | Correct accept/reject and received-card staging |
| Phase three | All affected players plant all cards and choose card order |
| Phase-four draw | Correct sequential three-card append and turn advance |
| Harvests | Correct off-turn availability, payout, clearing, and singleton protection |
| Recycling/end timing | Correct first/second recycling and clarified third-depletion behavior |
| Final scoring | Correct final field values, ignored hands, winner, and tie-break |
| Private observations | Matches the approved interface decision |
| Serialization | Normal generated states/actions round-trip; validation is permissive but not shown to contradict reachable play |

## Missing deterministic scenarios

- Reach trade phases with 8, 10, and 12 eligible active-player cards and assert bounded-time legal-action access.
- Partner gives one or several hand cards to the active player as a gift; test acceptance and rejection.
- Active gives multiple cards to a partner, including revealed cards.
- Explicit 1-for-2 and 3-for-1 accepted trades.
- Multiple non-active players receive cards and independently choose non-front planting order.
- Third depletion on the first versus second phase-two reveal.
- Third depletion on each of the three phase-four draws.
- Forced harvest where singleton protection leaves only particular fields legal.
- Final ties at every clockwise distance from the Start-card holder.

## Material questions for a human

- Confirm that reciprocal gift wording permits a non-active trading participant to donate to the active player. If gifts are intentionally restricted to active-player donations, the source condition should state that restriction.
- Confirm whether the implementation’s active-first, clockwise phase-three ordering is an acceptable adjudication, particularly because players may harvest between planting decisions.

score: 0.62
confidence: high
critical_issues: 1
major_issues: 1
minor_issues: 0
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true