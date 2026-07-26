# Wizard: detaillierte Auswertung

[← Kurzüberblick](README.md)

**Modellsetup für beide Bedingungen:** Implementierung mit `gpt-5.6-sol`, Thinking `low`; drei neutrale Judges mit `gpt-5.6-sol`, Thinking `medium`. Original und Clarified verwendeten dasselbe PDF, denselben Contract-v2-Vertrag, dasselbe Profil, denselben Promptinhalt und dieselbe eingefrorene 34-Szenario-Rubrik. Clarified erhielt zusätzlich ausschließlich `clarifications_v2.json`.

## Auswertungsfolge

1. Agentischer Generations-Gate und evaluatorneutrale Selbstprüfungen.
2. Technische Checks 01–04.
3. 100 reproduzierbare Rollouts.
4. Vollständiger Action-Name-/Action-Data-Roundtrip.
5. Unterstützte Spielerzahlen 3–6 sowie Ablehnung von 2 und 7.
6. 34 zitierte V4-Szenarien, getrennt nach `clear` und `human_decision`.
7. Drei gegenseitig blinde neutrale Judges pro Bedingung.
8. Getrennte Ressourcen-, Annahmen- und Provenienzevidenz.

## Evidenzgruppen

| Evidenz | Original-PDF | PDF + Klarstellung |
|---|---:|---:|
| Agentischer Gate | PASS | PASS |
| Technische Checks 01–04 | 4/4 | 4/4 |
| Random Rollouts | 100/100 | 100/100 |
| Action-Language | 226.118/226.118 | 226.148/226.148 |
| Spielerzahl-Probes | 6/6 | 6/6 |
| Szenarien gesamt | 31 PASS / 3 FAIL | 33 PASS / 1 FAIL |
| Clear-basis | 22/23 | 23/23 |
| Human-decision-basis | 9/11 | 10/11 |
| Ausgewertete Abdeckung | 34/34 | 34/34 |
| Clear Claim-Mapping/Evaluation | 50/50 | 50/50 |
| Judge-Scores | 0,78 / 0,72 / 0,72 | 0,91 / 0,88 / 0,90 |
| Judge-Mittelwert (SD) | 0,740 (0,035) | 0,897 (0,015) |

Diese Gruppen werden nicht zu einem gemeinsamen Korrektheitsscore verrechnet.

## Alle Regelszenarien

| ID | Basis | Atomare Claims | Original | Clarified |
|---|---|---|---:|---:|
| `WIZ-R01-cited-card-totals` | clear | `WIZ-C-INV-TOTAL`, `WIZ-C-INV-SUITS`, `WIZ-C-INV-WIZARDS`, `WIZ-C-INV-JESTERS` | PASS | PASS |
| `WIZ-R02-exact-suit-rank-inventory` | human_decision | `WIZ-G-EXACT-INVENTORY` | PASS | PASS |
| `WIZ-R03-round-count-by-player-count` | clear | `WIZ-C-PLAYERS-SUPPORTED`, `WIZ-C-END-3P`, `WIZ-C-END-4P`, `WIZ-C-END-5P`, `WIZ-C-END-6P` | PASS | PASS |
| `WIZ-R04-first-round-deal-and-start` | human_decision | `WIZ-G-FIRST-DEALER-RESET` | **FAIL** | PASS |
| `WIZ-R05-revealed-wizard-requires-color` | human_decision | `WIZ-G-WIZARD-CHOICE-MANDATORY` | PASS | PASS |
| `WIZ-R06-prediction-domain` | human_decision | `WIZ-G-BID-DOMAIN` | PASS | PASS |
| `WIZ-R07-base-bids-may-equal-trick-count` | human_decision | `WIZ-G-BID-SUM` | PASS | PASS |
| `WIZ-R08-follow-suit-with-special-exceptions` | clear | `WIZ-C-FOLLOW-SUIT`, `WIZ-C-WIZARD-ALWAYS-LEGAL`, `WIZ-C-JESTER-ALWAYS-LEGAL` | PASS | PASS |
| `WIZ-R09-void-player-may-discard-or-trump` | clear | `WIZ-C-VOID-DISCARD`, `WIZ-C-VOID-TRUMP` | PASS | PASS |
| `WIZ-R10-first-wizard-wins-midgame` | clear | `WIZ-C-WIZARD-PRIORITY`, `WIZ-C-WIN-FIRST-WIZARD`, `WIZ-C-TRICK-CREDIT`, `WIZ-C-NEXT-LEADER` | PASS | PASS |
| `WIZ-R11-first-wizard-also-wins-final-round` | clear | `WIZ-C-WIN-FIRST-WIZARD` | PASS | PASS |
| `WIZ-R12-jester-then-ordinary-establishes-suit` | clear | `WIZ-C-JESTER-ORDINARY-LEADS` | PASS | PASS |
| `WIZ-R13-leading-jesters-wait-for-first-color` | human_decision | `WIZ-G-JESTER-CHAIN` | PASS | PASS |
| `WIZ-R14-jester-wizard-keeps-trick-colorless` | human_decision | `WIZ-G-JESTER-WIZARD` | **FAIL** | **FAIL** |
| `WIZ-R15-all-jesters-first-wins` | clear | `WIZ-C-ALL-JESTERS-FIRST`, `WIZ-C-TRICK-CREDIT` | PASS | PASS |
| `WIZ-R16-highest-trump-wins-without-wizard` | clear | `WIZ-C-WIN-HIGHEST-TRUMP`, `WIZ-C-JESTER-NOT-TRUMP` | PASS | PASS |
| `WIZ-R17-highest-led-color-wins-without-trump` | clear | `WIZ-C-WIN-HIGHEST-LED` | PASS | PASS |
| `WIZ-R18-final-round-scoring-and-winner` | clear | `WIZ-C-SCORE-EXACT-BONUS`, `WIZ-C-SCORE-EXACT-TRICKS`, `WIZ-C-SCORE-OVER`, `WIZ-C-SCORE-UNDER`, `WIZ-C-END-SCORE-FIRST`, `WIZ-C-END-HIGHEST-WINS` | PASS | PASS |
| `WIZ-R19-joint-winners-on-equal-high-score` | human_decision | `WIZ-G-TIE` | PASS | PASS |
| `WIZ-R20-private-hands-in-base-game` | human_decision | `WIZ-G-PRIVACY` | PASS | PASS |
| `WIZ-R21-round-reset-deal-and-dealer-rotation` | human_decision | `WIZ-G-FIRST-DEALER-RESET` | PASS | PASS |
| `WIZ-R22-player-count-setup-boundaries` | clear | `WIZ-C-PLAYERS-SUPPORTED`, `WIZ-C-PLAYERS-REJECT`, `WIZ-C-DEAL-ROUND`, `WIZ-C-DEAL-REMAINDER`, `WIZ-C-END-3P`, `WIZ-C-END-4P`, `WIZ-C-END-5P`, `WIZ-C-END-6P` | PASS | PASS |
| `WIZ-R23-complete-game-final-round-by-count` | clear | `WIZ-C-FINAL-NO-TRUMP`, `WIZ-C-END-3P`, `WIZ-C-END-4P`, `WIZ-C-END-5P`, `WIZ-C-END-6P`, `WIZ-C-END-ALL-DEALT`, `WIZ-C-END-SCORE-FIRST` | PASS | PASS |
| `WIZ-R24-revealed-card-trump-rules` | clear | `WIZ-C-TRUMP-REVEAL`, `WIZ-C-TRUMP-ORDINARY`, `WIZ-C-TRUMP-JESTER`, `WIZ-C-TRUMP-WIZARD-DEALER`, `WIZ-C-TRUMP-AFTER-HAND` | PASS | PASS |
| `WIZ-R25-complete-bid-order-and-first-leader` | clear | `WIZ-C-BID-REQUIRED`, `WIZ-C-BID-SEQUENTIAL`, `WIZ-C-BID-FIRST`, `WIZ-C-BID-RECORDED`, `WIZ-C-FIRST-LEADER` | PASS | PASS |
| `WIZ-R26-clockwise-play-and-next-leader` | clear | `WIZ-C-TURN-CLOCKWISE`, `WIZ-C-TRICK-CREDIT`, `WIZ-C-NEXT-LEADER` | PASS | PASS |
| `WIZ-R27-rank-endpoints-and-jester-no-priority` | clear | `WIZ-C-RANK-HIGH`, `WIZ-C-RANK-LOW`, `WIZ-C-JESTER-NOT-TRUMP`, `WIZ-C-WIN-HIGHEST-LED` | PASS | PASS |
| `WIZ-R28-wizard-lead-keeps-all-cards-legal` | clear | `WIZ-C-WIZARD-LEAD-FREE` | **FAIL** | PASS |
| `WIZ-R29-jester-second-card-free-then-follow-suit` | clear | `WIZ-C-JESTER-SECOND-FREE`, `WIZ-C-JESTER-ORDINARY-LEADS`, `WIZ-C-FOLLOW-SUIT` | PASS | PASS |
| `WIZ-R30-jester-does-not-remove-existing-suit` | clear | `WIZ-C-FOLLOW-SUIT`, `WIZ-C-JESTER-ALWAYS-LEGAL` | PASS | PASS |
| `WIZ-R31-midtrick-wizard-wins-without-erasing-suit` | clear | `WIZ-C-FOLLOW-SUIT`, `WIZ-C-WIN-FIRST-WIZARD` | PASS | PASS |
| `WIZ-R32-cumulative-scoring-boundaries` | clear | `WIZ-C-SCORE-EXACT-BONUS`, `WIZ-C-SCORE-EXACT-TRICKS`, `WIZ-C-SCORE-OVER`, `WIZ-C-SCORE-UNDER` | PASS | PASS |
| `WIZ-R33-expanded-private-observations` | human_decision | `WIZ-G-PRIVACY` | PASS | PASS |
| `WIZ-R34-clear-dealer-rotation-and-next-deal` | clear | `WIZ-C-DEALER-ROTATES`, `WIZ-C-DEAL-ROUND` | PASS | PASS |

### Bestätigte Original-Fehler

- **`WIZ-R04` / `WIZ-G-FIRST-DEALER-RESET`:** erwartet Geber 0, tatsächlich seedabhängig zufälliger Geber.
- **`WIZ-R14` / `WIZ-G-JESTER-WIZARD`:** nach Narr → Zauberer setzt eine spätere Farbkarte fälschlich `led_suit`.
- **`WIZ-R28` / `WIZ-C-WIZARD-LEAD-FREE`:** derselbe Zustandsfehler verletzt zusätzlich die klare Regel, dass nach eröffnendem Zauberer alle Karten frei bleiben.

### Verbleibender Clarified-Fehler

- **`WIZ-R14`:** Die Klarstellung korrigiert die direkte Zauberer-Eröffnung, aber nicht die Kombination Narr → Zauberer → Farbkarte vollständig.

## Unabhängige Judge-Evidenz

### Original: Mittelwert 0,740, Stichproben-SD 0,035, n=3

Alle drei Judges bestätigen den Zauberer-/`led_suit`-Defekt und die abweichende erste Geberwahl. Zwei Reviews behandeln außerdem nicht dauerhaft beobachtbare Karten abgeschlossener Stiche als materielles Informationsproblem.

### Clarified: Mittelwert 0,897, Stichproben-SD 0,015, n=3

Alle drei Judges bestätigen den verbleibenden Narr→Zauberer-Defekt. Ein Review wiederholt den Befund zur Sichtbarkeit abgeschlossener Stiche. Dieser Punkt bleibt mangels eingefrorener deterministischer Assertion ein Regressionkandidat und wird nicht nachträglich gescort.

## Deklarierte materielle Annahmen

### Original (3)

- **A-01 — missing:** The initial dealer is selected by the seeded chance source. (`Die Vorbereitung`)
- **A-02 — missing:** Clockwise order advances through increasing player IDs modulo the player count. (`Das Verteilen der Karten / Die Vorhersage / Der Kampf um den Stich`)
- **A-03 — ambiguous:** After one or more leading Fools, the first ordinary suit card establishes the suit to follow; a Wizard establishes no suit. (`Spezielle Rechte der Zauberer und Narren`)

### Clarified (2)

- **A-01 — missing:** Player 0 is the initial dealer (Vertrauter), and dealer duty then passes clockwise after each round. (`Die Vorbereitung / Das Verteilen der Karten`)
- **A-02 — missing:** Before terminal state returns are zero for every player; at terminal state each player's return is their final experience-point score. (`Die Vergabe der Erfahrungspunkte / Das Ende`)

Die Anzahl deklarierter Annahmen ist kein Korrektheitsscore.

## Ressourcen

| Messwert | Original | Clarified |
|---|---:|---:|
| Modellaufrufe | 4 | 4 |
| Provider-Zeit | 892,778 s | 904,204 s |
| Input-Tokens | 1.174.314 | 1.326.930 |
| Cached Input-Tokens | 968.192 | 1.132.800 |
| Output-Tokens | 26.421 | 29.168 |
| Reasoning-Tokens | 10.215 | 13.446 |
| API-Äquivalent | 2,31 USD | 2,41 USD |
| Codezeilen | 331 | 477 |

## Provenienz

- Regelwerk SHA-256: `167254a64b0866266746833c0b98836db51c08171b5b96e25f7461d5bf3dee79`
- Szenario-Suite SHA-256: `9b3963cf9e220f707ed43fdda2719950794639be4c3c0f177eb8beaff79f01c5`
- Adapter SHA-256: `8fea7418ea86340b5d5bbec7baeb8a8f7e34fa688e615b655f9e8ab0fe52473a`
- V4-Runner SHA-256: `002f9c000cba5993633c4af2fab10ced464603b0f16c6d16a251ae76f67f2aac`
- Original-Code SHA-256: `5d4871a25452f59af2f9fe5e28206cb3ca156e2ab61dbe922a676dd74edc9063`
- Clarified-Code SHA-256: `57307b1c8e4805e8f316b62b63dcb480eadb7cc196e7e047df43183101adf9f6`

## Artefakte

- Kurzvergleich: [`v2/COMPARISON.md`](v2/COMPARISON.md)
- Originalprofil: [`v2/original_result.json`](v2/original_result.json)
- Clarified-Profil: [`v2/clarified_result.json`](v2/clarified_result.json)
- Befunde: [`v2/original_findings.md`](v2/original_findings.md) · [`v2/clarified_findings.md`](v2/clarified_findings.md)
- Erfolgreiche Rohartefakte: `v2/raw/study_artifacts.tar.gz`
- Ungescorete Vor-Evaluationsversuche: `v2/raw/failed_attempts.tar.gz`
- Ausführbare Definitionen und Zitate: `../../../checks/scenarios/wizard_v2.json` und `../../../inputs/games/wizard/claims_v2.json`

Ältere Wizard-Präsentationen wurden durch diese V2-Ansicht ersetzt und bleiben über Git nachvollziehbar.
