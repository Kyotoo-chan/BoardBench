### 1. Score

score: 0.60  
confidence: medium

The implementation is playable and models a substantial one-hand Mahjong environment: four players, hidden hands, stochastic deal/draws, discards, Chi/Pong/Kang claims, Mahjong claims, robbing a Kang, terminal draw, and a broad scoring attempt. It is not benchmark-ready against the provided rulebook because it omits or simplifies several rule areas that affect legal play and scoring, especially flowers/seasons/dead wall, wind progression, claim priority, last-wall behavior, and multiple scoring details.

### 2. Top findings

- severity: major  
  evidence: Rulebook says flowers/seasons are drawn, exposed, and replaced from the dead wall; code states “flowers/seasons and dead wall are omitted.”  
  why it matters: This removes a full rule section and several scoring/doubling conditions.  
  suggested next action: Either make the no-bonus-tile variant explicit in config/docs, or implement bonus tiles and dead-wall replacement.

- severity: major  
  evidence: Rulebook says after the last live-wall tile is discarded, the game ends unless that discard completes Mahjong. Code still allows non-winning `claim_pong` and `claim_chi` when `remaining` is empty.  
  why it matters: This can continue play illegally after the wall should end.  
  suggested next action: In final-discard reaction states, allow only Mahjong claims and pass.

- severity: major  
  evidence: Rulebook lists reactions in priority-like order: Mahjong claims, Kang, Pong, Chi. Code resolves reactions sequentially by seating order.  
  why it matters: If multiple players can claim the same discard, the implementation may award the tile to the wrong player or claim type.  
  suggested next action: Clarify claim priority from the human/rule source, then encode priority before applying claims.

- severity: major  
  evidence: Rulebook has four rounds, East retention/loss, seat-wind rotation, and prevailing wind. Code fixes `p0=Osten` and `round_wind=Osten` for one hand.  
  why it matters: Seat wind and round wind affect scoring and long-game structure.  
  suggested next action: Document that this is a single-hand model, or add round/seat progression if the benchmark should cover a full Partie.

- severity: minor  
  evidence: Rulebook does not name the third suit or two dragons in text; code invents `Farbe3`, `Drache1`, `Drache2`, and action labels like `reddragon`/`whitedragon`.  
  why it matters: Action names and render output may not match the source artifact cleanly.  
  suggested next action: Keep neutral labels consistently, or derive labels from page images/brief if available.

### 3. Rule coverage review

| rule area | covered correctly / partially covered / missing / unclear | evidence | notes |
|---|---|---|---|
| setup | partially covered | Code has 136 non-bonus tiles, chance deal, 13/13/13/14 hands | Dice, wall break, dead wall, bonus-tile setup omitted |
| player count and turn order | partially covered | `NUM_PLAYERS = 4`, `next_player()` cycles p0-p1-p2-p3 | One-hand fixed seats; no wind drawing or rotation |
| legal actions | partially covered | Discard, Chi, Pong, Kang, Mahjong, pass modeled | Claim priority and final-discard restrictions are problematic |
| state transitions | partially covered | Claimed tile leads claimant to discard; draws are chance nodes | Open/closed status and Kang replacement partly simplified |
| terminal conditions | partially covered | Mahjong and wall exhaustion terminal states exist | Last-wall discard can still be claimed for non-Mahjong |
| scoring/returns | partially covered | Winner payout, East doubling, loser differences, many hand scores | Several bonuses/limit hands omitted or approximated; self-draw completion details not tracked |
| rendering/action names | partially covered | Stable render and round-trippable names implemented | Some names use invented labels and punctuation suffixes |
| chance | covered correctly | Deal/draw actions and probabilities from remaining tile counts | Wall order is abstracted as tile draws, not a physical wall |
| hidden information | partially covered | `information_state` hides other hands and wall contents | Full `render` reveals all state, acceptable as debug if documented |
| simultaneous moves | unclear/not applicable | No simultaneous API | Rulebook reactions may need priority handling rather than simultaneous moves |

### 4. Unsupported assumptions or invented rules

- Harmless convention: fixed single-hand seat assignment `p0=Osten`, `p1=Sueden`, `p2=Westen`, `p3=Norden`.
- Risky simplification: flowers, seasons, and dead wall are omitted despite explicit rulebook coverage.
- Risky simplification: physical wall construction, dice rolls, wall break, and dead-wall/live-wall split are abstracted away.
- Risky invented rule: discard reactions are handled in seating order rather than by a specified claim priority.
- Risky invented rule: after the last live-wall discard, non-Mahjong claims can still be legal.
- Harmless but externally colored labels: `reddragon`, `whitedragon`, and `character` are used although the text does not provide those names.
- Partial scoring assumption: several scoring bonuses are omitted because the implementation does not track the final tile’s exact role, dead-wall source, flowers/seasons, “only possible tile,” or multi-game East streaks.

### 5. Missing scenario tests

- Final live-wall discard: construct a state with `remaining=()`, a discard that another player can Chi/Pong but not Mahjong, then assert only `pass` or Mahjong claims are legal and pass ends the game.
- Claim priority conflict: construct one discard where one player can Pong and another can Mahjong, then verify the intended priority once clarified.
- Robbing a Kang: create an open Pong plus matching drawn tile, allow another player to complete Mahjong, then assert the declarer keeps only the open Pong and the game terminates.
- East initial Mahjong: after initial deal, make East complete and apply `mahjong_self...`; assert Heaven blessing/limit handling.
- Last live-wall win: draw the final `Kreis-1`, declare Mahjong, and verify the matching limit/doubling behavior from the rule text.
- Loser settlement example: encode a simplified scoring state matching the provided Abrechnungsbeispiel and compare returns.

### 6. Open questions for the human

- Should this BoardBench environment model one hand only, or the full four-round wind/seat progression?
- For simultaneous discard reactions, should Mahjong always outrank Kang/Pong/Chi, and how should ties between multiple Mahjong callers be resolved?
- Should flowers/seasons be included, or is the intended benchmark variant explicitly the simplified game without them?

### 7. Machine-readable summary

```text
score: 0.60
confidence: medium
critical_issues: 0
major_issues: 4
minor_issues: 1
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```