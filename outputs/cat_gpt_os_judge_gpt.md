### 1. Score

- `score: 0.45`
- `confidence: high`

The implementation captures several core Catan mechanisms: 3–4 players, turn phases, dice chance, resource production, building costs, robber/discard flow, hidden hands, and terminal win-at-10 logic. However, it is not benchmark-ready because the board/setup is largely invented, player trading is omitted, harbors are omitted, development cards are only partially modeled, and many official beginner-board details are absent or replaced with risky assumptions.

### 2. Top findings

1. **severity: major**  
   **evidence:** Code states the official beginner board figure is missing and uses “a small explicit abstract graph”; many tiles have `number=None`, empty crossing lists, and no real harbor layout.  
   **why it matters:** Board topology drives legal roads/settlements, production, robber targets, longest road, and scenario comparability. This makes the environment Catan-like rather than faithful to the supplied beginner setup.  
   **suggested next action:** Supply/encode the actual page-1 board graph, tile numbers, crossings, edges, harbors, and starting pieces.

2. **severity: major**  
   **evidence:** Rulebook explicitly allows Binnenhandel/player trading with the active player; code says “Player-to-player trading is omitted.”  
   **why it matters:** Trading is a central legal action and affects resource flow, strategy, and benchmark trajectories.  
   **suggested next action:** Add a bounded offer/accept/reject protocol or document that the benchmark intentionally excludes player trading.

3. **severity: major**  
   **evidence:** Rulebook defines 4:1, 3:1 harbor, and 2:1 special harbor trades; code has `HARBORS = {}` and only enables 4:1 trades.  
   **why it matters:** Harbor settlements should materially change legal actions and resource conversion.  
   **suggested next action:** Encode harbor positions/types from the setup figure or add explicit assumptions/tests.

4. **severity: major**  
   **evidence:** Rulebook includes Ritter, Fortschritt, and Siegpunkte development cards; code uses default deck `(1,1,1)`, has no progress-card effects, and only `play:knight` is legal.  
   **why it matters:** Development-card strategy, largest army, hidden VP, and progress effects are incomplete.  
   **suggested next action:** Provide deck composition and progress-card text, or clearly exclude progress cards from the benchmark.

5. **severity: minor**  
   **evidence:** `render()` exposes all resource hands and dev cards, while `information_state()` hides opponents’ private data.  
   **why it matters:** If `render()` is used as a player observation, it leaks hidden information.  
   **suggested next action:** Clarify that `render()` is debug-only or make render public-information-safe.

### 3. Rule coverage review

| rule area | coverage | evidence | notes |
|---|---|---|---|
| setup | partially covered | 3–4 players, initial 2 settlements/roads, starting resources for lettered settlements | Actual beginner board, full graph, harbors, number chips mostly missing/invented |
| player count and turn order | mostly covered | Supports 3 or 4 players; removes red for 3 players; advances `(turn_player + 1) % num_players` | “Oldest player” modeled by configurable `start_player` |
| legal actions | partially covered | Roll, discard, robber, 4:1 trade, build road/settlement/city/dev, play knight | Missing player trades, harbor trades, progress-card actions |
| state transitions | partially covered | Dice production, 7/discard/robber, costs, builds, city upgrade, knight/largest army implemented | Depends on abstract board; progress cards and full trading absent |
| terminal conditions | mostly covered | Active player wins at ≥10 VP during own turn | Reasonable; counts hidden VP cards, though VP-card value is assumed |
| scoring/returns | partially covered | Terminal winner gets `+1`, losers `-1/(N-1)` | Payoff convention invented; rulebook only specifies winner |
| rendering/action names | mostly covered | Stable string action names and deterministic render | Render leaks hidden info; board labels are invented |
| chance handling | mostly covered | Explicit chance nodes for dice, dev draw, robber steal | Dev deck composition invented; steal by resource type is acceptable abstraction |
| hidden information | partially covered | `information_state()` hides other hands/dev cards | `render()` reveals private info |
| simultaneous moves | unclear/partially covered | Discard-on-7 modeled sequentially by `pending_discard` | Rulebook says all affected players discard; simultaneity/order not specified |

### 4. Unsupported assumptions or invented rules

- **Risky:** Invented abstract board graph, crossing IDs, edge IDs, tile IDs, and many missing number chips.
- **Risky:** No harbors at all, despite harbor trading being in the rulebook.
- **Risky:** No player-to-player trading protocol.
- **Risky:** Development deck has one card of each type by default.
- **Risky:** Progress cards have no legal play action or effect.
- **Risky:** Several starting resources/placements beyond examples are inferred.
- **Risky:** Longest-road holder keeps the card unless another player is strictly longer, including possible unclear drop/tie cases.
- **Harmless/modeling convention:** Unlimited resource bank because card counts/depletion are not supplied.
- **Harmless/modeling convention:** Winner-take-all numeric returns.
- **Questionable:** Discard-on-7 resolved sequentially rather than simultaneously.
- **Questionable:** `render()` exposes hidden state as debug output.

### 5. Missing scenario tests

- Initial setup: verify 3-player setup excludes red and 4-player setup gives each player 2 settlements/2 roads.
- Dice production: `roll -> chance:dice:3`, check White gets Holz and Blue/Orange get Erz per rulebook example.
- Dice production with city: upgrade White settlement, then `roll -> chance:dice:10`, verify 2 Wolle.
- Robber/discard: fixture players with 8/9 cards, then `roll -> chance:dice:7`, verify discard counts and robber movement.
- Robber blocking: move robber to a productive tile, then roll that number and verify no yield.
- Development card freshness: `build:dev -> chance:dev:Ritter`, verify `play:knight` is not legal until a later turn.
- Harbor trade gap: fixture settlement on harbor once board exists; verify 3:1 and 2:1 trade actions.
- Player trading gap: verify intended offer/accept/reject action protocol once specified.
- Longest road: build 5-road chain, then opponent longer chain, then split by settlement.
- Terminal: fixture active player at 9 VP, build city/settlement or gain hidden VP, verify terminal returns.

### 6. Open questions for the human

1. Should this benchmark require the exact beginner board from page 1, including all crossings, edges, numbers, harbors, and starting placements?
2. How should free-form player trading be represented as finite BoardBench actions?
3. What are the development-card deck composition and progress-card effects?
4. Should resource-card bank depletion be modeled?
5. What longest-road tie/drop behavior should be used if not specified by the supplied rulebook?
6. Is `render()` allowed to be full debug state, or must it hide private information?

```text
score: 0.45
confidence: high
critical_issues: 0
major_issues: 4
minor_issues: 1
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```
