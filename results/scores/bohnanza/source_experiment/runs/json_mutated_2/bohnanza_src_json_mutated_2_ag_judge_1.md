## Assessment

score: 0.41  
confidence: high

The implementation captures the main four-phase loop, ordered hands, field compatibility, most bean counts, normal Bohnometers, basic harvesting, final scoring, and tie-breaking. However, one depletion bug can extend play past the required endpoint and change the winner. Eight additional material contradictions affect reshuffling, harvesting access, trading, planting order, private information, and scoring.

## Findings

### Critical

1. Third depletion can permit an extra planting phase and change final scores

- Canonical fact ID: `END-05`
- Evidence type: `human_decision`
- Source: `RULES`, PDF page 9
- Exact evidence: “Das Spiel endet, sobald der Nachziehstapel zum dritten Mal leer wird.”
- Conflicting code: `Game._take_card()` and the `draw_one` transition in `Game.apply_action()`.
- Expected: During variant phase 4, the draw that empties the deck for the third time ends the game immediately; no later player draws and no subsequent turn begins.
- Implemented: `_take_card()` increments `empty_count` only when a draw begins with an already-empty deck. Popping the final card does not register depletion. If the last player in `draw_order` takes that card, the implementation starts the next turn at `plant_first`. That player can plant cards and alter final harvest income before the next attempted draw notices the empty deck.
- Impact: Play can continue beyond the required endpoint, potentially producing the wrong winner.

### Major

2. First and second reshuffles are deferred and can include later discards

- Canonical fact ID: `DECK-01`
- Evidence type: `human_decision`
- Source: `RULES`, PDF page 9
- Exact evidence: “Ziehst du die letzte Karte vom Nachziehstapel, dann mische die Karten des Ablagestapels.”
- Conflicting code: `Game._take_card()`.
- Expected: Drawing the last card registers depletion and immediately turns the then-current discard pile into the new shuffled draw pile.
- Implemented: Reshuffling occurs only on the next attempted draw. Harvests between those events can add cards to `discard`, causing cards discarded after depletion to enter the reshuffle incorrectly.
- Impact: Materially changes deck composition and chance outcomes.

3. Non-acting owners cannot harvest at most permitted timing points

- Canonical fact ID: `HARV-01`
- Evidence type: `human_decision`
- Source: `RULES`, PDF page 7
- Exact evidence: “Du darfst jederzeit im Spiel deine Bohnenfelder abernten, auch wenn du nicht der aktive Spieler bist.”
- Conflicting code: `Game.legal_actions()`, specifically `p = s.actor` and the harvest actions generated only for `p`.
- Expected: Any owner may harvest between individual game steps, including during another player’s turn.
- Implemented: Only the player currently represented by `state.actor` can harvest. Other owners receive no harvest action.
- Impact: Removes material legal actions and can force players to miss profitable or protective harvest timing.

4. Unequal multi-card trades cannot be proposed atomically

- Canonical fact ID: `TRADE-04`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 5
- Exact evidence: “Ihr dürft mit einer unterschiedlichen Kartenanzahl handeln, z. B. zwei Blaue Bohnen gegen eine Gartenbohne.”
- Conflicting code: `Game.legal_actions()` trade generation and `accept_offer`.
- Expected: Trades such as two cards for one card are legal as one consensual, atomic exchange.
- Implemented: `offer_trade` always contains exactly one source card and exactly one target card; `offer_gift` contains one card for none. Several single-card offers are not equivalent to one atomic unequal trade.
- Impact: Excludes a material class of legal negotiations.

5. The active player can trade away a card just received in a prior trade

- Canonical fact ID: `TRADE-03`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 5
- Exact evidence: “Mit Karten, die ihr nach einem Handel bekommt, dürft ihr nicht weiterhandeln.”
- Conflicting code: `accept_offer()` appends a received card to `s.table` under the active player, while `legal_actions()` includes every active-owned table card in later trade sources.
- Expected: A received card waits outside the hand and cannot be traded again.
- Implemented: Cards received by the active player become eligible sources for subsequent gifts or trades during the same phase.
- Impact: Permits explicitly forbidden card circulation.

6. Mandatory table-card planting order is forced

- Canonical fact ID: `P3-02`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF page 7
- Exact evidence: “Jeder darf selbst entscheiden, in welcher Reihenfolge er die neuen Bohnenkarten anbaut.”
- Conflicting code: `Game.legal_actions()` in `stage == "plant_table"`, particularly `idx, bean = owned[0]`.
- Expected: Each recipient chooses which received or retained revealed card to plant next.
- Implemented: Only the first owned table entry may be planted.
- Impact: Planting order can determine which field must be harvested and therefore affect income and field state.

7. Three harvested Ackerbohnen are both scored and recycled

- Canonical fact ID: `ACKER-03`
- Evidence type: `human_decision`
- Source: `RULES`, PDF page 11
- Exact evidence: “Erntest du ein Feld mit drei Ackerbohnen, erhältst du wie gewohnt drei Bohnentaler.”
- Conflicting code: `Game._harvest()` Ackerbohne branch.
- Expected: Exactly three Ackerbohnen become three coin cards and leave the circulating bean deck.
- Implemented: The player gains three integer coins, but all three Ackerbohnen are also appended to `discard`. They can later be reshuffled and harvested again.
- Impact: Duplicates value and violates the finite-card economy.

8. Weinbrandbohne Bohnometer thresholds are wrong

- Canonical fact ID: `GOLD-09`
- Evidence type: `user_observation`
- Source: `COMPONENTS`, JSON Pointer `/bohnen/9/ernte`
- Exact evidence: `4→1, 7→2, 9→3, 11→4`
- Conflicting code: `BOHNOMETER["Weinbrandbohne"]`.
- Expected: Zero below four; then 1/2/3/4 coins at 4/7/9/11 or more cards.
- Implemented: 1/2/3/4 coins at 2/4/6/8.
- Impact: A common included bean type pays substantially too early and too much.

9. Private-hand observations are not enforced or exposed correctly

- Canonical fact ID: `HAND-03`
- Evidence type: `human_decision`
- Source: `RULES`, PDF page 3
- Exact evidence: “Die erste verteilte Karte auf deiner Hand ist die vorderste Karte.”
- Approved expectation: An owner sees their complete ordered hand; opponents see only its count.
- Conflicting code: Public `GameState.hands` and `Game.render()`.
- Expected: Player-relative observations expose the observer’s ordered hand and only opponents’ hand counts.
- Implemented: The state object exposes every complete hand to any caller, while `render()` exposes only counts and cannot show the observer their own hand. There is no player-relative observation method.
- Impact: The documented private-information boundary is absent.
- Provenance note: This is an approved human decision, not an explicit printed secrecy sentence.

### Minor

10. An empty hand requires two phase-advance actions

- Canonical fact ID: `P1-04`
- Source: `RULES`, PDF page 5
- Evidence: “Hast du zu Beginn der 1. Phase keine Karten auf der Hand, gehst du gleich zur 2. Phase über.”
- Conflicting transition: `advance_plant` moves `plant_first → plant_second`, requiring another `advance_plant` before `reveal`.
- Expected: Skip phase 1 directly.
- Implemented: Passes through an unnecessary second-plant decision state.
- Impact: Extra transition without an apparent scoring consequence.

## Rule-area coverage

| Area | Status | Notes |
|---|---|---|
| Setup and inventory | Mostly correct | 4–5 players, 129-card deck, five ordered cards, and two initial fields are correct. |
| Start player | Question | Player 0 is fixed; no explicit configuration API exists. |
| Phase order | Mostly correct | Four phases are represented; empty-hand skip has an extra transition. |
| Hand planting | Correct | Mandatory first, optional second, no third; forced harvest can be selected. |
| Reveal | Mostly correct | Two public cards represented, but depletion detection is delayed. |
| Trading | Material defects | No atomic unequal trades; received active-player cards can be retraded. |
| Mandatory planting | Material defect | All cards must be planted, but their order is forced. |
| Variant draw | Correct except depletion | One draw per player clockwise and append-to-hand are implemented. |
| Harvesting | Material defects | Protection rule works; non-actor timing is absent. |
| Bohnometers | Material defect | Weinbrand thresholds are wrong; other listed normal thresholds match. |
| Ackerbohne | Material defect | Field unlock works; three-card coin harvest recycles the scoring cards. |
| Private information | Material defect | No player-relative observation boundary. |
| Terminal and returns | Material defect | Final harvest and tie-break work, but third depletion may be detected too late. |
| Elimination | Correct | No elimination mechanism. |

## Missing deterministic scenarios

- Third depletion caused by the last player’s phase-4 draw, proving that no next `plant_first` state occurs.
- First or second depletion on the last owed draw, followed by a harvest, proving that later discards do not enter the already-required reshuffle.
- Third depletion on either the first or second phase-2 reveal, followed by completion of phases 2 and 3 only.
- A non-actor harvesting during another player’s planting, trading, and mandatory-planting steps.
- Atomic two-for-one and one-for-two accepted trades.
- Attempt to re-offer a card the active player just received.
- Two differently ordered mandatory cards where planting order changes the forced-harvest outcome.
- Weinbrand harvests at 2, 4, 7, 9, and 11 cards.
- Three-Acker harvest followed by reshuffle, confirming those three cards cannot re-enter play.
- Player-relative observations confirming own ordered hand and opponent counts only.
- Empty-hand phase-1 transition directly to reveal.
- Tie scoring with a nonzero configured start-player seat.

## Material questions for a human

- Is fixed seat 0 intended to count as the engine’s configured start player, or must callers be able to choose a start-player seat? The approved fact permits a configured/chosen player, but the intended API is not specified.
- What player-relative observation entry point is expected by the surrounding framework? The approved visibility policy is decided, but this isolated module defines no observation interface.

score: 0.41
confidence: high
critical_issues: 1
major_issues: 8
minor_issues: 1
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true