# Bohnanza Base Game 2023 V2: detaillierte Auswertung

[← Kurzüberblick](README.md)

## Design

- Quelle: vollständiges deutsches Publisher-PDF Version 5.4 / 2023, SHA-256 `e59f7a7d77ed2f052cdf46403b797a1d418996664dc1e3ae9baf7e498b727655`.
- 92 atomare Claims: 82 clear, 7 missing, 2 ambiguous, 1 untestable.
- 81 erforderliche Clear Claims: 80 szenariogemappt plus eine explizite nicht-exhaustive `jederzeit`-Coverage-Ausnahme.
- 42 eingefrorene Fälle: 38 clear, 4 human decision.
- Implementierung: `gpt-5.6-sol`, Thinking `low`; Judges: `gpt-5.6-sol`, Thinking `medium`.

Das Original erhielt nur das PDF. Das Clear-Rule-Emphasis-Paket wiederholt vier bereits klare Defektgruppen und ist kein Publishertext. Emphasis 2 ist eine vorab deklarierte exakte Wiederholung von Emphasis 1. Beide gültigen Emphasis-Läufe bleiben erhalten; es gibt keine Best-of-Auswahl.

## Evidenzgruppen

| Evidenz | Original | Emphasis 1 | Emphasis 2 |
|---|---:|---:|---:|
| Generationscalls / Repairs | 1 / 0 | 1 / 0 | 1 / 0 |
| Technischer Gate | 4/4 | 4/4 | 4/4 |
| Random Rollouts | 100/100 | 100/100 | 100/100 |
| Action-Language | 800.371/800.371 | 1.523.314/1.523.314 | 976.727/976.727 |
| Spielerzahlen 3–5 / Ablehnung 2,6 | 5/5 | 5/5 | 5/5 |
| Szenarien | 37 PASS / 5 FAIL | 33 PASS / 9 FAIL | 32 PASS / 10 FAIL |
| Clear-basis | 33/38 | 30/38 | 30/38 |
| Human-decision-basis | 4/4 | 3/4 | 2/4 |
| Ausgewertete Abdeckung | 42/42 | 42/42 | 42/42 |
| Neutral Judges | 0,68 / 0,70 / 0,55 | nicht ausgeführt | 0,38 / 0,45 / 0,44 |
| Judge-Mittel (SD) | 0,643 (0,081) | – | 0,423 (0,038) |

## Original: fünf fehlgeschlagene Szenarien

- `R16`, `R17`: ungleiche atomare Mehrkarten-Trades fehlen.
- `R30`: zwei Garden Beans zahlen eins statt zwei.
- `R33`: drei Soy Beans zahlen zwei statt eins.
- `R40`: nach dritter Leerung in Phase 2 wird Phase 4 verlangt.

Alle vier Human Decisions bestehen.

## Emphasis 1: neun fehlgeschlagene Szenarien

Gezielte Verbesserungen: `R16`, `R17`, `R30`, `R33`; auch der Terminalmechanismus von `R40` wird korrigiert. Neue Fehler:

- `R10`: zweite optionale Handkarte beendet Phase 1 nicht;
- `R12`: unpassende Bohne löst implizites Ernten+Pflanzen statt separater Ernte aus;
- `R22`, `R23`, `R24`: keine frei gewählte Reihenfolge neuer Karten;
- `R31`: falsches Red-Bohnometer;
- `R40`, `R41`, `R42`: Folgefehler des Red-Bohnometers in finaler Wertung.

Dieser Lauf wurde auf Nutzerentscheidung nicht gejudged, bleibt aber vollständig als Szenarioevidenz erhalten.

## Emphasis 2: zehn fehlgeschlagene Szenarien

- `R01`: drei Spieler erhalten zwei statt drei Felder;
- `R22`, `R23`, `R24`: Eigentümer dürfen die Reihenfolge neuer Karten nicht wählen;
- `R26`, `R27`: Off-turn-Ernten fehlt an stabilen Entscheidungsgrenzen;
- `R30`: Garden-Auszahlung erneut falsch;
- `R40`, `R41`, `R42`: finale Felder werden nicht korrekt geerntet, daher Münzen und Gewinner falsch.

Die gescorten Mehrkarten-Trades und Soy-Auszahlung bestehen. Der phase-two Terminalübergang erfolgt, aber ohne korrekte finale Ernte.

## Judge-Evidenz

### Original

Alle Judges bestätigen Garden-/Soy-Auszahlungen, Mehrkarten-Trades und Phase-two-Ende. Wiederholte ungescorte Kandidaten: verzögertes Recycling und private Handidentitäten in Trade-Aktionen.

### Emphasis 2

Alle drei Judges melden die ausgelassene finale Ernte als **kritisch**. Wiederholt bestätigt werden falsches Drei-Spieler-Setup, Garden-Auszahlung, begrenzte Trades, Pflanzreihenfolge und Off-turn-Ernten. Zwei beziehungsweise drei Reviews wiederholen Recycling- und Handinformationsprobleme.

Judges sind qualitative Signale und werden nicht mit Szenarien verrechnet.

## Interpretation

Die Intervention erhöht die Salienz der vier Zielgruppen und verbessert davon Teile reproduzierbar. Sie stabilisiert die Gesamtübersetzung jedoch nicht: beide Emphasis-Läufe verlieren jeweils drei zusätzliche Clear-Szenarien gegenüber dem Original und unterscheiden sich stark in ihren Defekten. Das spricht für erhebliche Generationsvarianz und Modell-/Übersetzungsfehler, nicht für die Behauptung, das Publisher-Regelwerk sei allein ursächlich.

## Evaluatorhistorie

Zwei Original-Replays und das erste Emphasis-2-Replay wurden vor gültigem Reporting wegen dokumentierter Evaluatorfehler verworfen. Sie erhielten keine Result Cards oder Judges. Details und Roharchive: `v2/raw/FAILED_ATTEMPTS.md`.

## Artefakte

- Original: `v2/original_result.json`, `v2/original_findings.md`
- Emphasis 1 unjudged: `v2/clear_rule_emphasis_1_findings.md`
- Emphasis 2: `v2/clear_rule_emphasis_2_result.json`, `v2/clear_rule_emphasis_2_findings.md`
- Vergleich: `v2/COMPARISON.md`
- Kompakte erfolgreiche Rohartefakte: `v2/raw/study_artifacts.tar.gz`
- Quellen/Claims/Szenarien: `inputs/games/bohnanza_base_2023/*_v2.*`, `checks/scenarios/bohnanza_base_2023_v2.json`

Ältere Bohnanza-Präsentationen bleiben über Git nachvollziehbar.
