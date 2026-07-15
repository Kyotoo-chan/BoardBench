# Rule coverage audit

Evidence used: `rulebook.txt` only. The focused probes below were run as an inline
standard-library Python script importing `implementation.py`; they did not inspect
or modify the evaluator-neutral self-check.

## Main rulebook sections and named cards

| Source section / rule | Implementing symbol(s) | Source-only probe / note | Assumption |
|---|---|---|---|
| Material: 56 cards; 2–5 players | `Game.__init__`, constants, `Game.initial_state` | Constructed games for 2, 3, 4, and 5 players; checked in-play totals after mandated boxed cards | The text names only two of the five four-card cat types implied by the stated counts. Three types use explicit `Katzen-Karte (unbenannt N)` placeholders. |
| Setup: set aside 4 Exploding Kittens and 6 Entschärfungen; deal 7 plus one Entschärfung; add player-count-minus-one kittens | `Game.initial_state` | For every player count, asserted eight-card hands, one starting Entschärfung each, and the exact kitten count in deck | None |
| Two-player setup: exactly two extra Entschärfungen; 3–5 players: all remaining | `Game.initial_state` | Asserted deck Entschärfung counts 2, 3, 2, 1 for 2–5 players | None |
| Shuffle and concealed deck / hands; player 0 starts | `Game.initial_state`, `GameState.rng`, `render` | Seeded setup inspected for counts; generic rollout exercised player 0 start | `render` is from the current decision-maker's perspective because the public interface has no observer argument. Other hands render as `?`. |
| Turn: play zero or more cards, remain active after normal effects, and draw at the end | `legal_actions`, `apply_action`, `_draw`, `_resolve` | Generic rollout plus focused action probes checked that normal resolved/cancelled actions retain the active player | None |
| Pass / draw | `("draw",)`, `_draw`, `_end_single_turn` | Generic rollout repeatedly exercised draws and turn advancement | “Passen” is represented directly by `draw`, since the source defines passing as playing no card and ending by drawing. |
| Elimination and last survivor wins | `_draw`, `is_terminal`, `returns` | Forced an undefused kitten draw; asserted immediate terminal state, no legal actions, and `[-1, +1]` | None |
| No hand-size limit and empty hands continue | `GameState.hands`, `legal_actions` | Forced terminal probe began with empty hands; nonterminal empty hands retain `draw` | None |
| **Exploding Kitten** | `_draw`, `EXPLODING` | Forced both defused and undefused draws | A kitten held after Fünfling has no standalone play action; the source specifies no such action. |
| **Entschärfung** | `_draw`, `phase == "defuse"`, `("place", position)` | Forced draw with Entschärfung; checked its discard and an explicit bottom insertion | Positions are zero-based deck insertion positions (`0` top, `len(deck)` bottom), stated in the code by behavior. |
| **Hops!** | `_resolve`, `_end_single_turn` | Under two owed turns, resolved Hops! and asserted same player remained with one owed turn | None |
| **Angriff** | `_resolve` | Resolved Angriff and asserted next living player owed exactly two turns; then checked Hops! debt reduction | None |
| **Wunsch** | `legal_actions`, `_resolve`, `phase == "donate"`, `current_player` | Resolved Wunsch, asserted target became decision-maker, then explicitly donated the selected card | None |
| **Mischen** | `_resolve`, `GameState.rng` | Generic rollout exercised seeded shuffle; cancellation probe checked no immediate turn end | Shuffle distribution is `random.Random.shuffle`, the ordinary seeded shuffle permitted by rule 21. |
| **Blick in die Zukunft** | `_resolve`, `viewed_top`, `view_owner`, `render` | Mechanically covered by generic rollout; code takes `deck[:3]`, preserving order and naturally handling fewer than three | Private display is scoped to the current decision-maker in `render`. |
| **NÖ!** / chained NÖ! | `_react`, `Pending.nope_count`, reaction actions | Played one NÖ! against Mischen, completed the pass round, and asserted cancellation and both discards | Reaction order starts with the next living player clockwise and includes the actor when the cycle reaches them. This is the smallest explicit interpretation of “lebende Spieler im Uhrzeigersinn”. |
| **Zombiekatze** | `CAT_1`, generic pair/combinations logic | Title included in seeded deck and all combination enumeration | No standalone effect, as stated for cat cards. |
| **Augenmampfende** | `CAT_2`, generic pair/combinations logic | Title included in seeded deck and all combination enumeration | No standalone effect, as stated for cat cards. |

## Combinations

| Named combination | Implementing symbol(s) | Source-only probe / note | Assumption |
|---|---|---|---|
| **Pärchen**: two equal titles; random steal; no printed effect | `legal_actions`, `_announce`, `_resolve` (`pair`) | Built a two-card matching hand and a two-card target hand; asserted one seeded-random transfer | None |
| **Drilling**: three equal titles; request any title, including Exploding Kitten | `legal_actions`, `_announce`, `_resolve` (`triple`), `TITLES` | Requested and received an Exploding Kitten from a target | Target may be any other living player, including one with an empty hand, because failure to possess the requested title explicitly does nothing. |
| **Fünfling**: exactly five different titles; discard first; retrieve any discard card, including a component | `legal_actions`, `_announce`, `_resolve` (`five`), `phase == "retrieve"` | Discarded five distinct components, entered explicit retrieval, and took one component back | None |
| Fünfling may retrieve Exploding Kitten without exploding | Retrieve logic in `apply_action` | Mechanically follows the same title transfer; no draw handler is called | Not separately forced in the focused script; path is identical to the probed component retrieval. |
| Combination cards do not execute printed effects | `_announce` separates `pair`, `triple`, and `five` effect kinds | Pair/five probes used action-card components and observed only combination behavior | None |

## Binding clarifications 1–21

| # | Implementing symbol(s) | Source-only probe / note | Assumption |
|---:|---|---|---|
| 1 | `_resolve`, `_draw`, `_end_single_turn` | Normal actions retain turn; draw/Hops!/Angriff and elimination paths probed | None |
| 2 | `_resolve` (`ATTACK`) | Asserted next living player owes exactly 2 | None |
| 3 | `_resolve` (`ATTACK`) overwrites `turns_owed = 2` | Code inspection plus attack debt probe | None |
| 4 | `_end_single_turn` | Asserted one Hops! changes debt 2 to 1 without changing active player | None |
| 5 | `_draw` elimination sets next player debt to 1 | Undefused elimination path probed | None |
| 6 | `_draw` automatically consumes Entschärfung | Forced kitten draw with Entschärfung; no voluntary explosion action existed | None |
| 7 | `phase == "defuse"`, placement actions | Checked used Entschärfung in discard and explicit insertion; `list.insert` preserves other relative order | None |
| 8 | defuse placement calls `_end_single_turn` | Checked normal debt end; code preserves additional debt through `_end_single_turn` | None |
| 9 | `_resolve` (`SEE`) | `deck[:3]` and tuple storage inspected; generic rollout action closure checked | None |
| 10 | `_resolve` (`SHUFFLE`) | Code only shuffles `deck`; action cancellation/turn retention probed | None |
| 11 | `legal_actions` target filtering; `donate` phase | Explicit target-owned donation probe | None |
| 12 | pair enumeration and seeded `_resolve` random choice | Random transfer probe | None |
| 13 | triple enumeration over `TITLES`; `_resolve` | Exploding Kitten request probe | None |
| 14 | five components discarded in `_announce`; retrieval is a later explicit phase | Component retrieval probe | None |
| 15 | retrieval moves discard to hand directly | Same retrieval path inspected; it never invokes `_draw` | None |
| 16 | distinct combination effect kinds | Pair/five probes with action-card titles | None |
| 17 | `Pending.nope_count`, `_react` | Odd NÖ! cancellation probed; parity toggle directly represents arbitrary chains | None |
| 18 | `Pending.responder`, `passes`, `_next_alive` | Completed full two-player pass rounds in every focused resolution | See clockwise-order assumption under NÖ! above. |
| 19 | `is_terminal`, `legal_actions`, `returns` | Asserted terminal immediately at one survivor, no actions, winner/loser returns | None |
| 20 | `initial_state` | Exhaustively checked player counts 2–5 | Unnamed cat-title placeholder gap only. |
| 21 | per-state seeded `random.Random`; `shuffle` and `choice` | Fixed-seed setup and pair steal were reproducible | None |

## Interface and closure

`GameState` and `Game` expose all requested methods. `Action` values are immutable
tuples; `action_to_name`/`name_to_action` use readable labels with reversible URL
escaping only for delimiters. `agentic_self_check.py` checked 300 states and 840
legal actions, including deep-copy transitions, unique names, and exact round trips.

