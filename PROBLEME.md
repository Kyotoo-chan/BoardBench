# BoardBench — Problemanalyse & offene Punkte

> **Zweck:** Arbeitsgrundlage für Thesis und Repo-Entwicklung. Beschreibt, was nach drei Pilotspielen (Havannah, Abalone, Exploding Kittens) schiefgehen kann, **warum**, und ob/wie man es angehen kann.
>
> **Stand:** 2026-06-29 · Commits bis `081e3e0` (Exploding Kittens)
>
> **Detail-Checkliste zum Abhaken:** [`docs/open_problems_self_evaluation.md`](docs/open_problems_self_evaluation.md)

---

## 1. Projektidee in Kurzform

BoardBench (Bachelorarbeit) soll ein **PaperBench-ähnlicher Benchmark** für Brett- und Kartenspiele werden:

1. **Input:** Regelwerk (Text/PDF, idealerweise ohne externes Spielwissen im Prompt)
2. **Generation:** LLM erzeugt ein **selbstständiges Python-Spielmodul** mit fester BoardBench-API
3. **Evaluation:** mechanische Checks → optional LLM-Judge → optional OpenSpiel-Vergleich (Tier A) → später Rubrik/Szenarien (Tier B)
4. **Langfristig:** Spiele vergleichen, Regelwerk-Klarheit operationalisieren, Kalibrierung an OpenSpiel wo möglich

**Aktueller Repo-Stand** (`AGENTS.md`): bewusst **manual-first**, Experiment-Vorbereitung — noch kein automatisierter, skalierbarer Benchmark.

Das ist kein Bug, sondern Scope. Die Probleme unten betreffen vor allem die **Lücke zwischen Vision und messbarer Regelkorrektheit**.

---

## 2. Was drei Pilotspiele gemeinsam zeigen

| Spiel | Typ | OpenSpiel | Agentic (Checks) | Oneshot (Checks) | Judge (agentic / oneshot) | Besonderes |
|-------|-----|-----------|------------------|------------------|---------------------------|------------|
| **Havannah** | Placement, perfekte Info | ja | 7/7 (+ OS 99.6%) | Syntax-Fail → Fix → 7/7 | 0.90 / 0.85 | Pair-Compare **1000/1000** |
| **Abalone** | Physisches Push-Spiel, Figur-Setup | unklar/nicht im Lauf | 6/7 (06 fail) | 6/7 (06 fail) | 0.78 / 0.60 | **Normalizer-Ambiguität** bei Zugnamen |
| **Exploding Kittens** | Karten, Zufall, Hidden Info | nein | 7/7 | 5/7 im Artefakt* | 0.72 / 0.65 | **287 vs 6** Startaktionen; Pair **0/1000** |

\* Oneshot-Artefakt `exploding_kittens_oneshot_checks.txt`: `05` 9/100 (`'ngriff'`), `06` 97.1%. Ein erneuter Lauf mit gleichem Code und Seed 1 ergab 2026-06-29 **7/7** — das Artefakt dokumentiert den Experimentlauf; Abweichung zeigt, dass Artefakte und Re-Runs abgeglichen werden müssen.

### 2.1 Muster über alle Spiele

1. **Smoke-Checks (01–04) sind zuverlässig** — Syntax, Import, API sind für starke Modelle selten das Hauptproblem.
2. **„Läuft es?“ ≠ „Stimmt es mit dem Regelbuch?“** — Rollouts finden Crashes, aber kaum systematische Regelverstöße.
3. **LLM-Judge liefert qualitative Hinweise**, ist aber kein ausführbares Orakel und kann mit mechanischen Checks **widersprechen** (z. B. Judge `critical_issues: 0` trotz Rollout-Crash im Artefakt).
4. **Vergleichbarkeit** (Pair, OpenSpiel) scheitert oft nicht an „falschem Python“, sondern an **unterschiedlicher Zugsemantik und Namensgebung** zwischen Varianten oder Referenzen.
5. **Regelwerk-Input** ist oft unvollständig ohne **Bilder/Vision** (Abalone Fig. 1, Exploding Kittens Kartennamen).
6. **Spielkomplexität** treibt `legal_actions`-Explosion (Kombinatorik) — mechanisch OK, für Benchmark und Vergleich problematisch.

---

## 3. Problemkategorien: Ursache, Fixbarkeit, Vorgehen

Legende **Fixbarkeit:**

- **Ja (repo)** — mit überschaubarem Aufwand im Repo lös- oder verbesserbar
- **Teilweise** — Verbesserung möglich, aber Grundproblem bleibt
- **Nein / Scope** — strukturelle Grenze; nur dokumentieren oder Thesis-Design anpassen
- **Forschung** — Designentscheidung für die Arbeit, kein reiner Bugfix

---

### 3.1 Das Ergebnis hängt am LLM-Output (Generation + Judge + Align)

**Symptom:** Jedes `outputs/<game>.py` ist neu, jeder Lauf anders; Pipeline-Qualität = Modell + Prompt + Regelinput.

**Ursache:** Kern-Artefakt ist LLM-generiert; Judge und Action-Language-Align sind **weitere** LLM-Schritte.

**Fixbarkeit:** **Teilweise**

| Was | Machbar |
|-----|---------|
| Prompts, Implementation Brief, OpenSpiel-Backbone schärfen | Ja |
| Modell/Seed/Parameter pro Run festhalten | Ja (teilweise schon in Judge-Packets) |
| Deterministische Reproduktion identischer Outputs | Nein (Modell-Sampling) |
| Agentic Generator sieht `checks/` nicht | Bewusst so (`workflow_description.md`) — gut gegen Overfitting, schlecht für gezielte Fixes |

**Thesis:** Als Limitation klar benennen; trennen, was **deterministisch** messbar ist (Checks 01–06, OS-Compare) vs. was **LLM-bewertet** ist (Judge, Align).

---

### 3.2 „Ist das überhaupt das richtige Spiel?“ (Identität & Regelabdeckung)

**Symptom:** Modul ist spielbar, aber vielleicht falsche Edition, falsches Setup, erfundene Kartennamen, vereinfachte Zufall.

**Ursache:** Kein Goldstandard-Orakel für Spiele **ohne** OpenSpiel; Checks prüfen nicht „Exploding Kittens vs. Mühle“.

**Fixbarkeit:** **Teilweise**

| Hebel | Nutzen |
|-------|--------|
| **Setup-Invarianten** (Spielerzahl, Handgröße, Steine/Karten zählen) | Ja — als `07_scenario_*.py` ableitbar |
| Judge setup-Review | Hilft, nicht mechanisch |
| Komponentenliste aus Regelbuch extrahieren | Manuell / später Rubrik |
| Bekannte-Spiele-Kontamination | Forschung — Perturbationstests |

**Aus den Läufen:** Exploding Kittens — Judge findet deterministisches Setup statt Shuffle; Abalone — Setup hängt an **Abb. 1**, die im Text nicht vollständig ist.

---

### 3.3 Regelwerk als Input: Text, PDF, Vision

**Symptom:** OCR/Text reicht nicht; Kartennamen/Koordinaten/Brettlayouts fehlen.

**Ursache:** Viele Regeln leben in **Abbildungen**; `game_rules.pdf` wird beim Spielwechsel überschrieben (Edition nur in Git-Historie).

**Fixbarkeit:** **Teilweise**

- `inputs/rulebook_pages/` + Vision im pi/Notebook-Workflow: **Ja**, bereits vorgesehen
- Automatische OCR-Qualitätsprüfung: **Nein** (noch nicht)
- Versionierung pro Spiel/Edition (`inputs/havannah/...`): **Ja**, organisatorisch

**Prof-Frage** (`QUESTIONS.txt`): PDFs brauchen Vision — **zutreffend** für Abalone und Exploding Kittens.

---

### 3.4 Mechanische Checks messen Robustheit, nicht Regellogik

**Was 01–06 wirklich tun:**

| Check | Misst | Misst nicht |
|-------|-------|-------------|
| 01–04 | Artefakt, Syntax, Start, API-Roundtrip am **Initialzustand** | Verhalten nach Zügen, Phasen |
| 05 | Kein Crash / kein dead state unter **Zufallspolicy**, 100×300 Schritte | Regelkonformität |
| 06 | `action_to_name` ↔ `name_to_action`, eindeutige Normalizer-Keys in besuchten Zuständen | Semantik der Züge |
| 90 | Parsebarer Judge-`score` | Ob Judge recht hat |
| 99 | Lockstep vs. OpenSpiel (nach Align + spielspezifischem Mapper) | Regelbuch direkt |

**Fixbarkeit:** **Ja (repo)** für **neue** Checks — aber nicht „ein Check für alle Regeln“.

**Empfehlung** (`TODO.md`): Erst Code + bestehende Checks verstehen, dann **regelbuch-abgeleitete Szenario-Checks** (Judge-Findings sind gute Kandidaten — z. B. Defuse-Flow, Havannah-Ring).

---

### 3.5 LLM-Judge: nützlich, aber kein hartes Orakel

**Symptome aus Exploding Kittens:**

- Agentic: 7/7 mechanisch, Judge 0.72, `critical_issues: 0`, `needs_code_change: true`
- Oneshot-Artefakt: 5/7 mechanisch, Judge 0.65, ebenfalls `critical_issues: 0`

**Ursachen:**

1. Judge bekomst **bewusst keine Check-Logs** (`llm_judge_review.md`) — Widerspruch ist Feature, erfordert Interpretation.
2. `90_llm_judge` parst nur `score` + `confidence`, **nicht** `critical_issues`.
3. `critical_issues` ist im Prompt nicht an Crashes gekoppelt.

**Fixbarkeit:** **Teilweise**

| Maßnahme | Aufwand |
|----------|---------|
| Judge-Prompt: Definition „critical = Crash, deadlock, falscher Winner“ | Gering |
| `critical_issues` mechanisch parsen / Gate | Gering |
| Judge-Score **getrennt** von mechanischer Summary in Thesis | Dokumentation |
| Mehrere Judges / Modelle | Mittel, Kosten |

---

### 3.6 Action-Language, Normalisierung, Vergleichbarkeit

**Kernproblem** (ursprünglich in `docs/PROBLEME.txt`): *OpenSpiel-Vergleich schwer, weil Zugsyntax unterschiedlich ist.*

**Stand im Repo:** Action-Language-Align (LLM) + `action_normalizer.py` — **hilft, löst nicht alles**.

**Belege:**

| Fall | Was passiert |
|------|----------------|
| **Abalone** | Zwei verschiedene Züge → gleicher Key `move:line->r1c1` → **06 FAIL** (42–79%) |
| **Exploding Kittens Pair** | Schritt 0: oneshot 6 Actions, agentic 287 — **semantisch andere Modellierung**, nicht nur Namen |
| **Havannah OS** | 99.6% — fast perfekt, aber **viel spielspezifischer Mapper** in `99_openspiel_compare.py` |

**Ursachen:**

1. Normalizer **erfindet keine Actions**, kann aber verschiedene Namen **zusammenlegen** (Ambiguität) oder gleiche Semantik **getrennt lassen**.
2. LLM-Align darf nur Naming ändern — **Compliance nicht enforced** (kein Diff `legal_actions` vor/nach Align).
3. Pair-Compare: **jede Variante** ruft `initial_state()` auf — kein geteilter Start; unterschiedliches Setup deterministisch erlaubt.
4. OpenSpiel-Labels (Havannah `a2`, `b5`, …) ≠ generierte `q/r`-Namen ohne Adapter.

**Fixbarkeit:** **Teilweise**

| Maßnahme | Fixbar |
|----------|--------|
| Normalizer weniger aggressiv / spielspezifische Regeln | Ja, wartungsintensiv |
| Check: Align ändert Action-Mengen nicht (Sample-States) | Ja |
| Pair-Compare nur nach explizitem „gleiches Setup“-Contract | Ja, Prompt + API |
| Generierte Module an **kanonisches Zugformat** im Prompt binden | Ja, schon angestrengt |
| Ein Mapper für alle Spiele | Nein |

---

### 3.7 Oneshot vs. Agentic: Vergleich ist methodisch heikel

**Beobachtung:** Nicht „welche Pipeline ist besser“, sondern oft **zwei verschiedene Spiele** mit ähnlicher Oberfläche.

**Exploding Kittens:**

- Agentic: Five-Card-Combos als riesige `move:five_...->discard_take_...`-Enumeration ab Start
- Oneshot: Five nur wenn Discard nicht leer; kleinere Startmenge
- Pair-Compare: sofortiger Abbruch — **0/1000**

**Havannah:** Pair **1000/1000** — zeigt, dass Vergleich **funktioniert**, wenn beide Varianten dieselbe Modellierung wählen.

**Fixbarkeit:** **Forschung**

- Entscheiden: Ist Pair-Compare „gleicher Code-Stil“ oder „verhaltensäquivalente Umsetzung“?
- Evtl. nur **eine** Generation pro Spiel als Referenz, andere Pipeline separat bewerten
- Joint Pair-Align (`action_language_pair_align.md`) erneut testen, wenn Semantik schon divergiert — **begrenzte Wirkung**

---

### 3.8 OpenSpiel: Kalibrierung, nicht Regelbuch-Wahrheit

**Havannah:** Agentic fast perfekt gegen OS; verbleibende 0.4% bei Schritt 110 (`generated=0` legal actions) — wahrscheinlich **Terminal/Stein-Vorrat/Draw**-Interpretation, nicht nur Naming.

**Exploding Kittens:** kein OpenSpiel — Tier A entfällt.

**Fixbarkeit:** **Teilweise**

- OS-Compare für ~70 Spiele als **Kalibrierung des Verfahrens** (`boardbench_checkliste.md`): sinnvoll
- OS-Implementierung kann vom Regelbuch abweichen: in Thesis erwähnen
- Pro OS-Spiel Mapper-Wartung: ja, aber Kosten skaliert mit Spielzahl

**Prof-Frage:** *OpenGame für Implementierung, nur Tests schreiben?* — würde Tier A invertieren (Referenz-Code statt generierter Code). Machbar für Kalibrierung, **widerspricht** der Forschungsfrage „Regelwerk → Code“.

---

### 3.9 Kombinatorische Explosion & Performance

**Symptom:** Exploding Kittens agentic — 138k Action-Language-Units in einem Lauf; 287 legale Startzüge.

**Ursache:** LLM modelliert Kombinationen als explizite Actions statt Phasen/Parameter.

**Fixbarkeit:** **Teilweise**

- Prompt: „keine kartesische Aufzählung von Kombos“ / Phasenmodell
- Check auf `len(legal_actions)`-Schwellwert als **Qualitätswarnung** (neu)
- Rollout-Budget anpassen — ändert nicht die Semantik

**Bewertung:** Mechanisch **bestanden**, für Benchmark **trotzdem problematisch** (Vergleich, Laufzeit, menschliche Review).

---

### 3.10 Stochastik, Hidden Information, Out-of-turn (Kartenspiele)

**Symptom:** Judge listet bei Exploding Kittens durchgängig:

- deterministisches Setup statt Shuffle/Deal
- erfundenes `Mischen`-Modell
- serialisierte `Nö!`-Phase statt „immer spielbar“
- automatisches Defuse

**Ursache:** Regelbuch ist **mehrdeutig** für sequentielle API; LLM wählt **testbare Vereinfachungen**.

**Fixbarkeit:** **Forschung** + **Teilweise**

| Option | Konsequenz |
|--------|------------|
| Scope: „deterministische Szenario-Variante“ | Ehrlich, benchmarkbar |
| Scope: „faithful stochastic“ | `chance_outcomes` + Setup-Chance nötig |
| Rubrik pro Spieltyp (Karten vs. Placement) | Ja, langfristig Tier B |

Checks prüfen **weder** `information_state`-Konsistenz **noch** Wahrscheinlichkeitssummen.

---

### 3.11 Scoring & eine Summary-Zahl

**Aktuell:** Gewichteter Mittelwert — 01–04 weight 1, Rest weight 10; proportional innerhalb Checks.

**Probleme:**

- Hohe mechanische Scores + mittlerer Judge → eine Zahl (~0.92 agentic EK) **überstrahlt** Judge-Findings
- LLM-Judge und Deterministik in **einer** Summary — konzeptionell verschiedene Größen
- `needs_code_change: true` wird nicht geparst

**Fixbarkeit:** **Ja (repo + Thesis)**

- Thesis: **getrennte Berichte** (Mechanik / Judge / OS / Pair)
- Optional: Judge als Gate unter Schwellwert, nicht nur Score

---

### 3.12 Projektreife: Benchmark vs. Experiment-Workflow

**Offen:**

- Keine Tier-B-Rubrik mit ausführbaren Szenarien pro Spiel
- Keine CI, keine Spiel-Datenbank
- `evaluation_draft.md` = Ideenpool, keine Spec
- Manual pi/Notebook — Reproduzierbarkeit über Git-Artefakte, nicht über Batch-API

**Fixbarkeit:** **Scope** — bewusst klein halten bis Pilot validiert.

---

## 4. Priorisierte Empfehlungen (was zuerst)

### Kurzfristig im Repo (hoher Nutzen, überschaubar)

1. **2–3 Szenario-Checks pro Pilotspiel** aus Judge-Findings (z. B. Havannah Ring-Ecke, EK Defuse ohne Hand, Abalone 2-vs-1 Sumito)
2. **Align-Guard:** Sample vor/nach Align — gleiche `len(legal_actions)` und Action-Typ-Menge
3. **Judge-Prompt:** `critical_issues` definieren; optional parsen
4. **Summary trennen** in Notebook/Logs: `---- summary mechanical` vs. `---- summary judge`
5. **Inputs versionieren:** `inputs/<game>/game_rules.pdf` statt Überschreiben

### Thesis / Design (kein reiner Code)

1. Operationalisieren: Was heißt „Regelwerk klar“ vs. „Modell schwach“ vs. „Spiel komplex“?
2. Scope für Karten/Zufall: deterministische Variante explizit erlauben oder nicht
3. Pair-Compare: nur als **Sanity-Check gleicher Modellierung**, nicht als Hauptmetrik
4. OpenSpiel: Rolle als **Kalibrierung** dokumentieren, nicht als Regelbuch-Ground-Truth

### Bewusst nicht fixen (oder später)

- Vollautomatischer PaperBench-artiger Rubrik-Framework
- Ein Normalizer für alle Spiele
- API-key-Batch ohne manuellen Workflow

---

## 5. Offene Fragen (Professor / `QUESTIONS.txt`)

| Frage | Kurz-Einordnung |
|-------|-----------------|
| Wie geht es weiter? Es hängt am LLM-Output | Strukturell richtig — siehe §3.1 |
| Mehr vergleichen mit weniger oder mehr Output? | Weniger Output pro Spiel (fokussierte API) erleichtert Vergleich; mehr Output (vollständige Regeln) erschwert Bewertung — Trade-off |
| OpenGame für Implementierung, nur Tests schreiben? | Kalibrierung ja; Hauptpfad Regelwerk→Code nein, ohne Forschungsfrage zu ändern |
| Anleitungen / nur Text vs. PDF+Vision | Vision für Pilot 2+3 faktisch nötig |

---

## 6. Dateien & Belege

| Thema | Artefakt |
|-------|----------|
| Havannah Checks | Git `2568b38`, `17d8230` — `outputs/havannah_*_checks.txt` |
| Havannah Pair | `outputs/havannah_pair_action_compare.txt` (1000/1000) |
| Abalone Checks | Git `d15972e` — `outputs/abalone_*_checks.txt` |
| Exploding Kittens | `outputs/exploding_kittens_*` |
| Judge-Reviews | `outputs/*_judge.md` |
| Ältere Kurznotiz | `docs/PROBLEME.txt` (verweist hierher) |
| Selbst-Evaluation | `docs/open_problems_self_evaluation.md` |
| Checkliste Zielbild | `docs/boardbench_checkliste.md` |
| Kritische Einschätzung | `docs/boardbench_checkliste_einschaetzung.md` |

---

## 7. Zusammenfassung in einem Satz

**BoardBench kann heute zuverlässig prüfen, ob LLM-generierte Spiele technisch laufen und grob vergleichbar benannt sind — aber nicht, ob sie das Regelwerk korrekt abbilden; das bleibt abhängig von LLM (Generation, Judge, Align), vom Regelwerk-Input (oft Vision), und von noch fehlenden regelbuch-abgeleiteten Szenario-Orakeln (Tier B), während OpenSpiel nur für eine Teilmenge der Spiele als Kalibrierungs-Orakel (Tier A) dient.**
