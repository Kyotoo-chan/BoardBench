# BoardBench

Minimaler Startpunkt für einen manuellen BoardBench-Workflow.

Ziel: Aus einer Spielanleitung (PDF oder Text) mit bestehenden Chat-Subscriptions ohne API-Keys einen ersten Python-Entwurf für eine Spielumgebung erzeugen und diesen später manuell mit einer OpenSpiel-Referenz vergleichen.

## Aktueller Scope

Dieser Stand ist bewusst klein:

- `inputs/` für Spielregeln
- `outputs/` für rohe Modellantworten und extrahierten Python-Code
- `prompts/` für wiederverwendbare Prompts
- `notebooks/compare_to_openspiel.ipynb` für die manuelle Gegenüberstellung
- `AGENTS.md` für allgemeine Coding-Agent-Regeln
- `QUESTIONS.txt` als append-only Fragen-/Problemlog

Noch **nicht** enthalten:

- API-Provider
- Agent-Hooks
- automatisierte Benchmarks
- komplexe Projektstruktur

## Empfohlener Minimal-Workflow

1. Lege eine Spielregel als PDF in `inputs/` ab.
   - Falls ein Modell kein PDF gut verarbeitet, nutze stattdessen eine Textdatei.
2. Öffne `prompts/system.md` und `prompts/game_to_python.md`.
3. Nutze eine bestehende Subscription (z. B. ChatGPT, Claude, Copilot Chat) manuell.
4. Hänge die PDF an oder füge den Regeltext ein.
5. Verwende den festen Systemprompt und den Task-Prompt.
6. Speichere die **komplette rohe Modellantwort** in `outputs/`.
7. Speichere den extrahierten Python-Code zusätzlich als eigene `.py`-Datei in `outputs/`.
8. Vergleiche den LLM-Output später im Notebook manuell mit einer OpenSpiel-Referenz.
9. Trage offene Fragen, Probleme und Unsicherheiten in `QUESTIONS.txt` ein.

## Dateibenennung

Einfach und wiedererkennbar halten, z. B.:

- `inputs/tic_tac_toe.pdf`
- `outputs/tic_tac_toe__gpt5__response.md`
- `outputs/tic_tac_toe__gpt5.py`
- `outputs/tic_tac_toe__openspiel_reference.py`

## Warum noch keine Agenten/Hooks?

Für den ersten Meilenstein wäre das mehr Komplexität als Nutzen.

Solange du ohne API-Keys arbeitest und primär mit bestehenden Subscriptions experimentierst, ist ein **manueller Ein-Prompt-Workflow** der schnellste und klarste Einstieg.

Agenten, Hooks oder mehrstufige Reparatur-Loops werden erst sinnvoll, wenn du später brauchst:

- echte Automatisierung
- systematische Prompt-Varianten
- mehrfache Iterationen pro Spiel
- strengere Kontrolle über Inputs und Outputs
- spätere Benchmark-Metriken wie Illegal-Move-Rate

## Reproduzierbarkeit

Damit der manuelle Workflow trotzdem vergleichbar bleibt:

- nutze dieselben Prompt-Dateien
- speichere immer die rohe Modellantwort
- halte Dateinamen konsistent
- dokumentiere Unklarheiten in `QUESTIONS.txt`
- ändere oder lösche Fragen/Probleme nicht automatisch

## Nächster sinnvoller Schritt

Wenn der manuelle Ablauf für ein Pilotspiel funktioniert, ist Phase 2 wahrscheinlich:

- kleiner Syntax-/Import-Check für generierten Code
- klarerer Vergleich mit einer OpenSpiel-Referenz
- optional API-basierter Provider-Zugang für reproduzierbarere Runs
