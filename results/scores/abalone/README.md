# Abalone: Original-PDF vs. Setup-Emphasis

## Ergebnis auf einen Blick

Beide Umgebungen bestehen technische Checks, Spielerzahlprüfung, Rollouts und Interface-Roundtrips. Der Original-Run verfehlt ausschließlich die klare Startaufstellung und setzt 13 statt 14 Kugeln je Farbe. Nach einer getrennt attribuierten Wiederholung dieser klaren Figure-1-Regel besteht die Aufstellung; dafür regressiert der zuvor korrekte Forced Pass.

Der zweite Lauf ist ausdrücklich eine **Clear-Rule Emphasis Condition**, keine Klarstellung einer Quellenlücke.

| Evidenzgruppe | Original-PDF | PDF + Setup-Emphasis |
|---|---:|---:|
| Agentischer Gate (**EV1**) | 1,000 | 1,000 |
| Technische Checks 01–04 (**EV2**) | 4/4 | 4/4 |
| Robustheit (**EV3**) | 100/100 | 100/100 |
| Interface (**EV4**) | 8.888.062/8.888.062 | 8.528.518/8.528.518 |
| Klare Regeln (**EV5**) | 32/33 | 33/33 |
| Human Decisions (**EV6**) | 5/5 | 4/5 |
| Szenarioabdeckung (**EV7**) | 38/38 | 38/38 |
| Clear Claim-Mapping/Evaluation | 33/33 | 33/33 |
| Neutraler Judge-Mittelwert (**EV8**) | 0,867 (SD 0,031) | 0,893 (SD 0,081) |
| Persona-Reviews (**EV9**, kein Score) | nicht ausgeführt | nicht ausgeführt |
| Deklarierte materielle Annahmen (**EV10**, kein Score) | 2 | 2 |

*Die Evidenzgruppen werden nicht kombiniert. Abdeckung bedeutet Auswertung aller konfigurierten Szenarien, nicht vollständige Regelkorrektheit. Kein Plot vorhanden (optional).*

## Abweichungen

**Original:**
- `ABAL-R01`: 13 schwarze und 13 weiße Kugeln statt 14/14.

**Setup-Emphasis:**
- `ABAL-R01` wechselt zu PASS.
- `ABAL-R19` wechselt zu FAIL: kein Forced Pass ohne legale Bewegung.

Alle drei Judges pro Bedingung bestätigen jeweils den deterministischen Hauptfehler. Ein zusätzlicher Judge-Befund zu möglichen Action-Aliasen bleibt ein ungescorter Regressionkandidat, weil das eingefrorene Eindeutigkeitsszenario besteht.

## Ressourcen

| Messwert | Original | Setup-Emphasis |
|---|---:|---:|
| Modellaufrufe | 4 | 4 |
| Provider-Zeit | 688,769 s | 662,597 s |
| Input-Tokens | 1.101.308 | 944.830 |
| Cached Input-Tokens | 910.336 | 747.264 |
| Output-Tokens | 21.546 | 21.111 |
| Reasoning-Tokens | 9.444 | 8.197 |
| API-äquivalente Kostenschätzung | 2,06 USD | 1,99 USD |
| Python-Codezeilen | 245 | 344 |

## Detailansicht

**[Alle Checks, 38 Szenarien, Einzel-Judges, Annahmen und Provenienz öffnen](DETAILS.md)**

Maschinennahe Profile: [`v2/original_result.md`](v2/original_result.md) · [`v2/setup_emphasis_result.md`](v2/setup_emphasis_result.md) · [Vergleich](v2/COMPARISON.md)
