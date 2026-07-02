# BoardBench — offene Probleme & Selbst-Evaluations-Checkliste

> **Zweck:** Diese Datei ist eine **Arbeitsgrundlage für die Bachelorarbeit**, keine fertige Wahrheit.
> Gehe Abschnitt für Abschnitt durch, markiere selbst was zutrifft, und notiere Belege aus `outputs/`, Commits oder dem Code.
>
> **Stand:** Repo nach Exploding-Kittens-Lauf (`081e3e0`), Abalone/Havannah in der Git-Historie.
>
> **Konsolidierte Analyse (Lesen zuerst):** [`../PROBLEME.md`](../PROBLEME.md) — Projektidee, drei Pilotspiele, Fixbarkeit, Prioritäten.
>
> **Wie benutzen:** Diese Datei ist die **detaillierte Selbst-Evaluations-Checkliste**. Pro Punkt die Checkboxen ausfüllen. Bei „Trifft zu“ idealerweise ein konkretes Artefakt verlinken (`outputs/...`, Judge-Zeile, Check-Log).

---

## Inhaltsverzeichnis

1. [Projektreife & Scope](#1-projektreife--scope)
2. [LLM-Abhängigkeit (Generation, Judge, Align)](#2-llm-abhängigkeit-generation-judge-align)
3. [Regelwerk als Input](#3-regelwerk-als-input)
4. [Was die mechanischen Checks wirklich messen](#4-was-die-mechanischen-checks-wirklich-messen)
5. [Was die Checks **nicht** messen](#5-was-die-checks-nicht-messen)
6. [LLM-Judge vs. deterministische Checks](#6-llm-judge-vs-deterministische-checks)
7. [Logikfehler findbar machen](#7-logikfehler-findbar-machen)
8. [Testabdeckung & Sampling](#8-testabdeckung--sampling)
9. [Action-Language, Normalisierung, Vergleich](#9-action-language-normalisierung-vergleich)
10. [Oneshot vs. Agentic](#10-oneshot-vs-agentic)
11. [OpenSpiel-Referenz & Spiele ohne Referenz](#11-openspiel-referenz--spiele-ohne-referenz)
12. [Scoring, Gewichtung, Interpretation](#12-scoring-gewichtung-interpretation)
13. [Workflow, Reproduzierbarkeit, Artefakte](#13-workflow-reproduzierbarkeit-artefakte)
14. [Thesis-Forschungsfragen & Designentscheidungen](#14-thesis-forschungsfragen--designentscheidungen)
15. [Konkrete Beispiele aus bisherigen Läufen](#15-konkrete-beispiele-aus-bisherigen-läufen)
16. [Master-Checkliste (kurz, zum Abhaken)](#16-master-checkliste-kurz-zum-abhaken)

---

## Legende für jede Selbst-Evaluation

| Feld | Bedeutung |
|------|-----------|
| **Trifft zu?** | `ja` / `nein` / `teilweise` / `unklar` |
| **Schwere für Thesis** | `blockierend` / `wichtig` / `mittel` / `niedrig` / `nur Diskussion` |
| **Beleg** | Datei, Commit, Log-Zeile, eigene Notiz |
| **Was tun?** | ignorieren / dokumentieren / Prompt ändern / Check bauen / manuell prüfen |

---

## 1. Projektreife & Scope

### 1.1 Der Repo-Fokus ist noch „Experiment vorbereiten“, nicht „fertiger Benchmark“

**Kurz:** `AGENTS.md` sagt explizit: aktuell Repo-Bau und Experiment-Vorbereitung, noch kein automatisierter Benchmark.

**Im Repo heute:** Kleine `checks/`, manuelle Notebooks, keine CI-Pipeline, keine Spiel-Datenbank.

**Selbst-Evaluation:**
- [ ] Trifft zu? ___
- [ ] Schwere: ___
- [ ] Beleg: `AGENTS.md` Purpose-Abschnitt
- [ ] Was tun? ___

---

### 1.2 Es gibt noch keine feste „Tier-B“-Rubrik mit ausführbaren Regel-Asserts pro Spiel

**Kurz:** `docs/boardbench_checkliste.md` beschreibt Rubriken/Szenarien als Ziel; `TODO.md` sagt: erst Code + Checks verstehen, **dann** Szenario-Checks.

**Im Repo heute:** Nur generische Checks 01–06, kein `07_scenario_*.py`.

**Selbst-Evaluation:**
- [ ] Trifft zu? ___
- [ ] Schwere: ___
- [ ] Beleg: `TODO.md`, `evaluation_draft.md` §19
- [ ] Was tun? ___

---

### 1.3 Die Evaluation ist bewusst „manual-first“ (pi/Notebook), nicht API-key-batch

**Kurz:** Hard rule: keine stillen API-Workflows; Subscription/manuell.

**Im Repo heute:** `evaluation.ipynb` ruft `pi` per Subprocess; Laufzeiten variieren stark (Judge ~130s).

**Selbst-Evaluation:**
- [ ] Trifft zu? ___
- [ ] Schwere: ___
- [ ] Beleg: `AGENTS.md` Hard rules #2
- [ ] Was tun? ___

---

### 1.4 PaperBench-Inspiration ist Richtung, noch kein umgesetztes Rubrik-System

**Kurz:** `evaluation_draft.md` ist ein **breiter Ideenpool** (100+ Seiten Kandidaten), nicht die finale Spec.

**Selbst-Evaluation:**
- [ ] Trifft zu? ___
- [ ] Schwere: ___
- [ ] Beleg: `docs/evaluation_draft.md` §26
- [ ] Was tun? ___

---

### 1.5 „Ein Harness, zwei Orakel“ (OpenSpiel vs. Rubrik) ist konzeptionell, nicht voll implementiert

**Kurz:** `boardbench_checkliste.md` §1: Tier A/B als austauschbare Orakel — im Code nur Ansätze (99, Judge, fehlende Rubrik).

**Selbst-Evaluation:**
- [ ] Trifft zu? ___
- [ ] Schwere: ___
- [ ] Beleg: `docs/boardbench_checkliste.md`
- [ ] Was tun? ___

---

## 2. LLM-Abhängigkeit (Generation, Judge, Align)

### 2.1 Die **Spielimplementierung selbst** ist vollständig LLM-generiert

**Kurz:** Ohne LLM gibt es kein `outputs/<game>.py` — das ist der Kern-Artefakt.

**Risiko:** Jeder Lauf ist anders; Vergleiche über Modelle/Prompts/Spiele sind schwer ohne feste Seeds/Versionierung.

**Selbst-Evaluation:**
- [ ] Trifft zu? ___
- [ ] Schwere: ___
- [ ] Beleg: `prompts/rulebook_to_python.txt`, `outputs/exploding_kittens_*.py`
- [ ] Was tun? ___

---

### 2.2 Der **LLM-Judge** ist ein weiterer LLM-Schritt mit eigener Fehlerquote

**Kurz:** `90_llm_judge` parst nur `score:` + `confidence` — **nicht** `critical_issues` mechanisch.

**Risiko:** Judge kann halluzinieren, Severity falsch zählen, Runtime-Bugs übersehen.

**Selbst-Evaluation:**
- [ ] Trifft zu? ___
- [ ] Schwere: ___
- [ ] Beleg: `checks/90_llm_judge.py`, `docs/llm_judge_workflow.md` Limits
- [ ] Was tun? ___

---

### 2.3 **Action-Language-Align** (single + pair) ist wieder ein LLM-Schritt

**Kurz:** Vor OpenSpiel- oder Pair-Compare wird `action_to_name` / `name_to_action` per LLM umgeschrieben.

**Risiko:** Align kann Regellogik ändern (verboten im Prompt, aber nicht mechanisch erzwungen); Align kann scheitern ohne die eigentliche Semantik zu vereinheitlichen.

**Selbst-Evaluation:**
- [ ] Trifft zu? ___
- [ ] Schwere: ___
- [ ] Beleg: `prompts/action_language_pair_align.md`, `outputs/*_pre_align.py`
- [ ] Was tun? ___

---

### 2.4 Es gibt **keinen** mechanischen Guard „legal_actions vor/nach Align unverändert“

**Kurz:** Backups `*_pre_align.py` existieren, aber kein automatischer Diff der Action-Mengen.

**Selbst-Evaluation:**
- [ ] Trifft zu? ___
- [ ] Schwere: ___
- [ ] Beleg: `evaluation.ipynb` `run_pair_action_language_align`
- [ ] Was tun? Check-Idee: Sample-Zustände, `len(legal_actions)` + Hash der Action-Typen vergleichen

---

### 2.5 Agentic Generation läuft in **isoliertem Workspace ohne `checks/`**

**Kurz:** Generator sieht die Benchmark-Checks nicht — gut gegen Overfitting, schlecht für gezielte Fixes.

**Selbst-Evaluation:**
- [ ] Trifft zu? ___
- [ ] Schwere: ___
- [ ] Beleg: `docs/workflow_description.md`
- [ ] Was tun? ___

---

### 2.6 Modellwahl, Timeout und Prompt-Stack sind **experimentelle Parameter**, keine Konstanten

**Kurz:** `LLM_MODEL`, `USE_OPEN_SPIEL_BACKBONE`, Implementation Brief, PDF vs. Text — alles beeinflusst Output.

**Selbst-Evaluation:**
- [ ] Trifft zu? ___
- [ ] Schwere: ___
- [ ] Beleg: Setup-Zelle in `evaluation.ipynb`
- [ ] Was tun? Pro Run in Artefakten festhalten (teilweise schon in Judge-Packet)

---

### 2.7 „Es hängt am LLM Output“ (Prof-Meeting) ist strukturell korrekt

**Kurz:** `meeting/2.7/QUESTIONS.txt` — Pipeline-Ergebnis = Qualität des generierten Moduls + nachgelagerter LLM-Schritte.

**Selbst-Evaluation:**
- [ ] Trifft zu? ___
- [ ] Schwere: ___
- [ ] Beleg: `QUESTIONS.txt` Zeile 1
- [ ] Was tun? In Thesis als Limitation benennen + welche Teile trotzdem deterministisch sind

---

## 3. Regelwerk als Input

### 3.1 PDF-Regelwerke brauchen oft **Vision** (gerenderte Seiten)

**Kurz:** Textextraktion reicht nicht wenn Layout/Abbildungen Regeln tragen.

**Selbst-Evaluation:**
- [ ] Trifft zu? ___
- [ ] Schwere: ___
- [ ] Beleg: Exploding Kittens NSFW-PDF, `inputs/rulebook_pages/`
- [ ] Was tun? ___

---

### 3.2 „Nur Regelbuch, kein externes Wissen“ ist im Prompt, aber **nicht automatisch prüfbar**

**Kurz:** `rulebook_to_python.txt` verbietet Outside Knowledge — Check dafür existiert nicht.

**Selbst-Evaluation:**
- [ ] Trifft zu? ___
- [ ] Schwere: ___
- [ ] Beleg: `prompts/rulebook_to_python.txt` Zeile 4–5
- [ ] Was tun? Manuell / Judge / bekannte „Famous rules“-Heuristiken

---

### 3.3 **Mehrdeutige Regeln** werden zu Implementierungsentscheidungen — ohne einheitliche Bewertung

**Kurz:** Shuffle, Nö!-Timing, Defuse-Wahl — Judge listet sie, aber kein Goldstandard.

**Selbst-Evaluation:**
- [ ] Trifft zu? ___
- [ ] Schwere: ___
- [ ] Beleg: `exploding_kittens_*_judge.md` Findings
- [ ] Was tun? Scope in Thesis: „deterministische Variante“ vs. „faithful stochastic“

---

### 3.4 **Erfundene Kartennamen** wenn Regeltext unvollständig (Katzenkarte 2–5)

**Kurz:** Oneshot-Judge: minor issue — generische Namen nicht im gelieferten Text.

**Selbst-Evaluation:**
- [ ] Trifft zu? ___
- [ ] Schwere: ___
- [ ] Beleg: Judge Finding #4 oneshot
- [ ] Was tun? Bilder in Rulebook-Pages prüfen ob echte Namen sichtbar

---

### 3.5 Regelwerk-**Version/Edition** ist nicht versioniert

**Kurz:** `inputs/game_rules.pdf` wird überschrieben beim Spielwechsel; alte Edition nur in Git-Historie.

**Selbst-Evaluation:**
- [ ] Trifft zu? ___
- [ ] Schwere: ___
- [ ] Beleg: Commit `e0b9e10` vs. `bf34ada`
- [ ] Was tun? Pro Experiment Commit + Dateiname mit Spiel

---

### 3.6 Unklar: **Ist das generierte Spiel überhaupt das intendierte Spiel?**

**Kurz:** `PROBLEME.md` §3.2 — „Woran ableiten?“

**Selbst-Evaluation:**
- [ ] Trifft zu? ___
- [ ] Schwere: ___
- [ ] Beleg: `PROBLEME.md` §3.2
- [ ] Was tun? Setup-Karten zählen, Komponentenliste, Judge setup-Review, manuell 2–3 Kernregeln

---

## 4. Was die mechanischen Checks wirklich messen

### 4.1 `01_result_file` — Datei existiert

**Misst:** Artefakt da. **Misst nicht:** Inhalt.

**Selbst-Evaluation:** Trifft zu? ___ | Schwere: ___ | Beleg: ___

---

### 4.2 `02_python_syntax` — `ast.parse` / Syntax

**Misst:** Python parsebar. **Misst nicht:** Import, Laufzeit.

**Selbst-Evaluation:** ___

---

### 4.3 `03_startable_game` — Import, `Game()`, `initial_state()`

**Misst:** Konstruktion startet. **Misst nicht:** Regeltreue.

**Selbst-Evaluation:** ___

---

### 4.4 `04_required_api` — 8 API-Teilchecks inkl. ein Roundtrip, `render`, `returns`

**Misst:** Minimale BoardBench-Schnittstelle auf **Initialzustand**. **Misst nicht:** Verhalten nach Zügen, alle Phasen.

**Selbst-Evaluation:** ___

---

### 4.5 `05_random_rollouts` — 100 Zufallsspiele, max 300 Schritte, kein Crash / kein dead state

**Misst:** Robustheit unter **zufälliger** legaler Zugfolge. **Misst nicht:** Korrektheit der Züge vs. Regelbuch.

**Details:**
- Proportionaler Score: `9/100` = 0.09, nicht sofort 0
- Seed fix (`CHECK_SEED=1`) → reproduzierbar **wenn** Code unverändert

**Selbst-Evaluation:** ___

---

### 4.6 `06_action_language` — 100 Rollouts, **jede legale Action** in besuchten Zuständen: Roundtrip + eindeutige normalized keys

**Misst:** Naming-Konsistenz + keine Ambiguität nach Normalizer. **Misst nicht:** semantische Korrektheit der Actions.

**Wichtig:** Unit = eine legale Action in einem besuchten State → bei 287 Actions/Step explodiert Unit-Count (z. B. 138k Units).

**Selbst-Evaluation:** ___

---

### 4.7 `90_llm_judge` — nur gültiges `score:` + `confidence` in gespeicherter Judge-Datei

**Misst:** Format + numerischen Judge-Score (×100). **Misst nicht:** ob Judge recht hat.

**Selbst-Evaluation:** ___

---

### 4.8 `99_openspiel_compare` — Lockstep vs. OpenSpiel (spielspezifische Mapper)

**Misst:** Verhaltenale Übereinstimmung in gesampelten Trajektorien **nach** Align. **Misst nicht:** Karten-/Partyspiele ohne OS-Referenz.

**Selbst-Evaluation:** ___

---

### 4.9 `compare_pair` — Oneshot vs. Agentic Lockstep (normalized keys)

**Misst:** Gleiche Action-**Menge** pro Zustand + gleiche Trajektorie unter gleichem RNG für Zugwahl. **Misst nicht:** ob beide zum Regelbuch passen.

**Wichtig:** Jedes Spiel ruft **eigenes** `initial_state()` auf — **kein** geteilter Startzustand zwischen Varianten.

**Selbst-Evaluation:** ___

---

## 5. Was die Checks **nicht** messen

### 5.1 Kein Check vergleicht **Zugfolgen mit menschlichem Regelverständnis**

**Selbst-Evaluation:** Trifft zu? ___ | Schwere: ___ | Was tun? Rubrik/Szenario-Tests

---

### 5.2 Kein Check prüft **versteckte Information** (andere Spielerhände wirklich hidden)

**Kurz:** `information_state` optional; `render` darf alles leaken — Judge erwähnt das, Check nicht.

**Selbst-Evaluation:** ___

---

### 5.3 Kein Check prüft **Wahrscheinlichkeiten** / Chance-Knoten systematisch

**Kurz:** `chance_outcomes` optional; keine Summe=1-Prüfung über alle States.

**Selbst-Evaluation:** ___

---

### 5.4 Kein Check erkennt **kombinatorische Explosion** in `legal_actions` als Qualitätsproblem

**Kurz:** 287 legale Startzüge sind „OK“ für 05/06 solange nichts crasht.

**Selbst-Evaluation:** ___ | Beleg: Agentic Exploding Kittens Start

---

### 5.5 Kein Check erkennt **zwei Varianten mit verschiedener Zugsemantik** vor Pair-Align

**Selbst-Evaluation:** ___ | Beleg: Pair fail 6 vs 287

---

### 5.6 Kein Check validiert **Judge-Findings** (major/critical counts)

**Selbst-Evaluation:** ___ | Beleg: `critical_issues: 0` trotz Rollout-Fail

---

### 5.7 Kein Check für **Prompt-Compliance** der Rohantwort (Annahmen-Sektion, ein Codeblock)

**Selbst-Evaluation:** ___ | Siehe `evaluation_draft.md` §4

---

### 5.8 Kein Check für **Performance** (legal_actions Laufzeit)

**Selbst-Evaluation:** ___ | Siehe `evaluation_draft.md` §14.4

---

### 5.9 Kein Check ob **returns** zum Regelbuch passen (nur Typ+Länge am Start)

**Selbst-Evaluation:** ___

---

### 5.10 Kein Check ob **terminal** zur richtigen Zeit erreicht wird

**Selbst-Evaluation:** ___

---

## 6. LLM-Judge vs. deterministische Checks

### 6.1 Judge bekommt **bewusst keine Check-Logs**

**Kurz:** `llm_judge_review.md`: „Do not rerun deterministic checks“ — unabhängige Regel-Review.

**Nebenwirkung:** Widersprüche Judge ↔ 05/06 sind **feature**, nicht Bug — aber du musst sie interpretieren.

**Selbst-Evaluation:** ___

---

### 6.2 `critical_issues` ist **vom Judge frei definiert**, nicht an Checks gekoppelt

**Kurz:** Prompt listet Severity in Findings, aber keine Definition wann „critical“ = Runtime-Crash.

**Beispiel:** Oneshot Rollout-Crash (`'ngriff'`) → Judge `critical_issues: 0`, `major_issues: 2` (Shuffle, Nö!).

**Selbst-Evaluation:** ___

---

### 6.3 Judge-Score fließt in Summary mit **Gewicht 10** wie Quality-Checks

**Kurz:** Agentic 72/100 Judge → 0.72 trägt stark in gewichtete Summary (0.918).

**Frage:** Soll niedriger Judge bei hohen mechanischen Checks die Gesamtnote drücken — oder getrennt berichten?

**Selbst-Evaluation:** ___

---

### 6.4 Judge kann **plausible aber falsche** Implementierungen gut bewerten

**Kurz:** Statische Code-Lesbarkeit + Regelbook-Text ohne Ausführung.

**Selbst-Evaluation:** ___ | Beleg: Agentic 7/7 checks + Judge 0.72

---

### 6.5 Judge-Findings sind **gute Kandidaten für neue deterministische Tests**

**Kurz:** `llm_judge_workflow.md`: wiederholte Findings → Szenario-Checks.

**Selbst-Evaluation:** ___ | Beispiel: Judge schlägt Defuse-Flow-Test vor (oneshot §5)

---

### 6.6 Mehrere Judges / Modelle — **nicht** im Standard-Workflow

**Selbst-Evaluation:** ___ | Mitigation in `llm_judge_workflow.md` erwähnt, nicht umgesetzt

---

## 7. Logikfehler findbar machen

### 7.1 **Random Rollouts** finden Crashes, selten systematische Regelverstöße

**Kurz:** Wenn Fehler nur in seltenen Phasen (Nope-Kette, 5er-Combo) — niedrige Trefferwahrscheinlichkeit bei 100×300.

**Selbst-Evaluation:** ___

---

### 7.2 **Falsche aber konsistente** Logik (falsches Spiel, stabil) ist schwer erkennbar

**Kurz:** Kein Oracle außer OpenSpiel (wenn da) oder manuelle Rubrik.

**Selbst-Evaluation:** ___

---

### 7.3 **Setup-Unterschiede** zwischen Varianten verfälschen jeden Vergleich

**Kurz:** Oneshot `main` vs. Agentic `turn`; unterschiedliche deterministische Deals.

**Selbst-Evaluation:** ___ | Beleg: Pair-Compare step 0

---

### 7.4 **Action-Enumeration** ist Teil der Semantik, nicht nur Syntax

**Kurz:** Agentic: Five-Combos schon bei leerer Ablage; Oneshot: nur wenn Discard nicht leer.

**Selbst-Evaluation:** ___

---

### 7.5 Bugs in **Pending/Phase-Resolution** (z. B. falscher `kind`-Vergleich)

**Kurz:** Klassischer Logikfehler — tritt nur auf wenn bestimmte Karte gespielt + Nope-Phase.

**Selbst-Evaluation:** ___ | Beleg: möglicher `'ngriff'`-KeyError-Pfad in oneshot `_resolve_pending`

---

### 7.6 **Keine minimalen reproduzierbaren Szenario-Tests** im Repo

**Kurz:** Judge listet ~10 Szenarien für Exploding Kittens — keines als `checks/` umgesetzt.

**Selbst-Evaluation:** ___

---

### 7.7 Logikfehler in **OpenSpiel-Mapping** vs. Logikfehler im **Generierten**

**Kurz:** `99` hat Havannah-spezifische Label-Mapper — Fehlerquelle trennen schwer.

**Selbst-Evaluation:** ___

---

### 7.8 Menschliche **Code-Review** ist aktuell der einzige tiefe Logik-Kanal

**Kurz:** `TODO.md` fordert das explizit.

**Selbst-Evaluation:** ___

---

## 8. Testabdeckung & Sampling

### 8.1 Abdeckung = „besuchte States unter Random Policy“, nicht „alle Regeln“

**Selbst-Evaluation:** ___

---

### 8.2 `ROLLOUTS=100` ist bewusst klein (manuell); Agenten sollen Full-Eval nicht laufen

**Selbst-Evaluation:** ___ | `AGENTS.md`

---

### 8.3 `06_action_language` zählt **pro Action eine Unit** → Spiel mit großer Branching-Faktor dominiert Laufzeit und Score-Gewicht indirekt

**Selbst-Evaluation:** ___

---

### 8.4 **Keine** zurückgehaltenen Test-Trajektorien (Anti-Gaming)

**Selbst-Evaluation:** ___ | `boardbench_checkliste.md` §7

---

### 8.5 **Keine** Metrik „Anteil Regelbuch-Abschnitte abgedeckt“

**Selbst-Evaluation:** ___

---

### 8.6 Edge Cases explizit untergetestet

Kandidaten zum manuellen Abhaken:

- [ ] Spielstart / erste Runde
- [ ] Letzter Spieler / Elimination
- [ ] Unentschieden (falls relevant)
- [ ] Zug unter Zwang (muss ziehen)
- [ ] Out-of-turn (Nö!)
- [ ] Chance / Shuffle / verdeckte Karten
- [ ] Kombinationen (2er/3er/5er)
- [ ] 2-Spieler-Variante vs. 5 Spieler
- [ ] Defuse + Einfügeposition
- [ ] Attack-Kette / Extra-Züge

**Selbst-Evaluation pro Zeile:** ___

---

### 8.7 **Pair compare** `PAIR_ROLLOUTS=1000` — aber Abbruch beim ersten Mismatch

**Kurz:** Score `0/1000` bei step 0 — informativ, aber keine graduelle Divergenz-Tiefe.

**Selbst-Evaluation:** ___

---

## 9. Action-Language, Normalisierung, Vergleich

### 9.1 Normalizer **erfindet keine Actions** — mappt nur Strings (`action_normalizer.py`)

**Selbst-Evaluation:** ___

---

### 9.2 Normalizer kann **verschiedene Namen auf gleichen Key** legen → 06 FAIL (Ambiguity)

**Selbst-Evaluation:** ___ | Beleg: Abalone ambiguous `move:line->r1c1`

---

### 9.3 Normalizer kann **gleiche Semantik mit verschiedenen Keys** lassen → Pair/OS FAIL

**Selbst-Evaluation:** ___

---

### 9.4 LLM-Align soll nur Naming ändern — **Compliance nicht enforced**

**Selbst-Evaluation:** ___

---

### 9.5 OpenSpiel-Vergleich braucht oft **zusätzliche spielspezifische Mapper** (Havannah)

**Selbst-Evaluation:** ___ | `99_openspiel_compare.py`

---

### 9.6 `PROBLEME.md`: OpenSpiel-Vergleich schwer wegen Zugsyntax

**Selbst-Evaluation:** ___ | Teilweise durch Align+Normalizer adressiert, nicht gelöst für alle Spiele

---

### 9.7 Pair-Align (joint) vs. zwei Single-Aligns — erst letzteres im alten Fail-Lauf

**Selbst-Evaluation:** ___ | Neuer Prompt `action_language_pair_align.md` — erneut testen

---

## 10. Oneshot vs. Agentic

### 10.1 **Unterschiedliche Prompts/Workflows** → unterschiedliche APIs/Phasen-Namen erwartbar

**Selbst-Evaluation:** ___

---

### 10.2 Pair-Compare setzt implizit voraus: **gleiches Spiel, gleiche Modellierung**

**Kurz:** Aktuell oft falsch — unterschiedliche Zugmengen.

**Selbst-Evaluation:** ___

---

### 10.3 Agentic kann länger/komplexer sein (mehr Enumeration, mehr Phasen)

**Selbst-Evaluation:** ___ | 287 Start-Actions

---

### 10.4 Oneshot kann **mehr Runtime-Bugs** haben bei ähnlichem Judge-Score

**Selbst-Evaluation:** ___ | Oneshot 5/7 vs Judge 0.65; Agentic 7/7 vs 0.72

---

### 10.5 „Welche Variante ist die Referenz?“ — **nicht definiert**

**Selbst-Evaluation:** ___

---

## 11. OpenSpiel-Referenz & Spiele ohne Referenz

### 11.1 ~70 OpenSpiel-Spiele als **Kalibrierungs-Orakel** (Tier A) — Konzept

**Selbst-Evaluation:** ___ | `boardbench_checkliste.md`

---

### 11.2 Exploding Kittens: **kein OpenSpiel** → `INCLUDE_OPENSPIEL_COMPARE=False`

**Selbst-Evaluation:** ___

---

### 11.3 Ohne OpenSpiel: mehr Gewicht auf **Judge + Rubrik + Pair** — alle schwächer als Gold-Referenz

**Selbst-Evaluation:** ___

---

### 11.4 OpenSpiel-Vergleich testet **nicht** Regelbuch-Treue direkt — nur Übereinstimmung mit OS-Implementierung

**Selbst-Evaluation:** ___

---

### 11.5 OS und Regelbuch können **voneinander abweichen** (vereinfachtes OS-Spiel)

**Selbst-Evaluation:** ___

---

## 12. Scoring, Gewichtung, Interpretation

### 12.1 Summary-Score = **gewichteter Mittelwert pro Check**, nicht Summe aller Units

**Gewichte:** 01–04 → 1; 05, 06, 90, 99, Pair → 10.

**Selbst-Evaluation:** ___ | `AGENTS.md`, `checks/common.py`

---

### 12.2 Ein Check kann **proportional** bestehen (987/1000) — gut für Robustheit, schwer zu kommunizieren

**Selbst-Evaluation:** ___

---

### 12.3 **Pipeline läuft weiter** bei Fail bis Ende — Summary zeigt Mix

**Selbst-Evaluation:** ___

---

### 12.4 Judge-Score und mechanische Checks **konkurrieren** in einer Zahl wenn beide in Summary

**Selbst-Evaluation:** ___ | Trennung in Thesis erwägen

---

### 12.5 `needs_code_change: true` im Judge — **nicht** als Check geparst

**Selbst-Evaluation:** ___

---

## 13. Workflow, Reproduzierbarkeit, Artefakte

### 13.1 Git-Commits als **Experiment-Tagebuch** — gut für Thesis, unübersichtlich bei vielen Spielen

**Selbst-Evaluation:** ___ | `AGENTS.md` Git history rules

---

### 13.2 `outputs/` nicht gitignored — Artefakte sind Teil der Evidenz

**Selbst-Evaluation:** ___

---

### 13.3 Run-Timings in `*_checks.txt` (phase + summary) — neu, ältere Logs evtl. ohne

**Selbst-Evaluation:** ___

---

### 13.4 Notebook-Outputs vs. `outputs/` Logs können **auseinanderlaufen**

**Selbst-Evaluation:** ___

---

### 13.5 Kernel nicht neu gestartet → alte Funktionen in Notebook-Session

**Selbst-Evaluation:** ___

---

### 13.6 **Kein** automatisches „pre-commit run all checks“

**Selbst-Evaluation:** ___

---

## 14. Thesis-Forschungsfragen & Designentscheidungen

Geh diese Fragen schriftlich an (aus `evaluation_draft.md` §22 + `QUESTIONS.txt`):

### 14.1 Wie strikt ist „Korrektheit“ bei mehrdeutigem Regelbuch?

**Selbst-Evaluation:** Meine Antwort: ___

---

### 14.2 Bewerten: ehrliche Lücken vs. falsche Vollständigkeit?

**Selbst-Evaluation:** ___

---

### 14.3 Syntax-OK + Logik falsch vs. unvollständig + transparent?

**Selbst-Evaluation:** ___

---

### 14.4 OpenSpiel-Alignment: Kernscore oder Zusatzvergleich?

**Selbst-Evaluation:** ___

---

### 14.5 Automatisierung vs. manuelle Regel-Audit — welcher Anteil in der Note?

**Selbst-Evaluation:** ___

---

### 14.6 Pilot-Spiele wählen nach: Einfachheit, Vielfalt, OpenSpiel-Verfügbarkeit?

**Selbst-Evaluation:** ___

---

### 14.7 Stochastik / Hidden Info: eigene Bewertungsregeln?

**Selbst-Evaluation:** ___

---

### 14.8 „OpenGame für Implementierung, nur Tests schreiben?“ (`QUESTIONS.txt`)

**Selbst-Evaluation:** Meine Haltung: ___

---

### 14.9 Mehr vergleichen mit weniger oder mehr Output? (`QUESTIONS.txt`)

**Selbst-Evaluation:** ___

---

### 14.10 PDFs: Vision processing zwingend vs. nur Text-Prompts verbessern?

**Selbst-Evaluation:** ___

---

## 15. Konkrete Beispiele aus bisherigen Läufen

### 15.1 Exploding Kittens — Agentic

| Metrik | Wert | Interpretation |
|--------|------|----------------|
| Base checks | 7/7, Summary ~0.918 | Mechanisch stark |
| Judge | 0.72, critical 0 | Qualitativ „OK mit Lücken“ |
| Start legal actions | 287 | Five-Combo-Explosion |
| Pair compare | FAIL step 0 | Nicht vergleichbar mit oneshot |

**Selbst-Evaluation:** Was davon ist „Benchmark-Erfolg“? ___

---

### 15.2 Exploding Kittens — Oneshot

| Metrik | Wert | Interpretation |
|--------|------|----------------|
| Base checks | 5/7 (05, 06 fail) | Runtime-Probleme |
| Judge | 0.65, critical 0 | Judge sieht Crash nicht |
| Start legal actions | 6 | Kein Five am Start (leerer Discard) |

**Selbst-Evaluation:** Soll Judge-Crash widerspruch in Thesis? ___

---

### 15.3 Abalone (Historie) — action-language ambiguous keys

**Kurz:** Zwei verschiedene Züge → gleicher normalized key → 06 FAIL.

**Selbst-Evaluation:** Naming-Problem oder Normalizer zu aggressiv? ___

---

### 15.4 Havannah — OpenSpiel label mapping

**Kurz:** Viel Custom-Code in `99` — Kalibrierung vs. Wartungslast.

**Selbst-Evaluation:** ___

---

## 16. Master-Checkliste (kurz, zum Abhaken)

### A. LLM & Oracle

- [ ] A1 Generierung ist unvermeidlich LLM-abhängig
- [ ] A2 Judge ist LLM-abhängig und nicht ausführbar
- [ ] A3 Align ist LLM-abhängig
- [ ] A4 Kein mechanisches Oracle für Regelbuch-Treue bei Nicht-OS-Spielen
- [ ] A5 Judge und Checks können widersprechen — Interpretation nötig
- [ ] A6 `critical_issues` ist nicht mit Crashes gekoppelt

### B. Messbarkeit

- [ ] B1 Checks messen vor allem „läuft es“ + API + Naming
- [ ] B2 Regel-Logik fast nur indirekt (OS, Judge, manuell)
- [ ] B3 Random sampling deckt seltene Phasen schlecht ab
- [ ] B4 Große `legal_actions` sind erlaubt und unbemängelt
- [ ] B5 Pair-Compare verlangt gleiche Semantik, nicht nur gleiche Namen

### C. Testabdeckung

- [ ] C1 Keine festen Szenario-Tests pro Spiel
- [ ] C2 Judge-Testvorschläge nicht automatisiert
- [ ] C3 100 Rollouts = bewusst klein
- [ ] C4 Keine Coverage-Metrik für Regeln
- [ ] C5 Edge-Case-Liste nicht systematisch abgearbeitet

### D. Vergleich & Normalisierung

- [ ] D1 Normalizer löst nicht alle Cross-Variant-Probleme
- [ ] D2 Align erzwingt keine gleiche `legal_actions`-Menge
- [ ] D3 Pair-Compare: separate `initial_state()` pro Variante
- [ ] D4 OpenSpiel nur für Teilmenge der Spiele
- [ ] D5 OS-Vergleich ≠ Regelbuch-Vergleich

### E. Workflow & Thesis

- [ ] E1 Artefakt-Pipeline gut für Nachvollziehbarkeit
- [ ] E2 Git-Commits dokumentieren Experimente
- [ ] E3 Scoring-Gewichtung bewusst wählen / erklären
- [ ] E4 Scope: Benchmark-Vorbereitung vs. fertiger Benchmark klar trennen
- [ ] E5 Offene Prof-Fragen (`QUESTIONS.txt`) in Limitationen / Ausblick

### F. Nächste konkrete Schritte (optional — selbst priorisieren)

- [ ] F1 3–5 Judge-Szenarien als `checks/07_...` für ein Pilotspiel
- [ ] F2 Pre/Post-Align Guard für `legal_actions` cardinality
- [ ] F3 Pair-Compare: shared seeded setup oder nur Compare nach manueller Harmonisierung
- [ ] F4 Judge-Packet optional mit **Zusammenfassung** der Check-Fails (getrenntes Feld)
- [ ] F5 `critical_issues`-Definition im Judge-Prompt schärfen (z. B. = Crash, deadlock, falscher Winner)
- [ ] F6 Thesis-Tabelle: pro Spiel Spalten {mech., judge, OS, pair, manuell}
- [ ] F7 Entscheidung: Five-Combo-Enumeration — erlaubt oder cap/enumerate lazily

---

## Anhang: Schnellreferenz Dateien

| Thema | Datei |
|-------|-------|
| Agent-Regeln | `AGENTS.md` |
| Check-Implementierung | `checks/01`–`06`, `90`, `99`, `compare_pair.py` |
| Judge-Prompt | `prompts/llm_judge_review.md` |
| Judge-Workflow | `docs/llm_judge_workflow.md` |
| Eval-Ideen (breit) | `docs/evaluation_draft.md` |
| Architektur-Checkliste DE | `docs/boardbench_checkliste.md` |
| Prof-Fragen | `meeting/2.7/QUESTIONS.txt` |
| Konsolidierte Analyse | `PROBLEME.md` |
| Ältere Kurznotiz | `docs/PROBLEME.txt` |
| Letzter EK-Lauf | `outputs/exploding_kittens_*` |

---

*Ende der Checkliste. Ergänze eigene Punkte unten.*

## Eigene Notizen

```
(Datum: _________)




```
