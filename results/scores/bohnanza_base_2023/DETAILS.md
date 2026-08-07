# Bohnanza Base Game 2023 V2: detaillierte Auswertung

[← Kurzüberblick](README.md)

## Gemeinsame Basis

- Publisherquelle: vollständiges deutsches PDF Version 5.4 / 2023, SHA-256 `e59f7a7d77ed2f052cdf46403b797a1d418996664dc1e3ae9baf7e498b727655`.
- 92 atomare Claims: 82 clear, 7 missing, 2 ambiguous, 1 untestable.
- 81 erforderliche Clear Claims: 80 szenariogemappt plus eine explizite `jederzeit`-Coverage-Ausnahme.
- 42 eingefrorene Szenariogruppen: 38 clear, 4 human decision.
- Implementierung: `gpt-5.6-sol`, Thinking `low`; offizielle Judges: `gpt-5.6-sol`, Thinking `medium`.
- Evidenzgruppen werden nicht zu einem Correctness-Gesamtscore kombiniert.

## Interventionsfolge

1. **Original:** nur Publisher-PDF.
2. **Clear-rule emphasis 1:** vier bereits klare Originaldefektgruppen.
3. **Clear-rule emphasis 2:** exakte Wiederholung von Emphasis 1.
4. **Structured clarification 1:** vier freigegebene digitale Entscheidungen plus ausgewogene Ganzspiel-Checkliste.
5. **Structured clarification 2:** vorab registrierte exakte frische Wiederholung von Structured 1.

Structured 1 ist gegenüber den Emphasis-Läufen ein angepasster Nachfolger. Structured 2 repliziert diesen Nachfolger mit byte-identischem initialem Modellpaket. Alle Vorgänger bleiben erhalten; es gibt keine Best-of-Auswahl.

## Evidenzgruppen

| Evidenz | Original | Emphasis 1 | Emphasis 2 | Structured 1 | Structured 2 |
|---|---:|---:|---:|---:|---:|
| Generationscalls / Repairs | 1/0 | 1/0 | 1/0 | 1/0 | 2/1 |
| Technischer Gate | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 |
| Random Rollouts | 100/100 | 100/100 | 100/100 | 100/100 | 100/100 |
| Action-Language | 800.371/800.371 | 1.523.314/1.523.314 | 976.727/976.727 | 847.456/847.456 | 1.395.514/1.395.514 |
| Spielerzahlen | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| Szenarien PASS/FAIL/CRASH | 37/5/0 | 33/9/0 | 32/10/0 | 36/6/0 | 38/3/1 |
| Clear-basis | 33/38 | 30/38 | 30/38 | 33/38 | **35/38** |
| Human-decision-basis | 4/4 | 3/4 | 2/4 | 3/4 | 3/4 |
| Ausgewertete Abdeckung | 42/42 | 42/42 | 42/42 | 42/42 | 42/42 |
| Neutral Judges | 0,68/0,70/0,55 | nicht ausgeführt | 0,38/0,45/0,44 | 0,74/0,68/0,72 | 0,47/0,55/0,55 |
| Judge-Mittel (SD) | 0,643 (0,081) | – | 0,423 (0,038) | 0,713 (0,031) | 0,523 (0,046) |

## Ergebnisse nach Bedingung

### Original

Fünf Clear-Fehler: ungleiche Mehrkarten-Trades (`R16`, `R17`), Garden- und Soy-Bohnometer (`R30`, `R33`) sowie Phase-two-Ende bei dritter Leerung (`R40`). Alle vier Human Decisions bestehen.

### Clear-rule emphasis 1 und 2

Beide schmalen Interventionen erreichen 30/38 Clear, verlieren aber unterschiedliche nicht betonte Mechaniken. Emphasis 2 wiederholt den niedrigen Wert, weshalb Emphasis 1 kein isolierter Ausreißer ist. Das bleibt bei `n=2` deskriptiv.

### Structured clarification 1

33/38 Clear und 3/4 Human Decision. Fehler: optionales zweites Pflanzen (`R10`), ungleiche Mehrkarten-Trades (`R16`, `R17`) sowie frei gewählte staged/revealed Pflanzreihenfolge (`R22`–`R24`, einschließlich `R23`). Judge-Mittel 0,713.

### Structured clarification 2

35/38 Clear und 3/4 Human Decision. Mehrkarten-Trades und freie Kartenreihenfolge bestehen nun. Gescorte Defekte:

- `R04` (Clear, CRASH): exponentielle Materialisierung aller Angebots- und Anfrage-Teilmengen macht bounded play unpraktikabel;
- `R10` (Clear): Ablehnen der optionalen zweiten Handkarte bleibt in `plant_second`;
- `R14` (Clear): der Vier-Phasen-Ablauf bleibt in `plant_received`;
- `R23` (Human Decision): die freigegebene Phase-3-Reihenfolge erreicht ebenfalls nicht `draw`.

Alle drei offiziellen Judges bewerten die exponentielle Aktionsenumeration als kritisch. Wiederholt genannt werden außerdem zu späte Leerungs-/Recyclinggrenzen, private gegnerische Handidentitäten in Trade-Aktionen und fehlende einseitige Geschenke eines nicht aktiven Spielers an den aktiven Spieler.

## Evaluatorhistorie und Host-Schutz

- Zwei Original-Replays und das erste Emphasis-2-Replay bleiben als frühere ungültige Evaluatorversuche archiviert.
- Structured 2 hatte einen Auth-Preflight ohne Modellaufruf; er ist kein zusätzlicher Generationslauf.
- Eine technische Invocation nutzte versehentlich den Legacy- statt V2-Contract-Check; sie bleibt ungescort.
- Der unveränderte Full-Suite-Runner überschritt bei `R04` 1.800 Sekunden und fror den Host ein. Die Implementierung wurde nicht verändert. Eine dokumentierte Kompatibilitätsausführung rief dieselbe `run_scenario_v4`-Logik szenarioweise mit niedriger Priorität, einem CPU-Kern und 15-Sekunden-Prozessgrenze auf. Original und Structured 1 bestehen `R04` in 0,17/0,30 Sekunden; Structured 2 überschreitet die Grenze und wird als CRASH gewertet.
- Die erste Judge-Invocation nutzte versehentlich `low`; alle drei Reviews bleiben ungescort archiviert. Offiziell wurde das eingefrorene `medium`-Setting erneut ausgeführt.

## Interpretation

Structured 2 ist weder durchgehend schlechter noch durchgehend besser. Gegenüber Structured 1 steigt die Clear-Passrate von 33/38 auf 35/38, während Laufzeitverhalten und Judge-Signal deutlich schlechter werden. Gegenüber Original verbessert sich die Clear-Passrate ebenfalls, aber Human Decision fällt von 4/4 auf 3/4 und ein schwerer Performance-Crash kommt hinzu.

Damit zeigt die exakte Wiederholung vor allem Modellvarianz und die Notwendigkeit getrennter Evidenzgruppen. Zwei Wiederholungen erlauben keine kausale Aussage über die strukturierte Klarstellung.

## Artefakte

- Supplement: `inputs/games/bohnanza_base_2023/structured_clarification_v3.md`
- Replikations-Präregistrierung: `inputs/games/bohnanza_base_2023/structured_clarification_replication_v2.json`
- Original: `v2/original_result.json`, `v2/original_findings.md`
- Structured 1: `v2/structured_clarification_1_result.json`, `v2/structured_clarification_1_findings.md`
- Structured 2: `v2/structured_clarification_2_result.json`, `v2/structured_clarification_2_findings.md`
- Structured-2-Rohdaten: `v2/raw/structured_clarification_2/`
- Vergleich: `v2/COMPARISON.md`
