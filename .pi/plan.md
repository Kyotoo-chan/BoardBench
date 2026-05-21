# Plan: Minimaler manueller Workflow für BoardBench

## Status
Umgesetzt.

## Goal
Einen sehr schlanken ersten Workflow für ein Pilotspiel bereitstellen, der mit bestehenden Chat-Subscriptions ohne API-Keys funktioniert:

- 1 Input-Ordner für Spielregeln
- 1 Output-Ordner für rohe Modellantworten und extrahierten Python-Code
- 1 Notebook zur manuellen Gegenüberstellung mit einer OpenSpiel-Referenz
- 1 Prompt-Setup aus Systemprompt + Task-Prompt
- 1 append-only Datei für Fragen, Probleme und Unsicherheiten
- 1 `AGENTS.md` für allgemeine Coding-Agent-Regeln rund um das Repo

## Assumptions
- Das Repo bleibt im ersten Schritt minimal.
- Modellzugriff erfolgt zunächst manuell über bestehende Subscriptions.
- Der erste Generierungsversuch ist ein Ein-Prompt-Workflow von PDF/Text zu Python-Code.
- Es gibt noch keine API-Integration, keine Hooks und keine Automatisierung.
- Die Einschränkung „nur bereitgestellte Spielanleitung verwenden“ wird zunächst über Prompt-Disziplin gelöst.
- Für Vergleichbarkeit wird die rohe Modellantwort mitgespeichert.
- `QUESTIONS.txt` ist append-only und wird nicht automatisch bereinigt.
- `AGENTS.md` ist für Repo-Building-/Coding-Agenten gedacht, nicht für spätere Spiel-/Benchmark-Agenten.

## Open questions
Keine offenen Implementierungsfragen für diesen Stand.
Fachliche Forschungsfragen werden in `QUESTIONS.txt` gesammelt.

## Affected files
Erstellt oder geändert:

- `README.md`
- `AGENTS.md`
- `QUESTIONS.txt`
- `prompts/system.md`
- `prompts/game_to_python.md`
- `notebooks/compare_to_openspiel.ipynb`
- `inputs/.gitkeep`
- `outputs/.gitkeep`
- `.pi/plan.md`

## Step-by-step changes
1. Repo auf die Minimalstruktur reduziert und dokumentiert.
2. `README.md` auf den manuellen Subscription-Workflow umgestellt.
3. `AGENTS.md` im Repo-Root für allgemeine Coding-Agent-Regeln angelegt.
4. `QUESTIONS.txt` als append-only Fragen-/Problemlog angelegt.
5. `prompts/system.md` für allgemeine Modellregeln angelegt.
6. `prompts/game_to_python.md` als wiederverwendbaren Task-Prompt angelegt.
7. `inputs/` und `outputs/` als minimale Arbeitsordner vorbereitet.
8. `notebooks/compare_to_openspiel.ipynb` als manuelle Vergleichsvorlage angelegt.
9. Plan-Datei auf den tatsächlich umgesetzten Stand aktualisiert.

## Validation steps
- Dateistruktur geprüft: `inputs/`, `outputs/`, `prompts/`, `notebooks/` vorhanden.
- Zentrale Dateien geprüft: `README.md`, `AGENTS.md`, `QUESTIONS.txt`, Prompt-Dateien vorhanden.
- Notebook-Datei syntaktisch geprüft: JSON erfolgreich geladen.
- Workflow bleibt ohne API-Key und ohne zusätzliche Agenten-Infrastruktur nutzbar.

## Risks
- Manuelle Subscription-Nutzung bleibt nur eingeschränkt reproduzierbar.
- Prompt-Disziplin ist keine harte technische Isolation.
- Direkte Generierung von PDF/Text zu Python-Code in einem Schritt bleibt fragil.
- PDF-Unterstützung hängt vom jeweiligen Subscription-Produkt ab.
- Ohne automatische Checks können fehlerhafte Outputs leicht im `outputs/`-Ordner landen.
- Der OpenSpiel-Vergleich ist zunächst nur manuell/qualitativ.

## Deviations
- Zusätzlich zu den geplanten Ordnern wurden `inputs/.gitkeep` und `outputs/.gitkeep` angelegt, damit die leeren Arbeitsordner im Repository erhalten bleiben.
- Das Notebook ist eine Vergleichsvorlage; eine konkrete OpenSpiel-Referenzdatei wurde noch nicht hinzugefügt, weil noch kein Pilotspiel ausgewählt wurde.