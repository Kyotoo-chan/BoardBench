# Catan — Implementation Brief

Scope note: this brief uses only the supplied rulebook text (KOSMOS 2022 base game, "Einsteiger"/beginner setup). Several concrete data (board graph, number chips, harbor set, dev-card composition) live only in the page-1 figure and the referenced Almanach, which are not in the text. Those are marked `not specified` and collected in §10. I could not read `open_spiel_backbone.md` (not in context); §1 add-on mapping must be cross-checked against it.

## 1. Game classification

- **Players:** 3–4 (beginner setup drawn for 4 colors: Weiß, Blau, Orange, Rot; with 3 players all Rot pieces are removed). Exact min/max not stated as a range → open question.
- **Turn structure:** mixed. Predominantly sequential/clockwise ("linker Nachbar"), with two non-sequential sub-phases: discard-on-7 (all players with >7 cards act) and player-to-player trading (interactive during the active player's turn).
- **Chance:** stochastic — 2 dice per turn; development-card draw; robber steal from a hidden hand.
- **Information:** imperfect — hidden resource hands, hidden (unplayed) development cards including secret victory-point cards, shuffled dev deck.
- **Scoring type:** competitive winner-take-all (first to ≥10 VP on own turn). Not team, not identical-interest. Model as constant-sum single-winner; VP is an internal score, not the return.
- **Scoring timing:** VP accumulates during play (step/repeated), but the game **return** is terminal (single winner). No draws are possible — the winner is whoever triggers the threshold on their own turn.
- **Likely backbone add-ons (verify against `open_spiel_backbone.md`):** N-player (>2), explicit chance nodes, imperfect-information / per-player private state, hidden-hand + hidden-role-token scoring, and — critically — a negotiation/trade add-on. If no trade add-on exists, player trading must be abstracted (see §10/§11).

## 2. Rulebook-grounded entities and labels

Board / geography:
- `Insel Catan`; `Landfelder` (19 land tiles); `Meer` / `Meerfelder` (sea frame).
- `Landschaften`: `Wald`, `Ackerland`, `Hügelland`, `Weideland`, `Gebirge`, plus `Wüste` (no yield).
- `Kreuzung` (crossing; borders ≤3 tiles), `Weg` (path/edge), `Hafen` (`3:1-Hafen`, `Spezialhafen` = 2:1 for one named resource).
- `Zahlenchip` (number chip; red 6 and 8 are the most frequent).

Resources (`Rohstoffe`) and their sources:
- `Holz` ← `Wald`; `Lehm` ← `Hügelland`; `Wolle` ← `Weideland`; `Getreide` ← `Ackerland`; `Erz` ← `Gebirge`.

Pieces / cards / tokens:
- `Siedlung` (1 VP), `Stadt` (2 VP), `Straße`; `Räuber` (robber).
- `Rohstoffkarten` (5 types, held hidden).
- `Entwicklungskarten`: `Ritter`, `Fortschritt`, `Siegpunkte` (held secret).
- `Sonderkarten`: `Längste Handelsstraße` (2 VP), `Größte Rittermacht` (2 VP).
- `Karte Baukosten`, `Würfel` (2), `Kartenhalter`/`Fächer` (bank trays).

Per-player supply (total figures): 5 `Siedlungen`, 4 `Städte`, 15 `Straßen` — of which 2 settlements and 2 roads are pre-placed at start (so 3 settlements / 13 roads / 4 cities remain in reserve).

Scores/status: `Siegpunkte` (target 10); played (face-up) `Ritter` count per player.

## 3. Proposed `GameState` fields

Public:
- Tiles[19]: `landscape`, `number_chip` (none for `Wüste`), `has_robber`.
- Board graph: tile↔crossing, crossing↔crossing (adjacency for distance rule), crossing↔edge, edge↔edge (for road runs). (Concrete graph = board data; see §10.)
- Crossings: `occupant = {none | (player, Siedlung) | (player, Stadt)}`.
- Edges (`Wege`): `occupant = {none | (player, Straße)}`.
- Harbors: crossing→`{3:1 | 2:1(resource)}`.
- `robber_tile`.
- Per player: remaining supply (settlements/cities/roads), face-up knight count, public VP portion (buildings + special cards; hidden VP dev cards excluded).
- `laengste_handelsstrasse_owner` (+ current longest length), `groesste_rittermacht_owner`.
- Dev deck size; returned-card trays (optional bank counts per resource — see §10 on depletion).
- `current_player`, `phase`, last dice result, `dev_card_played_this_turn` (bool), start/oldest player.

Private per player:
- `hand`: counts per resource (hidden).
- `dev_hand`: list of Ritter/Fortschritt/Siegpunkte (hidden), each with `bought_this_turn` flag (cannot be played same turn).

Chance / setup:
- Shuffled dev deck order.
- Fixed beginner layout (tiles, chips, harbors, robber start, and the lettered starting settlements A–D) — deterministic setup, but values are `not specified` in text.

Derived (compute, do not store):
- VP totals; producing tiles for a given roll; legal build targets (road connectivity + distance rule); longest continuous road per player; whether any player ≥10 VP.

History:
- No repetition/undo rules → none required beyond `bought_this_turn` and information-state hiding.

## 4. Turn, phase, and chance flow

Setup: build the fixed beginner board (figure). Each player has 2 pre-placed `Siedlungen` and 2 `Straßen`. **Beginner-specific:** each player draws starting resources **only for their lettered settlement (A–D)** — one card per adjacent tile (e.g., B → 1 Holz+1 Erz+1 Lehm; C → 1 Erz+2 Getreide). Oldest player starts.

Per turn, in the rulebook's fixed order:
1. **PRE_ROLL (optional):** play ≤1 dev card (incl. Ritter → move robber) — but never a card bought this turn.
2. **ROLL (mandatory, chance):** 2 dice → sum 2–12.
   - Sum = 7 → **DISCARD** (every player with >7 cards discards ⌊half⌋, round down in the player's favor: 9→4) → **ROBBER** (active player moves robber to a different land tile, steals 1 random card from an adjacent opponent). No yields this roll.
   - Else → distribute yields to **all** players: settlement adjacent to a producing tile → 1 card; city → 2 cards; the tile carrying the robber produces nothing.
3. **TRADE:** bank/maritime (4:1; 3:1 at a harbor; 2:1 at a matching special harbor) and player trades (only with the active player; other players may not trade among themselves). Repeatable while the hand allows.
4. **BUILD:** any number of builds while resources/supply allow — road / settlement / city (upgrade) / buy dev card (chance draw). Recompute `Längste Handelsstraße` after roads/splitting settlements; `Größte Rittermacht` only changes when a Ritter is played.
5. Dev card: playable at PRE_ROLL or during MAIN, **exactly once per turn**, never a card bought this turn.
6. **END:** pass to left neighbor → their step 1.

Chance nodes (must be explicit, not internally sampled):
- Dice: model as sum with 2d6 weights (2:1/36 … 7:6/36 … 12:1/36).
- Dev draw: uniform over remaining deck (composition `not specified`).
- Robber steal: uniform over the victim's hidden cards.

## 5. Legal action grammar

Use stable board IDs (`e<edge>`, `x<crossing>`, `t<tile>`) from board data; resource enum `{Holz,Lehm,Wolle,Getreide,Erz}`; player `p<i>`.

- `roll` — mandatory decision node → chance outcome `chance:dice:<sum>`.
- `chance:dev:<Ritter|Fortschritt|Siegpunkte>` — dev-draw outcome.
- `chance:steal:<resource>` — robber-steal outcome.
- `build:road:<edge>`
- `build:settlement:<crossing>`
- `build:city:<crossing>` (upgrade in place)
- `build:dev` → resolves via `chance:dev:*`
- `trade:maritime:<n>:<give>-><get>` with `n∈{4,3,2}` (2 only at matching `Spezialhafen`)
- Player trade (needs a bounded protocol — see §10/§11): `offer:p<i>:give=<multiset>:get=<multiset>`, `accept`, `reject`, `counter:...`
- `robber:move:<tile>` then `robber:steal:p<i>` → `chance:steal:*`
- `discard:<multiset>` (one per over-limit player on a 7)
- `play:knight` (→ robber move+steal), `play:progress:<which>` (effect `not specified`)
- `pass` / `end_turn`

Note: `Siegpunkte` dev cards are **not "played"** — they stay secret and only count toward the win, revealed at 10 VP. No play action.

`name_to_action` reverse: split on `:`, dispatch on prefix (`build|trade|robber|play|discard|chance|roll|pass`), then parse typed fields — edge/crossing/tile IDs against the board table, resource enum, player index, and multisets like `2Getreide+1Erz`. Round-trip requires the stable ID scheme in §10.

## 6. State transition rules

- **roll:** resolve dice chance. On 7 → set DISCARD/ROBBER; else credit yields (settlement +1, city +2 per matching adjacent tile; skip the robber's tile) to every player's hidden hand.
- **build:road:** validate edge empty; adjacent to own road/settlement/city; not blocked by a foreign settlement/city on the connecting crossing; supply>0; pay 1 Lehm+1 Holz. Place road; recompute longest road → maybe reassign `Längste Handelsstraße` (see §10 on ties/break).
- **build:settlement:** validate crossing empty; ≥1 own road leads to it; **distance rule** — all three neighboring crossings empty (any owner); supply>0; pay Lehm+Holz+Wolle+Getreide. Place settlement (+1 VP); may split an opponent's road run.
- **build:city:** validate crossing holds own settlement; city supply>0; pay 3 Erz+2 Getreide. Return settlement to supply, place city; VP +1 net (1→2); doubles future yields there.
- **build:dev:** pay Erz+Wolle+Getreide; draw top card (chance); add to hand with `bought_this_turn=true`.
- **trade:maritime:** validate ratio (4:1 always; 3:1 only with a 3:1 harbor settlement; 2:1 only with the matching special-harbor settlement) and that `give` are identical where required; move cards hand↔bank.
- **player trade:** both sides hold the offered cards; only active player ↔ one other; swap on accept. (Protocol constraints `not specified`.)
- **discard:** validate multiset size = ⌊hand/2⌋ and cards owned; return to bank.
- **robber:move + steal:** target tile ≠ current robber tile and is a land tile; victim has a settlement/city on that tile and ≥1 card; move 1 random card victim→active.
- **play:knight:** mark dev played; robber move+steal; increment face-up knight count; if ≥3 and strictly more than current holder → assign `Größte Rittermacht`.
- **play:progress:** apply text effect (`not specified`), remove card from game; mark dev played.
- **end_turn:** clear `dev_card_played_this_turn`, clear `bought_this_turn` flags, advance current player; check terminal at start/appropriate point of the acting player's turn.

## 7. Terminal conditions and returns

- **Terminal:** exactly when the **active** player has ≥10 VP during their own turn (buildings + Längste Handelsstraße 2 + Größte Rittermacht 2 + hidden Siegpunkte cards). A hidden VP card may complete the 10 and win immediately on that player's turn; a player cannot win on someone else's turn.
- **Returns (modeling choice — text gives no payoffs):** pre-terminal returns = 0 for all. At terminal, recommend zero-sum winner-take-all: winner +1, each other player −1/(N−1); alternative winner 1 / others 0. VP is **not** the return.

## 8. Rendering and player-visible information

`render(state)`: hex map with each tile's landscape, number chip, and robber marker; crossings with settlement/city + owner color; edges with roads + owner; harbors; per-player public VP, remaining supply, face-up knights; owners of both Sonderkarten; dev-deck size; current player, phase, last dice.

`information_state(state, player)`: everything public above **plus** that player's own `hand` and full `dev_hand` (incl. secret Siegpunkte). Must hide: every other player's resource hand and unplayed dev cards, the dev-deck order, and the identity of a card being stolen (revealed only to the two involved players per the "verdeckt in der Hand" rule).

## 9. Minimal scenario tests

1. **Initial legal actions:** at a turn's PRE_ROLL, legal = `{play:knight/play:progress if a non-fresh dev card is held, roll}`; `roll` is mandatory before TRADE/BUILD.
2. **Normal yield (rulebook):** roll `3` → Wald+Gebirge produce; White settlement (D) on the 3-Wald → 1 Holz; Blue (B) and Orange (C) on the 3-Gebirge → 1 Erz each. Roll `8` → Red +2 Erz (two settlements), White +1 Erz; roll `10` → White +1 Wolle, or +2 Wolle if that settlement is a city.
3. **Illegal action:** `build:settlement:<x>` where a neighboring crossing is occupied (distance rule) — matches the "rot markierte Kreuzungen" example; likewise `build:road:<e>` on an occupied edge or one not connected to the player's network ("rot markierter Weg").
4. **Longest-road split (rulebook):** Red's 6-road continuous run (branch excluded) holds `Längste Handelsstraße`; a Red settlement splits Orange's 7 roads into runs of 2 and 5.
5. **Chance/hidden (rulebook):** roll `7` → each player with >7 cards discards ⌊half⌋ (9→4); active player moves robber to a new land tile and steals 1 random card from an adjacent opponent; while the robber sits on a tile, that tile yields nothing.

## 10. Open questions / assumptions

Board & setup (blocking, all in figures not text):
- Exact tile positions and the crossing/edge adjacency graph; stable ID scheme for round-tripping actions.
- Beginner layout: tile-type placement, number-chip assignment, harbor set/positions, robber start tile (Wüste?), and the lettered starting settlements/roads A–D per color.
- Full number-chip set (which numbers 2–12, counts of each).

Cards & bank:
- Dev-deck composition (counts of Ritter/Fortschritt/Siegpunkte), the specific `Fortschritt` effects, and VP value per `Siegpunkte` card (assumed 1, not stated).
- Resource-card counts per type in the bank and behavior on depletion.
- Harbor specifics: which resources have `Spezialhafen` (2:1), how many, where.

Rules needing clarification:
- Player-trade protocol: what is a legal offer, how many rounds, whether bank+player trades combine, and whether it can be reduced to a finite action set. (Biggest modeling gap.)
- Robber: victim selection when multiple opponents are adjacent; behavior when no adjacent opponent or none holds cards (assume no steal). Text does confirm the robber must move to a **different land tile**.
- Special-card dynamics: reassignment/removal when the longest road is broken below 5 or by a foreign settlement, and tie handling (text specifies "strictly longer/more" to take a card, and thresholds 5 / 3; behavior on dropping below is unstated).
- Discard-on-7: simultaneous vs. sequential resolution and confirmation that the player chooses which cards (assumed yes); active roller also discards (text: "alle Spieler").
- Trade-then-build ordering: rulebook lists them as ordered phases (2 then 3); whether interleaving is allowed is unstated.
- Confirm exactly one dev card played per turn and that `Siegpunkte` cards are never "played," only revealed at 10.

Do not silently resolve these; surface the assumptions above to the coding step.

## 11. Implementation risks

- **Player trading modeled unsoundly** — free negotiation is not a finite action set. Recommend v1 = maritime/bank trades only (concrete actions), with player trade behind a bounded propose/accept protocol added later; otherwise the action space explodes or leaks.
- **Longest-road computation** — longest *simple* path over the road subgraph with branches excluded and foreign settlements/cities cutting runs; easy to over/undercount. Own buildings do **not** cut a run; only foreign ones do.
- **Largest-army bookkeeping** — threshold 3 and strict-majority reassignment on each `play:knight`.
- **Hidden-information leakage** — opponents' hands, unplayed dev cards, deck order, and the stolen card's identity must never surface in public state or another player's information state.
- **Chance not explicit** — dice, dev draw, and robber steal sampled internally instead of as chance nodes.
- **Incomplete legal-move generation** — distance rule, road connectivity, harbor eligibility, supply limits, "can't play a dev card bought this turn," and robber-must-move-to-a-different-tile.
- **Terminal timing** — declaring a winner off-turn, or failing to count a hidden `Siegpunkte` card that completes 10 on the player's own turn.
- **Discard-on-7** — wrong threshold (must be **>7**, i.e. ≥8), wrong rounding (down, in the player's favor), or forcing card choice arbitrarily.
- **Action round-trip** — names depend on a stable board-ID scheme that the text does not provide (§10).
- **Returns definition** — winner-take-all payoff is a modeling decision, not in the rulebook; pre-terminal returns must be 0.
