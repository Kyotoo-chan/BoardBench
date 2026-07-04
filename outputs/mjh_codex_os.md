## Open questions / assumptions

- This models one hand only, not the full four-round wind rotation.
- Bonus tiles (flowers/seasons), dead-wall replacement, dice wall break, and official point settlement are not fully modeled.
- The tile set is inferred from the wall size and scoring text: three numbered suits, four winds, three dragons, four copies each. The third suit is unnamed in the text, so it is labeled `farbe3`.
- Hidden information is represented: `GameState` stores full truth, while `information_state` hides other hands.
- Claim conflicts are represented as a simultaneous/adjudication phase: all valid claims plus `pass:all` are listed, and the caller chooses the resolved action.
- Win detection supports normal Mah-Jongg, seven pairs, and thirteen wonders. Other limit hands are not separately scored.
- `returns` uses a simple abstract winner payoff, not the official scoring table.

```python
from collections import Counter
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

TERMINAL = -1
CHANCE = -2
SIMULTANEOUS = -3

PLAYERS = 4
WINDS = ("ost", "sued", "west", "nord")
ROUND_WIND = "ost"

SUITS = ("kreis", "bambus", "farbe3")
RANKS = tuple(range(1, 10))
NUMBER_TILES = tuple(f"{suit}_{rank}" for suit in SUITS for rank in RANKS)
WIND_TILES = WINDS
DRAGON_TILES = ("drache1", "drache2", "gruener_drache")
TILES = NUMBER_TILES + WIND_TILES + DRAGON_TILES
TILE_INDEX = {tile: i for i, tile in enumerate(TILES)}
COPIES_PER_TILE = 4

# Same final hand sizes as the described deal: 13 tiles each, East gets tile 14.
DEAL_SEQUENCE = tuple([p for _ in range(13) for p in range(PLAYERS)] + [0])


@dataclass(frozen=True)
class Meld:
    kind: str
    tiles: Tuple[str, ...]
    concealed: bool = False
    claimed_from: Optional[int] = None


@dataclass
class GameState:
    phase: str = "deal"
    current: int = 0
    wall: Counter = field(default_factory=Counter)
    hands: List[Counter] = field(default_factory=lambda: [Counter() for _ in range(PLAYERS)])
    melds: List[List[Meld]] = field(default_factory=lambda: [[] for _ in range(PLAYERS)])
    discards: List[List[str]] = field(default_factory=lambda: [[] for _ in range(PLAYERS)])
    dead_discards: List[str] = field(default_factory=list)
    last_discard: Optional[str] = None
    last_discarder: Optional[int] = None
    winner: Optional[int] = None
    win_source: Optional[str] = None
    deal_index: int = 0
    live_remaining: int = 0
    pending_kang_player: Optional[int] = None
    pending_kang_tile: Optional[str] = None
    pending_kang_meld_index: Optional[int] = None
    history: List[str] = field(default_factory=list)

    def clone(self):
        return GameState(
            phase=self.phase,
            current=self.current,
            wall=Counter(self.wall),
            hands=[Counter(hand) for hand in self.hands],
            melds=[list(melds) for melds in self.melds],
            discards=[list(discards) for discards in self.discards],
            dead_discards=list(self.dead_discards),
            last_discard=self.last_discard,
            last_discarder=self.last_discarder,
            winner=self.winner,
            win_source=self.win_source,
            deal_index=self.deal_index,
            live_remaining=self.live_remaining,
            pending_kang_player=self.pending_kang_player,
            pending_kang_tile=self.pending_kang_tile,
            pending_kang_meld_index=self.pending_kang_meld_index,
            history=list(self.history),
        )


def _full_wall():
    return Counter({tile: COPIES_PER_TILE for tile in TILES})


def _tile_sort_key(tile):
    return TILE_INDEX[tile]


def _positive_counts(counter):
    return Counter({tile: count for tile, count in counter.items() if count > 0})


def _remove_tile(counter, tile, count=1):
    if counter[tile] < count:
        raise ValueError(f"not enough {tile}")
    counter[tile] -= count
    if counter[tile] <= 0:
        del counter[tile]


def _add_tile(counter, tile, count=1):
    counter[tile] += count


def _right_neighbor(player):
    return (player + 1) % PLAYERS


def _player_label(player):
    if player in range(PLAYERS):
        return f"p{player}({WINDS[player]})"
    if player == CHANCE:
        return "chance"
    if player == SIMULTANEOUS:
        return "simultaneous"
    return "terminal"


def _number_parts(tile):
    if tile not in TILE_INDEX:
        return None
    parts = tile.rsplit("_", 1)
    if len(parts) != 2:
        return None
    suit, rank_text = parts
    if suit not in SUITS or not rank_text.isdigit():
        return None
    rank = int(rank_text)
    if rank not in RANKS:
        return None
    return suit, rank


def _make_number_tile(suit, rank):
    return f"{suit}_{rank}"


def _chi_sequences_for_tile(tile):
    parts = _number_parts(tile)
    if parts is None:
        return []
    suit, rank = parts
    sequences = []
    for start in range(rank - 2, rank + 1):
        if 1 <= start <= 7:
            sequences.append(tuple(_make_number_tile(suit, r) for r in range(start, start + 3)))
    return sequences


def _legal_chi_sequences(hand, tile):
    sequences = []
    for sequence in _chi_sequences_for_tile(tile):
        needed = Counter(sequence)
        needed[tile] -= 1
        needed = _positive_counts(needed)
        if all(hand[t] >= n for t, n in needed.items()):
            sequences.append(sequence)
    return sequences


def _can_partition_groups(counts, groups_needed):
    counts = _positive_counts(counts)
    if groups_needed == 0:
        return sum(counts.values()) == 0
    if sum(counts.values()) != groups_needed * 3:
        return False

    tile = min(counts, key=_tile_sort_key)

    if counts[tile] >= 3:
        next_counts = Counter(counts)
        _remove_tile(next_counts, tile, 3)
        if _can_partition_groups(next_counts, groups_needed - 1):
            return True

    parts = _number_parts(tile)
    if parts is not None:
        suit, rank = parts
        if rank <= 7:
            sequence = tuple(_make_number_tile(suit, r) for r in range(rank, rank + 3))
            if all(next_tile in counts and counts[next_tile] > 0 for next_tile in sequence):
                next_counts = Counter(counts)
                for next_tile in sequence:
                    _remove_tile(next_counts, next_tile)
                if _can_partition_groups(next_counts, groups_needed - 1):
                    return True

    return False


def _is_standard_mahjong(concealed_counts, melds):
    fixed_groups = len(melds)
    groups_needed = 4 - fixed_groups
    if groups_needed < 0:
        return False

    counts = _positive_counts(concealed_counts)
    if sum(counts.values()) != groups_needed * 3 + 2:
        return False

    for pair_tile in sorted(counts, key=_tile_sort_key):
        if counts[pair_tile] >= 2:
            next_counts = Counter(counts)
            _remove_tile(next_counts, pair_tile, 2)
            if _can_partition_groups(next_counts, groups_needed):
                return True
    return False


def _is_seven_pairs(concealed_counts, melds):
    # The rule text says exactly seven pairs. It does not say whether four
    # identical tiles may count as two pairs; this implementation allows it.
    if melds:
        return False
    counts = _positive_counts(concealed_counts)
    return sum(counts.values()) == 14 and all(c % 2 == 0 for c in counts.values()) and sum(c // 2 for c in counts.values()) == 7


def _is_thirteen_wonders(concealed_counts, melds):
    if melds:
        return False
    required = set()
    for suit in SUITS:
        required.add(_make_number_tile(suit, 1))
        required.add(_make_number_tile(suit, 9))
    required.update(WIND_TILES)
    required.update(DRAGON_TILES)

    counts = _positive_counts(concealed_counts)
    if sum(counts.values()) != 14:
        return False
    if any(tile not in required for tile in counts):
        return False
    if any(counts[tile] < 1 for tile in required):
        return False
    return sum(1 for tile in required if counts[tile] == 2) == 1 and all(counts[tile] in (1, 2) for tile in required)


def _is_complete_mahjong(concealed_counts, melds):
    return (
        _is_standard_mahjong(concealed_counts, melds)
        or _is_seven_pairs(concealed_counts, melds)
        or _is_thirteen_wonders(concealed_counts, melds)
    )


def _counter_text(counter):
    counter = _positive_counts(counter)
    if not counter:
        return "-"
    parts = []
    for tile in sorted(counter, key=_tile_sort_key):
        count = counter[tile]
        parts.append(tile if count == 1 else f"{tile}x{count}")
    return " ".join(parts)


def _meld_text(meld):
    visibility = "concealed" if meld.concealed else "open"
    return f"{visibility}_{meld.kind}(" + ",".join(meld.tiles) + ")"


def _melds_text(melds):
    if not melds:
        return "-"
    return " ".join(_meld_text(meld) for meld in melds)


def _tiles_text(tiles):
    if not tiles:
        return "-"
    counts = Counter(tiles)
    return _counter_text(counts)


def _validate_tile(tile):
    if tile not in TILE_INDEX:
        raise ValueError(f"unknown tile: {tile}")
    return tile


def _parse_player(text):
    if not text.startswith("p"):
        raise ValueError(f"bad player label: {text}")
    player = int(text[1:])
    if player not in range(PLAYERS):
        raise ValueError(f"bad player index: {player}")
    return player


class Game:
    num_players = PLAYERS

    def initial_state(self):
        wall = _full_wall()
        return GameState(wall=wall, live_remaining=sum(wall.values()))

    def current_player(self, state):
        if self.is_terminal(state):
            return TERMINAL
        if state.phase in ("deal", "draw", "replacement"):
            return CHANCE
        if state.phase in ("claim", "rob_kang"):
            return SIMULTANEOUS
        return state.current

    def legal_actions(self, state):
        if self.is_terminal(state):
            return []

        if state.phase in ("deal", "draw", "replacement"):
            return [action for action, _prob in self.chance_outcomes(state)]

        if state.phase == "discard":
            player = state.current
            hand = state.hands[player]
            actions = []

            if _is_complete_mahjong(hand, state.melds[player]):
                actions.append(("mahjong_self",))

            if state.live_remaining > 0:
                for tile in sorted(hand, key=_tile_sort_key):
                    if hand[tile] == 4:
                        actions.append(("kang_concealed", tile))
                for meld in state.melds[player]:
                    if meld.kind == "pong" and not meld.concealed:
                        tile = meld.tiles[0]
                        if hand[tile] > 0:
                            actions.append(("kang_extend", tile))

            for tile in sorted(hand, key=_tile_sort_key):
                if hand[tile] > 0:
                    actions.append(("discard", tile))
            return actions

        if state.phase == "claim":
            tile = state.last_discard
            discarder = state.last_discarder
            actions = []
            if tile is None or discarder is None:
                return [("pass_all",)]

            for player in range(PLAYERS):
                if player == discarder:
                    continue
                test_hand = Counter(state.hands[player])
                _add_tile(test_hand, tile)
                if _is_complete_mahjong(test_hand, state.melds[player]):
                    actions.append(("claim_mahjong", player, tile))

            # After the last live-wall tile has been discarded, the text only
            # allows Mah-Jongg completion before the hand ends.
            if state.live_remaining > 0:
                for player in range(PLAYERS):
                    if player == discarder:
                        continue
                    if state.hands[player][tile] >= 3:
                        actions.append(("claim_kang", player, tile))
                    if state.hands[player][tile] >= 2:
                        actions.append(("claim_pong", player, tile))

                chi_player = _right_neighbor(discarder)
                for sequence in _legal_chi_sequences(state.hands[chi_player], tile):
                    actions.append(("claim_chi", chi_player, sequence))

            actions.append(("pass_all",))
            return actions

        if state.phase == "rob_kang":
            tile = state.pending_kang_tile
            owner = state.pending_kang_player
            actions = []
            if tile is None or owner is None:
                return []
            for player in range(PLAYERS):
                if player == owner:
                    continue
                test_hand = Counter(state.hands[player])
                _add_tile(test_hand, tile)
                if _is_complete_mahjong(test_hand, state.melds[player]):
                    actions.append(("rob_mahjong", player, tile))
            actions.append(("continue_kang", tile))
            return actions

        return []

    def chance_outcomes(self, state):
        if state.phase not in ("deal", "draw", "replacement"):
            return []
        total = sum(state.wall.values())
        if total <= 0:
            return []

        if state.phase == "deal":
            kind = "chance_deal"
        elif state.phase == "draw":
            kind = "chance_draw"
        else:
            kind = "chance_replacement"

        return [((kind, tile), state.wall[tile] / total) for tile in sorted(state.wall, key=_tile_sort_key) if state.wall[tile] > 0]

    def apply_action(self, state, action):
        if action not in self.legal_actions(state):
            raise ValueError(f"illegal action: {action}")

        next_state = state.clone()
        next_state.history.append(self.action_to_name(action))
        kind = action[0]

        if kind in ("chance_deal", "chance_draw", "chance_replacement"):
            tile = action[1]
            _remove_tile(next_state.wall, tile)
            next_state.live_remaining -= 1

            if kind == "chance_deal":
                player = DEAL_SEQUENCE[next_state.deal_index]
                _add_tile(next_state.hands[player], tile)
                next_state.deal_index += 1
                if next_state.deal_index >= len(DEAL_SEQUENCE):
                    next_state.phase = "discard"
                    next_state.current = 0
                else:
                    next_state.phase = "deal"
                    next_state.current = DEAL_SEQUENCE[next_state.deal_index]
            else:
                _add_tile(next_state.hands[next_state.current], tile)
                next_state.phase = "discard"
            return next_state

        if kind == "discard":
            player = next_state.current
            tile = action[1]
            _remove_tile(next_state.hands[player], tile)
            next_state.discards[player].append(tile)
            next_state.last_discard = tile
            next_state.last_discarder = player
            next_state.phase = "claim"
            return next_state

        if kind == "mahjong_self":
            next_state.phase = "terminal"
            next_state.winner = next_state.current
            next_state.win_source = "self_draw"
            return next_state

        if kind == "kang_concealed":
            player = next_state.current
            tile = action[1]
            _remove_tile(next_state.hands[player], tile, 4)
            next_state.melds[player].append(Meld("kang", (tile,), concealed=True))
            next_state.phase = "replacement"
            return next_state

        if kind == "kang_extend":
            player = next_state.current
            tile = action[1]
            for index, meld in enumerate(next_state.melds[player]):
                if meld.kind == "pong" and not meld.concealed and meld.tiles[0] == tile:
                    next_state.pending_kang_player = player
                    next_state.pending_kang_tile = tile
                    next_state.pending_kang_meld_index = index
                    next_state.phase = "rob_kang"
                    return next_state
            raise ValueError("open pong not found for kang extension")

        if kind == "claim_mahjong":
            next_state.phase = "terminal"
            next_state.winner = action[1]
            next_state.win_source = "discard"
            return next_state

        if kind in ("claim_pong", "claim_kang", "claim_chi"):
            self._remove_claimed_discard(next_state)
            player = action[1]
            tile = next_state.last_discard
            discarder = next_state.last_discarder

            if kind == "claim_pong":
                _remove_tile(next_state.hands[player], tile, 2)
                next_state.melds[player].append(Meld("pong", (tile,), concealed=False, claimed_from=discarder))
                next_state.current = player
                next_state.phase = "discard"

            elif kind == "claim_kang":
                _remove_tile(next_state.hands[player], tile, 3)
                next_state.melds[player].append(Meld("kang", (tile,), concealed=False, claimed_from=discarder))
                next_state.current = player
                next_state.phase = "replacement"

            else:
                sequence = action[2]
                needed = Counter(sequence)
                needed[tile] -= 1
                needed = _positive_counts(needed)
                for needed_tile, count in needed.items():
                    _remove_tile(next_state.hands[player], needed_tile, count)
                next_state.melds[player].append(Meld("chi", tuple(sequence), concealed=False, claimed_from=discarder))
                next_state.current = player
                next_state.phase = "discard"

            next_state.last_discard = None
            next_state.last_discarder = None
            return next_state

        if kind == "pass_all":
            if next_state.last_discard is not None:
                next_state.dead_discards.append(next_state.last_discard)
            discarder = next_state.last_discarder
            next_state.last_discard = None
            next_state.last_discarder = None

            if next_state.live_remaining <= 0:
                next_state.phase = "terminal"
                next_state.winner = None
                next_state.win_source = "wall_empty"
            else:
                next_state.current = _right_neighbor(discarder)
                next_state.phase = "draw"
            return next_state

        if kind == "rob_mahjong":
            next_state.phase = "terminal"
            next_state.winner = action[1]
            next_state.win_source = "rob_kang"
            next_state.pending_kang_player = None
            next_state.pending_kang_tile = None
            next_state.pending_kang_meld_index = None
            return next_state

        if kind == "continue_kang":
            player = next_state.pending_kang_player
            tile = next_state.pending_kang_tile
            index = next_state.pending_kang_meld_index
            _remove_tile(next_state.hands[player], tile)
            old_meld = next_state.melds[player][index]
            next_state.melds[player][index] = Meld("kang", (tile,), concealed=False, claimed_from=old_meld.claimed_from)
            next_state.pending_kang_player = None
            next_state.pending_kang_tile = None
            next_state.pending_kang_meld_index = None
            next_state.current = player
            next_state.phase = "replacement"
            return next_state

        raise ValueError(f"unsupported action: {action}")

    def _remove_claimed_discard(self, state):
        discarder = state.last_discarder
        tile = state.last_discard
        if discarder is None or tile is None:
            return
        pile = state.discards[discarder]
        for index in range(len(pile) - 1, -1, -1):
            if pile[index] == tile:
                del pile[index]
                return

    def is_terminal(self, state):
        return state.phase == "terminal"

    def returns(self, state):
        if not self.is_terminal(state) or state.winner is None:
            return [0.0 for _ in range(PLAYERS)]
        result = [-1.0 for _ in range(PLAYERS)]
        result[state.winner] = 3.0
        return result

    def render(self, state):
        lines = [
            f"phase={state.phase} current={_player_label(self.current_player(state))} "
            f"round_wind={ROUND_WIND} wall={state.live_remaining} "
            f"winner={state.winner if state.winner is not None else '-'} source={state.win_source or '-'}"
        ]
        if state.last_discard is not None:
            lines.append(f"last_discard=p{state.last_discarder}:{state.last_discard}")
        if state.pending_kang_tile is not None:
            lines.append(f"pending_kang=p{state.pending_kang_player}:{state.pending_kang_tile}")

        for player in range(PLAYERS):
            lines.append(
                f"p{player} wind={WINDS[player]} "
                f"hand={_counter_text(state.hands[player])} "
                f"melds={_melds_text(state.melds[player])} "
                f"discards={_tiles_text(state.discards[player])}"
            )
        lines.append(f"dead_discards={_tiles_text(state.dead_discards)}")
        return "\n".join(lines)

    def information_state(self, state, player):
        if player not in range(PLAYERS):
            raise ValueError("bad player")

        lines = [
            f"viewer=p{player} wind={WINDS[player]} phase={state.phase} "
            f"current={_player_label(self.current_player(state))} wall={state.live_remaining}"
        ]
        if state.last_discard is not None:
            lines.append(f"last_discard=p{state.last_discarder}:{state.last_discard}")

        for p in range(PLAYERS):
            if p == player:
                hand_text = _counter_text(state.hands[p])
            else:
                hand_text = f"hidden_count={sum(state.hands[p].values())}"
            lines.append(
                f"p{p} wind={WINDS[p]} hand={hand_text} "
                f"melds={_melds_text(state.melds[p])} discards={_tiles_text(state.discards[p])}"
            )
        lines.append(f"dead_discards={_tiles_text(state.dead_discards)}")
        return "\n".join(lines)

    def action_to_name(self, action):
        kind = action[0]

        if kind == "chance_deal":
            return f"chance:deal:{action[1]}"
        if kind == "chance_draw":
            return f"chance:draw:{action[1]}"
        if kind == "chance_replacement":
            return f"chance:replacement:{action[1]}"
        if kind == "discard":
            return f"discard:{action[1]}"
        if kind == "mahjong_self":
            return "mahjong:self"
        if kind == "kang_concealed":
            return f"kang:concealed:{action[1]}"
        if kind == "kang_extend":
            return f"kang:extend:{action[1]}"
        if kind == "kang_continue" or kind == "continue_kang":
            return f"kang:continue:{action[1]}"
        if kind == "claim_mahjong":
            return f"claim:p{action[1]}:mahjong:{action[2]}"
        if kind == "claim_pong":
            return f"claim:p{action[1]}:pong:{action[2]}"
        if kind == "claim_kang":
            return f"claim:p{action[1]}:kang:{action[2]}"
        if kind == "claim_chi":
            return f"claim:p{action[1]}:chi:{'-'.join(action[2])}"
        if kind == "pass_all":
            return "pass:all"
        if kind == "rob_mahjong":
            return f"rob:p{action[1]}:mahjong:{action[2]}"

        raise ValueError(f"unknown action kind: {kind}")

    def name_to_action(self, name):
        parts = name.split(":")
        if parts[0] == "chance" and len(parts) == 3:
            tile = _validate_tile(parts[2])
            if parts[1] == "deal":
                return ("chance_deal", tile)
            if parts[1] == "draw":
                return ("chance_draw", tile)
            if parts[1] == "replacement":
                return ("chance_replacement", tile)

        if parts[0] == "discard" and len(parts) == 2:
            return ("discard", _validate_tile(parts[1]))

        if name == "mahjong:self":
            return ("mahjong_self",)

        if parts[0] == "kang" and len(parts) == 3:
            tile = _validate_tile(parts[2])
            if parts[1] == "concealed":
                return ("kang_concealed", tile)
            if parts[1] == "extend":
                return ("kang_extend", tile)
            if parts[1] == "continue":
                return ("continue_kang", tile)

        if parts[0] == "claim" and len(parts) == 4:
            player = _parse_player(parts[1])
            claim_kind = parts[2]
            if claim_kind == "chi":
                sequence = tuple(_validate_tile(tile) for tile in parts[3].split("-"))
                if len(sequence) != 3:
                    raise ValueError("chi action needs three tiles")
                return ("claim_chi", player, sequence)
            tile = _validate_tile(parts[3])
            if claim_kind == "mahjong":
                return ("claim_mahjong", player, tile)
            if claim_kind == "pong":
                return ("claim_pong", player, tile)
            if claim_kind == "kang":
                return ("claim_kang", player, tile)

        if name == "pass:all":
            return ("pass_all",)

        if parts[0] == "rob" and len(parts) == 4 and parts[2] == "mahjong":
            return ("rob_mahjong", _parse_player(parts[1]), _validate_tile(parts[3]))

        raise ValueError(f"cannot parse action name: {name}")
```