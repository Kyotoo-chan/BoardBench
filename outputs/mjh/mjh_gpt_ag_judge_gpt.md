### 1. Score

- `score: 0.65`
- `confidence: medium`

The implementation is playable and covers many core one-deal Mah-Jongg mechanics: 4 players, tile draws, discards, claims, Mah-Jongg detection, Kangs, some hidden information, and substantial scoring tables. However, it abstracts or omits important rulebook areas: exact wall/dead-wall setup, dice break, bonus replacement from the dead wall, full Partie/round wind rotation, and several context-sensitive scoring cases. Some invented procedural assumptions and a claim/source loophole could affect gameplay and benchmark results.

### 2. Top findings

1. **severity: major**  
   **evidence:** Rulebook section 6 defines a Partie with four wind rounds, wind rotation, East continuing until loss or four wins; code docstring says it models ÔÇ£one deal,ÔÇØ and wind rotation is outside the API.  
   **why it matters:** Benchmarks involving round wind changes, East streaks, repeated drawn games, or ÔÇ£Neunmal Mah-JonggÔÇØ cannot be faithfully represented.  
   **suggested next action:** Clarify whether BoardBench expects one hand only or the full Partie; if full, add match/round state and wind rotation.

2. **severity: major**  
   **evidence:** Rulebook describes dice, wall break, live wall/dead wall, and flower/season replacement from the dead wall; code draws from a flat remaining multiset and comments that dead-wall geometry is abstracted.  
   **why it matters:** Chance probabilities, wall exhaustion, bonus-tile handling, and dead-wall scoring/limit hands are not faithful.  
   **suggested next action:** Either restrict to the no-bonus simplified variant or explicitly model live wall, dead wall, replacement draws, and dice/wall break.

3. **severity: major**  
   **evidence:** After `_claim_pong`/`_claim_chi`, code enters `discard` phase, where `mahjong:selfdraw` may be legal if the claimed discard completed the hand.  
   **why it matters:** A player may pass a discard Mah-Jongg claim, take the same tile as an ordinary meld, then declare a wrongly sourced self-draw win.  
   **suggested next action:** Track whether the current discard phase follows an ordinary claim and suppress self-draw Mah-Jongg unless a real wall/replacement draw occurred.

4. **severity: major**  
   **evidence:** Code omits ÔÇ£Mah-Jongg nach Ruf zu Beginn,ÔÇØ cannot naturally produce dead-wall wins, does not update `east_consecutive_wins`, and simplifies several limit-hand predicates.  
   **why it matters:** Scoring is central to returns; missing context bonuses can change payoffs substantially.  
   **suggested next action:** Add targeted scoring tests from the rulebook examples and mark unsupported scoring categories explicitly.

5. **severity: minor**  
   **evidence:** Code invents labels such as `zeichen`, `drache-rot`, `drache-weiss`, and resolves claim ties by seating order.  
   **why it matters:** Mostly harmless for playability, but action names and tie behavior may diverge from intended benchmark conventions.  
   **suggested next action:** Confirm canonical tile labels and conflict-resolution rules.

### 3. Rule coverage review

| rule area | coverage | evidence | notes |
|---|---|---|---|
| setup | partially covered | 4 copies of normal tiles, optional bonus tiles, initial 14/13 deal sequence | Missing dice, wall break geometry, live/dead wall separation, random wind determination |
| player count and turn order | partially covered | `NUM_PLAYERS = 4`, East/South/West/North order, right neighbor `(p+1)%4` | Single-deal only; no Partie wind rotation |
| legal actions | partially covered | discard, claim Pong/Chi/Kang, self/discard Mah-Jongg, rob Kang | Claim priority is assumed; possible self-draw loophole after ordinary discard claim |
| state transitions | partially covered | explicit chance draws, discard/claim phases, replacement after Kangs | Bonus/dead-wall transitions are not faithful |
| terminal conditions | partially covered | Mah-Jongg terminal, wall exhaustion after final discard | Drawn game just returns zero; repeated game/round handling missing |
| scoring/returns | partially covered | many point tables, doubles, limits, East double settlement | Several context bonuses/limit hands incomplete or approximate |
| rendering/action names | mostly covered | stable string actions like `discard:<tile>`, `claim:pong...`; deterministic render | Some labels invented; render exposes full hidden state as debug |
| chance handling | partially covered | `chance_outcomes` over remaining multiset | No ordered wall, dice, dead wall, or exact replacement source |
| hidden information | partially covered | `information_state` hides opponentsÔÇÖ hands | Full `render` leaks all hands, acceptable only as debug |
| simultaneous moves | unclear/not applicable | reactions modeled sequentially by priority | Rulebook does not fully specify multiple-claim tie handling |
| bonus tiles | partially covered | flowers/seasons exposed and scored | Replacement should come from dead wall, not flat remaining pool |

### 4. Unsupported assumptions or invented rules

- **Harmless convention:** Third numbered suit is named `zeichen`; dragon labels are invented as red/green/white.
- **Risky assumption:** The environment models only one deal rather than the full Partie described in the wind section.
- **Risky assumption:** Player 0 is fixed as East, with fixed initial seating unless manually configured.
- **Risky assumption:** Dice, wall break, live wall, and dead wall are replaced by unordered tile-type chance draws.
- **Risky assumption:** Flower/season replacements draw from the same multiset instead of the dead wall.
- **Risky assumption:** Multiple claim conflicts are resolved by priority groups and seating order; the rulebook gives categories but not all tie details.
- **Risky assumption:** A maximum-scoring decomposition is chosen automatically for scoring.
- **Risky assumption:** Non-winner concealed scoring greedily extracts Pongs/pairs from hands; the rulebook examples imply scoring incomplete hands but do not fully define decomposition.
- **Risky assumption:** Concealed Kangs count toward ÔÇ£Drei verdeckte Pong.ÔÇØ
- **Known omission:** ÔÇ£Mah-Jongg nach Ruf zu BeginnÔÇØ is not implemented.
- **Known omission:** Dead-wall win bonuses/limit hands are effectively unreachable.
- **Known omission:** East consecutive wins and ÔÇ£Neunmal Mah-JonggÔÇØ are not updated through play.

### 5. Missing scenario tests

- Initial deal: force chance draws until East has 14 tiles and others 13, then verify East acts first.
- Turn order: `discard:<tile>` by East, all claims pass, South draws next.
- Claim priority: one discard where another player can Mah-Jongg, another can Pong/Kang, and right neighbor can Chi; verify offer order.
- Ordinary claim transition: `claim:chi:p1:...` then p1 must discard; after no claim, p2 draws.
- Regression for claim loophole: a player who passes `mahjong:discard:...` should not later claim the same tile and declare `mahjong:selfdraw`.
- Final wall tile: last draw, discard, only Mah-Jongg claims legal; if all pass, terminal draw.
- Robbing Kang: `kong:add:<idx>:bambus-2` followed by `mahjong:rob_kang:...` should end the game and score the rob-Kang bonus/limit if applicable.
- Bonus tile replacement: with bonus tiles enabled, drawing `blume-1` should expose it, replace it correctly, and score +4 plus wind bonus if applicable.
- Construct both rulebook accounting examples as terminal states and verify exact returns.
- Limit-hand tests: seven pairs half limit, thirteen wonders full limit, Segen des Himmels, Segen der Erde, four Kangs.

### 6. Open questions for the human

- Should the benchmark environment represent a single Spiel/deal, or the full Partie with four wind rounds and rotation?
- Is the simplified no-flower/no-season variant acceptable as the default benchmark target?
- If bonus tiles are included, must the dead wall and wall break be modeled exactly?
- What is the intended rule for multiple simultaneous Mah-Jongg claims or ties within the same claim priority?
- Can a player decline Mah-Jongg on a discard and still claim that same discard for an ordinary meld?

### 7. Machine-readable summary

```text
score: 0.65
confidence: medium
critical_issues: 0
major_issues: 4
minor_issues: 1
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```
