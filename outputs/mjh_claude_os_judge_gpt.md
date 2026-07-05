### 1. Score

- `score: 0.45`
- `confidence: medium`

The implementation has a playable four-player core with chance dealing/drawing, discards, claims, Kangs, robbing a Kang, and settlement-style returns. However, it only partially implements the rulebook: scoring is incomplete and often unreliable, Chi claims have a concrete legality bug, several terminal/setup details are simplified or wrong, and many limit/end-bonus rules are missing. It is useful as a prototype but not benchmark-ready for full rule fidelity.

### 2. Top findings

1. **severity: critical**  
   **evidence:** Rulebook §8 lists many figure points, Mahjong bonuses, doublings, flowers/seasons, and numerous limit hands. Code `_value`, `_set_doublings`, and `_hand_doublings` implement only a subset and the header notes “several named limit hands are not auto-detected.”  
   **why it matters:** `returns()` is central to judging terminal states; many legal wins/hands will receive incorrect values. Non-winning hands also appear limited to one concealed scoring pair, while the examples score multiple pairs.  
   **suggested next action:** Either fully implement the scoring table and limit hands or explicitly restrict the benchmark to the implemented scoring subset.

2. **severity: major**  
   **evidence:** Rulebook says the right neighbor may use a discarded tile to complete a Tschi. Code `_can_chi()` requires `hand.get(t) >= 1` for the discarded tile itself before entering Chi stage.  
   **why it matters:** Many valid Chi claims will never be offered unless the player already has another copy of the discarded tile.  
   **suggested next action:** Fix `_can_chi()` to require only the two non-discard tiles.

3. **severity: major**  
   **evidence:** Rulebook §5 says after the last live-wall tile is drawn, the player may discard, and if that discard is not used for Mah-Jongg the game ends. Code still allows normal Pong/Kong/Chi claim stages after that discard.  
   **why it matters:** The game can continue incorrectly after the live wall is exhausted.  
   **suggested next action:** When `wall == 0` after a discard, allow only Mahjong claims, then terminal washout.

4. **severity: major**  
   **evidence:** Code handles discard wins by adding the tile to the winner’s concealed hand and calling `_win`, without recording the winning meld/source.  
   **why it matters:** Scoring can incorrectly treat the final claimed figure as concealed and misses bonuses such as last discard, robbing Kang, final tile source, or pair-completion bonuses.  
   **suggested next action:** Track win source, final tile, final meld type, and openness for scoring.

5. **severity: major**  
   **evidence:** Setup in rulebook includes wall building, dice break, dead wall, East receiving a 14th tile before play, optional flowers/seasons, and wind/round structure. Code abstracts this to 52 chance deals, then an East draw, fixed round wind East, no flowers/seasons, and `wall = pool - 14`.  
   **why it matters:** Some simplifications may be acceptable for “oneshot,” but dead-wall size/source, starting state, and bonus tiles materially affect legal states and scoring.  
   **suggested next action:** Clarify intended variant and align setup/wall counts accordingly.

6. **severity: minor**  
   **evidence:** Code invents claim priority: all Mahjong claims, then Pong/Kong, then Chi, with seat-order sequential passes. Rulebook lists reactions but does not define conflict priority.  
   **why it matters:** Multi-claim states may resolve differently than intended.  
   **suggested next action:** Add a rulebook clarification or document this as a benchmark convention.

7. **severity: minor**  
   **evidence:** Tile/action labels such as `Zeichen`, `DracheRot`, `DracheWeiss`, and suit codes are code conventions not fully defined in the text.  
   **why it matters:** Mostly harmless for stable BoardBench names, but can diverge from rulebook labels.  
   **suggested next action:** Keep stable labels, but document them as notation conventions.

### 3. Rule coverage review

| rule area | covered correctly / partially covered / missing / unclear | evidence | notes |
|---|---|---|---|
| setup | partially covered | `GameState.pool`, chance deal, `wall = sum(pool)-14` | No dice break/wall structure; East starts via draw rather than initial 14th tile; dead wall count/source unclear; flowers removed. |
| player count and turn order | partially covered | `num_players = 4`, winds mapped to players, right neighbor `(p+1)%4` | Basic four-player order exists; no full rounds, wind rotation, East retention, or random wind assignment. |
| legal actions | partially covered | Discard, Mahjong, Pong, Kong, Chi, robbing Kang implemented | Chi stage bug; claim priority invented; concealed Kong timing may be broader than rulebook. |
| state transitions | partially covered | Claim stages, draw/discard loop, Kong replacement, robbing Kang | Final winning meld/source not tracked; last-wall discard can still trigger non-Mahjong claims. |
| terminal conditions | partially covered | Terminal on Mahjong or wall exhaustion | Misses “last discard only usable for Mahjong” detail; repeated washout game not modeled. |
| scoring/returns | partially covered / missing | Settlement logic resembles examples; `_value()` implements subset | Many scoring bonuses, doublings, flowers, and limit hands missing; discard wins and nonwinner scoring can be wrong. |
| rendering/action names | mostly covered | Stable string actions, `render`, `action_to_name` identity | Render reveals full hidden hands but notes it is debug view. |
| chance handling | partially covered | `chance_outcomes()` for deal/draw from tile pool | No explicit wall order/dice/dead-wall composition; probabilities may be acceptable abstraction if clarified. |
| hidden information | partially covered | `information_state()` hides other hands by count | Full `render()` reveals all hands; acceptable if render is debug-only. |
| simultaneous moves | unclear / not relevant | Sequential claim resolution | Rulebook reactions are listed, but conflict priority is not specified. |
| flowers/seasons | missing by assumption | No flower/season tile types | Rulebook says they may be removed to simplify; variant must clarify. |
| limit hands | partially covered | Detects seven pairs, thirteen orphans, all honors, all terminals | Most named limit hands are not detected. |

### 4. Unsupported assumptions or invented rules

- **Risky:** No flowers/seasons are included, despite rulebook scoring and replacement rules for them. This is only safe if the benchmark variant explicitly removes them.
- **Risky:** Single hand only, fixed round wind East, fixed seat winds by player index, no wind draw/rotation/rounds.
- **Risky:** Limit is fixed to `500` from the example, although the rulebook describes an agreed limit.
- **Risky:** Dead wall is modeled as 14 single unseen tiles; the rulebook wording about “vierzehn Doppelziegel” may imply a different count.
- **Risky:** Claim priority and tie-breaking are invented.
- **Risky:** Scoring uses best inferred decomposition rather than fully tracked declared/winning figures.
- **Risky:** Winning discard tile is treated as part of concealed hand for scoring.
- **Risky:** Normal non-Mahjong claims are allowed after the final live-wall discard.
- **Risky:** Concealed Kong can be declared whenever four identical tiles are in hand during discard phase, not clearly limited to drawing the fourth tile.
- **Harmless convention:** Stable internal tile labels such as `Bambus1`, `Kreis5`, `WindOst`.
- **Harmless convention:** `render()` is a full-truth debug view, while `information_state()` is player-filtered.
- **Harmless convention:** Zero-sum numeric returns represent settlement payments.

### 5. Missing scenario tests

- Chi claim without holding the discarded tile: P0 discards `Kreis5`; P1 has `Kreis3,Kreis4` but no `Kreis5`; legal actions should include `Chi:Kreis3+Kreis4+Kreis5`.
- Last-wall discard: after the final live-wall draw, P0 discards a tile; if no player can Mahjong, no Pong/Kong/Chi should be legal and the state should become washout.
- Discard win scoring: construct a hand where P1 wins from P0’s discard by completing a Pong/Chi/pair; assert the final figure is not scored as fully concealed.
- Robbing Kang: P0 has open Pong of `Bambus2`, declares `AddedKong:Bambus2`, P1 can Mahjong; assert P0 remains with open Pong and P1 wins.
- Rulebook settlement examples: construct terminal states matching both examples and assert returns `+456,-182,-152,-122` and `-1036,+1418,+192,-574`.
- Nonwinner multiple pairs: construct a nonwinner with both dragon pair and own-wind pair; assert both pair bonuses score if rulebook expects that.
- Limit hands not implemented: test named hands such as green hand, nine lanterns, four Kangs, and hidden treasure.
- Setup/wall count: after dealing, verify East has the rulebook-required starting hand and the live/dead wall counts match the clarified interpretation.
- Flowers/seasons, if included: drawing a flower/season should expose it, replace from dead wall, and affect scoring.

### 6. Open questions for the human

- Does the “oneshot” variant intentionally omit rounds, wind rotation, East retention, and repeated washout games?
- Are flowers and seasons included, or should the benchmark always use the simplified set without them?
- What is the exact agreed limit value, and should it always be 500?
- How should the dead wall size be interpreted from the rulebook text?
- What priority applies when multiple players can claim the same discard?
- Must the benchmark require the full scoring/limit-hand table, or only a reduced core subset?

### 7. Machine-readable summary

```text
score: 0.45
confidence: medium
critical_issues: 1
major_issues: 5
minor_issues: 2
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```
