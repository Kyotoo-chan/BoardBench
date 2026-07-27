# Rule coverage

The supplied German rule-sheet is the sole rules source. `GAME_PROFILE.json` is used only for representation and inventory identifiers; `clarifications_v2.json` resolves the stated empty-target gap.

| Source section / named rule | Implementing symbol | Probe or limitation | Assumption |
|---|---|---|---|
| So funktioniert's; explode/lose, last survivor wins | `apply_action`, `_eliminate`, `is_terminal`, `returns` | Rollouts and terminal fixture; eliminated hand and Kitten enter discard | none |
| Spielaufbau 1–7; 2-player variant | `initial_state`, `__init__` | Inventory/count fixture for 2–5 players; seeded setup repeatable | A-03 start player |
| Spielzug: play/pass, then draw; clockwise | `legal_actions`, `apply_action`, `_advance`, `_next_alive` | Every exposed action is applied by self-check | none |
| No hand limit; deck may be counted | state model, `observation_to_data` | No hand-size restriction; deck size public | none |
| Exploding Kitten | draw branch in `apply_action`, `_eliminate` | Source-only draw/elimination path | none |
| Entschärfung; secret reinsertion at any position | draw/`defuse_reinsert`; `reinsert` actions | Fixture covers pending phase and all positions are canonical | none |
| Angriff | `_resolve_proposed` | Source-only successor obligation | A-01 stacking/owed interpretation |
| Hops! (Skip) | `_resolve_proposed`, `_advance` | Consumes one owed turn without drawing | none |
| Wunsch (Favor) | `play_card`, `favor_give`, `give_card` | Empty targets excluded per clarification | none |
| Mischen | `_shuffle`, chance counter | Seed controls every shuffle | none |
| Blick in die Zukunft | `_resolve_proposed`, `preview`, observation | Own preview only; top three in order | none |
| NÖ!; Nope a Nope; out-of-turn play | reaction phase, `play_nope`, `pass_nope` | Fixture covers reaction payload; parity resolves chain | A-02 response order |
| Katzen-Karten individually powerless | `legal_actions` | No single-card action generated | none |
| Pärchen: any equal title, random steal | `play_pair`, `_choice` | Empty targets excluded per clarification; seeded random choice | none |
| Drilling: request named card | `play_triple` | Requested card transferred only if held | none |
| Fünfling: five different titles, retrieve discard | `play_five` | Legal combinations enumerate five distinct hand titles | none |
| Combination instructions replace card text | pair/triple/five branches | Combination cards do not execute their individual text | none |
| Example turn | component actions above | Not separately scripted; it is one legal path through See Future, Attack, Nope, Shuffle, Draw | none |
| Canonical state/action/observation public contract | serialization methods | `agentic_self_check.py` and `profile_fixture_self_check.py` | evaluator representation only |
