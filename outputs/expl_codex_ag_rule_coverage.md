# Regelabdeckung

| Quelle / benannte Regel | Implementierendes Symbol | Probe / Begründung | Annahme |
|---|---|---|---|
| So funktioniert's; wer explodiert verliert, letzter Spieler gewinnt | `apply_action`, `is_terminal`, `returns` | Rollouts im `agentic_self_check.py`; terminale Zustände ohne Aktionen | A-05 |
| Spielaufbau 1–7; 2-Spieler-Variante | `initial_state`, `Game.__init__` | Inventar-, Hand-, Spielerzahl- und Seed-Prüfung durch Initialzustand/Profile-Check | A-01 |
| Spielzug: beliebig spielen/passen, dann ziehen; Uhrzeigersinn | `legal_actions`, `_finish_turn`, `_alive_after` | Alle legalen Aktionen werden angewandt; Ziehen beendet Zug | — |
| Exploding Kitten | `apply_action` (`draw`) | Rollout/Fixture; Eliminierung und Terminalpfad | A-05 |
| Entschärfung; geheime freie Wiedereinfügung | `legal_actions`, `apply_action` (`reinsert`) | Jede Position `0..deck_size` legal; Beobachtung verbirgt Deckreihenfolge | — |
| Angriff | `_resolve` (`attack`) | Jede legale Angriff-Aktion im Self-check | A-02 |
| Hops! | `_resolve` (`skip`) | Jede legale Hops!-Aktion im Self-check | A-02 |
| Wunsch | `_resolve`, Phase `favor_give`, `give_card` | Jede mögliche Karte des Zielspielers ist legal und wird privat gewählt | — |
| Mischen | `_resolve`, `_shuffle` | Seed kontrolliert Shuffle; Roundtrip bewahrt Chance-Zähler | — |
| Blick in die Zukunft | `_resolve`, `observation_to_data` | Nur eigener `preview` wird beobachtet | — |
| Nö!; Nö! auf Nö!; außerhalb des eigenen Zuges | Phase `reaction`, `play_nope`, `pass_nope` | Reaktions-Rollouts, Paritätsauflösung | A-03, A-04 |
| Katzen-Karten einzeln machtlos | `legal_actions` | Kein einzelnes `play_card` für Katzen-Karten | — |
| Pärchen gleicher Titel, zufälliger Diebstahl | `play_pair`, `_resolve`, `_rng` | Alle Ziele; Seed kontrolliert Zufall | — |
| Drilling, gewünschte Karte | `play_triple`, `_resolve` | Alle Kartenbezeichnungen als Wunsch; Transfer nur bei Besitz | — |
| Fünfling, fünf verschiedene Titel, Ablagekarte nehmen | `play_five`, `_resolve` | Kombinationen und vorhandene Ablagekarten werden enumeriert | — |
| Kombinationen ignorieren Kartentext | `legal_actions`, `_resolve` | Kombinationsauflösung verwendet nur Kombinationswirkung | — |
| Beispielzug | Zusammenspiel von `see_future`, `attack`, Reaktion, `shuffle`, `draw` | Kein eigener Sondermechanismus; durch Einzelregeln abgedeckt | — |
| Gut zu wissen: Handlimit keines; Stapel darf gezählt werden | fehlendes Handlimit; `observation_to_data.deck_size` | Direkte Zustands-/Beobachtungsprüfung | — |

Nicht regelbestimmte Repräsentationsfelder, Serialisierung und Fixture-Toleranz folgen ausschließlich `ENVIRONMENT_CONTRACT.md` und `GAME_PROFILE.json`.
