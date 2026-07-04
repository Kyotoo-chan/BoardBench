Open questions / assumptions:
- This implements one 4-player hand only; wind rotation, rounds, dice wall break, flowers/seasons, and dead-wall replacement are omitted.
- Tile labels not fully named in the text are explicit assumptions: third suit is `Farbe3`; unnamed dragons are `Drache1`/`Drache2`.
- Multiple discard reactions are resolved by asking players counter-clockwise one at a time; the rule text does not fully specify conflict priority.
- Scoring implements the listed core figure points, settlement, and detectable doubles/limit hands; event hands needing omitted match/dead-wall history are documented as gaps in comments.

```python
from dataclasses import dataclass, replace
from functools import lru_cache
from collections import Counter
from typing import Optional, Tuple, List

TERMINAL = -1
CHANCE = -2
SIMULTANEOUS = -3

NUM_PLAYERS = 4
DEFAULT_LIMIT = 500

# Assumed labels where the German text is incomplete:
# It names Bambus and Kreis; the third numbered suit is not named, so "Farbe3" is used.
# It names Gruener Drachen; the other two dragons are not named.
SUITS = ("Bambus", "Kreis", "Farbe3")
WINDS = ("Osten", "Sueden", "Westen", "Norden")
DRAGONS = ("Drache1", "Drache2", "GruenerDrache")
ROUND_WIND_DEFAULT = "Osten"

TILE_TYPES = tuple(f"{s}-{r}" for s in SUITS for r in range(1, 10)) + WINDS + DRAGONS
TILE_TO_INDEX = {t: i for i, t in enumerate(TILE_TYPES)}
FULL_WALL = tuple(t for t in TILE_TYPES for _ in range(4))

# Three passes of four tiles per player, then 13th tile to all and 14th to East.
DEAL_TARGET_SEQUENCE = (
    tuple(p for _round in range(3) for p in range(NUM_PLAYERS) for _ in range(4))
    + (0, 1, 2, 3, 0)
)

GREEN_TILES = {
    "Bambus-2", "Bambus-3", "Bambus-4", "Bambus-6", "Bambus-8", "GruenerDrache"
}


@dataclass(frozen=True)
class Meld:
    kind: str  # "chi", "pong", "kang"
    tiles: Tuple[str, ...]
    concealed: bool = False  # concealed for scoring; concealed kongs are still public melds here


@dataclass(frozen=True)
class HandAnalysis:
    melds: Tuple[Meld, ...]
    pair_tile: Optional[str] = None
    special: str = ""  # "", "seven_pairs", "thirteen_wonders"


@dataclass(frozen=True)
class GameState:
    phase: str
    hands: Tuple[Tuple[str, ...], ...]
    melds: Tuple[Tuple[Meld, ...], ...]
    remaining: Tuple[str, ...]

    current: int = 0
    deal_index: int = 0

    discard_tile: Optional[str] = None
    discard_from: Optional[int] = None
    reaction_pos: int = 0

    pending_draw_player: Optional[int] = None
    pending_draw_reason: str = ""

    pending_kang_player: Optional[int] = None
    pending_kang_tile: Optional[str] = None
    kang_reaction_pos: int = 0

    dead_discards: Tuple[str, ...] = ()

    winner: Optional[int] = None
    terminal_reason: str = ""
    win_source: str = ""
    win_tile: Optional[str] = None
    win_kind: str = ""
    win_live_count_before: int = 0
    win_discard_from: Optional[int] = None

    round_wind: str = ROUND_WIND_DEFAULT
    seat_winds: Tuple[str, ...] = WINDS

    may_declare_self: bool = False
    last_draw_player: Optional[int] = None
    last_draw_source: str = ""
    last_draw_tile: Optional[str] = None
    last_draw_live_count_before: int = 0

    discard_count: int = 0
    history: Tuple[str, ...] = ()


def tile_key(tile: str):
    return (TILE_TO_INDEX.get(tile, 999), tile)


def sorted_tiles(tiles):
    return tuple(sorted(tiles, key=tile_key))


def unique_tiles(tiles):
    return tuple(sorted(set(tiles), key=tile_key))


def suited_info(tile: str):
    if "-" not in tile:
        return None
    suit, rank_s = tile.rsplit("-", 1)
    if suit in SUITS and rank_s.isdigit():
        rank = int(rank_s)
        if 1 <= rank <= 9:
            return suit, rank
    return None


def is_suited(tile: str) -> bool:
    return suited_info(tile) is not None


def is_wind(tile: str) -> bool:
    return tile in WINDS


def is_dragon(tile: str) -> bool:
    return tile in DRAGONS


def is_honor(tile: str) -> bool:
    return is_wind(tile) or is_dragon(tile)


def is_terminal_suited(tile: str) -> bool:
    info = suited_info(tile)
    return info is not None and info[1] in (1, 9)


def is_main_tile(tile: str) -> bool:
    return is_honor(tile) or is_terminal_suited(tile)


def make_suited_tile(suit: str, rank: int) -> str:
    return f"{suit}-{rank}"


def sequence_tiles(suit: str, start: int) -> Tuple[str, str, str]:
    return (make_suited_tile(suit, start), make_suited_tile(suit, start + 1), make_suited_tile(suit, start + 2))


def counter_to_tiles(counter: Counter) -> Tuple[str, ...]:
    out = []
    for tile in sorted(counter.keys(), key=tile_key):
        out.extend([tile] * counter[tile])
    return tuple(out)


def add_tiles(tiles, to_add) -> Tuple[str, ...]:
    return sorted_tiles(tuple(tiles) + tuple(to_add))


def remove_tiles(tiles, to_remove) -> Tuple[str, ...]:
    counts = Counter(tiles)
    for tile in to_remove:
        if counts.get(tile, 0) <= 0:
            raise ValueError(f"Cannot remove missing tile {tile}")
        counts[tile] -= 1
        if counts[tile] == 0:
            del counts[tile]
    return counter_to_tiles(counts)


def has_tiles(tiles, needed) -> bool:
    have = Counter(tiles)
    need = Counter(needed)
    return all(have.get(t, 0) >= c for t, c in need.items())


def next_player(player: int) -> int:
    return (player + 1) % NUM_PLAYERS


def reaction_player(source: int, pos: int) -> int:
    return (source + 1 + pos) % NUM_PLAYERS


def set_player_tuple(items, player: int, value):
    lst = list(items)
    lst[player] = value
    return tuple(lst)


def append_meld(melds, player: int, meld: Meld):
    return set_player_tuple(melds, player, melds[player] + (meld,))


def replace_open_pong_with_kang(melds, player: int, tile: str):
    player_melds = list(melds[player])
    for i, meld in enumerate(player_melds):
        if meld.kind == "pong" and not meld.concealed and meld.tiles[0] == tile:
            player_melds[i] = Meld("kang", (tile, tile, tile, tile), concealed=False)
            return set_player_tuple(melds, player, tuple(player_melds))
    raise ValueError("No matching open pong to extend")


def possible_chi_sequences_for_tile(tile: str):
    info = suited_info(tile)
    if info is None:
        return ()
    suit, rank = info
    out = []
    for start in (rank - 2, rank - 1, rank):
        if 1 <= start <= 7:
            out.append((suit, start))
    return tuple(out)


def needed_for_chi(discard_tile: str, suit: str, start: int):
    seq = list(sequence_tiles(suit, start))
    seq.remove(discard_tile)
    return tuple(seq)


def counts_tuple_from_counter(counter: Counter) -> Tuple[int, ...]:
    return tuple(counter.get(t, 0) for t in TILE_TYPES)


@lru_cache(maxsize=None)
def _can_form_melds_tuple(counts_tuple: Tuple[int, ...], needed: int) -> bool:
    total = sum(counts_tuple)
    if total != needed * 3:
        return False
    if needed == 0:
        return total == 0

    try:
        i = next(i for i, c in enumerate(counts_tuple) if c > 0)
    except StopIteration:
        return False

    tile = TILE_TYPES[i]

    if counts_tuple[i] >= 3:
        new_counts = list(counts_tuple)
        new_counts[i] -= 3
        if _can_form_melds_tuple(tuple(new_counts), needed - 1):
            return True

    info = suited_info(tile)
    if info is not None:
        suit, rank = info
        if rank <= 7:
            t1 = make_suited_tile(suit, rank + 1)
            t2 = make_suited_tile(suit, rank + 2)
            j = TILE_TO_INDEX[t1]
            k = TILE_TO_INDEX[t2]
            if counts_tuple[j] > 0 and counts_tuple[k] > 0:
                new_counts = list(counts_tuple)
                new_counts[i] -= 1
                new_counts[j] -= 1
                new_counts[k] -= 1
                if _can_form_melds_tuple(tuple(new_counts), needed - 1):
                    return True

    return False


@lru_cache(maxsize=None)
def _decompose_melds_tuple(counts_tuple: Tuple[int, ...], needed: int):
    total = sum(counts_tuple)
    if total != needed * 3:
        return ()
    if needed == 0:
        return ((),) if total == 0 else ()

    try:
        i = next(i for i, c in enumerate(counts_tuple) if c > 0)
    except StopIteration:
        return ()

    tile = TILE_TYPES[i]
    results = []

    if counts_tuple[i] >= 3:
        new_counts = list(counts_tuple)
        new_counts[i] -= 3
        meld = Meld("pong", (tile, tile, tile), concealed=True)
        for rest in _decompose_melds_tuple(tuple(new_counts), needed - 1):
            results.append((meld,) + rest)

    info = suited_info(tile)
    if info is not None:
        suit, rank = info
        if rank <= 7:
            t1 = make_suited_tile(suit, rank + 1)
            t2 = make_suited_tile(suit, rank + 2)
            j = TILE_TO_INDEX[t1]
            k = TILE_TO_INDEX[t2]
            if counts_tuple[j] > 0 and counts_tuple[k] > 0:
                new_counts = list(counts_tuple)
                new_counts[i] -= 1
                new_counts[j] -= 1
                new_counts[k] -= 1
                meld = Meld("chi", sequence_tiles(suit, rank), concealed=True)
                for rest in _decompose_melds_tuple(tuple(new_counts), needed - 1):
                    results.append((meld,) + rest)

    return tuple(results)


def can_form_melds_fixed_pair(hand, existing_meld_count: int) -> bool:
    needed = 4 - existing_meld_count
    if needed < 0 or len(hand) != needed * 3:
        return False
    return _can_form_melds_tuple(counts_tuple_from_counter(Counter(hand)), needed)


def is_standard_complete(hand, existing_meld_count: int) -> bool:
    needed = 4 - existing_meld_count
    if needed < 0 or len(hand) != needed * 3 + 2:
        return False
    counts = Counter(hand)
    for tile in unique_tiles(hand):
        if counts[tile] >= 2:
            c = counts.copy()
            c[tile] -= 2
            if _can_form_melds_tuple(counts_tuple_from_counter(c), needed):
                return True
    return False


def standard_analyses(hand, exposed_melds) -> List[HandAnalysis]:
    existing = len(exposed_melds)
    needed = 4 - existing
    if needed < 0 or len(hand) != needed * 3 + 2:
        return []
    counts = Counter(hand)
    analyses = []
    for pair_tile in unique_tiles(hand):
        if counts[pair_tile] >= 2:
            c = counts.copy()
            c[pair_tile] -= 2
            for concealed_melds in _decompose_melds_tuple(counts_tuple_from_counter(c), needed):
                analyses.append(HandAnalysis(tuple(exposed_melds) + tuple(concealed_melds), pair_tile, ""))
    return analyses


def is_seven_pairs(hand) -> bool:
    counts = Counter(hand)
    return len(hand) == 14 and len(counts) == 7 and all(c == 2 for c in counts.values())


def is_thirteen_wonders(hand) -> bool:
    required = set()
    for suit in SUITS:
        required.add(make_suited_tile(suit, 1))
        required.add(make_suited_tile(suit, 9))
    required.update(WINDS)
    required.update(DRAGONS)

    counts = Counter(hand)
    if len(hand) != 14:
        return False
    if any(t not in required for t in counts):
        return False
    if any(counts.get(t, 0) < 1 for t in required):
        return False
    return sum(1 for t in required if counts.get(t, 0) == 2) == 1


def winning_claim_actions(hand, meld_count: int, tile: str, player: int, tag: str):
    actions = []
    counts = Counter(hand)

    # Listed order: Pong to Mahjong, Tschi to Mahjong, Paar to Mahjong.
    if counts.get(tile, 0) >= 2 and meld_count < 4:
        rem = remove_tiles(hand, (tile, tile))
        if is_standard_complete(rem, meld_count + 1):
            actions.append((tag, player, "pong", tile))

    if meld_count < 4:
        for suit, start in possible_chi_sequences_for_tile(tile):
            needed = needed_for_chi(tile, suit, start)
            if has_tiles(hand, needed):
                rem = remove_tiles(hand, needed)
                if is_standard_complete(rem, meld_count + 1):
                    actions.append((tag, player, "chi", (suit, start)))

    if counts.get(tile, 0) >= 1:
        rem = remove_tiles(hand, (tile,))
        if can_form_melds_fixed_pair(rem, meld_count):
            actions.append((tag, player, "pair", tile))

    # Special hands explicitly listed as goals.
    if meld_count == 0:
        h = add_tiles(hand, (tile,))
        if is_seven_pairs(h) or is_thirteen_wonders(h):
            actions.append((tag, player, "special", tile))

    return actions


def meld_points(meld: Meld) -> int:
    if meld.kind == "chi":
        return 0

    tile = meld.tiles[0]
    info = suited_info(tile)
    simple_suited = info is not None and 2 <= info[1] <= 8

    if meld.kind == "pong":
        if simple_suited:
            return 4 if meld.concealed else 2
        return 8 if meld.concealed else 4

    if meld.kind == "kang":
        if simple_suited:
            return 16 if meld.concealed else 8
        return 32 if meld.concealed else 16

    return 0


def pair_points(tile: str, player: int, state: GameState) -> int:
    points = 0
    if is_dragon(tile):
        points += 2
    if tile == state.seat_winds[player]:
        points += 2
    if tile == state.round_wind:
        points += 2
    return points


def pair_completion_bonus(tile: Optional[str]) -> int:
    if tile is None:
        return 0
    info = suited_info(tile)
    if info is not None:
        return 2 if 2 <= info[1] <= 8 else 4
    if is_honor(tile):
        return 4
    return 0


def analysis_tiles(analysis: HandAnalysis, concealed_hand) -> Tuple[str, ...]:
    if analysis.special:
        return sorted_tiles(concealed_hand)
    tiles = []
    for meld in analysis.melds:
        tiles.extend(meld.tiles)
    if analysis.pair_tile is not None:
        tiles.extend([analysis.pair_tile, analysis.pair_tile])
    return sorted_tiles(tiles)


def suits_and_honor_count(tiles):
    suits = set()
    honors = 0
    for tile in tiles:
        info = suited_info(tile)
        if info is None:
            honors += 1
        else:
            suits.add(info[0])
    return suits, honors


def pattern_doubles(melds, pair_tiles, player: int, state: GameState) -> int:
    doubles = 0
    own_wind = state.seat_winds[player]
    round_wind = state.round_wind

    for meld in melds:
        if meld.kind not in ("pong", "kang"):
            continue
        tile = meld.tiles[0]
        if is_dragon(tile):
            doubles += 1
        if tile == own_wind:
            doubles += 1
        if tile == round_wind:
            doubles += 1

    # Literal table says "Drei verdeckte Pong"; Kangs are not counted here.
    concealed_pongs = sum(1 for m in melds if m.kind == "pong" and m.concealed)
    if concealed_pongs >= 3:
        doubles += 1

    dragon_sets = sum(1 for m in melds if m.kind in ("pong", "kang") and is_dragon(m.tiles[0]))
    wind_sets = sum(1 for m in melds if m.kind in ("pong", "kang") and is_wind(m.tiles[0]))
    dragon_pair = any(is_dragon(t) for t in pair_tiles)
    wind_pair = any(is_wind(t) for t in pair_tiles)

    if dragon_sets == 2 and dragon_pair:
        doubles += 1
    if dragon_sets == 3:
        doubles += 2
    if wind_sets == 3 and wind_pair:
        doubles += 1
    if wind_sets == 4:
        doubles += 2

    return doubles


def all_hand_doubles(analysis: HandAnalysis, player: int, state: GameState) -> int:
    pair_tiles = [analysis.pair_tile] if analysis.pair_tile is not None else []
    return pattern_doubles(analysis.melds, pair_tiles, player, state)


def mahjong_doubles(analysis: HandAnalysis, concealed_hand, player: int, state: GameState) -> int:
    # Omitted due unmodeled information: flowers/seasons, dead-wall win,
    # exact "only possible tile", and "Null-Punkte-Hand".
    doubles = 0
    tiles = analysis_tiles(analysis, concealed_hand)

    if all(m.kind != "chi" for m in analysis.melds):
        doubles += 1

    if analysis.melds and all(m.concealed for m in analysis.melds) and state.win_source in ("self_draw", "initial_deal"):
        doubles += 1

    suits, honors = suits_and_honor_count(tiles)
    if len(suits) == 1 and honors > 0:
        doubles += 1
    if len(suits) == 1 and honors == 0:
        doubles += 3
    if tiles and all(is_main_tile(t) for t in tiles):
        doubles += 1
    if tiles and all(is_honor(t) for t in tiles):
        doubles += 2

    if state.win_source == "self_draw" and state.win_live_count_before == 1:
        doubles += 1
    if state.win_source == "discard" and len(state.remaining) == 0:
        doubles += 1
    if state.win_source == "rob_kang":
        doubles += 1
    if state.win_source == "initial_deal":
        doubles += 1

    return doubles


def is_winding_snake(analysis: HandAnalysis) -> bool:
    if analysis.special or analysis.pair_tile is None:
        return False
    tiles = analysis_tiles(analysis, ())
    suits, honors = suits_and_honor_count(tiles)
    if honors or len(suits) != 1:
        return False

    pair_info = suited_info(analysis.pair_tile)
    if pair_info is None or pair_info[1] not in (2, 5, 8):
        return False

    chi_count = sum(1 for m in analysis.melds if m.kind == "chi")
    has_1 = any(m.kind in ("pong", "kang") and suited_info(m.tiles[0]) and suited_info(m.tiles[0])[1] == 1 for m in analysis.melds)
    has_9 = any(m.kind in ("pong", "kang") and suited_info(m.tiles[0]) and suited_info(m.tiles[0])[1] == 9 for m in analysis.melds)
    return chi_count == 2 and has_1 and has_9


def is_nine_lanterns(hand) -> bool:
    if len(hand) != 14:
        return False
    infos = [suited_info(t) for t in hand]
    if any(i is None for i in infos):
        return False
    suits = {i[0] for i in infos}
    if len(suits) != 1:
        return False
    ranks = Counter(i[1] for i in infos)
    if ranks[1] < 3 or ranks[9] < 3:
        return False
    return all(ranks[r] >= 1 for r in range(2, 9))


def format_tiles(tiles) -> str:
    if not tiles:
        return "-"
    counts = Counter(tiles)
    return " ".join(f"{t}x{counts[t]}" if counts[t] > 1 else t for t in sorted(counts, key=tile_key))


def format_meld(meld: Meld) -> str:
    vis = "concealed" if meld.concealed else "open"
    return f"{meld.kind}:{vis}:{'+'.join(meld.tiles)}"


def format_melds(melds) -> str:
    return " ".join(format_meld(m) for m in melds) if melds else "-"


def player_token(player: int) -> str:
    return f"p{player}"


def parse_player_token(token: str) -> int:
    if not token.startswith("p") or not token[1:].isdigit():
        raise ValueError(f"Bad player token: {token}")
    player = int(token[1:])
    if not 0 <= player < NUM_PLAYERS:
        raise ValueError(f"Player out of range: {token}")
    return player


def chi_name(suit: str, start: int) -> str:
    return "+".join(sequence_tiles(suit, start))


def parse_chi_name(name: str):
    tiles = name.split("+")
    if len(tiles) != 3:
        raise ValueError(f"Bad chi name: {name}")
    info = suited_info(tiles[0])
    if info is None:
        raise ValueError(f"Bad chi start: {name}")
    suit, start = info
    if tuple(tiles) != sequence_tiles(suit, start):
        raise ValueError(f"Non-consecutive chi: {name}")
    return suit, start


class Game:
    """A compact, explicit Mahjong hand model from the provided German rule text.

    Simplifications are intentional:
    - one hand only, fixed seats p0=Osten, p1=Sueden, p2=Westen, p3=Norden;
    - flowers/seasons and dead wall are omitted;
    - remaining undealt tiles form the live wall;
    - stochastic setup/draws are explicit chance actions.
    """

    def __init__(self, limit: int = DEFAULT_LIMIT):
        self.num_players = NUM_PLAYERS
        self.limit = limit

    def initial_state(self) -> GameState:
        return GameState(
            phase="deal",
            hands=tuple(() for _ in range(NUM_PLAYERS)),
            melds=tuple(() for _ in range(NUM_PLAYERS)),
            remaining=FULL_WALL,
        )

    def current_player(self, state: GameState) -> int:
        if state.phase == "terminal":
            return TERMINAL
        if state.phase in ("deal", "draw_live"):
            return CHANCE
        if state.phase == "discard":
            return state.current
        if state.phase == "reaction" and state.discard_from is not None:
            return reaction_player(state.discard_from, state.reaction_pos)
        if state.phase == "kang_reaction" and state.pending_kang_player is not None:
            return reaction_player(state.pending_kang_player, state.kang_reaction_pos)
        return TERMINAL

    def legal_actions(self, state: GameState):
        if self.is_terminal(state):
            return []

        if state.phase == "deal":
            if state.deal_index >= len(DEAL_TARGET_SEQUENCE):
                return []
            target = DEAL_TARGET_SEQUENCE[state.deal_index]
            return [("chance_deal", target, t) for t in unique_tiles(state.remaining)]

        if state.phase == "draw_live":
            if state.pending_draw_player is None or not state.remaining:
                return []
            p = state.pending_draw_player
            reason = state.pending_draw_reason
            return [("chance_draw", p, reason, t) for t in unique_tiles(state.remaining)]

        if state.phase == "discard":
            p = state.current
            hand = state.hands[p]
            actions = []

            if state.may_declare_self and self._can_self_mahjong(state, p):
                actions.append(("declare_mahjong", p))

            if state.remaining:
                counts = Counter(hand)
                for tile in unique_tiles(hand):
                    if counts[tile] == 4:
                        actions.append(("declare_kang", p, "concealed", tile))
                for meld in state.melds[p]:
                    if meld.kind == "pong" and not meld.concealed and counts.get(meld.tiles[0], 0) >= 1:
                        actions.append(("declare_kang", p, "extend_pong", meld.tiles[0]))

            actions.extend(("discard", p, t) for t in unique_tiles(hand))
            return actions

        if state.phase == "reaction":
            if state.discard_tile is None or state.discard_from is None:
                return []
            p = reaction_player(state.discard_from, state.reaction_pos)
            tile = state.discard_tile
            hand = state.hands[p]
            counts = Counter(hand)
            actions = []

            actions.extend(winning_claim_actions(hand, len(state.melds[p]), tile, p, "claim_mahjong"))

            if state.remaining and counts.get(tile, 0) >= 3:
                actions.append(("claim_kang", p, tile))
            if counts.get(tile, 0) >= 2:
                actions.append(("claim_pong", p, tile))
            if p == next_player(state.discard_from):
                for suit, start in possible_chi_sequences_for_tile(tile):
                    needed = needed_for_chi(tile, suit, start)
                    if has_tiles(hand, needed):
                        actions.append(("claim_chi", p, suit, start))

            actions.append(("pass", p))
            return actions

        if state.phase == "kang_reaction":
            if state.pending_kang_player is None or state.pending_kang_tile is None:
                return []
            p = reaction_player(state.pending_kang_player, state.kang_reaction_pos)
            tile = state.pending_kang_tile
            actions = winning_claim_actions(state.hands[p], len(state.melds[p]), tile, p, "rob_mahjong")
            actions.append(("pass", p))
            return actions

        return []

    def chance_outcomes(self, state: GameState):
        if self.current_player(state) != CHANCE or not state.remaining:
            return []
        counts = Counter(state.remaining)
        total = len(state.remaining)
        return [(a, counts[a[-1]] / total) for a in self.legal_actions(state)]

    def apply_action(self, state: GameState, action):
        legal = self.legal_actions(state)
        if action not in legal:
            raise ValueError(f"Illegal action {action!r} in phase {state.phase}")

        name = self.action_to_name(action)
        hist = state.history + (name,)
        tag = action[0]

        if tag == "chance_deal":
            _, target, tile = action
            hands = set_player_tuple(state.hands, target, add_tiles(state.hands[target], (tile,)))
            remaining = remove_tiles(state.remaining, (tile,))
            deal_index = state.deal_index + 1
            if deal_index == len(DEAL_TARGET_SEQUENCE):
                return replace(
                    state, phase="discard", current=0, hands=hands, remaining=remaining,
                    deal_index=deal_index, may_declare_self=True,
                    last_draw_player=0, last_draw_source="initial_deal",
                    last_draw_tile=None, last_draw_live_count_before=0,
                    history=hist
                )
            return replace(state, hands=hands, remaining=remaining, deal_index=deal_index, history=hist)

        if tag == "chance_draw":
            _, p, reason, tile = action
            live_before = len(state.remaining)
            hands = set_player_tuple(state.hands, p, add_tiles(state.hands[p], (tile,)))
            remaining = remove_tiles(state.remaining, (tile,))
            return replace(
                state, phase="discard", current=p, hands=hands, remaining=remaining,
                pending_draw_player=None, pending_draw_reason="",
                may_declare_self=True,
                last_draw_player=p, last_draw_source="wall",
                last_draw_tile=tile, last_draw_live_count_before=live_before,
                discard_tile=None, discard_from=None, reaction_pos=0,
                history=hist
            )

        if tag == "discard":
            _, p, tile = action
            hands = set_player_tuple(state.hands, p, remove_tiles(state.hands[p], (tile,)))
            return replace(
                state, phase="reaction", current=p, hands=hands,
                discard_tile=tile, discard_from=p, reaction_pos=0,
                may_declare_self=False, discard_count=state.discard_count + 1,
                history=hist
            )

        if tag == "declare_mahjong":
            _, p = action
            source = "initial_deal" if state.last_draw_source == "initial_deal" else "self_draw"
            return replace(
                state, phase="terminal", winner=p, terminal_reason="mahjong",
                win_source=source, win_tile=state.last_draw_tile, win_kind="self",
                win_live_count_before=state.last_draw_live_count_before,
                may_declare_self=False, history=hist
            )

        if tag == "declare_kang":
            _, p, kind, tile = action
            if kind == "concealed":
                hands = set_player_tuple(state.hands, p, remove_tiles(state.hands[p], (tile, tile, tile, tile)))
                melds = append_meld(state.melds, p, Meld("kang", (tile, tile, tile, tile), concealed=True))
                return replace(
                    state, phase="draw_live", current=p, hands=hands, melds=melds,
                    pending_draw_player=p, pending_draw_reason="concealed_kang_replacement",
                    may_declare_self=False, history=hist
                )
            if kind == "extend_pong":
                return replace(
                    state, phase="kang_reaction",
                    pending_kang_player=p, pending_kang_tile=tile, kang_reaction_pos=0,
                    may_declare_self=False, history=hist
                )

        if tag == "pass":
            if state.phase == "reaction":
                if state.reaction_pos < NUM_PLAYERS - 2:
                    return replace(state, reaction_pos=state.reaction_pos + 1, history=hist)

                dead = state.dead_discards + (state.discard_tile,)
                if not state.remaining:
                    return replace(
                        state, phase="terminal", terminal_reason="wall_exhausted",
                        dead_discards=dead, discard_tile=None, discard_from=None,
                        may_declare_self=False, history=hist
                    )
                draw_player = next_player(state.discard_from)
                return replace(
                    state, phase="draw_live", pending_draw_player=draw_player,
                    pending_draw_reason="normal_draw",
                    dead_discards=dead, discard_tile=None, discard_from=None,
                    reaction_pos=0, may_declare_self=False, history=hist
                )

            if state.phase == "kang_reaction":
                if state.kang_reaction_pos < NUM_PLAYERS - 2:
                    return replace(state, kang_reaction_pos=state.kang_reaction_pos + 1, history=hist)

                p = state.pending_kang_player
                tile = state.pending_kang_tile
                hands = set_player_tuple(state.hands, p, remove_tiles(state.hands[p], (tile,)))
                melds = replace_open_pong_with_kang(state.melds, p, tile)
                return replace(
                    state, phase="draw_live", hands=hands, melds=melds,
                    pending_draw_player=p, pending_draw_reason="extended_kang_replacement",
                    pending_kang_player=None, pending_kang_tile=None, kang_reaction_pos=0,
                    may_declare_self=False, history=hist
                )

        if tag in ("claim_pong", "claim_chi", "claim_kang"):
            p = action[1]
            tile = state.discard_tile
            if tag == "claim_pong":
                hands = set_player_tuple(state.hands, p, remove_tiles(state.hands[p], (tile, tile)))
                melds = append_meld(state.melds, p, Meld("pong", (tile, tile, tile), concealed=False))
                return replace(
                    state, phase="discard", current=p, hands=hands, melds=melds,
                    discard_tile=None, discard_from=None, reaction_pos=0,
                    may_declare_self=False, history=hist
                )

            if tag == "claim_chi":
                _, p, suit, start = action
                needed = needed_for_chi(tile, suit, start)
                hands = set_player_tuple(state.hands, p, remove_tiles(state.hands[p], needed))
                melds = append_meld(state.melds, p, Meld("chi", sequence_tiles(suit, start), concealed=False))
                return replace(
                    state, phase="discard", current=p, hands=hands, melds=melds,
                    discard_tile=None, discard_from=None, reaction_pos=0,
                    may_declare_self=False, history=hist
                )

            if tag == "claim_kang":
                hands = set_player_tuple(state.hands, p, remove_tiles(state.hands[p], (tile, tile, tile)))
                melds = append_meld(state.melds, p, Meld("kang", (tile, tile, tile, tile), concealed=False))
                return replace(
                    state, phase="draw_live", current=p, hands=hands, melds=melds,
                    pending_draw_player=p, pending_draw_reason="claim_kang_replacement",
                    discard_tile=None, discard_from=None, reaction_pos=0,
                    may_declare_self=False, history=hist
                )

        if tag == "claim_mahjong":
            return self._apply_discard_mahjong(state, action, "discard", hist)

        if tag == "rob_mahjong":
            return self._apply_rob_kang_mahjong(state, action, hist)

        raise ValueError(f"Unhandled action {action!r}")

    def _apply_discard_mahjong(self, state, action, source, hist):
        _, p, kind, data = action
        tile = state.discard_tile
        hands = state.hands
        melds = state.melds

        if kind == "pair" or kind == "special":
            hands = set_player_tuple(hands, p, add_tiles(hands[p], (tile,)))
        elif kind == "pong":
            hands = set_player_tuple(hands, p, remove_tiles(hands[p], (tile, tile)))
            melds = append_meld(melds, p, Meld("pong", (tile, tile, tile), concealed=False))
        elif kind == "chi":
            suit, start = data
            needed = needed_for_chi(tile, suit, start)
            hands = set_player_tuple(hands, p, remove_tiles(hands[p], needed))
            melds = append_meld(melds, p, Meld("chi", sequence_tiles(suit, start), concealed=False))

        return replace(
            state, phase="terminal", hands=hands, melds=melds,
            winner=p, terminal_reason="mahjong",
            win_source=source, win_tile=tile, win_kind=kind,
            win_discard_from=state.discard_from,
            discard_tile=None, discard_from=None, reaction_pos=0,
            may_declare_self=False, history=hist
        )

    def _apply_rob_kang_mahjong(self, state, action, hist):
        _, p, kind, data = action
        declarer = state.pending_kang_player
        tile = state.pending_kang_tile

        hands = set_player_tuple(state.hands, declarer, remove_tiles(state.hands[declarer], (tile,)))
        melds = state.melds

        if kind == "pair" or kind == "special":
            hands = set_player_tuple(hands, p, add_tiles(hands[p], (tile,)))
        elif kind == "pong":
            hands = set_player_tuple(hands, p, remove_tiles(hands[p], (tile, tile)))
            melds = append_meld(melds, p, Meld("pong", (tile, tile, tile), concealed=False))
        elif kind == "chi":
            suit, start = data
            needed = needed_for_chi(tile, suit, start)
            hands = set_player_tuple(hands, p, remove_tiles(hands[p], needed))
            melds = append_meld(melds, p, Meld("chi", sequence_tiles(suit, start), concealed=False))

        return replace(
            state, phase="terminal", hands=hands, melds=melds,
            winner=p, terminal_reason="mahjong",
            win_source="rob_kang", win_tile=tile, win_kind=kind,
            win_discard_from=declarer,
            pending_kang_player=None, pending_kang_tile=None, kang_reaction_pos=0,
            may_declare_self=False, history=hist
        )

    def is_terminal(self, state: GameState) -> bool:
        return state.phase == "terminal"

    def returns(self, state: GameState):
        if not self.is_terminal(state) or state.winner is None:
            return tuple(0 for _ in range(NUM_PLAYERS))

        values = [self._score_player(state, p) for p in range(NUM_PLAYERS)]
        winner = state.winner
        ret = [0 for _ in range(NUM_PLAYERS)]

        win_value = values[winner]
        for p in range(NUM_PLAYERS):
            if p == winner:
                continue
            amount = win_value
            if state.seat_winds[p] == "Osten" or state.seat_winds[winner] == "Osten":
                amount *= 2
            ret[winner] += amount
            ret[p] -= amount

        losers = [p for p in range(NUM_PLAYERS) if p != winner]
        for i, a in enumerate(losers):
            for b in losers[i + 1:]:
                if values[a] == values[b]:
                    continue
                high, low = (a, b) if values[a] > values[b] else (b, a)
                amount = abs(values[a] - values[b])
                if state.seat_winds[high] == "Osten" or state.seat_winds[low] == "Osten":
                    amount *= 2
                ret[high] += amount
                ret[low] -= amount

        return tuple(int(x) if isinstance(x, float) and x.is_integer() else x for x in ret)

    def _can_self_mahjong(self, state: GameState, player: int) -> bool:
        hand = state.hands[player]
        meld_count = len(state.melds[player])
        return (
            is_standard_complete(hand, meld_count)
            or (meld_count == 0 and is_seven_pairs(hand))
            or (meld_count == 0 and is_thirteen_wonders(hand))
        )

    def _score_player(self, state: GameState, player: int):
        if state.winner == player:
            return self._winner_score(state, player)
        return self._partial_score(state, player)

    def _winner_score(self, state: GameState, player: int):
        hand = state.hands[player]
        exposed = state.melds[player]
        analyses = standard_analyses(hand, exposed)

        if not exposed:
            if is_seven_pairs(hand):
                analyses.append(HandAnalysis((), None, "seven_pairs"))
            if is_thirteen_wonders(hand):
                analyses.append(HandAnalysis((), None, "thirteen_wonders"))

        if not analyses:
            return min(self.limit, self._partial_score(state, player) + 20)

        return max(self._score_winning_analysis(state, player, a) for a in analyses)

    def _score_winning_analysis(self, state: GameState, player: int, analysis: HandAnalysis):
        limit_value = self._limit_value(state, player, analysis)
        if limit_value is not None:
            return limit_value

        if analysis.special:
            return min(self.limit, 20)

        base = 20  # Mah-Jongg-Ruf
        base += sum(meld_points(m) for m in analysis.melds)
        if analysis.pair_tile is not None:
            base += pair_points(analysis.pair_tile, player, state)

        if state.win_source == "self_draw":
            base += 2
        if state.win_kind == "pair":
            base += pair_completion_bonus(state.win_tile)

        doubles = all_hand_doubles(analysis, player, state)
        doubles += mahjong_doubles(analysis, state.hands[player], player, state)
        return min(self.limit, base * (2 ** doubles))

    def _partial_score(self, state: GameState, player: int):
        base = 0
        melds = list(state.melds[player])
        for meld in melds:
            base += meld_points(meld)

        counts = Counter(state.hands[player])
        for tile in sorted(list(counts.keys()), key=tile_key):
            if counts[tile] >= 3:
                # If an undeclared fourth tile remains in hand, the text says it scores only as Pong.
                meld = Meld("pong", (tile, tile, tile), concealed=True)
                melds.append(meld)
                base += meld_points(meld)
                counts[tile] -= 3

        pair_tiles = []
        for tile in sorted(list(counts.keys()), key=tile_key):
            if counts[tile] >= 2:
                pair_tiles.append(tile)
                base += pair_points(tile, player, state)

        doubles = pattern_doubles(tuple(melds), pair_tiles, player, state)
        return min(self.limit, base * (2 ** doubles))

    def _half_limit(self):
        return self.limit // 2 if self.limit % 2 == 0 else self.limit / 2

    def _limit_value(self, state: GameState, player: int, analysis: HandAnalysis):
        # Not tracked/implemented: Kang-on-Kang in one move, dead-wall Kreis-5,
        # ninth East win in a row, flowers/seasons.
        values = []
        hand = state.hands[player]
        tiles = analysis_tiles(analysis, hand)

        if state.win_source == "initial_deal" and state.seat_winds[player] == "Osten":
            values.append(self.limit)
        if (
            state.win_source == "discard"
            and state.discard_count == 1
            and state.win_discard_from is not None
            and state.seat_winds[state.win_discard_from] == "Osten"
            and state.seat_winds[player] != "Osten"
        ):
            values.append(self.limit)

        if analysis.special == "seven_pairs":
            values.append(self._half_limit())
        if analysis.special == "thirteen_wonders":
            values.append(self.limit)

        if tiles and all(is_honor(t) for t in tiles):
            values.append(self.limit)
        if tiles and all(suited_info(t) is not None and suited_info(t)[1] in (1, 9) for t in tiles):
            values.append(self.limit)
        if tiles and all(t in GREEN_TILES for t in tiles):
            values.append(self.limit)

        if not analysis.special:
            suits, honors = suits_and_honor_count(tiles)
            if len(suits) == 1 and honors == 0 and all(m.concealed for m in analysis.melds) and state.win_source in ("self_draw", "initial_deal"):
                values.append(self.limit)
            if is_winding_snake(analysis):
                values.append(self.limit)
            if sum(1 for m in analysis.melds if m.kind == "kang") == 4:
                values.append(self.limit)

            dragon_sets = sum(1 for m in analysis.melds if m.kind in ("pong", "kang") and is_dragon(m.tiles[0]))
            pong_kang_sets = sum(1 for m in analysis.melds if m.kind in ("pong", "kang"))
            if dragon_sets == 3 and pong_kang_sets >= 4:
                values.append(self.limit)

            wind_sets = sum(1 for m in analysis.melds if m.kind in ("pong", "kang") and is_wind(m.tiles[0]))
            if wind_sets == 4:
                values.append(self.limit)

            if not state.melds[player] and is_nine_lanterns(hand):
                values.append(self.limit)

            if (
                state.win_source == "self_draw"
                and len(analysis.melds) == 4
                and all(m.kind in ("pong", "kang") and m.concealed for m in analysis.melds)
            ):
                values.append(self.limit)

        if state.win_source == "self_draw" and state.win_live_count_before == 1 and state.win_tile == "Kreis-1":
            values.append(self.limit)
        if state.win_source == "rob_kang" and state.win_tile == "Bambus-2":
            values.append(self.limit)

        return max(values) if values else None

    def render(self, state: GameState) -> str:
        cp = self.current_player(state)
        cp_s = "TERMINAL" if cp == TERMINAL else "CHANCE" if cp == CHANCE else player_token(cp)
        lines = [
            f"phase={state.phase}; current={cp_s}; wall={len(state.remaining)}; "
            f"discard={state.discard_tile or '-'}; winner={state.winner if state.winner is not None else '-'}; "
            f"reason={state.terminal_reason or '-'}",
            f"round_wind={state.round_wind}; dead_discards={format_tiles(state.dead_discards)}",
        ]
        if state.phase == "kang_reaction":
            lines.append(f"pending_kang={player_token(state.pending_kang_player)}:{state.pending_kang_tile}")
        for p in range(NUM_PLAYERS):
            lines.append(
                f"{player_token(p)}({state.seat_winds[p]}): "
                f"hand={format_tiles(state.hands[p])}; melds={format_melds(state.melds[p])}"
            )
        if self.is_terminal(state):
            lines.append("returns=" + ",".join(str(x) for x in self.returns(state)))
        return "\n".join(lines)

    def information_state(self, state: GameState, player: int) -> str:
        if not 0 <= player < NUM_PLAYERS:
            raise ValueError("player out of range")
        cp = self.current_player(state)
        cp_s = "TERMINAL" if cp == TERMINAL else "CHANCE" if cp == CHANCE else player_token(cp)
        lines = [
            f"player={player_token(player)}({state.seat_winds[player]}); phase={state.phase}; current={cp_s}; wall_count={len(state.remaining)}",
            f"discard={state.discard_tile or '-'}; dead_discards={format_tiles(state.dead_discards)}",
        ]
        if state.phase == "kang_reaction":
            lines.append(f"pending_kang_tile={state.pending_kang_tile}")
        for p in range(NUM_PLAYERS):
            if p == player:
                hand_s = format_tiles(state.hands[p])
            else:
                hand_s = f"hidden_count={len(state.hands[p])}"
            lines.append(f"{player_token(p)}({state.seat_winds[p]}): hand={hand_s}; melds={format_melds(state.melds[p])}")
        return "\n".join(lines)

    def action_to_name(self, action) -> str:
        tag = action[0]

        if tag == "chance_deal":
            _, p, tile = action
            return f"chance:deal:{player_token(p)}:{tile}"
        if tag == "chance_draw":
            _, p, reason, tile = action
            return f"chance:draw:{player_token(p)}:{reason}:{tile}"
        if tag == "discard":
            _, p, tile = action
            return f"discard:{player_token(p)}:{tile}"
        if tag == "declare_mahjong":
            _, p = action
            return f"mahjong:{player_token(p)}:self"
        if tag == "declare_kang":
            _, p, kind, tile = action
            return f"kang:{player_token(p)}:{kind}:{tile}"
        if tag == "pass":
            _, p = action
            return f"pass:{player_token(p)}"
        if tag == "claim_pong":
            _, p, tile = action
            return f"claim:{player_token(p)}:pong:{tile}"
        if tag == "claim_kang":
            _, p, tile = action
            return f"claim:{player_token(p)}:kang:{tile}"
        if tag == "claim_chi":
            _, p, suit, start = action
            return f"claim:{player_token(p)}:chi:{chi_name(suit, start)}"
        if tag in ("claim_mahjong", "rob_mahjong"):
            _, p, kind, data = action
            data_s = chi_name(*data) if kind == "chi" else data
            prefix = "claim" if tag == "claim_mahjong" else "rob_kang"
            return f"{prefix}:{player_token(p)}:mahjong:{kind}:{data_s}"

        raise ValueError(f"Unknown action tag: {tag}")

    def name_to_action(self, name: str):
        parts = name.split(":")
        if not parts:
            raise ValueError("empty action name")

        if parts[0] == "chance":
            if len(parts) == 4 and parts[1] == "deal":
                return ("chance_deal", parse_player_token(parts[2]), parts[3])
            if len(parts) == 5 and parts[1] == "draw":
                return ("chance_draw", parse_player_token(parts[2]), parts[3], parts[4])

        if parts[0] == "discard" and len(parts) == 3:
            return ("discard", parse_player_token(parts[1]), parts[2])

        if parts[0] == "mahjong" and len(parts) == 3 and parts[2] == "self":
            return ("declare_mahjong", parse_player_token(parts[1]))

        if parts[0] == "kang" and len(parts) == 4:
            return ("declare_kang", parse_player_token(parts[1]), parts[2], parts[3])

        if parts[0] == "pass" and len(parts) == 2:
            return ("pass", parse_player_token(parts[1]))

        if parts[0] == "claim" and len(parts) >= 4:
            p = parse_player_token(parts[1])
            if parts[2] == "mahjong" and len(parts) == 5:
                kind = parts[3]
                data = parse_chi_name(parts[4]) if kind == "chi" else parts[4]
                return ("claim_mahjong", p, kind, data)
            if parts[2] == "pong" and len(parts) == 4:
                return ("claim_pong", p, parts[3])
            if parts[2] == "kang" and len(parts) == 4:
                return ("claim_kang", p, parts[3])
            if parts[2] == "chi" and len(parts) == 4:
                suit, start = parse_chi_name(parts[3])
                return ("claim_chi", p, suit, start)

        if parts[0] == "rob_kang" and len(parts) == 5 and parts[2] == "mahjong":
            p = parse_player_token(parts[1])
            kind = parts[3]
            data = parse_chi_name(parts[4]) if kind == "chi" else parts[4]
            return ("rob_mahjong", p, kind, data)

        raise ValueError(f"Cannot parse action name: {name}")
```
