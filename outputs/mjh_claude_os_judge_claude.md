# Mah-Jongg (oneshot) — LLM judge review

## 1. Score

- `score: 0.7`
- `confidence: medium`

The mechanical core is faithful and the settlement engine is validated: I hand-traced both worked examples from section 10 and the code reproduces them exactly (Example 1 East win → +456/-182/-152/-122; Example 2 West win with Südwind's Große-Drei-Drachen 28×2⁶=1792 capped to 500 → -1036/+1418/+192/-574), including East double-pay, pairwise differences, and the limit cap. Claims/priority, robbing the kong, both kong variants, washout with the last-discard win window, and turn order are all correct against the rule text. It stays below 0.8 because hand *valuation completeness* is only partial — most limit hands are undetected, several doublings and all Mahjong-tile bonus points are missing, and claim-completed winning sets are mis-scored as concealed — so `returns` are wrong for many non-trivial wins. Confidence is medium because the limit-hand figure images and some per-figure OCR in section 10 were unavailable/garbled.

## 2. Top findings

**Finding 1 — Hand valuation is only partially implemented (major)**
- Evidence: `_hand_doublings` implements only Kein Chi, Alle verdeckt, Null-Punkte, and the one-suit family. Missing from the section 8 tables: all Mahjong-tile bonuses (Schlussziegel von der Mauer/einzig möglicher/completes-pair 2–4 pts), Nur Hauptziegel, Schlussziegel von der toten Mauer, letzter Mauerziegel, Schlussziegel = letzter Abwurf, Beraubung des Kang (+1x), Mahjong nach Ruf-zu-Beginn. `_value` auto-detects only 4 limit hands (seven pairs, 13 orphans, pure honors, terminals-only); the ~15 other named limit hands (winding snake, four kong, three scholars, four blessings, imperial green, nine lanterns, hidden treasure, heaven/earth, kong-on-kong, plum blossom, moon, pillar, ninefold) fall back to generic scoring.
- Why it matters: returns are a first-class benchmark output; any win invoking an unimplemented bonus/doubling/limit hand yields a wrong (usually too low) score. The *structure* is right, but coverage is incomplete.
- Next action: prioritize the always-applicable doublings (Beraubung, last-tile, dead-wall tile) and add limit-hand detectors; document precisely which remain unscored.

**Finding 2 — Claim-completed winning set scored as concealed (major)**
- Evidence: `_apply_claim`/`_apply_robkong` do `s.hands[cur][t] += 1` then `_win`; the claimed tile enters the concealed hand, so `_best_decomp` scores that set with `concealed=True`. Rulebook: a pong/chi completed with a called tile "muss offen ausgelegt werden und gilt als offen."
- Why it matters: over-scores the winning set (e.g. 4 vs 2 for a suit pong) and can spuriously grant "Alle Figuren verdeckt" (a full doubling) when the winner's only exposed set is the claimed one.
- Next action: mark the win-completing meld as open unless the win is a self-draw; track the winning-tile source in `GameState`.

**Finding 3 — Single-game scope drops all of Section 6 (major, documented)**
- Evidence: `ROUND_WIND="WE"` fixed; player 0 always East; no wind draw, no S→O/W→S/N→W/O→N rotation, no 4-round match, no "Neunmal Mah-Jongg" wind change, no game-count stop rule.
- Why it matters: an entire rulebook chapter is unmodeled; own-wind/round-wind scoring never varies. Acceptable as a one-game environment but limits fidelity to the full ruleset.
- Next action: state explicitly that the environment models one game; optionally add a match wrapper.

**Finding 4 — In-file smoke test never exercises the (validated) scoring engine (minor)**
- Evidence: the harness always takes `acts[0]`. In discard phase `Discard:` sorts before `Mahjong`, so self-draw wins are never chosen; runs almost always reach washout → `returns=[0,0,0,0]`, and `sum(r)==0` then proves nothing about scoring.
- Why it matters: the strongest part of the file (settlement) is untested by its own harness.
- Next action: add the section-10 examples as deterministic assertions.

**Finding 5 — Third suit and 7-pairs shape are assumptions (question)**
- Evidence: `SUITS=("B","K","Z")` with `"Z"` marked "(3rd assumed)"; the rule text names only Bambus/Kreis by example. `is_seven_pairs` accepts four-of-a-kind as two pairs (`v % 2 == 0`).
- Why it matters: tile universe and a limit-hand definition rest on unstated readings.
- Next action: confirm 3 suits / third-suit label and whether a kong may count as two of the "genau sieben Paare."

## 3. Rule coverage review

| Rule area | Status | Evidence | Notes |
|---|---|---|---|
| Setup / components | partially covered | 136 tiles (34×4), 13 dealt each, East draws 14th, 14-tile dead wall reserved | Flowers/seasons removed (rulebook-sanctioned); deal modeled as chance, not 4-2-4-2 blocks; wind draw skipped |
| Player count / turn order | covered correctly | `num_players=4`, right-neighbor `(p+1)%4`, counterclockwise E→S→W→N | Matches "gegen den Uhrzeigersinn", "rechter Nachbar ist als nächstes dran" |
| Legal actions | covered correctly | discard/kong/win in `_discard_actions`; staged claim actions; chance deal/draw | `legal_actions ⊆ apply_action`; every non-terminal state has ≥1 action |
| State transitions | covered correctly | claim stages A>B>C, pong/kong/chi resolution, added vs concealed kong, robbing | Concealed-pong→kong routed via `ConcealedKong` (stays concealed); win-completion open to all seats, chi only to right neighbor |
| Terminal conditions | covered correctly | Mahjong call or living-wall exhaustion; last drawer still discards/others may claim | Matches section 5; washout → repeat (no scoring) |
| Scoring — settlement | covered correctly | `returns` reproduces both section-10 examples exactly, incl. East ×2 and pairwise diffs | Zero-sum guaranteed; limit cap applied |
| Scoring — hand valuation | partially covered | point/doubling tables partly encoded; großes/kleines Drachen/Freuden, one-suit correct | Missing many doublings, all Mahjong-tile bonuses, most limit hands; claim-win concealed bug (F2) |
| Rendering / action names | covered correctly | `render` deterministic full-truth; identity `action_to_name`/`name_to_action` | Names use tile labels (Bambus1, DracheRot), no raw indices; round-trip exact |
| Chance handling | covered correctly | `chance_outcomes` = pool[t]/total, sums to 1; deal & draw as chance nodes | Dead-wall tiles left in draw pool, capped by `wall` count (harmless abstraction) |
| Hidden information | covered correctly | `information_state` hides others' hands (count only); `render` flagged non-visible | Action names don't leak private tiles |
| Simultaneous moves | n/a | reactions serialized by seat within priority stages | Rulebook implies priority, not true simultaneity; serialization is reasonable |
| Rounds / winds rotation | missing | Section 6 not modeled | See F3 |
| Flowers / seasons | missing (sanctioned) | rulebook allows removal | Related bonus points/doublings out of scope |

## 4. Unsupported assumptions or invented rules

Harmless conventions:
- Player 0 = East, no randomized wind draw (relabeling only for a single game).
- East's 14th tile modeled as a first draw rather than dealt.
- Dead wall = 14 tiles reserved by count; its specific composition folded into the draw pool.
- Kong replacement drawn from the living wall — this actually follows the rule text ("Ersatzstein von der lebenden Mauer"), not standard mahjong; correct to prefer the rulebook.
- Claim priority Mahjong > Pong/Kong > Chi, head-bumped by seat order — a defensible reading of the listed reaction order (rulebook does not state it explicitly).

Risky / fidelity-affecting:
- `ROUND_WIND` fixed to East and `LIMIT=500` taken from the worked example as a global constant.
- Third suit "Zeichen" invented (not named in the text).
- Seven pairs counts a kong as two pairs.
- Claim-completed winning set treated as concealed (contradicts explicit "gilt als offen").

## 5. Missing scenario tests

- Section-10 Example 2, Südwind hand: exposed Kang(Drache)+Pong(Süd wind)+Pong(Drache)+Pong(Drache) as a non-winner → assert `_value == 500` (1792 capped).
- Full Example 1 settlement: build the four hands, force East's Mahjong, assert `returns == [456, -182, -152, -122]`.
- Full Example 2 settlement: West Mahjong, assert `returns == [-1036, 1418, 192, -574]`.
- Robbing the kong: `AddedKong:<t>` with a right-seat player holding a chi that `t` completes → sequence `AddedKong` then `Mahjong`; assert victim's meld reverts to `pong` and winner ends the game.
- Washout boundary: drive `wall` to 0, confirm the last drawer may `Discard`/`Mahjong` and that a following unclaimed discard yields `phase=terminal, winner=None, returns=[0,0,0,0]`.
- Concealed-pong→kong: hold four identical, `ConcealedKong:<t>`, assert meld stored concealed and a replacement draw occurs.
- Priority: same discard claimable as pong by one seat and chi by the right neighbor → assert `Pong` preempts `Chi`.

## 6. Open questions for the human

- Is this intended as a single game (as implemented) or should the four-round match with wind rotation from Section 6 be modeled?
- Are there exactly three suits, and is "Zeichen" the correct third-suit label? (Not in the rule text.)
- For "genau sieben Paare," may a four-of-a-kind count as two pairs, or must the pairs be distinct?
- Should limit hands and the missing doublings/Mahjong-tile bonuses be scored for benchmark parity, or is the current documented subset acceptable?
- Is `LIMIT=500` a fixed benchmark value or a per-table agreement that should be a parameter?

## 7. Machine-readable summary

```text
score: 0.7
confidence: medium
critical_issues: 0
major_issues: 3
minor_issues: 4
needs_rulebook_clarification: true
needs_code_change: true
needs_more_tests: true
```
