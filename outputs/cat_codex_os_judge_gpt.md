### 1. Score

score: 0.4  
confidence: medium

The implementation captures some core Catan mechanics: dice chance, resource production, basic building costs, robber/discard flow, longest road/largest army bookkeeping, and terminal winner-take-all returns. However, it uses a small invented example board instead of the 19-land-field beginner setup, omits player trading and progress-card effects, invents development-card composition and a max-turn draw, and has several rule/state mismatches that make it not benchmark-ready.

### 2. Top findings

1. **severity: critical**  
   **evidence:** Rulebook: “Sie besteht aus 19 Landfeldern” and beginner setup on page 1 with harbors/starting placements. Code: `make_text_example_board()` says “Small text-derived example board, not the missing official page-1 layout” and defines only 8 tiles, no harbors, and partial starting hands.  
   **why it matters:** Board topology, legal builds, production, harbors, starting resources, and action names are central to Catan. This is a toy scenario, not the specified game setup.  
   **suggested next action:** Add the full beginner board graph, all 19 land tiles, number chips, harbors, starting settlements/roads, and all starting resources.

2. **severity: major**  
   **evidence:** Rulebook allows Binnenhandel: active player may trade with all other players. Code implements only `_trade_actions()` for maritime/bank trades.  
   **why it matters:** A major legal action class is missing, changing strategy and reachable states.  
   **suggested next action:** Define a bounded player-trade protocol or explicitly scope it out with benchmark approval.

3. **severity: major**  
   **evidence:** Rulebook has development cards `Ritter`, `Fortschritt`, `Siegpunkte`; progress cards execute their card text. Code has no `play:progress` action and invents default deck counts `{"Ritter":1,"Fortschritt":1,"Siegpunkte":1}`.  
   **why it matters:** Bought progress cards become unusable, and dev-card chance probabilities are unsupported by the provided rules.  
   **suggested next action:** Provide/card-code progress effects and official composition, or remove/disable unsupported card types consistently.

4. **severity: major**  
   **evidence:** Rulebook: game ends when active player has/reaches 10+ VP. Code default `max_turns=200` can set `terminal_winner=-1` and return all zeros.  
   **why it matters:** This invents a draw/truncation condition not in the rules and can corrupt terminal/scoring benchmarks.  
   **suggested next action:** Remove default max-turn terminal or make it an explicit non-rule testing option disabled by default.

5. **severity: major**  
   **evidence:** Rulebook says robber must move to another `Landfeld`; desert is a land field with no yield. Code legal robber moves exclude tiles where `LANDSCAPE_RESOURCE` is `None`, so `Wueste` cannot be chosen.  
   **why it matters:** Robber movement legal action set is wrong after the robber leaves the desert.  
   **suggested next action:** Allow robber movement to any land tile except the current robber tile, including desert.

6. **severity: minor/major**  
   **evidence:** Rulebook gives ordered phases: roll, trade, then build. Code combines trade/build/dev/end into one `"main"` phase and allows interleaving.  
   **why it matters:** If strict ordering is intended, legal sequences are too permissive.  
   **suggested next action:** Clarify whether trade/build interleaving is allowed; otherwise split phases.

### 3. Rule coverage review

| rule area | covered correctly / partially covered / missing / unclear | evidence | notes |
|---|---|---|---|
| setup | missing | Code uses 8-tile text example board, no full 19-tile setup, no harbors by default | Biggest fidelity issue |
| player count and turn order | partially covered | Supports 3/4 players; fixed player 0 starts | “Oldest player starts” modeled as fixed p0 assumption |
| legal actions | partially covered | Roll, build, maritime trade, knight, robber/discard present | Missing player trade, progress cards, full harbor actions due no harbors |
| state transitions | partially covered | Resource production, costs, roads/settlements/cities, robber discard mostly present | Depends on incomplete board; trade/build order questionable |
| terminal conditions | partially covered | Active player 10+ VP detected | Invented max-turn draw condition |
| scoring/returns | partially covered | VP includes buildings, special cards, hidden VP dev cards; returns winner +1, losers negative | Returns are an unsupported modeling choice but acceptable if documented |
| chance handling | partially covered | Dice, dev draw, robber steal modeled as chance nodes | Dev deck composition invented |
| hidden information | partially covered | `information_state` shows own hand/devs and not opponents’ exact card types | Public render shows card counts; probably acceptable but should be clarified |
| rendering/action names | partially covered | Stable string action names and deterministic render | Board IDs are invented from toy board; no player-trade names |
| simultaneous/multi-player subphases | partially covered/unclear | Discard queue sequentially resolves all over-limit players | Rule does not specify exact discard ordering; player trade negotiation absent |

### 4. Unsupported assumptions or invented rules

- **Risky:** Replaces the official beginner board with a small invented board.
- **Risky:** No default harbors, despite harbor trade being in the rulebook.
- **Risky:** Starting resources are only partially filled from examples, not all players’ marked settlements.
- **Risky:** Development deck composition defaults to 1 Knight, 1 Progress, 1 Victory Point.
- **Risky:** Progress cards exist but cannot be played and have no effects.
- **Risky:** Player trading is omitted entirely.
- **Risky:** Default max-turn draw at 200 turns.
- **Risky:** Robber cannot move to the desert.
- **Risky/unclear:** Trade and build actions are freely interleaved in one main phase.
- **Risky/unclear:** Longest-road ownership is not removed if the owner’s road is broken below threshold; the rulebook text is incomplete on this edge case.
- **Harmless convention:** Player 0 is treated as the oldest/starting player.
- **Harmless convention:** Terminal returns use +1 for winner and equal negative values for losers, since payoff values are not specified.

### 5. Missing scenario tests

- Initial setup test: assert 19 land tiles, correct robber start, harbors present, and each player has 2 settlements/2 roads.
- Production example: `roll -> chance:dice:3`; verify White gets 1 Holz, Blue and Orange each get 1 Erz according to the rulebook example.
- Production example: `roll -> chance:dice:8`; verify Red gets 2 Erz from two settlements and White gets 1 Erz.
- Robber desert legality: after moving robber off desert, verify `robber:move:t_wueste` or equivalent desert tile action is legal.
- Seven/discard: set a player to 9 resource cards, then `roll -> chance:dice:7`; verify exactly 4 chosen cards must be discarded.
- Player trade availability: after dice resolution in trade phase, verify some bounded active-player-to-opponent trade action exists.
- Progress card: buy/draw `chance:dev:Fortschritt`, advance turn, then verify a legal progress-card play action or documented unsupported behavior.
- Terminal no-draw: with no player at 10 VP, advance near 200 turns and verify no rule-invented terminal draw occurs.

### 6. Open questions for the human

- Is the full page-1 beginner board layout required for this benchmark, including exact graph, harbors, chips, and starting placements?
- How should free-form player negotiation/trading be represented as finite deterministic actions?
- Are the development-card composition and progress-card texts available, or should development cards be restricted?
- Should trade and build be strictly ordered, or may they be interleaved?
- What return convention should BoardBench use for multiplayer Catan: winner-take-all zero-sum or winner 1/others 0?
- How should longest-road ownership behave when the holder’s road is broken below 5 or ties occur?

### 7. Machine-readable summary

```text
score: 0.4
confidence: medium
critical_issues: 1
major_issues: 5
minor_issues: 3
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```
