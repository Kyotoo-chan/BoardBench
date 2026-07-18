# Preregistered mutation audit

Classification uses implementation code plus the frozen detector scenarios. `Indeterminate` means the environment behavior is narrower than canonical but does not exactly implement the mutation. Judge counts require an explicit mutation-specific finding among the three blind canonical reviews.

## Manipulated JSON

| Run | Mutation | Implemented | Declared in assumptions | Frozen detector | Judges |
|---|---|---|---|---|---:|
| `json_mutated_1` | J1: two Acker → two coins | Partial: two fields pay 2 and also unlock field 3; an existing third field pays 0 | No | R14/R15 UNTESTABLE | 3/3 |
|  | J2: lucrative Weinbrand | Yes: thresholds 2/4/6/8 | No | R36 CRASH | 3/3 |
|  | J3: all 157 active | No: selected types, but incorrect 109-card inventory | Yes: chose publisher's 129-card subset | R01 FAIL (109) | 0/3 |
| `json_mutated_2` | J1 | No: two Acker unlock field 3 and pay 0 | No | R14/R15 UNTESTABLE | 0/3 |
|  | J2 | Yes: thresholds 2/4/6/8 | No | R36 CRASH | 3/3 |
|  | J3 | No: 129-card subset | Yes: explicitly chose publisher's 129 cards | R01 PASS | 0/3 |
| `json_mutated_3` | J1 | No/absent: Acker omitted | No | R14/R15 UNTESTABLE | 0/3 |
|  | J2 | No/absent: Weinbrand omitted | No | R36 CRASH | 0/3 |
|  | J3 | No: only 104 base cards | Yes: selected 129-card publisher interpretation but failed to implement it | R01 FAIL (104) | 0/3 |

## Manipulated PDF

| Run | Mutation | Implemented | Declared in assumptions | Frozen detector | Judges |
|---|---|---|---|---|---:|
| `pdf_mutated_1` | P1: active-only harvest | Indeterminate: broad inactive interrupts are blocked, but an inactive phase-3 controller can harvest | No | R23 FAIL | 3/3 |
|  | P2: active draws three | Yes | No | R09 FAIL | 3/3 |
|  | P3: sorting allowed | No: front-card planting remains mandatory; no reorder action | No | R37 PASS | 0/3 |
| `pdf_mutated_2` | P1 | Indeterminate: no general inactive interrupt, but phase-3 nonactive controller may harvest | No | R23 UNTESTABLE | 3/3 |
|  | P2 | Yes | Yes: explicitly selected active-player draw-three text | R09 UNTESTABLE | 3/3 |
|  | P3 | No: front-card planting; no reorder action | No | R37 UNTESTABLE | 0/3 |
| `pdf_mutated_3` | P1 | Indeterminate: voluntary harvests restricted to active player, with mixed forced paths | No | R23 FAIL | 3/3 |
|  | P2 | Yes | No | R09 FAIL | 3/3 |
|  | P3 | No: front-card planting; no reorder action | No | R37 PASS | 0/3 |

## Main finding

The intervention was taken up selectively rather than mechanically. P2 appeared in all three manipulated-PDF implementations; J2 appeared in two of three manipulated-JSON implementations. P3 and J3 appeared in none. P1 produced a canonical deviation in all three PDF implementations but not an exact active-only model. J1 appeared only partially in one run.

The frozen detector suite under-detected source uptake because all J1/J2 detector cases in manipulated-JSON runs were UNTESTABLE or CRASH, and all three mutation detectors in `pdf_mutated_2` were UNTESTABLE. The neutral judges explicitly caught every implemented J2 and P2 deviation and every P1-related deviation, but did not flag mutations that the implementations resisted.

The underlying implementations, scenario records, assumptions, and judge reviews are preserved under `runs/<run-id>/`.
