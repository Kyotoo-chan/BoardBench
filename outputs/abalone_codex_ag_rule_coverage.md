# Rule coverage audit

Only `game_rules.pdf` and the four freshly rendered rulebook pages were used as rule evidence. Coordinates are an internal axial labeling of the pictured 61 hollows.

| Supplied section / named rule | Implementing symbol | Source-only probe or disposition | Assumption |
|---|---|---|---|
| **Spielanleitung / Ein Spiel für 2 Spieler** | `GameState.player`, `Game.current_player` | Initial state has one active colour and turns alternate after each move. | None |
| **Ziel des Spieles**: first to push six opposing balls off | `Game.is_terminal`, `Game.returns`, `Game.apply_action` | Constructed states with six ejected balls terminate and award only the other colour. | None |
| **Vorbereitung**, Figure 1: pictured starting positions | `Game.initial_state` | Initial state has 14 black and 14 white balls in the pictured 5-6-3 opposing formation. | None |
| **Vorbereitung**: draw which player receives which colour | Players are represented by their assigned colour (`0` Schwarz, `1` Weiß). | The draw assigns humans to roles but does not alter the game state after assignment. | None |
| **Der Spielablauf**: alternate; Schwarz begins | `Game.initial_state`, `Game.apply_action`, `Game.current_player` | Initial player is Schwarz; every accepted action switches colour. | None |
| One **Bewegung** per turn; own balls only | `Game.legal_actions`, `Game.apply_action` | Actions contain one group belonging to the active colour; transition is atomic. | None |
| Movement reaches only the next hollow | `DIRECTIONS`, `_add`, `Game.legal_actions` | Every destination is exactly one neighboring axial coordinate. | None |
| Six possible directions | `DIRECTIONS` | Six distinct adjacent vectors are enumerated. | None |
| Adjacent hollow must be free | `Game.legal_actions` | Ordinary line/side moves require empty destinations; Sumito is the expressly covered exception. | None |
| Move one, two, or three balls; multi-ball groups share one direction | `Game._groups`, `Game.legal_actions` | Generated groups have length 1–3 and one direction field. | None |
| No more than three balls of one colour per move; longer row may be split | `Game._groups` | Four-ball fixture yields only its contiguous 1–3 subsets, never a four-ball action. | None |
| Two movement types; Figure 2 **Bewegung in gerader Linie** | `Game.legal_actions`, `Game.action_to_name` | Inline translation into the next empty hollow is generated with the source label. | None |
| Figure 3 **Bewegung zur Seite** | `Game.legal_actions`, `Game.action_to_name` | Broadside translation is generated only when every translated hollow is in-board and empty. | None |
| Completed movement cannot be changed | `Game.apply_action` | Immutable `GameState`; an action makes one complete transition. | None |
| **Sumito**: numerical superiority; Figure 4 named 2-zu-1, 3-zu-1, 3-zu-2 | `Game.legal_actions`, `Game.apply_action` | Source fixtures for all three ratios produce an inline push and shift each attacked ball once. | None |
| Sumito only in a straight line, balls directly adjacent, free hollow behind attacked balls | `Game.legal_actions` | Push scan requires a contiguous opposing chain and then empty in-board space or the off-board ejection case. | None |
| Figure 5 no Sumito: no free hollow; gap; not a straight line | `Game.legal_actions` | Each stated blocker fails the contiguous-inline-and-free-beyond predicate. | None |
| A possible Sumito need not be used | `Game.legal_actions` | Legal actions include all other legal groups/directions alongside a push. | None |
| **Patt**: equal numbers give neither player an advantage | strict `count < len(group)` in `Game.legal_actions` | Equal 1-1, 2-2, and 3-3 inline fixtures have no push action. | None |
| Figure 6 named 1-zu-1, 2-zu-2, 3-zu-3 Patt | `Game.legal_actions` | Each named equality is covered by the same strict-superiority probe. | None |
| More than three in a Patt are not counted; 4-zu-3 is 3-zu-3 | maximum group size in `Game._groups` | A four-ball row cannot create numerical strength greater than three. | None |
| Break Patt by attacking over another straight line / angle; Figure 7 lines a-b and c-d | ordinary `Game.legal_actions` generation | Legality is recomputed for every group and direction, so a different-axis superior attack is available when its cells satisfy Sumito. | None |
| **Hinausschieben**, Figure 8: ball leaves game when pushed over edge | `Game.apply_action`, `GameState.ejected` | Edge Sumito removes the outer opposing ball and increments its colour's ejected count. | None |
| **Wer gewinnt?** first player to push six opposing balls out wins | `Game.is_terminal`, `Game.returns`, terminal guard in `Game.legal_actions` | On sixth ejection the mover receives +1; terminal legal actions are empty. | None |
| **Gegen die Zeit**: optional allotted time (examples 10/15 minutes; official competitions use a clock) | Not modeled | This is an optional external timing mode, and the source supplies no timeout transition or result. Omitting it does not choose a legal-action, transition, scoring, or terminal rule for the supplied complete game. | None |
| Figures 1–8 | Symbols listed in the corresponding rows above | Every captioned figure is accounted for as setup, movement, Sumito/Patt example, alternate-axis attack, or ejection probe. | None |

No chance event remains after players have been assigned colours, and the source specifies no private information.
