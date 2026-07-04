**Pair action naming changes**

Shared convention: normalizer-safe lowercase action keys with canonical tile labels such as `kreis_1`, `bambus_1`, `farbe3_1`, `ost`, `drache1`, and `gruener_drache`. Discards, declarations, claims, rob-kang wins, passes, and chi sequences now use matching comparison stems like `discard_<tile>`, `kang_extend_<tile>`, `claim_chi_<t1>__<t2>__<t3>`, and `pass`. The left file keeps claimant ids as trailing punctuation markers so tuple actions still round-trip while normalizing to the same state-relative claim keys as the right file.

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


_SEQUENCE_SEP = "__"
_PLAYER_MARKS = {0: "!", 1: "!!", 2: "!!!", 3: "!!!!"}
_PLAYER_BY_MARK = {mark: player for player, mark in _PLAYER_MARKS.items()}


def _tile_action_label(tile):
    return _validate_tile(tile)


def _tile_from_action_label(label):
    return _validate_tile(label)


def _sequence_action_label(sequence):
    return _SEQUENCE_SEP.join(_tile_action_label(tile) for tile in sequence)


def _sequence_from_action_label(label):
    parts = label.split(_SEQUENCE_SEP)
    if len(parts) != 3:
        raise ValueError("chi action needs three tiles")
    return tuple(_tile_from_action_label(part) for part in parts)


def _with_player_marker(base, player):
    if player not in _PLAYER_MARKS:
        raise ValueError(f"bad player index: {player}")
    return base + _PLAYER_MARKS[player]


def _split_player_marker(name):
    base = name.rstrip("!")
    mark = name[len(base) :]
    if mark not in _PLAYER_BY_MARK:
        raise ValueError(f"missing player marker: {name}")
    return base, _PLAYER_BY_MARK[mark]


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
            return f"chance_deal_{_tile_action_label(action[1])}"
        if kind == "chance_draw":
            return f"chance_draw_{_tile_action_label(action[1])}"
        if kind == "chance_replacement":
            return f"chance_replacement_{_tile_action_label(action[1])}"
        if kind == "discard":
            return f"discard_{_tile_action_label(action[1])}"
        if kind == "mahjong_self":
            return "mahjong_self"
        if kind == "kang_concealed":
            return f"kang_concealed_{_tile_action_label(action[1])}"
        if kind == "kang_extend":
            return f"kang_extend_{_tile_action_label(action[1])}"
        if kind == "kang_continue" or kind == "continue_kang":
            return f"kang_continue_{_tile_action_label(action[1])}"
        if kind == "claim_mahjong":
            return _with_player_marker(f"claim_mahjong_{_tile_action_label(action[2])}", action[1])
        if kind == "claim_pong":
            return _with_player_marker(f"claim_pong_{_tile_action_label(action[2])}", action[1])
        if kind == "claim_kang":
            return _with_player_marker(f"claim_kang_{_tile_action_label(action[2])}", action[1])
        if kind == "claim_chi":
            return _with_player_marker(f"claim_chi_{_sequence_action_label(action[2])}", action[1])
        if kind == "pass_all":
            return "pass"
        if kind == "rob_mahjong":
            return _with_player_marker(f"rob_mahjong_{_tile_action_label(action[2])}", action[1])

        raise ValueError(f"unknown action kind: {kind}")

    def name_to_action(self, name):
        if name.startswith("chance_deal_"):
            return ("chance_deal", _tile_from_action_label(name[len("chance_deal_") :]))
        if name.startswith("chance_draw_"):
            return ("chance_draw", _tile_from_action_label(name[len("chance_draw_") :]))
        if name.startswith("chance_replacement_"):
            return ("chance_replacement", _tile_from_action_label(name[len("chance_replacement_") :]))
        if name.startswith("discard_"):
            return ("discard", _tile_from_action_label(name[len("discard_") :]))
        if name == "mahjong_self":
            return ("mahjong_self",)
        if name.startswith("kang_concealed_"):
            return ("kang_concealed", _tile_from_action_label(name[len("kang_concealed_") :]))
        if name.startswith("kang_extend_"):
            return ("kang_extend", _tile_from_action_label(name[len("kang_extend_") :]))
        if name.startswith("kang_continue_"):
            return ("continue_kang", _tile_from_action_label(name[len("kang_continue_") :]))
        if name == "pass":
            return ("pass_all",)

        try:
            base, player = _split_player_marker(name)
        except ValueError:
            base = None
            player = None

        if base is not None:
            if base.startswith("claim_mahjong_"):
                return ("claim_mahjong", player, _tile_from_action_label(base[len("claim_mahjong_") :]))
            if base.startswith("claim_pong_"):
                return ("claim_pong", player, _tile_from_action_label(base[len("claim_pong_") :]))
            if base.startswith("claim_kang_"):
                return ("claim_kang", player, _tile_from_action_label(base[len("claim_kang_") :]))
            if base.startswith("claim_chi_"):
                return ("claim_chi", player, _sequence_from_action_label(base[len("claim_chi_") :]))
            if base.startswith("rob_mahjong_"):
                return ("rob_mahjong", player, _tile_from_action_label(base[len("rob_mahjong_") :]))

        raise ValueError(f"cannot parse action name: {name}")
```

```python
"""Self-contained Mah-Jongg rules model built only from the supplied rules.

Open questions and assumptions are repeated here because the extracted
rulebook text omits some labels and conflict-resolution details:

* The third numbered suit and two dragon names are not visible in the text.
  They are represented as ``Farbe3``, ``DracheA`` and ``DracheB``; the named
  tiles ``Bambus``, ``Kreis`` and ``Gruen-Drache`` are kept where the text
  names them.
* Setup is deterministic. The real rules use dice and a shuffled wall; this
  API avoids hidden randomness and exposes no external random source.
* The literal dead-wall description is treated as fourteen double tiles plus
  two loose tiles, i.e. thirty tiles.
* Claim conflicts are resolved by asking responders counter-clockwise from the
  discarder. The rule text lists possible reactions but does not give a full
  priority table.
* Scoring implements the printed point and doubling tables where the needed
  information is present. Ambiguous bonuses such as "only possible tile" are
  not inferred.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, replace
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


TERMINAL = -1
CHANCE = -2
SIMULTANEOUS = -3

NUM_PLAYERS = 4
WINDS = ("Ost", "Sued", "West", "Nord")
SUITS = ("Bambus", "Kreis", "Farbe3")
DRAGONS = ("DracheA", "DracheB", "Gruen-Drache")
FLOWERS = ("Blume1", "Blume2", "Blume3", "Blume4")
SEASONS = ("Jahreszeit1", "Jahreszeit2", "Jahreszeit3", "Jahreszeit4")
BONUS_TILES = FLOWERS + SEASONS
GREEN_TILES = {
    "Bambus-2",
    "Bambus-3",
    "Bambus-4",
    "Bambus-6",
    "Bambus-8",
    "Gruen-Drache",
}


@dataclass(frozen=True)
class Meld:
    kind: str
    tiles: Tuple[str, ...]
    open: bool
    source: str = ""


@dataclass(frozen=True)
class Arrangement:
    melds: Tuple[Meld, ...]
    pair: Optional[Tuple[str, str]] = None


@dataclass(frozen=True)
class HandScore:
    value: int
    base_points: int
    doubles: int
    limit_hand: Optional[str] = None
    details: Tuple[str, ...] = ()


@dataclass(frozen=True)
class GameState:
    hands: Tuple[Tuple[str, ...], ...] = ((), (), (), ())
    live_wall: Tuple[str, ...] = ()
    dead_wall: Tuple[str, ...] = ()
    exposed: Tuple[Tuple[Meld, ...], ...] = ((), (), (), ())
    bonus: Tuple[Tuple[str, ...], ...] = ((), (), (), ())
    discards: Tuple[Tuple[str, ...], ...] = ((), (), (), ())
    dead_discards: Tuple[str, ...] = ()
    phase: str = "terminal"
    player: int = TERMINAL
    round_wind: str = "Ost"
    place_winds: Tuple[str, ...] = WINDS
    last_discard: Optional[str] = None
    last_discarder: Optional[int] = None
    responders_passed: Tuple[int, ...] = ()
    pending_rob: Optional[Tuple[int, int, str]] = None
    terminal_reason: Optional[str] = None
    winner: Optional[int] = None
    winning_tile: Optional[str] = None
    win_source: Optional[str] = None
    last_draw_source: Optional[str] = None
    last_draw_tile: Optional[str] = None
    last_draw_was_last_live: bool = False
    kang_chain: int = 0
    history: Tuple[str, ...] = ()


def _suited_tile(suit: str, rank: int) -> str:
    return f"{suit}-{rank}"


def _split_suited(tile: str) -> Optional[Tuple[str, int]]:
    for suit in SUITS:
        prefix = suit + "-"
        if tile.startswith(prefix):
            rest = tile[len(prefix) :]
            if rest.isdigit():
                rank = int(rest)
                if 1 <= rank <= 9:
                    return suit, rank
    return None


_CANONICAL_SUIT_LABELS = {"Bambus": "bambus", "Kreis": "kreis", "Farbe3": "farbe3"}
_ACTION_TILE_LABELS = {
    "Ost": "ost",
    "Sued": "sued",
    "West": "west",
    "Nord": "nord",
    "DracheA": "drache1",
    "DracheB": "drache2",
    "Gruen-Drache": "gruener_drache",
}
_ACTION_TILE_LABELS.update({tile: tile.lower() for tile in BONUS_TILES})
_ACTION_LABEL_TO_TILE = {label: tile for tile, label in _ACTION_TILE_LABELS.items()}
for _suit, _label in _CANONICAL_SUIT_LABELS.items():
    for _rank_value in range(1, 10):
        _ACTION_LABEL_TO_TILE[f"{_label}_{_rank_value}"] = _suited_tile(_suit, _rank_value)
_SEQUENCE_SEP = "__"


def _tile_action_label(tile: str) -> str:
    parsed = _split_suited(tile)
    if parsed:
        suit, rank = parsed
        return f"{_CANONICAL_SUIT_LABELS[suit]}_{rank}"
    if tile in _ACTION_TILE_LABELS:
        return _ACTION_TILE_LABELS[tile]
    raise ValueError(f"unknown tile: {tile}")


def _tile_from_action_label(label: str) -> str:
    try:
        return _ACTION_LABEL_TO_TILE[label]
    except KeyError as exc:
        raise ValueError(f"unknown tile label: {label}") from exc


def _sequence_action_label(sequence: Sequence[str]) -> str:
    return _SEQUENCE_SEP.join(_tile_action_label(tile) for tile in sequence)


def _sequence_from_action_label(label: str) -> Tuple[str, str, str]:
    parts = label.split(_SEQUENCE_SEP)
    if len(parts) != 3:
        raise ValueError("chi action needs three tiles")
    return tuple(_tile_from_action_label(part) for part in parts)  # type: ignore[return-value]


def _is_suited(tile: str) -> bool:
    return _split_suited(tile) is not None


def _suit(tile: str) -> Optional[str]:
    parsed = _split_suited(tile)
    return parsed[0] if parsed else None


def _rank(tile: str) -> Optional[int]:
    parsed = _split_suited(tile)
    return parsed[1] if parsed else None


def _is_wind(tile: str) -> bool:
    return tile in WINDS


def _is_dragon(tile: str) -> bool:
    return tile in DRAGONS


def _is_honor(tile: str) -> bool:
    return _is_wind(tile) or _is_dragon(tile)


def _is_bonus(tile: str) -> bool:
    return tile in BONUS_TILES


def _is_terminal_suited(tile: str) -> bool:
    return _is_suited(tile) and _rank(tile) in (1, 9)


def _is_terminal_or_honor(tile: str) -> bool:
    return _is_terminal_suited(tile) or _is_honor(tile)


def _tile_sort_key(tile: str) -> Tuple[int, int, int, str]:
    parsed = _split_suited(tile)
    if parsed:
        suit, rank = parsed
        return (0, SUITS.index(suit), rank, tile)
    if tile in WINDS:
        return (1, WINDS.index(tile), 0, tile)
    if tile in DRAGONS:
        return (2, DRAGONS.index(tile), 0, tile)
    if tile in FLOWERS:
        return (3, FLOWERS.index(tile), 0, tile)
    if tile in SEASONS:
        return (4, SEASONS.index(tile), 0, tile)
    return (9, 0, 0, tile)


def _sorted_tiles(tiles: Iterable[str]) -> Tuple[str, ...]:
    return tuple(sorted(tiles, key=_tile_sort_key))


def _next_player(player: int) -> int:
    return (player + 1) % NUM_PLAYERS


def _responders_after(player: int) -> Tuple[int, int, int]:
    first = _next_player(player)
    return (first, _next_player(first), _next_player(_next_player(first)))


def _next_responder(actor: int, passed: Sequence[int]) -> Optional[int]:
    passed_set = set(passed)
    for candidate in _responders_after(actor):
        if candidate not in passed_set:
            return candidate
    return None


def _replace_group(
    grouped: Tuple[Tuple[object, ...], ...], player: int, value: Iterable[object]
) -> Tuple[Tuple[object, ...], ...]:
    items = [tuple(group) for group in grouped]
    items[player] = tuple(value)
    return tuple(items)


def _remove_tiles(hand: Sequence[str], tiles: Iterable[str]) -> Tuple[str, ...]:
    result = list(hand)
    for tile in tiles:
        try:
            result.remove(tile)
        except ValueError as exc:
            raise ValueError(f"tile {tile!r} is not available") from exc
    return _sorted_tiles(result)


def _deterministic_mix(tiles: Sequence[str]) -> Tuple[str, ...]:
    size = len(tiles)
    keyed = sorted(
        enumerate(tiles),
        key=lambda item: ((item[0] * 37 + 17) % size, item[1], item[0]),
    )
    return tuple(tile for _, tile in keyed)


def _full_wall(include_bonus_tiles: bool) -> Tuple[str, ...]:
    tiles: List[str] = []
    for suit in SUITS:
        for rank in range(1, 10):
            tiles.extend([_suited_tile(suit, rank)] * 4)
    for wind in WINDS:
        tiles.extend([wind] * 4)
    for dragon in DRAGONS:
        tiles.extend([dragon] * 4)
    if include_bonus_tiles:
        tiles.extend(BONUS_TILES)
    return _deterministic_mix(tiles)


def _meld_text(meld: Meld) -> str:
    visibility = "open" if meld.open else "concealed"
    return f"{meld.kind}:{'+'.join(meld.tiles)}:{visibility}"


def _counter_key(counter: Counter) -> Tuple[Tuple[str, int], ...]:
    return tuple(
        sorted(
            ((tile, count) for tile, count in counter.items() if count),
            key=lambda item: _tile_sort_key(item[0]),
        )
    )


def _meld_groupings(
    counter: Counter,
    needed: int,
    memo: Optional[
        Dict[
            Tuple[Tuple[Tuple[str, int], ...], int],
            Tuple[Tuple[Meld, ...], ...],
        ]
    ] = None,
) -> Tuple[Tuple[Meld, ...], ...]:
    if memo is None:
        memo = {}
    key = (_counter_key(counter), needed)
    if key in memo:
        return memo[key]
    remaining = sum(counter.values())
    if needed == 0:
        result = ((),) if remaining == 0 else ()
        memo[key] = result
        return result
    if remaining != needed * 3:
        memo[key] = ()
        return ()

    first = min((tile for tile, count in counter.items() if count), key=_tile_sort_key)
    results: List[Tuple[Meld, ...]] = []

    if counter[first] >= 3:
        next_counter = counter.copy()
        next_counter[first] -= 3
        meld = Meld("pong", (first, first, first), False, "concealed")
        for rest in _meld_groupings(next_counter, needed - 1, memo):
            results.append((meld,) + rest)

    parsed = _split_suited(first)
    if parsed:
        suit, rank = parsed
        if rank <= 7:
            second = _suited_tile(suit, rank + 1)
            third = _suited_tile(suit, rank + 2)
            if counter[second] > 0 and counter[third] > 0:
                next_counter = counter.copy()
                next_counter[first] -= 1
                next_counter[second] -= 1
                next_counter[third] -= 1
                meld = Meld("tschi", (first, second, third), False, "concealed")
                for rest in _meld_groupings(next_counter, needed - 1, memo):
                    results.append((meld,) + rest)

    memo[key] = tuple(results)
    return memo[key]


def _standard_arrangements(
    concealed_tiles: Sequence[str], exposed_melds: Sequence[Meld]
) -> Tuple[Arrangement, ...]:
    needed = 4 - len(exposed_melds)
    if needed < 0 or len(concealed_tiles) != needed * 3 + 2:
        return ()
    counter = Counter(concealed_tiles)
    arrangements: List[Arrangement] = []
    for pair_tile in sorted(counter, key=_tile_sort_key):
        if counter[pair_tile] < 2:
            continue
        next_counter = counter.copy()
        next_counter[pair_tile] -= 2
        for concealed_melds in _meld_groupings(next_counter, needed):
            arrangements.append(
                Arrangement(tuple(exposed_melds) + concealed_melds, (pair_tile, pair_tile))
            )
    return tuple(arrangements)


def _is_seven_pairs(concealed_tiles: Sequence[str], exposed_melds: Sequence[Meld]) -> bool:
    if exposed_melds or len(concealed_tiles) != 14:
        return False
    counts = Counter(concealed_tiles)
    return len(counts) == 7 and all(count == 2 for count in counts.values())


def _is_thirteen_wonders(
    concealed_tiles: Sequence[str], exposed_melds: Sequence[Meld]
) -> bool:
    if exposed_melds or len(concealed_tiles) != 14:
        return False
    required = {_suited_tile(suit, rank) for suit in SUITS for rank in (1, 9)}
    required.update(WINDS)
    required.update(DRAGONS)
    counts = Counter(concealed_tiles)
    return set(counts) == required and sorted(counts.values()) == [1] * 12 + [2]


def _arrangement_tiles(arrangement: Arrangement) -> Tuple[str, ...]:
    tiles: List[str] = []
    for meld in arrangement.melds:
        tiles.extend(meld.tiles)
    if arrangement.pair:
        tiles.extend(arrangement.pair)
    return tuple(tiles)


class Game:
    """A small deterministic engine for the supplied Mah-Jongg rules."""

    def __init__(self, limit: int = 500, include_bonus_tiles: bool = False):
        self.num_players = NUM_PLAYERS
        self.limit = int(limit)
        self.include_bonus_tiles = bool(include_bonus_tiles)

    def initial_state(self) -> GameState:
        wall = list(_full_wall(self.include_bonus_tiles))
        dead_count = 30
        dead_wall = wall[:dead_count]
        live_wall = wall[dead_count:]

        hands: List[List[str]] = [[] for _ in range(NUM_PLAYERS)]
        for _ in range(3):
            for player in range(NUM_PLAYERS):
                for _ in range(4):
                    hands[player].append(live_wall.pop(0))
        for player in range(NUM_PLAYERS):
            hands[player].append(live_wall.pop(0))
        east_extra = live_wall.pop(0)
        hands[0].append(east_extra)

        state = GameState(
            hands=tuple(_sorted_tiles(hand) for hand in hands),
            live_wall=tuple(live_wall),
            dead_wall=tuple(dead_wall),
            exposed=((), (), (), ()),
            bonus=((), (), (), ()),
            discards=((), (), (), ()),
            dead_discards=(),
            phase="discard",
            player=0,
            round_wind="Ost",
            place_winds=WINDS,
            last_draw_source="initial",
            last_draw_tile=east_extra,
            history=("setup:deterministic",),
        )
        for player in range(NUM_PLAYERS):
            state = self._resolve_bonus_from_hand(state, player)
        return state

    def current_player(self, state: GameState) -> int:
        if self.is_terminal(state):
            return TERMINAL
        return state.player

    def legal_actions(self, state: GameState) -> List[str]:
        if self.is_terminal(state):
            return []
        if state.phase == "draw":
            return ["draw:live"] if state.live_wall else []
        if state.phase == "discard":
            return self._legal_discard_actions(state, state.player)
        if state.phase == "claim":
            return self._legal_claim_actions(state, state.player)
        if state.phase == "rob_kang":
            return self._legal_rob_kang_actions(state, state.player)
        return []

    def apply_action(self, state: GameState, action: str) -> GameState:
        if action not in self.legal_actions(state):
            raise ValueError(f"illegal action {action!r} in phase {state.phase!r}")
        history = state.history + (action,)
        if state.phase == "draw":
            start = replace(state, kang_chain=0)
            return self._draw_live(start, state.player, history)
        if state.phase == "discard":
            return self._apply_discard_action(state, action, history)
        if state.phase == "claim":
            return self._apply_claim_action(state, action, history)
        if state.phase == "rob_kang":
            return self._apply_rob_kang_action(state, action, history)
        raise ValueError(f"unsupported phase {state.phase!r}")

    def is_terminal(self, state: GameState) -> bool:
        return state.terminal_reason is not None or (
            state.phase == "draw" and not state.live_wall
        )

    def returns(self, state: GameState) -> List[int]:
        if not self.is_terminal(state):
            return [0, 0, 0, 0]
        if state.terminal_reason != "mahjong" or state.winner is None:
            return [0, 0, 0, 0]

        values = [self.score_hand(state, player).value for player in range(NUM_PLAYERS)]
        winner = state.winner
        east = state.place_winds.index("Ost")
        returns = [0, 0, 0, 0]

        for payer in range(NUM_PLAYERS):
            if payer == winner:
                continue
            multiplier = 2 if payer == east or winner == east else 1
            amount = values[winner] * multiplier
            returns[winner] += amount
            returns[payer] -= amount

        others = [player for player in range(NUM_PLAYERS) if player != winner]
        for index, first in enumerate(others):
            for second in others[index + 1 :]:
                if values[first] == values[second]:
                    continue
                high, low = (
                    (first, second)
                    if values[first] > values[second]
                    else (second, first)
                )
                multiplier = 2 if high == east or low == east else 1
                amount = abs(values[first] - values[second]) * multiplier
                returns[high] += amount
                returns[low] -= amount
        return returns

    def render(self, state: GameState) -> str:
        lines = [
            (
                f"phase={state.phase} current={self.current_player(state)} "
                f"winner={state.winner} reason={state.terminal_reason}"
            ),
            (
                f"round_wind={state.round_wind} live={len(state.live_wall)} "
                f"dead={len(state.dead_wall)} last_discard={state.last_discard} "
                f"last_discarder={state.last_discarder} win_source={state.win_source}"
            ),
        ]
        for player in range(NUM_PLAYERS):
            exposed = ",".join(_meld_text(meld) for meld in state.exposed[player]) or "-"
            hand = ",".join(state.hands[player]) or "-"
            bonus = ",".join(state.bonus[player]) or "-"
            discards = ",".join(state.discards[player]) or "-"
            lines.append(
                f"P{player} wind={state.place_winds[player]} hand={hand} "
                f"exposed={exposed} bonus={bonus} discards={discards}"
            )
        lines.append("dead_discards=" + (",".join(state.dead_discards) or "-"))
        lines.append("history=" + "|".join(state.history))
        return "\n".join(lines)

    def action_to_name(self, action: str) -> str:
        if not isinstance(action, str):
            raise TypeError("actions are canonical strings")
        if action == "draw:live":
            return "draw_live"
        if action == "declare:mahjong":
            return "mahjong_self"
        if action == "pass":
            return "pass"
        if action.startswith("declare:kang:") and action.endswith(":concealed"):
            tile = action[len("declare:kang:") : -len(":concealed")]
            return f"kang_concealed_{_tile_action_label(tile)}"
        if action.startswith("declare:kang:") and action.endswith(":extend"):
            tile = action[len("declare:kang:") : -len(":extend")]
            return f"kang_extend_{_tile_action_label(tile)}"
        if action.startswith("discard:"):
            tile = action[len("discard:") :]
            return f"discard_{_tile_action_label(tile)}"
        if action.startswith("claim:mahjong:"):
            tile = action[len("claim:mahjong:") :]
            return f"claim_mahjong_{_tile_action_label(tile)}"
        if action.startswith("claim:kang:"):
            tile = action[len("claim:kang:") :]
            return f"claim_kang_{_tile_action_label(tile)}"
        if action.startswith("claim:pong:"):
            tile = action[len("claim:pong:") :]
            return f"claim_pong_{_tile_action_label(tile)}"
        if action.startswith("claim:tschi:"):
            sequence = tuple(action[len("claim:tschi:") :].split("+"))
            return f"claim_chi_{_sequence_action_label(sequence)}"
        if action.startswith("mahjong:rob-kang:"):
            tile = action[len("mahjong:rob-kang:") :]
            return f"rob_mahjong_{_tile_action_label(tile)}"
        raise ValueError(f"unknown action string: {action}")

    def name_to_action(self, name: str) -> str:
        if not isinstance(name, str):
            raise TypeError("action names are strings")
        if name == "draw_live":
            return "draw:live"
        if name == "mahjong_self":
            return "declare:mahjong"
        if name == "pass":
            return "pass"
        if name.startswith("kang_concealed_"):
            return f"declare:kang:{_tile_from_action_label(name[len('kang_concealed_') :])}:concealed"
        if name.startswith("kang_extend_"):
            return f"declare:kang:{_tile_from_action_label(name[len('kang_extend_') :])}:extend"
        if name.startswith("discard_"):
            return f"discard:{_tile_from_action_label(name[len('discard_') :])}"
        if name.startswith("claim_mahjong_"):
            return f"claim:mahjong:{_tile_from_action_label(name[len('claim_mahjong_') :])}"
        if name.startswith("claim_kang_"):
            return f"claim:kang:{_tile_from_action_label(name[len('claim_kang_') :])}"
        if name.startswith("claim_pong_"):
            return f"claim:pong:{_tile_from_action_label(name[len('claim_pong_') :])}"
        if name.startswith("claim_chi_"):
            return "claim:tschi:" + "+".join(_sequence_from_action_label(name[len("claim_chi_") :]))
        if name.startswith("rob_mahjong_"):
            return f"mahjong:rob-kang:{_tile_from_action_label(name[len('rob_mahjong_') :])}"
        raise ValueError(f"cannot parse action name: {name}")

    def information_state(self, state: GameState, player: int) -> str:
        if player < 0 or player >= NUM_PLAYERS:
            raise ValueError("player must be 0..3")
        lines = [
            f"viewer=P{player}",
            f"phase={state.phase} current={self.current_player(state)}",
            f"round_wind={state.round_wind} own_wind={state.place_winds[player]}",
            f"live_count={len(state.live_wall)} dead_count={len(state.dead_wall)}",
            f"last_discard={state.last_discard} last_discarder={state.last_discarder}",
        ]
        for seat in range(NUM_PLAYERS):
            exposed = ",".join(_meld_text(meld) for meld in state.exposed[seat]) or "-"
            bonus = ",".join(state.bonus[seat]) or "-"
            discards = ",".join(state.discards[seat]) or "-"
            if seat == player:
                hand_info = ",".join(state.hands[seat]) or "-"
            else:
                hand_info = f"{len(state.hands[seat])} concealed"
            lines.append(
                f"P{seat} wind={state.place_winds[seat]} hand={hand_info} "
                f"exposed={exposed} bonus={bonus} discards={discards}"
            )
        return "\n".join(lines)

    def score_hand(self, state: GameState, player: int) -> HandScore:
        exposed = state.exposed[player]
        concealed = state.hands[player]
        is_winner = state.terminal_reason == "mahjong" and state.winner == player

        special_scores: List[HandScore] = []
        if _is_seven_pairs(concealed, exposed):
            special_scores.append(
                HandScore(
                    max(0, self.limit // 2),
                    0,
                    0,
                    "Paariges Spiel",
                    ("seven pairs limit hand; half limit by rule text",),
                )
            )
        if _is_thirteen_wonders(concealed, exposed):
            special_scores.append(
                HandScore(
                    self.limit,
                    0,
                    0,
                    "Die 13 einzigartigen Wunder",
                    ("required terminals, winds, dragons, and one pair",),
                )
            )

        candidates = list(special_scores)
        for arrangement in _standard_arrangements(concealed, exposed):
            limit_name = self._limit_hand_name(state, player, arrangement, is_winner)
            if limit_name:
                candidates.append(
                    HandScore(self.limit, 0, 0, limit_name, ("limit hand",))
                )
            else:
                candidates.append(
                    self._score_arrangement(state, player, arrangement, is_winner)
                )

        if not candidates:
            candidates.append(self._score_partial_hand(state, player))
        return max(candidates, key=lambda score: score.value)

    def _legal_discard_actions(self, state: GameState, player: int) -> List[str]:
        hand = state.hands[player]
        actions: List[str] = []
        if self._is_complete_hand(hand, state.exposed[player]):
            actions.append("declare:mahjong")

        counts = Counter(hand)
        if state.live_wall:
            for tile in sorted(counts, key=_tile_sort_key):
                if counts[tile] >= 4:
                    actions.append(f"declare:kang:{tile}:concealed")
            for meld in state.exposed[player]:
                if meld.kind == "pong" and meld.open:
                    tile = meld.tiles[0]
                    if counts[tile] >= 1:
                        actions.append(f"declare:kang:{tile}:extend")

        for tile in sorted(counts, key=_tile_sort_key):
            actions.append(f"discard:{tile}")
        return actions

    def _legal_claim_actions(self, state: GameState, player: int) -> List[str]:
        tile = state.last_discard
        if tile is None or state.last_discarder is None:
            return []
        actions = ["pass"]
        if self._can_win_with_tile(state, player, tile):
            actions.append(f"claim:mahjong:{tile}")

        if not state.live_wall:
            return actions

        counts = Counter(state.hands[player])
        if counts[tile] >= 3:
            actions.append(f"claim:kang:{tile}")
        if counts[tile] >= 2:
            actions.append(f"claim:pong:{tile}")
        if player == _next_player(state.last_discarder):
            for sequence in self._possible_tschi_sequences(state.hands[player], tile):
                actions.append("claim:tschi:" + "+".join(sequence))
        return actions

    def _legal_rob_kang_actions(self, state: GameState, player: int) -> List[str]:
        if state.pending_rob is None:
            return []
        _, _, tile = state.pending_rob
        actions = ["pass"]
        if self._can_win_with_tile(state, player, tile):
            actions.append(f"mahjong:rob-kang:{tile}")
        return actions

    def _apply_discard_action(
        self, state: GameState, action: str, history: Tuple[str, ...]
    ) -> GameState:
        player = state.player
        if action == "declare:mahjong":
            source = state.last_draw_source or "self_draw"
            return self._terminal_win(
                state,
                player,
                state.last_draw_tile,
                source,
                history,
                add_tile=False,
            )

        if action.startswith("declare:kang:") and action.endswith(":concealed"):
            tile = action[len("declare:kang:") : -len(":concealed")]
            hand = _remove_tiles(state.hands[player], [tile] * 4)
            meld = Meld("kang", (tile, tile, tile, tile), False, "concealed")
            state = self._set_hand(state, player, hand)
            state = self._add_exposed_meld(state, player, meld)
            state = replace(state, kang_chain=state.kang_chain + 1)
            return self._draw_live(state, player, history)

        if action.startswith("declare:kang:") and action.endswith(":extend"):
            tile = action[len("declare:kang:") : -len(":extend")]
            meld_index = self._find_open_pong(state, player, tile)
            hand = _remove_tiles(state.hands[player], [tile])
            return replace(
                self._set_hand(state, player, hand),
                phase="rob_kang",
                player=_next_player(player),
                pending_rob=(player, meld_index, tile),
                responders_passed=(),
                last_draw_source=None,
                last_draw_tile=None,
                last_draw_was_last_live=False,
                kang_chain=state.kang_chain + 1,
                history=history,
            )

        if action.startswith("discard:"):
            tile = action[len("discard:") :]
            hand = _remove_tiles(state.hands[player], [tile])
            discards = [list(group) for group in state.discards]
            discards[player].append(tile)
            return replace(
                self._set_hand(state, player, hand),
                discards=tuple(tuple(group) for group in discards),
                phase="claim",
                player=_next_player(player),
                last_discard=tile,
                last_discarder=player,
                responders_passed=(),
                pending_rob=None,
                last_draw_source=None,
                last_draw_tile=None,
                last_draw_was_last_live=False,
                kang_chain=0,
                history=history,
            )

        raise ValueError(f"unsupported discard action {action!r}")

    def _apply_claim_action(
        self, state: GameState, action: str, history: Tuple[str, ...]
    ) -> GameState:
        player = state.player
        tile = state.last_discard
        discarder = state.last_discarder
        if tile is None or discarder is None:
            raise ValueError("claim phase without a discard")

        if action == "pass":
            passed = state.responders_passed + (player,)
            next_player = _next_responder(discarder, passed)
            if next_player is not None:
                return replace(state, player=next_player, responders_passed=passed, history=history)
            if not state.live_wall:
                return replace(
                    state,
                    phase="terminal",
                    player=TERMINAL,
                    terminal_reason="wall_empty",
                    responders_passed=passed,
                    history=history,
                )
            return replace(
                state,
                phase="draw",
                player=_next_player(discarder),
                dead_discards=state.dead_discards + (tile,),
                last_discard=None,
                last_discarder=None,
                responders_passed=(),
                history=history,
            )

        if action == f"claim:mahjong:{tile}":
            return self._terminal_win(state, player, tile, "discard", history, add_tile=True)

        if action == f"claim:pong:{tile}":
            hand = _remove_tiles(state.hands[player], [tile, tile])
            meld = Meld("pong", (tile, tile, tile), True, "discard")
            state = self._remove_current_discard(self._set_hand(state, player, hand))
            state = self._add_exposed_meld(state, player, meld)
            return replace(
                state,
                phase="discard",
                player=player,
                last_discard=None,
                last_discarder=None,
                responders_passed=(),
                kang_chain=0,
                history=history,
            )

        if action == f"claim:kang:{tile}":
            hand = _remove_tiles(state.hands[player], [tile, tile, tile])
            meld = Meld("kang", (tile, tile, tile, tile), True, "discard")
            state = self._remove_current_discard(self._set_hand(state, player, hand))
            state = self._add_exposed_meld(state, player, meld)
            state = replace(
                state,
                phase="discard",
                player=player,
                last_discard=None,
                last_discarder=None,
                responders_passed=(),
                kang_chain=1,
            )
            return self._draw_live(state, player, history)

        if action.startswith("claim:tschi:"):
            sequence = tuple(action[len("claim:tschi:") :].split("+"))
            needed = list(sequence)
            try:
                needed.remove(tile)
            except ValueError as exc:
                raise ValueError("tschi action does not include discarded tile") from exc
            hand = _remove_tiles(state.hands[player], needed)
            meld = Meld("tschi", sequence, True, "discard")
            state = self._remove_current_discard(self._set_hand(state, player, hand))
            state = self._add_exposed_meld(state, player, meld)
            return replace(
                state,
                phase="discard",
                player=player,
                last_discard=None,
                last_discarder=None,
                responders_passed=(),
                kang_chain=0,
                history=history,
            )

        raise ValueError(f"unsupported claim action {action!r}")

    def _apply_rob_kang_action(
        self, state: GameState, action: str, history: Tuple[str, ...]
    ) -> GameState:
        if state.pending_rob is None:
            raise ValueError("rob-kang phase without pending kang")
        robbed_player, _, tile = state.pending_rob
        player = state.player

        if action == "pass":
            passed = state.responders_passed + (player,)
            next_player = _next_responder(robbed_player, passed)
            if next_player is not None:
                return replace(state, player=next_player, responders_passed=passed, history=history)
            state = self._complete_pending_kang(state)
            return self._draw_live(replace(state, history=history), robbed_player, history)

        if action == f"mahjong:rob-kang:{tile}":
            return self._terminal_win(
                state, player, tile, "rob_kang", history, add_tile=True
            )

        raise ValueError(f"unsupported rob-kang action {action!r}")

    def _draw_live(
        self, state: GameState, player: int, history: Tuple[str, ...]
    ) -> GameState:
        if not state.live_wall:
            return replace(
                state,
                phase="terminal",
                player=TERMINAL,
                terminal_reason="wall_empty",
                history=history,
            )

        live_wall = list(state.live_wall)
        dead_wall = list(state.dead_wall)
        hands = [list(group) for group in state.hands]
        bonus = [list(group) for group in state.bonus]

        tile = live_wall.pop(0)
        source = "live"
        was_last_live = len(live_wall) == 0

        while _is_bonus(tile):
            bonus[player].append(tile)
            if not dead_wall:
                return replace(
                    state,
                    live_wall=tuple(live_wall),
                    dead_wall=tuple(dead_wall),
                    bonus=tuple(tuple(group) for group in bonus),
                    phase="discard",
                    player=player,
                    last_draw_source="dead",
                    last_draw_tile=tile,
                    last_draw_was_last_live=was_last_live,
                    history=history,
                )
            tile = dead_wall.pop(0)
            source = "dead"
            was_last_live = False

        hands[player].append(tile)
        return replace(
            state,
            hands=tuple(_sorted_tiles(hand) for hand in hands),
            live_wall=tuple(live_wall),
            dead_wall=tuple(dead_wall),
            bonus=tuple(tuple(_sorted_tiles(group)) for group in bonus),
            phase="discard",
            player=player,
            last_draw_source=source,
            last_draw_tile=tile,
            last_draw_was_last_live=was_last_live,
            history=history,
        )

    def _resolve_bonus_from_hand(self, state: GameState, player: int) -> GameState:
        hand = list(state.hands[player])
        dead_wall = list(state.dead_wall)
        bonus = [list(group) for group in state.bonus]

        changed = True
        while changed:
            changed = False
            regular_hand: List[str] = []
            for tile in hand:
                if _is_bonus(tile):
                    bonus[player].append(tile)
                    changed = True
                    if dead_wall:
                        regular_hand.append(dead_wall.pop(0))
                else:
                    regular_hand.append(tile)
            hand = regular_hand

        return replace(
            state,
            hands=_replace_group(state.hands, player, _sorted_tiles(hand)),  # type: ignore[arg-type]
            dead_wall=tuple(dead_wall),
            bonus=tuple(tuple(_sorted_tiles(group)) for group in bonus),
        )

    def _terminal_win(
        self,
        state: GameState,
        winner: int,
        tile: Optional[str],
        source: str,
        history: Tuple[str, ...],
        add_tile: bool,
    ) -> GameState:
        if add_tile and tile is not None:
            hands = [list(group) for group in state.hands]
            hands[winner].append(tile)
            state = replace(state, hands=tuple(_sorted_tiles(hand) for hand in hands))
        if source == "discard":
            state = self._remove_current_discard(state)
        return replace(
            state,
            phase="terminal",
            player=TERMINAL,
            terminal_reason="mahjong",
            winner=winner,
            winning_tile=tile,
            win_source=source,
            last_discard=None,
            responders_passed=(),
            pending_rob=None,
            history=history,
        )

    def _complete_pending_kang(self, state: GameState) -> GameState:
        if state.pending_rob is None:
            return state
        player, meld_index, tile = state.pending_rob
        exposed = [list(group) for group in state.exposed]
        old = exposed[player][meld_index]
        exposed[player][meld_index] = Meld(
            "kang", tuple(old.tiles) + (tile,), True, "extended"
        )
        return replace(
            state,
            exposed=tuple(tuple(group) for group in exposed),
            phase="discard",
            player=player,
            pending_rob=None,
            responders_passed=(),
        )

    def _remove_current_discard(self, state: GameState) -> GameState:
        if state.last_discarder is None or state.last_discard is None:
            return state
        discards = [list(group) for group in state.discards]
        pile = discards[state.last_discarder]
        if pile and pile[-1] == state.last_discard:
            pile.pop()
        else:
            pile.remove(state.last_discard)
        return replace(state, discards=tuple(tuple(group) for group in discards))

    def _set_hand(self, state: GameState, player: int, hand: Iterable[str]) -> GameState:
        return replace(
            state,
            hands=_replace_group(state.hands, player, _sorted_tiles(hand)),  # type: ignore[arg-type]
        )

    def _add_exposed_meld(self, state: GameState, player: int, meld: Meld) -> GameState:
        exposed = [list(group) for group in state.exposed]
        exposed[player].append(meld)
        return replace(state, exposed=tuple(tuple(group) for group in exposed))

    def _find_open_pong(self, state: GameState, player: int, tile: str) -> int:
        for index, meld in enumerate(state.exposed[player]):
            if meld.kind == "pong" and meld.open and meld.tiles[0] == tile:
                return index
        raise ValueError(f"no open pong of {tile!r}")

    def _possible_tschi_sequences(
        self, hand: Sequence[str], discard: str
    ) -> Tuple[Tuple[str, str, str], ...]:
        parsed = _split_suited(discard)
        if not parsed:
            return ()
        suit, rank = parsed
        counts = Counter(hand)
        sequences: List[Tuple[str, str, str]] = []
        for start in range(rank - 2, rank + 1):
            if start < 1 or start + 2 > 9:
                continue
            sequence = tuple(_suited_tile(suit, value) for value in range(start, start + 3))
            needed = list(sequence)
            needed.remove(discard)
            if all(counts[tile] >= needed.count(tile) for tile in set(needed)):
                sequences.append(sequence)  # type: ignore[arg-type]
        return tuple(sequences)

    def _can_win_with_tile(self, state: GameState, player: int, tile: str) -> bool:
        hand = _sorted_tiles(tuple(state.hands[player]) + (tile,))
        return self._is_complete_hand(hand, state.exposed[player])

    def _is_complete_hand(
        self, concealed_tiles: Sequence[str], exposed_melds: Sequence[Meld]
    ) -> bool:
        return bool(
            _standard_arrangements(concealed_tiles, exposed_melds)
            or _is_seven_pairs(concealed_tiles, exposed_melds)
            or _is_thirteen_wonders(concealed_tiles, exposed_melds)
        )

    def _score_partial_hand(self, state: GameState, player: int) -> HandScore:
        counts = Counter(state.hands[player])
        concealed_melds: List[Meld] = []
        for tile in sorted(list(counts), key=_tile_sort_key):
            if counts[tile] >= 3:
                concealed_melds.append(Meld("pong", (tile, tile, tile), False, "concealed"))
                counts[tile] -= 3

        best_pair: Optional[Tuple[str, str]] = None
        best_pair_value = -1
        for tile in sorted(counts, key=_tile_sort_key):
            if counts[tile] >= 2:
                value = self._pair_value(
                    (tile, tile), state.place_winds[player], state.round_wind
                )
                if value > best_pair_value:
                    best_pair = (tile, tile)
                    best_pair_value = value

        arrangement = Arrangement(
            tuple(state.exposed[player]) + tuple(concealed_melds), best_pair
        )
        return self._score_arrangement(state, player, arrangement, False)

    def _score_arrangement(
        self,
        state: GameState,
        player: int,
        arrangement: Arrangement,
        is_winner: bool,
    ) -> HandScore:
        if is_winner:
            arrangement = self._scoring_arrangement_for_winner(state, arrangement)

        details: List[str] = []
        figure_points = 0
        doubles = 0
        player_wind = state.place_winds[player]

        for meld in arrangement.melds:
            points = self._meld_value(meld)
            figure_points += points
            if points:
                details.append(f"{_meld_text(meld)}={points}")

        if arrangement.pair:
            pair_points = self._pair_value(arrangement.pair, player_wind, state.round_wind)
            figure_points += pair_points
            if pair_points:
                details.append(f"pair:{arrangement.pair[0]}={pair_points}")

        bonus_points = len(state.bonus[player]) * 4
        if bonus_points:
            details.append(f"bonus_tiles={bonus_points}")

        base = figure_points + bonus_points
        if is_winner:
            base += 20
            details.append("Mah-Jongg-Ruf=20")
            if state.win_source in ("live", "dead", "initial", "self_draw"):
                base += 2
                details.append("Schlussziegel von der Mauer=2")
            pair_bonus = self._winning_pair_bonus(state, arrangement)
            if pair_bonus:
                base += pair_bonus
                details.append(f"Schlussziegel komplettiert Paar={pair_bonus}")

        doubles += self._bonus_tile_doubles(state, player, details)
        doubles += self._meld_doubles(state, player, arrangement, details)

        if is_winner:
            if figure_points == 0:
                doubles += 1
                details.append("Null-Punkte-Hand=1x")
            if not any(meld.kind == "tschi" for meld in arrangement.melds):
                doubles += 1
                details.append("Kein Chi=1x")
            if (
                state.win_source not in ("discard", "rob_kang")
                and all(not meld.open for meld in arrangement.melds)
            ):
                doubles += 1
                details.append("Alle Figuren verdeckt=1x")
            doubles += self._winner_tile_pattern_doubles(arrangement, details)
            if state.win_source == "dead":
                doubles += 1
                details.append("Schlussziegel von der toten Mauer=1x")
            if state.win_source == "live" and state.last_draw_was_last_live:
                doubles += 1
                details.append("mit dem letzten Ziegel der Mauer gewonnen=1x")
            if state.win_source == "discard" and not state.live_wall:
                doubles += 1
                details.append("Schlussziegel ist letzter abgelegter Ziegel=1x")
            if state.win_source == "rob_kang":
                doubles += 1
                details.append("Beraubung des Kang=1x")
            if state.win_source == "initial":
                doubles += 1
                details.append("Mah-Jongg nach Ruf zu Beginn=1x")

        value = base * (2**doubles)
        if self.limit and value > self.limit:
            value = self.limit
            details.append(f"Limit={self.limit}")
        return HandScore(value, base, doubles, None, tuple(details))

    def _scoring_arrangement_for_winner(
        self, state: GameState, arrangement: Arrangement
    ) -> Arrangement:
        if state.win_source not in ("discard", "rob_kang") or not state.winning_tile:
            return arrangement
        melds = list(arrangement.melds)
        for index, meld in enumerate(melds):
            if not meld.open and state.winning_tile in meld.tiles:
                melds[index] = replace(meld, open=True, source=state.win_source)
                return Arrangement(tuple(melds), arrangement.pair)
        return arrangement

    def _meld_value(self, meld: Meld) -> int:
        if meld.kind == "tschi":
            return 0
        tile = meld.tiles[0]
        honor = _is_honor(tile)
        terminal = _is_terminal_suited(tile)
        if meld.kind == "pong":
            if honor:
                return 4 if meld.open else 8
            if terminal:
                return 4 if meld.open else 8
            return 2 if meld.open else 4
        if meld.kind == "kang":
            if honor:
                return 16 if meld.open else 32
            if terminal:
                return 16 if meld.open else 32
            return 8 if meld.open else 16
        return 0

    def _pair_value(
        self, pair: Tuple[str, str], player_wind: str, round_wind: str
    ) -> int:
        tile = pair[0]
        value = 0
        if _is_dragon(tile):
            value += 2
        if tile == player_wind:
            value += 2
        if tile == round_wind:
            value += 2
        return value

    def _bonus_tile_doubles(
        self, state: GameState, player: int, details: List[str]
    ) -> int:
        tiles = set(state.bonus[player])
        doubles = 0
        wind_number = WINDS.index(state.place_winds[player]) + 1
        if f"Blume{wind_number}" in tiles and f"Jahreszeit{wind_number}" in tiles:
            doubles += 1
            details.append("beide Bonusziegel des eigenen Windes=1x")
        if all(tile in tiles for tile in FLOWERS):
            doubles += 1
            details.append("alle Blumenziegel=1x")
        if all(tile in tiles for tile in SEASONS):
            doubles += 1
            details.append("alle Jahreszeitenziegel=1x")
        return doubles

    def _meld_doubles(
        self, state: GameState, player: int, arrangement: Arrangement, details: List[str]
    ) -> int:
        doubles = 0
        player_wind = state.place_winds[player]
        dragon_melds = 0
        wind_melds = 0
        dragon_pair = arrangement.pair is not None and _is_dragon(arrangement.pair[0])
        wind_pair = arrangement.pair is not None and _is_wind(arrangement.pair[0])
        concealed_pongs = 0

        for meld in arrangement.melds:
            if meld.kind not in ("pong", "kang"):
                continue
            tile = meld.tiles[0]
            if not meld.open:
                concealed_pongs += 1
            if _is_dragon(tile):
                dragon_melds += 1
                doubles += 1
                details.append(f"{meld.kind} aus Drachen=1x")
            if _is_wind(tile):
                wind_melds += 1
            if tile == player_wind:
                doubles += 1
                details.append(f"{meld.kind} des eigenen Windes=1x")
            if tile == state.round_wind:
                doubles += 1
                details.append(f"{meld.kind} des Rundenwindes=1x")

        if concealed_pongs >= 3:
            doubles += 1
            details.append("Drei verdeckte Pong=1x")
        if dragon_melds == 3:
            doubles += 2
            details.append("Grosse Drei Drachen=2x")
        elif dragon_melds == 2 and dragon_pair:
            doubles += 1
            details.append("Kleine Drei Drachen=1x")
        if wind_melds == 4:
            doubles += 2
            details.append("Grosse Vier Freuden=2x")
        elif wind_melds == 3 and wind_pair:
            doubles += 1
            details.append("Kleine Vier Freuden=1x")
        return doubles

    def _winner_tile_pattern_doubles(
        self, arrangement: Arrangement, details: List[str]
    ) -> int:
        tiles = _arrangement_tiles(arrangement)
        if not tiles:
            return 0
        suited_suits = {_suit(tile) for tile in tiles if _is_suited(tile)}
        has_honor = any(_is_honor(tile) for tile in tiles)
        doubles = 0
        if len(suited_suits) == 1 and has_honor:
            doubles += 1
            details.append("Nur Ziegel einer Farbe und Bildziegel=1x")
        elif len(suited_suits) == 1 and not has_honor:
            doubles += 3
            details.append("Nur Ziegel einer Farbe=3x")
        if all(_is_terminal_or_honor(tile) for tile in tiles):
            doubles += 1
            details.append("Nur Hauptziegel=1x")
        if all(_is_honor(tile) for tile in tiles):
            doubles += 2
            details.append("Nur Bildziegel=2x")
        return doubles

    def _winning_pair_bonus(self, state: GameState, arrangement: Arrangement) -> int:
        if not state.winning_tile or not arrangement.pair:
            return 0
        tile = arrangement.pair[0]
        if tile != state.winning_tile:
            return 0
        if _is_suited(tile):
            return 2 if _rank(tile) in (2, 3, 4, 5, 6, 7, 8) else 4
        if _is_honor(tile):
            return 4
        return 0

    def _limit_hand_name(
        self,
        state: GameState,
        player: int,
        arrangement: Arrangement,
        is_winner: bool,
    ) -> Optional[str]:
        tiles = _arrangement_tiles(arrangement)
        if not tiles:
            return None
        pongs_or_kangs = [
            meld for meld in arrangement.melds if meld.kind in ("pong", "kang")
        ]
        dragon_melds = [meld for meld in pongs_or_kangs if _is_dragon(meld.tiles[0])]
        wind_melds = [meld for meld in pongs_or_kangs if _is_wind(meld.tiles[0])]
        kongs = [meld for meld in arrangement.melds if meld.kind == "kang"]
        all_concealed = all(not meld.open for meld in arrangement.melds) and (
            not is_winner or state.win_source not in ("discard", "rob_kang")
        )
        suited_suits = {_suit(tile) for tile in tiles if _is_suited(tile)}
        has_honor = any(_is_honor(tile) for tile in tiles)

        if all(_is_honor(tile) for tile in tiles):
            return "Reine Bildziegel-Hand"
        if all(_is_suited(tile) and _rank(tile) in (1, 9) for tile in tiles):
            return "Koepfe und Schwaenze"
        if all(tile in GREEN_TILES for tile in tiles):
            return "Die kaiserliche gruene Hand"
        if len(kongs) == 4:
            return "Vierfacher Reichtum"
        if len(dragon_melds) == 3 and len(pongs_or_kangs) >= 4:
            return "Die drei grossen Gelehrten"
        if len(wind_melds) == 4:
            return "Vier Segen ueber der Tuer"
        if self._is_winding_snake(arrangement):
            return "Die sich windende Schlange"
        if len(suited_suits) == 1 and not has_honor and all_concealed:
            return "Verdecktes reines Farbspiel"
        if self._is_nine_gates(state.hands[player], state.exposed[player]):
            return "Neun Laternen"
        if (
            len(pongs_or_kangs) == 4
            and all(not meld.open for meld in pongs_or_kangs)
            and is_winner
            and state.win_source in ("live", "dead", "initial", "self_draw")
        ):
            return "Verborgener Schatz"

        if is_winner:
            if state.win_source == "initial" and state.place_winds[player] == "Ost":
                return "Segen des Himmels"
            if (
                state.win_source == "discard"
                and state.last_discarder is not None
                and state.place_winds[state.last_discarder] == "Ost"
                and state.place_winds[player] != "Ost"
                and sum(len(pile) for pile in state.discards) == 0
                and len(state.history) <= 3
            ):
                return "Segen der Erde"
            if state.kang_chain >= 2:
                return "Doppeltes Glueck"
            if state.win_source == "dead" and state.winning_tile == "Kreis-5":
                return "Die Pflaumenbluete vom Dach pfluecken"
            if (
                state.win_source == "live"
                and state.last_draw_was_last_live
                and state.winning_tile == "Kreis-1"
            ):
                return "Den Mond vom Meeresgrund holen"
            if state.win_source == "rob_kang" and state.winning_tile == "Bambus-2":
                return "Einen tragenden Pfosten beanspruchen"
        return None

    def _is_winding_snake(self, arrangement: Arrangement) -> bool:
        tiles = _arrangement_tiles(arrangement)
        suits = {_suit(tile) for tile in tiles if _is_suited(tile)}
        if len(suits) != 1 or any(not _is_suited(tile) for tile in tiles):
            return False
        pair_rank = _rank(arrangement.pair[0]) if arrangement.pair else None
        pong_ranks = {
            _rank(meld.tiles[0])
            for meld in arrangement.melds
            if meld.kind in ("pong", "kang")
        }
        chi_count = sum(1 for meld in arrangement.melds if meld.kind == "tschi")
        return pong_ranks == {1, 9} and pair_rank in {2, 5, 8} and chi_count == 2

    def _is_nine_gates(
        self, concealed_tiles: Sequence[str], exposed_melds: Sequence[Meld]
    ) -> bool:
        if exposed_melds or len(concealed_tiles) != 14:
            return False
        suits = {_suit(tile) for tile in concealed_tiles if _is_suited(tile)}
        if len(suits) != 1 or any(not _is_suited(tile) for tile in concealed_tiles):
            return False
        counts = Counter(_rank(tile) for tile in concealed_tiles)
        return (
            counts[1] >= 3
            and counts[9] >= 3
            and all(counts[rank] >= 1 for rank in range(2, 9))
        )
```