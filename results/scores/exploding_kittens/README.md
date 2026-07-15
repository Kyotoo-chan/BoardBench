# Exploding Kittens: Original-PDF vs. präzisierte Fassung

## Kurzfazit

Beide erzeugten Spielumgebungen sind technisch stabil. Die Implementierung aus dem Original-PDF verfehlt jedoch vier getestete Regelinteraktionen. Nach sichtbarer Präzisierung der gefundenen Regelungslücken besteht eine frische Implementierung alle 22 Szenarien; auch der neutrale Judge-Mittelwert steigt von `0,467` auf `0,953`.

## Auswertungsablauf

1. Aus jeder Quellenfassung wird mit denselben Modell- und Protokolleinstellungen eine **neue, isolierte Implementierung** erzeugt.
2. Ausführbare Prüfungen bewerten Technik, Robustheit, Interface und zitierte Regelszenarien (`EV1–EV6`).
3. Drei neutrale Judges und drei spezialisierte Personas prüfen jede Implementierung unabhängig (`EV7–EV8`).
4. Annahmen und Ressourcen werden separat ausgewiesen (`EV9` und Aufwand). Es gibt keinen vermischten Gesamtscore.

## Evidenzschlüssel

| ID | Evaluation | Was genau geprüft wird |
|---|---|---|
| **EV1** | Technical Gate | Ergebnisdatei vorhanden; gültige Python-Syntax; Spiel importierbar und startbar; vereinbarte API mit Rendering, legalen Aktionen, numerischen Returns und Action-Name-Roundtrip. |
| **EV2** | Runtime Robustness | 100 reproduzierbare Zufalls-Rollouts auf Abstürze, ungültige Sackgassen und inkonsistente Terminalzustände. |
| **EV3** | Interface | Alle in 100 Rollouts beobachteten legalen Aktionen müssen nicht leere, eindeutige Namen besitzen und `action → name → action` korrekt zurückführen. |
| **EV4** | Klare Regeln | 12 deterministische Szenarien, deren Erwartung direkt durch Seitenangabe und Zitat aus der gedruckten Anleitung belegt ist. |
| **EV5** | Klarstellungsabhängige Regeln | 10 deterministische Szenarien zu Lücken oder Mehrdeutigkeiten. Die Erwartung ist als menschlich bestätigte Entscheidung markiert und wird nicht als gedruckte Regel ausgegeben. |
| **EV6** | Szenarioabdeckung | Zeigt, wie viele der 22 Szenarien tatsächlich erreicht und ausgewertet wurden. Abdeckung ist getrennt vom Bestehen. |
| **EV7** | Neutrale Judges | Drei gegenseitig blinde Reviews erhalten Quelle, bestätigte Regelfakten und genau eine Implementierung, aber keine Tests oder anderen Reviews. Jeder liefert Score und belegte Befunde; berichtet werden Mittelwert und Sample SD. |
| **EV8** | Persona-Reviews | **Regeltreue** sucht konkrete Widersprüche zwischen Quelle und Code. **Ambiguität/Spezifikation** sucht fehlende oder mehrdeutige Regeln, plausible Auslegungen und nötige Klarstellungen. **Ausführbare Systeme** prüft Randfälle wie Reaktionsphasen, Mehrfachzüge, Hidden Information, Eliminierung und leere Ressourcen. Personas erzeugen qualitative Befunde, keinen gemeinsamen Score, und fließen nicht in EV7 ein. |
| **EV9** | Materielle Annahmen | Vom Implementierer deklarierte Entscheidungen zu fehlenden, mehrdeutigen oder widersprüchlichen Quellenstellen, die Spielzustand, Aktionen, Information oder Ergebnis beeinflussen. |

## Ergebnisse auf einen Blick

| Evidenz | Original-PDF | Präzisierte Fassung |
|---|---:|---:|
| Technical Gate (**EV1**) | 4/4 | 4/4 |
| Runtime Robustness (**EV2**) | 100/100 | 100/100 |
| Interface (**EV3**) | 1,000 | 1,000 |
| Klare Regeln (**EV4**) | 11/12 | 12/12 |
| Klarstellungsabhängige Regeln (**EV5**) | 7/10 | 10/10 |
| Szenarioabdeckung (**EV6**) | 22/22 | 22/22 |
| Neutraler Judge-Mittelwert (**EV7**) | 0,467 (SD 0,042) | 0,953 (SD 0,055) |
| Persona-Reviews (**EV8**) | zusätzliche Regel- und Randfallbefunde | keine belegten kritischen/großen Defekte; 3 offene Fragen |
| Materielle Annahmen (**EV9**) | 3 | 2 |

<img src="../../plots/exploding_kittens/pdf_vs_clarified/evidence_profile.png" alt="Original-PDF im Vergleich zur präzisierten Fassung" width="50%">

*Abbildung 1: Die drei für den Quellenvergleich zentralen Ergebnisgruppen. EV1–EV3 und EV6 dienen hier als erfolgreiche technische Kontrollen.*

## Einordnung der Ergebnisse

### Original-PDF

Die Implementierung besteht EV1–EV3 vollständig, weicht aber in vier Szenarien ab:

- **EV4:** Fünf-Karten-Kombination bei anfangs leerem Ablagestapel.
- **EV5:** verbleibende Angriffszüge nach einer Entschärfung.
- **EV5:** Ankündigung der Drilling-Parameter vor NÖ!/DOCH!-Reaktionen.
- **EV5:** Auflösung einer wiederhergestellten Aktion, nachdem das Ziel seine letzte Karte ausgegeben hat.

EV8 markiert zusätzlich Eliminierungsablage, Kombinationen mit Sonderkarten, verdeckte Drilling-Anfragen und veraltetes Vorschauwissen als prüfenswerte Punkte. Diese Persona-Befunde wurden nicht nachträglich als Szenario-Pass oder -Fail gezählt.

### Präzisierte Fassung

Die frische Implementierung besteht EV1–EV6 vollständig. Die Regeltreue- und Systems-Persona finden keinen belegten kritischen oder großen Defekt. Der starke Anstieg in EV5 und EV7 stützt die Diagnose, dass die Spezifikation der Quelle zu Problemen der ursprünglichen Übersetzung beigetragen hat.

Mit derzeit einem Implementierungslauf pro Quellenbedingung (`n=1`) ist der Vergleich noch kein Varianz- oder alleiniger Kausalitätsnachweis.

## Offene Punkte

Die Ambiguitäts-Persona (EV8) findet auch nach der Präzisierung drei Fragen:

- Darf eine Katzenkarte einzeln und ohne Effekt gespielt werden?
- Darf ein Drilling einen Spieler ohne Handkarten als Ziel wählen?
- Wie lange soll unverändertes Vorschauwissen digital sichtbar bleiben?

Diese offenen Fragen sind selbst ein Ergebnis des Workflows; sie müssen für diesen Vergleich nicht zugunsten einer „perfekten“ Spielumgebung beseitigt werden.

## Aufwand im Vergleich

| Ressource | Original-PDF | Präzisierte Fassung |
|---|---:|---:|
| LLM-Aufrufe inklusive EV7 und EV8 | 7 | 7 |
| Input-Tokens (davon gecacht) | 1.035.093 (802.304) | 1.523.405 (1.251.584) |
| Output-Tokens | 48.345 | 44.734 |
| Provider-Zeit | 1.598,681 s | 1.605,015 s |
| Python-Codezeilen | 187 | 320 |
| API-äquivalente Kostenschätzung | 3,02 USD | 3,33 USD |

Die Kostenschätzung verwendet die am 15.07.2026 dokumentierten öffentlichen `gpt-5.6-sol`-Preise aus `generation/model_prices.json`. Sie ist nicht die tatsächliche Codex-OAuth-Abrechnung.

## Original- und Detailpfade

- Original-PDF: `../../../inputs/games/expl/game_rules.pdf`
- Präzisierte Quelle: `../../../inputs/games/expl/variants/expl_clarified.txt`
- Bestätigte Regelfakten: `../../../inputs/games/expl/rulefacts.md`
- Szenarien: `../../../checks/scenarios/expl.json`
- Originalprofil: `pdf/result.md`
- Präzisiertes Profil: `clarified/result.md`
- Rohdaten: `pdf/raw/` und `clarified/raw/`
- Vergleichsabbildung: `../../plots/exploding_kittens/pdf_vs_clarified/evidence_profile.png`
