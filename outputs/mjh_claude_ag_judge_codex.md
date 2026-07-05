### 1. Score

score: 0.55  
confidence: medium

The implementation is playable and covers a substantial single-hand draw/discard/claim loop, explicit chance, hidden hands, basic win detection, and some settlement logic. However, several rulebook areas are partial or materially wrong: reaction turn ownership, last-wall terminal behavior, full Partie/wind rotation, flowers/seasons, dead-wall details, and many scoring/limit-hand rules. These issues make it useful as a prototype but not yet benchmark-ready.

### 2. Top findings

severity: major  
evidence: In `current_player`, `REACT` and `ROB` phases return `state.current`, but `_apply_discard` leaves `state.current` as the discarder while `legal_actions` reads `pending["claimants"][idx]`.  
why it matters: The acting player during reactions/robbery is misreported, so hidden-information views and benchmark action attribution can be wrong.  
suggested next action: Return the pending claimant in `current_player` for `REACT`/`ROB`, or update `state.current` when entering those phases.

severity: major  
evidence: Rulebook section 5 says after the last living-wall tile is drawn, the player may discard, and if that discard is not used for Mah-Jongg the game ends. `_apply_discard` still offers normal `pong`, `kong`, and `chi` claims.  
why it matters: The game can continue through non-winning claims after the wall should be exhausted.  
suggested next action: Detect the final-discard window and allow only `mahjong:claim:<tile>` reactions before ending as a draw.

severity: major  
evidence: Rulebook sections 8-11 include many scoring bonuses, doubling cases, and limit hands. Code comments acknowledge only a subset is implemented; missing examples include flowers/seasons, several special limit hands, last discard, dead wall, last wall tile, only possible tile, Kang-on-Kang, and robbery doubling.  
why it matters: `returns` are a central benchmark output and can differ substantially from the rulebook.  
suggested next action: Add explicit scoring flags for win source/context and implement or deliberately mark each table row unsupported.

severity: major  
evidence: Rulebook section 6 defines a Partie of four wind rounds with seat-wind rotation. Code explicitly scopes itself to one `Spiel` with fixed seats.  
why it matters: If the benchmark target is the whole rulebook game, long-term wind/round state and East retention are missing.  
suggested next action: Decide whether BoardBench’s Mahjong target is one deal or a full Partie; document that scope in the prompt/artifact.

severity: minor  
evidence: `_apply_react` adds claimed tiles to melds but does not remove or mark the tile in `discards` / `discard_order`.  
why it matters: Rendered public state can show the same tile as both discarded and claimed, hurting side-by-side trace inspection.  
suggested next action: Mark claimed discards or move them from discard history into a claimed-discard record.

severity: question  
evidence: The rulebook lists reactions but does not clearly define priority. Code assumes Mah-Jongg > Kong/Pong > Chi, ties by nearest counter-clockwise player.  
why it matters: Competing claims affect legal actions and game trajectory.  
suggested next action: Ask the human to confirm claim priority or annotate it as an implementation convention.

severity: question  
evidence: Code infers a third suit label `Z` and two unnamed dragon labels `Da`/`Db` from the rulebook structure.  
why it matters: The inferred tile set is plausible from the text, but action/render labels may not match the original visual rulebook.  
suggested next action: Confirm canonical labels for the unnamed suit and dragons from the source material.

### 3. Rule coverage review

| rule area | covered correctly / partially covered / missing / unclear | evidence | notes |
|---|---|---|---|
| setup | partially covered | `initial_state` creates 136 non-bonus tiles and deals through chance actions | Dice, wall break, exact dead wall construction, and flowers/seasons setup are not really modeled. |
| player count and turn order | partially covered | 4 players, fixed East/South/West/North seats, next player `(p + 1) % 4` | Reaction/rob current-player reporting is wrong; full wind-round rotation is missing. |
| legal actions | partially covered | Supports discard, draw win, chi, pong, kong, robbery, pass | Last-wall reactions and claim priority are problematic/assumed. |
| state transitions | partially covered | Fresh state returned; phases for deal/draw/discard/react/replace/rob | Claimed discards remain in discard history; some terminal transitions are wrong. |
| terminal conditions | partially covered | Ends on Mah-Jongg or wall exhaustion | Final discard after last wall tile incorrectly allows non-winning claims. |
| scoring/returns | partially covered | Implements settlement examples, figure points, some doublings and special hands | Many table rows and context-sensitive bonuses are missing. |
| rendering/action names | partially covered | Stable string actions and deterministic render | Render is full debug and may duplicate claimed discards; inferred labels may need confirmation. |
| chance | partially covered | Explicit chance nodes for deal/draw/replacement | Uses aggregate wall counts; exact live/dead wall order and bonus replacement handling are absent. |
| hidden information | partially covered | `information_state` hides other hands and wall contents | Reaction `current_player` bug can expose the wrong player’s perspective to callers. |
| simultaneous moves | missing / not relevant | `SIMULTANEOUS` unused | Rulebook does not require simultaneous moves. |

### 4. Unsupported assumptions or invented rules

- Harmless convention: one generated module models only a single `Spiel`, not the full Partie.
- Risky assumption: reaction priority is invented as Mah-Jongg > Kong/Pong > Chi with distance tie-breaks.
- Mostly justified inference: three suits, four winds, and three dragons are inferred from the “13 unique wonders” text, but some labels are placeholders.
- Risky simplification: flowers/seasons are omitted by default, and `use_bonus=True` is not implemented.
- Risky simplification: dead wall is represented only as the final 14 reserved tiles, without wall-break or bonus-tile replacement mechanics.
- Harmless-to-risky convention: winning is optional, so a complete hand may discard instead of declaring Mah-Jongg.
- Risky scoring convention: ambiguous or unimplemented limit hands are scored through normal scoring and cap behavior.
- Risky scoring convention: non-winner concealed figures are extracted greedily rather than by an explicit rulebook scoring choice.
- Harmless convention: `limit=500` defaults from the worked examples.
- Risky interface convention: `render` is full debug state, while `information_state` is player-visible.

### 5. Missing scenario tests

- Discard reaction ownership: construct a state where P0 discards `B5`, P1 can `chi:B3-B4-B5`, then assert `current_player` is P1 during the reaction.
- Last-wall discard: with only one living-wall tile left, draw it, discard it, and assert only Mah-Jongg claims are legal; after passes the game is terminal draw.
- Claimed discard rendering: P0 `discard:B5`, P1 `pong:B5`; assert the claimed tile is not shown as an ordinary unclaimed discard.
- Robbery of Kang: P0 has open `pong(B2)` plus `B2` in hand, P1 can win with `B2`; `kong_promote:B2` then `mahjong:claim:B2` should terminally set `win_source=rob`.
- Claim priority: one player can Mah-Jongg on a discard while another can Pong/Chi; assert the Mah-Jongg claimant is offered first.
- Scoring context: create terminal wins for last wall tile, last discard, robbed Kang, and pair-completing final tile; assert the correct bonuses/doublings.
- Limit hands: deterministic terminal states for seven pairs, thirteen unique wonders, four Kangs, three dragon pongs plus extra set, and pure honor hand.
- Full settlement: public API terminal states matching both worked examples, not only private `_settle`.

### 6. Open questions for the human

- Should this benchmark target one Mahjong deal only, or the full four-round Partie with seat-wind rotation?
- Should the simplified no-flowers/no-seasons variant be the official target?
- What exact priority should apply when multiple players can claim the same discard?
- What canonical labels should be used for the unnamed third suit and unnamed dragons?
- Must every listed limit hand be detected mechanically, or is a documented scoring subset acceptable?

### 7. Machine-readable summary

```text
score: 0.55
confidence: medium
critical_issues: 0
major_issues: 4
minor_issues: 3
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```