# Exploding Kittens V2: detaillierte Auswertung

[← Kurzüberblick](README.md)

**Modellsetup:** Beide Implementierungen `gpt-5.6-sol`, Thinking `low`; je drei gegenseitig blinde neutrale Judges `gpt-5.6-sol`, Thinking `medium`. Beide Bedingungen verwenden dasselbe vollständige Publisher-PDF, Contract-v2-Profil, Prompt und dieselbe V2.2-Rubrik. Clarified erhält zusätzlich ausschließlich `clarifications_v2.json`.

## Studiendesign

1. 78 atomare Claims: 66 `clear`, 5 `missing`, 4 `ambiguous`, 2 `untestable`, 1 `conflicting`.
2. 65 materielle/testbare Clear Claims sind 65/65 auf Szenarien gemappt und ausgewertet.
3. Original wird blind generiert, gegated und vollständig evaluiert.
4. Erst danach wird der reproduzierte Source-Gap-Defekt ausgewählt: leere Favor-/Pärchenziele.
5. Clarified behält PDF, Modell, Prompt, Contract, Profil und Evaluator byte- bzw. methodengleich und ergänzt genau eine attribuierte Entscheidung.
6. Technischer Gate, Robustheit, Interface, Spielerzahlen, 38 Szenarien und drei neutrale Judges bleiben getrennte Evidenz.

Es gibt keinen vermischten Korrektheitsscore und keine Best-of-Auswahl.

## Ausführbare Evidenz

| Evidenz | Original | Clarified |
|---|---:|---:|
| Agentischer Gate | PASS; 1 Call, 0 Repairs | PASS; 2 Calls, 1 Pre-Eval-Repair |
| Checks 01–04 | 4/4 | 4/4 |
| Random Rollouts | 98/100 | 100/100 |
| Action-Language | 12.436/12.436 | 15.589/15.589 |
| Spielerzahlen 2–5 / Ablehnung 1,6 | 6/6 | 6/6 |
| Szenarien gesamt | 35 PASS / 3 FAIL | 37 PASS / 1 FAIL |
| Clear-basis | 32/34 | 33/34 |
| Human-decision-basis | 3/4 | 4/4 |
| Ausgewertete Szenarien | 38/38 | 38/38 |
| Clear Claim-Mapping/Evaluation | 65/65 | 65/65 |

Die 34 Clear- und 4 Human-Decision-Fälle stehen mit Quellenzitaten, Fixtures und exakten Erwartungen in `checks/scenarios/expl_v2.json`. Vollständige Einzelergebnisse: `v2/original_scenarios.json` und `v2/clarified_scenarios.json` im gebündelten Roharchiv.

## Bestätigte Szenarioabweichungen

| Szenario | Basis | Original | Clarified | Diagnose |
|---|---|---:|---:|---|
| `EXPL-R11-explosion-eliminates` | clear | FAIL | PASS | Original eliminiert den Spieler, legt aber dessen Resthand nicht ab. |
| `EXPL-R12-last-survivor-wins` | clear | FAIL | PASS | Derselbe Ablagefehler ist im terminalen Zwei-Spieler-Fall sichtbar. |
| `EXPL-R27-empty-target-illegal` | human_decision | FAIL | PASS | Gezielte Klarstellung verbietet leere Favor-/Pärchenziele. |
| `EXPL-R18-attack-chain` | clear | PASS | FAIL | Clarified addiert die Zugschuld und erzeugt drei statt genau zwei Züge. |

Alle übrigen konfigurierten Szenarien bestehen in beiden Bedingungen. Die zwei Original-Rolloutfehler und ein zusätzlicher reproduzierter Diagnosezustand enden jeweils in `favor_give` gegen eine leere Hand; sie sind dieselbe Ursache wie `R27`.

## Unabhängige Judges

| Review | Original | Clarified |
|---|---:|---:|
| Judge 1 | 0,80 | 0,90 |
| Judge 2 | 0,82 | 0,90 |
| Judge 3 | 0,82 | 0,92 |
| **Mittelwert** | **0,813** | **0,907** |
| **Sample SD** | **0,012** | **0,012** |

Alle drei Original-Judges nennen sowohl die fehlende Eliminierungsablage als auch leere Favor-/Pärchenziele. Alle drei Clarified-Judges nennen ausschließlich die überhöhte Angriffsschuld. Judges sahen die vollständige jeweils zugewiesene Quellenbedingung einschließlich der attribuierten Klarstellung, aber keine Szenarien, Scores, anderen Reviews oder Vergleichsimplementierung.

## Deklarierte materielle Annahmen

### Original

- NÖ!-Reaktionen laufen als explizite Pass-/Reaktionsrunden.
- Angriff ersetzt eine vorhandene Zugschuld durch genau zwei Züge.
- Pärchen stiehlt reproduzierbar zufällig aus der Zielhand.

### Clarified

- Angriff wurde als `vorhandene Schuld + 1` interpretiert; diese Annahme verursacht `R18`.
- Nach einem NÖ! beginnt eine neue Reaktionsrunde für alle lebenden Mitspieler.
- Spieler 0 startet, weil kein digitales physisches Startkriterium vorliegt.

Die Anzahl der Annahmen ist kein Score.

## Intervention und Zurechnung

Die Klarstellung enthält nur `EXPL-D-EMPTY-TARGET`. Daher ist der Wechsel von `R27` und der zugehörigen Robustheit direkt interventionskongruent. Die korrigierte Eliminierungsablage und die neue Angriffsketten-Regression stammen aus der frischen Generation und dürfen nicht der Klarstellung zugerechnet werden.

## Ungültige Vorläufer

Vier frühere Artefaktgruppen bleiben ausdrücklich ungescort:

- `failed_preflight_1.tar.gz`: fehlerhafte evaluatorseitige Fixture-Inventur.
- `invalid_profile_evaluation_1.tar.gz`: nicht definierte Deckoberseite und falsche Evaluator-Timingannahmen.
- `failed_preflight_2.tar.gz`: der generische Self-Check akzeptierte das eingefrorene Schema `/2` noch nicht.
- `invalid_temporal_evaluation_2.tar.gz`: verbliebene Reaktions-/Zwischenphasenfehler im Replay.

Keine dieser Gruppen erhielt eine Result-Card oder Judges. `v2_original_2` ist der einzige gescorte Original-Run. Der Clarified-Repair blieb vor jeder Evaluation im selben isolierten Run.

## Provenienz

- Publisher-PDF SHA-256: `f15c85be6345ff0101d01059509bc07e4989896f4f1927ace4248bba4ce1e853`
- Klarstellung SHA-256: `03f295bb413faffb35fd313c20ee46d14aabbc1b40f66db2bc274bca3f6c6a89`
- Szenario-Suite SHA-256: `8a0c4acd4da77cd5f40e2bc2c59f2924f481a5fc565c19085f59428962ef5352`
- Adapter SHA-256: `ec9414df50150a6e570cb62021208854da210769471e3ab0fbff9c88df6cd14d`
- V4-Runner SHA-256: `002f9c000cba5993633c4af2fab10ced464603b0f16c6d16a251ae76f67f2aac`
- Original-Code SHA-256: `0bdb0e8d02565e0467e16b42bd5095836417e1f03d5ea4c7a8299f87f2ed9c7c`
- Clarified-Code SHA-256: `c71840ff7630ea6b10923897f435d127cc00db542a392a734edc770de8bf1415`

## Artefakte

- Maschinenprofile: `v2/original_result.json`, `v2/clarified_result.json`
- Befunde: `v2/original_findings.md`, `v2/clarified_findings.md`
- Kurzvergleich: `v2/COMPARISON.md`
- Erfolgreiche Lauf-, Check-, Szenario-, Judge- und Usage-Artefakte: `v2/raw/study_artifacts.tar.gz`
- Ungültige Vorläufer und Erläuterung: `v2/raw/FAILED_ATTEMPTS.md` plus die drei benannten Archive
- Aktive kanonische Clarified-Artefakte: `outputs/expl_codex_ag*`

Die ältere Exploding-Kittens-Präsentation wurde durch diese V2-Ansicht ersetzt und bleibt über Git nachvollziehbar.
