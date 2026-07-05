# Mahjong (oneshot) — LLM judge review

## 1. Score

- `score: 0.78`
- `confidence: medium`
- Justification: This is a careful, well-documented single-hand implementation whose scoring and settlement are faithful — I traced the second worked example (§10) and `returns` reproduces all four seat totals exactly (West wins with 48; Süd's Große-Drei-Drachen hand caps to 500; East-involved amounts doubled). Meld/pair/Mahjong points and the doubling table match the rulebook, and ~15 of the 19 limit hands are implemented with the rest explicitly documented as omitted. Points are lost mainly for the sequential (seat-order) resolution of competing claims, an action-naming scheme that is fragile under punctuation normalization, and the deliberate reduction to a single hand that drops the entire §6 Partie structure. Confidence is medium because the checks are not rerun and parts of the extracted rulebook (§10 tables) are garbled.

## 2. Top findings

1. **Major — claim priority is strict seat order, not by claim type.** In `legal_actions`/`apply_action` the reaction phase advances `reaction_pos` one seat at a time and applies the first claim immediately. So the right neighbour's `claim_chi` can be taken before a farther player's `claim_pong`/`claim_kang`/`claim_mahjong` is ever offered. The rulebook lists reactions but does **not** define a priority rule, so this is an assumption — but it deviates from the usual "Mahjong > Pong/Kang > Chi" and can change who wins a contested discard. *Next action:* confirm intended priority with the human; consider resolving all reactors before committing a claim.
2. **Major — action names encode the player as a run of `!`.** `hidden_player_suffix`/`hidden_chance_suffix` append `"!"*(k)` for `discard_…`, `pass`, `mahjong_self`, `kong_…`, and chance deals/draws. `discard_bamboo1!` (p0) vs `discard_bamboo1!!` (p1), and `pass!` vs `pass!!!`, collapse if punctuation is normalized — exactly the failure the generation prompt warns about ("different points cannot collapse when punctuation is normalized"). It round-trips inside the file but is not human-readable and is inconsistent with `claim_*`, which correctly use `p0/p1` tokens. *Next action:* use explicit `p<idx>` tokens for all actions.
3. **Major — scope reduced to one hand; §6 Partie not modeled.** Four rounds, seat rotation `S→O, W→S, N→W, O→N`, the 4–16-games-per-round stop rule, consecutive-win tracking, and "Neunmal Mah-Jongg" are absent; `round_wind` is fixed to `Osten` and `seat_winds` is fixed `p0=Osten…`. Round-wind-dependent scoring therefore never varies. Documented and plausibly intended for a per-hand benchmark, but it is a large slice of the rulebook. *Next action:* confirm the single-hand granularity is the intended environment unit.
4. **Minor — no dead wall.** Kang replacements are drawn from `remaining` (live wall). Dead-wall-specific scoring ("Schlussziegel von der toten Mauer", "Pflaumenblüte"/Kreis-5) is consequently unreachable. Documented.
5. **Minor — flowers/seasons omitted.** This is a rulebook-sanctioned simplification (§7: "können die Steine rausgenommen werden … 17 Doppelziegel"), so it is acceptable; the associated bonus points and three flower/season doublings are simply inert.
6. **Minor — a handful of scoring items omitted:** "Null-Punkte-Hand", "Schlussziegel ist einzig möglicher Ziegel", "Doppeltes Glück/Kang auf Kang", "Neunmal Mah-Jongg". All documented in comments.
7. **Question/minor — chance action names embed the drawn tile** (`chance:draw:bamboo1…`). `information_state` correctly hides hands, but a shared action log would reveal which private tile went to which seat.
8. **Minor — pair-completion bonus** ("Schlussziegel komplettiert Paar …") is applied only when `win_kind=="pair"` (discard/rob), not when a self-drawn final tile completes the pair.

## 3. Rule coverage review

| Rule area | Status | Evidence | Notes |
|---|---|---|---|
| Setup / components | Partially covered | `FULL_WALL` = 4×34 tiles; no dice, wall geometry, dead wall, flowers | Deal modeled as chance draws from the multiset — distribution-equivalent to a shuffle |
| Player count / turn order | Covered | `NUM_PLAYERS=4`; `next_player=(p+1)%4`; seats O/S/W/N | Counterclockwise, right-neighbour-next matches §4/§6 |
| Deal | Covered | `DEAL_TARGET_SEQUENCE`: 12 each + 13th to all + 14th to East | Matches "drei mal zwei Doppelziegel" + 13./14. Stein |
| Legal actions | Mostly covered | discard/kang/mahjong; reaction pong/chi/kang/mahjong/pass; robbing | Chi restricted to right neighbour (`p==next_player`) ✓; priority is seat-order (finding 1) |
| State transitions | Covered | phase machine deal→discard→reaction→(draw_live/kang_reaction)→… | Claim jumps turn to claimer; kang draws replacement then discards ✓ |
| Robbing the Kang | Covered | `kang_reaction`, `_apply_rob_kang_mahjong`; loser keeps open pong | Matches §4 "Beraubung des Kang"; concealed kang correctly not robbable |
| Terminal conditions | Covered | Mahjong → winner; wall empty → draw; last-tile-then-discard handled | `returns`=0 on draw ("wiederholt") ✓ |
| Scoring / returns | Covered | meld/pair/Mahjong tables; doublings; ~15 limit hands; §5 settlement | Reproduces §10 example 2 exactly for all four seats; limit short-circuits doublings; East double ✓ |
| Rendering / action names | Partially covered | `render`/`information_state` compact & deterministic | Names round-trip but `!`-suffix fragile (finding 2) |
| Chance | Covered | `chance_outcomes` = count/total, sums to 1 | Deal and live draws are explicit chance nodes |
| Hidden information | Covered | `information_state` shows own hand + `hidden_count` others | No hand leakage; action-log tile leak is separate (finding 7) |
| Simultaneous moves | Partially covered | Reactions serialized via `reaction_pos` | No true simultaneity/priority (finding 1) |

## 4. Unsupported assumptions or invented rules

- **Seat-order claim resolution** (finding 1) — risky invented tie-break; rulebook silent.
- **`Farbe3` third suit and `Drache1/Drache2` + canonical `reddragon/whitedragon`** — harmless labels; rulebook only names Bambus, Kreis and Grüner Drachen. Colours/dragons are scoring-equivalent, so this cannot distort points.
- **`round_wind="Osten"` default and fixed seat winds** — harmless for the given examples (round wind is East there) but hardcodes §6.
- **"Alle Figuren verdeckt" and "Verdecktes reines Farbspiel" require self-draw/initial** (`win_source` guard) — reasonable disambiguation of "verdeckt", but a concealed hand completed by a claimed *pair* is treated as not-fully-concealed; borderline.
- **"Drei verdeckte Pong" excludes concealed kangs** — follows the literal wording; defensible.
- **"Schlussziegel ist letzter abgelegter Ziegel" ≡ discard win with empty wall** — plausible reading, not stated verbatim.
- **`!`-suffix player encoding** (finding 2) — convention, but fragile.

## 5. Missing scenario tests

- **Settlement fixtures for §10 examples:** build the two hands/meld sets and assert `returns` equals the payoff matrices (highest-value regression test; example 2 already matches by hand-trace).
- `chance:deal:*` full deal → East `mahjong_self!` → assert winner=East, limit value (Segen des Himmels).
- `discard_… ` → `claim_pong_p2_…` → `discard_…` → `mahjong_discard_p3_pong_…`: discard win with an open pong; assert that pong scores as open.
- Extend open pong (`kong_extend_…`) → another seat `mahjong_rob_kong_p_…`: assert `win_source=rob_kang`, +1 double, and loser retains an open pong.
- `kong_concealed_…` → replacement draw → `mahjong_self`: assert Verborgener Schatz limit for four concealed sets.
- Wall-exhaustion: drive `remaining` to 0, all `pass`, assert terminal `wall_exhausted` and `returns` all 0.
- Seven pairs → half limit; thirteen orphans → full limit; imperial-green (`GREEN_TILES`) → limit.
- Non-right-neighbour attempts Chi: assert `claim_chi` absent from `legal_actions`.
- Round-trip: for sampled states, assert `name_to_action(action_to_name(a))==a` over every legal `a`, and `sum(p for _,p in chance_outcomes)==1`.

## 6. Open questions for the human

1. When several players can react to one discard, what is the intended priority (standard Mahjong > Pong/Kang > Chi, or the current seat order)? The rulebook does not specify.
2. Is a single hand the intended benchmark unit, or should the four-round Partie with wind rotation and consecutive-win tracking (§6) be modeled?
3. Should the flowers/seasons variant ever be enabled, or is the 17-wall no-flower simplification fixed?
4. Is the `!`-suffix action-naming acceptable for the BoardBench interface, or must all actions use explicit `p<idx>` tokens?

## 7. Machine-readable summary

```text
score: 0.78
confidence: medium
critical_issues: 0
major_issues: 3
minor_issues: 6
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```
