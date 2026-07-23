## Review result

**Score: 0.62 — confidence: high.**

The module models most printed rules accurately: inventory, setup, ordered hands, planting, harvesting, payouts, phase-three planting, depletion timing, scoring, and tie-breaking. However, exhaustive trade-action construction can make ordinary late-game states computationally unusable, and one printed gift direction is absent.

## Findings

### Critical — Exponential trade enumeration can prevent games from completing

- **Canonical facts:** `CLAR-TRADE-01`, supported by `BASE-PLANT-02` and `BASE-DRAW-01`
- **Evidence type:** `human_decision`
- **Source:** `BOHN-BASE-CLARIFY`, `/clarifications/2/text`
- **Exact evidence:** “Jede endliche Anzahl zulässiger eigener Hand- oder Aufdeckkarten darf gegen jede endliche Anzahl zulässiger Handkarten der anderen beteiligten Person angeboten werden, begrenzt nur durch vorhandene Karten und beiderseitige Zustimmung.”
- **Conflicting symbols:** `_nonempty_subsets`, `_trade_actions`, `legal_actions`, and the membership check at the start of `apply_action`
- **Expected:** Every finite eligible bundle must remain representable while normal reachable trade states remain executable.
- **Implemented:** `_trade_actions` eagerly materializes every offered subset crossed with every requested subset for every partner. For pools of sizes `a` and `b`, this creates roughly `(2^a−1)(2^b−1)` exchanges per partner, plus gifts. Hands can grow because only one hand card is mandatory while three are drawn each turn. With 17 eligible active cards and a 15-card partner hand, one partner alone produces over four billion candidate exchanges. `apply_action` reconstructs the same list merely to check membership.
- **Impact:** Common sufficiently late trade phases can exhaust memory or effectively deadlock, so a core game may not complete reliably.

### Major — A non-active player cannot give cards to the active player

- **Canonical facts:** `BASE-TRADE-02`, `BASE-TRADE-07`
- **Evidence type:** `rule_quote`
- **Source:** `BOHN-BASE-RULES`, PDF page 2
- **Exact evidence:** “Als besondere Form des Handelns dürft ihr euch auch Bohnenkarten schenken. Die beschenkte Person muss dem Geschenk aber zustimmen. Lehnt sie ab, kommt der Handel nicht zustande.”
- **Conflicting symbols:** `_trade_actions`, `_validate_action_args`, `trade_propose`, `trade_response`
- **Expected:** Within the active player’s bilateral trading phase, either participant can be the donor; the recipient must consent. Thus the active player must be able to accept a gift from a non-active player.
- **Implemented:** Every gift must contain a nonempty `offered` bundle owned by the active player, must have an empty `requested` bundle, and always awaits the partner’s response. An empty active offer with a nonempty partner-side gift is rejected by `_validate_action_args`, so only active-to-partner gifts exist.
- **Impact:** A material printed trading option is absent.

No supported minor contradictions were found.

## Rule-area coverage

| Rule area | Coverage | Assessment |
|---|---:|---|
| Inventory and player setup | Complete | Counts, five-card hands, and 3/2 fields are correct |
| Hand order and phase-one planting | Complete | Front-card rule, optional second, no third, and empty-hand skip are correct |
| Forced harvest and field compatibility | Complete | Compatible planting and harvest-before-plant flow are represented |
| Reveal and ownership | Complete | Two public cards and active ownership are correct |
| Trading | Partial | Eligible bundles and consent work, but enumeration is non-scalable and reverse gifts are absent |
| Phase-three planting | Complete | All affected players choose order; active also plants remaining revealed cards |
| Drawing and turn rotation | Complete | Three sequential cards are appended and play rotates clockwise |
| Harvest legality and payouts | Complete | Off-turn boundaries, singleton protection, zero payouts, and all curves are correct |
| Recycling and third depletion | Complete | First two recycles and clarified terminal timing are correctly represented |
| Final scoring and tie-break | Complete | Hands ignored; final field values and clockwise tie-break are correct |
| Private information | Complete for scored fidelity | Canonical observations conceal opponent identities; privacy is explicitly unscored |
| Serialization validation | Unclear | Structural checks exist, but source condition does not establish required rejection semantics for impossible imported states |

## Missing deterministic scenarios

- Late-game trade legality with large hands, including a bounded-time/memory assertion.
- Active player accepting a gift originating from a non-active player.
- Active-to-partner gift acceptance and rejection with unchanged state after rejection.
- Multi-card trades such as 3-for-1 and 1-for-3 after earlier trades have changed hand indices.
- Phase three with several affected players, active received cards, and untraded revealed cards simultaneously.
- Forced harvest where singleton protection leaves only a multi-card field harvestable.
- Third depletion on the first reveal versus during the first or second phase-four draw.
- Final all-field valuation covering zero-value fields and the clarified Garden-bean curve.
- Ties involving the Start-card holder and multiple clockwise positions.

## Material questions for a human

- Must `state_from_data` reject states that violate exact field counts, card conservation, or phase/pending coherence? The publisher sources define legal play but do not specify deserialization trust boundaries.
- Is `render()` considered a player-facing observation surface? It exposes every hand identity, although privacy is expressly excluded from fidelity scoring.

score: 0.62
confidence: high
critical_issues: 1
major_issues: 1
minor_issues: 0
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true