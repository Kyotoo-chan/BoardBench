# Abalone: detaillierte Auswertung

[← Kurzüberblick](README.md)

**Modellsetup:** beide Implementierungen `gpt-5.6-sol:low`; jeweils drei neutrale Judges `gpt-5.6-sol:medium`. PDF, Prompt, Contract-v2-Profil und 38-Szenario-Rubrik sind identisch. Der zweite Lauf erhält zusätzlich nur die nach Original-Evaluation genehmigte Setup-Emphasis.

## Design und Reihenfolge

1. V2-Matrix und Human Decisions wurden geprüft und freigegeben.
2. Original-PDF-only wurde frisch generiert und vollständig evaluiert.
3. Einziger Fehler: klare Figure-1-Aufstellung 13/13 statt 14/14.
4. Da keine Quellenlücke betroffen war, wurde kein Gap-Clarified-Paket erzeugt.
5. Nutzerfreigabe für eine separat gelabelte Clear-Rule Setup-Emphasis.
6. Frische zweite Generierung und identische Evaluation.

## Evidenzgruppen

| Evidenz | Original | Setup-Emphasis |
|---|---:|---:|
| Agentischer Gate | PASS | PASS |
| Technische Checks | 4/4 | 4/4 |
| Rollouts | 100/100 | 100/100 |
| Interface | 8.888.062/8.888.062 | 8.528.518/8.528.518 |
| Spielerzahl | 3/3 | 3/3 |
| Clear-basis | 32/33 | 33/33 |
| Human-decision-basis | 5/5 | 4/5 |
| Coverage | 38/38 | 38/38 |
| Judges | 0,86 / 0,90 / 0,84 | 0,80 / 0,93 / 0,95 |
| Judge-Mittelwert (SD) | 0,867 (0,031) | 0,893 (0,081) |

## Alle Szenarien

| ID | Basis | Claims | Original | Emphasis |
|---|---|---|---:|---:|
| `ABAL-R01-exact-initial-setup` | clear | `ABAL-C-SETUP-FIGURE`, `ABAL-C-BOARD-61`, `ABAL-C-SETUP-COUNTS`, `ABAL-C-SETUP-ROWS` | **FAIL** | PASS |
| `ABAL-R02-single-marble-one-step-and-turn` | clear | `ABAL-C-ONE-MOVE`, `ABAL-C-ONE-STEP`, `ABAL-C-SIX-DIRECTIONS`, `ABAL-C-TURN-ORDER` | PASS | PASS |
| `ABAL-R03-two-marble-inline` | clear | `ABAL-C-GROUP-SIZE`, `ABAL-C-SAME-DIRECTION`, `ABAL-C-STRAIGHT-CONTIGUOUS`, `ABAL-C-INLINE` | PASS | PASS |
| `ABAL-R04-three-marble-broadside` | clear | `ABAL-C-GROUP-SIZE`, `ABAL-C-SAME-DIRECTION`, `ABAL-C-STRAIGHT-CONTIGUOUS`, `ABAL-C-BROADSIDE`, `ABAL-C-EMPTY-DESTINATION` | PASS | PASS |
| `ABAL-R05-four-marble-move-illegal` | clear | `ABAL-C-GROUP-SIZE`, `ABAL-C-MAX-THREE` | PASS | PASS |
| `ABAL-R06-two-v-one-sumito` | clear | `ABAL-C-SUMITO-SUPERIOR`, `ABAL-C-SUMITO-PATTERNS`, `ABAL-C-SUMITO-INLINE`, `ABAL-C-SUMITO-ADJACENT`, `ABAL-C-SUMITO-FREE-BEHIND` | PASS | PASS |
| `ABAL-R07-three-v-one-sumito` | clear | `ABAL-C-SUMITO-SUPERIOR`, `ABAL-C-SUMITO-PATTERNS` | PASS | PASS |
| `ABAL-R08-three-v-two-sumito` | clear | `ABAL-C-SUMITO-SUPERIOR`, `ABAL-C-SUMITO-PATTERNS` | PASS | PASS |
| `ABAL-R09-broadside-push-illegal` | clear | `ABAL-C-SUMITO-INLINE`, `ABAL-C-BROADSIDE`, `ABAL-C-EMPTY-DESTINATION` | PASS | PASS |
| `ABAL-R10-equal-strength-pushes-illegal` | clear | `ABAL-C-PATT-EQUAL` | PASS | PASS |
| `ABAL-R11-four-v-three-still-patt` | clear | `ABAL-C-PATT-FOUR-THREE`, `ABAL-C-MAX-THREE` | PASS | PASS |
| `ABAL-R12-blocked-sumito-illegal` | clear | `ABAL-C-SUMITO-FREE-BEHIND`, `ABAL-C-SUMITO-BLOCKED` | PASS | PASS |
| `ABAL-R13-gap-does-not-push` | clear | `ABAL-C-SUMITO-ADJACENT`, `ABAL-C-SUMITO-GAP` | PASS | PASS |
| `ABAL-R14-non-collinear-push-illegal` | clear | `ABAL-C-SUMITO-INLINE`, `ABAL-C-SUMITO-COLLINEAR` | PASS | PASS |
| `ABAL-R15-edge-ejection` | clear | `ABAL-C-EJECTION`, `ABAL-C-EDGE-EXCEPTION`, `ABAL-C-SUMITO-SUPERIOR` | PASS | PASS |
| `ABAL-R16-sixth-ejection-wins` | clear | `ABAL-C-SIXTH-WINS`, `ABAL-C-EJECTION` | PASS | PASS |
| `ABAL-R17-sumito-is-optional` | clear | `ABAL-C-SUMITO-OPTIONAL` | PASS | PASS |
| `ABAL-R18-patt-may-withdraw` | clear | `ABAL-C-PATT-EQUAL`, `ABAL-C-PATT-WITHDRAW` | PASS | PASS |
| `ABAL-R20-three-marble-inline` | clear | `ABAL-C-GROUP-SIZE`, `ABAL-C-STRAIGHT-CONTIGUOUS`, `ABAL-C-INLINE` | PASS | PASS |
| `ABAL-R21-two-broadside-from-longer-row` | clear | `ABAL-C-STRAIGHT-CONTIGUOUS`, `ABAL-C-BROADSIDE`, `ABAL-C-SUBSET-LONG-ROW` | PASS | PASS |
| `ABAL-R22-one-v-one-patt` | clear | `ABAL-C-PATT-EQUAL` | PASS | PASS |
| `ABAL-R23-two-v-two-patt` | clear | `ABAL-C-PATT-EQUAL` | PASS | PASS |
| `ABAL-R19-forced-pass-only-with-no-move` | human_decision | `ABAL-G-PASS` | PASS | **FAIL** |
| `ABAL-R24-player-count-and-bounded-playability` | clear | `ABAL-C-PLAYERS` | PASS | PASS |
| `ABAL-R25-single-step-e` | clear | `ABAL-C-ONE-STEP`, `ABAL-C-SIX-DIRECTIONS` | PASS | PASS |
| `ABAL-R26-single-step-ne` | clear | `ABAL-C-ONE-STEP`, `ABAL-C-SIX-DIRECTIONS` | PASS | PASS |
| `ABAL-R27-single-step-nw` | clear | `ABAL-C-ONE-STEP`, `ABAL-C-SIX-DIRECTIONS` | PASS | PASS |
| `ABAL-R28-single-step-w` | clear | `ABAL-C-ONE-STEP`, `ABAL-C-SIX-DIRECTIONS` | PASS | PASS |
| `ABAL-R29-single-step-sw` | clear | `ABAL-C-ONE-STEP`, `ABAL-C-SIX-DIRECTIONS` | PASS | PASS |
| `ABAL-R30-single-step-se` | clear | `ABAL-C-ONE-STEP`, `ABAL-C-SIX-DIRECTIONS` | PASS | PASS |
| `ABAL-R31-invalid-group-and-destination-boundaries` | clear | `ABAL-C-STRAIGHT-CONTIGUOUS`, `ABAL-C-GROUP-SIZE`, `ABAL-C-EMPTY-DESTINATION`, `ABAL-C-SUMITO-INLINE` | PASS | PASS |
| `ABAL-R32-broadside-blocked-and-offboard` | human_decision | `ABAL-G-BROADSIDE-DESTINATIONS` | PASS | PASS |
| `ABAL-R33-patt-broadside-withdrawal` | clear | `ABAL-C-PATT-WITHDRAW`, `ABAL-C-BROADSIDE` | PASS | PASS |
| `ABAL-R34-crossing-angle-breaks-patt` | clear | `ABAL-C-PATT-EQUAL`, `ABAL-C-PATT-CROSSING` | PASS | PASS |
| `ABAL-R35-three-v-two-edge-ejects-one` | clear | `ABAL-C-SUMITO-PATTERNS`, `ABAL-C-EJECTION`, `ABAL-C-EDGE-EXCEPTION` | PASS | PASS |
| `ABAL-R36-terminal-api-and-returns` | human_decision | `ABAL-G-TERMINAL-API`, `ABAL-G-RETURNS` | PASS | PASS |
| `ABAL-R37-action-serialization-is-unique` | human_decision | `ABAL-G-ACTION-UNIQUE` | PASS | PASS |
| `ABAL-R38-public-contract-observability` | human_decision | `ABAL-G-PUBLIC-STATE`, `ABAL-G-PLAYER-MAPPING` | PASS | PASS |

## Bestätigte Defekte

**Original:** `ABAL-R01` — Figure 1 verlangt 14 schwarze und 14 weiße Kugeln; tatsächlich 13/13.

**Setup-Emphasis:** `ABAL-R19` — in einem Zustand ohne legale Bewegung fehlt der genehmigte Forced Pass.

## Judge-Evidenz

Alle drei Original-Judges bestätigen nur den Setup-Defekt. Alle drei Emphasis-Judges bestätigen den fehlenden Forced Pass. Ein Emphasis-Judge meldet zusätzlich mögliche doppelte Aktionsserialisierungen; `ABAL-R37` besteht deterministisch, daher bleibt dies ein Regressionkandidat.

## Annahmen

- Original: 2 deklarierte materielle Annahmen.
- Setup-Emphasis: 2 deklarierte materielle Annahmen.

## Provenienz

- Regelwerk SHA-256: `c293ed5d319ccb4fa5725921613f4a05ba2453074d2b2dcdc11cdeb9f8570550`
- Rubrik SHA-256: `be0b349288ab099973bf2ead1e6f793a7f7b866756b4be83bae1aba07a973935`
- Adapter SHA-256: `7b83946eb17394320b77b5b2da3925172a14ef8434322243080c498c707141da`
- Original-Code SHA-256: `4098c2dfc360915fd2760393907fe107e878c7b9a4ac3d2c4fcebab71b7e4ccd`
- Emphasis-Code SHA-256: `e90443a23286c3e13645f0b464b346834db8c7641b66d6db913a4231f5c6f446`

## Artefakte

- Vergleich: [`v2/COMPARISON.md`](v2/COMPARISON.md)
- Originalprofil: [`v2/original_result.json`](v2/original_result.json)
- Emphasisprofil: [`v2/setup_emphasis_result.json`](v2/setup_emphasis_result.json)
- Befunde: [`v2/original_findings.md`](v2/original_findings.md) · [`v2/setup_emphasis_findings.md`](v2/setup_emphasis_findings.md)
- Ausführbare Definitionen: `../../../checks/scenarios/abalone_v2.json`
- Kompakte Rohartefakte: `v2/raw/study_artifacts.tar.gz`

Die frühere Abalone-Präsentation wird durch diese V2-Ansicht ersetzt und bleibt über Git erreichbar.
