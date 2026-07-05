# Mah-Jongg (oneshot) — judge review

## 1. Score

- `score: 0.6`
- `confidence: medium`
- The play engine is genuinely faithful: correct 34-tile / 136-tile set, correct 4-player counter-clockwise order, robust standard/seven-pairs/thirteen-orphans completion, correct chi-only-by-right-neighbor, correct robbing-only-on-open-pong, and correct wall-empty-with-last-discard-grace terminal. It loses substantial ground because the entire scoring/doubling/limit/East-double/difference system (roughly half the rulebook) is silently collapsed to a flat +3/−1 return, the dead wall is not reserved (wall-empty terminal fires too late), and the claim node is labeled `SIMULTANEOUS` but neither returns joint actions nor enforces claim priority. Mechanics are strong; rule-fidelity of scoring and a few interface points drag it to "playable but notably partial."

## 2. Top findings

**1. Entire scoring system reduced to win/loss, undocumented — severity: major**
- Evidence: `returns()` returns `[-1,-1,-1,-1]` with `+3` for the winner. Rulebook §8/§10/§11 define figure points (open/concealed pong/kang, terminals vs 2–8, dragons/winds), Mah-Jongg call points, ~15 doublings, the limit, East pays/receives double, and loser-vs-loser difference settlement. None of this is implemented and no comment flags the reduction.
- Why it matters: For a rulebook whose second half is scoring, `returns` is the primary faithfulness signal; the flat return also contradicts the rulebook's payment structure (losers pay by hand-value difference, not equally; East is doubled).
- Next action: Either implement figure-point + doubling scoring with East-double and difference settlement, or add an explicit documented assumption that scoring is intentionally win/loss-only and reflect that in a code comment near `returns`.

**2. No dead wall reserved; wall-empty terminal is ~14–16 tiles late — severity: major**
- Evidence: `initial_state` sets `live_remaining = sum(wall.values())` = 136 and never carves out the "tote Mauer" (§3: 14 double-tiles + 2 loose). All tiles are drawable; the draw terminal only triggers at 0.
- Why it matters: Terminal timing is a focus area. Games run materially longer than the rulebook allows, shifting draw-game frequency for a benchmark.
- Next action: Reserve a dead-wall count (document the exact size, since §3 wording is ambiguous) and end on live-wall exhaustion. Kang replacements per §4 come from the live wall, so keep that draw source.

**3. `SIMULTANEOUS` claim node returns individual actions and ignores priority — severity: major**
- Evidence: `current_player` returns `SIMULTANEOUS` in `claim`, but `legal_actions` returns a menu of single-player claims (`claim_pong`, `claim_chi`, …) + `pass:all`, not joint `p0:a0|p1:a1` actions; nothing enforces mahjong > pong/kang > chi (§4 lists reactions in that order).
- Why it matters: A harness expecting joint actions at a simultaneous node will mishandle this; a policy could legally select a chi over another player's pong, violating §4.
- Next action: Either model claims as a normal decision node with encoded priority, or emit true joint actions per the backbone. At minimum document that the arbiter must apply priority.

**4. `rob_mahjong` never transfers the robbed tile or shrinks the loser's pong — severity: minor (latent)**
- Evidence: `rob_mahjong` only sets `winner`/`phase`; the tile stays in the owner's hand and the open pong is unchanged. Harmless under +3/−1 returns, but wrong hand state for any real scoring and for `render`/`information_state` inspection at the terminal.
- Next action: Move the tile into the robber's hand and reduce the owner's meld before setting terminal.

**5. Flowers/seasons dropped without in-code note — severity: minor**
- Evidence: No flower/season tiles; wall is 34×4. §7 explicitly permits removal ("um das Spiel zu vereinfachen … können die Steine rausgenommen werden"), so this is sanctioned, but the code carries no assumption note.
- Next action: Add a one-line comment stating the simplified 17-per-side variant is used and flower scoring/doublings are therefore out of scope.

**6. Action labels use `p0..p3` rather than wind names; kang rendered with one tile — severity: minor**
- Evidence: `claim:p1:pong:...`, `rob:p0:...`; `_meld_text` prints `open_kang(kreis_5)` (single tile). The rulebook identifies players by wind (Ost/Süd/West/Nord).
- Next action: Prefer wind labels in action names for rulebook alignment; optionally expand kang to four tiles in render. Round-tripping is otherwise clean.

## 3. Rule coverage review

| Rule area | Status | Evidence | Notes |
|---|---|---|---|
| Setup (tiles, deal) | covered correctly | 34 types ×4; `DEAL_SEQUENCE` → 13 each, East 14 | Double-tile deal mechanics abstracted; final hand sizes correct |
| Dead wall / live wall | partially covered | `live_remaining = sum(wall)` | No dead wall reserved (finding 2) |
| Player count & turn order | covered correctly | `PLAYERS=4`, `_right_neighbor=(p+1)%4`, WINDS order | Counter-clockwise, right neighbor next — matches §4/§6 |
| Legal actions | covered correctly | discard/kang/mahjong; claim pong/kang/chi/mahjong; rob | Chi restricted to right neighbor (§4); pong/kang/chi blocked once wall empty |
| State transitions | covered correctly | claim→discard(claimer), pass→draw(right neighbor), kang→replacement | Tile accounting for pong/kang/chi and rinshan is consistent |
| Terminal conditions | partially covered | mahjong self/discard/rob; `wall_empty` on final pass | Last-discard grace correct; but wall-empty timing off (finding 2) |
| Scoring / returns | missing | flat `+3/−1` | Entire §8/§10/§11 system absent (finding 1) |
| Limit hands | partially covered | seven pairs + thirteen orphans as completion; others via standard structure | Recognized only for *completeness*, never scored as limit |
| Robbing the Kang | covered correctly | `kang_extend`→`rob_kang`; concealed kang skips robbing | Matches §4 (open-pong extension only); tile-transfer latent bug (finding 4) |
| Rendering / action names | covered correctly | deterministic sorted render; clean round-trip | p-index labels, one-tile kang render (finding 6) |
| Chance handling | covered correctly | deal/draw/replacement as chance, `wall[tile]/total` | Probabilities non-negative, sum to 1 |
| Hidden information | covered correctly | `information_state` shows own hand, others as `hidden_count` | No tile-identity leak |
| Simultaneous moves | partially covered | `SIMULTANEOUS` phase | Individual-action menu, no priority (finding 3) |
| Flowers / seasons | missing (by choice) | absent | §7-sanctioned simplification, undocumented (finding 5) |
| Partie / round rotation | missing (by scope) | single game, `ROUND_WIND="ost"` fixed | §6 multi-game structure out of scope; acceptable for one episode |

## 4. Unsupported assumptions or invented rules

- Harmless conventions: tile names `kreis`/`bambus`/`farbe3` (third suit unnamed in text), dragons `drache1`/`drache2`/`gruener_drache` (only green named in §8), single-tile-at-a-time deal, fixed seat-wind = player index, fixed round wind = East.
- Assumption inside code: seven pairs may count four-of-a-kind as two pairs (explicitly commented) — reasonable given §8 silence.
- Risky/invented: `+3/−1` payoff structure invents an equal-payment, no-East-double result that contradicts §5/§10; treating all 136 tiles as live wall invents a larger playable wall than §3 describes; allowing `kang_extend` from a long-held (not just-drawn) tile is slightly broader than §4's "zieht … den vierten Stein". None are documented as assumptions.

## 5. Missing scenario tests

- `discard:*` → `claim:pX:pong:<tile>` → claimer must discard, then `current` = claimer's right neighbor.
- `claim:pX:chi:*` legal only for `_right_neighbor(discarder)`; assert a non-neighbor cannot chi.
- Concealed kang: `kang:concealed:<tile>` → `replacement` chance → `discard`, meld `concealed=True`, `live_remaining` decremented by both the earlier draw and the replacement.
- Robbing: `kang:extend:<tile>` → `rob:pY:mahjong:<tile>` yields terminal winner Y, source `rob_kang`; and the `continue_kang` path converts the open pong to an open kang.
- Wall-empty draw: drive `live_remaining` to 0, discard, all `pass:all` → terminal `winner=None`, source `wall_empty`; assert the final discard admits only mahjong claims (no pong/kang/chi).
- Terminal invariants: for each terminal source, `legal_actions == []` and `returns` sums to 0 with correct length 4.
- Round-trip fuzz: for every action in several sampled `legal_actions`, `name_to_action(action_to_name(a)) == a` (especially chi sequences and wind-tile discards).
- Completion recognizers: fixed hands for seven pairs, thirteen orphans, and a standard 4-melds+pair with one kang (assert `groups_needed` accounting via `_is_standard_mahjong`).

## 6. Open questions for the human

- Should this environment implement real §8/§10/§11 scoring (points, doublings, East-double, loser-difference settlement), or is win/loss the intended benchmark target? This is the single largest fidelity lever.
- Exact dead-wall size: §3 says "14 Doppelziegel + 2 lose" — is that 30 tiles, 28+2, or a conventional 14? Needed to fix the draw terminal.
- When multiple players can call Mah-Jongg on one discard, what priority applies? The rulebook does not specify.

## 7. Machine-readable summary

```text
score: 0.6
confidence: medium
critical_issues: 0
major_issues: 3
minor_issues: 3
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```
