Open questions / assumptions:
- Single-deal implementation, not full four-round Partie wind rotation.
- Third numbered suit is named `zeichen`; dragons are red/green/white.
- Dice/wall-break geometry is abstracted into explicit chance draws.
- Bonus tiles are optional and disabled by default.

```python
"""
Self-contained implementation of the German Mah-Jongg rule text supplied to the
agent.  The module models one deal (one "Spiel"), not the complete four-round
Partie.

Assumptions forced by gaps in the source text are kept explicit:
* The rulebook names Bambus and Kreis tiles but does not name the third numbered
  suit; this file calls it "zeichen".
* The rulebook refers to dragons, and specifically to the green dragon, without
  listing all dragon labels; this file uses red/green/white dragon labels.
* Initial dice, exact wall break geometry, and player wind drawing are abstracted
  into chance draws from the remaining tile multiset.  Player 0 is East, then
  South, West, North counter-clockwise.
* Bonus-tile play is optional.  By default bonus tiles are left out, as allowed
  by the rulebook's simplification note.  When enabled, flower/season replacement
  draws are modelled from the same remaining multiset rather than a geometrically
  exact dead wall.
* Claim conflicts are resolved by explicit priority opportunities in the order
  stated by the rule text: Mah-Jongg claims, Kang, Pong, then Tschi by the right
  neighbour.  Ties inside one priority are offered in seating order from the
  discarder's right.
* Scoring implements the printed tables as far as the final state makes them
  observable.  Ambiguous/context-only bonuses are documented in comments near the
  relevant code.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

TERMINAL = -1
CHANCE = -2
SIMULTANEOUS = -3

NUM_PLAYERS = 4
WINDS = ("ost", "sued", "west", "nord")
SUITS = ("bambus", "kreis", "zeichen")
DRAGONS = ("drache-rot", "drache-gruen", "drache-weiss")
FLOWERS = ("blume-1", "blume-2", "blume-3", "blume-4")
SEASONS = ("jahreszeit-1", "jahreszeit-2", "jahreszeit-3", "jahreszeit-4")

NORMAL_TILES: Tuple[str, ...] = tuple(
    [f"{suit}-{rank}" for suit in SUITS for rank in range(1, 10)]
    + [f"wind-{wind}" for wind in WINDS]
    + list(DRAGONS)
)
BONUS_TILES: Tuple[str, ...] = FLOWERS + SEASONS
ALL_TILE_TYPES: Tuple[str, ...] = NORMAL_TILES + BONUS_TILES

ORPHANS: Tuple[str, ...] = tuple(
    [f"{suit}-1" for suit in SUITS]
    + [f"{suit}-9" for suit in SUITS]
    + [f"wind-{wind}" for wind in WINDS]
    + list(DRAGONS)
)

GREEN_TILES = {"bambus-2", "bambus-3", "bambus-4", "bambus-6", "bambus-8", "drache-gruen"}


def _is_suited(tile: str) -> bool:
    return tile.split("-", 1)[0] in SUITS and _tile_rank(tile) is not None


def _tile_suit(tile: str) -> Optional[str]:
    head = tile.split("-", 1)[0]
    return head if head in SUITS else None


def _tile_rank(tile: str) -> Optional[int]:
    parts = tile.rsplit("-", 1)
    if len(parts) == 2 and parts[0] in SUITS:
        try:
            value = int(parts[1])
        except ValueError:
            return None
        return value if 1 <= value <= 9 else None
    return None


def _is_wind(tile: str) -> bool:
    return tile.startswith("wind-") and tile[5:] in WINDS


def _wind_index(tile: str) -> Optional[int]:
    if not _is_wind(tile):
        return None
    return WINDS.index(tile[5:])


def _is_dragon(tile: str) -> bool:
    return tile in DRAGONS


def _is_honor(tile: str) -> bool:
    return _is_wind(tile) or _is_dragon(tile)


def _is_bonus(tile: str) -> bool:
    return tile in BONUS_TILES


def _is_terminal(tile: str) -> bool:
    rank = _tile_rank(tile)
    return rank in (1, 9)


def _is_simple_suited(tile: str) -> bool:
    rank = _tile_rank(tile)
    return rank is not None and 2 <= rank <= 8


def _is_major(tile: str) -> bool:
    return _is_honor(tile) or _is_terminal(tile)


def _tile_sort_key(tile: str) -> Tuple[int, int, str]:
    suit = _tile_suit(tile)
    if suit is not None:
        return (SUITS.index(suit), _tile_rank(tile) or 0, tile)
    if _is_wind(tile):
        return (10, WINDS.index(tile[5:]), tile)
    if _is_dragon(tile):
        return (11, DRAGONS.index(tile), tile)
    if tile in FLOWERS:
        return (12, FLOWERS.index(tile), tile)
    if tile in SEASONS:
        return (13, SEASONS.index(tile), tile)
    return (99, 0, tile)


def _sorted_tiles(tiles: Iterable[str]) -> List[str]:
    return sorted(tiles, key=_tile_sort_key)


def _make_tile_counts(include_bonus_tiles: bool) -> Dict[str, int]:
    counts = {tile: 4 for tile in NORMAL_TILES}
    if include_bonus_tiles:
        for tile in BONUS_TILES:
            counts[tile] = 1
    return counts


@dataclass(frozen=True)
class Meld:
    """A declared or inferred figure used for play and scoring."""

    kind: str  # "chi", "pong", or "kang"
    tiles: Tuple[str, ...]
    concealed: bool = False
    source_player: Optional[int] = None

    def label(self) -> str:
        exposure = "verdeckt" if self.concealed else "offen"
        return f"{exposure}-{self.kind}:{'+'.join(self.tiles)}"


@dataclass(frozen=True)
class ScoreBreakdown:
    value: int
    base: int
    doubles: int
    limit_hands: Tuple[str, ...] = ()
    notes: Tuple[str, ...] = ()


@dataclass
class GameState:
    phase: str = "deal"
    current: int = CHANCE
    hands: List[List[str]] = field(default_factory=lambda: [[] for _ in range(NUM_PLAYERS)])
    melds: List[List[Meld]] = field(default_factory=lambda: [[] for _ in range(NUM_PLAYERS)])
    bonus: List[List[str]] = field(default_factory=lambda: [[] for _ in range(NUM_PLAYERS)])
    dead_discards: List[List[str]] = field(default_factory=lambda: [[] for _ in range(NUM_PLAYERS)])
    remaining: Dict[str, int] = field(default_factory=dict)

    dealer: int = 0
    round_wind: int = 0
    player_winds: Tuple[int, int, int, int] = (0, 1, 2, 3)
    include_bonus_tiles: bool = False
    limit: int = 500

    deal_index: int = 0
    draw_for: Optional[int] = None
    draw_source: str = "wall"  # "wall" or "dead" in the scoring vocabulary.

    last_draw_player: Optional[int] = None
    last_draw_tile: Optional[str] = None
    last_draw_source: str = "wall"
    last_draw_was_final: bool = False

    last_discard: Optional[Tuple[int, str]] = None
    discard_after_final_draw: bool = False
    last_discard_was_first_east: bool = False
    first_discard_made: bool = False

    claim_groups: List[Tuple[int, Tuple[str, ...]]] = field(default_factory=list)
    claim_index: int = 0
    pending_kong: Optional[Tuple[int, int, str]] = None  # owner, meld index, tile
    kongs_in_current_turn: int = 0

    terminal: bool = False
    winner: Optional[int] = None
    win_source: Optional[str] = None  # "wall", "dead", "discard", "rob_kang"
    winning_tile: Optional[str] = None
    winning_from: Optional[int] = None
    win_on_last_wall_tile: bool = False
    east_consecutive_wins: int = 0

    history: List[str] = field(default_factory=list)

    def copy(self) -> "GameState":
        return GameState(
            phase=self.phase,
            current=self.current,
            hands=[list(hand) for hand in self.hands],
            melds=[list(meld_list) for meld_list in self.melds],
            bonus=[list(items) for items in self.bonus],
            dead_discards=[list(items) for items in self.dead_discards],
            remaining=dict(self.remaining),
            dealer=self.dealer,
            round_wind=self.round_wind,
            player_winds=tuple(self.player_winds),
            include_bonus_tiles=self.include_bonus_tiles,
            limit=self.limit,
            deal_index=self.deal_index,
            draw_for=self.draw_for,
            draw_source=self.draw_source,
            last_draw_player=self.last_draw_player,
            last_draw_tile=self.last_draw_tile,
            last_draw_source=self.last_draw_source,
            last_draw_was_final=self.last_draw_was_final,
            last_discard=self.last_discard,
            discard_after_final_draw=self.discard_after_final_draw,
            last_discard_was_first_east=self.last_discard_was_first_east,
            first_discard_made=self.first_discard_made,
            claim_groups=[(p, tuple(actions)) for p, actions in self.claim_groups],
            claim_index=self.claim_index,
            pending_kong=self.pending_kong,
            kongs_in_current_turn=self.kongs_in_current_turn,
            terminal=self.terminal,
            winner=self.winner,
            win_source=self.win_source,
            winning_tile=self.winning_tile,
            winning_from=self.winning_from,
            win_on_last_wall_tile=self.win_on_last_wall_tile,
            east_consecutive_wins=self.east_consecutive_wins,
            history=list(self.history),
        )


class Game:
    """One-deal Mah-Jongg game engine following the supplied German rule text."""

    def __init__(
        self,
        include_bonus_tiles: bool = False,
        limit: int = 500,
        round_wind: str = "ost",
        dealer: int = 0,
    ) -> None:
        if dealer not in range(NUM_PLAYERS):
            raise ValueError("dealer must be a player index 0..3")
        if round_wind not in WINDS:
            raise ValueError(f"round_wind must be one of {WINDS}")
        self.num_players = NUM_PLAYERS
        self.include_bonus_tiles = include_bonus_tiles
        self.limit = int(limit)
        self.dealer = dealer
        self.round_wind = WINDS.index(round_wind)
        # In one isolated deal, seating is fixed with East at player 0 unless a
        # caller constructs a state manually.  The rulebook's wind rotation is a
        # multi-game procedure and is outside this one-deal API.
        self.player_winds = (0, 1, 2, 3)

    # ------------------------------------------------------------------
    # Basic API
    # ------------------------------------------------------------------

    def initial_state(self) -> GameState:
        return GameState(
            phase="deal",
            current=CHANCE,
            remaining=_make_tile_counts(self.include_bonus_tiles),
            dealer=self.dealer,
            round_wind=self.round_wind,
            player_winds=self.player_winds,
            include_bonus_tiles=self.include_bonus_tiles,
            limit=self.limit,
        )

    def current_player(self, state: GameState) -> int:
        if state.terminal or state.phase == "terminal":
            return TERMINAL
        if state.phase in ("deal", "draw", "draw_replacement"):
            return CHANCE
        if state.phase in ("claim", "rob_kong"):
            if 0 <= state.claim_index < len(state.claim_groups):
                return state.claim_groups[state.claim_index][0]
            return TERMINAL if state.terminal else CHANCE
        return state.current

    def legal_actions(self, state: GameState, player: Optional[int] = None) -> List[str]:
        if self.is_terminal(state):
            return []
        if state.phase in ("deal", "draw", "draw_replacement"):
            return [action for action, _prob in self.chance_outcomes(state)]
        if state.phase == "discard":
            p = state.current if player is None else player
            if p != state.current:
                return []
            return self._discard_phase_actions(state, p)
        if state.phase in ("claim", "rob_kong"):
            if not (0 <= state.claim_index < len(state.claim_groups)):
                return []
            p, actions = state.claim_groups[state.claim_index]
            if player is not None and player != p:
                return []
            return list(actions) + ["pass"]
        return []

    def apply_action(self, state: GameState, action: str) -> GameState:
        legal = self.legal_actions(state)
        if action not in legal:
            raise ValueError(f"illegal action {action!r} in phase {state.phase}; legal actions: {legal[:20]}")
        if state.phase in ("deal", "draw", "draw_replacement"):
            return self._apply_chance_draw(state, action)
        if state.phase == "discard":
            return self._apply_discard_phase_action(state, action)
        if state.phase == "claim":
            return self._apply_claim_action(state, action)
        if state.phase == "rob_kong":
            return self._apply_rob_kong_action(state, action)
        raise ValueError(f"unsupported phase {state.phase!r}")

    def is_terminal(self, state: GameState) -> bool:
        return state.terminal or state.phase == "terminal"

    def returns(self, state: GameState) -> List[float]:
        if not self.is_terminal(state) or state.winner is None:
            return [0.0 for _ in range(NUM_PLAYERS)]
        scores = [self.score_breakdown(state, p).value for p in range(NUM_PLAYERS)]
        winner = state.winner
        totals = [0 for _ in range(NUM_PLAYERS)]

        # All players pay the Mah-Jongg caller.  East pays and receives double.
        for p in range(NUM_PLAYERS):
            if p == winner:
                continue
            factor = 2 if (p == state.dealer or winner == state.dealer) else 1
            payment = scores[winner] * factor
            totals[winner] += payment
            totals[p] -= payment

        # Remaining non-winners settle pairwise by score difference, again with
        # East doubling all payments involving East.
        others = [p for p in range(NUM_PLAYERS) if p != winner]
        for i, a in enumerate(others):
            for b in others[i + 1 :]:
                if scores[a] == scores[b]:
                    continue
                high, low = (a, b) if scores[a] > scores[b] else (b, a)
                factor = 2 if (high == state.dealer or low == state.dealer) else 1
                payment = (scores[high] - scores[low]) * factor
                totals[high] += payment
                totals[low] -= payment
        return [float(v) for v in totals]

    def render(self, state: GameState) -> str:
        parts = [
            f"phase={state.phase}",
            f"current={self.current_player(state)}",
            f"wall={self._remaining_total(state)}",
            f"round_wind={WINDS[state.round_wind]}",
        ]
        if state.last_discard is not None:
            parts.append(f"last_discard=p{state.last_discard[0]}:{state.last_discard[1]}")
        if state.winner is not None:
            parts.append(f"winner=p{state.winner}:{state.win_source}:{state.winning_tile}")
        lines = [" | ".join(parts)]
        for p in range(NUM_PLAYERS):
            hand = " ".join(_sorted_tiles(state.hands[p]))
            melds = ",".join(m.label() for m in state.melds[p]) or "-"
            bonus = " ".join(_sorted_tiles(state.bonus[p])) or "-"
            discards = " ".join(_sorted_tiles(state.dead_discards[p])) or "-"
            wind = WINDS[state.player_winds[p]]
            lines.append(f"p{p}({wind}) hand=[{hand}] melds=[{melds}] bonus=[{bonus}] discards=[{discards}]")
        if self.is_terminal(state):
            lines.append("returns=[" + ",".join(str(int(v)) if v.is_integer() else str(v) for v in self.returns(state)) + "]")
        return "\n".join(lines)

    def action_to_name(self, action: str) -> str:
        return str(action)

    def name_to_action(self, name: str) -> str:
        return str(name)

    # ------------------------------------------------------------------
    # Optional stochastic / hidden-information API
    # ------------------------------------------------------------------

    def chance_outcomes(self, state: GameState) -> List[Tuple[str, float]]:
        if self.is_terminal(state) or state.phase not in ("deal", "draw", "draw_replacement"):
            return []
        total = self._remaining_total(state)
        if total <= 0:
            return []
        outcomes: List[Tuple[str, float]] = []
        for tile in sorted(state.remaining, key=_tile_sort_key):
            count = state.remaining.get(tile, 0)
            if count > 0:
                outcomes.append((f"chance:draw:{tile}", count / total))
        return outcomes

    def information_state(self, state: GameState, player: int) -> str:
        if player not in range(NUM_PLAYERS):
            raise ValueError("player must be 0..3")
        lines = [
            f"player=p{player}",
            f"phase={state.phase}",
            f"current={self.current_player(state)}",
            f"wall_count={self._remaining_total(state)}",
            f"round_wind={WINDS[state.round_wind]}",
        ]
        if state.last_discard is not None:
            lines.append(f"last_discard=p{state.last_discard[0]}:{state.last_discard[1]}")
        own = " ".join(_sorted_tiles(state.hands[player]))
        lines.append(f"own_hand=[{own}]")
        for p in range(NUM_PLAYERS):
            melds = ",".join(m.label() for m in state.melds[p]) or "-"
            bonus = " ".join(_sorted_tiles(state.bonus[p])) or "-"
            discards = " ".join(_sorted_tiles(state.dead_discards[p])) or "-"
            if p == player:
                hand_info = f"hand_count={len(state.hands[p])}"
            else:
                hand_info = f"hidden_hand_count={len(state.hands[p])}"
            lines.append(f"p{p}:{hand_info}:melds=[{melds}]:bonus=[{bonus}]:discards=[{discards}]")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Action generation and transitions
    # ------------------------------------------------------------------

    def _initial_deal_sequence(self, state: GameState) -> List[int]:
        order = [(state.dealer + i) % NUM_PLAYERS for i in range(NUM_PLAYERS)]
        sequence: List[int] = []
        for _ in range(3):
            for p in order:
                sequence.extend([p, p, p, p])
        for p in order:
            sequence.append(p)
        sequence.append(state.dealer)
        return sequence

    def _discard_phase_actions(self, state: GameState, p: int) -> List[str]:
        actions: List[str] = []
        # A player may declare Mah-Jongg with the drawn hand.  The initial East
        # hand is also treated as a wall/self draw for "Segen des Himmels".
        if self._winning_hand_kind(state, p) is not None:
            actions.append("mahjong:selfdraw")

        # Kangs require a replacement draw; disallow them if no tile remains to
        # prevent a non-terminal chance state with no outcomes.
        if self._remaining_total(state) > 0:
            counts = Counter(state.hands[p])
            for tile in sorted(counts, key=_tile_sort_key):
                if counts[tile] >= 4 and not _is_bonus(tile):
                    actions.append(f"kong:concealed:{tile}")
            for idx, meld in enumerate(state.melds[p]):
                if meld.kind == "pong" and not meld.concealed:
                    tile = meld.tiles[0]
                    if counts[tile] >= 1:
                        # The index is included so action names remain unique if
                        # a manually constructed state contains duplicate melds.
                        actions.append(f"kong:add:{idx}:{tile}")

        for tile in sorted(set(state.hands[p]), key=_tile_sort_key):
            if not _is_bonus(tile):
                actions.append(f"discard:{tile}")
        return actions

    def _apply_chance_draw(self, state: GameState, action: str) -> GameState:
        tile = action[len("chance:draw:") :]
        ns = state.copy()
        if ns.remaining.get(tile, 0) <= 0:
            raise ValueError(f"tile {tile!r} is not available")
        ns.remaining[tile] -= 1
        if ns.remaining[tile] == 0:
            del ns.remaining[tile]
        ns.history.append(action)

        if ns.phase == "deal":
            sequence = self._initial_deal_sequence(ns)
            if ns.deal_index >= len(sequence):
                return self._begin_discard_turn(ns, ns.dealer)
            p = sequence[ns.deal_index]
            if _is_bonus(tile):
                ns.bonus[p].append(tile)
                ns.bonus[p] = _sorted_tiles(ns.bonus[p])
                if self._remaining_total(ns) == 0:
                    return self._make_draw_terminal(ns)
                return ns
            ns.hands[p].append(tile)
            ns.hands[p] = _sorted_tiles(ns.hands[p])
            ns.deal_index += 1
            if ns.deal_index >= len(sequence):
                ns.phase = "discard"
                ns.current = ns.dealer
                ns.draw_for = None
                ns.last_draw_player = ns.dealer
                ns.last_draw_tile = None
                ns.last_draw_source = "wall"
                ns.last_draw_was_final = False
            return ns

        if ns.draw_for is None:
            raise ValueError("draw phase without draw_for")
        p = ns.draw_for
        if _is_bonus(tile):
            ns.bonus[p].append(tile)
            ns.bonus[p] = _sorted_tiles(ns.bonus[p])
            # Bonus tiles do not count to the hand and are immediately replaced.
            # If none remain, the deal cannot continue and is a wall draw.
            if self._remaining_total(ns) == 0:
                return self._make_draw_terminal(ns)
            return ns

        ns.hands[p].append(tile)
        ns.hands[p] = _sorted_tiles(ns.hands[p])
        ns.last_draw_player = p
        ns.last_draw_tile = tile
        ns.last_draw_source = ns.draw_source
        ns.last_draw_was_final = self._remaining_total(ns) == 0
        ns.phase = "discard"
        ns.current = p
        ns.draw_for = None
        return ns

    def _apply_discard_phase_action(self, state: GameState, action: str) -> GameState:
        if action == "mahjong:selfdraw":
            return self._declare_selfdraw_win(state)
        if action.startswith("kong:concealed:"):
            tile = action[len("kong:concealed:") :]
            return self._declare_concealed_kong(state, tile)
        if action.startswith("kong:add:"):
            _prefix, _kind, index_text, tile = action.split(":", 3)
            return self._declare_added_kong(state, int(index_text), tile)
        if action.startswith("discard:"):
            tile = action[len("discard:") :]
            return self._discard_tile(state, tile)
        raise ValueError(f"unknown discard-phase action {action!r}")

    def _apply_claim_action(self, state: GameState, action: str) -> GameState:
        if action == "pass":
            return self._pass_claim(state)
        if action.startswith("mahjong:discard:"):
            _a, _b, player_text, tile = action.split(":", 3)
            return self._declare_discard_win(state, int(player_text[1:]), tile)
        if action.startswith("claim:pong:"):
            _a, _b, player_text, tile = action.split(":", 3)
            return self._claim_pong(state, int(player_text[1:]), tile)
        if action.startswith("claim:kang:"):
            _a, _b, player_text, tile = action.split(":", 3)
            return self._claim_kang(state, int(player_text[1:]), tile)
        if action.startswith("claim:chi:"):
            _a, _b, player_text, sequence_text = action.split(":", 3)
            return self._claim_chi(state, int(player_text[1:]), tuple(sequence_text.split("+")))
        raise ValueError(f"unknown claim action {action!r}")

    def _apply_rob_kong_action(self, state: GameState, action: str) -> GameState:
        if action == "pass":
            return self._pass_rob_kong(state)
        if action.startswith("mahjong:rob_kang:"):
            _a, _b, player_text, tile = action.split(":", 3)
            return self._declare_rob_kong_win(state, int(player_text[1:]), tile)
        raise ValueError(f"unknown rob-kong action {action!r}")

    def _begin_discard_turn(self, state: GameState, player: int) -> GameState:
        state.phase = "discard"
        state.current = player
        state.draw_for = None
        return state

    def _begin_wall_draw_or_terminal(self, state: GameState, player: int) -> GameState:
        if self._remaining_total(state) == 0:
            return self._make_draw_terminal(state)
        state.phase = "draw"
        state.current = CHANCE
        state.draw_for = player
        state.draw_source = "wall"
        state.last_draw_was_final = False
        state.kongs_in_current_turn = 0
        return state

    def _begin_replacement_draw_or_terminal(self, state: GameState, player: int, source: str = "wall") -> GameState:
        if self._remaining_total(state) == 0:
            return self._make_draw_terminal(state)
        state.phase = "draw_replacement"
        state.current = CHANCE
        state.draw_for = player
        state.draw_source = source
        return state

    def _make_draw_terminal(self, state: GameState) -> GameState:
        state.phase = "terminal"
        state.current = TERMINAL
        state.terminal = True
        state.winner = None
        state.win_source = None
        return state

    def _declare_selfdraw_win(self, state: GameState) -> GameState:
        p = state.current
        ns = state.copy()
        ns.phase = "terminal"
        ns.current = TERMINAL
        ns.terminal = True
        ns.winner = p
        source = ns.last_draw_source if ns.last_draw_player == p else "wall"
        ns.win_source = source
        ns.winning_tile = ns.last_draw_tile
        ns.winning_from = None
        ns.win_on_last_wall_tile = bool(ns.last_draw_was_final)
        ns.history.append("mahjong:selfdraw")
        return ns

    def _declare_concealed_kong(self, state: GameState, tile: str) -> GameState:
        p = state.current
        ns = state.copy()
        self._remove_tiles(ns.hands[p], [tile, tile, tile, tile])
        ns.melds[p].append(Meld("kang", (tile, tile, tile, tile), concealed=True, source_player=None))
        ns.kongs_in_current_turn += 1
        ns.history.append(f"kong:concealed:{tile}")
        return self._begin_replacement_draw_or_terminal(ns, p, source="wall")

    def _declare_added_kong(self, state: GameState, meld_index: int, tile: str) -> GameState:
        p = state.current
        ns = state.copy()
        if meld_index < 0 or meld_index >= len(ns.melds[p]):
            raise ValueError("bad meld index")
        meld = ns.melds[p][meld_index]
        if meld.kind != "pong" or meld.concealed or meld.tiles[0] != tile:
            raise ValueError("can only add to an open pong of the same tile")

        groups = self._build_rob_kong_groups(ns, p, tile)
        if groups:
            ns.phase = "rob_kong"
            ns.current = groups[0][0]
            ns.claim_groups = groups
            ns.claim_index = 0
            ns.pending_kong = (p, meld_index, tile)
            ns.history.append(f"kong:add-offered:{meld_index}:{tile}")
            return ns

        self._remove_tiles(ns.hands[p], [tile])
        ns.melds[p][meld_index] = Meld("kang", (tile, tile, tile, tile), concealed=False, source_player=meld.source_player)
        ns.kongs_in_current_turn += 1
        ns.history.append(f"kong:add:{meld_index}:{tile}")
        return self._begin_replacement_draw_or_terminal(ns, p, source="wall")

    def _discard_tile(self, state: GameState, tile: str) -> GameState:
        p = state.current
        ns = state.copy()
        self._remove_tiles(ns.hands[p], [tile])
        ns.last_discard = (p, tile)
        ns.discard_after_final_draw = bool(state.last_draw_was_final)
        ns.last_discard_was_first_east = (not state.first_discard_made and p == state.dealer)
        ns.first_discard_made = True
        ns.history.append(f"discard:{tile}")

        # After the final live-wall draw, the last discard may only be used to
        # complete Mah-Jongg; otherwise the game is over per the rule text.
        only_wins = ns.discard_after_final_draw
        groups = self._build_claim_groups(ns, p, tile, only_wins=only_wins)
        if groups:
            ns.phase = "claim"
            ns.current = groups[0][0]
            ns.claim_groups = groups
            ns.claim_index = 0
            ns.kongs_in_current_turn = 0
            return ns
        ns.dead_discards[p].append(tile)
        ns.dead_discards[p] = _sorted_tiles(ns.dead_discards[p])
        ns.last_discard = None
        ns.kongs_in_current_turn = 0
        if ns.discard_after_final_draw:
            return self._make_draw_terminal(ns)
        return self._begin_wall_draw_or_terminal(ns, self._right_neighbor(p))

    def _pass_claim(self, state: GameState) -> GameState:
        ns = state.copy()
        ns.history.append("pass")
        ns.claim_index += 1
        if ns.claim_index < len(ns.claim_groups):
            ns.current = ns.claim_groups[ns.claim_index][0]
            return ns
        if ns.last_discard is None:
            return self._make_draw_terminal(ns)
        discarder, tile = ns.last_discard
        ns.dead_discards[discarder].append(tile)
        ns.dead_discards[discarder] = _sorted_tiles(ns.dead_discards[discarder])
        ns.last_discard = None
        ns.claim_groups = []
        ns.claim_index = 0
        if ns.discard_after_final_draw:
            return self._make_draw_terminal(ns)
        return self._begin_wall_draw_or_terminal(ns, self._right_neighbor(discarder))

    def _declare_discard_win(self, state: GameState, player: int, tile: str) -> GameState:
        ns = state.copy()
        if ns.last_discard is None:
            raise ValueError("no discard to claim")
        discarder, discarded_tile = ns.last_discard
        if tile != discarded_tile:
            raise ValueError("winning tile does not match last discard")
        ns.hands[player].append(tile)
        ns.hands[player] = _sorted_tiles(ns.hands[player])
        ns.phase = "terminal"
        ns.current = TERMINAL
        ns.terminal = True
        ns.winner = player
        ns.win_source = "discard"
        ns.winning_tile = tile
        ns.winning_from = discarder
        ns.win_on_last_wall_tile = False
        ns.history.append(f"mahjong:discard:p{player}:{tile}")
        return ns

    def _claim_pong(self, state: GameState, player: int, tile: str) -> GameState:
        ns = state.copy()
        if ns.last_discard is None or ns.last_discard[1] != tile:
            raise ValueError("no matching discard to pong")
        discarder = ns.last_discard[0]
        self._remove_tiles(ns.hands[player], [tile, tile])
        ns.melds[player].append(Meld("pong", (tile, tile, tile), concealed=False, source_player=discarder))
        ns.last_discard = None
        ns.claim_groups = []
        ns.claim_index = 0
        ns.last_draw_was_final = False
        ns.kongs_in_current_turn = 0
        ns.history.append(f"claim:pong:p{player}:{tile}")
        return self._begin_discard_turn(ns, player)

    def _claim_kang(self, state: GameState, player: int, tile: str) -> GameState:
        ns = state.copy()
        if ns.last_discard is None or ns.last_discard[1] != tile:
            raise ValueError("no matching discard to kang")
        discarder = ns.last_discard[0]
        self._remove_tiles(ns.hands[player], [tile, tile, tile])
        ns.melds[player].append(Meld("kang", (tile, tile, tile, tile), concealed=False, source_player=discarder))
        ns.last_discard = None
        ns.claim_groups = []
        ns.claim_index = 0
        ns.kongs_in_current_turn = 1
        ns.history.append(f"claim:kang:p{player}:{tile}")
        return self._begin_replacement_draw_or_terminal(ns, player, source="wall")

    def _claim_chi(self, state: GameState, player: int, sequence: Tuple[str, ...]) -> GameState:
        ns = state.copy()
        if ns.last_discard is None:
            raise ValueError("no discard to chi")
        discarder, tile = ns.last_discard
        if tile not in sequence or len(sequence) != 3:
            raise ValueError("chi sequence must include the discarded tile")
        needed = list(sequence)
        needed.remove(tile)
        self._remove_tiles(ns.hands[player], needed)
        ns.melds[player].append(Meld("chi", tuple(_sorted_tiles(sequence)), concealed=False, source_player=discarder))
        ns.last_discard = None
        ns.claim_groups = []
        ns.claim_index = 0
        ns.last_draw_was_final = False
        ns.kongs_in_current_turn = 0
        ns.history.append(f"claim:chi:p{player}:{'+'.join(sequence)}")
        return self._begin_discard_turn(ns, player)

    def _pass_rob_kong(self, state: GameState) -> GameState:
        ns = state.copy()
        ns.history.append("pass")
        ns.claim_index += 1
        if ns.claim_index < len(ns.claim_groups):
            ns.current = ns.claim_groups[ns.claim_index][0]
            return ns
        if ns.pending_kong is None:
            return self._make_draw_terminal(ns)
        owner, meld_index, tile = ns.pending_kong
        old_meld = ns.melds[owner][meld_index]
        self._remove_tiles(ns.hands[owner], [tile])
        ns.melds[owner][meld_index] = Meld("kang", (tile, tile, tile, tile), concealed=False, source_player=old_meld.source_player)
        ns.pending_kong = None
        ns.claim_groups = []
        ns.claim_index = 0
        ns.kongs_in_current_turn += 1
        ns.history.append(f"kong:add:{meld_index}:{tile}")
        return self._begin_replacement_draw_or_terminal(ns, owner, source="wall")

    def _declare_rob_kong_win(self, state: GameState, player: int, tile: str) -> GameState:
        if state.pending_kong is None:
            raise ValueError("no pending kong to rob")
        owner, _meld_index, pending_tile = state.pending_kong
        if pending_tile != tile:
            raise ValueError("robbed tile mismatch")
        ns = state.copy()
        self._remove_tiles(ns.hands[owner], [tile])
        ns.hands[player].append(tile)
        ns.hands[player] = _sorted_tiles(ns.hands[player])
        ns.phase = "terminal"
        ns.current = TERMINAL
        ns.terminal = True
        ns.winner = player
        ns.win_source = "rob_kang"
        ns.winning_tile = tile
        ns.winning_from = owner
        ns.win_on_last_wall_tile = False
        ns.pending_kong = None
        ns.history.append(f"mahjong:rob_kang:p{player}:{tile}")
        return ns

    def _build_claim_groups(self, state: GameState, discarder: int, tile: str, only_wins: bool = False) -> List[Tuple[int, Tuple[str, ...]]]:
        groups: List[Tuple[int, Tuple[str, ...]]] = []
        order = [self._right_neighbor(discarder), (discarder + 2) % NUM_PLAYERS, (discarder + 3) % NUM_PLAYERS]

        # 1. Any Mah-Jongg claim has priority over ordinary figure claims.
        for p in order:
            if self._winning_hand_kind(state, p, extra_tile=tile) is not None:
                groups.append((p, (f"mahjong:discard:p{p}:{tile}",)))
        if only_wins:
            return groups

        # 2. Kang from a concealed pong in hand.
        if self._remaining_total(state) > 0:
            for p in order:
                if Counter(state.hands[p])[tile] >= 3:
                    groups.append((p, (f"claim:kang:p{p}:{tile}",)))

        # 3. Pong from a pair in hand.
        for p in order:
            if Counter(state.hands[p])[tile] >= 2:
                groups.append((p, (f"claim:pong:p{p}:{tile}",)))

        # 4. Tschi only by the player to the right of the discarder.
        chi_player = self._right_neighbor(discarder)
        chi_actions = self._chi_claim_actions(state, chi_player, tile)
        if chi_actions:
            groups.append((chi_player, tuple(chi_actions)))
        return groups

    def _build_rob_kong_groups(self, state: GameState, owner: int, tile: str) -> List[Tuple[int, Tuple[str, ...]]]:
        groups: List[Tuple[int, Tuple[str, ...]]] = []
        order = [self._right_neighbor(owner), (owner + 2) % NUM_PLAYERS, (owner + 3) % NUM_PLAYERS]
        for p in order:
            if self._winning_hand_kind(state, p, extra_tile=tile) is not None:
                groups.append((p, (f"mahjong:rob_kang:p{p}:{tile}",)))
        return groups

    def _chi_claim_actions(self, state: GameState, player: int, tile: str) -> List[str]:
        if not _is_suited(tile):
            return []
        suit = _tile_suit(tile)
        rank = _tile_rank(tile)
        assert suit is not None and rank is not None
        hand_counts = Counter(state.hands[player])
        actions: List[str] = []
        for start in (rank - 2, rank - 1, rank):
            if start < 1 or start > 7:
                continue
            seq = tuple(f"{suit}-{r}" for r in range(start, start + 3))
            needed = list(seq)
            needed.remove(tile)
            if all(hand_counts[t] >= needed.count(t) for t in set(needed)):
                actions.append(f"claim:chi:p{player}:{'+'.join(seq)}")
        return actions

    # ------------------------------------------------------------------
    # Hand completion
    # ------------------------------------------------------------------

    def _winning_hand_kind(self, state: GameState, player: int, extra_tile: Optional[str] = None) -> Optional[str]:
        counter = Counter(state.hands[player])
        if extra_tile is not None:
            counter[extra_tile] += 1
        meld_count = len(state.melds[player])
        if meld_count == 0 and self._is_thirteen_wonders(counter):
            return "thirteen_wonders"
        if meld_count == 0 and self._is_seven_pairs(counter):
            return "seven_pairs"
        if self._standard_decompositions(counter, state.melds[player], limit=1):
            return "standard"
        return None

    def _is_seven_pairs(self, counter: Counter) -> bool:
        return sum(counter.values()) == 14 and len(counter) == 7 and all(v == 2 for v in counter.values())

    def _is_thirteen_wonders(self, counter: Counter) -> bool:
        if sum(counter.values()) != 14:
            return False
        if any(tile not in ORPHANS for tile in counter):
            return False
        return all(counter[tile] >= 1 for tile in ORPHANS) and sum(1 for tile in ORPHANS if counter[tile] == 2) == 1

    def _standard_decompositions(
        self, counter: Counter, declared_melds: Sequence[Meld], limit: int = 64
    ) -> List[Tuple[Tuple[Meld, ...], str]]:
        needed_sets = 4 - len(declared_melds)
        if needed_sets < 0:
            return []
        if sum(counter.values()) != needed_sets * 3 + 2:
            return []
        results: List[Tuple[Tuple[Meld, ...], str]] = []
        for pair_tile in sorted(counter, key=_tile_sort_key):
            if counter[pair_tile] < 2:
                continue
            rest = Counter(counter)
            rest[pair_tile] -= 2
            if rest[pair_tile] == 0:
                del rest[pair_tile]
            for sets in self._set_partitions(rest, needed_sets, limit=limit):
                results.append((sets, pair_tile))
                if len(results) >= limit:
                    return results
        return results

    def _set_partitions(self, counter: Counter, needed_sets: int, limit: int = 64) -> List[Tuple[Meld, ...]]:
        if needed_sets == 0:
            return [tuple()] if sum(counter.values()) == 0 else []
        if sum(counter.values()) != needed_sets * 3:
            return []
        remaining_tiles = [tile for tile, count in counter.items() if count > 0]
        if not remaining_tiles:
            return []
        tile = min(remaining_tiles, key=_tile_sort_key)
        results: List[Tuple[Meld, ...]] = []

        if counter[tile] >= 3:
            rest = Counter(counter)
            rest[tile] -= 3
            if rest[tile] == 0:
                del rest[tile]
            meld = Meld("pong", (tile, tile, tile), concealed=True)
            for suffix in self._set_partitions(rest, needed_sets - 1, limit=limit):
                results.append((meld,) + suffix)
                if len(results) >= limit:
                    return results

        if _is_suited(tile):
            suit = _tile_suit(tile)
            rank = _tile_rank(tile)
            assert suit is not None and rank is not None
            if rank <= 7:
                seq = (f"{suit}-{rank}", f"{suit}-{rank + 1}", f"{suit}-{rank + 2}")
                if all(counter[t] > 0 for t in seq):
                    rest = Counter(counter)
                    for t in seq:
                        rest[t] -= 1
                        if rest[t] == 0:
                            del rest[t]
                    meld = Meld("chi", seq, concealed=True)
                    for suffix in self._set_partitions(rest, needed_sets - 1, limit=limit):
                        results.append((meld,) + suffix)
                        if len(results) >= limit:
                            return results
        return results

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    def score_breakdown(self, state: GameState, player: int) -> ScoreBreakdown:
        if player not in range(NUM_PLAYERS):
            raise ValueError("player must be 0..3")
        is_winner = self.is_terminal(state) and state.winner == player
        if is_winner:
            return self._winner_score_breakdown(state, player)
        groups, pairs = self._nonwinner_scoring_figures(state, player)
        return self._regular_score_from_figures(state, player, groups, pairs, is_winner=False)

    def _winner_score_breakdown(self, state: GameState, player: int) -> ScoreBreakdown:
        hand_kind = self._winning_hand_kind(state, player)
        counter = Counter(state.hands[player])

        if hand_kind in ("seven_pairs", "thirteen_wonders"):
            limit = self._limit_score_for_context(state, player, [], None, hand_kind)
            if limit is not None:
                return limit
            # This fallback is unlikely because both special kinds are limit
            # hands in the rulebook.  It keeps the API total for malformed states.
            return ScoreBreakdown(0, 0, 0, notes=(hand_kind,))

        decomps = self._standard_decompositions(counter, state.melds[player], limit=64)
        if not decomps:
            return ScoreBreakdown(0, 0, 0, notes=("no complete decomposition",))

        limit_scores: List[ScoreBreakdown] = []
        regular_scores: List[ScoreBreakdown] = []
        for concealed_sets, pair_tile in decomps:
            groups = list(state.melds[player]) + list(concealed_sets)
            groups = self._mark_discard_completed_group(state, groups, pair_tile)
            limit_score = self._limit_score_for_context(state, player, groups, pair_tile, "standard")
            if limit_score is not None:
                limit_scores.append(limit_score)
            regular_scores.append(self._regular_score_from_figures(state, player, groups, [pair_tile], is_winner=True))

        if limit_scores:
            return max(limit_scores, key=lambda s: (s.value, len(s.limit_hands)))
        return max(regular_scores, key=lambda s: (s.value, s.base, s.doubles))

    def _mark_discard_completed_group(self, state: GameState, groups: List[Meld], pair_tile: Optional[str]) -> List[Meld]:
        if state.win_source not in ("discard", "rob_kang") or state.winning_tile is None:
            return groups
        # A discard/robbed tile used as the pair does not change figure points,
        # but it still prevents the "all figures concealed" double elsewhere.
        if pair_tile == state.winning_tile:
            return groups
        marked: List[Meld] = []
        changed = False
        for meld in groups:
            if not changed and meld.concealed and state.winning_tile in meld.tiles:
                marked.append(Meld(meld.kind, meld.tiles, concealed=False, source_player=state.winning_from))
                changed = True
            else:
                marked.append(meld)
        return marked

    def _nonwinner_scoring_figures(self, state: GameState, player: int) -> Tuple[List[Meld], List[str]]:
        groups = list(state.melds[player])
        counter = Counter(state.hands[player])
        # Undeclared four-of-a-kind is counted only as a concealed Pong, matching
        # the rule text's note that a non-laid Kang scores merely as Pong.
        for tile in sorted(list(counter), key=_tile_sort_key):
            if counter[tile] >= 3 and not _is_bonus(tile):
                groups.append(Meld("pong", (tile, tile, tile), concealed=True))
                counter[tile] -= 3
        pairs: List[str] = []
        for tile in sorted(counter, key=_tile_sort_key):
            if counter[tile] >= 2 and self._pair_points(state, player, tile) > 0:
                pairs.append(tile)
        return groups, pairs

    def _regular_score_from_figures(
        self, state: GameState, player: int, groups: Sequence[Meld], pairs: Sequence[str], is_winner: bool
    ) -> ScoreBreakdown:
        notes: List[str] = []
        figure_base = 0
        for meld in groups:
            figure_base += self._meld_points(meld)
        for pair_tile in pairs:
            figure_base += self._pair_points(state, player, pair_tile)
        figure_base += 4 * len(state.bonus[player])

        base = figure_base
        if is_winner:
            base += 20
            notes.append("Mah-Jongg-Ruf +20")
            if state.win_source in ("wall", "dead") and state.winning_tile is not None:
                base += 2
                notes.append("Schlussziegel von der Mauer +2")
            if self._only_possible_winning_tile(state, player):
                base += 2
                notes.append("einzig moeglicher Schlussziegel +2")
            pair_completion = self._winning_pair_completion_points(state, pairs)
            if pair_completion:
                base += pair_completion
                notes.append(f"Schlussziegel komplettiert Paar +{pair_completion}")

        doubles = self._all_hand_doubles(state, player, groups, pairs)
        if is_winner:
            doubles += self._mahjong_only_doubles(state, player, groups, pairs, figure_base)

        value = base * (2 ** doubles)
        if value > state.limit:
            notes.append(f"Limit {state.limit}")
            value = state.limit
        return ScoreBreakdown(int(value), int(base), int(doubles), notes=tuple(notes))

    def _meld_points(self, meld: Meld) -> int:
        if meld.kind == "chi":
            return 0
        tile = meld.tiles[0]
        concealed = meld.concealed
        if meld.kind == "pong":
            if _is_simple_suited(tile):
                return 4 if concealed else 2
            if _is_terminal(tile) or _is_honor(tile):
                return 8 if concealed else 4
        if meld.kind == "kang":
            if _is_simple_suited(tile):
                return 16 if concealed else 8
            if _is_terminal(tile) or _is_honor(tile):
                return 32 if concealed else 16
        return 0

    def _pair_points(self, state: GameState, player: int, tile: str) -> int:
        points = 0
        if _is_dragon(tile):
            points += 2
        wind = _wind_index(tile)
        if wind is not None:
            if wind == state.player_winds[player]:
                points += 2
            if wind == state.round_wind:
                points += 2
        return points

    def _all_hand_doubles(self, state: GameState, player: int, groups: Sequence[Meld], pairs: Sequence[str]) -> int:
        doubles = 0
        bonus_set = set(state.bonus[player])
        wind_number = state.player_winds[player] + 1
        if f"blume-{wind_number}" in bonus_set and f"jahreszeit-{wind_number}" in bonus_set:
            doubles += 1
        if all(tile in bonus_set for tile in FLOWERS):
            doubles += 1
        if all(tile in bonus_set for tile in SEASONS):
            doubles += 1

        set_groups = [m for m in groups if m.kind in ("pong", "kang")]
        dragon_sets = [m for m in set_groups if _is_dragon(m.tiles[0])]
        doubles += len(dragon_sets)
        for meld in set_groups:
            wind = _wind_index(meld.tiles[0])
            if wind is not None and wind == state.player_winds[player]:
                doubles += 1
            if wind is not None and wind == state.round_wind:
                doubles += 1

        # The table says "Drei verdeckte Pong".  A concealed Kang necessarily
        # contains a concealed Pong-shaped figure, so it is counted here.
        if sum(1 for m in set_groups if m.concealed) >= 3:
            doubles += 1

        dragon_pair = any(_is_dragon(tile) for tile in pairs)
        if len(dragon_sets) == 3:
            doubles += 2
        elif len(dragon_sets) == 2 and dragon_pair:
            doubles += 1

        wind_sets = [m for m in set_groups if _is_wind(m.tiles[0])]
        wind_pair = any(_is_wind(tile) for tile in pairs)
        if len(wind_sets) == 4:
            doubles += 2
        elif len(wind_sets) == 3 and wind_pair:
            doubles += 1
        return doubles

    def _mahjong_only_doubles(
        self, state: GameState, player: int, groups: Sequence[Meld], pairs: Sequence[str], figure_base: int
    ) -> int:
        doubles = 0
        if figure_base == 0:
            doubles += 1
        if all(m.kind != "chi" for m in groups):
            doubles += 1
        if all(m.concealed for m in groups) and state.win_source not in ("discard", "rob_kang"):
            doubles += 1

        normal_tiles = self._player_normal_tiles(state, player)
        suits = {_tile_suit(t) for t in normal_tiles if _is_suited(t)}
        honors_present = any(_is_honor(t) for t in normal_tiles)
        if len(suits) == 1 and not honors_present:
            doubles += 3
        elif len(suits) == 1 and honors_present:
            doubles += 1
        if normal_tiles and all(_is_major(t) for t in normal_tiles):
            doubles += 1
        if normal_tiles and all(_is_honor(t) for t in normal_tiles):
            # Only awarded here if the hand was not treated as the pure-honors
            # limit hand; limit hands bypass this regular scoring function.
            doubles += 2
        if state.win_source == "dead":
            doubles += 1
        if state.win_on_last_wall_tile:
            doubles += 1
        if state.win_source == "discard" and state.discard_after_final_draw:
            doubles += 1
        if state.win_source == "rob_kang":
            doubles += 1
        # "Mah-Jongg nach Ruf zu Beginn" is named in the scoring table but the
        # supplied play rules do not define the declaration procedure.  It is
        # therefore intentionally not awarded by this engine.
        return doubles

    def _limit_score_for_context(
        self,
        state: GameState,
        player: int,
        groups: Sequence[Meld],
        pair_tile: Optional[str],
        hand_kind: str,
    ) -> Optional[ScoreBreakdown]:
        names: List[str] = []
        half_limit = False
        normal_tiles = self._player_normal_tiles(state, player)
        suits = {_tile_suit(t) for t in normal_tiles if _is_suited(t)}
        honors_present = any(_is_honor(t) for t in normal_tiles)
        set_groups = [m for m in groups if m.kind in ("pong", "kang")]

        if normal_tiles and all(_is_honor(t) for t in normal_tiles):
            names.append("Reine Bildziegel-Hand")
        if normal_tiles and all(_is_suited(t) and _is_terminal(t) for t in normal_tiles):
            names.append("Koepfe und Schwaenze")
        if hand_kind == "thirteen_wonders":
            names.append("Die 13 einzigartigen Wunder")
        if hand_kind == "seven_pairs":
            names.append("Paariges Spiel")
            half_limit = True
        if len(suits) == 1 and not honors_present and groups and all(m.concealed for m in groups) and state.win_source not in ("discard", "rob_kang"):
            names.append("Verdecktes reines Farbspiel")
        if self._is_winding_snake(groups, pair_tile):
            names.append("Die sich windende Schlange")
        if sum(1 for m in groups if m.kind == "kang") == 4:
            names.append("Vierfacher Reichtum")
        dragon_sets = [m for m in set_groups if _is_dragon(m.tiles[0])]
        if len(dragon_sets) == 3 and len(set_groups) >= 4 and pair_tile is not None:
            names.append("Die drei grossen Gelehrten")
        wind_sets = [m for m in set_groups if _is_wind(m.tiles[0])]
        if len(wind_sets) == 4:
            names.append("Vier Segen ueber der Tuer")
        if normal_tiles and all(t in GREEN_TILES for t in normal_tiles):
            names.append("Die kaiserliche gruene Hand")
        if self._is_nine_gates(state, player):
            names.append("Neun Laternen")
        if len([m for m in set_groups if m.concealed]) >= 4 and state.win_source in ("wall", "dead"):
            names.append("Verborgener Schatz")
        if player == state.dealer and not state.first_discard_made and state.win_source == "wall":
            names.append("Segen des Himmels")
        if player != state.dealer and state.win_source == "discard" and state.last_discard_was_first_east:
            names.append("Segen der Erde")
        if state.kongs_in_current_turn >= 2 and state.win_source in ("wall", "dead"):
            names.append("Doppeltes Glueck")
        if state.win_source == "dead" and state.winning_tile == "kreis-5":
            names.append("Die Pflaumenbluete vom Dach pfluecken")
        if state.win_on_last_wall_tile and state.winning_tile == "kreis-1":
            names.append("Den Mond vom Meeresgrund holen")
        if state.win_source == "rob_kang" and state.winning_tile == "bambus-2":
            names.append("Einen tragenden Pfosten beanspruchen")
        if player == state.dealer and state.east_consecutive_wins >= 8:
            names.append("Neunmal Mah-Jongg")

        if not names:
            return None
        # All listed limit hands score the full limit except "Paariges Spiel",
        # which the rulebook explicitly values at half limit.  If a seven-pairs
        # hand simultaneously satisfies a full-limit pattern, the full limit is
        # used because a limit hand was played.
        full_limit_names = [name for name in names if name != "Paariges Spiel"]
        if full_limit_names:
            value = state.limit
        else:
            value = state.limit // 2 if half_limit else state.limit
        return ScoreBreakdown(int(value), int(value), 0, limit_hands=tuple(names))

    def _is_winding_snake(self, groups: Sequence[Meld], pair_tile: Optional[str]) -> bool:
        if pair_tile is None or not _is_suited(pair_tile):
            return False
        suit = _tile_suit(pair_tile)
        all_tiles: List[str] = [pair_tile, pair_tile]
        for meld in groups:
            all_tiles.extend(meld.tiles)
        if any(_tile_suit(t) != suit for t in all_tiles if _is_suited(t)) or any(_is_honor(t) for t in all_tiles):
            return False
        pair_rank = _tile_rank(pair_tile)
        if pair_rank not in (2, 5, 8):
            return False
        has_1_set = any(m.kind in ("pong", "kang") and _tile_rank(m.tiles[0]) == 1 for m in groups)
        has_9_set = any(m.kind in ("pong", "kang") and _tile_rank(m.tiles[0]) == 9 for m in groups)
        chi_count = sum(1 for m in groups if m.kind == "chi")
        return has_1_set and has_9_set and chi_count >= 2

    def _is_nine_gates(self, state: GameState, player: int) -> bool:
        if state.melds[player]:
            return False
        tiles = state.hands[player]
        if len(tiles) != 14:
            return False
        suits = {_tile_suit(t) for t in tiles if _is_suited(t)}
        if len(suits) != 1 or any(not _is_suited(t) for t in tiles):
            return False
        suit = next(iter(suits))
        counts = Counter(tiles)
        if counts[f"{suit}-1"] < 3 or counts[f"{suit}-9"] < 3:
            return False
        return all(counts[f"{suit}-{rank}"] >= 1 for rank in range(2, 9))

    def _only_possible_winning_tile(self, state: GameState, player: int) -> bool:
        if state.winning_tile is None:
            return False
        counter = Counter(state.hands[player])
        if counter[state.winning_tile] <= 0:
            return False
        counter[state.winning_tile] -= 1
        if counter[state.winning_tile] == 0:
            del counter[state.winning_tile]
        winners = []
        temp = state.copy()
        temp.hands[player] = []
        for tile in NORMAL_TILES:
            trial = Counter(counter)
            trial[tile] += 1
            if len(state.melds[player]) == 0 and (self._is_thirteen_wonders(trial) or self._is_seven_pairs(trial)):
                winners.append(tile)
            elif self._standard_decompositions(trial, state.melds[player], limit=1):
                winners.append(tile)
            if len(winners) > 1:
                return False
        return winners == [state.winning_tile]

    def _winning_pair_completion_points(self, state: GameState, pairs: Sequence[str]) -> int:
        tile = state.winning_tile
        if tile is None or tile not in pairs:
            return 0
        if _is_simple_suited(tile):
            return 2
        if _is_terminal(tile) or _is_honor(tile):
            return 4
        return 0

    def _player_normal_tiles(self, state: GameState, player: int) -> List[str]:
        tiles = [t for t in state.hands[player] if not _is_bonus(t)]
        for meld in state.melds[player]:
            tiles.extend(t for t in meld.tiles if not _is_bonus(t))
        return tiles

    # ------------------------------------------------------------------
    # Small utilities
    # ------------------------------------------------------------------

    def _right_neighbor(self, player: int) -> int:
        return (player + 1) % NUM_PLAYERS

    def _remaining_total(self, state: GameState) -> int:
        return sum(state.remaining.values())

    def _remove_tiles(self, hand: List[str], tiles: Iterable[str]) -> None:
        for tile in tiles:
            try:
                hand.remove(tile)
            except ValueError as exc:
                raise ValueError(f"hand does not contain required tile {tile!r}") from exc
        hand[:] = _sorted_tiles(hand)
```
