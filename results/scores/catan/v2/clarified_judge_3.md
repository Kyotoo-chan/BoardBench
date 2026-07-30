score: 0.84  
confidence: high

The module implements most setup, economy, robber, privacy, scoring, and terminal rules correctly. Two material defects affect legal timing and the Longest Road award; neither appears to make ordinary games unplayable.

## Findings

### Major

1. Development cards cannot be played before rolling

- Canonical fact: `CAT-C-DEV-ANYTIME`
- Evidence type: `rule_quote`
- Source: `CATAN22-RULES`, PDF p.2
- Exact evidence: “zu einem beliebigen Zeitpunkt seines Zuges (auch vor dem Würfeln)”
- Conflicting code: `Game.legal_actions()`, especially the development-card phase whitelist and `phase == "roll"` branch.
- Expected: An eligible Knight or progress card can be played at a permitted point before the active player rolls.
- Implemented: Development actions are generated only during `discard`, `robber_move`, `robber_steal`, `trade`, `trade_offer`, and `build`. During `roll`, the sole action is `roll_dice`.
- Impact: Material timing options are absent. In particular, a pre-production Knight robber move is impossible.

2. Building an opponent settlement does not recompute Longest Road

- Canonical facts: `CAT-C-LR-OPP-BLOCK`, `CAT-C-LR-TRANSFER`, `CAT-C-LR-HOLDER-TIE`, `CAT-C-LR-VACANT-TIE`
- Evidence type: `rule_quote`
- Source: `CATAN22-ALMANAC`, PDF p.8
- Exact evidence: “Eine Handelsstraße kann für die Zählung des längsten Straßenzugs unterbrochen werden, wenn ein anderer Spieler eine Siedlung auf einer freien Kreuzung der Handelsstraße errichtet!” The same section specifies incumbent-retention and vacant-card outcomes for resulting ties.
- Conflicting code: `Game.apply_action()` transition `build_settlement`; `Game._update_longest()`.
- Expected: Immediately after a settlement is placed through an opponent’s road network, route lengths and ownership must be recomputed, including the printed tie rules and any resulting score/victory change.
- Implemented: `_update_longest()` is called after road placement only. `build_settlement` places and pays for the settlement without recalculating the award.
- Impact: Longest Road ownership and two victory points can remain stale, potentially producing a wrong winner or delaying a valid win.

### Minor

3. Played progress cards remain represented in the player’s development hand

- Canonical fact: `CAT-C-PROGRESS-REMOVED`
- Evidence type: `rule_quote`
- Source: `CATAN22-RULES`, PDF p.4
- Exact evidence: “Danach wird die Karte aus dem Spiel entfernt.”
- Conflicting code: `Game._play_dev()`.
- Expected: A played Road Building, Year of Plenty, or Monopoly card leaves the player’s hand and the game.
- Implemented: The card remains in `development_hand` with `revealed=True` and is additionally copied into `bank.played_development`.
- Impact: Replay is correctly prevented, so this is principally a zone/conservation and observation-model error rather than a core-flow defect.

## Rule-area coverage

| Rule area | Assessment |
|---|---|
| Illustrated 3/4-player setup and inventory | Covered |
| Oldest player and clockwise turns | Covered, with seat 0 declared oldest |
| Strict roll → trade → build flow | Covered |
| Production and bank shortages | Covered |
| Seven, discard escrow, robber and blind theft | Covered |
| Domestic and maritime trade | Covered |
| Costs, stock, road/settlement/city legality | Covered |
| Development purchase and effects | Partial: pre-roll timing missing |
| Longest Road | Partial: road graph calculation works, but settlement interruption is not applied |
| Largest Army | Covered |
| Private resources/development information | Covered |
| Scoring and immediate active-player victory | Covered except consequences of stale Longest Road |
| Terminal state and returns | Covered |

## Missing deterministic scenarios

- Give the active player each eligible non-VP development-card type at the start of `roll`; verify the card action is available before `roll_dice`.
- Place an opponent settlement in the middle of the Longest Road holder’s route and verify:
  - unique transfer,
  - incumbent-leading tie,
  - tie excluding the incumbent,
  - loss below five.
- Make that settlement interruption change the active player’s score to ten and verify immediate termination with the correct winner.
- Play each progress-card type and assert that it leaves the owning development hand while remaining observable only through an appropriate public history/removed-card representation.
- Snapshot the complete initial 3-player and 4-player beginner states, including board, harbors, pieces, starting resources, bank totals, deck composition, and removed red pieces.

## Material questions for a human

- Is constructor seat 0 intentionally the externally designated oldest player, or should callers be able to supply the oldest seat? The publisher source does not define a digital age-input protocol.
- Is `bank.played_development` intended as a non-owning audit history? If so, the state contract should distinguish that history from physical card ownership and remove played progress cards from `development_hand`.

Neither question is needed to adjudicate the two clear printed-rule contradictions above.

score: 0.84
confidence: high
critical_issues: 0
major_issues: 2
minor_issues: 1
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true