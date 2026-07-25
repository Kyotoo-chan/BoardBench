# Bohnanza Base 2023: Original-PDF vs. präzisierte Fassung

## Ergebnis auf einen Blick

Beide Spielumgebungen bestehen die technischen und gesampelten Stabilitätsprüfungen. Die Implementierung aus dem Original-PDF verfehlt sieben getestete Regelinteraktionen. Nach Präzisierung steigen die Szenarien von `34/41` auf `39/41`; der neutrale Judge-Mittelwert steigt von `0,32` auf `0,60`. Zwei finale Erntefälle bleiben in beiden Bedingungen fehlgeschlagen — mit unterschiedlichen Defekten.

**Modellsetup für beide Bedingungen:** Implementierung mit `gpt-5.6-sol`, Thinking `low`; drei neutrale Judges mit `gpt-5.6-sol`, Thinking `medium`. Personas wurden in diesem Pilotlauf nicht ausgeführt.

| Evidenz | Original-PDF | Präzisierte Fassung |
|---|---:|---:|
| Technical Gate (**EV1**) | 4/4 | 4/4 |
| Runtime Robustness (**EV2**) | 100/100 | 100/100 |
| Interface (**EV3**) | 1,000 | 1,000 |
| Klare Regeln (**EV4**) | 25/26 | 25/26 |
| Klarstellungsabhängige Regeln (**EV5**) | 9/15 | 14/15 |
| Szenarioabdeckung (**EV6**) | 41/41 | 41/41 |
| Neutraler Judge-Mittelwert (**EV7**) | 0,320 (SD 0,069) | 0,600 (SD 0,035) |
| Persona-Reviews (**EV8**, kein Score) | nicht ausgeführt | nicht ausgeführt |
| Deklarierte materielle Annahmen (**EV9**, kein Score) | 3 Deklarationen | 4 Deklarationen |

*EV1–EV3 sind technische Kontrollen; EV6 bestätigt vollständige Szenarioabdeckung, nicht Korrektheit. EV4, EV5 und EV7 zeigen den für die Quellenänderung relevanten Unterschied. Kein Plot vorhanden (optional).*

## Erkannte Abweichungen des Originals (durch Klarstellung behoben)

- **EV5:** dritte Leerung in Phase 4 beendet sofort (erste Ziehkarte).
- **EV5:** Gartenbohnen-Auszahlungskurve.
- **EV5:** dritte Leerung genau auf der dritten Phase-4-Karte.
- **EV5:** Phase 3 geht an nicht-aktive Empfänger mit eigener Pflanzreihenfolge.
- **EV5:** dritte Leerung genau auf der zweiten Phase-4-Karte.

## Gemeinsame verbleibende Fehler

- **EV5 / EV4:** verpflichtende Endernte nach Phase-4-Leerung bzw. nach Phase-2-Fortsetzung — in beiden Bedingungen Fail, aber mit unterschiedlichen Ursachen (siehe DETAILS).

Die Klarstellung reduziert gezielte Übersetzungsfehler, löst aber weder die beobachtbare Endernte noch die von Judges markierten Action-Space-Probleme. Mit einem Implementierungslauf pro Bedingung (`n=1`) ist dies noch kein Varianz- oder alleiniger Kausalitätsnachweis.

## Aufwand

| Ressource | Original-PDF | Präzisierte Fassung |
|---|---:|---:|
| Implementierungsmodell | `gpt-5.6-sol` (`low`) | `gpt-5.6-sol` (`low`) |
| Reviewmodell für Judges | `gpt-5.6-sol` (`medium`) | `gpt-5.6-sol` (`medium`) |
| LLM-Aufrufe | 4 | 4 |
| Input-Tokens (davon gecacht) | 718.808 (529.152) | 856.596 (687.616) |
| Output-Tokens | 29.020 | 35.967 |
| API-äquivalente Kostenschätzung | 2,08 USD | 2,27 USD |
| Python-Codezeilen | 383 | 551 |

## Detailansicht

**[Alle Evaluationen, Checks 01–06, 41 Szenarien, Einzel-Judges, Annahmen und Rohpfade öffnen](DETAILS.md)**

Maschinennahe Zwischenberichte: [`base_pdf_1/REPORT.md`](base_pdf_1/REPORT.md) · [`clarified_1/COMPARISON.md`](clarified_1/COMPARISON.md)
