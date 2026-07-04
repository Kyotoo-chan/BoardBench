### 1. Score

score: 0.55  
confidence: medium

The implementation is a playable single-hand Mah-Jongg model with many core mechanics represented: four players, winds, hands, meld claims, kongs, robbing the kang, bonus tiles, terminal draw handling, and a substantial scoring attempt. However, it makes several benchmark-relevant assumptions not specified by the packet, especially deterministic setup instead of explicit chance, sequential claim resolution without a rule priority model, incomplete round/wind progression, and partial or fragile scoring for non-winning hands and special cases.

### 2. Top findings

1. severity: major  
   evidence: The rulebook setup uses shuffled face-down tiles and dice to determine the wall break. The code uses `_deterministic_mix()` and exposes no `chance_outcomes()`.  
   why it matters: This removes the stochastic setup and makes wall/hand information deterministic, which materially changes a hidden-information tile game.  
   suggested next action: Either implement explicit chance nodes for shuffle/deal/wall draw, or document the environment as a deterministic simplified subgame.

2. severity: major  
   evidence: The rulebook lists reactions in priority-like order, including Mah-Jongg claims before ordinary Kang/Pong/Tschi. The code asks responders one at a time via `_next_responder()` and lets the current responder take ordinary claims before later players can claim Mah-Jongg.  
   why it matters: Claim priority can decide who wins a hand.  
   suggested next action: Clarify and encode claim priority, especially Mah-Jongg over ordinary claims.

3. severity: major  
   evidence: The rulebook includes a full wind/round structure: four rounds, East rotation, East continuing after wins, and max repeated East wins. The code only models one hand with fixed `round_wind="Ost"` and fixed `place_winds=WINDS`.  
   why it matters: Round wind and seat wind affect scoring and the longer game structure.  
   suggested next action: Decide whether BoardBench should score only one hand or the full Partie; if one hand, document that scope explicitly.

4. severity: major  
   evidence: Rulebook settlement scores all players’ hands before pairwise payments. Code `_score_partial_hand()` greedily finds concealed pongs and only one best pair. The rulebook examples include multiple scoring pairs for one non-winning hand.  
   why it matters: Non-winner payments can be wrong even if the winner is detected correctly.  
   suggested next action: Add deterministic scoring tests from both printed settlement examples.

5. severity: major  
   evidence: Some printed scoring cases are omitted or heuristic: “Schlussziegel ist einzig möglicher Ziegel” is not implemented; “Neunmal Mah-Jongg” is impossible without match state; some first-discard/initial win conditions are inferred from history length.  
   why it matters: Returns can diverge on exactly the rare hands and edge cases the rulebook emphasizes.  
   suggested next action: Maintain an explicit supported-scoring checklist and mark unsupported bonuses as absent in output.

6. severity: minor  
   evidence: Code invents labels `Farbe3`, `DracheA`, and `DracheB` because the extracted rule text does not show all tile names.  
   why it matters: Action names and render output may not match the rulebook images or later comparison artifacts.  
   suggested next action: Recover tile labels from rulebook images or document the placeholder mapping.

7. severity: minor  
   evidence: `include_bonus_tiles` defaults to `False`, while the rulebook describes both playing with and without flowers/seasons.  
   why it matters: Different setup sizes and scoring rules apply depending on this mode.  
   suggested next action: Make the chosen benchmark mode explicit in the game metadata or tests.

8. severity: minor  
   evidence: `render()` reveals all hands and wall counts, while `information_state()` hides other players’ hands.  
   why it matters: Full debug render is useful for checks but not player-visible in a hidden-information game.  
   suggested next action: Document `render()` as omniscient debug output and use `information_state()` for player-facing evaluation.

### 3. Rule coverage review

| rule area | covered correctly / partially covered / missing / unclear | evidence | notes |
|---|---|---|---|
| setup | partially covered | `initial_state()` deals 13/14 tiles and creates live/dead walls | Dice, random shuffle, and wall break are replaced by deterministic setup |
| components | partially covered | suits, winds, dragons, flowers, seasons are modeled | Some labels are placeholders due missing/OCR text |
| player count and turn order | partially covered | `NUM_PLAYERS = 4`, `_next_player()` follows East/South/West/North order | No full round or East-rotation lifecycle |
| legal actions | partially covered | discard, draw, claim, pong, tschi, kang, mahjong actions exist | Claim priority across multiple responders is likely wrong |
| state transitions | partially covered | draw/discard/claim phases are implemented | Deterministic wall and sequential claims simplify the rulebook flow |
| terminal conditions | mostly covered | Mah-Jongg terminal and wall-empty draw are represented | Last-discard-after-last-draw behavior is reasonably modeled |
| scoring/returns | partially covered | Many point tables, doubles, limit hands, and East double payments are attempted | Non-winning hand scoring and several edge bonuses are incomplete |
| rendering/action names | mostly covered | Stable string actions and deterministic render | Placeholder tile names reduce rulebook fidelity |
| chance | missing | No `chance_outcomes()`; deterministic wall | Rulebook requires shuffle/dice/random wall draws |
| hidden information | partially covered | `information_state()` hides other hands | Full state still contains all hidden information, which is acceptable internally |
| simultaneous moves | unclear/not relevant | No simultaneous API | Rulebook reactions are not simultaneous, but competing claims need priority handling |

### 4. Unsupported assumptions or invented rules

- Risky: deterministic tile order and deterministic setup replace the rulebook’s shuffle and dice.
- Risky: claim conflicts are resolved by seating order from the discarder, not by a complete priority table.
- Risky: the environment models one hand only, not the full four-round wind structure.
- Risky: non-winning partial hand scoring uses a simplified greedy interpretation.
- Risky: default play excludes flowers/seasons even though the rulebook describes both modes.
- Risky: `limit=500` is used as a default from the example, while the rulebook says the limit is agreed.
- Risky: several limit/bonus detections are inferred from state history rather than explicit rule events.
- Harmless convention: action names such as `discard:<tile>` and `claim:pong:<tile>` are invented but clear.
- Harmless convention: placeholder labels for missing tile names are documented, though they should be replaced if page images provide the real labels.
- Harmless convention: omniscient `render()` is useful for BoardBench inspection if clearly treated as debug output.

### 5. Missing scenario tests

- Printed scoring example 1: construct the four displayed hands and assert final returns `+456, -182, -152, -122`.
- Printed scoring example 2: construct the four displayed hands with limit 500 and assert final returns `-1036, +1418, +192, -574`.
- Claim priority: after `discard:<tile>`, create a state where one responder can `claim:pong:<tile>` and another can `claim:mahjong:<tile>`; verify Mah-Jongg priority.
- Tschi restriction: verify only the right neighbor of the discarder can use `claim:tschi:<sequence>`.
- Robbing the kang: use `declare:kang:Bambus-2:extend` followed by `mahjong:rob-kang:Bambus-2`.
- Last wall tile: set one live tile, run `draw:live`, then `discard:<tile>`, then three `pass` actions, and assert terminal draw.
- Bonus replacement: with flowers/seasons enabled, draw `Blume1` and verify it moves to bonus and is replaced from the dead wall.
- Non-winner scoring: construct a hand with both a dragon pair and own-wind pair and verify both score where applicable.
- Seven pairs and thirteen wonders: assert both are recognized as special hands and scored at the expected limit/half-limit.
- Concealed vs open scoring: compare identical pongs/kangs marked open and concealed.

### 6. Open questions for the human

- Should this benchmark environment model a single hand only, or the full Partie with round winds and East rotation?
- Should stochastic setup be represented as explicit chance nodes, or is deterministic setup acceptable for this experiment phase?
- What exact priority order should apply when multiple players can claim the same discard?
- What are the intended canonical names for the third suit and the two unnamed dragons?
- Should the pilot benchmark use flowers/seasons by default?

### 7. Machine-readable summary

```text
score: 0.55
confidence: medium
critical_issues: 0
major_issues: 5
minor_issues: 3
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```