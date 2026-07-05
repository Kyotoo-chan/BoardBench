### 1. Score

score: 0.58  
confidence: medium

The implementation is playable and covers many core Mah-Jongg mechanics from the provided rulebook: four players, concealed hands, discard claims, Pong/Tschi/Kang, Mah-Jongg terminal states, hidden information, and much of the scoring table. However, it makes several risky abstractions around wall construction, dead wall replacement, setup dice, round/wind progression, and claim/win priority. The scoring logic is ambitious but contains likely rule-fidelity gaps and context-dependent bonuses that are guessed rather than fully supported by the rule text.

### 2. Top findings

- severity: major  
  evidence: Rulebook section 3 defines wall construction, dice break, dead wall, living wall, and replacement tiles from the dead wall. Code states that dice and exact wall geometry are abstracted, and replacement draws come from the same remaining multiset.  
  why it matters: Dead-wall vs live-wall source affects legal replacement draws and scoring bonuses such as “Schlussziegel von der toten Mauer”.  
  suggested next action: Model live wall and dead wall as separate ordered chance pools, or explicitly mark this as an unsupported simplified variant.

- severity: major  
  evidence: Rulebook section 6 defines a Partie of four wind rounds, each with four to sixteen games, dealer continuation, and wind rotation. Code models only one deal and fixes player winds as `(0, 1, 2, 3)`.  
  why it matters: Round wind, seat wind, East continuation, and “Neunmal Mah-Jongg” depend on multi-game state.  
  suggested next action: Either implement match/round state or narrow the benchmark target explicitly to a single isolated Spiel.

- severity: major  
  evidence: Rulebook says the discarded tile can be used for “Pong zum Mah-Jongg”, “Tschi zum Mah-Jongg”, or “Paar zum Mah-Jongg”. Code exposes only generic `mahjong:discard:pX:<tile>` and does not record whether the winning tile completed Pong, Tschi, or pair.  
  why it matters: Some scoring depends on the final tile completing a pair or other contextual conditions; benchmark traces also lose important action semantics.  
  suggested next action: Encode the winning completion type in legal actions and terminal state.

- severity: major  
  evidence: Rulebook says bonus tiles are replaced by a tile from the dead wall. Code default excludes bonus tiles and, when enabled, draws replacement tiles from the same `remaining` multiset with `draw_source` usually `"wall"`.  
  why it matters: Bonus-tile handling changes wall exhaustion, replacement flow, and dead-wall scoring.  
  suggested next action: Add a separate dead-wall source and deterministic replacement phase for flowers/seasons.

- severity: minor  
  evidence: Rulebook does not list all dragon labels or the third suit label. Code invents `drache-rot`, `drache-gruen`, `drache-weiss`, and `zeichen`.  
  why it matters: Mostly harmless for playability, but action names and rendered states are not directly grounded in provided labels.  
  suggested next action: Keep these as explicit assumptions, or use neutral labels like `drache-1..3` and `farbe-3`.

- severity: question  
  evidence: Rulebook lists claim reactions in an order but does not fully specify tie-breaking among multiple Mah-Jongg claimants. Code uses seating order from the discarder’s right within priority classes.  
  why it matters: Different tie resolution can change winners in contested discard states.  
  suggested next action: Ask the human whether seating-order tie-break is acceptable.

### 3. Rule coverage review

| rule area | covered correctly / partially covered / missing / unclear | evidence | notes |
|---|---|---|---|
| setup | partially covered | Code deals 13 tiles to each player and 14 to East through chance draws. | Dice, wall break, dead wall geometry, and exact wall order are abstracted. |
| player count and turn order | partially covered | `NUM_PLAYERS = 4`; right neighbor is `(player + 1) % 4`; East starts. | Full wind rotation and multi-game Partie are missing. |
| legal actions | partially covered | Supports discard, self-draw Mah-Jongg, claim Pong/Tschi/Kang, concealed/additional Kang, robbing Kang. | Winning claim actions do not specify whether tile completes Pong/Tschi/pair. |
| state transitions | partially covered | Discard leads to claim phase or next player draw; Kang leads to replacement draw. | Replacement source is not faithful to dead wall; wall exhaustion is simplified. |
| terminal conditions | partially covered | Ends on Mah-Jongg or empty wall after final discard opportunity. | Single-deal terminal only; repeated game/round structure missing. |
| scoring/returns | partially covered | Implements many table values, doubles, limit hands, East double payments. | Several bonuses require context not reliably tracked; non-winner scoring decomposition is simplified. |
| rendering/action names | partially covered | Stable render and canonical action names exist. | Some names use invented English labels and omit completion type for Mah-Jongg claims. |
| chance | partially covered | Uses explicit `chance_outcomes` for draws. | No ordered wall, no dice, no separate dead wall. |
| hidden information | partially covered | `information_state` hides other players’ hands by count. | `render` exposes full debug state, which is acceptable if used as debug only. |
| simultaneous moves | unclear/not relevant | Rulebook uses reaction opportunities, not simultaneous hidden commitments. | Sequential priority windows are a reasonable interface choice. |

### 4. Unsupported assumptions or invented rules

- Harmless convention: third numbered suit is called `zeichen`, because the rulebook does not name it explicitly.
- Harmless convention: dragon labels are red/green/white, though only green is explicitly named in the rulebook.
- Risky abstraction: dice, wall break, live wall ordering, and dead wall ordering are replaced by unordered chance draws.
- Risky abstraction: bonus replacement tiles come from the same remaining multiset rather than a modeled dead wall.
- Risky rule: claim ties within a priority class are resolved by seating order from the discarder’s right; the rulebook does not clearly define this.
- Risky scope reduction: the implementation models one `Spiel`, not the full four-round Partie with dealer continuation and wind rotation.
- Risky scoring assumption: concealed Kang counts toward “Drei verdeckte Pong”.
- Risky scoring assumption: unexposed three-of-a-kind in non-winner hands are greedily scored as concealed Pong, without proving the best scoring arrangement.
- Risky omission: “Mah-Jongg nach Ruf zu Beginn” is intentionally not implemented because the declaration procedure is unclear.
- Risky simplification: replacement draws after Kang use source `"wall"` rather than the dead wall, affecting dead-wall bonuses.

### 5. Missing scenario tests

- Initial deal: after all chance deal actions, East has 14 normal tiles and the other players have 13.
- Dead discard flow: `discard:<tile>`, all claim players `pass`, then the right neighbor enters a wall draw phase.
- Tschi restriction: only the right neighbor can claim `claim:chi`, while other players with matching sequence tiles cannot.
- Pong/Kang priority: after a discard, Mah-Jongg claims appear before Kang, Kang before Pong, and Pong before Tschi.
- Last-wall discard: after the final live-wall draw, allow only Mah-Jongg claims on the discard, then terminate if all pass.
- Robbing Kang: player extends an open Pong; another player can claim Mah-Jongg by robbing the Kang; the original meld remains only a Pong.
- Bonus tile replacement with `include_bonus_tiles=True`: drawing `blume-1` should expose it and require a replacement without increasing hand size.
- Scoring example: construct the first rulebook accounting example and compare East/South/West/North settlement totals.
- Limit hand: construct seven pairs and verify half-limit scoring.
- Action round-trip: every legal action in claim, discard, draw, and rob-Kang phases round-trips through `action_to_name` and `name_to_action`.

### 6. Open questions for the human

- Should the benchmark target be one isolated `Spiel`, or the full Partie with wind rounds and dealer rotation?
- Should wall geometry and dead-wall replacement be required for this Mahjong rulebook, or is unordered chance drawing acceptable?
- How should simultaneous or competing Mah-Jongg claims on the same discard be resolved?
- Are invented dragon and third-suit labels acceptable for canonical action names?

### 7. Machine-readable summary

```text
score: 0.58
confidence: medium
critical_issues: 0
major_issues: 4
minor_issues: 1
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```