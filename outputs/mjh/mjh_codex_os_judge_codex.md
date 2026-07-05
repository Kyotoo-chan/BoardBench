### 1. Score

score: 0.45  
confidence: high

The implementation captures a playable four-player Mahjong-like core with deal, draw, discard, claims, kongs, robbing a kong, hidden hands, and simple terminal handling. However, it omits or simplifies large rulebook areas: flowers/seasons and dead wall behavior, wind/round progression, complete scoring and settlement, discard-claim priority/order, and many limit hands. It also invents tile labels, return values, and a simplified chance/deal model, so it is useful as a rough environment but not benchmark-ready for rule fidelity.

### 2. Top findings

severity: critical  
evidence: Rulebook section 5 gives full post-Mah-Jongg scoring, limit handling, East double payments, and pairwise settlement among non-winners; code `returns()` only returns `3.0` for winner and `-1.0` for others.  
why it matters: Scoring/returns are a major benchmark target and currently do not represent the rulebookÔÇÖs payoff structure.  
suggested next action: Implement hand value calculation, doubling rules, limit hands, East doubling, and non-winner settlement, or explicitly scope the environment as win/loss-only.

severity: major  
evidence: Rulebook includes flowers/seasons, dead wall replacement, 17/18 double-tile wall setup, and replacement from the dead wall; code excludes flowers/seasons entirely and draws all replacement tiles from the same `wall` while decrementing `live_remaining`.  
why it matters: This changes setup, chance structure, tile counts, scoring bonuses, and wall-empty timing.  
suggested next action: Add an explicit option for playing without bonus tiles, or model bonus tiles/dead wall separately.

severity: major  
evidence: Rulebook says if a discarded tile is claimed, the claimant must discard and ÔÇ£sein rechter Nachbar ist als n├ñchstes dranÔÇØ; code after a claim sets `current = player`, then after that discard a normal claim/pass sequence advances from that discarder.  
why it matters: This may be correct after the claimantÔÇÖs discard, but the code does not encode claim priority or competing reaction resolution. All claims are exposed as a flat simultaneous action list.  
suggested next action: Define deterministic priority among Mahjong/Pong/Kang/Chi reactions, or document that the judge/player chooses among all legal claims.

severity: major  
evidence: Rulebook has four rounds, rotating winds, East retention until loss or up to four wins; code fixes `ROUND_WIND = "ost"` and player winds permanently.  
why it matters: Wind identity affects turn order, settlement doubling, scoring doubles, and the broader ÔÇ£PartieÔÇØ structure.  
suggested next action: Either implement multi-hand wind progression or document that this models one isolated East-round hand only.

severity: major  
evidence: Rulebook lists many limit hands; code only recognizes standard four-groups-and-pair, seven pairs, and thirteen wonders.  
why it matters: Many legal Mah-Jongg wins and scoring outcomes are missing.  
suggested next action: Add limit-hand detection at least for the listed hands, or separate ÔÇ£win detectionÔÇØ from ÔÇ£scoring onlyÔÇØ if some hands remain unsupported.

severity: minor  
evidence: Code uses invented labels `farbe3`, `drache1`, `drache2`, `gruener_drache`; rulebook text names Kreis, Bambus, colors, winds, dragons, but not this exact complete tile taxonomy.  
why it matters: Action names and renders are less comparable to rulebook terminology and future references.  
suggested next action: Rename tiles to stable German rulebook-style labels where possible.

### 3. Rule coverage review

| rule area | covered correctly / partially covered / missing / unclear | evidence | notes |
|---|---|---|---|
| setup | partially covered | Code builds 4 copies of suited, wind, and dragon tiles and deals 13 each plus East 14. | Dice, wall break, dead wall, optional flowers/seasons, and 17/18 double-wall structure are omitted/simplified. |
| player count and turn order | partially covered | `PLAYERS = 4`, winds assigned East/South/West/North, `_right_neighbor(player)`. | One-hand flow exists, but round wind and wind rotation are missing. |
| legal actions | partially covered | Supports discard, self Mahjong, claim Mahjong/Pong/Kang/Chi, concealed/extended Kang, rob Kang. | Claim priority and some reaction timing are underspecified; all competing claims appear as selectable simultaneous actions. |
| state transitions | partially covered | Deterministic transitions for deal, draw, discard, claims, replacement, rob kong. | Replacement draws from live wall, not dead wall; bonus tile replacement missing. |
| terminal conditions | partially covered | Terminal on Mahjong or wall empty after last discard is unclaimed. | Wall-empty handling is approximate because dead/live wall distinction is absent. |
| scoring/returns | missing | `returns()` uses `[3, -1, -1, -1]` for winner and zeros otherwise. | Does not implement rulebook scoring tables, doubling, limits, East doubling, or settlement. |
| rendering/action names | partially covered | Stable action names like `discard:kreis_1`, `claim:p1:pong:ost`; deterministic render. | Names are readable but some tile labels are invented or less faithful. |
| chance | partially covered | Explicit `chance_outcomes()` for deal/draw/replacement. | Does not model dice/wall break/dead wall; replacement source is wrong relative to dead wall rules. |
| hidden information | partially covered | Full state stores hands; `information_state()` hides other hands by count. | Good interface choice, though render reveals full debug state. |
| simultaneous moves | partially covered / unclear | `current_player()` returns `SIMULTANEOUS` during claim/rob phases. | Legal actions are not joint actions; they represent a judge-selected single claim/pass outcome. |
| special hands | partially covered | Standard hand, seven pairs, thirteen wonders. | Most listed limit hands are absent. |
| flowers/seasons | missing | No bonus tile constants or replacement-on-draw behavior. | Rulebook allows removing them to simplify, but code does not expose that assumption clearly. |

### 4. Unsupported assumptions or invented rules

Harmless convention: `farbe3` is used as a third suit name because the extracted rulebook text does not clearly name all suit labels.

Risky invented rule: `returns()` uses winner-takes-3 and losers-take-minus-1 instead of rulebook settlement.

Risky invented rule: Seven pairs allows four identical tiles to count as two pairs; the code comments note the rulebook is unclear on this.

Risky invented rule: Claims are represented as a flat simultaneous action choice plus `pass_all`, with no encoded priority among multiple players or claim types.

Risky invented rule: Bonus tiles are excluded without a clear game option, even though the rulebook discusses play with or without them.

Risky invented rule: Replacement tiles for Kang come from the same wall pool rather than a modeled dead wall.

Risky invented rule: Round wind is fixed to East and player winds never rotate.

Risky invented rule: Dragons are named `drache1`, `drache2`, and `gruener_drache`, inventing two generic dragon identities.

Risky invented rule: Wall break and dice setup are ignored and replaced by probabilistic tile-by-tile dealing from an unordered wall counter.

Risky invented rule: Only three win patterns are recognized, excluding many listed limit hands.

### 5. Missing scenario tests

Test initial chance deal until complete: after 53 deal actions, East has 14 tiles, others 13, phase is `discard`, current player is East.

Test discard pass flow: East discards, all pass, discarded tile moves to `dead_discards`, South becomes next draw player.

Test Pong claim flow: East discards a tile where another player has a pair; `claim:pX:pong:<tile>` creates an open pong and requires claimant to discard.

Test Chi restriction: only the right neighbor of the discarder can claim `chi` with a valid suited sequence.

Test claim-Mahjong from discard: adding the discarded tile completes a standard hand and terminal winner is the claimant.

Test concealed Kang: player with four identical concealed tiles may declare `kang:concealed:<tile>` and enters replacement phase.

Test robbing a Kang: extending an open Pong exposes `rob:pX:mahjong:<tile>` when another player can win with that tile.

Test wall exhaustion: after final live-wall draw and discard, only Mahjong claims can prevent terminal draw.

Test scoring placeholder failure: a known scoring example from section 10 should not currently match `returns()`, documenting missing scoring.

Test information state: a player sees their own hand but only hidden counts for other players.

### 6. Open questions for the human

Should this benchmark implementation model a single hand only, or the full four-round wind progression described in section 6?

Should flowers and seasons be included, or should the environment explicitly use the rulebookÔÇÖs simplified no-bonus-tile variant?

Should `returns()` represent full point settlement from section 5 and the scoring tables, or only winner/loser utility for rollout checks?

What claim-priority rule should be used when multiple players can claim the same discard?

```text
score: 0.45
confidence: high
critical_issues: 1
major_issues: 5
minor_issues: 1
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```
