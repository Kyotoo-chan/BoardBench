# Rule coverage

Only the supplied German Version 1.0 rulebook is treated as rule evidence. The
environment contract and profile are used solely for representation.

| Source section / named rule | Implementing symbol | Probe or reason not probed | Assumption |
|---|---|---|---|
| Title metadata: 3–6 players, 60 cards | `Game.__init__`, `_deck` | Constructor/card inventory source probe | None |
| Es war einmal … | — | Theme/history has no game operation | None |
| Die Aufgabe | `Game._finish_round`, `Game.returns` | Exact-prediction scoring and terminal score rollout | A-02 |
| Die Vorbereitung | `Game.initial_state`, `Game._start_round` | Initial hands/dealer probe | A-01 |
| Die Charakterkarten: Menschen (blau), Elfen (grün), Zwerge (rot), Riesen (gelb) | `SUITS`, `_deck`, `_card`, `action_to_name` | Inventory and reversible-label probe | None |
| Strength 13 highest, 1 lowest | `_finish_trick` | Source-only winner fixtures | None |
| Four Zauberer always trump and above 13 | `_deck`, `_finish_trick` | Wizard-priority fixture | None |
| Four Narren never trump and below 1 | `_deck`, `_finish_trick` | Jester-only and mixed-trick fixtures | None |
| Das Verteilen der Karten | `_start_round` | Round hand-size rollout (1, 2, 3, …) | A-01 |
| Undealt cards form face-down middle stack | `_start_round`, `zones.deck` | Zone-size probe | None |
| Deal responsibility rotates clockwise | `_finish_round` | Multi-round dealer probe | None |
| Der Trumpf: reveal top stack card | `_start_round` | Ordinary/Wizard/Jester reveal fixtures via seeded states | None |
| Ordinary reveal establishes its suit as trump | `_start_round` | Suit reveal probe | None |
| Narr reveal means no trump | `_start_round` | Jester reveal probe | None |
| Zauberer reveal lets dealer choose one of four suits after viewing cards | `legal_actions`, `apply_action`, `pending` | Four-choice and phase-order probe | None |
| Last round has no stack and no trump | `_start_round` | 3/4/5/6-player final-round inventory probe | None |
| Die Vorhersage: clockwise from dealer's left; 0 through round trick count | `legal_actions`, `apply_action` | Prediction-order/range rollout | None |
| Predictions recorded openly | `players[].prediction`, `observation_to_data` | Observation probe | None |
| Der Kampf um den Stich: dealer's left leads first trick; winner leads next | `_start_round`, `_finish_trick` | Leader-transition probe | None |
| Must follow led suit if possible | `legal_actions` | Hand fixture with matching/off-suit cards | A-03 |
| If unable to follow, any color or trump | `legal_actions` | Void-suit hand fixture | None |
| Zauberer and Narren may always be played | `legal_actions` | Follow-suit hand containing specials | None |
| Highest card wins; trump beats other colors | `_finish_trick` | Winner matrix fixture | None |
| First Zauberer wins the trick | `_finish_trick` | Multiple-Wizard fixture | None |
| Wizard-led trick permits arbitrary later cards | `apply_action`, `legal_actions` | Wizard-lead fixture | A-03 |
| Narr-led trick: second card may be arbitrary; it establishes suit if suited | `apply_action`, `legal_actions` | Jester-lead fixture | A-03 |
| Narren lose every trick except all-Narr trick, where first wins | `_finish_trick` | All-Jester fixture | None |
| First round contains exactly one trick | Round-size mechanics in `_start_round` | Full first-round rollout | None |
| Vergabe der Erfahrungspunkte: exact = 20 + 10/trick | `_finish_round` | Rulebook example arithmetic probe | None |
| Miss = −10 per trick over/under prediction | `_finish_round` | Rulebook example arithmetic probe | None |
| Das Ende: final round deals all 60; maxima 20/15/12/10 | `max_round`, `_start_round` | Constructor probes for 3/4/5/6 players | None |
| Highest experience total wins | Scores retained in terminal state and `returns` | Terminal rollout; ties are not resolved by source | A-02 |
| Variante Plus/minus Eins | — | Not implemented: optional variant; profile requires `variant: base` | None |
| Variante Verdeckter Tipp | — | Not implemented: optional variant; profile requires base game | None |
| Variante Geheime Vorhersage | — | Not implemented: optional variant; profile requires base game | None |
| Variante Hellsehen | — | Not implemented: optional variant; profile requires base game | None |
| Variante Einfarbig (3 oder 4 Spieler) | — | Not implemented: optional variant; profile requires base game | None |

## Representation and source-only checks

`state_to_data` / `state_from_data`, action conversion, and
`observation_to_data` implement the evaluator profile rather than additional
rules. Private hands and the face-down deck appear only in privileged state;
each observation exposes only that player's hand, public predictions, played
cards, counts, scores, trump, and turn information.

Repeated Zauberer and Narr cards have the same source label and no
source-distinguishing identity. They therefore produce one legal action per
label while removal consumes one copy.
