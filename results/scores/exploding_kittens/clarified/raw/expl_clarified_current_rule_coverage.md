# Regelabdeckung

| Gelieferter Abschnitt / benannte Regel | Implementierendes Symbol | Source-only-Probe oder Begründung | Annahme |
|---|---|---|---|
| Spielaufbau; 2–5 Spieler; Startspieler; 7 Karten + Entschärfung; Kitten/Entschärfungen im Stapel; verdeckte Hände | `Game.__init__`, `Game.initial_state`, `Game.render` | Seed-identische Zustände und Kartenmengen im Selbstcheck/gezielten Setup prüfbar | A-01 |
| Spielzug: beliebig spielen, Ziehen am Ende, Uhrzeigersinn | `legal_actions`, `apply_action`, `_draw`, `_end_one_turn`, `_next_alive` | Aktionskarte lässt Spieler aktiv; Ziehen wechselt Spieler | — |
| Spielende / Explosion / letzter lebender Spieler gewinnt | `_draw`, `is_terminal`, `returns` | Künstlicher Ein-Kitten-Stapel ohne Entschärfung liefert `+1/-1` und keine Aktionen | — |
| Entschärfung | `_draw`, Phase `insert`, `_end_one_turn` | Ziehen mit Entschärfung erzwingt explizite Position und verbraucht genau eine Karte | — |
| Hops! | `_resolve`, `_end_one_turn` | Ein Hops! reduziert zwei offene Züge auf einen | — |
| Angriff | `_resolve` | Setzt beim nächsten lebenden Spieler exakt zwei, ohne Addition | — |
| Blick in die Zukunft | `_resolve`, `GameState.preview`, `render` | Maximal drei oberste Karten nur für aktuellen Betrachter sichtbar | A-02 |
| Mischen | `_resolve`, `GameState.rng` | Seedbarer RNG; Spieler und Zug bleiben gleich; Vorschau gelöscht | — |
| Wunsch | Ankündigung, Phase `donate`, `_resolve` | Ziel explizit; Ziel wählt explizit eine vorhandene Karte | — |
| NÖ! / DOCH! / Reaktionsrunde | Phase `reaction`, `_react` | NÖ!-Parität und vollständige Runde aufeinanderfolgender Pässe; Karten werden abgelegt | — |
| Pärchen | `legal_actions`, `_announce`, `_resolve` | Gleichnamige Zweiergruppe, explizites gültiges Ziel, seedbare Zufallsauswahl | — |
| Drilling | `legal_actions`, `_announce`, `_resolve`, `TITLES` | Ziel und Titel einschließlich Exploding Kitten explizit; Fehlschlag ohne Transfer | — |
| Fünfling | `legal_actions`, `_announce`, `_resolve` | Fünf verschiedene Titel; Rücknahme vorab angekündigt, einschließlich Komponenten/Kitten | — |
| Kombinationen lösen keine Einzelwirkungen aus | `_announce`, `_resolve` nach `kind` | Kombinationspfade rufen keine Einzelkartenwirkung auf | — |
| Exploding Kitten aus Ablage per Fünfling | `_resolve` (`kind == "five"`) | Karte geht auf Hand, ohne `_draw` aufzurufen | — |
| Ziel verliert letzte Karte in NÖ!-Kette | `_resolve` für `favor`/`pair` | Leere Zielhand beendet wirksame Aktion transferlos | — |
| Verbindliche Präzisierungen 1–24 | Phasenmaschine und oben einzeln zugeordnete Symbole | Jede Präzisierung ist durch die jeweilige Zeile abgedeckt; 21 durch `rng` und verdecktes `render`, 23 durch vollständige Aktionsnamen | A-02 |
| Zombiekatze; Augenmampfende; „Katzen-Karten: 4 jeder Art“; 56 Karten | `CATS`, `ACTION_COUNTS` | Gesamtzahl 56 und fünf Spieler erzwingen rechnerisch fünf Arten zu je vier; drei fehlende Titel bleiben sichtbar als unbenannte Platzhalter | A-01 |

Die Online-Video-Aufforderung wurde nicht verwendet; sie enthält im gelieferten Text keine Regeln und externe Quellen sind ausgeschlossen.
