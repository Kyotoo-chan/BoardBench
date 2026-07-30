Score: **0.83**, confidence: **high**. The module statically covers the illustrated 3/4-player setup and most clear gameplay rules well, including strict phases, production, building legality, awards, development effects, privacy, and immediate victory. Three material defects affect the approved digital interrupt/consent protocol. No code or tests were executed.

## Findings

### Major — Knight interrupts resume with the wrong decision-maker

- Canonical fact ID: `CAT-M-DEV-BOUNDARY`
- Evidence type: `human_decision`
- Source: `CATAN22-V2-RULEFACTS`
- Locator: `canonical_rulefacts.md`, “Approved decisions,” item 7
- Exact evidence: “an eligible card may interrupt pending discard, seven-sourced robber or trade-consent decisions; resolve it on a pending-state stack, then resume unless terminal.”
- Conflicting code: `_play_development`, `_push_robber`, `_finish_pending` (`implementation.py:478-489`, `435-463`)
- Expected: After an interrupting Knight and its robber sequence, the exact suspended discard or trade-consent decision resumes with its prior decision-maker.
- Implemented: `_push_robber` always records `resume_current_player` as `active_player`. If a Knight interrupts another player’s discard or trade response, resolution resumes with the active player. During an awaiting trade response, this exposes `accept_domestic_trade` and `reject_domestic_trade` to the offeror, allowing self-acceptance.

This is an adjudication-dependent contradiction, not a contradiction of an independently clear printed atomic-boundary rule.

### Major — Submitted discard escrow remains stealable

- Canonical fact ID: `CAT-M-DISCARD-ESCROW`
- Evidence type: `human_decision`
- Source: `CATAN22-V2-RULEFACTS`
- Locator: `canonical_rulefacts.md`, “Approved decisions,” item 10
- Exact evidence: “submitted private selections are unavailable to interrupts and settle together after every required submission.”
- Conflicting code: discard selection/submission, `_submit_discard`, `_steal`, and Monopoly resolution (`implementation.py:355-358`, `426-433`, `452-458`, `492-495`)
- Expected: Once submitted, selected cards are escrowed and cannot be stolen or transferred by an interrupt before simultaneous settlement.
- Implemented: Submitted selections remain part of the player’s ordinary resource hand. An interrupting Knight or Monopoly can transfer them; later discard settlement deducts the original selection anyway, potentially producing negative resource counts.

This is also adjudication-dependent.

### Major — Trade acceptance does not revalidate holdings

- Canonical fact ID: `CAT-M-TRADE-PROTOCOL`
- Evidence type: `human_decision`
- Source: `CATAN22-V2-RULEFACTS`
- Locator: `canonical_rulefacts.md`, “Approved decisions,” item 5
- Exact evidence: “finite bilateral offer builder, one partner, positive bundles on both sides, explicit accept/reject, atomic transfer only on acceptance.”
- Additional exact evidence: “acceptance validates actual holdings.”
- Conflicting code: `legal_actions` awaiting-response branch and `accept_domestic_trade` (`implementation.py:299-312`, `371-376`)
- Expected: Acceptance is legal only if both parties still hold their complete promised bundles; transfer is then atomic.
- Implemented: Acceptance is always exposed and directly applies bundle deltas without checking current holdings. For example, an interrupting Monopoly can remove the partner’s promised resources, after which acceptance can drive that partner negative.

This is an adjudication-dependent protocol defect.

### Minor — Played progress cards remain in the development hand

- Canonical fact ID: `CAT-C-PROGRESS-REMOVED`
- Evidence type: `rule_quote`
- Source: `CATAN22-RULES`
- Locator: PDF page 4; `canonical_claims.json#/claims/76/source/quote`
- Exact evidence: “Danach wird die Karte aus dem Spiel entfernt.”
- Conflicting code: `_play_development` marks the card revealed but leaves it in `development_hand` and also appends a played record.
- Expected: A played progress card leaves the player’s hand and the game.
- Implemented: It remains as an inert revealed hand entry. This does not permit replay, so the gameplay effect is localized.

## Rule-area coverage

| Area | Result | Notes |
|---|---|---|
| Setup and inventory | Covered | Illustrated 3/4-player layouts, initial resources, stock, bank, deck and robber represented |
| Turn flow | Covered | Roll → trade → build; clockwise advancement |
| Production and seven | Partial | Production and robber sequence correct; discard escrow interrupt defect |
| Trading | Partial | Ratios, harbors and positive bilateral bundles covered; consent revalidation defective |
| Building and graph legality | Covered | Costs, stock, distance, connectivity, blocking and city replacement |
| Development cards | Partial | Effects and timing largely covered; interrupt restoration and progress-card removal defects |
| Awards and scoring | Covered | Longest Road/Largest Army recalculation, ties and scoring represented |
| Terminal and returns | Covered | Active-player immediate victory, minimum VP reveal and terminal returns |

## Deterministic scenarios needed

Because existing scenario/test artifacts were intentionally not inspected, these are scenarios needed to close the identified risks:

- Knight interrupts an awaiting trade response; the same partner must resume and the offeror must not accept.
- Knight interrupts each possible player’s discard; the exact suspended discarder resumes.
- A submitted discard selection followed by interrupting Knight theft or Monopoly; escrow cards must remain unavailable and no count may become negative.
- A trade offer followed by Monopoly removing the partner’s promised type; acceptance must disappear or be rejected atomically.
- Played Road Building, Year of Plenty, and Monopoly cards are absent from every development-hand zone afterward.
- Longest Road threshold, branch, own/opponent interruption, both interruption-tie outcomes, transfer, loop profile, and immediate victory from its award.
- Road Building with zero, one, and two remaining road pieces and with feasibility disappearing after the first placement.

## Material questions for a human

None are required to implement these fixes: the three digital behaviors are expressly decided by the approved fact inventory. The packet’s printed Knight decline conflict does not affect these findings because the approved profile mandates victim choice when an adjacent opponent exists.

score: 0.83
confidence: high
critical_issues: 0
major_issues: 3
minor_issues: 1
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true