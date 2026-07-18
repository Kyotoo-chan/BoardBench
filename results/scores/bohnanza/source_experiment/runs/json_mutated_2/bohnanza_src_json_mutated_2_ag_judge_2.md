score: 0.34  
confidence: high

The module models the basic four-phase loop and most inventory correctly, but eight material deviations affect scoring, legal trades, planting choice, deck composition, information boundaries, and game-end timing. I found no common crash or unavoidable deadlock, so none rises to `critical`.

## Findings

### Major

1. **Weinbrandbohne rewards use the wrong Bohnometer**

   - Fact: `GOLD-09`
   - Evidence type: `user_observation`
   - Source: `COMPONENTS`, `/bohnen/9/ernte`
   - Exact evidence: `4→1, 7→2, 9→3, 11→4`
   - Code: `BOHNOMETER["Weinbrandbohne"]`
   - Expected: 0 below four; then 1/2/3/4 coins at 4/7/9/11+.
   - Implemented: 1/2/3/4 coins at 2/4/6/8+.
   - Impact: frequent overpayment directly changes scores and winners.

2. **Pile depletion is recorded one draw too late**

   - Facts: `DECK-01`, `END-01`, `END-02`, `END-05`
   - Evidence types: `human_decision` for `DECK-01`/`END-05`; `rule_quote` for `END-01`/`END-02`
   - Source: `RULES`, PDF p.9
   - Exact evidence:
     - “Ziehst du die letzte Karte vom Nachziehstapel, dann mische die Karten des Ablagestapels.”
     - “Das Spiel endet, sobald der Nachziehstapel zum dritten Mal leer wird.”
     - “beim Aufdecken … spielt ihr die 2. und die 3. Phase noch zu Ende”
   - Code: `_take_card`, especially lines 156–165; `draw_one`
   - Expected: taking the final card immediately counts a depletion. The first two depletions immediately reshuffle the then-current discard; the third observes the phase-specific terminal boundary.
   - Implemented: depletion is counted only on the next call made while `deck` is already empty.
   - Impact: harvest discards created after the real depletion can enter a reshuffle that should already have occurred. Third depletion can also leave an extra `draw_one` decision before termination.

3. **Unequal-card-count trades cannot be expressed**

   - Fact: `TRADE-04`
   - Evidence type: `rule_quote`
   - Source: `RULES`, PDF p.5
   - Exact evidence: “Ihr dürft mit einer unterschiedlichen Kartenanzahl handeln”
   - Code: `legal_actions` creates only a single offered card and a single wanted card; `accept_offer` transfers at most one each.
   - Expected: consensual exchanges such as two cards for one are legal.
   - Implemented: only one-for-one trades and active-player gifts are available.
   - Impact: a material portion of the legal negotiation space is absent.

4. **A card received in a trade can be traded again**

   - Fact: `TRADE-03`
   - Evidence type: `rule_quote`
   - Source: `RULES`, PDF p.5
   - Exact evidence: “Mit Karten, die ihr nach einem Handel bekommt, dürft ihr nicht weiterhandeln.”
   - Code: `accept_offer` appends the received target card to `s.table` with the active player as owner; `legal_actions` subsequently includes every active-owned table card as a trade source.
   - Expected: received cards remain outside the hand and cannot be traded again.
   - Implemented: the active player can immediately offer a received card in another trade or gift.
   - Impact: permits explicitly forbidden trade chains.

5. **Mandatory table-card planting order is forced**

   - Fact: `P3-02`
   - Evidence type: `rule_quote`
   - Source: `RULES`, PDF p.7
   - Exact evidence: “Jeder darf selbst entscheiden, in welcher Reihenfolge er die neuen Bohnenkarten anbaut.”
   - Code: `legal_actions`, `plant_table` branch, selects only `owned[0]`.
   - Expected: the recipient chooses any pending received/revealed card to plant next.
   - Implemented: only the first table card owned by that player may be planted.
   - Impact: order affects which fields must be harvested and therefore coin income.

6. **Only the current decision actor may harvest**

   - Fact: `HARV-01`
   - Evidence type: `human_decision`
   - Source: `RULES`, PDF p.7
   - Exact evidence: “Du darfst jederzeit im Spiel deine Bohnenfelder abernten, auch wenn du nicht der aktive Spieler bist.”
   - Approved decision: an owner may harvest between individual game steps, including during another player’s turn.
   - Code: `legal_actions` sets `p = s.actor` and generates harvest actions only for that player.
   - Expected: every player with a legally harvestable field can harvest at permitted step boundaries.
   - Implemented: inactive non-actors cannot harvest; during a pending response, only the responding player can do so.
   - Impact: legal timing decisions that can change later planting and harvest outcomes are unavailable.
   - Provenance note: the exact atomic-step boundary is adjudication-dependent, but the implementation is narrower even at ordinary decision boundaries.

7. **Three harvested Ackerbohnen are simultaneously scored and recycled**

   - Fact: `ACKER-03`
   - Evidence type: `human_decision`
   - Source: `RULES`, PDF p.11
   - Exact evidence: “Erntest du ein Feld mit drei Ackerbohnen, erhältst du wie gewohnt drei Bohnentaler.”
   - Approved decision: exactly three become three coins and do not unlock field three.
   - Code: `_harvest` gives three coins but also executes `s.discard.extend([bean] * n)`.
   - Expected: the three cards become the three coin cards and leave the bean-card circulation.
   - Implemented: three abstract coins are awarded while all three physical Ackerbohnen also enter the discard and can be drawn again.
   - Impact: duplicates value, violates the three-card inventory, and enables repeated Ackerbohne rewards.
   - Provenance note: the “exactly three become three coins” representation is an approved human decision.

8. **Private-information observations are not implemented**

   - Fact: `HAND-03` and the approved executable observation convention
   - Evidence type: `human_decision`
   - Source: `RULES`, PDF p.3
   - Exact evidence: “Die erste verteilte Karte auf deiner Hand ist die vorderste Karte. Sie ist komplett sichtbar.”
   - Approved decision: each player observes their own complete ordered hand and only opponents’ hand counts.
   - Code: no player-specific observation method; `GameState.hands` exposes every hand, while `render` shows only counts even to the owner.
   - Expected: a player-scoped observation with own ordered cards and opponent counts.
   - Implemented: consumers either access all private hands through state or receive no hand identities through `render`.
   - Impact: the required private-information boundary cannot be enforced.

### Minor

1. **An empty hand takes two phase-advance actions**

   - Fact: `P1-04`
   - Source: `RULES`, PDF p.5
   - Evidence: “Hast du zu Beginn der 1. Phase keine Karten auf der Hand, gehst du gleich zur 2. Phase über.”
   - Code: `advance_plant` moves `plant_first → plant_second`; another `advance_plant` is required to reach `reveal`.
   - Expected: direct transition to phase 2.
   - Impact: adds a redundant deterministic step but does not normally alter outcome.

## Rule-area coverage

| Area | Status | Notes |
|---|---|---|
| Setup/inventory | Mostly correct | 4–5 players, 129-card composition, five-card hands, two fields |
| Ordered hands | Partial | Planting preserves order; observation boundary absent |
| Turn phases | Mostly correct | Four phases represented; empty-hand skip has an extra step |
| Phase-1 planting | Correct core | Mandatory first and optional second; forced harvest is possible |
| Reveal/trading | Material defects | No unequal trades; received cards can be re-traded |
| Phase-3 planting | Material defect | Pending-card order is forced |
| Harvest legality | Material defect | Non-actor harvesting unavailable |
| Harvest rewards | Material defects | Weinbrand meter wrong; three Ackerbohnen recycled |
| Draw/reshuffle | Material defect | Depletion timing is delayed |
| End/scoring | Partial | Final harvest and tie-break exist; terminal boundary is delayed |
| Returns | Correct | Zero nonterminal, winner-based terminal returns |
| No elimination | Correct | No elimination mechanism present |

## Missing deterministic scenarios

- Weinbrand harvests at 2, 4, 6, 7, 8, 9, and 11 cards.
- A two-for-one consensual trade.
- Active player attempting to re-trade a card just received.
- A player choosing between two differently typed pending table cards whose planting orders force different harvests.
- An inactive, non-responding player harvesting between another player’s actions.
- Harvesting exactly three Ackerbohnen, followed by inspection of discard, deck, and total card conservation.
- First or second depletion caused by the last reveal/draw, with cards harvested afterward; verify those later discards are not included in the already-completed reshuffle.
- Third depletion on reveal card one versus reveal card two.
- Third depletion during a phase-4 draw, verifying no later player gets a draw action.
- Player-scoped observations verifying own ordered hand and opponent counts only.
- Empty hand at phase-1 entry transitioning directly to reveal.
- Tie scoring with a nonzero configured start-player seat.

## Material questions for a human

- Is seat 0 intentionally treated as the chosen start player by canonical seat relabeling, or must callers be able to configure a different `start_player`? The approved fact says configured/chosen, while the implementation fixes it to zero.
- Is `GameState` intended to be privileged internal state? If not, direct access to `hands` itself leaks every player’s private cards; if so, a separate player-observation API is still required.
- Should pure gifts from an inactive player to the active player be explicitly representable? The supplied text says players may give cards to each other with recipient consent, while this implementation only initiates gifts from the active player.

score: 0.34
confidence: high
critical_issues: 0
major_issues: 8
minor_issues: 1
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true