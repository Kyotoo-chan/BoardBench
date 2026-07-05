# BoardBench judge review — mahjong (agentic), `mjh_codex_ag.py`

## 1. Score

- `score: 0.75`
- `confidence: medium`
- Justification: A carefully built, well-structured single-game engine that follows this rulebook's specific quirks (dead wall = 30 tiles, kang replacement from the **live** wall, bonus replacement from the **dead** wall) rather than generic mahjong. The payment/settlement logic reproduces both printed Abrechnungsbeispiel matrices exactly given hand values, and scoring/limit-hand coverage is unusually complete. It loses points for a genuine returns-affecting bug (non-winner hands score only one pair) and for flattening simultaneous claims into a positional ask with no Mah-Jongg priority. Confidence is medium because parts of the rulebook (images, the worked examples) are OCR-garbled and cannot serve as a clean numeric oracle.

## 2. Top findings

**1. [major] Non-winner partial-hand scoring counts only a single pair — returns diverge from the worked example.**
- Evidence: `_score_partial_hand` builds `best_pair` (one pair) only. Abrechnungsbeispiel 1, Westwind scores *both* "Paar Drachen" (2) and "Paar eigene Winde" (2) for total 22; the code would score one pair → 20.
- Why it matters: `returns()` uses these values in the pairwise-difference settlement, so a wrong non-winner value shifts every difference against that player. This is the benchmark's numeric output.
- Next action: sum all scoring pairs (dragon / own-wind / round-wind) for non-winners rather than picking one, and add a test reproducing the example matrix.

**2. [major] Claim reactions are resolved by positional counter-clockwise ask; no Mah-Jongg priority; simultaneity flattened.**
- Evidence: `_apply_claim_action` walks `_responders_after(discarder)` one at a time; the right neighbor (only Tschi-eligible seat) is asked *first*, so a Tschi or Pong can be committed before a farther seat's `claim:mahjong` is ever offered.
- Why it matters: In rollouts a nearer non-winning claim can pre-empt a winning Mah-Jongg, which most Mah-Jongg variants forbid. The rulebook lists reactions but no priority table, so this is a documented interpretation — but it changes outcomes.
- Next action: confirm intended priority with the human; if standard, resolve Mah-Jongg claims before Pong/Kang before Tschi at a discard node.

**3. [minor] Fully deterministic setup; no chance nodes.**
- Evidence: `_deterministic_mix` fixes the wall; `initial_state` uses no dice; there is no `chance_outcomes`. Documented in the header.
- Why it matters: Dice wind-assignment, shuffling, and wall draws (Section 3) are chance events; the engine cannot exercise stochastic transitions or a truly hidden wall. Acceptable for a deterministic benchmark and clearly disclosed, but it is a fidelity reduction.
- Next action: keep as-is if determinism is desired; otherwise expose wall draws as `CHANCE` nodes.

**4. [minor] Multi-game Partie structure not modeled.**
- Evidence: `round_wind` fixed to `"Ost"`, `place_winds` fixed to `WINDS`; no wind rotation (S→O…), no round/game counters. `"Neunmal Mah-Jongg"` and the round-progression limit hands cannot occur.
- Why it matters: Section 6 defines a 4-round × 4–16-game Partie; the engine is one game. Reasonable scope, but the omission should be explicit for benchmark expectations.

**5. [minor] Invented tile labels and a few omitted scoring lines.**
- Evidence: `Farbe3`, `DracheA`, `DracheB` stand in for tiles only shown in un-OCR'd images; `"Schlussziegel ist einzig möglicher Ziegel"` (+2) is deliberately not inferred. Both documented.
- Why it matters: Harmless for structure, but action names/render will not match the true tile names for the third suit and two dragons.

**6. [question] The printed Abrechnungsbeispiele are not a clean numeric oracle.**
- Evidence: Beispiel 1 Ostwind sums to 38 only if the "offener Pong Wind" is worth 8, yet the table says open wind pong = 4; the examples also state schlussziegel/concealment bonuses are "ausser acht gelassen," while the code models them.
- Why it matters: Deterministic tests built directly from the example *totals* will fail even with correct code. Only the settlement *matrix given hand values* is safely reproducible.

## 3. Rule coverage review

| Rule area | Status | Evidence | Notes |
|---|---|---|---|
| Setup / components | partially covered | 3 suits×9×4 + winds + dragons (+bonus) in `_full_wall`; dead wall = 30 (14 double + 2 loose); deal 3×4 then 13th, East 14th | Deterministic (no dice/shuffle); 17-vs-18 wall abstracted to fixed dead=30; third suit/dragons are placeholders |
| Player count & turn order | covered correctly | `NUM_PLAYERS=4`; `_next_player = (p+1)%4` = counter-clockwise right neighbor; East starts in `discard` | Matches "gegen den Uhrzeigersinn" and right-neighbor progression |
| Legal actions | covered correctly | draw/discard/claim/rob_kang actions; Tschi gated to `_next_player(discarder)`; kang only with `live_wall` | `legal_actions` ⊆ `apply_action` by the up-front membership check |
| State transitions | partially covered | phase machine; kang replacement from **live** wall; bonus replacement from **dead** wall; kang-chain tracking | Claim priority is positional (finding 2); rare edge: bonus drawn with empty dead wall leaves hand one tile short in `_draw_live` |
| Terminal conditions | covered correctly | `is_terminal` = mahjong or empty live wall in draw; last drawer still discards; all-pass + empty wall → `wall_empty` | Matches Section 5; terminal states yield no legal actions |
| Scoring / returns | partially covered | winner pays/receives, East double; pairwise-difference settlement, East double; limit cap; both example matrices reproduced given values | Non-winner multi-pair bug (finding 1); greedy concealed-pong heuristic in partial scoring; draw ⇒ all-zero returns ✓ |
| Rendering / action names | covered correctly | `render` compact & deterministic; identity `action_to_name`/`name_to_action` round-trip; names use tile labels, no bare indices | `render` shows all hands (debug); `information_state` hides opponents' tiles |
| Chance handling | missing (by design) | no `chance_outcomes`; deterministic wall | Documented assumption; Section 3 dice/shuffle not modeled |
| Hidden information | covered correctly | `information_state` shows own hand, others as "N concealed", public melds/discards | Deterministic wall is theoretically recomputable but not exposed via API |
| Simultaneous moves | partially covered | discard reactions modeled sequentially | No true simultaneity/priority; rulebook gives no priority table |

## 4. Unsupported assumptions or invented rules

- Harmless conventions: deterministic wall via `_deterministic_mix`; fixed `dead_count=30`; placeholder labels `Farbe3`/`DracheA`/`DracheB`; identity action encoding; `render` as full debug state with a hiding `information_state`; treating East's complete initial 14 as `win_source="initial"` (Segen des Himmels).
- Riskier invented resolutions: **positional claim priority** (counter-clockwise ask lets a nearer Tschi/Pong beat a farther Mah-Jongg) — the rulebook specifies no priority. **Single-pair non-winner scoring** — contradicts the worked example. **`Segen der Erde`** gated by `len(history) <= 3` and empty discard piles — a fragile heuristic for "after East's first discard." **`Doppeltes Glück`** keyed to `kang_chain >= 2` — a reasonable but unstated encoding of "two kang in one turn."

## 5. Missing scenario tests

- East immediate win from the dealt 14 → `declare:mahjong`, expect `win_source="initial"` and the "Segen des Himmels" limit path.
- Discard → far seat `claim:pong:<tile>` → verify turn jumps to claimer, intermediate seats skipped, claimer must `discard:`.
- Tschi legality: assert `claim:tschi:*` present only for `_next_player(discarder)` and absent for other seats holding the sequence.
- Rob-the-kang: `declare:kang:<tile>:extend` on an open pong, other seat `mahjong:rob-kang:<tile>` → terminal, robbed player left with an open pong, "Beraubung des Kang" double.
- Concealed kang: `declare:kang:<tile>:concealed` → replacement drawn from live wall, concealed hand count = 14−3·(melds) preserved.
- Wall exhaustion: pass to empty live wall → `terminal_reason="wall_empty"`, `returns == [0,0,0,0]`.
- Settlement oracle: construct a terminal state with fixed per-player hand values and assert the full 4×4 matrix and totals match Abrechnungsbeispiel 1 and 2 (drives out finding 1 and finding 6).
- Multi-valued-pair non-winner (dragon pair + own-wind pair) → expected 4 pair points, currently 2.
- Seven pairs → half limit; Thirteen Orphans → full limit; all-honors hand → "Reine Bildziegel-Hand" limit.

## 6. Open questions for the human

- Reaction priority: should Mah-Jongg outrank Pong/Kang outrank Tschi at a discard, or is the positional counter-clockwise ask intended?
- Non-winner scoring: confirm all valued pairs (and any concealed melds) are summed, as Abrechnungsbeispiel 1 West implies.
- Are the printed example totals authoritative despite the open-wind-pong 4-vs-8 inconsistency and the stated omission of schlussziegel bonuses? This decides whether they can be used as test oracles.
- Is single-game scope acceptable, or must round/Partie state (wind rotation, "Neunmal Mah-Jongg") be modeled?
- Should dice/shuffle/wall draws be exposed as chance nodes, or is a fixed deterministic wall the intended benchmark form?

## 7. Machine-readable summary

```text
score: 0.75
confidence: medium
critical_issues: 0
major_issues: 2
minor_issues: 4
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```
