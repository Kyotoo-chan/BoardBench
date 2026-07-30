## Assessment

Score: **0.72**, confidence: **high**. The module implements most setup, production, building, development-card effects, awards, and victory rules correctly. Three material defects remain: one clear printed privacy contradiction and two deviations from approved digital adjudications.

### Critical findings

None.

### Major findings

1. **Domestic-trade action enumeration reveals private resource identities**

   - Canonical fact ID: `CAT-C-INFO-RESOURCE-PRIVATE`
   - Evidence type: `rule_quote`
   - Source: `CATAN22-RULES`, PDF page 2
   - Exact evidence: “Rohstoffkarten hält jeder Spieler verdeckt in der Hand.”
   - Conflicting symbol: `Game.legal_actions`, `trade_offer`/`add_trade_item` generation, especially `self._player(s, owner)["resources"][r] > bundle[r]`
   - Expected: An active player may know an opponent’s aggregate hand size, but available actions must not disclose which resource types or quantities that opponent holds.
   - Implemented: A `take` item is exposed only when the selected partner actually holds another card of that resource. Repeatedly inspecting legal actions reveals every resource identity and exact per-type count in the partner’s hand.
   - Impact: Material private-information leak affecting negotiation and Monopoly decisions.

2. **Trade acceptance is not revalidated after permitted interrupts**

   - Canonical fact ID: `CAT-M-TRADE-PROTOCOL`
   - Evidence type: `human_decision`
   - Source: `CATAN22-V2-RULEFACTS`, “Approved decisions,” items 5 and 9
   - Exact evidence: “Domestic trade: finite bilateral offer builder, one partner, positive bundles on both sides, explicit accept/reject, atomic transfer only on acceptance.” Also: “acceptance validates actual holdings.”
   - Conflicting transition: `accept_domestic_trade` in `Game.apply_action`
   - Expected: At acceptance, both parties must still possess their promised bundles. If not, the transfer must not commit.
   - Implemented: Acceptance performs unconditional arithmetic without checking either hand. An allowed Monopoly or Knight interrupt can remove a promised resource before consent, after which acceptance creates a negative resource count while crediting the other player.
   - Impact: Corrupts resource conservation and permits impossible trades.

3. **Knight interrupts resume pending decisions with the wrong player**

   - Canonical fact ID: `CAT-M-DEV-BOUNDARY`
   - Evidence type: `human_decision`
   - Source: `CATAN22-V2-RULEFACTS`, “Approved decisions,” item 7
   - Exact evidence: “an eligible card may interrupt pending discard, seven-sourced robber or trade-consent decisions; resolve it on a pending-state stack, then resume unless terminal.”
   - Conflicting symbols: `Game._play_development` → `Game._push_robber`; `_push_robber` stores `resume_current_player = active_player`
   - Expected: After the Knight’s robber sequence, the interrupted frame resumes with the same pending decision-maker—for example, the affected discarder or the partner considering a trade.
   - Implemented: Knight always records the active player as the resuming player. During another player’s discard it permits a spurious active-player discard submission; during pending trade consent it lets the proposer accept or reject their own offer.
   - Impact: Material phase and consent violation.

### Minor findings

1. **Played progress cards remain in `development_hand`**

   - Canonical fact ID: `CAT-C-PROGRESS-REMOVED`
   - Source evidence: `CATAN22-RULES`, page 4: “Fortschrittskarten kommen aus dem Spiel.”
   - `_play_development` marks the card revealed and records it in `played_development`, but never removes it from `development_hand`. It is no longer playable, so this is primarily a zone/serialization inconsistency.

2. **Unowned Longest Road retains a nonzero synchronized length**

   - Canonical emphasis ID: `CATAN-EMPH-LONGEST-ROAD`
   - Source: `CATAN-V2-CLEAR-RULE-EMPHASIS`, JSON Pointer `/emphasis/0/text`
   - Evidence: “Keep owner and measured length synchronized.”
   - `_recalculate_specials` sets `longest_road_owner = None` after an excluding leading tie but retains `longest_road_length = m`. Scoring is correct, but the exposed award state is not synchronized as emphasized.

### Question

- `returns()` assigns `+1` to the winner and `-1` to every loser. The supplied rules determine the winner but do not define a numeric utility convention. Canonical claims `CAT-C-WIN-ACTIVE` and `CAT-C-WIN-IMMEDIATE` therefore establish terminal identity, not the payoff scale. A human should confirm the intended BoardBench return contract; this is not scored as a contradiction.

## Rule-area coverage

| Rule area | Coverage | Result |
|---|---|---|
| Beginner setup, 3/4 players | Board, pieces, starting resources, bank/deck, robber | Covered |
| Turn order and strict phases | Roll → trade → build; clockwise progression | Covered |
| Production and shortages | Settlements/cities, robber blocking, all-or-none shortage decision | Covered |
| Seven and robbery | Discards, movement, victim selection, blind transfer | Covered; interrupt-resume defect |
| Domestic/maritime trade | Ratios, repetition, positive bilateral bundles | Two major defects |
| Building and piece stock | Costs, connectivity, distance, upgrades, stock | Covered |
| Development cards | Timing, purchase restriction, effects, one-per-turn | Covered; minor removal-state defect |
| Chance and private information | Seeded dice/deck/theft, observations | Trade action leak |
| Longest Road/Largest Army | Thresholds, blocking, ties, transfers | Gameplay covered; minor state mismatch |
| Scoring and terminal state | Active-player immediate victory, VP reveal | Covered |
| Returns | Winner identity mapped consistently | Utility magnitude undecided |

## Needed deterministic scenarios

- Compare trade legal actions for two partner hands with equal public size but different compositions; the action surface must be identical.
- Propose a trade, interrupt with Monopoly or Knight so a promised card becomes unavailable, then attempt acceptance; assert atomic rejection and no negative counts.
- Interrupt another player’s pending discard with Knight; after robbery, assert the same discarder and selection frame resume.
- Interrupt pending partner consent with Knight; assert control returns to that partner, not the proposer.
- Create an interruption-induced leading tie excluding the incumbent; assert owner and exposed award-length state follow the supplement together.
- Play each progress-card type and assert it leaves the development hand while remaining publicly recorded as played.

## Material human questions

- What numeric payoff vector should `returns()` use for a completed multiplayer game?
- Should `longest_road_length` be zero/null whenever the award is unowned, or should a separate global maximum-route field exist?

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