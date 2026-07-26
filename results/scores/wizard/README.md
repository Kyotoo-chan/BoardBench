# Wizard: Original-PDF vs. präzisierte Fassung

## Ergebnis auf einen Blick

Beide Spielumgebungen bestehen die technischen, Spielerzahl- und gesampelten Stabilitätsprüfungen. Die Implementierung aus dem Original-PDF verfehlt drei getestete Regelinteraktionen. Nach Ergänzung der sieben getrennt attribuierten Klarstellungen bestehen zwei davon; eine Entscheidung zum farblosen Stich nach Narr → Zauberer bleibt fehlerhaft.

Die Klarstellung verbessert damit die getestete Regeltreue sichtbar, beseitigt aber nicht jeden Übersetzungsfehler. Das ist Evidenz für einen wesentlichen Spezifikationsbeitrag in diesem Paar, kein allgemeiner Kausalnachweis bei `n=1`.

| Evidenzgruppe | Original-PDF | PDF + Klarstellung |
|---|---:|---:|
| Agentischer Gate (**EV1**) | 1,000 | 1,000 |
| Technische Checks 01–04 (**EV2**) | 4/4 | 4/4 |
| Robustheit, 100 Rollouts (**EV3**) | 100/100 | 100/100 |
| Interface (**EV4**) | 226.118/226.118 | 226.148/226.148 |
| Klare Regeln (**EV5**) | 22/23 | 23/23 |
| Klarstellungsabhängige Regeln (**EV6**) | 9/11 | 10/11 |
| Szenarioabdeckung (**EV7**) | 34/34 | 34/34 |
| Clear-Claim-Mapping/Evaluation | 50/50 | 50/50 |
| Neutraler Judge-Mittelwert (**EV8**) | 0,740 (SD 0,035) | 0,897 (SD 0,015) |
| Persona-Reviews (**EV9**, kein Score) | nicht ausgeführt | nicht ausgeführt |
| Deklarierte materielle Annahmen (**EV10**, kein Score) | 3 | 2 |

*Die Evidenzgruppen werden nicht zu einem Gesamtscore kombiniert. Szenarioabdeckung bedeutet, dass alle konfigurierten Fälle ausgewertet wurden; Claim-Mapping ist kein Vollständigkeitsbeweis jeder einzelnen Assertion. Kein Plot vorhanden (optional).*

## Änderungen durch die Klarstellung

Zwei Erwartungen wechseln von FAIL zu PASS:

1. **`WIZ-R04`** — Spieler 0 ist deterministisch erster Geber; die Original-Implementierung wählte den Geber zufällig.
2. **`WIZ-R28`** — eröffnet ein Zauberer den Stich, bleibt der Stich farblos und alle späteren Karten bleiben legal.

Weiterhin fehlerhaft:

- **`WIZ-R14`** — nach Narr → Zauberer setzt eine spätere Farbkarte weiterhin fälschlich `led_suit`. Der erste Zauberer gewinnt zwar, aber der Stich bleibt nicht vollständig farblos und frei.

Ein Judge-Befund zur dauerhaften Sichtbarkeit bereits gespielter Karten bleibt ein neuer Regressionkandidat. Er wird nicht rückwirkend als Szenariofehler gezählt.

## Ressourcen

| Messwert | Original-PDF | PDF + Klarstellung |
|---|---:|---:|
| Modellaufrufe inklusive Judges | 4 | 4 |
| Provider-Zeit | 892,778 s | 904,204 s |
| Input-Tokens | 1.174.314 | 1.326.930 |
| Cached Input-Tokens | 968.192 | 1.132.800 |
| Output-Tokens | 26.421 | 29.168 |
| Reasoning-Tokens | 10.215 | 13.446 |
| API-äquivalente Kostenschätzung | 2,31 USD | 2,41 USD |
| Python-Codezeilen | 331 | 477 |

Die tatsächlichen OAuth-Abonnementkosten sind nicht verfügbar; USD-Werte sind getrennt ausgewiesene API-Äquivalente.

## Detailansicht

**[Alle Checks, 34 Szenarien, Einzel-Judges, Annahmen, Befunde und Provenienz öffnen](DETAILS.md)**

Maschinennahe Profile: [`v2/original_result.md`](v2/original_result.md) · [`v2/clarified_result.md`](v2/clarified_result.md) · [Vergleich](v2/COMPARISON.md)
