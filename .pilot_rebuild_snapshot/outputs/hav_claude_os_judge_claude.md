I don't have a write tool available in this session, so I can't create `outputs/havannah_oneshot_judge.md` directly. Here is the complete judge reply to save to that path.

---

# Havannah (oneshot) — LLM judge review

Scope: rule fidelity of `outputs/havannah_oneshot.py` against the supplied rulebook images only (`inputs/rulebook_pages/game_rules/page-1..3.png`). Page 1 is the rules; pages 2-3 are strategy/tactics and add no mechanics. Deterministic checks were not rerun and were not used to set the score.

## 1. Score

- `score: 0.8`
- `confidence: medium`

The implementation is a faithful, clean reading of the one rules page: correct hexagonal board (169 points, side 8 / radius 7), correct turn order, placement-only transitions, and correct detection of bridge and fork. The one more-than-minor problem is the ring detector: it only finds rings that enclose an empty or enemy cell, but the rulebook explicitly states (bolded "Wichtig") that the enclosed point may also be the player's *own* stone, and that case is missed. The remaining deviations (full-board draw, fixed colours, unenforced stone supply) are documented, harmless assumptions, which is why this lands at 0.8 rather than lower or higher.

## 2. Top findings

### Finding 1 — Ring enclosing only the mover's own stones is not detected (severity: major)
- Evidence (code): `_has_ring` builds `not_c` = all cells that are **not** the mover's colour (empty + enemy), floods inward from the boundary, and reports a ring iff some `not_c` cell is unreachable. If every enclosed cell is the mover's own colour, `not_c` contains no trapped cell, so no ring is reported.
- Evidence (rulebook, page 1): "Der eingeschlossene Punkt oder die eingeschlossenen Punkte können leer, **eigen** oder vom Gegner besetzt sein", reinforced by the bolded **"Wichtig"** note that it is irrelevant whether/by whom the enclosed points are occupied. So a loop closed around an own stone (e.g. 6 stones around 1 own centre, the centre filled before the loop closes) is a legal win.
- Why it matters: this is a missed terminal/win condition on an explicitly emphasised rule. In rollouts or scenario checks that reach such a position the game wrongly continues, diverging from the reference. The scenario is narrow (you must fill your own ring interior before closing the loop) but reachable.
- Suggested next action: detect rings via an actual cycle in the colour adjacency graph that bounds at least one cell (equivalently: test whether the mover's own group has a bounded face), not only via complement enclosure. Add the scenario test in section 5.

### Finding 2 — Full-board draw is invented and unreachable under the real component count (severity: minor / assumption)
- Evidence: rulebook ships "55 schwarze und 55 rote Steine" (110 stones) for 169 points and says nothing about draws. The code does not enforce the supply and declares `draw` only when all 169 cells are filled.
- Why it matters: the draw branch can only fire after 169 placements, which the real 110-stone supply cannot produce; it is an invented terminal on an otherwise-unreachable state. Practically harmless (Havannah is effectively drawless) but it is an added rule.
- Suggested next action: confirm the draw convention with the human; optionally enforce the 110-stone cap or document the divergence explicitly.

### Finding 3 — Colour assignment / first player simplified (severity: minor / assumption)
- Evidence: rulebook "Die Farbe wird ausgelost; Rot fängt an." The code fixes Red = player 0 and Red to move first, dropping the random colour draw.
- Why it matters: harmless and well-documented; only relevant if the benchmark cares about the chance colour assignment. Keeps the game deterministic, which is desirable here.
- Suggested next action: none required; keep the documented assumption.

### Finding 4 — Stone supply not modelled (severity: question / minor)
- Evidence: code comment says "~55/56" while the rulebook clearly states 55 each; supply is never enforced, so a game may exceed 110 stones.
- Why it matters: irrelevant to figure completion (55 stones is ample for any figure) but it is a stated component the model ignores.
- Suggested next action: fix the comment to 55; decide whether to enforce the cap.

### Positive observations (no action needed)
- Bridge (`corners >= 2` in one connected component) and fork (`>= 3` distinct sides, corners excluded) match the rulebook precisely, including "Die Eckpunkte gehören nicht zu den Seiten."
- Ring detection is correct for the empty/enemy-enclosure cases and correctly does *not* false-trigger on an enemy enclosure (the flood passes through enemy cells).
- Placement-only, no capture/move ("Es wird nicht geschlagen und nicht gezogen"), no pass, alternate turns, immutable `apply_action`, terminal has no legal actions, `returns` = +1/-1/0 per player — all consistent.
- The model correctly treated pages 2-3 as strategy only and, importantly, did **not** invent a swap/pie rule that the rulebook does not mention.

## 3. Rule coverage review

| rule area | status | evidence | notes |
|---|---|---|---|
| Setup / board & components | covered correctly | 169 cells, R=7 (side 8), cube coords `_all_cells`/`_on_board` | matches "169 Schnittpunkte"; stone count 55 noted but not enforced |
| Player count & turn order | covered correctly | `NUM_PLAYERS=2`, Red first, alternation in `apply_action` | random colour draw dropped (documented) |
| Legal actions | covered correctly | `legal_actions` = all empty cells; no pass | matches place-on-any-free-point |
| State transitions | covered correctly | place own stone, switch player, stones stay | no capture/move, immutable copy |
| Terminal — bridge | covered correctly | `_has_bridge_or_fork` corners>=2 | "zwischen zwei beliebigen Eckpunkten" |
| Terminal — fork | covered correctly | sides>=3, corners excluded via `_side_of` | "drei beliebige Seiten", corners not sides |
| Terminal — ring | partially covered | `_has_ring` complement flood | correct for empty/enemy-enclosed; **misses own-stone-enclosed** (Finding 1) |
| Draw | unclear / invented | full-board -> draw | rulebook silent; unreachable under 110 stones |
| Scoring / returns | covered correctly | `returns` +1/-1, 0 draw | one value per player |
| Rendering / action names | covered correctly | `place:x..y..z..`, p/n signs, round-trips | signs unambiguous; corners marked `+` when empty |
| Chance | n/a | none | only colour draw, deliberately omitted |
| Hidden info / simultaneous | n/a | none | perfect-information sequential |

## 4. Unsupported assumptions or invented rules

Harmless conventions:
- Cube-coordinate action notation (`place:x..y..z..`) — rulebook gives no labels; explicit, stable, round-tripping. Good.
- Red fixed as player 0 and first mover instead of a random colour draw — documented.
- Render symbols `R`/`B`/`.`/`+` — cosmetic, deterministic.

Riskier / invented:
- Full-board → draw: a terminal condition not in the rulebook, on a state the real 110-stone supply cannot reach. Low impact but genuinely invented.
- "Only the mover can create a figure": logically forced (you only place your own colour), so not a real assumption — fine.

Notable: no invented swap rule, no invented capture/removal (e.g. "tote Gruppe" on page 3 is correctly treated as strategy, not a removal mechanic).

## 5. Missing scenario tests

Prefer action-name sequences (`place:x..y..z..`). Highest value first:
- **Ring around own stone (exposes Finding 1):** fill an own centre, surround with five own stones, place the sixth to close — expect a ring win; current code does not terminate.
- Ring around an empty cell: 6 stones around 1 empty centre — expect ring win, figure `ring`.
- Ring around an enemy stone: enemy stone in the centre, own loop closes around it — expect ring win.
- Near-miss ring: same loop with one gap — expect no win; with one enclosed cell also touching the board edge (pocket against the rim) — expect no win.
- Loop broken by enemy colour inside the would-be ring path — expect no win (single-colour-group requirement).
- Minimal bridge: straight chain joining two adjacent corners — expect win, figure `bridge`; and a bridge path interrupted by an enemy stone — expect no win.
- Minimal fork: chain touching three distinct sides — expect win, figure `fork`; and a chain touching two sides plus a corner only — expect no win (corner is not a side).
- Multi-figure move: a single placement completing both a bridge and a fork — expect win and both figures listed in `render`.
- Robustness: `apply_action` on an occupied cell and on an off-board action both raise; `legal_actions` is empty at a terminal state.
- Action round-trip on signed/zero/corner coordinates, e.g. `place:xp7_yn7_z0`, `place:x0_y0_z0`, `place:xn7_yp7_z0`.

## 6. Open questions for the human

1. Does the ring rule, as you read the scan, require counting a loop closed around the player's **own** stone(s) as a win? The visible text ("...leer, eigen oder vom Gegner...") says yes; confirming locks Finding 1 as a code bug to fix.
2. How should a no-figure full position resolve — draw, or is it simply unreachable and the branch should be removed / the 110-stone cap enforced?
3. Is fixing Red as the first player (dropping the random colour draw) acceptable for the benchmark, or should the colour draw be modelled as a chance node?

## 7. Machine-readable summary

```text
score: 0.8
confidence: medium
critical_issues: 0
major_issues: 1
minor_issues: 3
needs_rulebook_clarification: false
needs_code_change: true
needs_more_tests: true
```

---

Headline: the code is a solid, faithful reading (bridge/fork/placement/turn-order all correct, no invented swap rule), but the ring detector misses the rulebook's explicit "own-stone-enclosed" case — a real but narrow missed-win. The passing `06_action_language` check (1.3M round-trips) and `05_random_rollouts` (100/100) confirm the API is sound but, as expected, don't exercise that edge case. Want me to also draft the cycle-based ring fix?
