# Bohnanza Base Game 2023 V2

## Ergebnis auf einen Blick

| Evidenzgruppe | Original | Structured 1 | Structured 2 | Structured 3 |
|---|---:|---:|---:|---:|
| Technische Checks 01–04 | 4/4 | 4/4 | 4/4 | 4/4 |
| Robustheit | 100/100 | 100/100 | 100/100 | 100/100 |
| Spielerzahl-Probes | 5/5 | 5/5 | 5/5 | 5/5 |
| Clear-basis | 33/38 | 33/38 | **35/38** | 33/38 |
| Human-decision-basis | **4/4** | 3/4 | 3/4 | 3/4 |
| Szenario PASS/FAIL/CRASH | 37/5/0 | 36/6/0 | 38/3/1 | 36/6/0 |
| Neutraler Judge-Mittelwert | 0,643 | **0,713** | 0,523 | 0,617 |

*Diese Gruppen werden nicht zu einem Gesamtscore kombiniert. Die beiden Clear-Emphasis-Läufe bleiben im vollständigen Vergleich sichtbar.*

## Drei exakte Wiederholungen der verbesserten Form

Alle drei Structured-Läufe wurden frisch aus demselben byte-identischen initialen Modellpaket erzeugt. Frühere Ergebnisse bleiben unabhängig vom Ausgang erhalten.

- **Structured 1:** 33/38 Clear, stärkstes Judge-Signal.
- **Structured 2:** 35/38 Clear, aber exponentielle Trade-Aktionsmenge und `R04`-Crash.
- **Structured 3:** 33/38 Clear, kein Crash, Judge-Signal zwischen 1 und 2.

Structured 3 reproduziert exakt die sechs gescorten Fehler von Structured 1: `R10`, `R16`, `R17`, `R22`, `R23`, `R24`. Das Modell wählte ausdrücklich nur Ein-Karten-Angebote, obwohl das Supplement beliebig große positive Kartenmengen vorgibt.

## Interpretation

Kein Structured-Lauf ist über alle Evidenzgruppen der beste. Die drei exakten Generationen zeigen Varianz: Clear-Passrate, Laufzeit und unabhängiges Review bewegen sich nicht gemeinsam. Bei `n=3` bleibt das deskriptiv und erlaubt keine kausale Aussage.

## Details

**[Vollständige Methodik, Fehlergruppen, Judges und Provenienz](DETAILS.md)**

Maschinenprofile: [`v2/original_result.md`](v2/original_result.md) · [`v2/structured_clarification_1_result.md`](v2/structured_clarification_1_result.md) · [`v2/structured_clarification_2_result.md`](v2/structured_clarification_2_result.md) · [`v2/structured_clarification_3_result.md`](v2/structured_clarification_3_result.md) · [Sechsfachvergleich](v2/COMPARISON.md)
