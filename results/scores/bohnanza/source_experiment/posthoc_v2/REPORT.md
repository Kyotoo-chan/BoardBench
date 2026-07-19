# Bericht: einheitliches Ausgabeformat und Evaluator v2

## Problem

Die ursprüngliche Bohnanza-Auswertung setzte voraus, dass generierte Zustände bestimmte Attribute, Containerformen, Phasenbezeichnungen und Tupelpositionen verwenden. Diese Annahmen waren nie Teil des Implementierungsvertrags. Dadurch wurden semantisch ähnliche Implementierungen abhängig von ihrer internen Python-Repräsentation unterschiedlich bewertet.

Über 13 Implementierungen enthielten die eingefrorenen Ergebnisse 141 Szenario-Crashes. Der post-hoc Adapter v2 klassifiziert davon 84 als PASS, 21 als bestätigten FAIL und 36 als UNTESTABLE. Kein Crash bleibt übrig. Zusätzlich wechseln 60 ursprüngliche FAILs zu PASS, hauptsächlich wegen vorher zu enger Aktions- und Phasenbezeichnungsannahmen.

## Dauerhafte Lösung für neue Generationen

Neue Contract-v2-Implementierungen behalten die bisherige `Game`-API und müssen zusätzlich vier Methoden bereitstellen:

```text
state_to_data(state)
state_from_data(payload)
action_to_data(action)
action_from_data(payload)
```

Die Methoden verwenden JSON-sichere, BoardBench-eigene Datenprofile. Für Bohnanza ist das Profil in `inputs/games/bohnanza/environment_profile.json` definiert. Der generische Vertrag liegt in `inputs/prompts/environment_contract.md`.

Damit testen Szenarien künftig ausschließlich:

- kanonische vollständige Zustandsdaten;
- kanonische Aktionsdaten;
- die bestehende öffentliche `Game`-API.

Nicht mehr zulässig sind Zugriffe auf generierte Attribute, Dataclasses, Modulkonstanten, private Hilfsmethoden, Aktions-Tupelpositionen oder erratene Aliasnamen. `agentic_self_check.py` und Check 04 erzwingen Methoden, JSON-Domäne, Profilfelder sowie State-/Action-Roundtrips bereits vor der eigentlichen Evaluation.

## Post-hoc Ergebnisse

| Bedingung | V2 P/F/C/U | Passanteil bewertet | Coverage |
|---|---:|---:|---:|
| PDF + korrekte JSON | 61/33/0/17 | 0,649 | 0,847 |
| PDF + manipulierte JSON | 26/7/0/78 | 0,788 | 0,297 |
| manipulierte PDF + JSON | 20/45/0/46 | 0,308 | 0,586 |
| PDF allein | 42/17/0/52 | 0,712 | 0,532 |
| neuer korrekter Diagnoselauf | 29/7/0/1 | 0,806 | 0,973 |

Der neue korrekte Lauf verändert sich von `0/2/35/0` auf `29/7/0/1`. Sein Judge-Mittel von 0,443 bleibt unverändert. Diese Kombination ist plausibel: Viele Kernregeln funktionieren, während die Judges weiterhin sieben materielle Defektbereiche erkennen.

## Interpretation

- Die extrem niedrigen ursprünglichen Szenariowerte waren zu einem großen Teil Evaluatorartefakte.
- Der neue korrekte Lauf ist nicht grundsätzlich kaputt; mit representation-sicherer Auswertung besteht er 29 von 36 bewertbaren Fällen.
- Die manipulierte PDF bleibt auch mit v2 klar schwächer als die sauberen, gut abdeckbaren Läufe.
- Hohe Passanteile bei `json_mutated` und einzelnen PDF-Runs sind wegen sehr geringer Coverage nicht als gute Regelkonformität interpretierbar.
- PDF allein kann wegen nur 53,2 % Coverage nicht fair als besser als saubere JSON bewertet werden.

## Wissenschaftliche Grenze

V2 wurde post hoc nach Sichtung der Fehlermuster entwickelt und ist deshalb diagnostische, nicht preregistrierte Evidenz. Die eingefrorenen Originaldateien bleiben unverändert. Für eine methodisch saubere neue Vergleichsrunde muss der Contract-v2 inklusive Bohnanza-Profil vor der Generation eingefroren und anschließend für alle Bedingungen unverändert verwendet werden.
