# Rule coverage

Only the supplied two-page German rulebook is behavioral evidence. The canonical contract/profile is used solely for representation.

| Source section / named rule | Implementing symbol | Source-only probe or reason not probed | Assumption |
|---|---|---|---|
| Das Spiel… / contents and 3–6 players | `Game.__init__`, `_cards`, `SUITS` | Constructor counts and 60-card inventory exercised by both self-checks | none |
| Es war einmal… | — | Theme/history has no mechanic | none |
| Die Aufgabe | predictions, tricks and scores in `GameState`; `_finish_trick` | rollout covers prediction, trick collection, scoring | none |
| Die Vorbereitung | `initial_state`, `_deal_round` | deterministic repeated initial-state probe | A-01 |
| Die Charakterkarten: Menschen (blau), Elfen (grün), Zwerge (rot), Riesen (gelb), ranks 1–13 | `SUITS`, `_cards`, `_suit`, `_rank` | inventory/serialization fixture | none |
| Four Zauberer always trump and above 13 | `_cards`, `_finish_trick` | winner logic source inspection; stochastic rollout may not cover every combination | none |
| Four Narren never trump and below 1 | `_cards`, `_finish_trick` | all-Fool branch and ordinary candidate filtering; exhaustive combination probe omitted because not supplied test harness | none |
| Das Verteilen der Karten: round N deals N cards; undealt stack; dealer rotates clockwise | `_deal_round`, `_finish_trick`, `_next` | multi-round rollout and count fixtures | A-02 |
| Der Trumpf: reveal top stack card; suit sets trump; Fool means no trump; Wizard dealer chooses; final round no trump | `_deal_round`, `legal_actions`, `apply_action` | choose-trump phase fixture; rollout covers ordinary/Fool reveal; final-round behavior source inspection | none |
| Die Vorhersage: starts left of dealer, open predictions 0..round size, recorded | `legal_actions`, `apply_action`, observation serialization | rollout accepts every generated prediction | A-02 |
| Der Kampf um den Stich: left of dealer leads first; clockwise; follow suit if possible; otherwise discard or trump | `leader`, `legal_actions`, `apply_action` | rollout legality; targeted state fixtures reconstruct play states | A-02, A-03 |
| Zauberer/Narren may always be played, even when able to follow | `legal_actions` | legal-action source inspection and rollout | none |
| Highest card wins; Wizard above all/trump; winner leads next | `_finish_trick` | rollout plus direct branch logic inspection | none |
| First round has one trick | round-size dealing in `_deal_round` | rollout | none |
| Winner priority summary: first Wizard; else highest trump; else highest led suit | `_finish_trick` | branch logic inspection | none |
| Spezielle Rechte: Wizard-led trick permits arbitrary cards and first Wizard wins | `led_suit`, `legal_actions`, `_finish_trick` | play phase fixture plus logic inspection | A-03 |
| Fool-led: second card arbitrary; first ordinary card determines suit; Fools lose | `led_suit`, `legal_actions`, `_finish_trick` | logic inspection; wording about “second card” generalized only as stated in A-03 | A-03 |
| All Fools: first Fool wins (3- or 4-player only) | fallback in `_finish_trick` | source inspection; no exhaustive probe | none |
| Die Vergabe der Erfahrungspunkte: exact = 20 + 10/trick; miss = −10 per difference | `_finish_trick` | rollout scoring | none |
| Example rounds Thomas/Ute/Kevin | `_finish_trick` scoring formula | arithmetic corresponds to shown 20/30/−10 and cumulative 10/10/20; not encoded as named players | none |
| Das Ende: all 60 cards in last round; 6→10, 5→12, 4→15, 3→20; highest score wins | `max_round`, `_finish_trick`, `is_terminal`, `returns` | count fixtures and terminal transition logic; returns expose final scores, preserving ties because no tiebreak is supplied | none |
| Varianten: Plus/minus Eins | — | Not implemented: profile requires variant `base` | none |
| Varianten: Verdeckter Tipp | — | Not implemented: profile requires variant `base` | none |
| Varianten: Geheime Vorhersage | — | Not implemented: profile requires variant `base` | none |
| Varianten: Hellsehen | — | Not implemented: profile requires variant `base` | none |
| Varianten: Einfarbig (3/4 players) | — | Not implemented: profile requires variant `base` | none |

## Explicit source gaps

The source does not specify a tiebreak among equal highest final scores; `returns` therefore exposes raw final scores and invents no winner resolution. Identical special-card copies are one action because choosing one copy or another produces the same state transition and the source assigns no distinction between them.
