# Projektgespräch: offene Fragen, Entscheidungen und Weiterarbeit

> **Stand:** 12.07.2026  
> **Rolle:** kanonische Arbeitsgrundlage nach Abgleich von Exposé, Meeting-Notizen (9.6., 29.6., 2.7., 10.7.) und Repository.  
> **Änderungsbericht:** [`thesis_decisions_and_changes.md`](thesis_decisions_and_changes.md)

## 1. Auf welcher „Page“ wir sind

BoardBench ist heute ein gut dokumentierter **Pilot- und Experiment-Workflow**, aber noch kein wissenschaftlich belastbarer Universalbenchmark. Die Pipeline kann zuverlässig feststellen, ob ein generiertes Spielmodul vorhanden, importierbar, startbar, robust abspielbar und über eine konsistente API bedienbar ist. Sie kann noch nicht allgemein beweisen, dass die Spielregeln vollständig korrekt umgesetzt wurden.

Der zentrale nächste Schritt ist deshalb nicht „noch mehr Spiele generieren“, sondern die Lücke zwischen **technischer Nutzbarkeit** und **regeltextlich belegter Korrektheit** zu schließen.

## 2. Ziel der Bachelorarbeit aus dem Exposé

Das Exposé beginnt mit dem Problem, dass natürlichsprachliche Brettspielanleitungen mehrdeutig oder in Sonderfällen unvollständig sein können. Computerprogramme benötigen dagegen eindeutige Zustände, Aktionen und Endbedingungen. Die Arbeit soll untersuchen, ob LLMs solche Anleitungen in ausführbare Spielumgebungen übersetzen und dadurch Unklarheiten sichtbar machen können.

Daraus folgt als geeignete Hauptfrage:

> **Wie belastbar lassen sich Unklarheiten und Umsetzungsrisiken in Brettspielanleitungen durch ihre LLM-gestützte Übersetzung in ausführbare Spielumgebungen sichtbar machen, und welche Evaluationsschichten sind nötig, um Modellfehler von regeltextlich begründeten Problemen zu unterscheiden?**

Diese Formulierung erhält das Ziel des Exposés, vermeidet aber den unzulässigen Schluss „schlechter Code = schlechte Anleitung“.

### PaperBench-Übertragung

PaperBench bewertet nicht die Qualität eines Papers dadurch, dass ein Agent daran scheitert. Es zerlegt die Replikationsaufgabe in hierarchische, einzeln bewertbare Rubriken; die Rubriken wurden mit den Paper-Autoren abgestimmt. Auch der LLM-Judge wird separat validiert.

Für BoardBench bedeutet das:

1. Regelwerk statt Paper als Spezifikation,
2. ausführbare Spielumgebung statt reproduziertem Experiment als Artefakt,
3. **regelwerksspezifische, zitierbare Szenarien** statt ausschließlich generischer Checks,
4. LLM-Judges als skalierbares Hilfsmittel, nicht als Wahrheit,
5. OpenSpiel als Kalibrierungsreferenz, nicht automatisch als richtige Edition,
6. menschliche oder autoritative Prüfung der Rubrik selbst.

Die PaperBench-Idee ist daher nicht „ein Gesamtscore für alles“, sondern **eine nachvollziehbare Zerlegung der Aufgabe in belegbare Teilanforderungen**.

## 3. Prioritäten und sinnvolle Reihenfolge

| Priorität | Problem | Warum zuerst? | Entscheidung / Status |
|---|---|---|---|
| **P0** | Forschungsziel und zulässige Aussagen | Ohne klares Ziel werden weitere Läufe nicht interpretierbar. | Hauptfrage oben festgelegt; Bestätigung im Professorengespräch offen. |
| **P0** | Vermischter Gesamtscore | Der bisherige Score erzeugt den Eindruck hoher Regelkorrektheit, obwohl 05/06 dies nicht messen. | Methodische Trennung beschlossen. Plot-Redesign bewusst vertagt, bis der agentische Workflow stabil ist. |
| **P0** | Falsche/stale Rulebook-Bilder | Ein falsches Bildpaket kann Generation und Judge systematisch mit der falschen Anleitung versorgen. | Aktivierung löscht alte gerenderte Seiten; aktuell falsche Havannah-Bilder zum aktiven EK-PDF entfernt. |
| **P1** | Fehlende regelspezifische Orakel | Das ist die größte fachliche Lücke zwischen Pilot und PaperBench-Idee. | Minimaler, regelbuchzitierter Szenario-Runner ergänzt: Havannah `5/5` (inkl. Brücke/Ring), Conect `3/3` Grundfluss. Tiefe Negativ-/Siegfälle fehlen noch. |
| **P1** | Align kann Logik verändern | Dann misst der OpenSpiel-/Pair-Vergleich nicht mehr das ursprüngliche Artefakt. | Seed-basierter Pre-/Post-Align-Guard eingebaut; bei Abweichung wird das Backup wiederhergestellt. |
| **P1** | Judge kann Regeln oder Severity falsch einordnen | EK zeigte auch menschliche Fehlinterpretationen. | Judge-Prompt verlangt Regelzitat, Seite, Code-Stelle und klare Severity-Definition. |
| **P1** | Keine Trennung von Modellfehler, Regelunklarheit und Spielkomplexität | Sonst kann die Arbeit das Exposé-Ziel nicht beantworten. | Versuchsdesign mit Kontrollen und Wiederholungen nötig; siehe §7. |
| **P2** | Seltene Logikfehler / Edge Cases | Random Rollouts erreichen sie selten. | Nach Szenario-Basis: coverage-guided Exploration; kein RL als erster Schritt. |
| **P2** | Trainingsdaten-Kontamination | Bekannte Spiele könnten ohne echtes Regelverständnis besser ausfallen. | Anonymisierte Regelwerk-Bedingung und Bekanntheitsproxy als Kontrolle vorsehen. |
| **P3** | Günstige Modelle, Scraping, Inhouse-LLM | Praktisch interessant, beantwortet aber nicht die Kernfrage. | GLM bleibt Kosten-/Machbarkeitssignal; Scraper und Inhouse-Modelle nicht zum Hauptbeitrag machen. |

## 4. Abgleich mit den Meeting-Notizen

| Meeting-Punkt | Einordnung | Konkrete Folge |
|---|---|---|
| „Wie findet man spielspezifische Logikfehler?“ | **Kernproblem, offen** | Zitierbare Szenarien zuerst; danach seltene Zustände gezielt suchen. |
| Manuelle State-Beschreibungen / PaperBench an Spiel anpassen | **richtig** | Version-1-Szenarioformat nutzt Regelzitat, Seite, Aktionen und öffentliche Erwartungen. |
| Unklare Spielzustände sammeln | **richtig** | Als `question`/mehrdeutig speichern; nicht automatisch als Implementierungsfehler zählen. |
| RL-Agent | **zurückgestellt** | Ein RL-Agent findet Exploits, ist aber kein Regel-Orakel. Coverage-guided Sampling ist einfacher und besser erklärbar. |
| „LLM run mit Regelwerk, um Logiklücken zu schließen“ | **nur als Kandidatengenerator** | Analyst/Testdesigner/Judge trennen; jedes harte Finding benötigt Textbeleg. |
| Catan-Scores wirken zu gut | **erklärt und geprüft** | Bei perfekten 05/06 ergibt selbst Judge `0.0` bisher noch `0.706`; der alte Plot bleibt daher nur Pilotdarstellung. Alle zwölf historischen Reviews wurden quergelesen: Scores `0.40–0.68`, jeweils 3–5 Major-Issues, u. a. abstrakter Spielplan, fehlender Spielerhandel/Häfen, unvollständige Entwicklungskarten und automatisches Abwerfen bei einer Sieben. CATAN ist Stressfall, kein hoch-fideler Erfolg. |
| Scores enthalten Noise | **bestätigt** | Einzelne Läufe nur deskriptiv; Hauptaussagen benötigen Wiederholungen und Streuung/Konfidenzintervalle. |
| Zugindex ist stateabhängig | **geklärt** | Indizes sind nur innerhalb eines Zustands gültig; Vergleiche müssen semantische Aktionsschlüssel verwenden. |
| Judge-Blindtests mit falschem Spiel | **erledigt** | Grobe und mechanisch ähnliche Mismatches wurden erkannt. Das kalibriert Identitätserkennung, nicht feine Regelkorrektheit. |
| Cross-Judge | **erledigt** | GPT- und Codex-Judges reduzieren Einzelmodellabhängigkeit, ersetzen aber keinen Goldstandard. |
| EK-Kritik teilweise menschlich falsch | **methodisch wichtig** | Kritische Findings nur mit Zitat + Code-Stelle + Zweitprüfung; alte Läufe nicht still überschreiben. |
| Alle erlauben beliebig viele Karten abzuwerfen | **nicht ungeprüft übernehmen** | Erst anhand konkreter EK-Regelstelle und reproduzierbarer Sequenz bestätigen. |
| Aktionsresultat-Verteilung / Balancing | **andere Forschungsfrage** | Misst Stärke/Balance, nicht Regeltreue; höchstens späteres Exploit-Signal. |
| Catan sprengt starke Modelle | **Stressfall** | Als dokumentierte Komplexitätsgrenze verwenden, nicht als alleinige Benchmarkbasis. |
| Mahjong/UNO/mehr Spiele | **nicht jetzt priorisieren** | Tiefe Evidenz für wenige taxonomisch gewählte Spiele ist wissenschaftlich wertvoller. |
| Bekannte Spiele in Trainingsdaten | **offen** | Titel-anonymisierte Bedingung und plausibel niedrig exponiertes Spiel (Conect) verwenden; „unseen“ nicht behaupten. Conect zeigt zugleich eine echte Spezifikationsfrage: historische Implementierungen wählen 21 oder 37 Zellen, weil die Anleitung mehrere Geometrien zeigt, aber keine eindeutige Zielgröße nennt. |
| PDF braucht Vision | **bestätigt** | Bilder sind Teil des Inputs; nun Schutz gegen veraltete Seiten. OCR/Text allein genügt nicht immer. |
| OpenGame nutzen und nur Tests schreiben | **für Hauptpfad abgelehnt** | Würde die Aufgabe „Regelwerk → Code“ umgehen; als Testdesign-Inspiration oder Kalibrierung möglich. |
| Wikipedia / fertiges Beispielspiel als Zusatzinput | **nicht im Hauptvergleich** | Verändert die Forschungsfrage und erhöht Kontaminationsrisiko; nur als klar getrennte Ablation. |
| GLM/Kimi/günstige Modelle | **GLM-Pilot erledigt** | Kosten erfassen, aber Modellpreis nicht zum Kernbeitrag machen. |
| Anleitungsscraper | **Tooling vorhanden, nachrangig** | Erst Methodik einfrieren; Masse ohne Rubriken vergrößert nur die ungelöste Bewertungsfrage. |
| Inhouse-/Cloud-LLM | **Ressourcenfrage offen** | Nur verfolgen, wenn es eine kontrollierte Modellbedingung ermöglicht. |
| Formale Angabe der KI-Nutzung | **offen, organisatorisch wichtig** | Mit Hochschule/Betreuer klären; Modelle, Versionen, Prompts und menschliche Eingriffe im Methodikteil offenlegen. |

## 5. Scoring: Diagnose und neue Regel

### Warum die bisherigen Werte zu hoch wirken

Für Spiele ohne OpenSpiel lautete die bisherige Formel sinngemäß:

```text
(4 × smoke + 10 × rollout + 10 × action-language + 10 × judge) / 34
```

Wenn Smoke, Rollout und Action-Language perfekt sind, aber der Judge `0.0` vergibt, entsteht trotzdem:

```text
(4 + 10 + 10 + 0) / 34 = 0.706
```

Damit kann ein technisch stabiles, aber regelinhaltlich völlig unzureichendes Spiel einen scheinbar guten Gesamtscore erhalten. Bei Catan sind 05 und 06 durchgehend `1.0`, während die Judges nur `0.410–0.670` vergeben; die alten Gesamtwerte von `0.826–0.903` sind daher kein Beleg für gute Catan-Regeltreue.

### Entscheidung

Es gibt für die Thesis **keinen primären Gesamtscore über ungleiche Evidenzarten**. Berichtet werden:

1. **Technical gate:** 01–04; Voraussetzung, keine Regelqualitätspunkte.
2. **Runtime robustness:** 05.
3. **Interface/action language:** 06.
4. **Rulebook scenarios:** bestandene, menschlich/zweifach bestätigte Regelfakten.
5. **Reference agreement:** 99, falls passend.
6. **LLM-judge signal:** Mittelwert und Streuung je Judge; klar als Modellurteil.
7. **Uncertainty:** unklare/nicht testbare Regeln und Judge-Widersprüche.
8. **Efficiency:** Laufzeit, Kosten, manueller Prüfaufwand.

Ein optionaler Gesamtscore darf nur **innerhalb einer homogenen Rubrik** gebildet werden, beispielsweise gewichtete Regelnachweise nach vorab festgelegtem Severity-Gewicht. Technical gates dürfen einen ungültigen Lauf ausschließen, aber keine fehlende Regeltreue kompensieren.

## 6. Evaluationsreihenfolge pro Artefakt

1. **Gate:** Datei, Syntax, Start, API (01–04).
2. **Robustheit:** Random Rollouts (05).
3. **Schnittstelle:** Action-Language (06).
4. **Regelfakten:** zitierbare Szenarien; jeder Fakt hat Quelle, Erwartung und Status.
5. **Judge:** unabhängige statische Review; Findings sind Kandidaten.
6. **Referenz:** OpenSpiel nur bei passender Version/Modellierung.
7. **Adversarial Exploration:** seltene Zustände suchen und Gegenbeispiele minimieren.
8. **Adjudikation:** nur Widersprüche, Mehrdeutigkeiten und ergebnisrelevante Findings manuell/autoritativen Quellen vorlegen.

## 7. Empfohlenes Hauptversuchsdesign

Die sechs bisherigen Spiele und Einzelruns bleiben **Pilotdaten**. Sie sind wertvoll für Fehlerklassen und Workflowentwicklung, aber wegen fehlender Wiederholungen und nachträglicher Methodikänderungen keine saubere konfirmatorische Hauptstudie.

Für die Hauptstudie ist eine kleinere, vorab festgelegte Auswahl sinnvoll:

- optional ein deterministisches OpenSpiel-Spiel zur beiläufigen Kalibrierung,
- ein deterministisches, plausibel niedrig exponiertes Spiel ohne Referenz (z. B. Conect),
- ein stochastisches/Hidden-Information-Spiel als Stressfall,
- optional ein komplexes bekanntes Spiel wie Catan nur als Belastungsgrenze.

Pro Kernspiel:

- gleiche Regelwerksedition und Hash,
- agentische Generierung als einziger neuer Hauptpfad,
- `gpt-5.6-sol:low` als dokumentierter Default; andere Modelle/Thinking-Stufen nur als explizite Bedingungen,
- mindestens drei unabhängige Generationen je zentrale Bedingung, sofern Budget möglich,
- mindestens zwei unabhängige Judges,
- vorab eingefrorene Szenarien und Severity-Regeln,
- Titel-vorhanden vs. anonymisiert als kleine Kontaminationskontrolle,
- keine Gewichtsänderung nach Sichtung der Hauptergebnisse.

„Bekanntheit“ bleibt ein Proxy, solange Trainingsdaten unbekannt sind. Ein einzelnes neueres Spiel beweist keine Trainingsdatenfreiheit.

## 8. Bereits autonom umgesetzt

- Score-Dimensionen methodisch getrennt; Plot-Redesign bis nach der Workflow-Stabilisierung vertagt,
- Berechnung zukünftiger Check-Log-Summaries berücksichtigt 05/06 korrekt,
- Pre-/Post-Align-Verhaltensguard in beide Notebooks eingebaut,
- regelbuchzitierter Szenario-Runner sowie fünf Havannah-Szenarien (inklusive terminaler Brücke und Ring) und drei Conect-Grundszenarien ergänzt,
- Judge-Prompt gegen unbelegte Regelinterpretationen geschärft,
- veraltete gerenderte Rulebook-Seiten beim Spielwechsel abgesichert,
- aktuell falsche Bildseiten und eine bitidentische Conect-PDF-Dublette entfernt,
- zentrale Thesis-Richtung und Repo-Entscheidungen dokumentiert,
- agentischen pi-Skill-Workflow (`bb`, `bbedge`, `bbimpl`, `bbeval`) angelegt,
- `@tintinweb/pi-subagents` global installiert; projektlokale Rollen erben standardmäßig vom Parent und dürfen ohne expliziten Auftrag nicht stärker sein,
- Prompts und `AGENTS.md` deutlich gekürzt; alte One-shot-/Extension-Steuerung aus dem neuen Hauptpfad entfernt.

## 9. Nächste Schritte nach dieser Runde

1. Den neuen Skill-Workflow mit einem frischen Regelwerk praktisch durchlaufen und Reibung entfernen.
2. Die begonnenen Regelfakt-Suiten für Havannah und Conect auf jeweils 10–20 validierte Fakten erweitern.
3. Mindestens 5–10 je Spiel ausführbar machen; bei Conect zuerst Brettgröße/Geometrie adjudizieren, dann Siegbedingungen testen.
4. Ein kleines Goldset aus absichtlich mutierten Implementierungen erstellen und messen, welche Evaluationsschicht welchen Fehler findet.
5. Erst danach coverage-guided Exploration ergänzen.
6. Hauptstudie und Wiederholungszahl vor dem nächsten großen Generationsblock einfrieren.

## 10. Fragen, die gemeinsam entschieden werden müssen

1. **Welches Anspruchsniveau gilt für die Hauptstudie:** drei tiefe Kernspiele mit Wiederholungen oder mehr Spiele mit nur deskriptiven Einzelruns?
2. **Darf eine menschlich validierte Rubrik als Goldstandard dienen**, oder werden offizielle Autoren-/Verlagsklärungen für strittige Kernregeln erwartet?
3. Welche formalen Hochschulregeln gelten für Offenlegung und Eigenständigkeit bei KI-generiertem Code, Judges und Textunterstützung?
4. Reicht `thinking=low` als festes Hauptsetting, wenn Eskalationen nur als dokumentierte Reparaturläufe erfolgen?

Bis zum nächsten Zwei-Wochen-Termin (voraussichtlich um den 24.07.2026) ist der sinnvolle Stand: **den neuen agentischen Skill-Workflow an einem frischen Regelwerk praktisch testen, Reibung dokumentieren und Pilotfehler in belegbare Rubriken überführen, aber keine weitere breite Hauptserie starten.**
