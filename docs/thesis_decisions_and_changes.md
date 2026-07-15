# BoardBench: Entscheidungen, Änderungen und Begründungen

> **Datum:** 12.07.2026  
> **Zweck:** Nachvollziehbarer Bericht darüber, was nach der Auswertung von Exposé, Meeting-Notizen und Repository geändert wurde und warum.

## 1. Warum diese Bachelorarbeit gemacht wird

Brettspielregeln sind ein geeigneter Testfall für die Übersetzung natürlicher Sprache in ausführbare Spezifikationen. Menschen können fehlende Details am Tisch aushandeln. Ein Programm muss dagegen für jeden erreichbaren Zustand entscheiden können:

- wer handelt,
- welche Aktionen legal sind,
- wie eine Aktion den Zustand verändert,
- was öffentlich oder privat ist,
- wann das Spiel endet,
- und welche Returns beziehungsweise Gewinner daraus folgen.

Genau an dieser Grenze zwischen alltagstauglicher Sprache und formaler Ausführbarkeit liegt der wissenschaftliche Wert der Arbeit. Ein LLM kann aus dem Regelwerk Code erzeugen und zwingt dadurch implizite Annahmen an die Oberfläche. Der erzeugte Code ist deshalb nicht nur ein Softwareartefakt, sondern ein **operationalisiertes Verständnis des Regeltexts**.

Die Arbeit darf daraus jedoch nicht vorschnell folgern, dass jeder Codefehler eine schlechte Anleitung beweist. Ein Fehler kann mindestens vier Ursachen haben:

1. der Regeltext ist tatsächlich unklar oder unvollständig,
2. Bilder, Edition oder Kontext wurden falsch übertragen,
3. das Generator-Modell versteht eine klare Regel falsch,
4. die Evaluation beziehungsweise der Mensch interpretiert die Regel falsch.

BoardBench wird wissenschaftlich interessant, wenn es diese Ursachen nicht versteckt, sondern systematisch trennt.

## 2. Was „PaperBench für Brettspielanleitungen“ konkret bedeutet

PaperBench lässt Agenten wissenschaftliche Arbeiten aus eigener Kraft replizieren. Der entscheidende methodische Punkt ist nicht nur der Agentenlauf, sondern die hierarchische Zerlegung in einzeln bewertbare Rubriken. Die Rubriken wurden mit Autoren abgestimmt; zusätzlich wurde der automatische Judge selbst evaluiert.

Die passende Übertragung lautet:

| PaperBench | BoardBench |
|---|---|
| wissenschaftliches Paper | Brettspielregelwerk einer festen Edition |
| Replikations-Code und Experimente | selbstständige Python-Spielumgebung |
| hierarchische Rubrik | atomare Regelfakten und ausführbare Szenarien |
| Paper-Autoren validieren Kriterien | Regelzitate, offizielle Errata, Autoren/Verlag oder fachliche Adjudikation |
| LLM-Judge gegen Judge-Benchmark | Cross-Judges plus Fehler-Goldset und menschliche Kontrolle |

Eine bloße Sammlung generischer Smoke-Tests wäre daher noch kein PaperBench-artiger Benchmark. Der zentrale fehlende Baustein sind **task-spezifische, quellengebundene Bewertungskriterien**.

## 3. Wichtigste Diagnose des bisherigen Repositories

### 3.1 Stärken

- Der Weg von PDF/Text zu Rohantwort und Python-Artefakt ist reproduzierbar dokumentiert.
- One-shot und agentische Generierung sind praktisch durchführbar.
- Rohantworten, Check-Logs, Judges, Laufzeiten und historische Runs bleiben erhalten.
- Cross-Judges und Blind-Mismatch-Tests sind bereits vorhanden.
- OpenSpiel-Lockstep funktioniert bei hinreichend gleicher Modellierung.
- Git-Historie wird sinnvoll als Experimenttagebuch genutzt.

Diese Infrastruktur soll erhalten bleiben. Eine große neue Plattform oder Provider-Abstraktion wäre für die Bachelorarbeit unnötig.

### 3.2 Zentrale Schwäche

Die vorhandenen numerischen Ergebnisse messen überwiegend, ob ein Environment **läuft**, nicht ob es das Regelwerk **richtig abbildet**. Gleichzeitig wurden diese Messgrößen zu einem Gesamtscore kombiniert. Dadurch sahen insbesondere komplexe Spiele besser aus, als die Judge-Befunde rechtfertigen.

Beispiel CATAN:

- 05 Random Rollouts: überall `1.000`,
- 06 Action Language: überall `1.000`,
- LLM-Judges: nur `0.410–0.670`,
- alter aggregierter Plot: trotzdem `0.826–0.903`.

Der hohe Wert war mathematisch erwartbar, aber semantisch missverständlich. Bei perfekten technischen und Interface-Werten ergab selbst ein Judge-Score von `0.0` noch `0.706`. Das Problem war daher nicht primär die konkrete Wahl `1` gegen `10`, sondern das Vermischen verschiedener Konstrukte.

Eine zusätzliche Prüfung aller zwölf historischen CATAN-Reviews (sechs Implementierungen × zwei Judges) bestätigt, dass dies kein rein kosmetisches Scoringproblem war:

- Scores lagen nur zwischen `0.40` und `0.68`;
- jeder Review meldete drei bis fünf große Probleme, zwei Reviews sogar ein kritisches Problem;
- wiederkehrend waren ein erfundenes/abstraktes statt des abgebildeten Spielplans, fehlender Spielerhandel, fehlende Häfen, unvollständige Entwicklungskarten, automatisches statt wählbares Abwerfen bei einer Sieben und vereinfachte Zufalls-/Auflösungslogik;
- selbst die stärkeren Claude-Varianten ließen zentrale Handels-, Abwurf- und Fortschrittskartenregeln nur vereinfacht oder wirkungslos.

CATAN ist damit **technisch robust, aber regelinhaltlich stark abstrahiert**. Es eignet sich als Stressfall und als Beleg für die Schwäche generischer Checks, nicht als hoch bewerteter Benchmark-Erfolg.

### 3.3 Verteilung der Pilotwerte

Über die gepinnten Pilotdaten zeigen 05 und 06 starke Deckeneffekte:

- Abalone, Mahjong, CATAN und Conect: 05 und 06 durchgehend `1.000`,
- Exploding Kittens: bis auf einen Pi-One-shot-Lauf fast vollständig `1.000`,
- Havannah: starke Varianz wird hauptsächlich durch einen fehlgeschlagenen Pi-One-shot-Lauf verursacht,
- Judge-Werte differenzieren deutlich stärker und liegen bei Mahjong, CATAN und Conect im Mittel nur ungefähr zwischen `0.49` und `0.56`.

Damit eignen sich 05/06 als Gate-, Robustheits- und Schnittstellenindikatoren. Sie eignen sich nicht als dominierende Qualitätsmetrik. Aus je einem Lauf pro Zelle lässt sich außerdem keine belastbare Streuung des Generators schätzen.

### 3.4 Conect als konkreter Regelwerk-Unklarheitsfall

Die Conect-Anleitung beschreibt Zugfolge und drei Siegbedingungen, zeigt aber mehrere Geometrien (gewöhnliches Erklärbrett, breiter und schmaler Kegel sowie Projektionen), ohne im Fließtext eine einzige verbindliche Brettgröße für die Implementierung festzulegen. Genau hier divergieren die vier historischen Implementierungen:

- Pi One-shot modelliert 21 spielbare Zellen,
- Pi Agentic und Codex One-shot modellieren 37 Zellen,
- die Benennung von Zentrum, Apex, Naht und geteilten Randzellen unterscheidet sich ebenfalls.

Das ist nicht automatisch ein Modellfehler. Es ist ein **zu adjudizierender Spezifikationspunkt**: Soll Figure 1 nur die Regeln erklären, ist die Brettgröße parametrisierbar, oder ist eine konkrete Projektion gemeint? Deshalb behauptet die neue Conect-Suite absichtlich keine Soll-Zellenzahl. Sie prüft zunächst nur textlich eindeutige Fakten (leeres Brett, Rot beginnt, abwechselnd genau ein freies Feld). Dieser Fall illustriert direkt das Exposé-Ziel: Codegeneration macht eine zuvor leicht überlesene Spezifikationslücke sichtbar.

## 4. Durchgeführte Code- und Workflowänderungen

### 4.1 Score-Dimensionen getrennt, Plot-Redesign vertagt

**Entscheidung:** Technical Gate, Robustheit, Interface, Regelszenarien, Judge und OpenSpiel werden methodisch getrennt interpretiert. Die vorhandenen Pilotplots wurden jedoch wiederhergestellt und bleiben vorläufig historische Darstellungen.

**Warum:** Die inhaltliche Abstraktion ist richtig, aber die beste einfache Visualisierung ist noch offen. Zuerst wird der agentische Workflow stabilisiert; danach kann die Darstellung anhand der tatsächlich finalen Evidenzgruppen gestaltet werden. Alte Gesamtwerte dürfen bis dahin nicht als Regeltreue interpretiert werden.

### 4.2 Korrektur zukünftiger Summary-Berechnung

**Datei:** `generation/run_pilot_checks.py`

**Änderung:** Die Funktion zur Aktualisierung von Check-Logs berechnet die Base-Phase nun aus den tatsächlichen Zeilen 01–06. Vorher wurde die Base-Phase unabhängig von 05/06 als `1.000` behandelt und der Endscore berücksichtigte im Wesentlichen Smoke, Judge und OpenSpiel.

**Warum:** Auch wenn der aggregierte Score nicht mehr die Thesis-Hauptmetrik ist, müssen gespeicherte Logs rechnerisch korrekt bleiben. Alte Logs werden nicht still umgeschrieben; die Korrektur gilt für künftige Aktualisierungen.

### 4.3 Schutz vor Logikänderung durch Action-Language-Align

**Dateien:**

- `checks/align_guard.py`
- `evaluation.ipynb`

**Änderung:** Vor und nach dem Align werden mehrere seed-basierte Trajektorien verglichen. Der Guard ignoriert absichtlich die Aktionsnamen, vergleicht aber aktuelle Spieler, Terminalität, rohe legale Aktionen, Returns und Render-Ausgabe. Bei einer Abweichung wird das Pre-Align-Backup wiederhergestellt und der Schritt bricht ab.

**Warum:** Align soll nur eine Vergleichssprache herstellen. Wenn dabei Legalität oder State-Transition verändert wird, wäre der anschließende OpenSpiel-/Pair-Vergleich keine Bewertung des ursprünglich generierten Artefakts mehr.

**Grenze:** Sampling beweist keine vollständige Äquivalenz. Es ist ein starker Schutz gegen beobachtbare Änderungen, kein formaler Beweis.

Zusätzlich akzeptiert `checks/action_normalizer.py` nun die bereits erzeugte Koordinatenform `q_z0:r_n7`. Dadurch werden semantisch gleiche Havannah-Koordinaten des Codex-One-shot-Laufs nicht mehr nur wegen des Doppelpunkts getrennt behandelt.

### 4.4 Erster regelbuchgebundener Szenario-Layer

**Dateien:**

- `checks/run_scenarios.py`
- `checks/scenarios/havannah.json`
- `prompts/rulebook_to_scenarios.md`

**Änderung:** Ein kleiner Standardbibliothek-Runner führt Black-box-Szenarien ausschließlich über die öffentliche BoardBench-API aus. Jede Erwartung muss an eine Rulebook-Datei mit SHA-256, eine Seite und ein direktes Zitat gebunden sein. Der Havannah-Prototyp prüft:

1. leeres Brett, Startspieler und 169 freie Punkte,
2. Platzierung auf einem freien Punkt,
3. Spielerwechsel und sinkende Zahl legaler Punkte über zwei Züge,
4. eine vollständige, regelzitierte Brücken-Sequenz zwischen zwei Eckpunkten,
5. einen kleinstmöglichen Ring um einen Punkt; beide Siegpfade prüfen Terminalität und Returns.

**Warum:** Das ist der erste konkrete Schritt von generischer Robustheit zu PaperBench-artigen, task-spezifischen Kriterien. Hash und Zitat verhindern, dass ein Test unbemerkt für eine andere Edition als „Wahrheit“ weiterverwendet wird.

**Validierung:** Der Runner wurde gegen alle sechs historischen Havannah-Pilotimplementierungen (drei Backends × zwei Varianten) ausgeführt; alle bestanden `5/5`. Das zeigt, dass Setup, Grundfluss, Brücke und Ring implementierungsübergreifend prüfbar sind.

Für Conect wurde als zweites Spiel ohne OpenSpiel eine kleine Suite ergänzt. Sie prüft drei eindeutig textbelegte Grundfakten, ohne die im Regelwerk nicht eindeutig festgelegte Brettgröße vorwegzunehmen. Alle vier historischen Conect-Implementierungen bestehen `3/3`.

**Grenze:** Die Suiten sind weiterhin ein Infrastrukturprototyp. Wissenschaftlich entscheidend sind als Nächstes Havannah-Gabel-/Negativfälle sowie adjudizierte Conect-Siegpfade. Die Kandidaten müssen unabhängig validiert werden.

### 4.5 Strengerer Judge-Prompt

**Datei:** `prompts/llm_judge_review.md`

**Änderung:** Kritische und große Findings benötigen jetzt ein genaues Regelzitat mit Seite sowie die widersprechende Code-Stelle beziehungsweise Transition. Eine aus dem Packet nicht entscheidbare Frage muss `question` bleiben. Critical/Major/Minor wurden inhaltlich definiert.

**Warum:** Die korrigierten EK-Interpretationen zeigen, dass auch Evaluatoren plausible, aber falsche Regeln annehmen können. Ein Judge soll Unsicherheit sichtbar machen, nicht durch selbstbewusste Sprache in vermeintliche Ground Truth verwandeln.

### 4.6 Schutz gegen falsche Rulebook-Bilder

**Datei:** `generation/config.py`

**Änderung:** Beim Aktivieren eines Spiels wird der bisherige Render-Ordner für `game_rules.pdf` gelöscht. Die aktuell vorhandenen Havannah-Seiten gehörten nicht zum aktiven Exploding-Kittens-PDF und wurden entfernt.

**Warum:** Alle aktiven PDFs heißen `game_rules.pdf`. Ohne Invalidierung kann der gemeinsame Ordner `inputs/rulebook_pages/game_rules/` Seiten des vorherigen Spiels enthalten. Das ist ein P0-Datenfehler, weil Generator und Judge dann möglicherweise verschiedene Regelquellen sehen.

### 4.7 Minimale Bereinigung

**Entfernt:**

- `inputs/games/conect/Conect_rules.pdf` — bitidentische Dublette von `inputs/games/conect/game_rules.pdf`,
- temporäre Exposé-Textextraktion,
- veraltete Rulebook-Renderbilder.

**Bewusst behalten:**

- Meeting-Notizen und `QUESTIONS.txt` als Forschungs-/Entscheidungsprotokoll,
- historische Problem- und Workflowdokumente,
- Rohantworten und aktuelle GLM-Artefakte,
- manuelles EK-Notebook,
- Provider-/Rerun-Skripte, solange sie historische Experimente reproduzierbar machen,
- unterschiedliche CATAN-PDFs, weil sie nicht bitidentisch sind und ohne Editionsprüfung nicht als Dublette gelten.

**Warum:** Minimalismus bedeutet hier nicht, Evidenz zu löschen. Entfernt wurden nur nachweislich falsche, temporäre oder bitidentische Dateien.

### 4.8 Agentischer Skill-Workflow und niedrige Default-Reasoning-Stufe

Neue BoardBench-Läufe werden nicht mehr als One-shot-vs.-Agentic-Paar geplant. Die One-shot-Artefakte bleiben Pilotdaten; der neue Hauptpfad ist agentisch und wird über projektlokale pi-Skills gesteuert:

- `bb` für Status und Routing,
- `bbedge` für zitierte Regelfakten und gemeinsame Edge-Case-Entscheidungen,
- `bbimpl` für eine isolierte Agentenimplementierung,
- `bbeval` für getrennte Evidenzgruppen.

`npm:@tintinweb/pi-subagents` wurde im Benutzerprofil installiert und ersetzt das zunächst getestete andere Subagent-Paket. BoardBench definiert vier projektlokale Rollen ohne fest gepinntes Modell oder Thinking. Der Parent entscheidet standardmäßig; ohne explizite Nutzerwahl darf ein Child nur gleich stark oder nachweislich schwächer sein. Modell und Thinking bleiben über `submodel` und `subthinking` explizit steuerbar. Ein globaler `gc`-Skill kapselt die gewünschte Solo-/Team-Git-Policy ohne Co-Author-Trailer.

`AGENTS.md` und die Kernprompts wurden gekürzt. Die alte projektspezifische Restriktions-Extension, der alte Cursor-Skill, `evaluation2.ipynb`, Pair-Compare, das manuelle EK-Notebook und die nur für die lokale Claude-NPM-Installation benötigten Package-Dateien wurden entfernt. Git-Historie erhält die Pilotartefakte.

**Reasoning-Entscheidung:** Gute Skills reduzieren Suchraum und Widersprüche, ersetzen aber keine schwierige Regelinterpretation. `low` ist deshalb ein sinnvoller Kosten-/Geschwindigkeitsdefault. Eskaliert wird nur bei konkreten Konflikten, unklaren Terminal-/Chance-Regeln oder wiederholtem Scheitern; die Eskalation wird als eigene Versuchsbedingung dokumentiert.

## 5. Warum RL nicht als nächstes implementiert wurde

Die Meeting-Idee, Aktionen über Erwartungswert und Varianz ihrer Resultate zu bewerten, untersucht primär Spielstärke und Balance. Eine laut Regelwerk korrekte Aktion darf extrem stark sein; eine falsch implementierte Aktion kann statistisch unauffällig bleiben. Ein RL-Agent besitzt daher kein unabhängiges Regel-Orakel.

RL kann später nützlich sein, um:

- Exploits und Endlosschleifen zu finden,
- seltene Zustände zu erreichen,
- starke Unterschiede zwischen Implementierungen aufzudecken.

Vorher müssen aber Invarianten und Regelszenarien existieren, gegen die ein gefundener Zustand geprüft werden kann. Deshalb ist die Reihenfolge **Szenario-Orakel → coverage-guided Exploration → optional RL** methodisch sauberer und für eine Bachelorarbeit realistischer.

## 6. Was im Repo sinnvoll beziehungsweise unnötig ist

### Sinnvoll für die Abschlussarbeit

- `inputs/games/`: versionierte Quellregelwerke,
- `prompts/`: reproduzierbare Rollen und Bedingungen,
- `outputs/` plus Git-Historie: Rohartefakte und Experimentbelege,
- `checks/`: kleine ausführbare Evaluationsschichten,
- `results/scores/`: gepinnte, von `outputs/` entkoppelte Ergebnisdaten,
- `results/plots/`: ausschließlich erzeugte Abbildungen,
- `evaluation.ipynb`: transparenter agentischer Manual-Fallback,
- Meeting- und Entscheidungsdokumente: Nachweis, wie Methodik entstanden ist.

### Nicht zum Kern aufblasen

- generischer Rulebook-Scraping-Dienst,
- großer RL-Stack,
- universeller Action-Normalizer für alle Spiele,
- Provider-Framework oder API-Key-Batchplattform,
- möglichst viele Spiele ohne tiefe Rubriken,
- Game-Balance als Ersatzmetrik für Regeltreue,
- Pair-Compare als Ground Truth.

### Historie und kanonische Dokumente

Veraltete Problemchecklisten, Provider-Anleitungen und One-shot-Workflowdateien wurden aus dem Working Tree entfernt; ihre Entstehungsgeschichte bleibt in Git. Kanonisch sind jetzt:

1. `docs/projektgespraech_offene_fragen_und_weiterarbeit.md`,
2. dieses Änderungsdokument,
3. die tatsächlichen Checks/Prompts,
4. später ein eingefrorenes Hauptstudienprotokoll.

## 7. Wissenschaftlich sinnvolle nächste Untersuchung

Ein gutes nächstes Experiment ist kein weiterer unkontrollierter Spielelauf, sondern ein **Evaluator-Sensitivitätstest**:

1. Für zwei Spiele je 10–20 validierte Regelfakten festlegen.
2. Aus korrekten Pilotimplementierungen gezielt Mutanten erzeugen: falscher Startspieler, belegtes Feld erneut legal, falsches Spielende, falsche Returns, fehlender Zufall, Hidden-Information-Leak.
3. Mechanische Checks, Szenarien, Judge und OpenSpiel jeweils blind darauf anwenden.
4. Pro Evaluationsschicht berichten: Treffer, Fehlalarm, nicht entscheidbar.

Damit wird erstmals messbar, ob BoardBench die Fehler erkennt, die es zu erkennen behauptet. Das entspricht der PaperBench-Idee besser als eine bloße Rangliste von Modellen.

## 8. Technische Validierung dieser Änderung

Ausgeführt im Conda-Environment `boardbench`:

- Python-Compilecheck für `checks/` und `generation/`,
- JSON- und Python-Syntaxvalidierung des verbleibenden agentischen Notebooks,
- temporärer Dimensionsplot-Prototyp geprüft und anschließend zugunsten der Workflow-Priorität zurückgestellt,
- Havannah-Szenarios gegen alle sechs historischen Implementierungen: jeweils `5/5`,
- Conect-Grundszenarios gegen alle vier historischen Implementierungen: jeweils `3/3`,
- Align-Guard gegen eine unveränderte historische Implementierung,
- Positiv-/Negativprobe: reine Umbenennung akzeptiert, geänderte Transition erkannt,
- synthetische Prüfung der korrigierten Summary-Berechnung,
- inhaltliche Quersichtung aller zwölf historischen CATAN-Judge-Reviews,
- statische Validierung aller vier projektlokalen Skills und des globalen `gc`-Skills,
- Prüfung der Tintinweb-Subagent-Konfiguration, projektlokalen Agent-Frontmatter und Parent/Child-Cap-Regeln,
- Compilecheck und CLI-Hilfe des aktualisierten agentischen pi-Runners,
- `git diff --check`.

Es wurde bewusst **keine vollständige LLM-Generation oder Full-Evaluation** gestartet; bestehende Experimentartefakte wurden nicht neu bewertet oder überschrieben. Ein Live-Miniprompt zur Skill-Discovery konnte wegen des aktuell erreichten OpenAI-Codex-Nutzungslimits nicht abgeschlossen werden; die lokale Discovery-Struktur und Frontmatter wurden statisch validiert.

## 9. Offene Entscheidungen und aktueller Projektstand

Gemeinsam mit dem Betreuer zu klären sind:

- Ist die Hauptfrage primär Regelwerkdiagnose oder Agentenvergleich?
- Wie viele Wiederholungen sind budgetär realistisch?
- Welche zwei bis vier Spiele bilden die konfirmatorische Hauptstudie?
- Wer validiert die Regelfakt-Rubrik bei strittigen Regeln?
- Welche formalen Regeln gelten für die Offenlegung der KI-Nutzung?

Der aktuelle Stand lässt sich knapp so beschreiben:

> **Der Workflow ist als Pilot funktionsfähig. Die Arbeit befindet sich jetzt am Übergang von „Code läuft“ zu „Regelkorrektheit ist quellengebunden messbar“. Breite Generierung ist vorerst weniger wichtig als die Validierung des Evaluators und das Einfrieren eines kleinen, kontrollierten Hauptversuchs.**
