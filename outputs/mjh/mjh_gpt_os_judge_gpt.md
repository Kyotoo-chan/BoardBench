### 1. Score

score: 0.60  
confidence: medium

The implementation is playable and covers many core one-hand mechanics: four players, deal/draw/discard flow, claims, Kangs, robbing Kang, Mahjong terminal states, chance draws, hidden-information views, and settlement-style returns. However, it is a simplified interpretation with important omissions or assumptions around setup/dead wall, reaction priority, scoring completeness, optional bonus tiles, and wind/round structure, so it is not fully benchmark-ready for the provided rulebook.

### 2. Top findings

1. **severity: major**  
   **evidence:** Rulebook setup describes wall building, dice, wall break, dead wall, and live wall; code states ÔÇ£flowers/seasons and dead wall are omittedÔÇØ and treats all undealt tiles as `remaining`.  
   **why it matters:** Wall exhaustion timing, replacement draws, dead-wall bonuses, and setup fidelity can differ from the rulebook.  
   **suggested next action:** Decide whether this benchmark is explicitly ÔÇ£no flowers/no dead wallÔÇØ; otherwise model dead/live wall split and setup dice/break.

2. **severity: major**  
   **evidence:** Rulebook lists possible reactions by other players after a discard; code resolves reactions sequentially by seat with `reaction_pos`.  
   **why it matters:** If multiple players can react, the rulebookÔÇÖs listed order may imply priority, but the code lets earlier seat-order reactions occur before later Mahjong claims.  
   **suggested next action:** Clarify discard-claim priority and implement deterministic conflict resolution.

3. **severity: major**  
   **evidence:** Code comments omit scoring items: flowers/seasons, dead-wall win, exact ÔÇ£only possible tile,ÔÇØ Null-Punkte-Hand, Kang-on-Kang, ninth East win, etc. Loser scoring is heuristic via hidden pongs/pairs.  
   **why it matters:** Returns are central to benchmarking, and many rulebook scoring categories affect payouts.  
   **suggested next action:** Either limit the benchmark to simplified scoring or add state needed for all scoring table entries.

4. **severity: minor**  
   **evidence:** Rulebook has full wind rounds, East rotation, and multi-game partie structure; code fixes `p0=Osten`, round wind `Osten`, and one hand only.  
   **why it matters:** Some scoring/limit hands depend on round wind or repeated East wins. For `oneshot`, this may be acceptable if documented.  
   **suggested next action:** Document one-shot scope clearly or add round/wind state.

5. **severity: minor**  
   **evidence:** Code invents labels `Farbe3`, `Drache1`, `Drache2` because text lacks full tile names.  
   **why it matters:** Action names may not match intended rulebook/image labels.  
   **suggested next action:** Use exact labels from source images or explicitly approve placeholders.

6. **severity: question**  
   **evidence:** Rulebook says flowers/seasons can be removed to simplify; code always removes them.  
   **why it matters:** This changes components and scoring but may be a valid variant.  
   **suggested next action:** Human should confirm whether the target variant excludes flowers/seasons.

### 3. Rule coverage review

| rule area | covered correctly / partially covered / missing / unclear | evidence | notes |
|---|---|---|---|
| setup | partially covered | `FULL_WALL`, `DEAL_TARGET_SEQUENCE`; no dice, wall break, dead wall, flowers/seasons | Deal counts are close; physical wall/dead wall omitted. |
| player count and turn order | partially covered | `NUM_PLAYERS = 4`, winds fixed East/South/West/North, `next_player` | Basic counterclockwise order modeled; random wind assignment/rotation omitted. |
| legal actions | partially covered | discard, claim chi/pong/kang, declare Mahjong, declare Kang | Core actions present; flower replacement and reaction priority unclear/missing. |
| state transitions | partially covered | phases `deal`, `draw_live`, `discard`, `reaction`, `kang_reaction`, `terminal` | Good one-hand flow; dead wall and full round progression absent. |
| terminal conditions | mostly covered | Mahjong terminal; wall exhausted after last discard/pass | Uses all undealt tiles as live wall, so exhaustion timing may differ. |
| scoring/returns | partially covered | settlement logic, many meld scores/doubles/limit hands | Important scoring categories omitted or approximated. |
| rendering/action names | covered correctly | stable names like `discard:p0:Bambus-1`, deterministic `render` | Uses invented tile labels where rule text lacks names. |
| chance | partially covered | explicit chance actions for deal/draw with probabilities | Does not model dice, wall break, wind selection. |
| hidden information | mostly covered | `information_state` hides opponent hands and wall composition | `render` is full debug state, acceptable if documented. |
| simultaneous/conflict reactions | unclear/missing | sequential `reaction_pos` handling | Needs clarification if multiple players can claim same discard. |

### 4. Unsupported assumptions or invented rules

- **Risky:** Fixed one-shot game with `p0=Osten`, `p1=Sueden`, `p2=Westen`, `p3=Norden`, round wind always East.
- **Risky:** No dice, wall break, dead wall, or wall-side structure; all undealt tiles are treated as the live wall.
- **Risky:** Flowers/seasons are always omitted, not optional/configurable.
- **Risky:** Discard reactions are resolved sequentially by seat order instead of an explicit priority system.
- **Risky:** Non-winning playersÔÇÖ scores are inferred heuristically from exposed melds, hidden pongs, and pairs.
- **Risky:** Several scoring categories are omitted because required state is not tracked.
- **Harmless/necessary:** Placeholder names for third suit and two dragons due incomplete text labels.
- **Harmless/likely acceptable:** Best scoring decomposition is chosen for a winning hand.
- **Harmless if documented:** `render` exposes full state while `information_state` gives player-visible state.
- **Unclear:** Self-Mahjong declaration is optional; complete hands may still discard.

### 5. Missing scenario tests

- Initial deal count: after deterministic `chance:deal:*` sequence, verify p0 has 14 tiles, p1-p3 have 13, current player is p0.
- Right-neighbor Chi only: after `discard:p0:Bambus-3`, verify only p1 can use `claim:p1:chi:Bambus-1+Bambus-2+Bambus-3`.
- Claim conflict: p0 discards a tile where p1 can Chi and p2 can Mahjong; verify expected priority once clarified.
- Pong turn order: `discard:p0:Drache1`, `pass:p1`, `claim:p2:pong:Drache1`, then p2 discards; if unclaimed, p3 should draw next.
- Last-wall exhaustion: with one live tile, `chance:draw:p0:normal_draw:Kreis-1`, `discard:p0:Kreis-1`, all pass => terminal draw with zero returns.
- Concealed Kang: `kang:p0:concealed:Bambus-2`, replacement draw, verify concealed Kang scoring state.
- Rob Kang: `kang:p0:extend_pong:Bambus-2`, then `rob_kang:p1:mahjong:chi:Bambus-1+Bambus-2+Bambus-3`; verify p1 wins and p0 retains only open Pong.
- Seven pairs / thirteen wonders scoring tests using `claim:*:mahjong:special:*`.
- Settlement tests matching simplified versions of the rulebook examples, especially East double payments.
- Information-state test: opponent hands and wall composition must not appear in `information_state`.

### 6. Open questions for the human

1. Is the target variant explicitly without flowers/seasons?
2. Should the dead wall still exist when flowers/seasons are removed?
3. What is the exact priority when multiple players can react to the same discard?
4. Is this benchmark intended to model only one hand, or full wind rounds and East rotation?
5. Are full scoring tables required, including rare limit hands and all bonuses?
6. What exact tile labels should be used for the third suit and unnamed dragons?

### 7. Machine-readable summary

```text
score: 0.60
confidence: medium
critical_issues: 0
major_issues: 3
minor_issues: 2
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```
