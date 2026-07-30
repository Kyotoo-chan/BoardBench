## Review result

`score: 0.80`, `confidence: high`.

The module implements the core beginner game comprehensively, including the emphasized Longest Road recalculation and road-stock rules. The principal weaknesses are one clear printed-rule privacy violation and three failures in the approved digital interrupt/consent protocol. Review was static as required; no code was edited or checks executed.

## Findings

### Major — contradiction of a clear printed rule

1. Domestic-offer construction reveals an opponent’s private resource identities.

- Canonical fact: `CAT-C-INFO-RESOURCE-PRIVATE`
- Evidence type: `rule_quote`
- Source: `CATAN22-RULES`, PDF page 2
- Exact evidence: “Seine Rohstoffkarten hält jeder Spieler verdeckt in der Hand.”
- Conflicting symbol: [`Game.legal_actions`, `trade_offer`](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-jEvcwB/boardbench_clear_rule_emphasis_r2_judge_1_v2up6thu/implementation.py:299), especially lines 301–306.
- Expected: Offer construction must not disclose which resource types the partner holds. The approved finite bound may use public aggregate hand size, with actual holdings checked upon acceptance.
- Implemented: An `add_trade_item` action for a requested resource exists only while the partner owns another card of that exact type. Inspecting legal actions therefore reveals every type and its exact quantity.

### Major — deviations from approved human decisions

2. A Knight interrupt can give trade-consent control to the offering player.

- Canonical facts: `CAT-M-DEV-BOUNDARY`, `CAT-M-TRADE-PROTOCOL`
- Evidence type: `human_decision`
- Source: `CATAN22-V2-RULEFACTS`, “Approved decisions,” items 5 and 7
- Exact evidence:
  - “Domestic trade: finite bilateral offer builder, one partner, positive bundles on both sides, explicit accept/reject, atomic transfer only on acceptance.”
  - “An eligible card may interrupt pending discard, seven-sourced robber or trade-consent decisions; resolve it on a pending-state stack, then resume unless terminal.”
- Conflicting transitions: [`Game._push_robber`](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-jEvcwB/boardbench_clear_rule_emphasis_r2_judge_1_v2up6thu/implementation.py:435) and `trade_offer → play_knight → robber → trade_offer`.
- Expected: After resolving the interrupt, the original partner remains the current decision-maker and must accept or reject.
- Implemented: `_push_robber` always records `resume_current_player=active_player`. When Knight interrupts an awaiting trade response, resolution resumes with the offeror as current player, allowing the offeror to accept its own offer.

3. Trade acceptance is not revalidated after an interrupt changes holdings.

- Canonical facts: `CAT-M-TRADE-PROTOCOL`, `CAT-M-TRADE-OFFER-BOUND`
- Evidence type: `human_decision`
- Source: `CATAN22-V2-RULEFACTS`, “Approved decisions,” items 5 and 9
- Exact evidence:
  - “atomic transfer only on acceptance.”
  - “acceptance validates actual holdings.”
- Conflicting transition: [`accept_domestic_trade`](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-jEvcwB/boardbench_clear_rule_emphasis_r2_judge_1_v2up6thu/implementation.py:371).
- Expected: If Knight theft or Monopoly makes either bundle unavailable while consent is pending, acceptance must cease to be legal or fail atomically without changing resources.
- Implemented: Acceptance remains unconditional and applies arithmetic directly. A depleted participant can acquire a negative resource count.

4. Submitted seven-discard cards are not protected by escrow during development interrupts.

- Canonical fact: `CAT-M-DISCARD-ESCROW`
- Evidence type: `human_decision`
- Source: `CATAN22-V2-RULEFACTS`, “Approved decisions,” item 10
- Exact evidence: “submitted private selections are unavailable to interrupts and settle together after every required submission.”
- Conflicting symbols: [`Game._submit_discard`](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-jEvcwB/boardbench_clear_rule_emphasis_r2_judge_1_v2up6thu/implementation.py:426) and `_play_development`.
- Expected: Submitted cards are reserved immediately, cannot be stolen or transferred by Monopoly, and all escrows settle together.
- Implemented: A submission records only resource names and quantities; the cards remain in the player’s ordinary holdings. A later Knight or Monopoly interrupt can transfer them, after which final discard settlement subtracts them again and may create negative counts.

### Minor

5. Played progress cards remain represented in the development hand.

- Canonical fact: `CAT-C-PROGRESS-REMOVED`
- Source: `CATAN22-RULES`, PDF page 4
- Evidence: “Danach wird die Karte aus dem Spiel entfernt.”
- Conflicting symbol: [`Game._play_development`](/C:/Users/benti/AppData/Local/Temp/.ctx-mode-jEvcwB/boardbench_clear_rule_emphasis_r2_judge_1_v2up6thu/implementation.py:478).
- The card is marked revealed and added to `played_development`, but is never removed from `development_hand`. It cannot be replayed and is excluded from hidden counts, so this is primarily a zone/serialization inconsistency.

## Rule-area coverage

| Rule area | Coverage | Assessment |
|---|---|---|
| 3/4-player illustrated setup | Complete | Fixed board, colors, pieces, starting resources, bank, robber and deck represented |
| Turn order and strict phases | Complete | Roll → trade → build; clockwise progression |
| Production and shortages | Complete | Settlements/cities, robber blocking and approved all-or-none shortages |
| Domestic/maritime trade | Defective | Core exchanges work; private holdings leak and pending acceptance is unsafe |
| Paid building and stock | Complete | Costs, connectivity, distance, upgrades and piece limits |
| Seven and robbery | Partial | Printed sequence works; approved discard escrow is absent |
| Development cards | Partial | Effects and timing mostly complete; interrupt restoration has defects |
| Longest Road | Complete | Threshold, branches, blocking, ties, transfer and edge-simple loops implemented |
| Largest Army | Complete | Threshold, strict transfer and scoring implemented |
| Private information | Defective | Observations are mostly filtered, but legal offers leak resources |
| Victory and returns | Complete | Active-player immediate victory, hidden VP handling and terminal returns |
| Serialization/zones | Partial | Progress-card removal is represented inconsistently |

## Missing deterministic scenarios

- Two partners with equal public hand size but different resource composition must expose identical offer-builder actions.
- Awaiting trade response → active player plays Knight → robbery completes → original partner still controls accept/reject.
- Pending offer → Monopoly or theft removes an offered card → acceptance is unavailable and all holdings remain nonnegative.
- Multiple seven discards → one player submits → development interrupt targets that player → escrowed cards remain untouchable and settle once.
- Progress-card play removes the card from the live development-hand zone.
- Emphasis regression matrix: Longest Road threshold, branching, own/opponent interruption, both tie outcomes, loop handling, zero/one/two road pieces, and immediate victory from the award.
- Immediate victory during the first free Road Building placement cancels the second placement.
- Three- and four-player initial-state snapshots validating every illustrated piece and starting resource.

## Material questions for a human

None. The material deviations above are decided by either clear printed rules or the approved human decisions; no additional rulebook adjudication is needed.

```text
score: 0.80
confidence: high
critical_issues: 0
major_issues: 4
minor_issues: 1
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true
```