# Rule coverage

The probes below are source-only checks encoded by `agentic_self_check.py` rollouts or direct implementation invariants. Evaluator representation fields are not treated as rule evidence.

| Supplied section / named rule | Implementing symbol | Source-only probe or reason not probed | Assumption |
|---|---|---|---|
| Players 2–10; 104 cards; ten cards each | `Game.__init__`, `Game.initial_state`, `Game._deal` | Constructor boundary and initial zone/hand counts | None |
| Spielidee: avoid bullheads | `_bullheads`, `_capture`, `returns` | Score aggregation and terminal winner invariant | A-02 only for return utility/ties |
| Spielvorbereitung | `Game._deal` | Seeded shuffle, ten-card hands, four singleton rows, remainder reserve | None |
| Vier Reihen bilden; maximum five cards | `Game._deal`, `_continue_resolution` | Every normal placement leaves rows at length ≤5 | None |
| 1. Karte ausspielen; hidden simultaneous choice; resolve ascending | `legal_actions`, `apply_action`, `_continue_resolution` | All hand cards legal at commit; revealed list sorted by card | A-01 |
| 1. Regel “Aufsteigende Zahlenfolge” | `_continue_resolution` | Eligible rows require last card lower than played card | None |
| 2. Regel “Niedrigste Differenz” | `_continue_resolution` | Selected eligible row minimizes positive difference | None |
| Example cards 14, 15, 44, 61 / Abb. 2 | `_continue_resolution` | Not separately probed: illustrative instance of rules 1–2 | None |
| 3. Regel “Volle Reihe” | `_continue_resolution`, `_capture` | Sixth card captures exactly the prior five and starts row with played card | None |
| Example cards 21, 26, 30, 36 / Abb. 3 | `_continue_resolution` | Not separately probed: illustrative instance of rule 3 | None |
| 4. Regel “Niedrige Karte” | `_continue_resolution`, `legal_actions`, `apply_action` | Low card exposes all four row choices; chosen row captured and replaced | None |
| Example cards 3, 9, 68, 83 / Abb. 4 | `_continue_resolution` | Not separately probed: illustrative instance of rule 4 | None |
| Tip: usually select fewest minus points | No enforced symbol | Advice, not a legality or transition rule | None |
| Horns = minus points: ordinary cards | `_bullheads` | Non-special card returns one | None |
| Multiples of 5: two bullheads | `_bullheads` | Modulo-5 branch | None |
| Multiples of 10: three bullheads | `_bullheads` | Modulo-10 precedence | None |
| Doubles 11, 22, …: five bullheads | `_bullheads` | Modulo-11 branch | None |
| Card 55: seven bullheads | `_bullheads` | Explicit precedence branch | None |
| Hornussenstapel; captured cards face down and never return to hand | `_capture`, `observation_to_data` | Captured identities private to owner; no transition moves them to hand | None |
| Spielende after ten hand cards | `_finish_round` | Round 10 scores game and either restarts or terminates | None |
| Record scores; new game; continue until a player has over 66 | `_finish_round`, `_deal` | Strict `> 66`; totals retained across newly shuffled games | None |
| Winner has fewest bullheads | `_finish_round`, `returns` | Winner IDs are the minimum-total players | A-02 |
| Different point target / number of games may be agreed | Not implemented | Optional pre-game agreement has no requested constructor representation beyond fixed profile target | None |
| Spieltipps examples 45 and 62 / Abb. 5–6 | No enforced symbol | Strategic advice, not additional rules | None |

Chance state is serialized by `_shuffle`, `state_to_data`, and `state_from_data`; observations redact opponents' hands, captured identities, and committed-card identities until reveal.
