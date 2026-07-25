# Bohnanza Base 2023: detaillierte Auswertung

[← Kurzüberblick](README.md)

**Modellsetup für beide Bedingungen:** Implementierung mit `gpt-5.6-sol`, Thinking `low`; drei neutrale Judges mit `gpt-5.6-sol`, Thinking `medium`. Keine Personas in diesem Pilotlauf. Frische isolierte Generationen (Replacement-Vergleich v4); gleiche Rubrik, gleiche Checks, kein Post-Eval-Repair.

## Auswertungsfolge

1. Für Original-PDF und präzisierte Fassung wird jeweils eine frische, isolierte Implementierung erzeugt.
2. Checks 01–06 prüfen technische Ausführbarkeit, Robustheit und Interface (`EV1–EV3`).
3. 41 zitierte Szenarien prüfen klare und klarstellungsabhängige Regeln (`EV4–EV6`).
4. Drei neutrale Judges prüfen die Implementierungen blind (`EV7`).
5. Materielle Annahmen und Ressourcen bleiben separate Evidenz (`EV9` und Aufwand).

Es gibt keinen vermischten Gesamtscore. Personas (**EV8**) wurden hier nicht ausgeführt.

## EV1–EV3: ausführbare Checks 01–06

| Check | Inhalt | Original-PDF | Präzisierte Fassung |
|---|---|---:|---:|
| **01 – Result file (EV1)** | Generierte Python-Datei vorhanden und nicht leer. | PASS 1/1 | PASS 1/1 |
| **02 – Python syntax (EV1)** | Datei lässt sich als Python kompilieren. | PASS 1/1 | PASS 1/1 |
| **03 – Startable game (EV1)** | Modul importierbar; `Game()` und `initial_state()` liefern Objekte. | PASS 1/1 | PASS 1/1 |
| **04 – Required API (EV1)** | Pflicht-API: Klassen/Methoden, Rendering, legale Aktionen, Action-Name-Roundtrip, numerische Returns. | PASS 9/9 | PASS 9/9 |
| **05 – Random rollouts (EV2)** | 100 reproduzierbare Zufallsspiele ohne Absturz oder inkonsistenten Terminalzustand. | PASS 100/100 | PASS 100/100 |
| **06 – Action language (EV3)** | Jede beobachtete legale Aktion hat einen nicht leeren, eindeutigen Namen und besteht `action → name → action`. | PASS 1.473.350/1.473.350 | PASS 1.373.753/1.373.753 |

Die unterschiedliche Zahl bei Check 06 entsteht durch unterschiedlich viele beobachtete Zustände und Aktionen; beide Bedingungen bestehen alle jeweils ausgeführten Prüfungen. EV2 und EV3 sind Stichproben mit festem Seed und keine Vollständigkeitsbeweise.

Rohlogs: [Original](base_pdf_1/runs/base_pdf/bohnanza_base_2023_codex_ag_checks.txt) · [Präzisiert](clarified_1/runs/clarified/bohnanza_base_2023_clarified_codex_ag_checks.txt)

## EV4–EV6: alle 41 Regelszenarien

**Basis `clear` (EV4):** Erwartung mit Seite und direktem Zitat aus der gedruckten Anleitung.

**Basis `human_decision` (EV5):** Erwartung zu einer Lücke oder Mehrdeutigkeit, die menschlich bestätigt und sichtbar getrennt wurde.

**Coverage (EV6):** Ein Szenario zählt nur als abgedeckt, wenn es tatsächlich erreicht und ausgewertet wurde.

| ID | Basis | Geprüftes Verhalten | Original | Präzisiert |
|---|---|---|---:|---:|
| BASE-R01 | clear | Exakter Grundspiel-Bestand / Setup. | PASS | PASS |
| BASE-R02 | clear | Vorderste Handkarte muss angebaut werden. | PASS | PASS |
| BASE-R03 | clear | Zweite Bohne optional, keine dritte. | PASS | PASS |
| BASE-R04 | clear | Leere Hand überspringt Phase 1. | PASS | PASS |
| BASE-R05 | clear | Nur eine Sorte pro Feld. | PASS | PASS |
| BASE-R06 | clear | Nur aktive Person darf handeln. | PASS | PASS |
| BASE-R07 | clear | Erhaltene Karten gehen nicht auf die Hand. | PASS | PASS |
| BASE-R08 | clear | Abgelehntes Geschenk ohne Transfer. | PASS | PASS |
| BASE-R10 | clear | Einzelkarten-Schutz beim Ernten. | PASS | PASS |
| BASE-R11 | clear | Einzelkarte erlaubt, wenn alle Felder einzeln. | PASS | PASS |
| BASE-R12 | clear | Normale Ernte leert das Feld. | PASS | PASS |
| BASE-R17 | clear | Dritte Leerung beim Aufdecken beendet Phase 2/3 noch. | PASS | PASS |
| BASE-R18 | human_decision | Dritte Leerung in Phase 4 endet sofort. | **FAIL** | PASS |
| BASE-R19 | human_decision | Endwertung ignoriert Handkarten. | PASS | PASS |
| BASE-R20 | clear | Gleichstand: Startperson im Uhrzeigersinn. | PASS | PASS |
| BASE-R21 | human_decision | Nicht-terminale Leerung: nachfüllen und Aufdecken fortsetzen. | PASS | PASS |
| BASE-R22 | human_decision | Ernte zwischen Pflichtpflanzungen. | PASS | PASS |
| BASE-R23 | human_decision | Nicht-aktive Person darf ernten. | PASS | PASS |
| BASE-R25 | clear | Fünf-Spieler-Setup. | PASS | PASS |
| BASE-R26 | clear | Ungleicher Tausch aus beliebigen Handpositionen. | PASS | PASS |
| BASE-R27 | clear | Erzwungene Ernte vor Pflichtpflanzung. | PASS | PASS |
| BASE-R28 | clear | Blaue-Bohnen-Kurve. | PASS | PASS |
| BASE-R29 | clear | Feuerbohnen-Kurve. | PASS | PASS |
| BASE-R30 | clear | Saubohnen-Kurve. | PASS | PASS |
| BASE-R31 | clear | Brechbohnen-Kurve. | PASS | PASS |
| BASE-R32 | clear | Sojabohnen-Kurve. | PASS | PASS |
| BASE-R33 | clear | Augenbohnen-Kurve. | PASS | PASS |
| BASE-R34 | clear | Rote-Bohnen-Kurve. | PASS | PASS |
| BASE-R35 | human_decision | Gartenbohnen-Kurve. | **FAIL** | PASS |
| BASE-R37 | clear | Handsortierung verboten. | PASS | PASS |
| BASE-R38 | clear | Drei-Spieler-Setup. | PASS | PASS |
| CLAR-R39 | human_decision | Dritte Leerung genau auf der dritten Phase-4-Karte. | **FAIL** | PASS |
| CLAR-R40 | human_decision | Dritte Leerung genau auf zweikartigem Aufdecken. | PASS | PASS |
| CLAR-R41 | human_decision | Erste Leerung recycled auf letzter Karte. | PASS | PASS |
| CLAR-R42 | human_decision | Phase 3 an nicht-aktiven Empfänger mit Reihenfolge. | **FAIL** | PASS |
| CLAR-R43 | human_decision | 1-gegen-2-Tausch ist legal. | PASS | PASS |
| CLAR-R44 | human_decision | 3-gegen-1-Tausch ist legal. | PASS | PASS |
| BASE-R45 | human_decision | Pflicht-Endernte nach Phase-4-Leerung. | **FAIL** | **FAIL** |
| BASE-R46 | clear | Pflicht-Endernte nach Phase-2-Fortsetzung. | **FAIL** | **FAIL** |
| CLAR-R47 | human_decision | Zweite Leerung in Phase 4 beendet den Zug. | PASS | PASS |
| CLAR-R48 | human_decision | Dritte Leerung genau auf der zweiten Phase-4-Karte. | **FAIL** | PASS |

Gesamt: Original `34 PASS / 7 FAIL`, präzisiert `39 PASS / 2 FAIL`; Coverage jeweils `41/41`.  
EV4 klar: `25/26` → `25/26`. EV5 human_decision: `9/15` → `14/15`.

### Erklärung der Original-Fehler, die Klarstellung behebt

- **BASE-R18 / CLAR-R39 / CLAR-R48:** dritte Leerung in Phase 4 wurde nicht positionsgenau als sofortiges Ende behandelt.
- **BASE-R35:** Gartenbohne zahlte bei zwei Karten 1 statt 2 Taler.
- **CLAR-R42:** Phase 3 blieb beim aktiven Spieler statt zum nicht-aktiven Empfänger mit eigener Pflanzwahl zu wechseln.

### Gemeinsame Endernte-Fails (unterschiedliche Defekte)

- **BASE-R45 / BASE-R46 Original:** Felder werden geerntet, aber verbleibende Handkarten fälschlich in Taler umgewandelt und entfernt („Die Karten auf der Hand zählen nicht mehr“).
- **BASE-R45 / BASE-R46 Präzisiert:** Zustand wird terminal markiert, ohne Felder beobachtbar zu ernten; `returns()` kann hypothetisch korrekt wirken, obwohl die Pflicht-Endernte fehlt.

Deshalb muss Endernte als Zustandsübergang getestet werden, nicht nur über Terminal-Returns.

Ausführbare Definitionen und Zitate: `../../../checks/scenarios/bohnanza_base_2023_comparison_v4.json`

Rohresultate: [Original](clarified_1/comparison/original_scenarios.json) · [Präzisiert](clarified_1/comparison/clarified_scenarios.json)

## EV7: drei neutrale Judges

Für beide Bedingungen erhalten die Judges die Evaluationsreferenz (Publisher-PDF / bestätigte Fakten) und genau eine Implementierung. Tests, andere Reviews und die Vergleichsimplementierung bleiben verborgen. Kritische oder große Befunde benötigen Zitat, Seite, Fact-ID, Codeort sowie Soll-/Ist-Verhalten.

| Review | Original-PDF | Präzisierte Fassung |
|---|---:|---:|
| Judge 1 | 0,28 | 0,56 |
| Judge 2 | 0,28 | 0,62 |
| Judge 3 | 0,40 | 0,62 |
| **Mittelwert** | **0,320** | **0,600** |
| **Sample SD** | **0,069** | **0,035** |

Die Sample SD beschreibt nur die Streuung zwischen den drei Judges derselben Implementierung, nicht zwischen Implementierungsläufen.

Wiederholte Befunde:

- **Original:** illegale Endwertung von Handkarten, exponentielle Trade-Enumeration, unvollständige nicht-aktive Phase-3-Pflanzung, ungeprüfte Direktaktionen, fehlende Erntegelegenheiten.
- **Präzisiert:** weiterhin kritische Trade-Enumeration und fehlende Partner-zu-Aktiv-Geschenke; alle drei Judges bewerten die Endwertung als korrekt und **verpassen** den beobachtbaren Endernte-Defekt (siehe deterministische Szenarien).

- Originalreviews: [1](base_pdf_1/runs/base_pdf/bohnanza_base_2023_codex_ag_judge_1.md) · [2](base_pdf_1/runs/base_pdf/bohnanza_base_2023_codex_ag_judge_2.md) · [3](base_pdf_1/runs/base_pdf/bohnanza_base_2023_codex_ag_judge_3.md)
- Präzisierte Reviews: [1](clarified_1/runs/clarified/bohnanza_base_2023_clarified_codex_ag_judge_1.md) · [2](clarified_1/runs/clarified/bohnanza_base_2023_clarified_codex_ag_judge_2.md) · [3](clarified_1/runs/clarified/bohnanza_base_2023_clarified_codex_ag_judge_3.md)

## EV8: Personas

Nicht ausgeführt in diesem Pilotlauf. Kein Score, keine Verrechnung mit EV7.

## EV9: materielle Annahmen

EV9 ist **kein Test und kein Score**. Es dokumentiert, welche materiellen Quellenentscheidungen der jeweilige Implementierer selbst angegeben hat. Die IDs beginnen in jedem Lauf neu.

| Bedingung | Lauf-ID | Quellenstelle | Deklarierte Entscheidung |
|---|---|---|---|
| Original-PDF | A-01 | Beginn des Spiels | Spieler 0 beginnt. |
| Original-PDF | A-02 | Leerer Nachziehstapel | Leerung zählt beim Ziehen der letzten Karte; vor dritter Leerung sofort nachfüllen. |
| Original-PDF | A-03 | Spielende | Dritte Leerung in Phase 4 endet sofort; in Phase 2 werden Phase 2/3 noch beendet. |
| Präzisierte Fassung | A-01 | Wer beginnt | Spieler 0 erhält die Startkarte und beginnt. |
| Präzisierte Fassung | A-02 | Austeilen | Karten reihum austeilen; erste erhaltene Karte ist die Vorderste. |
| Präzisierte Fassung | A-03 | Handel / Geschenk | Aktive Person schlägt endliches Angebot an einen Partner vor; Partner akzeptiert/lehnt ab. |
| Präzisierte Fassung | A-04 | CLAR-END-01 / Spielende | Aufdecken stoppt sofort nach der Karte der dritten Leerung; Phase 2/3 mit tatsächlich aufgedeckten Karten fortsetzen. |

`3` gegenüber `4` ist kein Verbesserungsscore. Der Quellenvergleich stützt sich primär auf EV4, EV5 und EV7.

Vollständige Einträge: [Original](base_pdf_1/runs/base_pdf/bohnanza_base_2023_codex_ag_assumptions.json) · [Präzisiert](clarified_1/runs/clarified/bohnanza_base_2023_clarified_codex_ag_assumptions.json)

## Offene Punkte

- Verpflichtende Endernte bleibt in beiden Bedingungen ungelöst (unterschiedliche Defekte).
- Judges können Endernte als korrekt bewerten, obwohl der State-Übergang fehlt.
- Trade-Action-Space / Legalität bleibt laut Judges problematisch; die Klarstellung war darauf nicht als Intervention ausgelegt.
- Mit `n=1` pro Bedingung keine Laufvarianz.

## Aufwand

| Ressource | Original-PDF | Präzisierte Fassung |
|---|---:|---:|
| Implementierungsmodell | `gpt-5.6-sol` (`low`) | `gpt-5.6-sol` (`low`) |
| Reviewmodell für EV7 | `gpt-5.6-sol` (`medium`) | `gpt-5.6-sol` (`medium`) |
| LLM-Aufrufe inklusive EV7 | 4 | 4 |
| Provider-Zeit | 753,969 s | 910,303 s |
| Input-Tokens (davon gecacht) | 718.808 (529.152) | 856.596 (687.616) |
| Output-Tokens | 29.020 | 35.967 |
| Reasoning-Tokens | 14.964 | 13.066 |
| Python-Codezeilen | 383 | 551 |
| API-äquivalente Kostenschätzung | 2,08 USD | 2,27 USD |

Die vier LLM-Aufrufe bestehen jeweils aus einer Implementierung und drei neutralen Judges; beide Läufe benötigten keine Reparatur. Die Provider-Zeit ist die Summe der Call-Dauern und wegen paralleler Reviews nicht die verstrichene Gesamtzeit. Die Kostenschätzung nutzt die am 15.07.2026 dokumentierten öffentlichen `gpt-5.6-sol`-Preise aus `../../../generation/model_prices.json`; sie ist nicht die tatsächliche Codex-OAuth-Abrechnung.

## Original- und Rohpfade

- Original-PDF / Fakten: `../../../inputs/games/bohnanza_base_2023/`
- Präzisierte Bedingung: `../../../inputs/games/bohnanza_base_2023_clarified/`
- Szenarien: `../../../checks/scenarios/bohnanza_base_2023_comparison_v4.json`
- Original-Rohdaten: `base_pdf_1/runs/base_pdf/`
- Präzisierte Rohdaten: `clarified_1/runs/clarified/`
- Maschinenvergleich: `clarified_1/COMPARISON.md` · `clarified_1/comparison.json`
- Einzelbericht Original: `base_pdf_1/REPORT.md`
