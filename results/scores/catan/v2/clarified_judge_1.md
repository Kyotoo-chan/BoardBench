score: 0.85  
confidence: high

The module implements most approved setup, production, trading, construction, chance/privacy, development-card, scoring, and source-gap decisions correctly. Two clear-rule failures materially affect legal play and scoring. Overlapping domestic-trade bundles—including returning one of the offered resource type—were not penalized because the approved facts permit them.

## Findings

### Major

1. Development cards cannot be played before rolling.

   - Canonical fact: `CAT-C-DEV-ANYTIME`
   - Evidence type: `rule_quote`
   - Source: `CATAN22-RULES`, PDF page 2
   - Exact evidence: “zu einem beliebigen Zeitpunkt seines Zuges (auch vor dem Würfeln)”
   - Conflicting symbol: `Game.legal_actions`, especially lines 164–176
   - Expected: An eligible Knight or progress card is available during the active player’s pre-roll state, subject to the one-card and purchase-turn restrictions.
   - Implemented: Development actions are injected only for `discard`, `robber_move`, `robber_steal`, `trade`, `trade_offer`, and `build`. In `roll`, the sole action is `roll_dice`.
   - Impact: A material timing option expressly granted by the rules is absent.

2. Building an opponent settlement does not recompute Longest Road.

   - Canonical fact: `CAT-C-LR-OPP-BLOCK`
   - Evidence type: `rule_quote`
   - Source: `CATAN22-ALMANAC`, PDF page 8
   - Exact evidence: “Wird eine Straße durch eine fremde Siedlung unterbrochen”
   - Related facts: `CAT-C-LR-TRANSFER`, `CAT-C-LR-HOLDER-TIE`, `CAT-C-LR-VACANT-TIE`, `CAT-C-SCORE-AWARDS`, `CAT-C-WIN-IMMEDIATE`
   - Conflicting transition: `Game.apply_action` → `build_settlement`
   - Expected: Placing a settlement on an opponent’s road junction immediately interrupts that route and recalculates Longest Road ownership, its two points, and any resulting active-player victory.
   - Implemented: `_update_longest(d)` is called after road placement but not after `build_settlement`; the stored owner and length can remain stale indefinitely.
   - Impact: Special-card ownership, visible scores, and potentially the winner can be wrong.

### Minor

3. Played progress cards remain represented in the player’s development hand.

   - Canonical fact: `CAT-C-PROGRESS-REMOVED`
   - Evidence type: `rule_quote`
   - Source: `CATAN22-RULES`, PDF page 4
   - Exact evidence: “Fortschrittskarten kommen aus dem Spiel.”
   - Conflicting symbol: `Game._play_dev`
   - Expected: A played progress card leaves the hand and game.
   - Implemented: The card is marked `revealed=True` and copied into `bank.played_development`, but its original object remains in `development_hand`.
   - Impact: Replay is correctly prevented, so this is primarily a state-zone and observation inconsistency.

### Question

4. Terminal return values lack an approved source convention.

   - `Game.returns` produces `+1` for the winner and `-1` for every loser, with zero before termination.
   - None of the assigned publisher, fact, claim, or clarification sources defines utility/payoff encoding.
   - Human decision needed: confirm whether BoardBench expects this vector, zero-sum normalization, winner-only rewards, or another convention. This is not scored as a contradiction.

## Rule-area coverage

| Rule area | Result | Notes |
|---|---|---|
| Beginner setup, 3/4 players | Pass | Fixed board, red removal, pieces, initial resources, bank, deck and robber represented |
| Turn order and strict phases | Partial | Roll → trade → build works; pre-roll development play is absent |
| Production and shortages | Pass | Settlement/city production, robber blocking and approved all-or-none shortage rule |
| Domestic/maritime trade | Pass | Active-player restriction, consent, finite bounds, atomic transfer, harbors and different receive type |
| Building legality and stock | Pass | Costs, road connectivity, settlement distance and city replacement |
| Longest Road | Partial | Trail calculation and ties align with approved decision; settlement interruption is not recomputed |
| Seven and robbery | Pass | Escrowed discards, movement, victim selection and blind theft |
| Development cards | Partial | Effects and limits largely correct; pre-roll timing absent and progress cards remain in hand state |
| Privacy/chance | Pass | Private identities, public aggregates and seeded dice/deck/theft represented |
| Scoring and victory | Partial | Normal scoring and immediate checks work; stale Longest Road can corrupt scoring/winner |
| Serialization/returns | Question | Serialization is present; payoff convention is source-undecided |

## Missing deterministic scenarios

- Eligible Knight, Road Building, Year of Plenty, and Monopoly actions before rolling; resolution must return to `roll`.
- Pre-roll development restrictions: one card per turn and no same-turn purchased card.
- Settlement placement splitting an incumbent’s road, including retained-holder tie, vacant tie, and transfer cases.
- Settlement-triggered Longest Road change that immediately gives or removes the active player’s tenth point.
- Played progress card absent from the private development hand and present only in an appropriate removed/history zone.
- Terminal and nonterminal return-vector assertions once the human confirms the payoff convention.

## Material questions for a human

- What payoff vector must `returns` expose? The assigned rule sources establish the winner but not utility encoding.
- Should played progress cards be physically removed from `development_hand`, or is a revealed historical record there acceptable to downstream consumers? The printed rule supports actual removal.

```text
score: 0.85
confidence: high
critical_issues: 0
major_issues: 2
minor_issues: 1
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```