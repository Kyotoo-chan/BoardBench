# Bohnanza Base Game 2023 V2

## Ergebnis auf einen Blick

| Evidenzgruppe | Original | Emphasis 1 | Emphasis 2 | Structured 1 | Structured 2 |
|---|---:|---:|---:|---:|---:|
| Technische Checks 01–04 | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 |
| Robustheit | 100/100 | 100/100 | 100/100 | 100/100 | 100/100 |
| Spielerzahl-Probes | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| Clear-basis | 33/38 | 30/38 | 30/38 | 33/38 | **35/38** |
| Human-decision-basis | 4/4 | 3/4 | 2/4 | 3/4 | 3/4 |
| Szenario PASS/FAIL/CRASH | 37/5/0 | 33/9/0 | 32/10/0 | 36/6/0 | 38/3/1 |
| Neutraler Judge-Mittelwert | 0,643 | nicht ausgeführt | 0,423 | **0,713** | 0,523 |

*Diese Gruppen werden nicht zu einem Gesamtscore kombiniert.*

## Exakte Wiederholung der verbesserten Form

`Structured 2` ist eine vorab registrierte, frische Generation mit demselben initialen Modellpaket wie `Structured 1`. Beide behalten das Publisher-PDF und dieselbe strukturierte Klarstellung; frühere Läufe werden nicht ersetzt.

Der zweite Lauf ist nicht einfach schlechter: Er verbessert die Clear-Szenarien von 33/38 auf 35/38 und behebt Mehrkarten-Trades sowie freie Kartenreihenfolge. Gleichzeitig erzeugt er eine exponentielle Trade-Aktionsmenge, wodurch `R04` nicht mehr in praktikabler Zeit läuft, und erhält deutlich niedrigere Judge-Werte.

Verbleibende gescorte Fehler:

- `R04`: bounded play crasht/timeoutet wegen exponentieller Aktionsenumeration;
- `R10`: Ablehnen der optionalen zweiten Handkarte wechselt nicht in Phase 2;
- `R14`: der Vier-Phasen-Ablauf bleibt in `plant_received` hängen;
- `R23`: dieselbe Phasenabschlussstörung betrifft die freigegebene Phase-3-Reihenfolge.

## Interpretation

Ein zweiter identischer Lauf ist nicht automatisch „cooked“. Die beiden strukturierten Läufe zeigen Modellvarianz: bessere abgedeckte Szenarien können mit schlechterer Laufzeit und niedrigerem unabhängigen Review einhergehen. Bei `n=2` ist das deskriptiv, nicht kausal.

## Details

**[Vollständige Methodik, Fehlergruppen, Judges und Provenienz](DETAILS.md)**

Maschinenprofile: [`v2/original_result.md`](v2/original_result.md) · [`v2/structured_clarification_1_result.md`](v2/structured_clarification_1_result.md) · [`v2/structured_clarification_2_result.md`](v2/structured_clarification_2_result.md) · [Fünffachvergleich](v2/COMPARISON.md)
