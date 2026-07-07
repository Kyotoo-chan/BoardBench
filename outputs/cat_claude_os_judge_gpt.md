### 1. Score

- `score: 0.64`
- `confidence: medium`

The implementation delivers a playable four-player beginner-board CATAN core: hex production, building, bank/harbor trade, robber flow, development cards, longest road, and largest army. However, setup is fully scripted, seven-discard is automated, player negotiation is absent, the bank is infinite, the development deck order is fixed, and several development-card effects are stubbed. The environment is useful for rollouts but not benchmark-ready for full rule fidelity.

### 2. Top findings

1. **severity: major**  
   **evidence:** Rulebook §2–3 describes Binnenhandel where the active player negotiates offers and counter-offers with any opponent; only the active player may trade with others. Code `legal_actions()` in the main phase exposes only `("bank", …)` trades and no player-to-player actions.  
   **why it matters:** Trading is central to CATAN strategy and resource conversion; omitting it materially changes reachable states and action branching.  
   **suggested next action:** Add at least a simplified player-trade action model or document this as an intentional benchmark subset.

2. **severity: major**  
   **evidence:** Rulebook §4a on rolling a 7 requires each overstocked player to choose half their cards (rounded down). Code `_discard_auto()` deterministically drops the most abundant resource types via `_discard_auto(Counter(h))` in the roll-7 branch.  
   **why it matters:** Discard choice affects hand composition, steal targets, and downstream build/trade legality; auto-discard hides a player decision point.  
   **suggested next action:** Expose discard as explicit legal actions or document auto-discard as a fixed policy.

3. **severity: major**  
   **evidence:** Rulebook §3d and Almanach references describe Fortschritt cards (road building, year of plenty) with concrete effects. Code `apply_action()` for `("play", idx, "road")` and `("play", idx, "year")` only removes the card from hand without granting roads or resources.  
   **why it matters:** Development-card semantics are incomplete; agents can “play” cards that do nothing, diverging from rulebook outcomes.  
   **suggested next action:** Implement road-building and year-of-plenty sub-phases or remove those actions until implemented.

4. **severity: minor**  
   **evidence:** Rulebook recommends the beginner fixed board layout but players still choose where to place their two settlements and roads during setup. Code uses a hard-coded `SETUP` tuple and only offers `("setup", state.setup_step)` with no placement choice.  
   **why it matters:** Setup variability is removed; all games share identical opening geography and production access.  
   **suggested next action:** Acceptable for a deterministic benchmark if documented; otherwise add legal setup placements obeying distance and connectivity rules.

5. **severity: minor**  
   **evidence:** Rulebook §3d says purchased development cards are drawn from a shuffled face-down deck. Code defines `DEV_DECK` as a fixed tuple and always takes `state.dev_deck[0]`.  
   **why it matters:** Card order is fully predictable across runs, affecting knight/monopoly/VP timing.  
   **suggested next action:** Shuffle via chance node at game start or document fixed deck as benchmark convention.

6. **severity: minor**  
   **evidence:** Rulebook implies finite resource stacks in the bank/card holders. Code bank trades never decrement a bank supply.  
   **why it matters:** Rare in practice but allows impossible resource injections when stacks would be empty.  
   **suggested next action:** Track bank counts or note infinite bank as harmless simplification.

7. **severity: question**  
   **evidence:** Rulebook §4b allows playing one development card at any time during the turn, including before rolling; not on a card bought the same turn. Code only enumerates dev-card plays in the `main` phase after a non-7 roll or robber resolution.  
   **why it matters:** Pre-roll knight/monopoly timing differs from the rulebook turn structure.  
   **suggested next action:** Clarify whether post-roll-only dev play is acceptable for BoardBench.

### 3. Rule coverage review

| rule area | covered correctly / partially covered / missing / unclear | evidence | notes |
|---|---|---|---|
| setup | partially covered | `SETUP` tuple, scripted `setup` phase, starting resources from second settlement hexes | Matches beginner board topology but not player placement choice; 4-player only. |
| player count and turn order | covered correctly | `NUM_PLAYERS = 4`, `pass` rotates `(p+1)%4`, oldest player starts at 0 | Aligns with beginner four-player flow. |
| legal actions | partially covered | roll, bank/harbor trade, build, buy/play dev, robber move/steal, pass | No player trades; road/year dev stubs; auto-discard on 7. |
| state transitions | partially covered | phases `setup → roll → main/robber`, knight → robber sub-phase | Dev play limited to main; no pre-roll dev; multiple dev plays per turn possible after monopoly. |
| terminal conditions | partially covered | `_check_winner()` on build/buy_dev/knight when acting player reaches 10 VP | Win only checked for acting player; hidden VP dev counted in `_total_vp`. |
| scoring/returns | partially covered | settlements 1 VP, cities 2 VP, longest road/largest army +2, VP dev cards | Public vs hidden VP split modeled; win-at-10 rule present. |
| rendering/action names | covered correctly | `action_to_name`, `name_to_action`, stable `bank:`, `build:`, `chance:roll:` prefixes | BoardBench-friendly string actions. |
| chance handling | partially covered | `chance_outcomes()` with `ROLL_PROBS` for 2–12 | Correct two-dice distribution; fixed dev deck not chanced. |
| hidden information | partially covered | Dev hands and VP cards tracked per player; `render()` shows all hands | Full-information debug render; acceptable if noted. |
| simultaneous moves | not relevant | Sequential turns | N/A for base CATAN. |
| robber / steal | partially covered | move robber, steal one card from hex occupant | Steal picks lexicographically first resource, not random/hidden choice. |
| longest road / largest army | partially covered | `_update_longest_road`, `_update_largest_army`, tie-retention logic | Road-length DFS may differ on complex graphs; minimum 5 roads / 3 knights enforced. |

### 4. Unsupported assumptions or invented rules

- **Risky:** Automatic discard policy on roll 7 instead of player-chosen half (rounded down).
- **Risky:** No player-to-player trading; bank/harbor only.
- **Risky:** Road-building and year-of-plenty cards are no-ops when played.
- **Risky:** Deterministic steal target (`sorted(vh.items())[0]`) instead of random card from victim’s hidden hand.
- **Risky:** Fixed development deck order; no shuffle.
- **Risky:** Infinite bank resource supply.
- **Harmless convention:** Script-driven beginner setup placements matching a fixed board diagram.
- **Harmless convention:** Internal resource codes `B/G/L/O/W` with readable names in action strings.
- **Harmless convention:** `render()` exposes all player hands for debugging.

### 5. Missing scenario tests

- Roll 7 with 9 cards: player holds 9 resources; after discard, hand size should be 5 (half rounded down); assert `_discard_auto` drops 4.
- Harbor 2:1 trade: place settlement adjacent to wool harbor; assert `bank:2:1:wool->brick` legal when holding 2 wool.
- Longest road tie: two players reach length 5 same turn; assert previous holder keeps card if still tied.
- Knight before monopoly: buy dev, assert dev bought same turn cannot be played; next turn knight should enter robber phase.
- Robber blocks production: robber on hex h5; roll matching number; assert no production from that hex.
- Win on hidden VP dev: buy 10th VP via VP development card; assert terminal with `winner` set.
- Road building card played: assert two free road placements or mark as known no-op until implemented.
- Distance rule: attempt settlement adjacent to existing settlement; assert action not legal.

### 6. Open questions for the human

- Should BoardBench CATAN omit player negotiation entirely, or is bank-only trade an accepted benchmark subset?
- Is scripted beginner setup acceptable, or must agents choose legal setup placements?
- Should roll-7 discard remain an automated policy, or become explicit player actions?
- Are stubbed Fortschritt cards (road/year) in scope for the next iteration, or should those actions be removed?
- Is a fixed, ordered development deck intentional for determinism?

### 7. Machine-readable summary

```text
score: 0.64
confidence: medium
critical_issues: 0
major_issues: 3
minor_issues: 3
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```
