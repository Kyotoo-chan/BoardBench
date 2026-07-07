### 1. Score

score: 0.55  
confidence: medium  

The implementation is playable and covers many core Catan mechanisms: dice chance, resource production, building costs, robber/discard flow, development-card timing, hidden hands, and terminal VP logic. However, it is not benchmark-ready against the provided rulebook because it invents the board/setup/harbors/dev deck, omits player-to-player trading, and implements Fortschritt cards as no-ops. Some setup issues remain uncertain because the packet text references page-1 figures whose exact graph/layout is not available as structured text.

### 2. Top findings

1. **severity: major**  
   **evidence:** Rulebook requires the beginner setup “gemäß der Abbildung auf Seite 1”; code states it uses a deterministic “abstract” 19-hex board and invented harbor positions.  
   **why it matters:** Board topology, starting positions, legal roads/settlements, harbor trades, and yield scenarios all depend on the exact setup.  
   **suggested next action:** Encode the actual page-1 beginner board graph, tile numbers, harbors, robber start, and starting pieces, or explicitly mark this as an abstract Catan variant.

2. **severity: major**  
   **evidence:** Rulebook includes Binnenhandel: active player may trade with other players; code says player negotiation is “not enumerated” and only implements maritime trades.  
   **why it matters:** Player trade is a central legal action and affects resource flow and strategy.  
   **suggested next action:** Add a bounded offer/accept/reject protocol, or document that this benchmark variant intentionally excludes player trade.

3. **severity: major**  
   **evidence:** Rulebook says Fortschritt cards execute their card text; code implements `play:progress` as a no-op and invents default dev deck counts `{Ritter:6, Fortschritt:3, Siegpunkte:3}`.  
   **why it matters:** Development-card probabilities and effects can materially affect victory and legal state transitions.  
   **suggested next action:** Provide card composition/effects from allowed artifacts, or disable/flag unsupported Fortschritt cards.

4. **severity: major**  
   **evidence:** Rulebook specifies threshold/strictly-longer transfer for Längste Handelsstraße but not all tie/drop cases; code invents tie/no-owner/removal behavior.  
   **why it matters:** This 2-VP card can decide terminal states.  
   **suggested next action:** Clarify tie and road-splitting behavior, then add deterministic tests.

5. **severity: minor**  
   **evidence:** Rulebook has resource-card stacks; code models no bank depletion.  
   **why it matters:** Usually rare, but can affect resource distribution/trades if finite card counts matter.  
   **suggested next action:** Clarify whether bank depletion is in scope.

6. **severity: minor**  
   **evidence:** Action names use abstract IDs like `x00`, `e00`, `t00`; rulebook only visibly labels some starting settlements A-D.  
   **why it matters:** Stable, but hard to compare to rulebook diagrams or deterministic scenarios.  
   **suggested next action:** Use rulebook/figure labels where available or provide a board-ID legend.

### 3. Rule coverage review

| rule area | covered correctly / partially covered / missing / unclear | evidence | notes |
|---|---|---|---|
| setup | partially covered | Preplaces 2 settlements/2 roads, supplies 5/4/15, starting resources; but abstract board/harbors/start layout | Exact beginner figure not implemented |
| player count and turn order | partially covered | Supports 3/4 players, removes red for 3p, `oldest_player`, advances `+1` | Seating/color order is assumed |
| legal actions | partially covered | Roll, build, maritime trade, discard, robber, dev play present | Player trade missing; progress cards generic/no-op |
| state transitions | partially covered | Costs, yields, robber, discard, city upgrade, dev timing implemented | Missing Binnenhandel and real Fortschritt effects; board-dependent legality invented |
| terminal conditions | mostly covered | Active/current player with total VP ≥10; hidden VP counted; terminal has no legal actions | Off-turn/special-card edge cases need tests |
| scoring/returns | partially covered | Public/total VP tracked; terminal winner-take-all zero-sum returns | Return convention is invented; rulebook only defines winner |
| chance handling | partially covered | Explicit dice, dev draw, robber steal chance nodes | Dev deck composition invented |
| hidden information | mostly covered | `information_state` hides opponent hands/dev identities | `render` is full debug; acceptable if documented |
| simultaneous / multi-actor | partially covered | Discard-on-7 modeled as sequential queue | Free-form trading omitted; discard simultaneity abstracted |
| rendering/action names | partially covered | Deterministic render and round-tripping string actions | Abstract IDs reduce rulebook fidelity |

### 4. Unsupported assumptions or invented rules

**Risky invented rules**
- Abstract 19-hex board topology, tile numbers, tile resources, crossing/edge IDs, starting settlements/roads.
- Abstract harbor positions and full set of 2:1 harbor resource types.
- Default development deck composition.
- `Fortschritt` cards as no-op actions.
- Omission of player-to-player trading.
- Longest-road tie, no-owner, and loss/reassignment behavior beyond the text.
- Hidden `Siegpunkte` card value assumed to be 1 VP.
- Unlimited resource bank / no depletion.
- Sequential discard queue after rolling 7.
- Robber steal modeled as victim choice followed by chance over resource type.

**Harmless or conventional assumptions**
- `oldest_player=0` default with configurable override.
- Clockwise/left-neighbor order represented as player index `+1`.
- Zero-sum terminal returns despite rulebook only specifying winner.
- Full-state debug `render` plus separate hidden-info-safe `information_state`.

### 5. Missing scenario tests

- Initial setup: verify each player has 2 settlements, 2 roads, correct remaining supply, and stated starting resources for B/C/D examples.
- Yield example: `roll -> chance:dice:3`; check White gets Holz and Blue/Orange get Erz according to the rulebook example.
- Robber/discard: with hands over 7, `roll -> chance:dice:7 -> discard:<multiset> -> robber:move:tXX -> robber:steal:pY -> chance:steal:Holz`.
- Maritime trade legality: check `trade:maritime:4:Holz->Erz` always legal with 4 Holz, and `3:1`/`2:1` only with matching harbor settlements.
- Player trade: construct active/non-active hands and expect some offer/accept flow; currently impossible.
- Dev timing: `pass -> build:dev -> chance:dev:Ritter`; verify fresh card cannot be played until after `end_turn`.
- Knight/largest army: play three `play:knight` actions across turns and verify Größte Rittermacht transfer only on strict lead.
- Longest road: build 5 roads, then a longer road, then split by foreign settlement.
- Terminal: active player reaches 10 via city/build/special/hidden VP; legal actions become empty and returns stable.
- Hidden info: compare `information_state(state, p0)` and `information_state(state, p1)` to ensure opponent hands/dev identities are hidden.

### 6. Open questions for the human

- Must this benchmark use the exact page-1 beginner board, including graph, harbors, number chips, and starting pieces?
- How should free-form player trading be represented as a finite action API?
- What are the allowed development-card composition and Fortschritt card effects?
- What exact longest-road behavior should apply for ties, broken roads, and falling below length 5?
- Should resource-card bank depletion be modeled?
- What terminal return convention should BoardBench use: zero-sum, winner 1/others 0, or VP-based?

### 7. Machine-readable summary

```text
score: 0.55
confidence: medium
critical_issues: 0
major_issues: 4
minor_issues: 2
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```
