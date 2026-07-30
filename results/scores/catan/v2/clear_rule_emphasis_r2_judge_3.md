score: 0.76  
confidence: high

The normal setup, roll–trade–build flow, production, construction, robber handling, development-card effects, scoring, and Longest Road algorithm are broadly faithful. The principal defects occur when approved development-card interrupts interact with pending discards or domestic-trade consent; these can assign decisions to the wrong player or create negative resource holdings.

## Findings

### Major — Submitted discard escrow remains transferable

- Canonical fact ID: `CAT-M-DISCARD-ESCROW`
- Evidence type: `human_decision`
- Source: `CATAN22-V2-RULEFACTS`
- Stable locator: `canonical_rulefacts.md`, “Approved decisions,” item 10
- Exact evidence: “submitted private selections are unavailable to interrupts and settle together after every required submission.”
- Conflicting symbols: `_submit_discard`, `_play_development` (`monopoly`)
- Expected: Once a player submits a discard selection, those cards are escrowed and unavailable to an interrupting Monopoly or other transfer until all submissions settle.
- Implemented: `_submit_discard` records the selection but leaves the cards in the resource hand. An interrupting Monopoly can transfer them; final discard settlement then subtracts the original selection again. This can produce negative resources and violate resource conservation.

### Major — Knight interrupts resume a pending decision with the wrong player

- Canonical fact ID: `CAT-M-DEV-BOUNDARY`
- Evidence type: `human_decision`
- Source: `CATAN22-V2-RULEFACTS`
- Stable locator: `canonical_rulefacts.md`, “Approved decisions,” item 7
- Exact evidence: “resolve it on a pending-state stack, then resume unless terminal.”
- Conflicting symbols: `_play_development`, `_push_robber`, `_finish_pending`, `legal_actions`
- Expected: After an interrupting Knight finishes, the suspended discard or trade-consent decision resumes with the player who was making that decision.
- Implemented: `_push_robber` always records `resume_current_player` as the active player. If Knight interrupts a partner’s trade response, completion returns control to the active offeror. `legal_actions` then exposes `accept_domestic_trade` and `reject_domestic_trade` to the offeror, allowing the active player to answer their own offer. A discard interrupt similarly resumes initially at the wrong seat.

### Major — Trade acceptance does not revalidate holdings after an interrupt

- Canonical fact IDs: `CAT-M-TRADE-PROTOCOL`, `CAT-M-TRADE-OFFER-BOUND`
- Evidence type: `human_decision`
- Source: `CATAN22-V2-RULEFACTS`
- Stable locator: `canonical_rulefacts.md`, “Approved decisions,” items 5 and 9
- Exact evidence:
  - “atomic transfer only on acceptance.”
  - “acceptance validates actual holdings.”
- Conflicting transition: `apply_action` → `accept_domestic_trade`
- Expected: Acceptance atomically succeeds only if both parties still possess every offered card.
- Implemented: Acceptance applies unconditional arithmetic without checking current holdings. For example, while consent is pending, the active player can play Monopoly and remove the resource offered by the partner; the partner can subsequently accept, driving their resource count negative.

### Minor — Initial Longest Road measurement is stale

- Emphasis ID: `CATAN-EMPH-LONGEST-ROAD`
- Source: `CATAN-V2-CLEAR-RULE-EMPHASIS`, JSON Pointer `/emphasis/0/text`
- Evidence: “Keep owner and measured length synchronized.”
- Conflicting symbol: `initial_state`
- The illustrated setup contains roads, but `longest_road_length` starts at zero. `_recalculate_specials` corrects it after the first committed action, so award and winner behavior are unlikely to change, but the initial public measurement is inconsistent with the board.

### Minor — Played progress cards remain in the development hand

- Canonical fact ID: `CAT-C-PROGRESS-REMOVED`
- Evidence type: `rule_quote`
- Source: `CATAN22-RULES`, PDF page 4
- Exact evidence: “Fortschrittskarten kommen aus dem Spiel.”
- Conflicting symbol: `_play_development`
- Expected: A played progress card moves out of the player’s hand and out of play.
- Implemented: It remains in `development_hand` marked `revealed`, while also being copied into `bank.played_development`. It cannot be replayed, so this is chiefly a zone/serialization inconsistency.

## Rule-area coverage

| Rule area | Assessment |
|---|---|
| Beginner setup, 3/4 players | Correctly represented, including colors, illustrated pieces, resources, bank, deck, and robber |
| Turn and strict phases | Correct normal roll → trade → build flow |
| Production and shortages | Correct additive production, robber blocking, and approved all-or-none shortages |
| Domestic trade | Basic offer/consent works; interrupt revalidation and resumption are materially defective |
| Maritime trade | Correct harbor ratios, bank availability, and different receive type |
| Building and stock | Costs, connectivity, distance, upgrades, and stock limits are implemented |
| Seven and robbery | Core sequence is correct; discard escrow fails under interrupts |
| Development cards | Main effects and timing are present; Knight interrupt restoration is defective |
| Longest Road | Edge-simple trail, blocking, ties, transfers, and stock interaction are substantially correct |
| Largest Army | Threshold, strict transfer, and scoring are correct |
| Privacy/chance | Hands are hidden and deterministic chance is supported; provisional own-discard visibility is underspecified |
| Victory and returns | Active-player immediate victory, VP exception, pending cancellation, and returns are correct |

## Missing deterministic scenarios

Review-derived scenarios needed to cover the defects:

1. A player submits discards; the active player interrupts with Monopoly targeting an escrowed resource; escrow must remain unavailable and all counts nonnegative.
2. A domestic offer awaits the partner; the active player plays Knight; after robbery, the same partner must resume consent.
3. Knight interrupts another player’s discard selection; the same discarding player must resume.
4. A partner offers a resource, then an interrupting Monopoly removes it; acceptance must be rejected or the offer canceled atomically.
5. Acceptance after any interrupt that changes either party’s holdings must never partially transfer or create negative counts.
6. Initial setup must report the actual measured longest route while leaving the award unowned.
7. Played Road Building, Year of Plenty, and Monopoly cards must reside outside the development hand.

## Material questions for a human

- The packet does not specify whether a player’s observation must show their own provisional discard selection. `observation_to_data` removes `selected` from the pending frame for every viewer, including the chooser. A digital-interface decision would clarify whether self-observation must be Markov-complete.
- No additional rulebook clarification is needed for the major findings: the approved human decisions already resolve both escrow and interrupt-resumption behavior.

score: 0.76
confidence: high
critical_issues: 0
major_issues: 3
minor_issues: 2
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true