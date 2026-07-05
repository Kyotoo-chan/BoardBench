### 1. Score

score: 0.55  
confidence: medium

The implementation is playable and covers many core single-deal Mahjong mechanics: 4 players, hidden hands, chance draws, discards, claims, melds, wall exhaustion, and a substantial scoring attempt. However, it deliberately omits the multi-game wind/round structure, simplifies wall/dead-wall setup, has several important state-transition issues, and only partially implements the large scoring/limit-hand rules. These issues are likely to affect benchmark fidelity, especially for terminal/scoring scenarios.

### 2. Top findings

1. **severity: major**  
   **evidence:** Rulebook section 6 defines a full Partie with four wind rounds, 4–16 games per round, East rotation, and cumulative settlement. Code docstring says one “Spiel” only and marks the multi-game Partie out of scope.  
   **why it matters:** Wind rotation and repeated scoring are part of the provided rules and materially affect returns over a full game.  
   **suggested next action:** Decide whether BoardBench target is one hand/deal or a full Partie; if full, add round/wind rotation and cumulative score state.

2. **severity: major**  
   **evidence:** Rulebook setup describes dice, wall break, live/dead wall, dead wall as Doppelziegel/loose tiles. Code uses a shuffled multiset Counter and reserves `DEAD_WALL = 14` individual tiles, with no dice/wall geometry.  
   **why it matters:** Draw order, dead-wall replacement, and exhaustion timing may differ from the rulebook.  
   **suggested next action:** Model an ordered wall with explicit live/dead wall segments, or document that setup/dice/wall geometry is intentionally abstracted.

3. **severity: major**  
   **evidence:** Rulebook says after the last living-wall tile is drawn, the player may discard; if that discard is not used to complete Mah-Jongg, the game ends. Code still allows non-winning `pong`, `kong`, and `chi` claims on that final discard.  
   **why it matters:** This changes terminal behavior and can extend or alter games after the wall should be exhausted.  
   **suggested next action:** Track “last living-wall discard” and restrict reactions to Mah-Jongg-only.

4. **severity: major**  
   **evidence:** Robbing the Kong rule says the robbed tile is taken by the Mah-Jongg caller and the promoting player has only the open Pong. Code’s `_apply_rob` gives the tile to the winner but does not remove it from the source player’s hand.  
   **why it matters:** Terminal scoring for the robbed player can be wrong, and tile conservation is broken.  
   **suggested next action:** Remove the promoted tile from the source hand when the rob succeeds.

5. **severity: major**  
   **evidence:** Scoring tables include many limit hands and bonuses. Code implements only a subset and documents several omissions. Claimed Mah-Jongg tiles are also folded into the concealed hand and may be scored as concealed.  
   **why it matters:** Returns are central to judging Mahjong outcomes; many legal hands will receive incorrect values.  
   **suggested next action:** Add structured win metadata: winning tile source, completed figure, open/concealed status, last-tile flags, robbing-kong flags, dead-wall flags, and implement remaining listed limit hands/bonuses.

6. **severity: minor**  
   **evidence:** When a discard is claimed for Pong/Chi/Kong/Mah-Jongg, code leaves it in `discards`.  
   **why it matters:** Render/information state shows a claimed tile as still discarded/dead, conflicting with the rulebook distinction between used and dead discarded stones.  
   **suggested next action:** Remove or mark claimed discards separately from dead discards.

### 3. Rule coverage review

| rule area | covered correctly / partially covered / missing / unclear | evidence | notes |
|---|---|---|---|
| setup | partially covered | Code creates 136 non-bonus tiles and deals 13 each plus East 14th. | Dice, wall break, ordered wall, exact dead wall, Doppelziegel structure not modeled. |
| player count and turn order | partially covered | 4 players, East/South/West/North seats, right-neighbor as `(p+1)%4`. | Full wind rounds and East rotation are missing. |
| legal actions | partially covered | Discard, draw Mah-Jongg, Pong, Chi, Kong, rob Kong implemented. | Reaction priority is assumed; final-discard reactions too broad; bonus tiles absent. |
| state transitions | partially covered | Claims set claimant to discard; no claim advances to right neighbor draw. | Robbed Kong does not remove source tile; claimed discard remains in discard pile; wall/dead-wall transitions simplified. |
| terminal conditions | partially covered | Terminal on Mah-Jongg or wall exhaustion. | Last-wall discard rule not faithfully enforced; full Partie terminal condition missing. |
| scoring/returns | partially covered | Settlement examples are encoded; many figure points/doublings implemented. | Many bonuses/limit hands missing; claimed winning figures may be scored concealed; non-winner scoring is greedy and incomplete. |
| rendering/action names | mostly covered | Stable string action names and deterministic render/information state. | Render exposes full hidden state by design; claimed discards can be misleading. |
| chance handling | partially covered | Chance nodes for deal/draw/replacement, no hidden RNG. | Chance uses tile multiset, not an ordered wall or explicit dice/dead-wall split. |
| hidden information | mostly covered | `information_state` hides other hands and wall contents. | Full `render` leaks by design as debug; acceptable if documented. |
| simultaneous moves | not relevant | Rulebook uses reaction order, not simultaneous commitments. | None needed. |
| flowers/seasons | mostly missing / optional | Code defaults `use_bonus=False`; flag not wired. | Rulebook allows removing them for simplification, but if included they affect wall size, replacement, points, doublings. |

### 4. Unsupported assumptions or invented rules

- **Harmless/mostly documented:** Tile labels `Z`, `Da`, `Db` are placeholders because the text implies a third suit and three dragons but only names some tile categories.
- **Risky:** Reaction priority `Mah-Jongg > Kong/Pong > Chi` with distance tie-break is assumed; the rulebook lists reactions but does not specify a full priority system.
- **Risky:** Modeling only a single deal rather than the full Partie with wind rounds and East rotation.
- **Risky:** Reserving exactly 14 individual tiles as dead wall, despite the rulebook’s Doppelziegel/loose-tile description.
- **Risky:** Treating all wall draws as draws from a Counter rather than from an ordered live wall after dice break.
- **Risky:** Default removal of flowers/seasons is allowed by the rulebook, but `use_bonus=True` is exposed without functional implementation.
- **Risky:** Scoring non-winners by greedily extracting concealed triplets/kongs and one best pair; the rulebook does not define this greedy simplification.
- **Risky:** Treating claimed Mah-Jongg tiles as concealed for decomposition/scoring.
- **Risky:** Allowing a player to choose not to declare Mah-Jongg and discard instead; the rulebook says a player “can” call, so optionality is plausible but not explicit.

### 5. Missing scenario tests

- Deal to a scripted near-exhausted wall, draw the last living-wall tile, discard it, and verify only `mahjong:claim:<tile>` reactions are legal.
- Robbing Kong: player has exposed Pong and fourth tile in hand; another player can Mah-Jongg from it; after `mahjong:claim`, verify source hand no longer contains the robbed tile.
- Claimed discard cleanup: after `discard:B5`, `pong:B5`, verify `B5` is not still represented as a dead discard.
- Claimed Mah-Jongg scoring: win by claiming discard to complete a Pong/Chi and verify open/concealed scoring matches the rulebook.
- Dead-wall/last-wall scoring flags: Mah-Jongg from last living-wall tile, last discard, replacement tile, and robbing Kong should trigger correct bonuses/doublings.
- Limit hands: seven pairs, thirteen orphans, four Kangs, three dragon triplets plus arbitrary set/pair, four wind triplets plus arbitrary pair, nine lanterns, green hand, heaven/earth blessings.
- Wind rotation/cumulative scoring, if full Partie is required: East loses, East wins repeatedly, maximum consecutive East wins, round wind changes.

### 6. Open questions for the human

1. Should the benchmark target a single Mahjong deal/hand or the full Partie with four wind rounds and East rotation?
2. Are flowers and seasons required, or is the simplified no-bonus-tile variant acceptable?
3. Should exact wall geometry/dice/dead-wall replacement be modeled, or is unordered tile chance acceptable?
4. What priority order should be used when multiple players can claim the same discard?

### 7. Machine-readable summary

```text
score: 0.55
confidence: medium
critical_issues: 0
major_issues: 5
minor_issues: 1
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```
