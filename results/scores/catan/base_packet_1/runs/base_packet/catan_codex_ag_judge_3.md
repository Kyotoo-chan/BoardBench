## Assessment

score: 0.63  
confidence: high

The implementation covers most fixed setup, production, trading, building, robber, development-card, scoring, and privacy rules. However, Road Building has a valid winning-action crash, can exceed physical road stock, and victory/reveal timing is incomplete.

## Findings

### Critical

1. **Winning with a free Road Building road crashes instead of ending the game**

- Canonical fact: `CAT-D-WIN`
- Evidence type: `human_decision`
- Source: `approved_rulefacts.md`, “Approved human decisions,” item 2
- Exact evidence: “Check victory after every completed atomic action or committed subaction… This includes turn start before rolling and the first free road of Road Building.”
- Conflicting transition: `apply_action()` → `place_free_road`; `_place_road()` → `_victory()`
- Implemented behavior: `_victory()` sets `pending = None` upon victory. Control then returns to `place_free_road`, which unconditionally executes `d["pending"]["remaining"] -= 1`, dereferencing `None`.
- Expected behavior: after either free road establishes ten points, the state becomes terminal immediately and no Road Building continuation state is accessed.
- Impact: a fully legal victory path raises an exception rather than producing a terminal winner.

### Major

2. **Road Building can place a second road when the player has no road piece left**

- Canonical facts: `CAT-BUILD-03`, `CAT-D-ROAD-CARD`
- Evidence type: `human_decision`
- Source: `approved_rulefacts.md`, “Approved human decisions,” item 5
- Exact evidence: “Road Building places the maximum feasible number up to two, sequentially. If two are legal and available, both are required; otherwise place exactly the feasible number.”
- Conflicting symbols: `legal_actions()` branch `phase == "road_building"` and `_place_road()`
- Implemented behavior: once Road Building begins, free-road actions are generated solely through `_road_legal()`. Remaining physical stock is not checked. A player starting with one road piece can place one, reach zero, then place another and decrement stock to `-1`.
- Expected behavior: with one road piece available, exactly one free road is placed.
- Impact: violates component limits and can incorrectly award Longest Road or victory.

3. **An incoming active player who already has ten points is not declared the winner**

- Canonical fact: `CAT-D-WIN`
- Evidence type: `human_decision`
- Source: `approved_rulefacts.md`, “Approved human decisions,” item 2
- Exact evidence: “Check victory after every completed atomic action or committed subaction… This includes turn start before rolling.”
- Conflicting transition: `apply_action()` → `end_turn`
- Implemented behavior: `end_turn` advances the active player and enters `roll` without calling `_victory()`. Rolling and ordinary trade transitions also do not check victory.
- Expected behavior: the newly active player is checked before rolling and wins immediately if still at ten or more.
- Impact: a player who gained points while inactive—for example, through Longest Road reassignment—can be forced to continue and may pass through an entire turn without receiving the required win.

4. **Hidden victory-point cards are never minimally revealed when they establish victory**

- Canonical fact: `CAT-D-VP-REVEAL`
- Evidence type: `human_decision`
- Source: `approved_rulefacts.md`, “Approved human decisions,” item 8
- Exact evidence: “Victory detection automatically reveals, in development-hand order, only the minimum number of hidden victory-point cards needed to establish ten.”
- Conflicting symbols: `_score()`, `_victory()`, `observation_to_data()`
- Implemented behavior: `_score()` silently counts every hidden victory-point card, but `_victory()` records no reveal. The cards remain in `development_hand`, while `public_scores` continues to exclude them.
- Expected behavior: reveal only the minimum necessary cards, in hand order, and reflect the established winning score publicly.
- Impact: terminal state can declare a winner while publicly showing fewer than ten points, and required reveal information is absent.

5. **The text renderer discloses concealed victory-point information before victory**

- Canonical fact: `CAT-INFO-01`
- Evidence type: `rule_quote`
- Source: `CATAN22-RULES`, PDF p. 4, “Siegpunkte”
- Exact evidence: “Karten mit Siegpunkten werden grundsätzlich geheim gehalten. Sie werden erst aufgedeckt, wenn ein Spieler insgesamt 10 Siegpunkte erreicht hat.”
- Conflicting symbol: `render()`
- Implemented behavior: `render()` calls `_score()` with its default `include_hidden=True` for every player. Since visible board points and special cards are public, this reveals the number of concealed victory-point cards through the displayed total.
- Expected behavior: public rendering excludes hidden victory-point cards until the required victory reveal.
- Impact: material private-information leakage that can affect player decisions.

### Minor

6. **Querying legal actions can mutate Road Building state**

`legal_actions()` calls `_finish_road_building(d)` directly when no free road is available. Merely inspecting legal actions can therefore consume the subphase and alter the supplied state. This is a localized transition/interface defect, though the approved packet does not explicitly prescribe query purity.

## Rule-area coverage

| Rule area | Status | Notes |
|---|---|---|
| Fixed setup and inventory | Covered | Four seats, illustrated terrain/numbers, initial pieces, hands, bank, deck composition |
| Turn phases | Mostly covered | Strict roll → trade → build; incoming-player victory check missing |
| Production | Covered | Settlements/cities, robber blocking, desert exclusion |
| Domestic/maritime trade | Covered | Active-player legs, atomic commit, ports and rates |
| Building legality and costs | Covered | Connections, distance rule, upgrades, normal stock |
| Longest Road | Covered | Edge-simple traversal, blocking and tie ownership |
| Seven and robber | Covered | Joint discard application, forced move, eligible victim selection, random resource |
| Development cards | Mostly covered | Effects and one-card limit; Road Building stock/terminal defects |
| Largest Army | Covered | Three-card threshold and strict transfer |
| Private information | Partial | Canonical observation hides identities; renderer leaks hidden VP totals |
| Scoring and terminal state | Partial | Normal scoring works; turn-start timing and VP reveal are wrong |
| Returns | Covered | Winner receives `+1`, others `-1` |

## Missing deterministic scenarios

- Road Building with exactly one road piece and at least two graph-legal edges.
- Victory caused by the first free Road Building road.
- Victory caused by the second free Road Building road.
- A non-active player reaches ten through Longest Road reassignment, then becomes active.
- Buying the winning victory-point card and verifying minimal public reveal.
- Winning with multiple hidden victory cards when only some are needed.
- Rendering a player with concealed victory-point cards before victory.
- Calling `legal_actions()` in a Road Building subphase with no feasible road and verifying state immutability.

## Material questions for a human

- Is `render()` contractually public/player-facing? If it is diagnostic-only and access-controlled, its hidden-score output may be downgraded from a rule contradiction to an interface question. `observation_to_data()` itself correctly excludes hidden victory points from public scores.
- No unresolved publisher-rule question remains for the frozen condition; the other findings are decided by the approved facts or human decisions.

score: 0.63
confidence: high
critical_issues: 1
major_issues: 4
minor_issues: 1
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true