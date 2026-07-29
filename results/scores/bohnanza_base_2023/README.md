# Bohnanza Base Game 2023 V2

## Ergebnis auf einen Blick

Alle drei frischen Implementierungen bestehen technische Checks, 100 reproduzierbare Rollouts, Interface und Spielerzahlen. Die Regeltreue bleibt jedoch instabil. Das Original besteht 33/38 Clear-Szenarien. Zwei Generierungen mit demselben Clear-Rule-Emphasis-Paket bestehen jeweils nur 30/38.

Die Betonung verbessert mehrere ausdrücklich angesprochene Mechaniken, erzeugt aber in beiden Läufen neue, nicht betonte Regressionen. Der schlechte erste Emphasis-Lauf ist damit kein isolierter Ausreißer. Da sämtliche betonten Regeln bereits im Publisher-PDF klar waren, handelt es sich nicht um Evidenz für eine Quellenlücke.

| Evidenzgruppe | Original | Emphasis 1 | Emphasis 2 |
|---|---:|---:|---:|
| Agentischer Gate | PASS | PASS | PASS |
| Technische Checks 01–04 | 4/4 | 4/4 | 4/4 |
| Robustheit | 100/100 | 100/100 | 100/100 |
| Spielerzahl-Probes | 5/5 | 5/5 | 5/5 |
| Clear-basis | 33/38 | 30/38 | 30/38 |
| Human-decision-basis | 4/4 | 3/4 | 2/4 |
| Szenarioabdeckung | 42/42 | 42/42 | 42/42 |
| Clear-Claim-Mapping | 80/81 + Ausnahme | gleich | gleich |
| Neutraler Judge-Mittelwert | 0,643 (SD 0,081) | nicht ausgeführt | 0,423 (SD 0,038) |

*Diese Gruppen werden nicht zu einem Gesamtscore kombiniert. Emphasis 1 bleibt als gültige unjudged Szenarioevidenz erhalten; nur Emphasis 2 erhielt wie vorab festgelegt Judges.*

## Gezielte Effekte

- Ungleiche Mehrkarten-Trades: beide Emphasis-Läufe verbessern die gescorten Zwei-gegen-eins-Fälle.
- Soy-Bohnometer: beide verbessern den Originalfehler.
- Garden-Bohnometer: nur Emphasis 1 verbessert ihn; Emphasis 2 regressiert erneut.
- Dritte Leerung in Phase 2: der Terminalübergang verbessert sich, aber neue Fehler bei Red-Auszahlung beziehungsweise finaler Ernte verhindern vollständiges Bestehen.

## Wichtigste Regressionen

Emphasis 1 führt Fehler bei optionalem zweitem Pflanzen, separatem Zwangsernten, Pflanzreihenfolge und Red-Bohnometer ein. Emphasis 2 erzeugt falsches Drei-Spieler-Setup, erzwungene Pflanzreihenfolge, fehlendes Off-turn-Ernten, falsches Garden-Bohnometer und ausgelassene finale Ernten.

Alle drei Emphasis-2-Judges bewerten die fehlende finale Ernte als kritisch.

## Details

**[Vollständige Methodik, Fehlergruppen, Wiederholungsdesign, Judges und Provenienz](DETAILS.md)**

Maschinenprofile: [`v2/original_result.md`](v2/original_result.md) · [`v2/clear_rule_emphasis_2_result.md`](v2/clear_rule_emphasis_2_result.md) · [Dreifachvergleich](v2/COMPARISON.md)
