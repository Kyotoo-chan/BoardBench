"""A small, self-contained CATAN model based only on the supplied rules text.

The printed beginner setup picture and the Almanach data are not available in the
text input.  Therefore this module uses a deterministic *abstract* 19-hex board
with stable IDs (t00, x00, e00, ...).  It preserves the rulebook examples that
are stated in text: the B settlement starts with Holz+Erz+Lehm, the C settlement
starts with Erz+2 Getreide, roll 3 gives Holz at D and Erz at B/C, roll 8 gives
2 Erz to red and 1 Erz to white, and roll 10 gives Wolle to white.

Player-to-player negotiation is not enumerated as actions because the rulebook
allows free-form offers/counteroffers without a finite protocol.  Maritime bank
trading is implemented.  Fortschritt development-card text, full development-deck
composition, exact harbor layout, bank depletion, and the exact page-1 board
layout are not specified by the supplied text; see comments below.
"""

from dataclasses import dataclass, field
import copy
from typing import Dict, List, Optional, Sequence, Tuple

TERMINAL = -1
CHANCE = -2
SIMULTANEOUS = -3

RESOURCES: Tuple[str, ...] = ("Holz", "Lehm", "Wolle", "Getreide", "Erz")
LANDSCAPE_TO_RESOURCE: Dict[str, Optional[str]] = {
    "Wald": "Holz",
    "Hügelland": "Lehm",
    "Weideland": "Wolle",
    "Ackerland": "Getreide",
    "Gebirge": "Erz",
    "Wüste": None,
}
DEV_TYPES: Tuple[str, ...] = ("Ritter", "Fortschritt", "Siegpunkte")

ROAD_COST = {"Lehm": 1, "Holz": 1}
SETTLEMENT_COST = {"Lehm": 1, "Holz": 1, "Wolle": 1, "Getreide": 1}
CITY_COST = {"Erz": 3, "Getreide": 2}
DEV_COST = {"Erz": 1, "Wolle": 1, "Getreide": 1}

DICE_WEIGHTS: Dict[int, int] = {2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6,
                                8: 5, 9: 4, 10: 3, 11: 2, 12: 1}

# Terminal is delayed while a mandatory chance/discard/robber sub-procedure is
# being resolved, so e.g. a played Ritter still moves the robber before the turn
# is closed as a win.
PENDING_PHASES = {
    "CHANCE_DICE", "CHANCE_DEV", "DISCARD",
    "ROBBER_MOVE", "ROBBER_STEAL", "CHANCE_STEAL",
}


def _zero_resources() -> Dict[str, int]:
    return {r: 0 for r in RESOURCES}


def _normal_counts(counts: Dict[str, int]) -> Dict[str, int]:
    out = _zero_resources()
    for r, n in counts.items():
        if r not in out:
            raise ValueError(f"Unknown resource {r!r}")
        if int(n) < 0:
            raise ValueError("Resource counts may not be negative")
        out[r] = int(n)
    return out


def _total_resources(hand: Dict[str, int]) -> int:
    return sum(hand.get(r, 0) for r in RESOURCES)


def _has_resources(hand: Dict[str, int], cost: Dict[str, int]) -> bool:
    return all(hand.get(r, 0) >= n for r, n in cost.items())


def _add_resources(hand: Dict[str, int], delta: Dict[str, int]) -> None:
    for r, n in delta.items():
        hand[r] = hand.get(r, 0) + n


def _sub_resources(hand: Dict[str, int], delta: Dict[str, int]) -> None:
    if not _has_resources(hand, delta):
        raise ValueError("Insufficient resources")
    for r, n in delta.items():
        hand[r] = hand.get(r, 0) - n


def _counts_name(counts: Dict[str, int]) -> str:
    parts = [f"{counts.get(r, 0)}{r}" for r in RESOURCES if counts.get(r, 0)]
    return "+".join(parts) if parts else "none"


def _parse_counts(text: str) -> Dict[str, int]:
    out = _zero_resources()
    if text == "none":
        return out
    if not text:
        raise ValueError("Empty resource multiset")
    for part in text.split("+"):
        i = 0
        while i < len(part) and part[i].isdigit():
            i += 1
        if i == 0 or i == len(part):
            raise ValueError(f"Bad resource multiset part {part!r}")
        n = int(part[:i])
        res = part[i:]
        if n <= 0 or res not in RESOURCES:
            raise ValueError(f"Bad resource multiset part {part!r}")
        out[res] += n
    return out


@dataclass(frozen=True)
class Tile:
    id: str
    coord: Tuple[int, int]
    landscape: str
    number: Optional[int]
    corners: Tuple[str, ...]
    edges: Tuple[str, ...]


@dataclass
class GameState:
    num_players: int
    phase: str
    current_player_index: int
    crossing_occupants: Dict[str, Optional[Tuple[int, str]]]
    edge_occupants: Dict[str, Optional[int]]
    robber_tile: str
    hands: List[Dict[str, int]]
    dev_hands: List[List[Tuple[str, bool]]]  # (card type, bought_this_turn)
    dev_deck: Dict[str, int]
    settlements_remaining: List[int]
    cities_remaining: List[int]
    roads_remaining: List[int]
    knights_played: List[int]
    longest_road_owner: Optional[int] = None
    longest_road_length: int = 0
    largest_army_owner: Optional[int] = None
    last_roll: Optional[int] = None
    dev_played_this_turn: bool = False
    discard_queue: List[int] = field(default_factory=list)
    phase_after_robber: str = "TRADE"
    pending_steal_victim: Optional[int] = None
    terminal_winner: Optional[int] = None
    turn_number: int = 1
    history: List[str] = field(default_factory=list)

    def clone(self) -> "GameState":
        return copy.deepcopy(self)


class Game:
    """Rulebook-shaped CATAN API.

    Actions are canonical strings.  ``apply_action`` returns a fresh state and
    never samples internally; dice, development draws, and robber steals are
    explicit chance actions when ``current_player`` returns ``CHANCE``.
    """

    def __init__(self, num_players: int = 4,
                 dev_deck_counts: Optional[Dict[str, int]] = None,
                 oldest_player: int = 0):
        if num_players not in (3, 4):
            raise ValueError("The supplied text supports the beginner setup for 3 or 4 players")
        self.num_players = num_players
        if not (0 <= oldest_player < num_players):
            raise ValueError("oldest_player out of range")
        self.oldest_player = oldest_player
        # The page text identifies B=blue, C=orange, D=white; with 3 players all
        # red pieces are removed.  A is therefore the remaining red setup point.
        self.colors: Tuple[str, ...] = (("Rot", "Blau", "Orange", "Weiss")
                                        if num_players == 4
                                        else ("Blau", "Orange", "Weiss"))
        self.tiles: Dict[str, Tile] = {}
        self.tile_ids: Tuple[str, ...] = ()
        self.crossing_ids: Tuple[str, ...] = ()
        self.edge_ids: Tuple[str, ...] = ()
        self.edge_to_crossings: Dict[str, Tuple[str, str]] = {}
        self.crossing_neighbors: Dict[str, Tuple[str, ...]] = {}
        self.crossing_edges: Dict[str, Tuple[str, ...]] = {}
        self.crossing_tiles: Dict[str, Tuple[str, ...]] = {}
        self.harbors: Dict[str, str] = {}
        self._build_abstract_board()
        if dev_deck_counts is None:
            # Exact composition is absent from the supplied text.  This small
            # default keeps all three stated card types possible and explicit.
            dev_deck_counts = {"Ritter": 6, "Fortschritt": 3, "Siegpunkte": 3}
        self.dev_deck_counts = _normal_dev_counts(dev_deck_counts)

    # ------------------------------------------------------------------
    # Board and setup
    # ------------------------------------------------------------------
    def _build_abstract_board(self) -> None:
        coords: List[Tuple[int, int]] = []
        for q in range(-2, 3):
            for r in range(-2, 3):
                if max(abs(q), abs(r), abs(q + r)) <= 2:
                    coords.append((q, r))
        coords.sort(key=lambda qr: (qr[1], qr[0]))

        # Exact integer corner coordinates for a 19-hex radius-2 island.
        offsets = [(1, 1), (0, 2), (-1, 1), (-1, -1), (0, -2), (1, -1)]
        raw_corners: List[List[Tuple[int, int]]] = []
        all_corners = set()
        for q, r in coords:
            cx, cy = 2 * q + r, 3 * r
            corners = [(cx + dx, cy + dy) for dx, dy in offsets]
            raw_corners.append(corners)
            all_corners.update(corners)

        sorted_corners = sorted(all_corners)
        coord_to_crossing = {xy: f"x{i:02d}" for i, xy in enumerate(sorted_corners)}
        self.crossing_ids = tuple(coord_to_crossing[xy] for xy in sorted_corners)

        tile_corner_ids: List[List[str]] = [
            [coord_to_crossing[xy] for xy in corners] for corners in raw_corners
        ]
        edge_pairs = set()
        for corners in tile_corner_ids:
            for a, b in zip(corners, corners[1:] + corners[:1]):
                edge_pairs.add(tuple(sorted((a, b))))
        sorted_edges = sorted(edge_pairs, key=lambda ab: (int(ab[0][1:]), int(ab[1][1:])))
        pair_to_edge = {pair: f"e{i:02d}" for i, pair in enumerate(sorted_edges)}
        self.edge_ids = tuple(pair_to_edge[pair] for pair in sorted_edges)
        self.edge_to_crossings = {pair_to_edge[pair]: pair for pair in sorted_edges}

        # Deterministic placeholder layout.  It is not claimed to be the printed
        # page-1 setup; it only uses data explicitly present in text examples.
        specs: Sequence[Tuple[str, Optional[int]]] = (
            ("Wald", 3),          # t00: D receives Holz on roll 3
            ("Ackerland", 4),
            ("Weideland", 11),
            ("Wald", 5),          # B's starting Holz, not a 3-chip forest
            ("Gebirge", 3),       # B/C receive Erz on roll 3
            ("Ackerland", 6),
            ("Hügelland", 9),
            ("Weideland", 2),
            ("Hügelland", 6),     # B's starting Lehm
            ("Wüste", None),
            ("Gebirge", 8),       # red x2 and white x1 Erz on roll 8
            ("Ackerland", 11),
            ("Wald", 4),
            ("Weideland", 9),
            ("Ackerland", 5),
            ("Weideland", 10),    # white receives Wolle on roll 10
            ("Hügelland", 12),
            ("Wald", 6),
            ("Gebirge", 8),
        )
        if len(specs) != 19:
            raise AssertionError("internal board spec error")

        crossing_to_tiles: Dict[str, List[str]] = {x: [] for x in self.crossing_ids}
        crossing_to_edges: Dict[str, List[str]] = {x: [] for x in self.crossing_ids}
        crossing_neighbors: Dict[str, set] = {x: set() for x in self.crossing_ids}
        tiles: Dict[str, Tile] = {}
        for i, ((landscape, number), corners) in enumerate(zip(specs, tile_corner_ids)):
            tile_id = f"t{i:02d}"
            edge_list: List[str] = []
            for a, b in zip(corners, corners[1:] + corners[:1]):
                pair = tuple(sorted((a, b)))
                edge_id = pair_to_edge[pair]
                edge_list.append(edge_id)
                crossing_neighbors[a].add(b)
                crossing_neighbors[b].add(a)
                if edge_id not in crossing_to_edges[a]:
                    crossing_to_edges[a].append(edge_id)
                if edge_id not in crossing_to_edges[b]:
                    crossing_to_edges[b].append(edge_id)
            for x in corners:
                crossing_to_tiles[x].append(tile_id)
            tiles[tile_id] = Tile(tile_id, coords[i], landscape, number,
                                  tuple(corners), tuple(edge_list))
        self.tiles = tiles
        self.tile_ids = tuple(f"t{i:02d}" for i in range(19))
        self.crossing_neighbors = {x: tuple(sorted(v, key=_id_num))
                                   for x, v in crossing_neighbors.items()}
        self.crossing_edges = {x: tuple(sorted(es, key=_id_num))
                               for x, es in crossing_to_edges.items()}
        self.crossing_tiles = {x: tuple(ts) for x, ts in crossing_to_tiles.items()}

        # Harbor positions are in the missing figure; these abstract boundary
        # harbors exercise the 4:1/3:1/2:1 rules without asserting real layout.
        self.harbors = {
            "x00": "3:1",
            "x05": "3:1",
            "x18": "2:1:Holz",
            "x23": "2:1:Lehm",
            "x36": "2:1:Wolle",
            "x47": "2:1:Erz",
            "x53": "2:1:Getreide",
        }

    def initial_state(self) -> GameState:
        crossing_occupants: Dict[str, Optional[Tuple[int, str]]] = {
            x: None for x in self.crossing_ids
        }
        edge_occupants: Dict[str, Optional[int]] = {e: None for e in self.edge_ids}
        hands = [_zero_resources() for _ in range(self.num_players)]
        dev_hands: List[List[Tuple[str, bool]]] = [[] for _ in range(self.num_players)]
        settlements = [5 for _ in range(self.num_players)]
        cities = [4 for _ in range(self.num_players)]
        roads = [15 for _ in range(self.num_players)]

        for p, color in enumerate(self.colors):
            setup = self._start_setup_for_color(color)
            for x in setup["settlements"]:
                crossing_occupants[x] = (p, "Siedlung")
                settlements[p] -= 1
            for e in setup["roads"]:
                edge_occupants[e] = p
                roads[p] -= 1
            # Starting resources are awarded only for the lettered settlement.
            marked = setup["marked"]
            for tile_id in self.crossing_tiles[marked]:
                res = LANDSCAPE_TO_RESOURCE[self.tiles[tile_id].landscape]
                if res is not None:
                    hands[p][res] += 1

        state = GameState(
            num_players=self.num_players,
            phase="PRE_ROLL",
            current_player_index=self.oldest_player,
            crossing_occupants=crossing_occupants,
            edge_occupants=edge_occupants,
            robber_tile="t09",
            hands=hands,
            dev_hands=dev_hands,
            dev_deck=dict(self.dev_deck_counts),
            settlements_remaining=settlements,
            cities_remaining=cities,
            roads_remaining=roads,
            knights_played=[0 for _ in range(self.num_players)],
        )
        self._update_longest_road(state)
        return state

    def _start_setup_for_color(self, color: str) -> Dict[str, object]:
        # Stable abstract beginner setup.  B/C/D resources and the roll examples
        # match the text as described in the module docstring.
        data = {
            "Rot": {"settlements": ("x32", "x44"), "roads": ("e38", "e63"), "marked": "x32"},
            "Blau": {"settlements": ("x14", "x00"), "roads": ("e13", "e00"), "marked": "x14"},
            "Orange": {"settlements": ("x25", "x53"), "roads": ("e37", "e71"), "marked": "x25"},
            "Weiss": {"settlements": ("x18", "x39"), "roads": ("e18", "e56"), "marked": "x18"},
        }
        return data[color]

    # ------------------------------------------------------------------
    # Required API
    # ------------------------------------------------------------------
    def current_player(self, state: GameState) -> int:
        if self.is_terminal(state):
            return TERMINAL
        if state.phase.startswith("CHANCE"):
            return CHANCE
        if state.phase == "DISCARD" and state.discard_queue:
            return state.discard_queue[0]
        return state.current_player_index

    def legal_actions(self, state: GameState) -> List[str]:
        if self.is_terminal(state):
            return []
        phase = state.phase
        p = state.current_player_index
        if phase == "PRE_ROLL":
            return self._legal_dev_plays(state, p) + ["roll"]
        if phase.startswith("CHANCE"):
            return [a for a, _prob in self.chance_outcomes(state)]
        if phase == "DISCARD":
            if not state.discard_queue:
                return []
            dp = state.discard_queue[0]
            needed = _total_resources(state.hands[dp]) // 2
            return ["discard:" + _counts_name(c) for c in self._discard_combinations(state.hands[dp], needed)]
        if phase == "ROBBER_MOVE":
            return [f"robber:move:{t}" for t in self.tile_ids if t != state.robber_tile]
        if phase == "ROBBER_STEAL":
            return [f"robber:steal:p{v}" for v in self._robber_victims(state)]
        if phase == "TRADE":
            return self._legal_dev_plays(state, p) + self._legal_maritime_trades(state, p) + ["pass"]
        if phase == "BUILD":
            return self._legal_dev_plays(state, p) + self._legal_build_actions(state, p) + ["end_turn"]
        if phase == "TERMINAL":
            return []
        raise ValueError(f"Unknown phase {phase!r}")

    def apply_action(self, state: GameState, action: str) -> GameState:
        action = self.name_to_action(action)
        legal = self.legal_actions(state)
        if action not in legal:
            raise ValueError(f"Illegal action {action!r} in phase {state.phase!r}")

        ns = state.clone()
        ns.history.append(action)
        phase = state.phase
        active = ns.current_player_index

        if action == "roll":
            ns.phase = "CHANCE_DICE"
            return ns

        if action == "play:knight":
            self._remove_dev_card(ns, active, "Ritter")
            ns.dev_played_this_turn = True
            ns.knights_played[active] += 1
            self._update_largest_army(ns, active)
            ns.phase_after_robber = phase
            ns.phase = "ROBBER_MOVE"
            return ns

        if action == "play:progress":
            # The text sends the reader to the card text/Almanach, unavailable
            # here.  Playing a Fortschritt card is represented as a legal no-op
            # that removes the card from the game and consumes the one dev-card
            # play allowed this turn.
            self._remove_dev_card(ns, active, "Fortschritt")
            ns.dev_played_this_turn = True
            self._maybe_set_terminal(ns)
            return ns

        if phase == "CHANCE_DICE":
            roll = int(action.split(":")[-1])
            ns.last_roll = roll
            if roll == 7:
                ns.discard_queue = [i for i in range(ns.num_players)
                                    if _total_resources(ns.hands[i]) > 7]
                ns.phase_after_robber = "TRADE"
                ns.phase = "DISCARD" if ns.discard_queue else "ROBBER_MOVE"
            else:
                self._distribute_yield(ns, roll)
                ns.phase = "TRADE"
            self._maybe_set_terminal(ns)
            return ns

        if phase == "DISCARD":
            discarder = ns.discard_queue.pop(0)
            counts = _parse_counts(action.split(":", 1)[1])
            _sub_resources(ns.hands[discarder], counts)
            ns.phase = "DISCARD" if ns.discard_queue else "ROBBER_MOVE"
            ns.phase_after_robber = "TRADE"
            return ns

        if phase == "ROBBER_MOVE":
            target = action.split(":")[-1]
            ns.robber_tile = target
            victims = self._robber_victims(ns)
            if victims:
                ns.phase = "ROBBER_STEAL"
            else:
                ns.phase = ns.phase_after_robber
                self._maybe_set_terminal(ns)
            return ns

        if phase == "ROBBER_STEAL":
            victim = int(action.rsplit("p", 1)[1])
            ns.pending_steal_victim = victim
            ns.phase = "CHANCE_STEAL"
            return ns

        if phase == "CHANCE_STEAL":
            res = action.split(":")[-1]
            victim = ns.pending_steal_victim
            if victim is None:
                raise ValueError("No pending steal victim")
            _sub_resources(ns.hands[victim], {res: 1})
            _add_resources(ns.hands[active], {res: 1})
            ns.pending_steal_victim = None
            ns.phase = ns.phase_after_robber
            self._maybe_set_terminal(ns)
            return ns

        if phase == "CHANCE_DEV":
            card = action.split(":")[-1]
            ns.dev_deck[card] -= 1
            ns.dev_hands[active].append((card, True))
            ns.phase = "BUILD"
            self._maybe_set_terminal(ns)
            return ns

        if phase == "TRADE":
            if action == "pass":
                ns.phase = "BUILD"
            elif action.startswith("trade:maritime:"):
                ratio_s, rest = action.split(":", 3)[2:]
                ratio = int(ratio_s)
                give, get = rest.split("->")
                _sub_resources(ns.hands[active], {give: ratio})
                _add_resources(ns.hands[active], {get: 1})
            else:
                raise ValueError(f"Unhandled trade action {action!r}")
            self._maybe_set_terminal(ns)
            return ns

        if phase == "BUILD":
            if action == "end_turn":
                # A just-bought development card becomes playable only on a
                # later turn.
                ns.dev_hands[active] = [(card, False) for card, _fresh in ns.dev_hands[active]]
                ns.dev_played_this_turn = False
                ns.current_player_index = (active + 1) % ns.num_players
                ns.phase = "PRE_ROLL"
                ns.phase_after_robber = "TRADE"
                ns.pending_steal_victim = None
                ns.turn_number += 1
                self._maybe_set_terminal(ns)
                return ns
            if action == "build:dev":
                _sub_resources(ns.hands[active], DEV_COST)
                ns.phase = "CHANCE_DEV"
                return ns
            if action.startswith("build:road:"):
                edge = action.split(":")[-1]
                _sub_resources(ns.hands[active], ROAD_COST)
                ns.edge_occupants[edge] = active
                ns.roads_remaining[active] -= 1
                self._update_longest_road(ns)
                self._maybe_set_terminal(ns)
                return ns
            if action.startswith("build:settlement:"):
                crossing = action.split(":")[-1]
                _sub_resources(ns.hands[active], SETTLEMENT_COST)
                ns.crossing_occupants[crossing] = (active, "Siedlung")
                ns.settlements_remaining[active] -= 1
                self._update_longest_road(ns)  # a new settlement can split roads
                self._maybe_set_terminal(ns)
                return ns
            if action.startswith("build:city:"):
                crossing = action.split(":")[-1]
                _sub_resources(ns.hands[active], CITY_COST)
                ns.crossing_occupants[crossing] = (active, "Stadt")
                ns.cities_remaining[active] -= 1
                ns.settlements_remaining[active] += 1
                self._maybe_set_terminal(ns)
                return ns

        raise ValueError(f"Unhandled action {action!r} in phase {phase!r}")

    def is_terminal(self, state: GameState) -> bool:
        return self._winner(state) is not None

    def returns(self, state: GameState) -> List[float]:
        winner = self._winner(state)
        if winner is None:
            return [0.0 for _ in range(state.num_players)]
        if state.num_players == 1:
            return [1.0]
        loser_value = -1.0 / (state.num_players - 1)
        return [1.0 if p == winner else loser_value for p in range(state.num_players)]

    def render(self, state: GameState) -> str:
        """Deterministic debug render.  It includes private hands/dev cards."""
        parts: List[str] = []
        cur = self.current_player(state)
        cur_s = "CHANCE" if cur == CHANCE else ("TERMINAL" if cur == TERMINAL else f"p{cur}")
        parts.append(f"phase={state.phase} current={cur_s} turn={state.turn_number} last_roll={state.last_roll}")
        parts.append(f"robber={state.robber_tile}")
        tile_bits = []
        for tid in self.tile_ids:
            t = self.tiles[tid]
            n = "-" if t.number is None else str(t.number)
            rb = "R" if state.robber_tile == tid else ""
            tile_bits.append(f"{tid}:{t.landscape}:{n}{rb}")
        parts.append("tiles=" + ",".join(tile_bits))
        buildings = []
        for x in self.crossing_ids:
            occ = state.crossing_occupants[x]
            if occ is not None:
                p, kind = occ
                buildings.append(f"{x}:p{p}:{kind}")
        parts.append("buildings=" + (",".join(buildings) if buildings else "none"))
        roads = []
        for e in self.edge_ids:
            p = state.edge_occupants[e]
            if p is not None:
                roads.append(f"{e}:p{p}")
        parts.append("roads=" + (",".join(roads) if roads else "none"))
        harbor_bits = [f"{x}={self.harbors[x]}" for x in sorted(self.harbors, key=_id_num)]
        parts.append("harbors=" + ",".join(harbor_bits))
        player_bits = []
        for p in range(state.num_players):
            dev_counts = self._dev_counts_for_render(state.dev_hands[p])
            player_bits.append(
                f"p{p}:{self.colors[p]} hand={_counts_name(state.hands[p])} "
                f"dev={dev_counts} vp_public={self.public_vp(state, p)} "
                f"vp_total={self.total_vp(state, p)} knights={state.knights_played[p]} "
                f"supply(S/C/R)={state.settlements_remaining[p]}/"
                f"{state.cities_remaining[p]}/{state.roads_remaining[p]}"
            )
        parts.append("players=" + " | ".join(player_bits))
        parts.append(f"longest_road={_owner_name(state.longest_road_owner)}:{state.longest_road_length}")
        parts.append(f"largest_army={_owner_name(state.largest_army_owner)}")
        parts.append(f"dev_deck_size={sum(state.dev_deck.values())}")
        if state.terminal_winner is not None:
            parts.append(f"winner=p{state.terminal_winner}")
        return "\n".join(parts)

    def action_to_name(self, action: str) -> str:
        return self.name_to_action(action)

    def name_to_action(self, name: str) -> str:
        if not isinstance(name, str):
            raise ValueError("Actions are canonical strings")
        if name in {"roll", "pass", "end_turn", "play:knight", "play:progress", "build:dev"}:
            return name
        if name.startswith("chance:dice:"):
            value = int(name.split(":")[-1])
            if value not in DICE_WEIGHTS:
                raise ValueError("Bad dice chance action")
            return name
        if name.startswith("chance:dev:"):
            card = name.split(":")[-1]
            if card not in DEV_TYPES:
                raise ValueError("Bad development chance action")
            return name
        if name.startswith("chance:steal:"):
            res = name.split(":")[-1]
            if res not in RESOURCES:
                raise ValueError("Bad steal chance action")
            return name
        if name.startswith("discard:"):
            _parse_counts(name.split(":", 1)[1])
            return name
        if name.startswith("robber:move:"):
            tile = name.split(":")[-1]
            if tile not in self.tiles:
                raise ValueError("Bad robber tile")
            return name
        if name.startswith("robber:steal:p"):
            p = int(name.rsplit("p", 1)[1])
            if not (0 <= p < self.num_players):
                raise ValueError("Bad robber victim")
            return name
        if name.startswith("build:road:"):
            edge = name.split(":")[-1]
            if edge not in self.edge_to_crossings:
                raise ValueError("Bad road edge")
            return name
        if name.startswith("build:settlement:") or name.startswith("build:city:"):
            crossing = name.split(":")[-1]
            if crossing not in self.crossing_ids:
                raise ValueError("Bad crossing")
            return name
        if name.startswith("trade:maritime:"):
            try:
                ratio_s, rest = name.split(":", 3)[2:]
                ratio = int(ratio_s)
                give, get = rest.split("->")
            except Exception as exc:  # pragma: no cover - defensive parse path
                raise ValueError("Bad maritime trade action") from exc
            if ratio not in (2, 3, 4) or give not in RESOURCES or get not in RESOURCES or give == get:
                raise ValueError("Bad maritime trade action")
            return name
        raise ValueError(f"Unknown action name {name!r}")

    # ------------------------------------------------------------------
    # Optional stochastic / information APIs
    # ------------------------------------------------------------------
    def chance_outcomes(self, state: GameState) -> List[Tuple[str, float]]:
        if self.is_terminal(state):
            return []
        if state.phase == "CHANCE_DICE":
            return [(f"chance:dice:{s}", w / 36.0) for s, w in sorted(DICE_WEIGHTS.items())]
        if state.phase == "CHANCE_DEV":
            total = sum(state.dev_deck.values())
            if total <= 0:
                return []
            return [(f"chance:dev:{card}", state.dev_deck.get(card, 0) / total)
                    for card in DEV_TYPES if state.dev_deck.get(card, 0) > 0]
        if state.phase == "CHANCE_STEAL":
            victim = state.pending_steal_victim
            if victim is None:
                return []
            total = _total_resources(state.hands[victim])
            if total <= 0:
                return []
            return [(f"chance:steal:{r}", state.hands[victim].get(r, 0) / total)
                    for r in RESOURCES if state.hands[victim].get(r, 0) > 0]
        return []

    def information_state(self, state: GameState, player: int) -> str:
        if not (0 <= player < state.num_players):
            raise ValueError("player out of range")
        lines: List[str] = []
        cur = self.current_player(state)
        cur_s = "CHANCE" if cur == CHANCE else ("TERMINAL" if cur == TERMINAL else f"p{cur}")
        lines.append(f"phase={state.phase} current={cur_s} you=p{player} last_roll={state.last_roll} robber={state.robber_tile}")
        public_tiles = []
        for tid in self.tile_ids:
            t = self.tiles[tid]
            n = "-" if t.number is None else str(t.number)
            rb = "R" if tid == state.robber_tile else ""
            public_tiles.append(f"{tid}:{t.landscape}:{n}{rb}")
        lines.append("tiles=" + ",".join(public_tiles))
        buildings = []
        for x in self.crossing_ids:
            occ = state.crossing_occupants[x]
            if occ is not None:
                p, kind = occ
                buildings.append(f"{x}:p{p}:{kind}")
        lines.append("buildings=" + (",".join(buildings) if buildings else "none"))
        roads = [f"{e}:p{p}" for e, p in sorted(state.edge_occupants.items(), key=lambda kv: _id_num(kv[0])) if p is not None]
        lines.append("roads=" + (",".join(roads) if roads else "none"))
        per_player = []
        for p in range(state.num_players):
            if p == player:
                private = f"hand={_counts_name(state.hands[p])} dev={self._dev_counts_for_render(state.dev_hands[p])}"
            else:
                private = f"hand_total={_total_resources(state.hands[p])} dev_count={len(state.dev_hands[p])}"
            per_player.append(
                f"p{p}:{self.colors[p]} {private} vp_public={self.public_vp(state, p)} "
                f"knights={state.knights_played[p]} supply={state.settlements_remaining[p]}/"
                f"{state.cities_remaining[p]}/{state.roads_remaining[p]}"
            )
        lines.append("players=" + " | ".join(per_player))
        lines.append(f"longest_road={_owner_name(state.longest_road_owner)}:{state.longest_road_length} largest_army={_owner_name(state.largest_army_owner)}")
        lines.append(f"dev_deck_size={sum(state.dev_deck.values())}")
        return "\n".join(lines)

    observation = information_state

    # ------------------------------------------------------------------
    # Rule helpers
    # ------------------------------------------------------------------
    def public_vp(self, state: GameState, player: int) -> int:
        vp = 0
        for occ in state.crossing_occupants.values():
            if occ is None:
                continue
            p, kind = occ
            if p == player:
                vp += 1 if kind == "Siedlung" else 2
        if state.longest_road_owner == player:
            vp += 2
        if state.largest_army_owner == player:
            vp += 2
        return vp

    def total_vp(self, state: GameState, player: int) -> int:
        # Assumption: each hidden Siegpunkte development card is worth 1 point;
        # the supplied page names the type but not the per-card value.
        hidden = sum(1 for card, _fresh in state.dev_hands[player] if card == "Siegpunkte")
        return self.public_vp(state, player) + hidden

    def _winner(self, state: GameState) -> Optional[int]:
        if state.terminal_winner is not None:
            return state.terminal_winner
        if state.phase == "TERMINAL":
            return state.terminal_winner
        if state.phase not in PENDING_PHASES:
            p = state.current_player_index
            if 0 <= p < state.num_players and self.total_vp(state, p) >= 10:
                return p
        return None

    def _maybe_set_terminal(self, state: GameState) -> None:
        winner = self._winner(state)
        if winner is not None:
            state.terminal_winner = winner
            state.phase = "TERMINAL"
            state.discard_queue = []
            state.pending_steal_victim = None

    def _legal_dev_plays(self, state: GameState, player: int) -> List[str]:
        if state.dev_played_this_turn:
            return []
        playable = {card for card, fresh in state.dev_hands[player] if not fresh}
        actions: List[str] = []
        if "Ritter" in playable:
            actions.append("play:knight")
        if "Fortschritt" in playable:
            actions.append("play:progress")
        return actions

    def _legal_build_actions(self, state: GameState, player: int) -> List[str]:
        actions: List[str] = []
        hand = state.hands[player]
        if _has_resources(hand, ROAD_COST) and state.roads_remaining[player] > 0:
            for e in self.edge_ids:
                if self._can_build_road(state, player, e):
                    actions.append(f"build:road:{e}")
        if _has_resources(hand, SETTLEMENT_COST) and state.settlements_remaining[player] > 0:
            for x in self.crossing_ids:
                if self._can_build_settlement(state, player, x):
                    actions.append(f"build:settlement:{x}")
        if _has_resources(hand, CITY_COST) and state.cities_remaining[player] > 0:
            for x in self.crossing_ids:
                if self._can_build_city(state, player, x):
                    actions.append(f"build:city:{x}")
        if _has_resources(hand, DEV_COST) and sum(state.dev_deck.values()) > 0:
            actions.append("build:dev")
        return actions

    def _legal_maritime_trades(self, state: GameState, player: int) -> List[str]:
        hand = state.hands[player]
        harbors = self._player_harbors(state, player)
        has_three = "3:1" in harbors
        special = {h.split(":", 2)[2] for h in harbors if h.startswith("2:1:")}
        actions: List[str] = []
        for give in RESOURCES:
            if hand[give] >= 4:
                actions.extend(f"trade:maritime:4:{give}->{get}" for get in RESOURCES if get != give)
            if has_three and hand[give] >= 3:
                actions.extend(f"trade:maritime:3:{give}->{get}" for get in RESOURCES if get != give)
            if give in special and hand[give] >= 2:
                actions.extend(f"trade:maritime:2:{give}->{get}" for get in RESOURCES if get != give)
        return actions

    def _player_harbors(self, state: GameState, player: int) -> List[str]:
        out: List[str] = []
        for x, harbor in self.harbors.items():
            occ = state.crossing_occupants.get(x)
            if occ is not None and occ[0] == player:
                out.append(harbor)
        return out

    def _discard_combinations(self, hand: Dict[str, int], size: int) -> List[Dict[str, int]]:
        result: List[Dict[str, int]] = []
        current = _zero_resources()

        def rec(i: int, remaining: int) -> None:
            if i == len(RESOURCES):
                if remaining == 0:
                    result.append(dict(current))
                return
            res = RESOURCES[i]
            max_take = min(hand.get(res, 0), remaining)
            for n in range(max_take + 1):
                current[res] = n
                rec(i + 1, remaining - n)
            current[res] = 0

        rec(0, size)
        return result

    def _can_build_road(self, state: GameState, player: int, edge: str) -> bool:
        if state.edge_occupants[edge] is not None or state.roads_remaining[player] <= 0:
            return False
        a, b = self.edge_to_crossings[edge]
        for x in (a, b):
            occ = state.crossing_occupants[x]
            if occ is not None and occ[0] != player:
                continue  # foreign settlement/city blocks building through this crossing
            if occ is not None and occ[0] == player:
                return True
            if any(state.edge_occupants[e] == player for e in self.crossing_edges[x]):
                return True
        return False

    def _can_build_settlement(self, state: GameState, player: int, crossing: str) -> bool:
        if state.crossing_occupants[crossing] is not None or state.settlements_remaining[player] <= 0:
            return False
        for nb in self.crossing_neighbors[crossing]:
            if state.crossing_occupants[nb] is not None:
                return False
        return any(state.edge_occupants[e] == player for e in self.crossing_edges[crossing])

    def _can_build_city(self, state: GameState, player: int, crossing: str) -> bool:
        return (state.cities_remaining[player] > 0 and
                state.crossing_occupants.get(crossing) == (player, "Siedlung"))

    def _distribute_yield(self, state: GameState, roll: int) -> None:
        for tid in self.tile_ids:
            if tid == state.robber_tile:
                continue
            tile = self.tiles[tid]
            if tile.number != roll:
                continue
            res = LANDSCAPE_TO_RESOURCE[tile.landscape]
            if res is None:
                continue
            for x in tile.corners:
                occ = state.crossing_occupants[x]
                if occ is None:
                    continue
                p, kind = occ
                state.hands[p][res] += 2 if kind == "Stadt" else 1

    def _robber_victims(self, state: GameState) -> List[int]:
        victims = set()
        tile = self.tiles[state.robber_tile]
        for x in tile.corners:
            occ = state.crossing_occupants[x]
            if occ is None:
                continue
            p, _kind = occ
            if p != state.current_player_index and _total_resources(state.hands[p]) > 0:
                victims.add(p)
        return sorted(victims)

    def _remove_dev_card(self, state: GameState, player: int, card_type: str) -> None:
        for i, (card, fresh) in enumerate(state.dev_hands[player]):
            if card == card_type and not fresh:
                del state.dev_hands[player][i]
                return
        raise ValueError(f"No playable {card_type} card")

    def _update_largest_army(self, state: GameState, player: int) -> None:
        if state.knights_played[player] < 3:
            return
        owner = state.largest_army_owner
        if owner is None or player == owner or state.knights_played[player] > state.knights_played[owner]:
            state.largest_army_owner = player

    def _update_longest_road(self, state: GameState) -> None:
        lengths = [self._longest_road_length_for(state, p) for p in range(state.num_players)]
        old = state.longest_road_owner
        if old is not None and lengths[old] >= 5 and all(lengths[old] >= lengths[p] for p in range(state.num_players)):
            state.longest_road_length = lengths[old]
            return
        max_len = max(lengths) if lengths else 0
        candidates = [p for p, length in enumerate(lengths) if length == max_len and length >= 5]
        if len(candidates) == 1:
            state.longest_road_owner = candidates[0]
            state.longest_road_length = max_len
        elif old in candidates:
            state.longest_road_owner = old
            state.longest_road_length = lengths[old]
        else:
            state.longest_road_owner = None
            state.longest_road_length = max_len if candidates else 0

    def _longest_road_length_for(self, state: GameState, player: int) -> int:
        own_edges = {e for e, p in state.edge_occupants.items() if p == player}
        if not own_edges:
            return 0
        incident: Dict[str, List[str]] = {x: [] for x in self.crossing_ids}
        for e in own_edges:
            a, b = self.edge_to_crossings[e]
            incident[a].append(e)
            incident[b].append(e)
        blocked = {x for x, occ in state.crossing_occupants.items()
                   if occ is not None and occ[0] != player}

        best = 0

        def other_end(edge: str, x: str) -> str:
            a, b = self.edge_to_crossings[edge]
            return b if a == x else a

        def dfs(x: str, used: set, length: int) -> None:
            nonlocal best
            if length > best:
                best = length
            if x in blocked and length > 0:
                return
            for e in incident[x]:
                if e in used:
                    continue
                used.add(e)
                dfs(other_end(e, x), used, length + 1)
                used.remove(e)

        for x in self.crossing_ids:
            if incident[x]:
                dfs(x, set(), 0)
        return best

    def _dev_counts_for_render(self, cards: List[Tuple[str, bool]]) -> str:
        if not cards:
            return "none"
        parts = []
        for card in DEV_TYPES:
            old = sum(1 for c, fresh in cards if c == card and not fresh)
            fresh = sum(1 for c, fr in cards if c == card and fr)
            if old or fresh:
                if fresh:
                    parts.append(f"{card}:{old}+fresh{fresh}")
                else:
                    parts.append(f"{card}:{old}")
        return ",".join(parts)


def _normal_dev_counts(counts: Dict[str, int]) -> Dict[str, int]:
    out = {card: 0 for card in DEV_TYPES}
    for card, n in counts.items():
        if card not in out:
            raise ValueError(f"Unknown development card type {card!r}")
        if int(n) < 0:
            raise ValueError("Development card counts may not be negative")
        out[card] = int(n)
    return out


def _id_num(identifier: str) -> int:
    return int(identifier[1:])


def _owner_name(owner: Optional[int]) -> str:
    return "none" if owner is None else f"p{owner}"
