# CATAN 2022 V2

## Ergebnis auf einen Blick

Der frische Original-Run nutzt ausschließlich die vollständige deutsche Spielanleitung 2022 und den editionsgleichen Publisher-Almanach. Er besteht Technik, 100 Rollouts, Interface und beide unterstützten Spielerzahlen vollständig. Die wesentliche Regellücke der Implementierung ist die vollständig fehlende Berechnung der Längsten Handelsstraße.

| Evidenzgruppe | Original V2 |
|---|---:|
| Agentischer Gate | PASS, 1 Call, 0 Repairs |
| Technische Checks 01–04 | 4/4 |
| Robustheit | 100/100 |
| Action-Language | 8.883.707/8.883.707 |
| Spielerzahlen | 4/4 |
| Clear-basis | **37/40** |
| Human-decision-basis | **8/11** |
| Szenarioabdeckung | 51/51 |
| Named Cases | 107/107 |
| Neutral Judges | 0,62 / 0,66 / 0,61 |
| Judge-Mittelwert | **0,630** (SD 0,026) |

*Diese Evidenzgruppen werden nicht zu einem Gesamtscore kombiniert.*

## Hauptbefunde

- **Clear:** Längste Handelsstraße wird nie berechnet, vergeben, übertragen oder nach Unterbrechung entfernt (`R18`–`R20`).
- **Human Decision:** Schleifen-/Figure-eight-Fälle scheitern als Folge derselben Auslassung (`R21`).
- **Human Decision:** Straßenbau ignoriert den verbleibenden Straßenstock (`R40`).
- **Human Decision:** Der sofortige Sieg nach der ersten kostenlosen Straße bleibt aus, weil die fehlende Handelsstraßenwertung die zwei Punkte nicht vergibt (`R43`).

Alle Judges bestätigen die fehlende Längste Handelsstraße und den Straßenstockfehler. Zusätzlich zeigen sie eine echte noch offene digitale Spezifikationsfrage: Der schrittweise Handel vermeidet Power-Set-Aktionen, besitzt aber noch keine definierte Obergrenze für die Länge eines Angebots.

## Methodischer Hinweis

Der erste Evaluator-Replay war wegen drei neutralen Repräsentationsfehlern ungültig und wurde weder gescort noch gejudged. Die Implementierung blieb unverändert. Nur Evaluator r2 ist gültige Evidenz.

## Details

**[Vollständige Fehlergruppen, Judge-Evidenz und Evaluatorhistorie](DETAILS.md)**

Maschinenprofil: [`v2/original_result.md`](v2/original_result.md) · [Findings](v2/original_findings.md)

Der ältere `base_packet_1/`-Stressfall bleibt unverändert als historische Pilot-Evidenz erhalten und wird nicht mit V2 vermischt.
