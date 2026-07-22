## Assessment

`score: 0.40` — `confidence: high`

The implementation captures most setup, planting, harvesting, payout, recycling, privacy, and phase-three rules. However, terminal scoring can select the wrong winner in every completed game, and exhaustive trade enumeration is likely to make ordinary longer games impractical. A further transition defect permits callers to bypass the required turn phases.

## Findings

### Critical — Mandatory final harvest is omitted from scoring

- Canonical fact: `BASE-SCORE-01`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-RULES`, PDF page 2
- Exact evidence: “Jede Person erntet noch ihre Bohnenfelder und erhält gegebenenfalls dafür Bohnentaler. Die Karten auf der Hand zählen nicht mehr. Anschließend zählen alle ihre Karten in ihrem jeweiligen Talerstapel.”
- Conflicting code: `returns`; terminal transition in `_draw_one`
- Expected: When the third depletion terminates the game, every field is harvested using its Bohnometer. Those proceeds determine final totals; hands are ignored.
- Implemented: `_draw_one` marks the state terminal immediately, while `returns` compares only existing `players[*]["coins"]`. It neither harvests nor notionally scores cards remaining on fields.
- Impact: Common, fundamental winner error. A player whose unharvested fields would produce the most coins can lose incorrectly.

### Critical — Trade action enumeration becomes exponentially unmanageable

- Canonical fact: `CLAR-TRADE-01`
- Evidence type: `human_decision`
- Source: `BOHN-BASE-CLARIFY`, JSON Pointer `/clarifications/2/text`
- Exact evidence: “Jede endliche Anzahl zulässiger eigener Hand- oder Aufdeckkarten darf gegen jede endliche Anzahl zulässiger Handkarten der anderen beteiligten Person angeboten werden, begrenzt nur durch vorhandene Karten und beiderseitige Zustimmung.”
- Conflicting code: `legal_actions`, especially `offered_sets` and its nested requested-card combination loops
- Expected: Arbitrary finite legal bundles, including 1-for-2 and 3-for-1, must be representable while the game remains operable.
- Implemented: The method eagerly materializes every nonempty subset of the active player’s eligible cards, then pairs each with every nonempty subset of every opponent’s hand. This is approximately `O(2^(m+n))` proposals per opponent, before accounting for object/JSON construction.
- Impact: Hands legally grow when players plant only the mandatory card and draw three. Moderate hand sizes therefore produce millions of actions, with larger hands risking severe memory exhaustion or an apparent deadlock. The core game cannot be expected to complete reliably under legal play.

### Major — `apply_action` permits phase-skipping and malformed transitions

- Canonical fact: `BASE-TURN-01`
- Evidence type: `rule_quote`
- Source: `BOHN-BASE-RULES`, PDF page 1
- Exact evidence: “Als aktive Person führst du nacheinander vier Phasen durch: 1. Bohnenkarten von der Hand anbauen 2. Bohnenkarten aufdecken und handeln 3. Gehandelte und aufgedeckte Bohnenkarten anbauen 4. Bohnenkarten nachziehen.”
- Conflicting code: `apply_action`, together with public construction paths `action_from_data` and `name_to_action`
- Expected: Actions must obey the current phase, acting player, legal source, and legal target; an illegal transition should be rejected.
- Implemented: `apply_action` checks only terminal status and whether the action type is known. For example, a syntactically valid `draw` submitted during `plant_first` draws cards and advances to the next player, skipping planting, reveal/trade, and phase three. `trade_accept` without a pending proposal can instead crash. Actor/argument consistency is likewise not enforced.
- Impact: Material action and phase rules are bypassable through the module’s public action interface.

### Question — Direction of gifts

- Relevant fact: `BASE-TRADE-07`
- Publisher evidence, page 2: “Ihr dürft euch auch Bohnenkarten schenken. Die beschenkte Person muss dem Geschenk aber zustimmen.”
- Implementation only generates gifts from the active player to another player: every gift has a nonempty `offered` bundle and an empty `requested` bundle.
- The supplied text does not explicitly settle whether another player may give a card to the active player during their bilateral negotiation. This should not be penalized without a human decision.

### Question — Visibility/configurability of the Start-card holder

The state records `start_player`, but observations omit it and setup always assigns player 0. The rulebook says the Start card remains with the initial player and later controls tie-breaking. The packet does not explicitly say whether seat 0 is an accepted interface convention or whether the starting player must be selectable/publicly observable.

## Rule-area coverage

| Rule area | Status | Notes |
|---|---|---|
| Inventory and player counts | Covered | Correct 104-card distribution; 3–5 players |
| Setup and field counts | Mostly covered | Correct hands and 3-player/2-field split; start fixed to player 0 |
| Immutable hand order | Covered | Front planting and ordered appends are represented |
| Phase-one planting | Covered | Mandatory first, optional second, no third, empty-hand skip |
| Forced harvest and field typing | Covered | Legal action generation supplies harvest opportunities |
| Reveal and bilateral trade | Partial | Main restrictions and consent work; exponential enumeration |
| Gifts | Ambiguous | Only active-to-partner gifts represented |
| Phase-three planting | Covered | Every affected player acts and chooses card order |
| Phase-four draw | Covered | Three sequential draws and clockwise turn advance |
| Harvesting and payouts | Covered | Off-turn harvest, singleton protection, zero payout, curves |
| Recycling and third depletion | Covered | Includes clarified immediate/phase-two distinction |
| Final scoring | Contradicted | Mandatory final field harvest absent |
| Tie-break | Covered | Clockwise-farthest tied player is selected |
| Private information | Covered | Opponent hands reduced to sizes; privacy is non-scored |
| Transition integrity | Contradicted | Public action application does not enforce legality |

## Missing deterministic scenarios

- Third depletion with unharvested fields whose payouts change the winner.
- Final harvest producing a tie, followed by the Start-card tie-break.
- Third depletion on each of the first, second, and third phase-four draws.
- Third depletion on the first versus second phase-two reveal, followed by complete phase-three planting.
- Trade generation with steadily growing 10-, 15-, and 20-card hands, including a bounded-time/memory expectation.
- Submission of every action type in the wrong phase, including mismatched actors and stale card references.
- Accepted and rejected gifts in both possible directions, if a human approves both directions.
- Observation of the Start-card holder from a mid-game serialized state.

## Material questions for a human

1. May a non-active participant gift cards to the active player during their bilateral negotiation?
2. Is player 0 an accepted fixed starting-player convention, or must setup allow the start player to be selected?
3. Must a standalone observation explicitly identify the Start-card holder?
4. Does the module contract require `apply_action` to reject actions outside `legal_actions`? The current public parsing/application API strongly suggests it should, but the allowed packet does not contain that contract.

```text
score: 0.40
confidence: high
critical_issues: 2
major_issues: 1
minor_issues: 0
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```