# BoardBench — Überlegungs-Checkliste

Themengruppierte Checkliste der Punkte, über die man sich beim Aufbau des Benchmarks
Gedanken machen muss. Grob geordnet von der Forschungsfrage bis zur Auswertung.

> **Hinweis zur Architektur:** Tier A und Tier B sind *kein* zwei Systeme und kein Fork
> im Code. Es ist *ein* Harness mit *einer* Schnittstelle; A und B sind nur zwei
> austauschbare Orakelquellen (woher die „richtige Antwort" kommt). Tier B
> (handgeschriebene Asserts/Szenarien) ist der allgemeine, für jedes Spiel funktionierende
> Pfad. Tier A (Differenztest gegen OpenSpiel) dient nur dazu, auf den ~70 verfügbaren
> Spielen unabhängig zu beweisen, dass das Verfahren — inklusive der Rubriken — Fehler
> zuverlässig erkennt (Kalibrierung).

## 1. Einheitliche Architektur (Tier A/B = Orakel, nicht zwei Systeme)
- [ ] EIN Harness + EINE Schnittstelle für alle Spiele
- [ ] Tier A/B als austauschbare Orakelquellen, kein Code-Fork
- [ ] gemeinsames Orakel-Interface (Referenz- und Rubrik-Orakel gleiche Signatur)
- [ ] Tier A nur wo Referenz existiert; Tier B überall → der allgemeine Pfad
- [ ] Rolle Tier A: Kalibrierung/Validierung des Verfahrens
- [ ] auf Überlappungs-Spielen Tier A nutzen, um die Tier-B-Rubrik zu prüfen
- [ ] Pipeline-Stufen entkoppeln: Extraktion → Generierung → Normalisierung → Bewertung → Scoring → Report

## 2. Regelwerk-Daten & Vorverarbeitung
- [ ] Beschaffung & Lizenz/Urheberrecht der Regelwerke
- [ ] Auswahlkriterien (Typ, Komplexität); bewusst obskure Spiele gegen Kontamination
- [ ] Extraktion PDF/HTML/Scan → Text, OCR-Qualität
- [ ] Tabellen, Diagramme, Symbole, Brett-Layouts behandeln
- [ ] Definition: was zählt als „das Regelwerk" (Kernregeln, Beispiele, Komponenten?)
- [ ] Mehrdeutigkeiten & Lücken dokumentieren (Ground Truth teils strittig)
- [ ] Versionierung (Editionen, Errata)
- [ ] Metadaten je Regelwerk (Spieleranzahl, Zufall, Länge, Komplexitätsindikator)

## 3. Output-Schnittstelle (der Vertrag)
- [ ] eigene minimale Schnittstelle statt OpenSpiel-Template
- [ ] Pflichtmethoden: `initial_state`, `current_player`, `legal_actions`, `apply_action`, `is_terminal`, `returns`
- [ ] `zug_zu_name` + Umkehrung verpflichtend
- [ ] `chance_outcomes` (Chance-Spieler) für Zufall
- [ ] `information_state` für versteckte Information
- [ ] `state` opak, aber clone-/kopierbar für Rollouts
- [ ] selbst-enthaltenes Modul, deterministische Factory, kein I/O, kein Netz
- [ ] erlaubte Bibliotheken & Fehlerverhalten spezifizieren
- [ ] Schnittstelle selbst versionieren

## 4. Kanonische Zug- & Ausgangs-Repräsentation (pro Spiel)
- [ ] eindeutiges, menschenlesbares Zugformat je Spiel definieren
- [ ] von Adapter UND Modell ausgegeben
- [ ] Eindeutigkeit & Vollständigkeit (jeder Zug eindeutig benennbar)
- [ ] Normalisierung: Groß/Klein, Whitespace, Synonyme, Reihenfolge
- [ ] gleiche Brücke für Chance-Ausgänge (kanonische Ausgangsnamen)
- [ ] Erzwingung des Formats im Prompt spezifizieren

## 5. Differenztest-Mechanik (Tier-A-Orakel)
- [ ] Verhaltensäquivalenz statt Code-/State-Vergleich
- [ ] Lockstep über gemeinsame Zugnamen, nie über Indizes
- [ ] pro Schritt prüfen: legale Zugmenge, current_player, terminal, Payoffs
- [ ] Adapter OpenSpiel → eigene Schnittstelle (selbst validieren)
- [ ] Zufallsknoten: Verteilungen mit Toleranz, Ausgangsnamen abgleichen
- [ ] Verhalten bei Divergenz am Start vs. später (abbrechen/weiterlaufen)
- [ ] Spieler-Permutationen/Symmetrien beachten

## 6. Rubrik & Szenarien (Tier-B-Orakel)
- [ ] Rubrik-Struktur: hierarchisch, gradierbare Einzelpunkte (PaperBench-Stil)
- [ ] Regelfakten als ausführbare Asserts
- [ ] gezielte Szenarien für seltene Regeln, Randfälle, Endbedingungen
- [ ] Rubrik = Ground Truth: wer erstellt sie, Konsistenz, Doppelkodierung
- [ ] Invarianten: terminiert? immer legale Züge bis terminal? Determinismus? Payoff-Summen?
- [ ] LLM-as-Judge nur weiches Zusatzsignal; Judge selbst validieren
- [ ] wiederverwendbare Rubrik-Vorlagen für gängige Regelmuster

## 7. Zustands-Abdeckung & Test-Strategie
- [ ] Random-Rollouts: Anzahl, Seeds, Länge/Tiefe
- [ ] gezielte Szenarien ergänzen seltene Pfade
- [ ] Coverage-Metrik (Anteil berührter Regeln/Zustände)
- [ ] Edge-Cases: Anfang, Ende, Unentschieden, Patt, Brettrand
- [ ] Test-Trajektorien zurückhalten (gegen Gameability)
- [ ] Nicht-Determinismus in Tests kontrollieren

## 8. Scoring & Aggregation
- [ ] abgestuft statt binär (Teilpunkte)
- [ ] Gate vorab: konstruiert/läuft das Modul überhaupt?
- [ ] Metriken: Zugmengen-Übereinstimmung (Jaccard), Terminierung, Payoff-Korrektheit, Coverage
- [ ] Gewichtung: sind alle Regeln gleich wichtig?
- [ ] Tier-A- und Tier-B-Score getrennt ausweisen, nicht stillschweigend mitteln
- [ ] Aggregation pro Spiel → pro Modell → pro Regelwerk
- [ ] Umgang mit Crash/Timeout (0 / partial / ausschließen) definieren
- [ ] Unsicherheit/Konfidenz des Scores

## 9. Experiment-Design
- [ ] Achsen: Regelwerke × Modelle × Bedingungen
- [ ] Pilotspiele: deterministisch + perfekte Information zuerst
- [ ] Spiele mit/ohne OpenSpiel-Referenz für Kalibrierung wählen
- [ ] Kontaminations-Proben: Regel-Perturbation; „nur Name" vs. „volles Regelwerk"
- [ ] 2–3 Modelle (Familien/Größen/Cutoffs) für Robustheit
- [ ] mehrere Läufe je Konfiguration → Varianz quantifizieren
- [ ] Ablationen (mit/ohne Beispiel, Einzel vs. Agentic)
- [ ] Baseline(s) definieren

## 10. Reproduzierbarkeit & Artefakt-Management
- [ ] Versionen pinnen (Modell-Strings, Schnittstelle, Rubriken, OpenSpiel)
- [ ] Seeds, Logs, vollständige Roh-Outputs archivieren
- [ ] extrahierten Code separat speichern
- [ ] Annahmen & ungelöste Mehrdeutigkeiten festhalten
- [ ] Umgebungs-Spec (requirements, Container)
- [ ] Release-Plan (Repo, Daten, Code)

## 11. Validität & Risiken
- [ ] Confounder trennen: Modellfähigkeit vs. Klarheit vs. Komplexität
- [ ] Kontamination/Memorisierung (Hauptbedrohung des Klarheits-Ziels)
- [ ] Coverage-Lücken (seltene Regeln ungetestet)
- [ ] Gameability (durch zurückgehaltene zufällige Trajektorien entschärft)
- [ ] Rubrik-Subjektivität & strittige Ground Truth
- [ ] Konstruktvalidität: misst der Score wirklich „Klarheit"?
- [ ] Generalisierbarkeit über Modelle, Spieltypen, Spiele außerhalb des Samples

## 12. Praktisches, Recht & Skalierungs-Roadmap
- [ ] Urheberrecht/Nutzung der Regelwerke klären
- [ ] API-Kosten & Rechenbudget
- [ ] Zeitplan/Meilensteine, Bachelor-Scope realistisch halten
- [ ] Onboarding neuer Spiele: Aufwand pro Spiel minimieren
- [ ] gestaffelte Roadmap: v1 deterministisch → v2 Zufall (Chance-Spieler) → v3 versteckte Information
- [ ] Grenzen: imperfect-information, riesige Zustandsräume, Echtzeit/kontinuierliche Spiele
