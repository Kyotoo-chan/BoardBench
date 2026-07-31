# Grober Schreibplan für die Bachelorarbeit

> Kurze Gedankenstütze. Beobachtungen in den Haupttext, Detailtabellen und Rohdaten in Anhang/Repository.

## 1. Einleitung

- Problem: Menschliche Brettspielregeln sind keine automatisch eindeutige, ausführbare Spezifikation.
- Leitfragen:
  1. Welche Probleme entstehen bei der Übersetzung eines Regelwerks in eine Spielumgebung?
  2. Welche Probleme verändern sich nach einer expliziten Klarstellung und frischen Generation?
  3. Wie zuverlässig lassen sich technische Qualität und Regeltreue messen?
- Beitrag: BoardBench-Workflow plus transparente Fallstudien.
- Abweichung vom Exposé offenlegen: Bekanntheit/Modellvergleich, OpenSpiel-Referenzvergleich und RL-Agent wurden nicht durchgeführt; Fokus wechselte zum diagnostischen Clarification-Workflow.

## 2. Hintergrund

- PaperBench als Inspiration für agentisches Nachbauen textueller Spezifikationen.
- Spielumgebungen/formale Schnittstellen, z. B. OpenSpiel.
- Natürliche Regeln vs. ausführbare Spezifikation vs. Testoracle.
- LLM-Codegenerierung: ausführbarer Code ist nicht automatisch regeltreu.
- Literatur aus `exposé/Bachelorarbeit_Exposé.pdf` übernehmen und um aktuelle Arbeiten ergänzen.

## 3. Methodik: BoardBench

### Quellen und Erwartungen

- Zugewiesene Publisher-Quellen; Begleitheft nur bei expliziter Delegation/passender Edition. Ein klar attribuierter Nutzer-Komponentenanhang darf nur Inventar/Setup stützen, nicht Spielregeln überschreiben.
- Kanonische PDFs plus vollständige 150-DPI-Seitenbilder, Hashes und Provenienz.
- Atomare Claims: `clear`, `ambiguous`, `missing`, `conflicting`, `untestable`.
- Zitat/Locator je harter Erwartung; Nutzerentscheidungen für digitale Lücken.
- Szenariomatrix, Claim-Mapping, Contract V2 und harte Spielerzahltests.

### Generierung und Intervention

- Blindes isoliertes Modellpaket; Evaluator und Ergebnisse bleiben unsichtbar.
- `gpt-5.6-sol`: Implementierung `low`, Judges `medium`; ein finaler Run je Bedingung.
- Reparaturen nur vor Evaluation; danach nur neue versionierte Nachfolger.
- Originalquellen bleiben byte-identisch. **Source-Gap-Clarification** entscheidet nur `ambiguous`/`missing`/`conflicting`; **Clear-/Setup-Emphasis** erhöht nur die Salienz bereits klarer Regeln. Beides getrennt auswerten.
- Keine Best-of-Auswahl; adaptierte Nachfolger sind keine Replikate.

### Getrennte Evaluation

1. Technik 01–04;
2. 100 Rollouts;
3. Interface/Action-Language;
4. Clear- und Human-Decision-Szenarien;
5. Claim-Mapping und evaluated coverage;
6. drei fallible neutrale Judges.

Historische Persona-Reviews nur ergänzend nennen; sie wurden nicht für alle V2-Bedingungen einheitlich erzeugt. Kein gemischter Correctness-Gesamtscore.

**Methodenquellen:** `AGENTS.md`, `WORKFLOW_EVALUATION_PLAN.md`, `docs/workflow_description.md`, `docs/methodology_audit_2026-07-25.md`, `inputs/prompts/`, `generation/`, `checks/`.

## 4. Studienaufbau und Workflow-Entwicklung

- Historische Piloten nur als Motivation: gemischte Scores und schwächere Isolation; nicht mit V2 aggregieren.
- V2-Härtung: atomare Claims, Contract, Spielerzahlen, Packet-Allowlist, Isolation, Evaluator-Freeze und getrennte Scores.
- Evaluatorfehler als eigener Befund: ungültige Replays ungescort archivieren; CATAN-Judges wegen fehlender Almanachbilder versioniert wiederholt.
- `docs/methodology_audit_2026-07-25.md` als damaligen Planungsstand kennzeichnen: Die dort ausgeschlossene CATAN-V2-Reihe wurde später bewusst doch versioniert durchgeführt; Git-Historie und neue Manifeste begründen die Ablösung.
- Spielauswahl/Komplexität begründen. Dominion bleibt ohne passende offizielle Begleitquelle pausiert.

## 5. Ergebnisse

Zuerst eine gemeinsame Tabelle; danach je Spiel nur Ziel, wichtigste Fehlergruppe, Intervention und Regression:

- **Wizard:** Klarstellung verbessert Zielbereich; Jester/Wizard-Randfall bleibt.
- **Abalone (Clear-Rule-Emphasis):** Setup repariert; anderer Human-Decision-Fall regressiert.
- **Exploding Kittens V2 (Source-Gap-Clarification):** Empty-Target-Ziel verbessert; neue Attack-Chain-Regression.
- **Bohnanza V2:** zwei Clear-Emphasis-Läufe schlechter; strukturierte Clarification verbessert Judge-Signal, aber nicht monoton den Szenariowert.
- **CATAN V2:** Clear-Emphasis ist stärkster Szenarionachfolger; getrennte Source-Gap-Clarification hat höchstes Judge-Signal, aber deutliche Clear-Regressionen.

Je Spiel Technik, Robustheit, Interface, Clear, Human Decision, Coverage und Judges getrennt zeigen. Zahlen aus `results/scores/<game>/README.md`, `DETAILS.md` und `v2/*COMPARISON.md` übernehmen.

## 6. Diskussion

- Fehlertypen unterscheiden:
  - publisher-klare Implementierungsfehler;
  - fehlende/mehrdeutige digitale Regeln;
  - Contract-/Repräsentationsfehler;
  - Evaluatorfehler;
  - Judge-/Szenario-Uneinigkeit.
- Hauptmuster: Klarstellungen können Zielverhalten treffen, garantieren aber keine global bessere Neugeneration.
- Mehr Salienz kann lokal helfen und gleichzeitig andere Bereiche verdrängen.
- Technische Stabilität beweist keine Regeltreue.
- Szenarien messen nur ihre konfigurierte Basis; Claim-Mapping ist keine vollständige Assertion-Abdeckung.
- Nur „in diesen Runs beobachtet“ schreiben, nicht kausal verallgemeinern.

## 7. Limitationen

- `n=1` je Bedingung; adaptierte Nachfolger statt Replikate.
- Ein Implementierungsmodell und Judges derselben Modellfamilie.
- Endliche manuelle Szenarien; Fixture-Erreichbarkeit nicht immer bewiesen.
- Nutzerentscheidungen sind digitale Ground Truth, keine Publisher-Regeln.
- Unterschiedliche Spielkomplexität und historische Workflow-Versionen.
- Bekanntheit, Cross-Model-Effekt und Varianz nicht gemessen.
- Evaluator und Judges sind selbst fehleranfällig.

## 8. Fazit und Ausblick

- BoardBench trennt Quellenlücken, Implementierungsfehler und Evaluationsprobleme.
- Aus Codefehlern allein keine schlechte Regelbuchqualität ableiten.
- Ausblick: weitere unberührte Spiele, Wiederholungen, andere Modelle/Judges, menschliche Doppelannotation und systematischere Coverage.

## Artefaktkarte / Anhang

- Quellen, Claims, Entscheidungen, Profile: `inputs/games/<game>/`.
- Szenarien/Adapter: `checks/scenarios/`, `checks/scenario_adapters/`.
- Prompts/Contract: `inputs/prompts/`.
- Code, Checks, Judges, Ergebnisse: `results/scores/<game>/`.
- Rohdaten/ungültige Versuche: jeweiliges `raw/`.
- Historische Piloten klar von V2 trennen.

## Sinnvolle Schreibreihenfolge

1. Einleitung, Hintergrund und Methodik jetzt schreiben.
2. Gemeinsame V2-Ergebnistabelle bauen.
3. Pro Spiel eine kurze Untersektion.
4. Diskussion entlang der Fehlertypen statt Wiederholung pro Spiel.
5. Limitationen fertigstellen und kausale Formulierungen prüfen.
