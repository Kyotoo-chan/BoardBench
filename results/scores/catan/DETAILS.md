# CATAN 2022 V2: detaillierte Auswertung

[← Kurzüberblick](README.md)

## Studiendesign

- Publisherquellen: deutsche Spielanleitung 2022 plus editionsgleicher CATAN-Almanach 2022.
- Scope: abgebildeter Einsteigeraufbau für 3 und 4 Spieler; strikte Phasen Würfeln → Handeln → Bauen.
- Ausgeschlossen: variabler Aufbau, empfohlener Experten-Phasenmix, App und Erweiterungen.
- 121 atomare Claims: 104 clear, 15 missing, 1 ambiguous, 1 untestable.
- 99 materielle und ausführbare Clear Claims.
- 51 Szenarien mit 107 Named Cases: 40 clear, 11 human decision.
- Generierung: `gpt-5.6-sol`, Thinking `low`; Judges: dasselbe Modell, Thinking `medium`.

## Gruppierte Ergebnisse

| Gruppe | Ergebnis |
|---|---:|
| Agentischer Pre-Evaluation-Gate | PASS |
| Generation / Repairs | 1 / 0 |
| Technik 01–04 | 4/4 |
| Random Rollouts | 100/100 |
| Action-Language | 8.883.707/8.883.707 |
| Spielerzahl 3/4 und Ablehnung 2/5 | 4/4 |
| Clear-basis | 37/40 |
| Human-decision-basis | 8/11 |
| Szenarien / Named Cases ausgewertet | 51/51 / 107/107 |
| Claim-Mapping / evaluated | 99/99 / 99/99 |
| Judges | 0,62 / 0,66 / 0,61 |
| Judge-Mittel (sample SD) | 0,630 (0,026) |

## Clear-Defektgruppe

### Längste Handelsstraße fehlt vollständig

`special_cards.longest_road_owner` und `longest_road_length` werden initialisiert, danach aber nirgends neu berechnet. Das verursacht sämtliche Clear-Fehler:

- `CAT-R18-longest-threshold-branch`: keine Vergabe bei fünf zusammenhängenden Straßen;
- `CAT-R19-longest-interruption`: weder gegnerische Unterbrechung noch eigene Nicht-Unterbrechung wird ausgewertet;
- `CAT-R20-longest-transfer-ties`: kein Transfer und keine korrekte Vakanz bei Gleichständen nach Unterbrechung.

Die Implementierung kann dadurch Punkte und Sieger falsch bestimmen. Alle drei Judges erkennen diese Auslassung unabhängig.

## Human-Decision-Fehler

### `R21`: Edge-simple Schleifen

Schleifen und Figure-eight-Fälle scheitern, weil überhaupt kein Longest-Road-Algorithmus existiert. Das ist keine isolierte Widerlegung der gewählten Edge-simple-Trail-Definition.

### `R40`: Straßenbau und Figurenstock

`_road_actions(..., free=True)` überspringt die Prüfung des verbleibenden Straßenstocks. Eine Person mit nur einer Straße kann nach deren Platzierung in `road_building` verbleiben und eine weitere Straße mit negativem Stock platzieren.

### `R43`: sofortiger Sieg während Karteneffekt

Der Fall erwartet, dass die erste kostenlose Straße die Längste Handelsstraße und damit den zehnten Punkt erzeugt. Wegen der fehlenden Vergabe bleibt der Zustand nichtterminal. Ob ein korrekt erzeugter Sieg den restlichen Effekt ordnungsgemäß abbricht, wird dadurch nicht unabhängig widerlegt.

## Judge-Evidenz

Gemeinsamer Kern aller Reviews:

1. fehlende Längste Handelsstraße — critical/major;
2. Straßenbau ignoriert Figurenstock — major;
3. schrittweiser Inlandshandel hat trotz endlicher Aktionen pro Zustand keine Gesamtobergrenze für Angebotsmengen.

Weitere Signale:

- Ein Review findet einen plausiblen ungescorten Interrupt-Fehler: bereits eingereichte private Abgaben werden erst am Ende entfernt und können zuvor durch eine erlaubte Entwicklungskarten-Unterbrechung verändert werden.
- Der Empty-victim-Befund eines Reviews widerspricht der eingefrorenen Human Decision: angrenzende leere Hände bleiben absichtlich auswählbar und übertragen nichts.
- Same-resource-Seehandel, optionaler Ritterraub und die physische Ablage gespielter Fortschrittskarten bleiben Interpretations-/Repräsentationsfragen und werden nicht als klare Defekte berichtet.

## Möglicher Interventionsbedarf

Noch keine Intervention ist festgelegt. Die Evidenz trennt:

- **publisher-clear Implementierungsfehler:** Longest Road, Road-Building-Stock;
- **echte digitale Spezifikationskandidaten:** maximale Angebotslänge, Stabilität bereits eingereichter Abgaben bei Interrupts, optionaler Ritterraub;
- **Evaluator-/Repräsentationsfragen:** Same-resource-Tausch und physische Kartenablage.

Eine spätere Source-Gap-Klarstellung darf nur die echten digitalen Lücken entscheiden. Eine Betonung der bereits klaren Longest-Road-Regeln müsste separat als Clear-Rule-Emphasis bezeichnet werden.

## Evaluatorrevision

Der erste Replay (40 PASS / 11 FAIL) war ungültig:

1. eine illegale Trade-Proposal-Aktion wurde dennoch ausgeführt;
2. eine nicht deklarierte Decklistenrichtung wurde hart vorausgesetzt;
3. historische Karten-Zonen-Erwartungen widersprachen den V2-`revealed`-Feldern.

Das Archiv liegt unter `v2/raw/invalid_evaluator_replay_1.tar.gz`. Evaluator r2 korrigiert ausschließlich diese Punkte; Code, Modellantwort und Generationsevidenz sind byte-identisch geblieben. Drei Judges wurden erst nach dem gültigen r2-Replay gestartet.

## Artefakte

- `v2/original_result.json`, `v2/original_result.md`
- `v2/original_findings.md`
- `v2/evaluation_manifest.json`
- `inputs/games/catan/evaluator_revision_v2_r2.json`
- `v2/raw/FAILED_ATTEMPTS.md`
- erfolgreiche Rohartefakte werden kompakt unter `v2/raw/study_artifacts.tar.gz` gebündelt
