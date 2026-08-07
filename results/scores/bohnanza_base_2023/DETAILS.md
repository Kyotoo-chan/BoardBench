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
5. **Structured clarification 2:** exakte frische Wiederholung von Structured 1.
6. **Structured clarification 3:** dritte und final vorab registrierte exakte frische Wiederholung.

Structured 1 ist gegenüber den Emphasis-Läufen ein angepasster Nachfolger. Structured 2 und 3 replizieren ihn mit byte-identischem initialem Modellpaket. Alle Vorgänger bleiben erhalten; es gibt keine Best-of-Auswahl.

## Evidenzgruppen

| Evidenz | Original | Emphasis 1 | Emphasis 2 | Structured 1 | Structured 2 | Structured 3 |
|---|---:|---:|---:|---:|---:|---:|
| Generationscalls / Repairs | 1/0 | 1/0 | 1/0 | 1/0 | 2/1 | 1/0 |
| Technischer Gate | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 |
| Random Rollouts | 100/100 | 100/100 | 100/100 | 100/100 | 100/100 | 100/100 |
| Action-Language | 800.371/800.371 | 1.523.314/1.523.314 | 976.727/976.727 | 847.456/847.456 | 1.395.514/1.395.514 | 563.753/563.753 |
| Spielerzahlen | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| Szenarien PASS/FAIL/CRASH | 37/5/0 | 33/9/0 | 32/10/0 | 36/6/0 | 38/3/1 | 36/6/0 |
| Clear-basis | 33/38 | 30/38 | 30/38 | 33/38 | **35/38** | 33/38 |
| Human-decision-basis | **4/4** | 3/4 | 2/4 | 3/4 | 3/4 | 3/4 |
| Ausgewertete Abdeckung | 42/42 | 42/42 | 42/42 | 42/42 | 42/42 | 42/42 |
| Neutral Judges | 0,68/0,70/0,55 | nicht ausgeführt | 0,38/0,45/0,44 | 0,74/0,68/0,72 | 0,47/0,55/0,55 | 0,62/0,62/0,61 |
| Judge-Mittel (SD) | 0,643 (0,081) | – | 0,423 (0,038) | **0,713 (0,031)** | 0,523 (0,046) | 0,617 (0,006) |

## Ergebnisse nach Bedingung

### Original

Fünf Clear-Fehler: ungleiche Mehrkarten-Trades (`R16`, `R17`), Garden- und Soy-Bohnometer (`R30`, `R33`) sowie Phase-two-Ende bei dritter Leerung (`R40`). Alle vier Human Decisions bestehen.

### Clear-rule emphasis 1 und 2

Beide schmalen Interventionen erreichen 30/38 Clear, verlieren aber unterschiedliche nicht betonte Mechaniken. Emphasis 2 wiederholt den niedrigen Wert. Das bleibt bei `n=2` deskriptiv.

### Structured clarification 1

33/38 Clear und 3/4 Human Decision. Fehler: optionales zweites Pflanzen (`R10`), ungleiche Mehrkarten-Trades (`R16`, `R17`) sowie frei gewählte staged/revealed Pflanzreihenfolge (`R22`–`R24`, einschließlich `R23`). Judge-Mittel 0,713.

### Structured clarification 2

35/38 Clear und 3/4 Human Decision. Mehrkarten-Trades und freie Kartenreihenfolge bestehen. Defekte: exponentielle Aktionsenumeration mit `R04`-Crash, `R10`, `R14` und `R23`. Judge-Mittel 0,523.

### Structured clarification 3

33/38 Clear und 3/4 Human Decision ohne Crash. Es reproduziert exakt den gescorten Fehlervektor von Structured 1: `R10`, `R16`, `R17`, `R22`, `R23`, `R24`. Judge-Mittel 0,617.

Die Implementierung dokumentiert eine materielle Annahme, nur Ein-Karten-Angebote zu erzeugen. Diese Auswahl widerspricht der Structured-Clarification-Vorgabe, dass ein Handel jede positive Kartenanzahl enthalten kann. Alle drei Judges finden zusätzlich die zu späte Leerungsgrenze und das Leck tiefer gegnerischer Handidentitäten.

## Evaluatorhistorie und Host-Schutz

- Frühere ungültige Original- und Emphasis-Replays bleiben archiviert und ungescort.
- Structured 2 hatte einen Auth-Preflight ohne Modellaufruf, eine ungescorte Legacy-Contract-Invocation und eine ungescorte Low-Thinking-Judge-Invocation.
- Structured 2s Full-Suite-Runner überschritt bei `R04` 1.800 Sekunden und fror den Host ein. Die Implementierung wurde nicht verändert. Seitdem läuft dieselbe `run_scenario_v4`-Logik szenarioweise mit niedriger Priorität, einem CPU-Kern und 15-Sekunden-Prozessgrenze.
- Structured 3 wurde von Beginn an in diesem ressourcenisolierten Modus evaluiert; alle Szenarien beendeten sich, `R04` in 0,20 Sekunden.

## Interpretation

Kein Structured-Lauf dominiert alle Evidenzgruppen:

- Structured 1: höchstes Judge-Signal;
- Structured 2: höchste Clear-Passrate, aber einziger Crash;
- Structured 3: kein Crash, aber Rückkehr zum Structured-1-Fehlervektor.

Über drei exakte Generationen lauten die Clear-Werte 33/38, 35/38 und 33/38; Human Decision bleibt dreimal 3/4. Das zeigt Modellvarianz und die Notwendigkeit getrennter Evidenzgruppen. Bei `n=3` ist dies weiterhin deskriptiv, nicht kausal.

## Artefakte

- Supplement: `inputs/games/bohnanza_base_2023/structured_clarification_v3.md`
- Replikationsregister: `inputs/games/bohnanza_base_2023/structured_clarification_replication_v2.json`
- Structured 1–3: `v2/structured_clarification_{1,2,3}_result.json` und jeweilige `*_findings.md`
- Structured-3-Rohdaten: `v2/raw/structured_clarification_3/`
- Vergleich: `v2/COMPARISON.md`
