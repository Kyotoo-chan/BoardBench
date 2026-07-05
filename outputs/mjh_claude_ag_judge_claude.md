# BoardBench judge review — mahjong (agentic), `outputs/mjh_claude_ag.py`

### 1. Score

- `score: 0.76`
- `confidence: medium`

The implementation faithfully models a single deal: setup (abstracted but functional), counter-clockwise turn order, the full discard/react loop (pong, chi, three kong variants, mahjong, robbing the kong, pass), terminal conditions (mahjong call and wall-exhaustion draw), chance nodes, hidden-information views, and round-tripping action names. Its strongest signal is that the settlement engine reproduces **both** worked examples exactly (including East doubling and the capped 1792→500 Great-Three-Dragons hand), and the doubling logic reconstructs those figure/doubling totals. The main deductions are incomplete limit-hand detection (several rulebook limit hands are scored as normal hands and can fall below the limit) and the deliberate exclusion of the multi-game "Partie" (round-wind rotation, per-round stop rules, Partie-level limit hands). I cannot fully validate the per-figure scoring against Section 10 because the PDF figure column is garbled, so confidence is medium.

### 2. Top findings

**[major] Limit-hand detection is only partial; some detectable limit hands can score below the limit.**
- Evidence: `_winner_value` maps only seven pairs (`limit//2`), thirteen orphans, only-honors, only-terminals, and `num_kong==4` to the limit. Section 9 lists ~14 more (Verdecktes reines Farbspiel, Neun Laternen, Die sich windende Schlange, kaiserliche grüne Hand, Verborgener Schatz, etc.).
- Why it matters: `returns` is a core benchmark output. A concealed pure-suit hand of all chi, for instance, scores `20 * 2^(3+1) = 320 < 500`, contradicting "Verdecktes reines Farbspiel = full limit". The code comment claims these "cap at the limit anyway", which is not always true.
- Next action: add shape detection for at least the deterministically detectable ones (concealed-one-suit, nine gates, imperial green, four winds, three scholars) or document precisely which are intentionally under-scored.

**[major] Only one "Spiel" is modelled; the "Partie" structure is out of scope.**
- Evidence: module docstring; `Game.__init__` takes fixed `round_wind`/`seats`; no seat rotation, no 4–16-games-per-round logic, no cumulative scoring.
- Why it matters: Section 6 and several Section-9 hands (Neunmal Mah-Jongg, Segen des Himmels/der Erde) are Partie-level and thus unreachable; round-wind never advances.
- Next action: acceptable as a documented single-deal unit for BoardBench, but the benchmark scope should be recorded so returns aren't compared against Partie-level expectations.

**[minor] Deterministic hand decomposition is greedy, not score-maximizing.**
- Evidence: `_form_sets` consumes the lowest present tile (pong before chi) and returns the first full parse; `_decompose_standard` returns the first workable pair. Win detection is correct, but the chosen parse and the `pair_tile` used for the final-tile bonus may not be the player's best-scoring reading.
- Why it matters: winner value can be lower than the rulebook's "best legal" scoring in ambiguous hands (e.g., a hand parseable as both seven pairs and four chi is forced to standard).
- Next action: enumerate decompositions and take the max-scoring one, or document the fixed parse as an assumption.

**[minor] Several special-condition points/doublings are unimplemented.**
- Evidence: "Schlussziegel ist einzig möglicher Ziegel", "Schlussziegel von der toten Mauer", "mit dem letzten Ziegel der Mauer gewonnen", "Schlussziegel ist letzter abgelegter Ziegel", "Kang auf Kang", plum-blossom/moon conditions — none are tracked. `win_source` distinguishes only wall/discard/rob/initial.
- Why it matters: modest but real returns deltas in specific terminal states.
- Next action: track enough provenance (dead-wall vs living-wall, last-living-tile, discard identity) to score these, or document as gaps.

**[question] Worked example shows an open wind pong worth 8, but the point table says 4.**
- Evidence: Section 10 East hand sums to 38 only if "offener Pong Wind" = 8, yet Section 8 states "Pong aus Drachen oder Winden, offen 4 / verdeckt 8". `_meld_points` follows the table (open wind pong = 4).
- Why it matters: if the example reflects the true rule, every open honor pong is systematically under-scored; if it is a PDF-extraction artifact, the code is correct.
- Next action: confirm against the source page images before trusting per-figure totals.

### 3. Rule coverage review

| Rule area | Status | Evidence | Notes |
|---|---|---|---|
| Setup / components | Partially covered | `initial_state` builds 136 tiles (4×34); deal via chance to 13 each + 14th East | Tile set derived from the 13-orphans description; wall building, dice, double-tile/dead-wall geometry abstracted (documented) |
| Player count & turn order | Covered correctly | `NUM_PLAYERS=4`; seats E/S/W/N; next = `(c+1)%4`; chi only to `(src+1)%4` | Matches counter-clockwise "rechter Nachbar"; East acts first with 14 tiles |
| Legal actions | Covered correctly | `_legal_discard`, `_build_claimants`: discard, pong, kong (discard/concealed/promote), chi, mahjong (self/claim/rob), pass | Winning chi allowed to any player; non-winning chi only right neighbour — matches rulebook distinction |
| State transitions | Covered correctly | `_apply_*`: pong/chi→claimer discards; kong→replace; robbing kong→ROB phase | Tile counts stay consistent across melds; verified by hand |
| Terminal conditions | Covered correctly | mahjong call sets `winner`; `_living_wall_empty` (≤14) sets `draw_game` after final discard | Matches "letzter Ziegel darf noch abgeworfen werden"; pong on final discard is harmless (draw regardless) |
| Scoring / returns | Partially covered | `_settle` reproduces both examples; `_meld_points`/`_pair_points`/`_doublings` reproduce the 1792→500 and 48 examples | Normal + common limit hands solid; rare limit hands and special-tile conditions incomplete |
| Rendering / action names | Covered correctly | Actions are their canonical strings; `render`/`information_state` deterministic; chi names carry full run | Round-trip trivially holds; names unique and human-readable |
| Chance handling | Covered correctly | `chance_outcomes` for DEAL/DRAW/REPLACE; probabilities sum to 1 (self-tested) | No hidden RNG; explicit chance nodes |
| Hidden information | Covered correctly | `information_state` hides other hands + wall contents, shows sizes + living-wall count | Action names do not leak concealed tiles |
| Simultaneous moves | Partially covered (assumption) | Reactions serialized by assumed priority (Mahjong>Kong>Pong>Chi, nearest first) | Rulebook does not order reactions; documented invented ordering |
| Flowers/seasons | Missing (sanctioned) | `use_bonus` flag exists but unwired; Section 7 & related scoring omitted | Rulebook explicitly permits the 17-wall no-bonus variant |
| Partie / rounds | Missing | No seat rotation / round-wind advance / per-round stop rules | Documented out of scope |

### 4. Unsupported assumptions or invented rules

Harmless / well-documented conventions:
- Tile set of 136 (3 suits ×9 ×4, 4 winds ×4, 3 dragons ×4) derived from the orphan-hand text; third suit `Z` and dragons `Da/Db` are placeholders (only Bambus/Kreis and green dragon are named).
- Seat order player 0..3 = E/S/W/N; `(p+1)%4` = right neighbour.
- Dead wall = a fixed count of 14 reserved tiles; game draws at that threshold.
- Deal one tile at a time (distribution equivalent to the 3×2 double-tile procedure).
- `limit` parameterized (default 500, matching examples).

Riskier invented/assumed rules (verify):
- Reaction priority order — invented; the rulebook is silent, so this can decide who wins a contested discard.
- "Nur Hauptziegel" = terminals + honors — the rulebook never defines "Hauptziegel".
- Kong-replacement drawn from the whole remaining pool (can include reserved dead-wall tiles) rather than strictly the living wall.
- Only-honors / only-terminals treated as full limit; picture/undetectable limit hands scored as normal-capped-at-limit — a judgment call given the missing Section-9 images.
- Pair-vs-set attribution of the winning tile follows the deterministic decomposition (affects the final-tile pair bonus).

### 5. Missing scenario tests

Prefer action-name sequences that can become checks:
- **Robbing the kong:** drive to `kong_promote:Ww` by P0 while P2 completes a chi with `Ww`; expect `mahjong:claim:Ww` legal for P2, `win_source == "rob"`, terminal, zero-sum returns, and P0 left holding only an open pong.
- **Chi is right-neighbour only:** after `discard:B5` by P0, assert only P1 sees `chi:*` options and P2/P3 do not (while a *winning* chi remains available to any player).
- **Pong preempts chi:** a discard where P1 can chi and P2 can pong; assert the pong branch resolves before the chi branch.
- **Concealed kong path:** `kong_concealed:K1` → REPLACE draws, no ROB offered, then DISCARD.
- **Wall-exhaustion draw:** force `sum(wall) → 14`; assert `draw_game`, no winner, `returns == [0,0,0,0]`.
- **Seven pairs / thirteen orphans terminals:** assert `winner_value == limit//2` and `== limit` respectively, and zero-sum returns (extend beyond the current single asserts).
- **End-to-end worked example:** construct the exact Section-10 hands and assert per-player values `[76,12,22,32]` and returns `[456,-182,-152,-122]`. Currently only `_settle` is tested with **hardcoded** values — the derivation from hands to those values is untested.
- **East initial mahjong:** deal a winning 14-tile East hand; assert `win_source == "initial"` and terminal before any discard.

### 6. Open questions for the human

1. Is an open pong of winds/dragons worth 4 (Section-8 table) or 8 (implied by the Section-10 East total of 38)? This changes every honor-pong score.
2. Which Section-9 limit hands must resolve to the limit even when their normal score is below it (esp. Verdecktes reines Farbspiel, Neun Laternen)? Section-9 images are not in the packet.
3. Is a single deal the intended BoardBench unit, or should the Partie (round rotation, per-round stop rules, cumulative scoring) be modelled?
4. Is there a canonical reaction-priority order, or should ties be resolved as the code assumes?

### 7. Machine-readable summary

```text
score: 0.76
confidence: medium
critical_issues: 0
major_issues: 2
minor_issues: 6
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```
