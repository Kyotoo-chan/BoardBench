# Bohnanza Base Game 2023 V2: detaillierte Auswertung

[← Kurzüberblick](README.md)

## Gemeinsame Basis

- Publisherquelle: vollständiges deutsches PDF Version 5.4 / 2023, SHA-256 `e59f7a7d77ed2f052cdf46403b797a1d418996664dc1e3ae9baf7e498b727655`.
- 92 atomare Claims: 82 clear, 7 missing, 2 ambiguous, 1 untestable.
- 81 erforderliche Clear Claims: 80 szenariogemappt plus eine explizite nicht-exhaustive `jederzeit`-Coverage-Ausnahme.
- 42 eingefrorene Fälle: 38 clear, 4 human decision.
- Implementierung: `gpt-5.6-sol`, Thinking `low`; Judges: `gpt-5.6-sol`, Thinking `medium`.
- Alle Bedingungen nutzen dasselbe PDF, Prompt, Contract, Profil und Modellsetting.

## Interventionsfolge

1. **Original:** nur Publisher-PDF.
2. **Clear-rule emphasis 1:** vier bereits klare Originaldefektgruppen als separates Experimenter-Artefakt.
3. **Clear-rule emphasis 2:** exakte vorab deklarierte Wiederholung von Emphasis 1.
4. **Structured clarification 1:** nachträglich angepasster Nachfolger. Vier freigegebene digitale Entscheidungen plus ausgewogene, quellenabgeleitete Ganzspiel-Checkliste ersetzen die schmale Betonung.

Die strukturierte Bedingung ist wegen der post-evaluation Anpassung kein unabhängiges Replikat. Alle Vorgänger bleiben erhalten; es gibt keine Best-of-Auswahl.

## Evidenzgruppen

| Evidenz | Original | Emphasis 1 | Emphasis 2 | Structured |
|---|---:|---:|---:|---:|
| Generationscalls / Repairs | 1 / 0 | 1 / 0 | 1 / 0 | 1 / 0 |
| Technischer Gate | 4/4 | 4/4 | 4/4 | 4/4 |
| Random Rollouts | 100/100 | 100/100 | 100/100 | 100/100 |
| Action-Language | 800.371/800.371 | 1.523.314/1.523.314 | 976.727/976.727 | 847.456/847.456 |
| Spielerzahlen | 5/5 | 5/5 | 5/5 | 5/5 |
| Szenarien | 37 PASS / 5 FAIL | 33 / 9 | 32 / 10 | 36 / 6 |
| Clear-basis | 33/38 | 30/38 | 30/38 | 33/38 |
| Human-decision-basis | 4/4 | 3/4 | 2/4 | 3/4 |
| Ausgewertete Abdeckung | 42/42 | 42/42 | 42/42 | 42/42 |
| Neutral Judges | 0,68 / 0,70 / 0,55 | nicht ausgeführt | 0,38 / 0,45 / 0,44 | 0,74 / 0,68 / 0,72 |
| Judge-Mittel (SD) | 0,643 (0,081) | – | 0,423 (0,038) | 0,713 (0,031) |

## Original

Fünf Clear-Fehler: ungleiche Mehrkarten-Trades (`R16`, `R17`), Garden- und Soy-Bohnometer (`R30`, `R33`) sowie Phase-two-Ende bei dritter Leerung (`R40`). Alle vier Human Decisions bestehen. Judges ergänzen verzögertes Recycling und private Handidentitäten in Trade-Aktionen.

## Narrow emphasis 1

Die Zielmechaniken werden grundsätzlich verbessert. Neue Fehler entstehen bei optionalem zweitem Pflanzen (`R10`), separatem Zwangsernten (`R12`), Pflanzreihenfolge (`R22`–`R24`) und Red-Bohnometer (`R31`, mit Folgen für `R40`–`R42`). Dieser gültige Lauf bleibt auf Nutzerentscheidung unjudged.

## Narrow emphasis 2

Die exakte Wiederholung erreicht erneut 30/38 Clear. Fehlergruppen: Drei-Spieler-Setup (`R01`), Pflanzreihenfolge (`R22`–`R24`), Off-turn-Ernten (`R26`, `R27`), Garden-Auszahlung (`R30`) und finale Ernte/Wertung (`R40`–`R42`). Alle Judges bewerten die fehlende finale Ernte als kritisch. Der schlechte erste Lauf war damit kein isolierter Ausreißer.

## Structured clarification 1

Das Supplement enthält keine evaluatorinternen Claims, Szenarien oder Resultate. Es liefert die vier freigegebenen digitalen Entscheidungen und eine ausgewogene Checkliste über alle zentralen Regelgruppen.

Es behebt die Setup-, Bohnometer-, Off-turn-Ernte-, Recycling- und Endspieldefekte der Emphasis-Läufe. Verbleibend:

- `R10`: Ablehnen der optionalen zweiten Handkarte beendet Phase 1 nicht;
- `R16`, `R17`: ungleiche Mehrkarten-Trades fehlen in `legal_actions`;
- `R22`, `R24`: keine frei gewählte Reihenfolge eigener staged/revealed cards;
- `R23`: dadurch scheitert auch die freigegebene beliebige Phase-three-Spielerreihenfolge.

Alle drei Judges bestätigen als Major: fehlende Mehrkarten-Trades in der Aktionsoberfläche, feste Pflanzreihenfolge und Leck tiefer gegnerischer Handidentitäten durch Trade-Aktionen. Ungültige Handelspartner sind ein wiederholter Minor-Befund.

## Warum die neue Übergabe besser funktioniert

Die frühere Intervention war kein echtes Clarification-Paket: Sie wiederholte nur vier bereits klare Regeln. Das erhöhte lokale Salienz, ließ dem Modell aber keinen Hinweis, die Gesamtmechanik gegen Regressionen auszubalancieren.

Die neue Übergabe entscheidet echte digitale Lücken ausdrücklich und verlangt zusätzlich einen Ganzspiel-Audit. Dadurch steigt die Regelstabilität deutlich und der Judge-Mittelwert von 0,423 auf 0,713. Die weiterhin explizit beschriebenen, aber falsch implementierten Aktionsfälle zeigen zugleich die Grenze: Kontext reduziert Spezifikationsprobleme, ersetzt aber keine zuverlässige Umsetzung komplexer Aktionsräume.

## Evaluatorhistorie

Zwei Original-Replays und das erste Emphasis-2-Replay wurden vor gültigem Reporting wegen dokumentierter Evaluatorfehler verworfen. Sie erhielten keine Result Cards oder Judges. Details: `v2/raw/FAILED_ATTEMPTS.md`.

## Artefakte

- Supplement: `inputs/games/bohnanza_base_2023/structured_clarification_v3.md`
- Original: `v2/original_result.json`, `v2/original_findings.md`
- Emphasis 1: `v2/clear_rule_emphasis_1_findings.md`
- Emphasis 2: `v2/clear_rule_emphasis_2_result.json`, `v2/clear_rule_emphasis_2_findings.md`
- Structured: `v2/structured_clarification_1_result.json`, `v2/structured_clarification_1_findings.md`
- Vergleich: `v2/COMPARISON.md`
- Kompakte erfolgreiche Rohartefakte: `v2/raw/study_artifacts.tar.gz`
- Quellen/Claims/Szenarien: `inputs/games/bohnanza_base_2023/*_v2.*`, `checks/scenarios/bohnanza_base_2023_v2.json`
