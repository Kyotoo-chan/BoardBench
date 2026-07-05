### 1. Score

score: 0.42  
confidence: medium

The implementation captures a playable four-player Mahjong-like environment with tile drawing, discarding, claims, Mahjong termination, washout, hidden information views, and parts of the scoring table. However, it makes many simplifying assumptions not stated in the rulebook, omits round/seat-wind progression, flowers/seasons, wall-break dice setup, many scoring conditions, most limit hands, and likely mis-models initial dealing and dead-wall behavior. It is useful as a rough BoardBench prototype, but not benchmark-ready for this rulebook.

### 2. Top findings

- severity: major  
  evidence: Rulebook says East receives an additional 14th starting tile; code deals only 52 tiles, then enters a normal draw phase for East.  
  why it matters: The first East action is modeled as a chance draw from the living wall, not as the initial extra tile from setup, changing wall count and opening state.  
  suggested next action: Deal 13 to all players plus East’s 14th tile during setup before the first discard.

- severity: major  
  evidence: Rulebook includes flowers/seasons as optional but described in detail; code hard-codes no bonus tiles and no dead-wall replacement for them.  
  why it matters: If the benchmark rulebook includes these tiles, tile count, replacement draws, scoring, and doublings are incomplete.  
  suggested next action: Either encode a documented “without flowers/seasons” variant in the test metadata or implement bonus tiles and replacements.

- severity: major  
  evidence: Rulebook describes a whole Partie with four wind rounds, rotation of East, repeated games, East retaining/losing seat, and max consecutive wins; code models only one hand with fixed `ROUND_WIND = "WE"` and fixed player winds.  
  why it matters: Returns and scoring depend on East and round wind; long-form game state is absent.  
  suggested next action: Decide whether BoardBench target is one hand or a full Partie. If one hand, document this explicitly as a benchmark scope reduction.

- severity: major  
  evidence: Code detects only a few limit hands: seven pairs, thirteen orphans, all honors, all terminals, while the rulebook lists many more.  
  why it matters: Terminal scoring can be substantially wrong for hands such as four kongs, green hand, nine gates, blessing hands, robbing specific kongs, etc.  
  suggested next action: Add limit-hand detection or mark scoring as partial and avoid using score fidelity as a benchmark target.

- severity: major  
  evidence: Rulebook says a Kong claim from a discard can complete a concealed Pong and then draw a replacement from the living wall; code allows `Kong:<tile>` when a player has three matching tiles in hand from another player’s discard.  
  why it matters: This may not match the described “verdeckten Pong zu einem Kang” reaction and exposes a different claim structure.  
  suggested next action: Clarify whether discard-called Kong requires exactly a concealed pong in hand and whether it should be represented as open.

- severity: major  
  evidence: Rulebook says the player who takes a discard must discard and then their right neighbor is next. Code after Pong/Kong/Chi claim sets `current = cur`, then after that player discards starts claims and eventually draws `(disc + 1) % 4`, where `disc` is the claiming player.  
  why it matters: This appears mostly consistent after the claimant discards, but the priority/order for claim decisions is assumed and not specified in full detail by the rulebook.  
  suggested next action: Add deterministic tests around claim turn order after Pong, Chi, Kong, and unclaimed discard.

- severity: minor  
  evidence: Rulebook has dice-based wall break and dead wall construction; code ignores dice and uses a simple random pool.  
  why it matters: For a single-hand abstract environment this is probably harmless, but it loses wall-order and dead-wall details relevant to replacements and last-tile conditions.  
  suggested next action: Document as an abstraction or model explicit wall order and dead-wall draws.

- severity: minor  
  evidence: Code has `information_state`, while `render` reveals all hands with a comment.  
  why it matters: This is acceptable for debug comparison, but hidden information is central to the game and checks should use `information_state` for player views.  
  suggested next action: Add tests that opponent hands are hidden in `information_state`.

### 3. Rule coverage review

| rule area | coverage | evidence | notes |
|---|---|---|---|
| setup | partially covered | Code creates 4 players, 34 tile types x4, no flowers, chance deal. | Missing dice, wall break, exact dead wall, East’s setup tile handled as draw. |
| player count and turn order | partially covered | `num_players = 4`, counterclockwise order via `(p + 1) % 4`. | No full Partie, wind rotation, East retention/loss rules, or round progression. |
| legal actions | partially covered | Draw, discard, Mahjong, Pong, Chi, Kong, rob-kong actions exist. | Claim priority is invented; some claim legality may not match text exactly. |
| state transitions | partially covered | Explicit phases: deal/draw/discard/claim/robkong/terminal. | Flowers/seasons, dead-wall replacements, round transitions, and detailed wall exhaustion are incomplete. |
| terminal conditions | partially covered | Ends on Mahjong or wall exhaustion. | Last drawn tile may still get discard before washout in rulebook; code terminals immediately if `wall == 0` before draw. |
| scoring/returns | partially covered | Encodes many point values, doubling settlement, East double payment, limit cap. | Many scoring bonuses and limit hands omitted; fixed limit and fixed round wind. |
| rendering/action names | covered correctly | Stable string actions and deterministic render. | Action names are readable and round-trip by identity. |
| chance handling | partially covered | Chance nodes enumerate deal/draw tile probabilities from `pool`. | Uses unordered pool abstraction, no explicit wall/dead-wall order or dice setup. |
| hidden information | partially covered | Full state stores hands; `information_state` hides opponent hands. | `render` reveals all hands, but documented as debug. |
| simultaneous moves | unclear/not relevant | Rulebook has sequential claims after a discard, not simultaneous commitments. | Code serializes claim responses by assumed priority. |

### 4. Unsupported assumptions or invented rules

- Harmless/risky: No flowers/seasons are included. The rulebook permits removing them for simplification, but the implementation fixes that variant without making it configurable.
- Risky: `ROUND_WIND` is always East.
- Risky: One isolated hand is modeled, not four rounds or repeated games.
- Risky: Limit is fixed at `500`, based on examples, though the rulebook says “vereinbarte Limit”.
- Risky: Claim priority is implemented as Mahjong claims first, then Pong/Kong, then Chi, with seat-order prompting. The rulebook lists reactions but does not fully specify conflict resolution.
- Risky: Dead wall is represented as a simple 14-tile reserve and not as the wall structure described in setup.
- Risky: Wall order and dice wall-break are replaced by pool-based chance draws.
- Risky: Many named limit hands are not detected and fall back to ordinary scoring.
- Risky: Last-tile, dead-wall-tile, unique-wait, pair-completion, and several other scoring bonuses are mostly absent.
- Harmless: Tile code `Z` is assumed for the third suit name.
- Harmless: `render` is a full debug view, while `information_state` is the player-visible view.

### 5. Missing scenario tests

- Initial deal reaches 13 tiles for players 1-3 and 14 for East before East’s first discard.
- Unclaimed discard: `Discard:<tile>`, all claim players `Pass`, right neighbor draws next.
- Chi only by the right neighbor, never by the other two players.
- Pong claim from discard creates an open Pong, removes two matching hand tiles, removes the discard, and claimant discards next.
- Mahjong claim from discard terminates immediately and assigns the claimant as winner.
- Added Kong can be robbed when another player can complete Mahjong with that tile.
- Wall exhaustion after final draw still allows the final discard and Mahjong claim before washout.
- Seven pairs scores half limit.
- A listed but currently missing limit hand, such as four Kongs, scores the full limit.
- East double settlement matches the rulebook example pattern.

### 6. Open questions for the human

- Should this BoardBench target model one Mahjong hand only, or the full Partie with wind rounds and East rotation?
- Are flowers and seasons intended to be included for this benchmark run, or is the simplified no-bonus-tile variant acceptable?
- Should scoring fidelity include all limit hands and all end-condition doublings, or is the benchmark mainly about legal play flow?

### 7. Machine-readable summary

```text
score: 0.42
confidence: medium
critical_issues: 0
major_issues: 6
minor_issues: 2
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```