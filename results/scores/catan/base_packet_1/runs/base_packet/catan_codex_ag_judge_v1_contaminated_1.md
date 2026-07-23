Score: **0.58**, confidence: **high**. The module implements most setup, production, trade, building, robber, scoring, and information rules coherently. Its principal weaknesses are concentrated around victory timing: Road Building can crash precisely when it wins, turn-start victory is omitted, and victory-point revelation is not implemented. Public rendering also leaks hidden victory points.

## Findings

### Critical — Road Building victory crashes instead of terminating

- Canonical fact ID: `CAT-D-WIN`
- Evidence type: `human_decision`
- Source ID: `approved_rulefacts.md`
- Stable locator: `§ Approved human decisions`, item 2
- Exact evidence: “Check victory after every completed atomic action or committed subaction; if the active player then has at least ten, terminate immediately. This includes turn start before rolling and the first free road of Road Building.”
- Conflicting code: `apply_action` transition `place_free_road`; `_place_road`; `_victory` ([implementation.py](C:/Users/benti/AppData/Local/Temp/boardbench-catan-judge-AcSZhP/implementation.py:316))
- Expected: If either free road awards Longest Road and brings the active player to ten points, that road placement returns a terminal winning state immediately.
- Implemented: `_place_road` invokes `_victory`, which sets `pending=None`. Control then returns to `place_free_road`, which executes `d["pending"]["remaining"] -= 1`. This dereferences `None` and crashes. The failure occurs whether the winning placement is the first or second free road.

Severity is critical because a specifically adjudicated winning transition fails instead of completing the game.

### Major — Victory is not checked at turn start

- Canonical fact ID: `CAT-D-WIN`
- Evidence type: `human_decision`
- Source ID: `approved_rulefacts.md`
- Stable locator: `§ Approved human decisions`, item 2
- Exact evidence: “This includes turn start before rolling.”
- Conflicting code: `end_turn` and `legal_actions` for phase `roll` ([implementation.py](C:/Users/benti/AppData/Local/Temp/boardbench-catan-judge-AcSZhP/implementation.py:328))
- Expected: After the active seat changes, the new active player must immediately win if they still possess at least ten points.
- Implemented: `end_turn` advances directly to `phase="roll"` without calling `_victory`; `legal_actions` then offers rolling and development cards. A player who acquired ten points while non-active—such as through Longest Road recalculation—must improperly continue the turn before winning.

This is adjudication-dependent, not a contradiction of an independently complete printed timing procedure.

### Major — Hidden victory-point cards are not revealed on victory

- Canonical fact ID: `CAT-D-VP-REVEAL`
- Evidence type: `human_decision`
- Source ID: `approved_rulefacts.md`
- Stable locator: `§ Approved human decisions`, item 8
- Exact evidence: “Victory detection automatically reveals, in development-hand order, only the minimum number of hidden victory-point cards needed to establish ten.”
- Conflicting code: `_victory`, `_score`, and `observation_to_data` ([implementation.py](C:/Users/benti/AppData/Local/Temp/boardbench-catan-judge-AcSZhP/implementation.py:441))
- Expected: Victory detection reveals the minimum necessary hidden victory-point cards, in hand order, and makes those points public.
- Implemented: `_victory` counts every hidden victory-point card but only sets terminal fields. It never marks, moves, or publishes any card. Consequently `public_scores`, which excludes hidden cards, may show the winner below ten even in the terminal state.

This is also an approved human-interface decision rather than a standalone printed-rule contradiction.

### Major — Public rendering exposes concealed victory points before victory

- Canonical fact ID: `CAT-INFO-01`
- Evidence type: `rule_quote`
- Source ID: `CATAN22-RULES`
- Stable locator: PDF p. 4, “Siegpunkte”
- Exact source evidence: “Karten mit Siegpunkten werden grundsätzlich geheim gehalten. Sie werden erst aufgedeckt, wenn ein Spieler insgesamt 10 Siegpunkte erreicht hat.”
- Conflicting code: `render` calls `_score(d, player)` with the default `include_hidden=True` for every player ([implementation.py](C:/Users/benti/AppData/Local/Temp/boardbench-catan-judge-AcSZhP/implementation.py:527))
- Expected: Unrevealed victory-point cards must not affect publicly displayed scores before they establish victory.
- Implemented: The rendered score includes every player’s hidden victory-point cards. Comparing it with the visible board score directly reveals how many hidden victory-point cards each player holds.

This is a contradiction of a clear publisher confidentiality rule.

No supported minor findings were identified.

## Rule-area coverage

| Rule area | Assessment | Notes |
|---|---|---|
| Fixed setup and inventory | Covered | Four seats, illustrated terrain/numbers, starting pieces/resources, bank and deck quantities represented. |
| Turn and phase flow | Partial | Strict roll → trade → build is enforced; turn-start victory is missing. |
| Production | Covered | Settlements/cities, multiple entitlements, robber blocking and desert handled. Bank-shortage behavior is expressly unscored. |
| Domestic/maritime trade | Covered | Active-player-only bilateral legs, atomic commit, positive exchange, harbor rates and city harbor retention represented. |
| Building and stock | Covered | Costs, connectivity, distance rule, city replacement, stock limits represented. |
| Longest Road | Covered | Edge-simple trails, opponent blocking, ties and transfer logic represented. |
| Seven and robber | Covered | Resource-only discard threshold, different destination, eligible victim choice and random resource theft represented. |
| Development cards | Partial | Timing and effects are largely covered; a winning Road Building placement crashes. |
| Largest Army | Covered | Three-card acquisition and strict transfer represented. |
| Private/public information | Partial | Observations mostly hide identities, but `render` leaks hidden victory points. |
| Terminal conditions | Defective | Ordinary active-player wins work, but turn-start timing, Road Building victory, and VP revelation do not. |
| Returns | Undecided interface | Winner `+1`, each loser `-1`; no approved payoff convention establishes whether this is required. |

## Missing deterministic scenarios

- First Road Building placement awards Longest Road and reaches ten.
- Second Road Building placement awards Longest Road and reaches ten.
- A non-active player reaches ten through special-card recalculation, remains at ten, and becomes active.
- Immediate victory after buying one victory-point card.
- Victory with several hidden victory-point cards where only the minimum required cards are revealed in hand order.
- Pre-victory rendering with zero, one, and multiple hidden victory-point cards.
- Public terminal observation showing the revealed winning score at ten or more.
- Road Building with zero, one, and two feasible placements, including exhausted road stock.

## Material questions for a human

- Is `render` intended as a public player-facing view or a privileged adjudicator/debug view? If public, its hidden-point disclosure must change; the player-scoped observation already demonstrates the safer model.
- Must `legal_actions` be observationally pure? When no free road is legal, it calls `_finish_road_building` on the supplied state, so merely requesting actions mutates the game state. The approved rules decide the zero-road result but not this interface behavior.
- What payoff convention should `returns` use? The sources determine the winner but do not determine whether all losers receive `-1`, `0`, or another utility.

```text
score: 0.58
confidence: high
critical_issues: 1
major_issues: 3
minor_issues: 0
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true
```