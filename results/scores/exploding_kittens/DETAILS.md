# Exploding Kittens: detaillierte Auswertung

[← Kurzüberblick](README.md)

**Modellsetup für beide Bedingungen:** Implementierung mit `gpt-5.6-sol`, Thinking `low`; drei neutrale Judges und drei Personas mit `gpt-5.6-sol`, Thinking `medium`. Alle aktuellen Vergleichsläufe wurden direkt über die native Codex-CLI ausgeführt.

## Auswertungsfolge

1. Für Original-PDF und präzisierte Fassung wird jeweils eine frische, isolierte Implementierung erzeugt.
2. Checks 01–06 prüfen technische Ausführbarkeit, Robustheit und Interface (`EV1–EV3`).
3. 22 zitierte Szenarien prüfen klare und klarstellungsabhängige Regeln (`EV4–EV6`).
4. Drei neutrale Judges und drei getrennte Personas prüfen die Implementierungen blind (`EV7–EV8`).
5. Materielle Annahmen und Ressourcen bleiben separate Evidenz (`EV9` und Aufwand).

Es gibt keinen vermischten Gesamtscore.

## EV1–EV3: ausführbare Checks 01–06

| Check | Inhalt | Original-PDF | Präzisierte Fassung |
|---|---|---:|---:|
| **01 – Result file (EV1)** | Generierte Python-Datei vorhanden und nicht leer. | PASS 1/1 | PASS 1/1 |
| **02 – Python syntax (EV1)** | Datei lässt sich als Python kompilieren. | PASS 1/1 | PASS 1/1 |
| **03 – Startable game (EV1)** | Modul importierbar; `Game()` und `initial_state()` liefern Objekte. | PASS 1/1 | PASS 1/1 |
| **04 – Required API (EV1)** | Acht Prüfungen: Klassen und Methoden vorhanden, Rendering, legale Aktionen, Action-Name-Roundtrip und numerische Returns. | PASS 8/8 | PASS 8/8 |
| **05 – Random rollouts (EV2)** | 100 reproduzierbare Zufallsspiele ohne Absturz, ungültige Sackgasse oder inkonsistenten Terminalzustand. | PASS 100/100 | PASS 100/100 |
| **06 – Action language (EV3)** | Jede beobachtete legale Aktion hat einen nicht leeren, eindeutigen Namen und besteht `action → name → action`. | PASS 20.204/20.204 | PASS 36.590/36.590 |

Die unterschiedliche Zahl bei Check 06 entsteht durch unterschiedlich viele beobachtete Zustände und Aktionen; beide Bedingungen bestehen alle jeweils ausgeführten Prüfungen.

Rohlogs: [Original](pdf/raw/expl_pdf_current_checks.txt) · [Präzisiert](clarified/raw/expl_clarified_current_checks.txt)

## EV4–EV6: alle 22 Regelszenarien

**Basis `clear` (EV4):** Erwartung mit Seite und direktem Zitat aus der gedruckten Anleitung.

**Basis `human_decision` (EV5):** Erwartung zu einer Lücke oder Mehrdeutigkeit, die menschlich bestätigt und sichtbar getrennt wurde.

**Coverage (EV6):** Ein Szenario zählt nur als abgedeckt, wenn es tatsächlich erreicht und ausgewertet wurde.

| ID | Basis | Geprüftes Verhalten | Original | Präzisiert |
|---|---|---|---:|---:|
| R01 | clear | Zwei-Spieler-Startzustand und acht Handkarten. | PASS | PASS |
| R02 | clear | Ein normaler Zug kann durch Ziehen beendet werden. | PASS | PASS |
| R03 | clear | Angriff gibt dem nächsten Spieler zwei Züge. | PASS | PASS |
| R04 | clear | Zwei Hops!-Karten verbrauchen zwei geschuldete Züge. | PASS | PASS |
| R05 | clear | Blick in die Zukunft beendet den aktuellen Zug nicht. | PASS | PASS |
| R06 | clear | Mischen beendet den aktuellen Zug nicht. | PASS | PASS |
| R07 | clear | Favor wird aufgelöst und der Zug läuft weiter. | PASS | PASS |
| R08 | clear | Der letzte verbleibende Spieler gewinnt. | PASS | PASS |
| R09 | human_decision | Gegenangriff ersetzt die Zugschuld durch genau zwei. | PASS | PASS |
| R10 | human_decision | Eine vorhandene Entschärfung muss benutzt werden. | PASS | PASS |
| R11 | human_decision | Entschärfung beendet nur einen von mehreren geschuldeten Zügen. | **FAIL** | PASS |
| R12 | clear | Fünf verschiedene Karten dürfen eine gerade abgelegte Komponente zurückholen. | **FAIL** | PASS |
| R13 | human_decision | Ein aus dem Ablagestapel geholtes Kitten explodiert nicht sofort. | PASS | PASS |
| R14 | human_decision | Favor darf keinen Spieler ohne Handkarten als Ziel wählen. | PASS | PASS |
| R15 | human_decision | Pärchen darf keinen Spieler ohne Handkarten als Ziel wählen. | PASS | PASS |
| R16 | human_decision | Drilling darf ein gehaltenes Exploding Kitten anfragen. | **FAIL** | PASS |
| R17 | clear | Katzenkarten können als Pärchen ausgespielt werden. | PASS | PASS |
| R18 | clear | Gültiger Aufbau enthält ein Kitten pro künftiger Eliminierung. | PASS | PASS |
| R19 | clear | Entschärfung setzt das Kitten ein, ohne andere Karten umzuordnen. | PASS | PASS |
| R20 | human_decision | Mischen macht eine frühere Vorschau ungültig. | PASS | PASS |
| R21 | human_decision | Ziel der Fünf-Karten-Rückholung wird vor NÖ! angekündigt. | PASS | PASS |
| R22 | human_decision | Wiederhergestellte Aktion gegen leeres Ziel endet ohne Transfer. | **FAIL** | PASS |

Gesamt: Original `18 PASS / 4 FAIL`, präzisiert `22 PASS / 0 FAIL`; Coverage jeweils `22/22`.

### Erklärung der vier Original-Fehler

- **R11:** Nach der Entschärfung wechselte die Implementierung zum nächsten Spieler, obwohl noch ein Angriffszug geschuldet war.
- **R12:** Bei anfangs leerem Ablagestapel wurde keine Fünf-Karten-Aktion angeboten; die gerade abgelegten Komponenten waren nicht als Rückholziel verfügbar.
- **R16:** Die möglichen Drilling-Anfragen wurden aus der privaten Zielhand abgeleitet. Dadurch fehlte die korrekte, vor der Reaktion angekündigte Kitten-Anfrage.
- **R22:** Nach NÖ!/DOCH! wurde die wiederhergestellte Aktion nicht als transferloses Ergebnis abgeschlossen, wenn das Ziel inzwischen keine Karte mehr hatte.

Ausführbare Definitionen und Zitate: `../../../checks/scenarios/expl.json`

Rohresultate: [Original](pdf/raw/expl_pdf_current_scenarios.json) · [Präzisiert](clarified/raw/expl_clarified_current_scenarios.json)

## EV7: drei neutrale Judges

Jeder Judge erhält die Regelquelle, bestätigte Regelfakten und genau eine Implementierung. Tests, andere Reviews und die Vergleichsimplementierung bleiben verborgen. Der Judge prüft Setup, Zugfolge, Aktionen, Zustandsübergänge, Zufall, private Information, Eliminierung und Spielende. Kritische oder große Befunde benötigen Zitat, Seite, Fact-ID, Codeort sowie Soll-/Ist-Verhalten.

| Review | Original-PDF | Präzisierte Fassung |
|---|---:|---:|
| Judge 1 | 0,42 | 0,98 |
| Judge 2 | 0,50 | 0,99 |
| Judge 3 | 0,48 | 0,89 |
| **Mittelwert** | **0,467** | **0,953** |
| **Sample SD** | **0,042** | **0,055** |

- Originalreviews: [1](pdf/raw/expl_pdf_current_judge_1.md) · [2](pdf/raw/expl_pdf_current_judge_2.md) · [3](pdf/raw/expl_pdf_current_judge_3.md)
- Präzisierte Reviews: [1](clarified/raw/expl_clarified_current_judge_1.md) · [2](clarified/raw/expl_clarified_current_judge_2.md) · [3](clarified/raw/expl_clarified_current_judge_3.md)

## EV8: drei getrennte Personas

Personas ergänzen EV7 um spezialisierte Fragestellungen. Sie werden weder miteinander noch mit dem neutralen Judge-Mittelwert verrechnet.

| Persona | Auftrag | Original-PDF | Präzisierte Fassung |
|---|---|---|---|
| **Regeltreue** | Konkrete Widersprüche zwischen Quelle und Code mit Zitat, Fact-ID, Codeort und Soll-/Ist-Verhalten finden. | Markiert u. a. Eliminierungsablage, Angriff/Entschärfung, Kombinationen, Drilling-Privatsphäre, Reaktionszeitpunkt und leeres Ziel. | Keine belegten kritischen oder großen Widersprüche; offene Frage zur Dauer angezeigten Vorschauwissens. |
| **Ambiguität / Spezifikation** | Fehlende oder mehrdeutige Regeln, plausible Auslegungen, Implementierungsentscheidung und passende Klarstellung benennen. | Zeigt mehrere Quelllücken; viele sind durch bestätigte Entscheidungen aufgelöst, werden von der Implementierung aber teilweise anders umgesetzt. | Drei ungelöste Fragen: einzelne Katzenkarte, Drilling gegen leere Hand, Dauer unveränderten Vorschauwissens. |
| **Ausführbare Systeme** | Phasenübergänge, Reaktionen, Mehrfachzüge, explizite Parameter, Hidden Information, Eliminierung sowie leere/kurze Ressourcen prüfen. | Markiert kritische Grenzen bei Angriff/Entschärfung, Drilling und wiederhergestellten Transfers sowie weitere Kombinations- und Vorschauprobleme. | Keine belegten kritischen oder großen Defekte; verbleibende Fragen zur Beobachtungsschnittstelle und historischem Wissen. |

- Original: [Regeltreue](pdf/raw/expl_pdf_current_persona_rule_fidelity.md) · [Ambiguität](pdf/raw/expl_pdf_current_persona_ambiguity.md) · [Systeme](pdf/raw/expl_pdf_current_persona_executable_systems.md)
- Präzisiert: [Regeltreue](clarified/raw/expl_clarified_current_persona_rule_fidelity.md) · [Ambiguität](clarified/raw/expl_clarified_current_persona_ambiguity.md) · [Systeme](clarified/raw/expl_clarified_current_persona_executable_systems.md)

## EV9: materielle Annahmen

- **Original-PDF: 3** — NÖ!-Reaktionszyklus, Angriff/Hops!-Zugschuld und fehlende Katzenkartentitel.
- **Präzisierte Fassung: 2** — drei fehlende Katzenkartentitel und Lebensdauer der gespeicherten Vorschau.

Vollständige strukturierte Einträge: [Original](pdf/raw/expl_pdf_current_assumptions.json) · [Präzisiert](clarified/raw/expl_clarified_current_assumptions.json)

## Offene Punkte

Nach der Präzisierung bleiben drei Quellfragen sichtbar:

1. Darf eine Katzenkarte einzeln und ohne Effekt gespielt werden?
2. Darf ein Drilling einen Spieler ohne Handkarten als Ziel wählen?
3. Wie lange soll unverändertes Vorschauwissen digital sichtbar bleiben?

Zusätzlich gilt: Mit einem Implementierungslauf pro Bedingung (`n=1`) lässt sich noch keine Laufvarianz schätzen.

## Aufwand

| Ressource | Original-PDF | Präzisierte Fassung |
|---|---:|---:|
| Implementierungsmodell | `gpt-5.6-sol` (`low`) | `gpt-5.6-sol` (`low`) |
| Reviewmodell für EV7/EV8 | `gpt-5.6-sol` (`medium`) | `gpt-5.6-sol` (`medium`) |
| LLM-Aufrufe inklusive EV7/EV8 | 7 | 7 |
| Provider-Zeit | 1.598,681 s | 1.605,015 s |
| Input-Tokens (davon gecacht) | 1.035.093 (802.304) | 1.523.405 (1.251.584) |
| Output-Tokens | 48.345 | 44.734 |
| Reasoning-Tokens | 26.367 | 25.972 |
| Python-Codezeilen | 187 | 320 |
| API-äquivalente Kostenschätzung | 3,02 USD | 3,33 USD |

Die Kostenschätzung nutzt die am 15.07.2026 dokumentierten öffentlichen `gpt-5.6-sol`-Preise aus `../../../generation/model_prices.json`; sie ist nicht die tatsächliche Codex-OAuth-Abrechnung.

## Original- und Rohpfade

- Original-PDF: `../../../inputs/games/expl/game_rules.pdf`
- Präzisierte Quelle: `../../../inputs/games/expl/variants/expl_clarified.txt`
- Bestätigte Regelfakten: `../../../inputs/games/expl/rulefacts.md`
- Szenarien: `../../../checks/scenarios/expl.json`
- Originalprofil: `pdf/result.md`
- Präzisiertes Profil: `clarified/result.md`
- Original-Rohdaten: `pdf/raw/`
- Präzisierte Rohdaten: `clarified/raw/`
- Vergleichsabbildung: `../../plots/exploding_kittens/pdf_vs_clarified/evidence_profile.png`
