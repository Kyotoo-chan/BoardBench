### 1. Score

- `score: 0.8`
- `confidence: medium`
- Justification: The engine is a complete, invariant-respecting BoardBench interface for a single deal, and its settlement logic reproduces **both** worked examples from §10 exactly — including per-player figure points, doublings (e.g. South's `28 × 2^6 = 1792` capped to `500`), the East double-payment rule, and pairwise difference settlement. The main deductions are the rulebook-silent valuation of non-winners' partial hands (which materially drives `returns` in real rollouts), the abstracted dead wall (making a few dead-wall scorings unreachable), and the absence of embedded scenario tests. Nothing found breaks playability or terminal/return stability.

### 2. Top findings

**Finding 1 — Non-winner "Spielbild" valuation is an unverified interpretation (major / question).**
`_nonwinner_scoring_figures` scores a loser as declared melds + concealed triplets pulled from the remaining hand + scoring pairs. Evidence: the rulebook (§5 "Verrechnung der anderen Spieler untereinander") requires every non-winner to have a *Wert*, but never defines how to value an *incomplete* hand; §10 only shows clean, fully-formed hands. The examples validate this path for complete figures (South's non-winning Große-Drei-Drachen hand reproduces exactly), but random rollouts end with messy concealed hands where this heuristic is untested and drives the returns matrix. Next action: confirm the intended loser-scoring rule (do concealed non-melded tiles/incomplete chi ever count?) and pin it with tests.

**Finding 2 — Dead wall not modeled, so several dead-wall scorings are unreachable (minor→major depending on config).**
`draw_source` is only ever `"wall"`; nothing sets `"dead"`. Evidence: kong/flower replacements all call `_begin_replacement_draw_or_terminal(..., source="wall")`, and in-deal/in-draw bonus tiles re-draw from the same multiset without a dead-wall source. Consequently `win_source == "dead"` is dead code, so *"Schlussziegel von der toten Mauer" (1x)*, *"Die Pflaumenblüte vom Dach pflücken"* (Circle-5 from dead wall), and the dead-wall branch of `_declare_selfdraw_win` can never trigger. Under the default `include_bonus_tiles=False` this is largely inert; it becomes a real fidelity gap in bonus mode. Next action: track a dead-wall source for replacement draws, or explicitly document these three scorings as intentionally unreachable.

**Finding 3 — Cross-game/round mechanics intentionally out of scope (minor).**
`east_consecutive_wins` is never incremented and wind rotation (`S→O, W→S, N→W, O→N`) is absent, so *"Neunmal Mah-Jongg"* and the round-wind-rotation limit hand cannot fire. Evidence: docstring states the module models one deal, not the Partie. Fair, but worth surfacing as unreachable limit hands.

**Finding 4 — `player_winds` decoupled from `dealer` (minor).**
`Game.__init__` hardcodes `player_winds=(0,1,2,3)` regardless of the `dealer` argument. Evidence: constructing `Game(dealer=2)` yields a dealer whose seat wind is West, breaking own-wind pair/pong scoring and East-doubling alignment. The default `dealer=0` is consistent; only non-default construction is affected.

**Finding 5 — Strong settlement/returns fidelity (positive, context).**
`returns` matches both §10 examples digit-for-digit (winner payments, East doubling, pairwise differences, and the general limit cap on a non-winner). This is the hardest part of the rulebook and is solidly correct.

**Finding 6 — No embedded deterministic tests (minor).**
No `__main__` / scripted scenarios. Evidence: file ends at the engine. For BoardBench, reproducible action-sequence checks are expected.

### 3. Rule coverage review

| Rule area | Status | Evidence | Notes |
|---|---|---|---|
| Setup / components | partially covered | `_initial_deal_sequence` gives 13/13/13/14; `_make_tile_counts` | Dice, wall break, wind draw, and dead-wall geometry abstracted into chance draws (documented) |
| Player count & turn order | covered | `NUM_PLAYERS=4`, `_right_neighbor=(p+1)%4`, East=player 0, counter-clockwise | Matches "gegen den Uhrzeigersinn"; right neighbor acts next after a claim |
| Legal actions | covered | `legal_actions` / `apply_action` guard (`action not in legal → ValueError`) | `legal_actions ⊆ apply_action`; deterministic sorted order |
| State transitions | covered | draw→discard→claim→draw; `_declare_added_kong`, `_pass_rob_kong` | Kong→replacement draw, robbing-the-kang offer, kong-on-kong all modeled |
| Terminal conditions | covered | `_make_draw_terminal`, `discard_after_final_draw`, `last_draw_was_final` | Mah-Jongg call or live-wall exhaustion; final discard only completes Mah-Jongg |
| Scoring / returns | partially covered | `returns` matches §10 examples; `_meld_points`, `_pair_points`, `_limit_score_for_context` | Core verified; dead-wall scorings unreachable; non-winner partial-hand valuation heuristic |
| Rendering / action names | covered | `render`, `action_to_name`/`name_to_action` | Deterministic render; canonical names round-trip (incl. `kong_extend_*?` hidden-index suffix) |
| Chance | covered | `chance_outcomes` (count/total, sums to 1) | Same actions as `legal_actions` at chance nodes; no hidden `random` |
| Hidden information | covered | `information_state` hides other hands (counts only) | Action names don't leak private tiles |
| Simultaneous moves | n/a (modeled sequential) | `_build_claim_groups`, `claim_index` | Simultaneous discard claims resolved as ordered priority opportunities (assumption) |

### 4. Unsupported assumptions or invented rules

- **Third suit `"zeichen"` and dragons `rot/gruen/weiss`** — forced by gaps; harmless (labels only). `GREEN_TILES` correctly matches the rulebook's imperial-green list.
- **Claim priority = Mah-Jongg > Kang > Pong > Chi, tie-broken in seating order from discarder's right** — reasonable, documented; rulebook lists reactions without an explicit total order.
- **Non-winner valuation = declared melds + concealed triplets + scoring pairs** — invented (rulebook silent on incomplete hands); *risky* because it feeds `returns`.
- **Flower/kong replacements drawn from the shared multiset with source `"wall"`** — deviates from "aus der toten Mauer"; risky only for bonus-mode dead-wall scorings.
- **"Segen des Himmels" = dealer's 14-tile self-win before any discard; "Segen der Erde" = win *on* East's first discard** — reasonable readings of terse text.
- **"Doppeltes Glück" = two kongs since the last draw + self-win** — approximation of "gleichzeitiger" Mah-Jongg-Ruf.
- **Undeclared four-of-a-kind scored as a concealed Pong** — this is *not* invented; it follows the §4 note that an unlaid Kang scores only as Pong.
- **Half-limit `limit // 2` for "Paariges Spiel"; full limit if it also matches a full-limit pattern** — reasonable; integer floor.

### 5. Missing scenario tests

- Reconstruct both §10 examples via scripted action sequences and assert the exact `returns` vectors (`[+456,-182,-152,-122]` and `[-1036,+1418,+192,-574]`).
- Self-draw standard win: assert `+20`, `+2` wall-tile, correct figure points and doublings.
- `claim_chi_*` offered only to the discarder's right neighbor; `claim_pong_*`/`claim_kong_*` offered to all three; verify priority when a Pong and a Chi compete.
- Robbing the kang: `kong_extend_*` → opponent `mahjong_rob_kong_*` wins (`win_source=rob_kang`, +1 double); and the all-`pass` path that completes the kong + replacement draw.
- `mahjong_self` on seven pairs and on 13 orphans → limit `250` and `500`.
- Live-wall exhaustion → `is_terminal`, `returns == [0,0,0,0]`.
- Final wall tile drawn then discarded: only `mahjong_discard_*` offered; all-pass → terminal draw.
- Round-trip `action_to_name`/`name_to_action` over every legal action in several sampled states, especially `kong_extend_bamboo3?` (hidden-index suffix).
- Two concealed kongs in one turn then self-win → `Doppeltes Glueck` limit.
- `Game(dealer=0)` immediate dealer win → `Segen des Himmels` limit; non-dealer win on East's first discard → `Segen der Erde`.

### 6. Open questions for the human

- How should an incomplete non-winner hand be valued at game end — only exposed melds, or also concealed triplets/honor pairs as the code assumes? This directly changes `returns`.
- Should a win on a flower- or kong-replacement tile count as "from the dead wall" (enabling *Pflaumenblüte* and the dead-wall double), i.e. should the dead wall be tracked at all in the abstracted model?
- Are the invented labels for the third suit and the three dragons acceptable, or should specific rulebook tiles be used?
- Is `limit // 2 = 250` (floor) the intended half-limit for "Paariges Spiel"?
- Among multiple simultaneous Mah-Jongg claimants, is "seating order from the discarder's right" the intended tiebreak?

### 7. Machine-readable summary

```text
score: 0.8
confidence: medium
critical_issues: 0
major_issues: 1
minor_issues: 5
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```
