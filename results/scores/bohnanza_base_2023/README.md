# Bohnanza Base Game 2023 V2

## Ergebnis auf einen Blick

Die Art der Zusatzinformation macht einen deutlichen Unterschied:

| Evidenzgruppe | Original | Emphasis 1 | Emphasis 2 | Strukturierte Klarstellung |
|---|---:|---:|---:|---:|
| Technische Checks 01–04 | 4/4 | 4/4 | 4/4 | 4/4 |
| Robustheit | 100/100 | 100/100 | 100/100 | 100/100 |
| Spielerzahl-Probes | 5/5 | 5/5 | 5/5 | 5/5 |
| Clear-basis | 33/38 | 30/38 | 30/38 | **33/38** |
| Human-decision-basis | 4/4 | 3/4 | 2/4 | **3/4** |
| Szenarioabdeckung | 42/42 | 42/42 | 42/42 | 42/42 |
| Neutraler Judge-Mittelwert | 0,643 | 0,560 | 0,423 | **0,713** |

*Diese Gruppen werden nicht zu einem Gesamtscore kombiniert.* Die Übersichtsplots zeigen Emphasis 1 (jetzt mit Judges); Emphasis 2 bleibt in den Tabellen.

Die beiden schmalen Emphasis-Pakete lenkten Aufmerksamkeit auf vier bekannte Fehlergruppen, erzeugten aber viele Regressionen. Die neue strukturierte Klarstellung kombiniert stattdessen:

- vier freigegebene Entscheidungen für digitale Quellenlücken;
- eine ausgewogene Ganzspiel-Checkliste für Setup, Phasen, Handel, Anbau, Ernte, alle Bohnometer, Recycling, Spielende und Privatinformation;
- die ausdrückliche Anweisung, keine Regel zugunsten einzelner Highlights zu vernachlässigen.

Das hilft: Setup, Bohnometer, Off-turn-Ernten und finale Wertung sind nun korrekt; der Judge-Mittelwert ist der höchste aller Bedingungen. Perfekt ist die Implementierung trotzdem nicht.

## Verbleibende Fehler

- Ablehnen der optionalen zweiten Handkarte wechselt nicht in Phase 2 (`R10`).
- Ungleiche Mehrkarten-Trades fehlen in der enumerierten Aktionsmenge (`R16`, `R17`).
- Eigentümer können die Reihenfolge ihrer neuen Karten nicht frei wählen (`R22`–`R24`).
- Die Judges finden zusätzlich private gegnerische Handidentitäten in Trade-Aktionen.

Diese Punkte standen ausdrücklich im Supplement. Sie sind daher Implementierungsfehler und keine verbleibenden Quellenlücken.

## Interpretation

Mehr Kontext hilft hier dann, wenn er **ausgewogen strukturiert ist und echte digitale Lücken explizit entscheidet**. Eine schmale Wiederholung bereits klarer Regeln kann dagegen Salienz verschieben und andere Mechaniken destabilisieren.

Die strukturierte Bedingung ist ein nachträglich angepasstes Nachfolgeexperiment, kein unabhängiges Replikat und keine Best-of-Ersetzung. Alle früheren Läufe bleiben sichtbar.

## Details

**[Vollständige Methodik, Fehlergruppen, Judges und Provenienz](DETAILS.md)**

Maschinenprofile: [`v2/original_result.md`](v2/original_result.md) · [`v2/clear_rule_emphasis_1_result.md`](v2/clear_rule_emphasis_1_result.md) · [`v2/clear_rule_emphasis_2_result.md`](v2/clear_rule_emphasis_2_result.md) · [`v2/structured_clarification_1_result.md`](v2/structured_clarification_1_result.md) · [Vierfachvergleich](v2/COMPARISON.md)
