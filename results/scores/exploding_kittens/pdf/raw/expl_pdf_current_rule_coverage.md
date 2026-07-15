# Rule coverage

| Supplied section / rule | Implementing symbol | Source-only probe / assumption |
|---|---|---|
| So funktioniert's; Grundsätzlich; Spielende | `apply_action`, `is_terminal`, `returns` | Rollouts probe draw, elimination, sole-survivor terminal and ±1 returns. |
| Spielaufbau steps 1–7; two-player variant | `Game.initial_state` | Counts, seven dealt cards plus one Entschärfung, n−1 kittens, player 0 start; setup shuffle probed by initial states. |
| Spielzug: play/pass then draw; clockwise | `legal_actions`, `apply_action`, `_next` | Every action checked and random rollouts exercise end-of-turn draw. “Pass” is represented directly by `Ziehen`. |
| Exploding Kitten | `apply_action` draw branch | Probe: drawing without Entschärfung eliminates player. |
| Entschärfung and secret chosen reinsertion | `phase == "insert"` | Every insertion index is an explicit action; hand secrecy is represented in state, though `render` exposes only counts. |
| Angriff (4) | `_resolve` | Explicit two-turn counter; chaining ambiguity A-02. |
| Hops! (4) | `_resolve` | Decrements one required turn without drawing. |
| Wunsch (4) | `phase == "favor"` | Target and target's donated card are explicit actions. |
| Mischen (4) | `_resolve` | Seeded standard-library shuffle. |
| Blick in die Zukunft (5) | `_resolve`, `GameState.seen` | Stores top three privately for actor without reordering. |
| NÖ! (5), including NÖ! on NÖ! and out-of-turn | `phase == "reaction"` | Explicit reaction/pass cycle; timing ambiguity A-01. Exploding Kitten and Entschärfung are excluded as stated. |
| Katzen-Karten (4 each) | `CATS`, setup | Source labels are unreadable/not stated in body text; material assumption A-03. |
| Pärchen | `legal_actions`, `_resolve` | Explicit equal title and target; random theft uses stored seeded RNG. |
| Drilling | `phase == "triple"` | Explicit equal title, target, and requested available card; “not present” action covers failure. |
| Fünfling | `legal_actions`, `_resolve` | Explicit five distinct titles and chosen discard card; card instructions are ignored as stated. |
| Beispielzug | Existing `SEE`, `ATTACK`, `NOPE`, `SHUFFLE`, draw transitions | Covered as the composition of those named mechanics; no separate scripted probe. |
| “no hand limit”; count remaining deck | State representation / `render` | No hand cap; deck size visible. Advice about retaining cards is non-binding and needs no transition. |

Validation also exhaustively clones and applies every legal action encountered by `agentic_self_check.py`.
