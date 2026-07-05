### 1. Score

- score: 0.55
- confidence: medium

The implementation is a playable single-hand Mah-Jongg model with four players, tile groups, discard/claim flow, Kangs, Robbing the Kang, bonus tiles, hidden-information views, and a substantial scoring attempt. However, it replaces explicit shuffled/dice setup with a deterministic wall, omits the multi-game wind/round structure, invents claim-conflict resolution, and uses incomplete/heuristic scoring for several rulebook areas. It is useful for experiments but not yet benchmark-ready as a faithful rulebook implementation.

### 2. Top findings

1. **severity: major**  
   **evidence:** Rulebook setup requires shuffled tiles, dice, wall break, live/dead wall construction; code uses `_deterministic_mix`, fixed `dead_count = 30`, and no `chance_outcomes`.  
   **why it matters:** Random setup and wall order materially affect hidden information and draw outcomes.  
   **suggested next action:** Add explicit chance/setup handling or clearly scope the environment to deterministic scenario testing only.

2. **severity: major**  
   **evidence:** Rulebook section “Winde” defines four rounds, 4–16 games per round, East retention/rotation, prevailing wind; code has one hand only with fixed `round_wind="Ost"` and `place_winds=WINDS`.  
   **why it matters:** Full-game scoring, wind bonuses, East doubling, and “Neunmal Mah-Jongg” depend on match state.  
   **suggested next action:** Decide whether BoardBench target is one deal or full Partie; if full, add round/game progression.

3. **severity: major**  
   **evidence:** Rulebook lists reactions to a discard but does not give a full priority table; code serializes responders with `_next_responder` and lets an earlier Pong/Kang/Tschi claim preclude later Mahjong claims.  
   **why it matters:** Claim priority changes legal outcomes and winners.  
   **suggested next action:** Clarify discard-claim priority; consider collecting all claims before resolving.

4. **severity: major**  
   **evidence:** Code omits or approximates scoring items such as “Schlussziegel ist einzig möglicher Ziegel”, full “Neunmal Mah-Jongg”, several timing-based limit hands, and loser hand valuation.  
   **why it matters:** Returns are central to benchmarking; small scoring errors can change rankings and payoffs.  
   **suggested next action:** Add scoring tests from the rulebook examples and encode missing scoring metadata.

5. **severity: major**  
   **evidence:** `_legal_discard_actions` permits `declare:kang:<tile>:extend` whenever an open Pong tile is in hand; rulebook says this happens when the player draws the fourth tile from the wall.  
   **why it matters:** Allows Kangs/Robbing-the-Kang opportunities that may not be legal.  
   **suggested next action:** Require the extending tile to be the latest drawn tile from the wall.

6. **severity: minor**  
   **evidence:** Code uses placeholder labels `Farbe3`, `DracheA`, `DracheB` because extracted rulebook text omits some image labels.  
   **why it matters:** Action/render names may not match human rulebook terminology.  
   **suggested next action:** Confirm exact tile labels from the source images.

7. **severity: minor**  
   **evidence:** `limit=500` and `include_bonus_tiles=False` are defaults; the rulebook says the limit is agreed and bonus tiles may be removed.  
   **why it matters:** Defaults may silently select one variant.  
   **suggested next action:** Document variant parameters in render/API or require explicit construction.

### 3. Rule coverage review

| rule area | covered correctly / partially covered / missing / unclear | evidence | notes |
|---|---|---|---|
| setup | partially covered | `initial_state`, `_full_wall`, deterministic wall/deal | Correct 4-player deal shape, but no shuffle/dice/wall-break chance. |
| player count and turn order | partially covered | `NUM_PLAYERS = 4`, winds, `_next_player` | East starts and counter-clockwise order modeled; no round/seat rotation. |
| legal actions | partially covered | discard, draw, pass, claim Pong/Tschi/Kang/Mahjong, declare Kang | Main actions exist, but claim priority and some Kang legality are assumptions. |
| state transitions | partially covered | claim/discard/draw phases, exposed melds, dead discards | Playable single-hand flow; conflict resolution and stochastic setup are weak. |
| terminal conditions | partially covered | Mahjong terminal; wall-empty after last discard/pass | Draw repeat/match continuation not modeled. |
| scoring/returns | partially covered | `score_hand`, payout settlement, East double payments | Many table entries attempted; several bonuses/limit/timing cases missing or heuristic. |
| rendering/action names | partially covered | stable string actions and `render` | Human-readable, but some invented tile labels and generic `claim:mahjong`. |
| chance | missing | no `chance_outcomes`; deterministic `_deterministic_mix` | Rulebook clearly has shuffle/dice setup. |
| hidden information | partially covered | `information_state` hides other hands and wall contents | Full `GameState` contains truth; deterministic setup reduces realism. |
| simultaneous/claim competition | unclear/partially covered | sequential responder model | Rulebook does not specify priority; implementation invents one. |
| bonus tiles | partially covered | optional `include_bonus_tiles`, replacement from dead wall | Basic replacement modeled; default excludes them and dead-wall ordering is assumed. |

### 4. Unsupported assumptions or invented rules

- **Risky:** Deterministic wall order replaces shuffled tiles and dice-based wall break.
- **Risky:** Single-hand game scope; no full Partie, round wind progression, East retention/loss tracking, or cumulative accounting.
- **Risky:** Sequential claim resolution by seating order without an explicit priority table.
- **Risky:** Open Pong extension to Kang allowed whenever the fourth tile is in hand, not only when just drawn.
- **Risky:** Scoring incomplete hands/loser hands by heuristic arrangement selection.
- **Risky:** Limit hands can be detected by arrangement logic even where timing or winner-only status may matter.
- **Risky:** Ambiguous timing hands are approximated using history length, discard counts, or `kang_chain`.
- **Harmless/conventional:** Placeholder tile labels for missing OCR/image names.
- **Harmless/conventional:** Canonical action strings such as `claim:tschi:...` and `declare:kang:...`.
- **Harmless but variant-defining:** Default `limit=500`, based on the example, and default exclusion of bonus tiles.

### 5. Missing scenario tests

- Initial setup: assert P0 has 14 non-bonus tiles, others 13, phase is `discard`, current player is East.
- Unclaimed discard: `discard:<tile>`, then three `pass`, then `draw:live`; verify discard becomes dead and right neighbor acts.
- Pong claim: constructed state where P2 has two matching tiles; sequence `discard:<tile>`, P1 `pass`, P2 `claim:pong:<tile>`.
- Tschi restriction: constructed discard from P0 where only P1 should have `claim:tschi:...`; P2/P3 should not.
- Mahjong from discard: constructed near-complete hand; `discard:<tile>`, responder `claim:mahjong:<tile>`, terminal returns nonzero.
- Kang from discard: responder with three matching tiles uses `claim:kang:<tile>` and receives replacement draw.
- Robbing the Kang: open Pong holder uses `declare:kang:<tile>:extend`; another player uses `mahjong:rob-kang:<tile>`.
- Last live tile: draw final live tile, discard, all pass; verify terminal draw returns `[0,0,0,0]`.
- Bonus replacement: with bonus tiles enabled, drawing `Blume1`/`Jahreszeit1` exposes it and draws replacement from dead wall.
- Scoring regression: construct the two rulebook accounting examples and assert final return totals match the printed totals.

### 6. Open questions for the human

- Should the benchmark target one Mah-Jongg hand or the full Partie with rounds, wind rotation, and cumulative scores?
- What is the intended priority when multiple players can claim the same discard?
- Should shuffled setup and dice be explicit chance nodes, or are deterministic scenario states acceptable?
- What are the exact missing suit/dragon tile names from the rulebook images?
- Should bonus tiles be included by default, or should the variant always require an explicit choice?

### 7. Machine-readable summary

```text
score: 0.55
confidence: medium
critical_issues: 0
major_issues: 5
minor_issues: 2
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```
