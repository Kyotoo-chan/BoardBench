### 1. Score

score: 0.45  
confidence: medium

The implementation captures a simplified four-player Mahjong hand with hidden hands, chance dealing/drawing, discards, chi/pong/kang claims, and basic Mah-Jongg detection. However, it omits or abstracts major rulebook mechanics, especially the detailed scoring/settlement system, dead/live wall setup, winds/round progression, bonus tiles, and realistic claim/pass resolution. It is playable as a reduced toy environment but not benchmark-ready for the provided rules.

### 2. Top findings

1. severity: critical  
   evidence: Rulebook section 5 and scoring tables define hand values, doubles, limits, East double payments, and pairwise settlement; code `returns()` only gives `[3, -1, -1, -1]` style winner utility.  
   why it matters: The rulebook’s endgame accounting is central and cannot be benchmarked.  
   suggested next action: Implement rulebook scoring or explicitly scope the environment to winner-only play.

2. severity: major  
   evidence: Rulebook setup creates live and dead walls after dice/wall break; code uses a flat `Counter` wall and all 136 non-bonus tiles are live-drawable.  
   why it matters: Wall exhaustion timing, replacement behavior, and last-tile bonuses depend on live/dead wall structure.  
   suggested next action: Model wall order, break, dead wall, and live wall count.

3. severity: major  
   evidence: Rulebook reactions involve other players choosing whether to take a discard; code collapses this to a single `SIMULTANEOUS` action such as `claim_pong` or `pass_all`.  
   why it matters: It removes individual pass/claim decisions and any priority/conflict resolution.  
   suggested next action: Define claim priority/pass protocol from the rules or document the abstraction.

4. severity: major  
   evidence: Rulebook includes many limit hands and detailed doubles; code only recognizes standard hand, seven pairs, and thirteen wonders for terminal detection, with no limit scoring.  
   why it matters: Many winning hands cannot be valued correctly.  
   suggested next action: Add limit-hand detection and score calculation.

5. severity: minor  
   evidence: Rulebook allows removing flowers/seasons for simplification; code omits them.  
   why it matters: Acceptable only if this variant intentionally excludes bonus tiles, but this should be explicit.  
   suggested next action: Document “no flowers/seasons” as a variant assumption.

### 3. Rule coverage review

| rule area | covered correctly / partially covered / missing / unclear | evidence | notes |
|---|---|---|---|
| setup | partially covered | Code creates 4 copies of suited, wind, and dragon tiles and deals 13/13/13/13 plus East 14th | No dice, wall break, dead wall, ordered wall, or optional flowers/seasons |
| player count and turn order | partially covered | `PLAYERS = 4`, winds fixed as East/South/West/North, `_right_neighbor` advances counterclockwise | Wind assignment and round/seat rotation are fixed or absent |
| legal actions | partially covered | Supports discard, self Mah-Jongg, chi/pong/kang claims, concealed/extended kang | Claim/pass priority and individual reaction choices are abstracted |
| state transitions | partially covered | Draw-discard-claim loop mostly works; claimed discard removed from discard pile | Robbed kang terminal state does not transfer/remove the robbed tile; wall/dead-wall transitions inaccurate |
| terminal conditions | partially covered | Ends on Mah-Jongg or after final live tile discard is not used | Live wall size is wrong because dead wall is not modeled |
| scoring/returns | missing | `returns()` uses fixed win/loss utility | Does not implement point tables, doubles, limits, East doubling, or settlement |
| rendering/action names | mostly covered | Stable names like `discard:kreis_1`, `claim:p1:pong:ost` | Some tile labels are invented, e.g. `farbe3`, `drache1` |
| chance handling | partially covered | Explicit `chance_outcomes()` for deal/draw/replacement | Random draw from unordered multiset rather than shuffled wall with break/dead wall |
| hidden information | partially covered | `information_state()` hides opponents’ hands | Full `render()` reveals all hands, acceptable as debug if documented |
| simultaneous/reaction handling | partially covered | `current_player()` returns `SIMULTANEOUS` for claims | Legal actions are not joint actions and do not model individual responses |

### 4. Unsupported assumptions or invented rules

- Harmless/risky: Flowers and seasons are omitted. This is allowed as a simplification by the rulebook, but the code should state it explicitly.
- Risky: All non-bonus tiles remain in a single live wall; the dead wall is ignored.
- Risky: Draws/deals are modeled as sampling from a multiset rather than from an ordered shuffled wall after a dice-determined break.
- Risky: Claim resolution is a single selected action or `pass_all`, not separate player decisions.
- Risky: Winner utility is fixed at +3/-1 rather than using rulebook scoring.
- Risky: Round wind is always East; wind/round rotation is absent.
- Harmless/unclear: Third suit is named `farbe3`; dragon names are partly invented because the rulebook text does not list all labels clearly.
- Risky: Four identical concealed tiles may be declared as a concealed kang whenever present, not only when the fourth tile was drawn.
- Risky: Seven pairs allows four identical tiles to count as two pairs; the code notes this ambiguity.

### 5. Missing scenario tests

- Initial deal sequence: after all `chance:deal:*` actions, East has 14 tiles and others have 13.
- Basic draw/discard/pass: East discards, all pass, South draws, then discards.
- Claim chi only by right neighbor: discard suited middle tile and verify only the right neighbor can `claim_chi`.
- Claim pong/kang by non-discarders: verify players with two or three matching tiles can claim.
- Last live-wall tile: after final draw and discard, only Mah-Jongg claims are legal; otherwise terminal draw.
- Self-draw Mah-Jongg: construct a complete hand and verify `mahjong:self` ends the game.
- Robbing the kang: extend an open pong and verify another player can win by `rob:pX:mahjong:<tile>`.
- Scoring regression: construct a known scoring-table example from section 10 and compare returns/payments once scoring is implemented.
- Limit hand tests: seven pairs, thirteen wonders, four kangs, pure honors, and other listed limit hands.

### 6. Open questions for the human

- Should this benchmark require full rulebook scoring, or is winner-only utility acceptable for the `oneshot` variant?
- Are flowers/seasons intentionally excluded?
- Should the dead wall and dice-based wall break be modeled explicitly?
- What claim priority should apply when multiple players can use the same discard?

### 7. Machine-readable summary

```text
score: 0.45
confidence: medium
critical_issues: 1
major_issues: 4
minor_issues: 1
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```
