# Einschätzung zur BoardBench-Checkliste

Stand: 2026-06-03

Diese Einschätzung bezieht sich auf `boardbench_checkliste.md`.
Die Checkliste ist als Ideensammlung sehr nützlich, aber für den aktuellen Bachelor- und Repo-Stand zu groß, wenn alles sofort als Framework umgesetzt würde.
Sinnvoll ist deshalb: die stabilisierenden Teile jetzt klein einbauen, forschungsnahe Entscheidungen sichtbar halten und die großen Automatisierungsblöcke erst nach einem Pilotlauf konkretisieren.

## Direkt umgesetzt

- `code/input/prompt.txt` fordert jetzt eine etwas klarere minimale Spiel-API, kanonische Aktionsnamen, Standardbibliothek-only und keine I/O-/Netz-/Subprozess-Nutzung ein.
- `CURRENT.md`, `workflow_description.md` und die lokale pi-Extension wurden nur dort angepasst, wo die neue Checklisten-Einschätzung sichtbar sein sollte.

Nicht umgesetzt wurden zusätzliche Dateien wie ein eigener Output-Vertrag oder eine separate Evaluation-Template-Datei, weil das Repo bewusst klein bleiben soll. Die nötigen Hinweise stehen im Prompt, in `code/evaluation_draft.md` und in dieser Einschätzung.

## Was jetzt besonders sinnvoll ist

### 1. Minimale API im Prompt

Der wichtigste direkte Punkt aus der Checkliste ist eine klare Schnittstelle.
Dafür braucht es aktuell keine eigene Vertragsdatei; die gewünschte Schnittstelle kann im bestehenden Prompt stehen.
Ohne eine solche minimale API werden spätere Vergleiche unnötig schwer, selbst wenn die generierte Logik gut ist.
Die Pflichtmethoden aus der Checkliste sind deshalb sinnvoll, aber bewusst klein gehalten:

- `initial_state`
- `current_player`
- `legal_actions`
- `apply_action`
- `is_terminal`
- `returns`
- `render`
- `action_to_name` / `name_to_action`

Wichtig ist hier besonders die Aktion-zu-Name-Brücke, weil spätere Vergleiche nicht von zufälligen Aktionsindizes abhängen sollten.

### 2. Prompt härter auf Artefaktqualität ausrichten

Die Prompt-Regeln zu Standardbibliothek-only, keine externen Dateien, keine Interaktion und keine fremden Spielkenntnisse sind sofort hilfreich.
Sie reduzieren frühe Fehler, ohne schon einen großen Harness zu bauen.

### 3. Manuelle Gate-Checks vor Scoring

Für den aktuellen Stand ist eine kleine manuelle Auswertung besser als ein vollständiges Scoring-System.
Erst sollte festgehalten werden, ob ein Modul überhaupt parsebar, importierbar, instanziierbar und schrittweise ausführbar ist.
Danach kommt der eigentliche Regelabgleich.

### 4. Artefakt-Erhaltung

Die Checkliste passt gut zur bisherigen Repo-Philosophie: Rohantwort, extrahierter Code, Annahmen und Beobachtungen müssen erhalten bleiben.
Das ist für die spätere Thesis-Diskussion wichtiger als frühe Automatisierung.

## Was sinnvoll ist, aber erst später eingebaut werden sollte

### Einheitlicher Harness mit Tier-A/Tier-B-Orakeln

Die Idee ist methodisch stark: Tier A und Tier B sollten keine zwei Systeme sein, sondern zwei Orakelquellen über dieselbe Schnittstelle.
Trotzdem wäre ein vollständiger Harness jetzt zu früh.
Zuerst sollte ein Pilotspiel zeigen, ob der minimale Vertrag und die manuelle Auswertung funktionieren.

### OpenSpiel-Differenztests

OpenSpiel ist für Kalibrierung sehr nützlich, aber nicht für jedes Spiel verfügbar und nicht automatisch dasselbe wie „Regelwerk-Klarheit".
Sinnvoll ist später ein Adapter, der über kanonische Aktionsnamen vergleicht, nicht über rohe Aktionsindizes.
Für jetzt reicht es, diese Richtung im Prompt und in `code/evaluation_draft.md` vorzubereiten.

### Rubriken und Szenarien

Ausführbare Szenarien und PaperBench-artige Teilpunkte sind wahrscheinlich der Kern einer späteren Bewertung.
Vor dem ersten Pilotlauf sollten aber noch keine Gewichtungen festgeschrieben werden.
Zuerst muss klarer werden, welche Fehlerarten in echten Modelloutputs auftreten.

### Sandbox / Container

Generierter Code ist untrusted code.
Eine Sandbox ist wichtig, sobald mehr als manuelle, kontrollierte Smoke-Tests laufen.
Für den aktuellen manuellen Stand ist es ausreichend, das Risiko sichtbar zu halten und keine zusätzliche Automatisierung einzuführen.

### Coverage, Random-Rollouts und mehrere Läufe

Diese Punkte sind methodisch sinnvoll, aber erst nach stabiler Schnittstelle und Pilotspiel sinnvoll.
Sonst optimiert man zu früh an Metriken, bevor klar ist, was die Module überhaupt zuverlässig liefern.

## Kritisch zu hinterfragen

### Misst BoardBench wirklich Regelwerk-Klarheit?

Das ist der größte offene Punkt.
Ein schlechter Output kann am Regelwerk liegen, aber auch am Modell, an Kontamination, an Spielkomplexität oder am Prompt.
Die Arbeit braucht eine operationalisierte Definition von „klar" und sollte nicht so tun, als könne ein Score diese Faktoren automatisch trennen.

### Kontamination und bekannte Spiele

Gerade OpenSpiel-Spiele oder bekannte Klassiker können im Training von Modellen vorkommen.
Wenn die Arbeit Regelwerk-Klarheit untersuchen will, müssen obskure Spiele, Regel-Perturbationen oder Kontrollbedingungen ernsthaft geprüft werden.

### Rubrik als Ground Truth

Tier-B-Szenarien sind allgemein verwendbar, aber sie sind nicht objektiv kostenlos.
Jemand muss entscheiden, welche Regelfakten wichtig sind, und strittige Regelstellen können die Bewertung verzerren.
Doppelkodierung wäre methodisch gut, kann im Bachelor-Scope aber zu aufwendig sein.

### Scoring-Gewichte

Ein 100-Punkte-Schema ist praktisch, aber schnell scheinpräzise.
Besonders kritisch ist, ob harte technische Gates, Regelkorrektheit, Transparenz von Annahmen und OpenSpiel-Abgleich in einem Score gemischt werden sollten.
Für die erste Phase sollten Tier-A- und Tier-B-Ergebnisse getrennt bleiben.

### Chance und versteckte Information

Die Checkliste deckt Zufall und hidden information ab, aber v1 sollte wahrscheinlich deterministische Spiele mit perfekter Information bevorzugen.
Sonst wird die Schnittstelle komplex, bevor der einfache Fall verstanden ist.

### Rechtliche Fragen zu Regelwerken

Urheberrecht und Speicherung von Regeltexten/PDFs im Repo müssen geklärt werden.
Das ist kein technisches Detail, sondern kann bestimmen, welche Inputs später veröffentlicht werden dürfen.

## Empfohlene nächste Schritte

1. Ein Pilotspiel mit dem neuen Prompt laufen lassen.
2. Rohantwort, extrahierten Code und kurze manuelle Notizen in `code/outputs/` speichern.
3. Nach dem Pilotlauf prüfen, welche Gate-Checks aus `code/evaluation_draft.md` wirklich nützlich waren und welche fehlen.
4. Erst danach entscheiden, ob der nächste Schritt ein kleiner OpenSpiel-Adapter oder zuerst handgeschriebene Szenarien sein sollte.
