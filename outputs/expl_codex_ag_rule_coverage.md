# Rule coverage

| Supplied section / named rule | Implementing symbol | Source-only probe / status | Assumption |
|---|---|---|---|
| So funktioniert's; explode loses, last survivor wins | `apply_action`, `is_terminal`, `returns` | Rollouts reach draws/elimination; terminal has no actions | — |
| Spielaufbau 1–7; 2-player variant | `COUNTS`, `Game.initial_state` | `profile_fixture_self_check.py` checks all 56 cards and 2–5 players | A-03 |
| Spielzug: play any number, then draw; clockwise | `legal_actions`, `_advance` | `agentic_self_check.py` rollout | — |
| Spielende; hand/deck notes | `apply_action`, `legal_actions` | Terminal and arbitrary hand sizes represented | — |
| Exploding Kitten (4) | draw branch in `apply_action` | Fixture/rollout | — |
| Entschärfung (6), secret reinsertion | draw/reinsert branches; `observation_to_data` hides deck | Fixture covers `defuse_reinsert` | — |
| Angriff (4) | `_resolve` | Legal-action rollout | A-02 |
| Hops! (4) | `_resolve` (`skip`) | Legal-action rollout | — |
| Wunsch (4) | `_resolve`, `favor_give`, `give_card` | Fixture covers `favor_give` | — |
| Mischen (4) | `_shuffle` | Seeded deterministic rollout | — |
| Blick in die Zukunft (5) | `_resolve`, player `preview` | Private observation exposes only own preview | — |
| NÖ! (5), NÖ! on NÖ!, out of turn; exclusions | reaction phase, `play_nope`, `pass_nope` | Fixture covers reaction; rollout covers legal responses | A-01 |
| Katzen-Karten, individually powerless | excluded from single-card actions | Legal-action inspection | — |
| Pärchen: any equal title, random steal | `play_pair`, `_resolve` | Canonical actions enumerate all targets | — |
| Drilling: request named card | `play_triple`, `_resolve` | Canonical actions enumerate all requests | — |
| Fünfling: five different titles, retrieve discard | `play_five`, `_resolve` | Canonical actions enumerate distinct sets/retrievals | — |
| Combination instructions replace card text | combination branches in `apply_action` | Combination cards are discarded without single-card effects | — |
| Example turn | composed effects: see future, attack, NÖ!, shuffle, draw | Not encoded as a separate scripted probe; each named effect is probed above | — |

The sheet gives no operational rule for an empty deck; its text says the deck will never become empty before all but one player explode. No invented empty-deck transition is implemented.
