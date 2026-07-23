# CATAN 2022 fixed four-player packet — grouped evaluation

> Technically robust; 43/44 clear-rule scenarios and 11/15 approved-decision scenarios passed; all 59 scenarios were evaluated. Evidence groups remain separate.

## Frozen condition

- Sources: `CATAN22-RULES` (`e0673fa9…cf3`) and matching `CATAN22-ALMANAC` (`8fe89cc6…11bc`).
- Scope: fixed four-player beginner setup; strict roll → trade → build.
- Implementation: `catan_codex_ag.py`, SHA-256 `bcd19e4a…65122`.
- Generation: native Codex `gpt-5.6-sol:low`, protocol `agentic-v3.1`, one source-audit repair.
- Evaluation rubric: `catan-2022-fixed4-v1-2026-07-23`.

## Separate evidence groups

| Evidence group | Raw result | Interpretation |
|---|---:|---|
| Technical gate, checks 01–04 | 4/4 checks; 12/12 units | Passed |
| Runtime robustness, check 05 | 100/100 rollouts | Passed under seed 1, max 1000 steps |
| Interface, check 06 | 999952/999952 | Passed action-name/API checks |
| Clear cited scenarios | 43/44 = 0.977 | One clear-rule reveal-state failure |
| Approved human decisions | 11/15 = 0.733 | Three failures and one crash |
| Scenario coverage | 59/59 = 1.000 | No `UNREACHED` or `UNTESTABLE` |
| Neutral Judge 1 | 0.58 | High confidence |
| Neutral Judge 2 | 0.66 | High confidence |
| Neutral Judge 3 | 0.63 | High confidence |
| **Judge mean (n=3)** | **0.623; sample SD 0.040** | Separate fallible review signal |

No combined correctness score is calculated.

## Deterministic scenario discrepancies

| Scenario | Basis | Outcome | Confirmed observable deviation |
|---|---|---|---|
| `CAT-D07-road-building-max-feasible-one` | human decision | `FAIL` | After the only remaining road is placed, phase stays `road_building` instead of resuming; stock is not used to stop further free-road actions. |
| `CAT-D08-victory-after-first-free-road` | human decision | `CRASH` | A winning free road clears `pending` in `_victory`, then `place_free_road` dereferences it, raising `TypeError`. |
| `CAT-D11-ten-at-own-turn-start-wins` | human decision | `FAIL` | `end_turn` activates a player already at ten but does not check victory before roll. |
| `CAT-R43-newly-bought-vp-card-can-win` | clear | `FAIL` | The terminal win occurs, but the newly bought winning VP card is not moved into public played/revealed state. |
| `CAT-D12-reveal-minimum-victory-cards` | human decision | `FAIL` | The minimum required VP cards remain in the concealed development hand instead of being revealed in hand order. |

The remaining 54 scenarios passed.

## Confirmed defects

1. **Road Building stock/completion:** the subphase ignores zero remaining road pieces after its first placement and can continue or mutate later during a query (`implementation.py:212–214, 413–415`).
2. **Road Building terminal crash:** all three neutral judges independently identified the same `pending=None` dereference; deterministic scenario `CAT-D08` reproduces it (`implementation.py:316–318, 441–445`).
3. **Missing own-turn-start victory:** all judges and `CAT-D11` agree that `end_turn` omits the required pre-roll check (`implementation.py:328–331`).
4. **Missing VP-card revelation:** `CAT-R43`, `CAT-D12`, and all judges agree that `_victory` counts hidden cards without revealing the minimum required cards or updating the public winning score (`implementation.py:155–163, 441–443, 501–525`).

Three of these four defect groups depend on approved executable conventions; the VP purchase/reveal requirement also has direct publisher support.

## Independent-review signals not yet deterministic failures

- Two judges report that public `render()` includes concealed VP points (`implementation.py:527–530`). Whether `render` is public or privileged is not frozen; retain this as an adjudication/interface question and regression candidate.
- One judge reports that availability of `take` actions during trade-offer construction reveals opponents’ exact resource identities (`implementation.py:215–229`). This is plausible under the clear secrecy rule but lacks an approved deterministic observation scenario.
- Judges note that `legal_actions()` may mutate an exhausted Road Building state (`implementation.py:212–214`). Query purity is an interface question not fixed by the publisher sources.

## Evaluator issue and replacement judges

The first neutral prompt inherited one Bohnanza-specific sentence. All three original judge artifacts are retained as `judge_v1_contaminated_*` and excluded from the mean. `JUDGE_PREFLIGHT_V2.md` records the issue and replacement prompt SHA-256 `137adad3…27ae`. Three new mutually blind reviews used the unchanged sources, facts, implementation, model, and `medium` thinking. Evaluator retry usage is retained in resource totals.

## Assumptions and unscored gaps

- The implementation chooses all-or-none payment when a resource pile cannot satisfy production. Resource-shortage states remain unscored.
- Random theft is uniform over the victim’s resource multiset, matching the approved convention.
- No outside CATAN rules were used.

## New regression candidates

1. Road Building with one road piece and multiple graph-legal edges.
2. Winning on the first and separately the second free road.
3. Public terminal score and minimum VP reveal after a bought card and after multiple hidden cards.
4. Opponent-resource privacy during staged trade action enumeration.
5. Public versus privileged `render()` semantics for hidden VP cards.
6. State immutability across repeated `legal_actions()` calls in automatic-completion phases.

## Reproducibility

- Suite: `b7a4f653…26cfe`
- Adapter: `fce085d7…83454`
- Scenario runner: `d852145a…6f762`
- Neutral judge prompt v2: `137adad3…27ae`
- Raw scenarios, checks, usage, reviews, events, implementation, and method copies are under `runs/base_packet/` and `method/`.
- Machine-readable profile: `result.json`; derived profile: `result.md`.

No implementation was repaired after evaluation. Any correction requires a new generation/run so this evidence remains immutable.
