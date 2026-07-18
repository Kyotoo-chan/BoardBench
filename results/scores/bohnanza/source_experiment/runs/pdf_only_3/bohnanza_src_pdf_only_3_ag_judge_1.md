score: 0.22  
confidence: high

The module implements several base-game mechanics correctly, but not the selected 129-card Ackerbohne condition. It also materially misimplements phase 4, end-game timing, tie resolution, trading, planting order, harvest availability, private information, and one harvest meter.

## Findings

### Critical

1. Third depletion does not end the game at the required boundary.

- Canonical facts: `END-01`, `END-02`, `END-05`
- Evidence:
  - `rule_quote`; source `RULES`, PDF p.9: “Das Spiel endet, sobald der Nachziehstapel zum dritten Mal leer wird.”
  - `rule_quote`; source `RULES`, PDF p.9: “Sollte dies beim Aufdecken der Karten in der 2. Phase … passieren … spielt ihr die 2. und die 3. Phase noch zu Ende.”
  - `human_decision`; source `RULES`, PDF p.9: “endet, sobald”; approved expectation: third depletion during variant phase 4 is immediately terminal after the emptying draw, before another player draws.
- Conflicting symbols/transitions: `Game._draw`, `Game.apply_action` → `finish_building`, `Game._reveal`
- Expected: depletion is registered when the last card is drawn. In phase 2, phases 2–3 finish and phase 4 is skipped; in phase 4, scoring begins immediately.
- Implemented: `_draw` registers depletion only when a later draw starts with an already-empty deck. If count three is reached inside the phase-4 loop, `finish_building` still advances the active player. The next player can execute phases 1–3 before finalization. A deck emptied by the second reveal is likewise not recognized in phase 2.
- Impact: extra planting, trading, harvesting, and reveals can change the final scores and winner.

2. Ties produce the wrong winner and wrong returns.

- Canonical fact: `END-04`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF p.9
- Exact evidence: “Bei einem Gleichstand gewinnt der Spieler, der im Uhrzeigersinn am weitesten weg vom Startspieler sitzt.”
- Conflicting symbols: `Game._finalize`, `Game.returns`
- Expected: among players tied for most coins, the player with the greatest clockwise distance from the original start player wins.
- Implemented:
  - `winner_order` sorts equal scores by ascending `(p - 0) % players`, favoring the closest seat.
  - `returns` awards `+1` to every player tied for the maximum, ignoring the rulebook tiebreak.
- Impact: the module can report multiple winners or select the opposite tied player.

### Major

3. The selected Ackerbohne deck and its defining field mechanic are absent.

- Canonical facts: `INV-03`, `INV-04`, `ACKER-01`, `ACKER-03`
- Evidence:
  - `rule_quote`; source `RULES`, PDF p.10: “alle Bohnensorten aus dem Grundspiel sowie die Ackerbohnen und die Weinbrandbohnen.”
  - `user_observation`; source `COMPONENTS`, JSON Pointers `/bohnen/9/anzahl_karten` and `/bohnen/11/anzahl_karten`: Weinbrandbohne `22`; Ackerbohne `3`.
  - `rule_quote`; source `RULES`, PDF p.11: “Erntest du ein Feld mit zwei Ackerbohnen, erhältst du ein drittes Bohnenfeld.”
  - `rule_quote`; source `RULES`, PDF p.11: “Erntest du ein Feld mit drei Ackerbohnen, erhältst du wie gewohnt drei Bohnentaler.”
- Conflicting symbols: `BEANS`, `COUNTS`, `METERS`, `initial_state`, `_harvest`, every `range(2)` field loop
- Expected: 129 cards containing the eight base types, 22 Weinbrandbohnen, and three Ackerbohnen; Acker harvests can unlock and subsequently use a persistent third field.
- Implemented: exactly the 104-card base deck, only two fields, no Weinbrand meter, and no Acker rewards or third-field transition.

4. Variant phase 4 draws the wrong number of cards for the wrong players.

- Canonical fact: `P4-01`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF p.10
- Exact evidence: “Anders als im Grundspiel zieht jeder von euch eine Karte vom Nachziehstapel … der aktive Spieler, die Mitspieler folgen im Uhrzeigersinn.”
- Conflicting transition: `apply_action` → `finish_building`
- Expected: every player draws one card, active player first and then clockwise, appending to each respective hand.
- Implemented: the active player alone draws three cards.

5. Legal trades cannot express the permitted quantities and gift direction.

- Canonical facts: `TRADE-04`, `TRADE-05`, `TRADE-07`
- Evidence:
  - `rule_quote`; source `RULES`, PDF p.5: “Ihr dürft mit einer unterschiedlichen Kartenanzahl handeln, z. B. zwei Blaue Bohnen gegen eine Gartenbohne.”
  - `rule_quote`; source `RULES`, PDF p.6: “Beide Spieler müssen dem Handel zustimmen.”
  - `rule_quote`; source `RULES`, PDF p.6: “Als besondere Form des Handels dürft ihr euch auch Bohnenkarten schenken. Der beschenkte Mitspieler muss dem Geschenk aber zustimmen.”
- Conflicting symbols: `legal_actions` → `offer_trade`, `apply_action` → `accept_trade`
- Expected: an atomic consensual offer may contain unequal nonempty quantities, and a participant may give a nonempty gift to the other participant.
- Implemented: every offer transfers exactly one active-player card and requests either zero or one target card. Two-for-one and similar atomic exchanges are impossible, as is an inactive player gifting a card to the active player.

6. Mandatory phase-3 planting order is fixed instead of chosen by each recipient.

- Canonical fact: `P3-02`
- Evidence type: `rule_quote`
- Source: `RULES`, PDF p.7
- Exact evidence: “Jeder darf selbst entscheiden, in welcher Reihenfolge er die neuen Bohnenkarten anbaut.”
- Conflicting symbols: `current_player`, `legal_actions` → `build`, `apply_action` → `plant_incoming`
- Expected: each owner chooses which received or retained card to plant next, including before a necessary harvest.
- Implemented: only `incoming[owner][0]` can be planted. The action chooses a field but cannot choose a card, so acquisition/list order dictates planting and potentially forced harvests.

7. Inactive owners cannot exercise the approved anytime-harvest action.

- Canonical fact: `HARV-01`
- Evidence type: `human_decision`
- Source: `RULES`, PDF p.7
- Exact source evidence: “Du darfst jederzeit im Spiel deine Bohnenfelder abernten, auch wenn du nicht der aktive Spieler bist.”
- Approved boundary: harvesting is allowed between individual steps, but not inside an executing atomic draw or transfer.
- Conflicting symbols: `current_player`, `legal_actions`
- Expected: any owner may harvest a legal field between atomic steps, including during another player’s turn.
- Implemented: harvest actions are generated only for `current_player(s)`, normally the active player or the currently selected incoming-card owner. Other owners receive no harvest action.

8. Opponents’ private hands are systematically exposed.

- Canonical fact: `HAND-03`
- Evidence type: `human_decision`
- Source: `RULES`, PDF p.3
- Exact source evidence: “Die erste verteilte Karte auf deiner Hand ist die vorderste Karte.”
- Approved information decision: the owner sees the complete ordered hand; opponents see only its count unless the owner voluntarily communicates.
- Conflicting symbols: `legal_actions` → `trade`, `render`
- Expected: opponent bean identities and positions remain private.
- Implemented: trade action enumeration includes `(index, bean)` for every card in every target hand, and `render` prints all complete ordered hands.

9. Gartenbohne harvest awards are understated.

- Canonical fact: `GOLD-08`
- Evidence type: `user_observation`
- Source: `COMPONENTS`, JSON Pointer `/bohnen/7/ernte`
- Exact evidence: `2 → 2`, `3 → 3`
- Conflicting symbol: `METERS["Gartenbohne"] = (2, 3, None, None)` as interpreted by `_harvest`
- Expected: one card pays zero, two cards pay two coins, and three or more pay three.
- Implemented: two cards pay one coin and three or more pay two.

### Minor

None.

## Rule-area coverage

| Rule area | Status | Main result |
|---|---|---|
| Setup and inventory | Contradicted | Correct five-card deal, but wrong 104-card condition and no variant beans |
| Hand order | Mostly correct | Front planting and append semantics work; privacy does not |
| Phase 1 planting | Mostly correct | Mandatory first and optional second represented |
| Reveal | Partial | Two cards revealed, but depletion timing is wrong |
| Trading | Contradicted | Consent and lockout represented; quantities, direction, and privacy fail |
| Phase 3 planting | Contradicted | Planting mandatory, but card order is not selectable |
| Phase 4 drawing | Contradicted | Three cards to active instead of one to every player |
| Harvesting | Partial | Protection and most meters work; timing, Garten, and Acker fail |
| Deck recycling | Partial | Reshuffling exists, but depletion is detected too late |
| Terminal scoring | Contradicted | Final harvest exists, but terminal boundary and tie winner are wrong |
| Returns | Contradicted | Nonterminal zeros correct; terminal ties ignore the tiebreak |

## Missing deterministic scenarios

- Assert the initial active deck contains exactly 129 cards before dealing, including 22 Weinbrandbohnen and three Ackerbohnen.
- Exercise one-, two-, and three-card Acker harvests, both before and after field 3 is unlocked.
- Verify phase 4 for four and five players, including clockwise order and one appended card per hand.
- Empty the deck on the first and second reveal card and on each possible phase-4 player draw; verify exact continuation or termination.
- Resolve equal-coin finishes at multiple clockwise distances from the start player.
- Accept a two-for-one trade and an inactive-to-active gift.
- Give a player multiple incoming bean types whose chosen planting order changes the required harvest.
- Harvest an inactive player’s field between two mandatory planting steps.
- Compare per-player observations and legal actions to ensure opponent hand identities are absent.
- Verify Gartenbohne payouts at field sizes one, two, and three.

## Material questions for a human

- Is caller-side seat renumbering intended to represent the chosen start player? The constructor has no start-player parameter, so this convention should be documented if seat 0 is deliberately normalized.
- Is `render` intended as a player-visible observation or only privileged debugging output? Regardless, `legal_actions` independently reveals opponents’ card identities and still requires correction.

```text
score: 0.22
confidence: high
critical_issues: 2
major_issues: 7
minor_issues: 0
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true
```