# Exploding Kittens V2: Original-PDF vs. gezielte Klarstellung

## Ergebnis auf einen Blick

Der gültige Original-Run besteht den technischen Gate, alle Spielerzahlprüfungen und 35 von 38 Szenarien, erzeugt aber in 2 von 100 Rollouts eine Sackgasse: Favor darf ein leeres Ziel wählen und wartet danach auf eine unmögliche Kartenübergabe. Die gezielte Klarstellung verbietet leere Favor- und Pärchenziele. Eine frische Implementierung besteht danach 37 von 38 Szenarien und 100 von 100 Rollouts.

Die Intervention behebt damit genau den beobachteten Source-Gap-Defekt. Gleichzeitig entsteht im frischen Lauf eine neue klare Abweichung: ein geketteter Angriff weist drei statt genau zwei Züge zu. Eine weitere Verbesserung bei der Eliminierungsablage ist nicht der Klarstellung zurechenbar.

| Evidenzgruppe | Original-PDF | PDF + gezielte Klarstellung |
|---|---:|---:|
| Agentischer Gate | PASS | PASS (1 Pre-Eval-Reparatur) |
| Technische Checks 01–04 | 4/4 | 4/4 |
| Robustheit, 100 Rollouts | 98/100 | 100/100 |
| Interface | 12.436/12.436 | 15.589/15.589 |
| Spielerzahl-Probes | 6/6 | 6/6 |
| Klare Regeln | 32/34 | 33/34 |
| Human-Decision-Regeln | 3/4 | 4/4 |
| Szenarioabdeckung | 38/38 | 38/38 |
| Clear-Claim-Mapping/Evaluation | 65/65 | 65/65 |
| Neutraler Judge-Mittelwert | 0,813 (SD 0,012) | 0,907 (SD 0,012) |

*Die Evidenzgruppen werden nicht zu einem Gesamtscore kombiniert. Szenarioabdeckung bedeutet nur, dass alle konfigurierten Fälle ausgewertet wurden. Claim-Mapping ist kein Vollständigkeitsbeweis jeder Assertion.*

## Bestätigte Veränderungen

- **Gezielter Erfolg:** `EXPL-R27` wechselt von FAIL zu PASS; leere Hände sind keine legalen Favor-/Pärchenziele mehr. Die zugehörige Runtime-Sackgasse verschwindet.
- **Nicht zurechenbare Verbesserung:** `EXPL-R11` und `EXPL-R12` wechseln zu PASS; die vollständige Hand eines eliminierten Spielers wird nun abgelegt. Diese Publisher-Regel war nicht Teil der Klarstellung.
- **Neue klare Regression:** `EXPL-R18` wechselt zu FAIL; ein Gegenangriff erzeugt drei statt genau zwei geschuldete Züge.

Alle drei Original-Judges bestätigen die beiden Originaldefekte. Alle drei Clarified-Judges bestätigen ausschließlich die Angriffsketten-Regression. Bei je einer frischen Implementierung pro Bedingung (`n=1`) ist dies kein allgemeiner Kausal- oder Varianznachweis.

## Ressourcen

| Messwert | Original | Clarified |
|---|---:|---:|
| Modellaufrufe inklusive Judges | 4 | 5 |
| Provider-Zeit | 846,120 s | 856,884 s |
| Input-Tokens (gecacht) | 1.704.563 (1.460.992) | 1.857.484 (1.587.712) |
| Output-/Reasoning-Tokens | 32.106 / 13.704 | 31.738 / 12.726 |
| API-äquivalente Schätzung | 2,91 USD | 3,09 USD |
| Python-Codezeilen | 504 | 486 |

Der Clarified-Lauf enthält zwei Implementierungsaufrufe, weil der erste vor der Evaluation keine Pflichtartefakte erzeugte und evaluatorneutral repariert wurde. Tatsächliche OAuth-Abonnementkosten sind nicht verfügbar.

## Detailansicht

**[Methodik, Defekte, Annahmen, Provenienz und Artefakte öffnen](DETAILS.md)**

Maschinennahe Profile: [`v2/original_result.md`](v2/original_result.md) · [`v2/clarified_result.md`](v2/clarified_result.md) · [Vergleich](v2/COMPARISON.md)
