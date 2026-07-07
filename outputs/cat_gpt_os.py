"""
Minimal self-contained Catan-like implementation from the supplied German rule text.

Important documented gaps:
- The official beginner board figure is not present.  This file uses a small
  explicit abstract graph with 19 land-field labels.  It preserves the rulebook
  examples: roll 3 gives White Holz and Blue/Orange Erz; roll 8 gives Red 2 Erz
  and White 1 Erz; roll 10 gives White Wolle.
- Player-to-player trading is omitted because free negotiation is not a finite
  action protocol in the supplied text.
- Harbor locations/types are not supplied, so only 4:1 bank trade is enabled.
- Development-card counts are not supplied.  The default deck is one each of the
  three named types; pass dev_deck_counts to Game(...) to change this.
- Progress-card text is not supplied, so progress cards have no legal play action.
- Resource bank depletion is not supplied, so the bank is treated as unlimited.
"""

from dataclasses import dataclass
import copy
from typing import Dict, List, Optional, Sequence, Set, Tuple


TERMINAL = -1
CHANCE = -2
SIMULTANEOUS = -3

RESOURCE_NAMES = ("Holz", "Lehm", "Wolle", "Getreide", "Erz")
RESOURCE_INDEX = {name: i for i, name in enumerate(RESOURCE_NAMES)}

DEV_TYPES = ("Ritter", "Fortschritt", "Siegpunkte")
DEV_INDEX = {name: i for i, name in enumerate(DEV_TYPES)}

PLAYER_LABELS = ("Weiss", "Blau", "Orange", "Rot")

COST_ROAD = (1, 1, 0, 0, 0)          # Holz + Lehm
COST_SETTLEMENT = (1, 1, 1, 1, 0)    # Holz + Lehm + Wolle + Getreide
COST_CITY = (0, 0, 0, 2, 3)          # 2 Getreide + 3 Erz
COST_DEV = (0, 0, 1, 1, 1)           # Wolle + Getreide + Erz

DICE_WEIGHTS = {
    2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6,
    8: 5, 9: 4, 10: 3, 11: 2, 12: 1,
}

DEFAULT_DEV_DECK_COUNTS = (1, 1, 1)  # Assumption: one of each named type.


@dataclass(frozen=True)
class Tile:
    landscape: str
    resource: Optional[str]
    number: Optional[int]
    crossings: Tuple[str, ...]


def _edge_label(a: str, b: str) -> str:
    return "weg-" + a + "--" + b


_CHAIN_SPECS = (
    ("D-WeissStart", ("x-Weiss-Waldweg1", "x-Weiss-Waldweg2", "x-Weiss-Waldweg3")),
    ("Weiss-ZweitStart", ("x-Weiss-Zweitweg1", "x-Weiss-Zweitweg2", "x-Weiss-Zweitweg3")),
    ("B-BlauStart", ("x-Blau-Waldweg1", "x-Blau-Waldweg2", "x-Blau-Waldweg3")),
    ("Blau-ZweitStart", ("x-Blau-Zweitweg1", "x-Blau-Zweitweg2", "x-Blau-Zweitweg3")),
    ("C-OrangeStart", ("x-Orange-Getreideweg1", "x-Orange-Getreideweg2", "x-Orange-Getreideweg3")),
    ("Orange-ZweitStart", ("x-Orange-Zweitweg1", "x-Orange-Zweitweg2", "x-Orange-Zweitweg3")),
    ("A-RotStart", ("x-Rot-Erzweg1", "x-Rot-Erzweg2", "x-Rot-Erzweg3")),
    ("Rot-ZweitStart", ("x-Rot-Zweitweg1", "x-Rot-Zweitweg2", "x-Rot-Zweitweg3")),
)


def _make_edge_pairs() -> Tuple[Tuple[str, str], ...]:
    pairs: List[Tuple[str, str]] = []
    for start, chain in _CHAIN_SPECS:
        previous = start
        for point in chain:
            pairs.append((previous, point))
            previous = point
    return tuple(pairs)


def _make_crossings() -> Tuple[str, ...]:
    seen: Dict[str, None] = {}
    for start, chain in _CHAIN_SPECS:
        seen[start] = None
        for point in chain:
            seen[point] = None
    return tuple(seen.keys())


CROSSINGS = _make_crossings()
_EDGE_PAIRS = _make_edge_pairs()
EDGE_ENDPOINTS = {_edge_label(a, b): (a, b) for a, b in _EDGE_PAIRS}
EDGE_LABELS = tuple(EDGE_ENDPOINTS.keys())


def _make_graph_maps() -> Tuple[Dict[str, Tuple[str, ...]], Dict[str, Tuple[str, ...]]]:
    incident: Dict[str, List[str]] = {c: [] for c in CROSSINGS}
    neighbors: Dict[str, List[str]] = {c: [] for c in CROSSINGS}
    for edge, (a, b) in EDGE_ENDPOINTS.items():
        incident[a].append(edge)
        incident[b].append(edge)
        neighbors[a].append(b)
        neighbors[b].append(a)
    return (
        {c: tuple(incident[c]) for c in CROSSINGS},
        {c: tuple(neighbors[c]) for c in CROSSINGS},
    )


INCIDENT_EDGES, CROSSING_NEIGHBORS = _make_graph_maps()

_FIRST_EDGE_BY_START = {start: _edge_label(start, chain[0]) for start, chain in _CHAIN_SPECS}

INITIAL_SETTLEMENTS_BY_PLAYER = {
    0: ("D-WeissStart", "Weiss-ZweitStart"),
    1: ("B-BlauStart", "Blau-ZweitStart"),
    2: ("C-OrangeStart", "Orange-ZweitStart"),
    3: ("A-RotStart", "Rot-ZweitStart"),
}
INITIAL_ROADS_BY_PLAYER = {
    0: (_FIRST_EDGE_BY_START["D-WeissStart"], _FIRST_EDGE_BY_START["Weiss-ZweitStart"]),
    1: (_FIRST_EDGE_BY_START["B-BlauStart"], _FIRST_EDGE_BY_START["Blau-ZweitStart"]),
    2: (_FIRST_EDGE_BY_START["C-OrangeStart"], _FIRST_EDGE_BY_START["Orange-ZweitStart"]),
    3: (_FIRST_EDGE_BY_START["A-RotStart"], _FIRST_EDGE_BY_START["Rot-ZweitStart"]),
}
LETTERED_START_BY_PLAYER = {
    0: "D-WeissStart",
    1: "B-BlauStart",
    2: "C-OrangeStart",
    3: "A-RotStart",  # Assumption: A is Red because B/C/D are identified in text.
}

TILE_DATA = {
    "t01-Wald-3": Tile("Wald", "Holz", 3, ("D-WeissStart", "x-Weiss-Waldweg2")),
    "t02-Gebirge-3": Tile("Gebirge", "Erz", 3, ("B-BlauStart", "C-OrangeStart", "x-Blau-Waldweg2", "x-Orange-Getreideweg2")),
    "t03-Huegelland-unbekannt": Tile("Huegelland", "Lehm", None, ("B-BlauStart", "x-Blau-Zweitweg2")),
    "t04-Ackerland-unbekannt": Tile("Ackerland", "Getreide", None, ("C-OrangeStart", "x-Orange-Getreideweg2")),
    "t05-Ackerland-unbekannt": Tile("Ackerland", "Getreide", None, ("C-OrangeStart", "x-Orange-Zweitweg2")),
    "t06-Gebirge-8": Tile("Gebirge", "Erz", 8, ("A-RotStart", "Rot-ZweitStart", "D-WeissStart", "x-Rot-Erzweg2", "x-Weiss-Zweitweg2")),
    "t07-Weideland-10": Tile("Weideland", "Wolle", 10, ("D-WeissStart", "x-Weiss-Waldweg2")),
    "t08-Wueste-keinErtrag": Tile("Wueste", None, None, ()),
    "t09-Wald-unbekannt": Tile("Wald", "Holz", None, ("B-BlauStart", "x-Blau-Waldweg2")),
    "t10-Huegelland-unbekannt": Tile("Huegelland", "Lehm", None, ("x-Rot-Erzweg2",)),
    "t11-Weideland-unbekannt": Tile("Weideland", "Wolle", None, ("x-Weiss-Zweitweg2",)),
    "t12-Ackerland-unbekannt": Tile("Ackerland", "Getreide", None, ("x-Orange-Zweitweg2",)),
    "t13-Gebirge-unbekannt": Tile("Gebirge", "Erz", None, ()),
    "t14-Wald-unbekannt": Tile("Wald", "Holz", None, ()),
    "t15-Huegelland-unbekannt": Tile("Huegelland", "Lehm", None, ()),
    "t16-Weideland-unbekannt": Tile("Weideland", "Wolle", None, ()),
    "t17-Ackerland-unbekannt": Tile("Ackerland", "Getreide", None, ()),
    "t18-Gebirge-unbekannt": Tile("Gebirge", "Erz", None, ()),
    "t19-Wald-unbekannt": Tile("Wald", "Holz", None, ()),
}
TILE_LABELS = tuple(TILE_DATA.keys())

# Exact harbor positions/types are in the missing figure, so none are enabled.
# Format if extended: crossing -> ("3:1", None) or ("2:1", "Holz")
HARBORS: Dict[str, Tuple[str, Optional[str]]] = {}


@dataclass
class GameState:
    num_players: int
    phase: str
    turn_player: int
    resources: Tuple[Tuple[int, ...], ...]
    dev_old: Tuple[Tuple[int, ...], ...]
    dev_new: Tuple[Tuple[int, ...], ...]
    dev_deck: Tuple[int, ...]
    settlements: Dict[str, int]
    cities: Dict[str, int]
    roads: Dict[str, int]
    robber_tile: str
    last_dice: Optional[int] = None
    pending_discard: Tuple[int, ...] = ()
    resume_phase: str = "trade"
    steal_victim: Optional[int] = None
    dev_played: bool = False
    played_knights: Tuple[int, ...] = ()
    longest_road_owner: Optional[int] = None
    longest_road_length: int = 0
    largest_army_owner: Optional[int] = None
    winner: Optional[int] = None
    history: Tuple[str, ...] = ()


def _format_multiset(counts: Sequence[int]) -> str:
    parts = [f"{counts[i]}{RESOURCE_NAMES[i]}" for i in range(len(RESOURCE_NAMES)) if counts[i]]
    return "+".join(parts) if parts else "empty"


def _parse_multiset_payload(payload: str) -> Tuple[int, ...]:
    if payload == "empty":
        return tuple(0 for _ in RESOURCE_NAMES)
    if not payload:
        raise ValueError("empty multiset payload")
    counts = [0 for _ in RESOURCE_NAMES]
    for item in payload.split("+"):
        if not item or item != item.strip():
            raise ValueError("bad multiset item")
        j = 0
        while j < len(item) and item[j].isdigit():
            j += 1
        if j == 0:
            raise ValueError("multiset item needs a positive amount")
        amount = int(item[:j])
        resource = item[j:]
        if amount <= 0 or resource not in RESOURCE_INDEX:
            raise ValueError("bad multiset item")
        counts[RESOURCE_INDEX[resource]] += amount
    return tuple(counts)


class Game:
    def __init__(
        self,
        num_players: int = 4,
        start_player: int = 0,
        dev_deck_counts: Optional[Sequence[int]] = None,
    ):
        if num_players not in (3, 4):
            raise ValueError("The supplied text supports 3 or 4 players.")
        if not 0 <= start_player < num_players:
            raise ValueError("bad start_player")
        self.num_players = num_players
        self.player_labels = PLAYER_LABELS[:num_players]
        self.start_player = start_player
        if dev_deck_counts is None:
            dev_deck_counts = DEFAULT_DEV_DECK_COUNTS
        if len(dev_deck_counts) != len(DEV_TYPES):
            raise ValueError("dev_deck_counts must have one count per DEV_TYPES")
        if any(int(x) < 0 for x in dev_deck_counts):
            raise ValueError("dev deck counts must be nonnegative")
        self.dev_deck_counts = tuple(int(x) for x in dev_deck_counts)

    def initial_state(self) -> GameState:
        resources = [[0 for _ in RESOURCE_NAMES] for _ in range(self.num_players)]
        settlements: Dict[str, int] = {}
        roads: Dict[str, int] = {}

        for p in range(self.num_players):
            for crossing in INITIAL_SETTLEMENTS_BY_PLAYER[p]:
                settlements[crossing] = p
            for edge in INITIAL_ROADS_BY_PLAYER[p]:
                roads[edge] = p

        # Starting resources are granted only for the lettered settlement.
        for p in range(self.num_players):
            crossing = LETTERED_START_BY_PLAYER[p]
            for tile in TILE_DATA.values():
                if crossing in tile.crossings and tile.resource is not None:
                    resources[p][RESOURCE_INDEX[tile.resource]] += 1

        zeros_dev = tuple(tuple(0 for _ in DEV_TYPES) for _ in range(self.num_players))
        state = GameState(
            num_players=self.num_players,
            phase="pre_roll",
            turn_player=self.start_player,
            resources=tuple(tuple(row) for row in resources),
            dev_old=zeros_dev,
            dev_new=zeros_dev,
            dev_deck=self.dev_deck_counts,
            settlements=settlements,
            cities={},
            roads=roads,
            robber_tile="t08-Wueste-keinErtrag",
            played_knights=tuple(0 for _ in range(self.num_players)),
        )
        self._recompute_longest_road(state)
        return state

    def current_player(self, state: GameState) -> int:
        if self.is_terminal(state):
            return TERMINAL
        if state.phase.startswith("chance_"):
            return CHANCE
        if state.phase == "discard":
            return state.pending_discard[0] if state.pending_discard else state.turn_player
        return state.turn_player

    def legal_actions(self, state: GameState) -> List[str]:
        if self.is_terminal(state):
            return []

        phase = state.phase
        if phase == "chance_dice":
            return [f"chance:dice:{value}" for value in sorted(DICE_WEIGHTS)]
        if phase == "chance_dev":
            return [f"chance:dev:{DEV_TYPES[i]}" for i, c in enumerate(state.dev_deck) if c > 0]
        if phase == "chance_steal":
            if state.steal_victim is None:
                return []
            hand = state.resources[state.steal_victim]
            return [f"chance:steal:{RESOURCE_NAMES[i]}" for i, c in enumerate(hand) if c > 0]

        if phase == "pre_roll":
            return self._playable_dev_actions(state) + ["roll"]

        if phase == "discard":
            if not state.pending_discard:
                return []
            player = state.pending_discard[0]
            needed = self._hand_total(state, player) // 2
            return ["discard:" + _format_multiset(c) for c in self._discard_combinations(state.resources[player], needed)]

        if phase == "robber_move":
            return [f"robber:move:{label}" for label in TILE_LABELS if label != state.robber_tile]

        if phase == "robber_steal_victim":
            return [f"robber:steal:{self._player_name(p)}" for p in self._robber_victims(state)]

        if phase == "trade":
            return self._playable_dev_actions(state) + self._maritime_trade_actions(state) + ["finish_trade"]

        if phase == "build":
            return self._playable_dev_actions(state) + self._build_actions(state) + ["end_turn"]

        return []

    def apply_action(self, state: GameState, action: str) -> GameState:
        name = self.name_to_action(action)
        legal = self.legal_actions(state)
        if name not in legal:
            raise ValueError(f"illegal action for phase {state.phase}: {name}")

        ns = copy.deepcopy(state)
        ns.history = tuple(state.history) + (name,)
        phase = state.phase
        player = state.turn_player

        if phase == "pre_roll":
            if name == "roll":
                ns.phase = "chance_dice"
                return ns
            if name == "play:knight":
                self._start_knight_robber(ns, "pre_roll")
                return ns

        if phase == "chance_dice":
            value = int(name.rsplit(":", 1)[1])
            ns.last_dice = value
            if value == 7:
                ns.resume_phase = "trade"
                pending = tuple(p for p in range(self.num_players) if self._hand_total(ns, p) > 7)
                ns.pending_discard = pending
                ns.phase = "discard" if pending else "robber_move"
            else:
                self._distribute_yields(ns, value)
                ns.phase = "trade"
            return ns

        if phase == "discard":
            discard_player = state.pending_discard[0]
            counts = _parse_multiset_payload(name[len("discard:"):])
            self._change_resources(ns, discard_player, tuple(-x for x in counts))
            ns.pending_discard = tuple(state.pending_discard[1:])
            ns.phase = "discard" if ns.pending_discard else "robber_move"
            ns.resume_phase = "trade"
            return ns

        if phase == "robber_move":
            target = name[len("robber:move:"):]
            ns.robber_tile = target
            ns.steal_victim = None
            if self._robber_victims(ns):
                ns.phase = "robber_steal_victim"
            else:
                ns.phase = state.resume_phase
                self._maybe_finish(ns)
            return ns

        if phase == "robber_steal_victim":
            victim_token = name[len("robber:steal:"):]
            ns.steal_victim = self._parse_player_token(victim_token)
            ns.phase = "chance_steal"
            return ns

        if phase == "chance_steal":
            resource = name[len("chance:steal:"):]
            victim = state.steal_victim
            if victim is None:
                raise ValueError("no victim for steal")
            idx = RESOURCE_INDEX[resource]
            self._change_resources(ns, victim, tuple(-1 if i == idx else 0 for i in range(len(RESOURCE_NAMES))))
            self._change_resources(ns, player, tuple(1 if i == idx else 0 for i in range(len(RESOURCE_NAMES))))
            ns.steal_victim = None
            ns.phase = state.resume_phase
            self._maybe_finish(ns)
            return ns

        if phase == "trade":
            if name == "finish_trade":
                ns.phase = "build"
                return ns
            if name == "play:knight":
                self._start_knight_robber(ns, "trade")
                return ns
            if name.startswith("trade:maritime:"):
                self._apply_maritime_trade(ns, name)
                return ns

        if phase == "build":
            if name == "end_turn":
                self._end_turn(ns)
                return ns
            if name == "play:knight":
                self._start_knight_robber(ns, "build")
                return ns
            if name == "build:dev":
                self._pay(ns, player, COST_DEV)
                ns.phase = "chance_dev"
                return ns
            if name.startswith("build:road:"):
                edge = name[len("build:road:"):]
                self._pay(ns, player, COST_ROAD)
                ns.roads[edge] = player
                self._recompute_longest_road(ns)
                self._maybe_finish(ns)
                return ns
            if name.startswith("build:settlement:"):
                crossing = name[len("build:settlement:"):]
                self._pay(ns, player, COST_SETTLEMENT)
                ns.settlements[crossing] = player
                self._recompute_longest_road(ns)
                self._maybe_finish(ns)
                return ns
            if name.startswith("build:city:"):
                crossing = name[len("build:city:"):]
                self._pay(ns, player, COST_CITY)
                del ns.settlements[crossing]
                ns.cities[crossing] = player
                self._maybe_finish(ns)
                return ns

        if phase == "chance_dev":
            card = name[len("chance:dev:"):]
            idx = DEV_INDEX[card]
            deck = list(ns.dev_deck)
            deck[idx] -= 1
            ns.dev_deck = tuple(deck)
            dev_new = [list(row) for row in ns.dev_new]
            dev_new[player][idx] += 1
            ns.dev_new = tuple(tuple(row) for row in dev_new)
            ns.phase = "build"
            self._maybe_finish(ns)
            return ns

        raise ValueError(f"unhandled action: {name}")

    def is_terminal(self, state: GameState) -> bool:
        return self._implicit_winner(state) is not None

    def returns(self, state: GameState) -> List[float]:
        winner = self._implicit_winner(state)
        if winner is None:
            return [0.0 for _ in range(self.num_players)]
        loser_value = -1.0 / (self.num_players - 1)
        return [1.0 if p == winner else loser_value for p in range(self.num_players)]

    def render(self, state: GameState) -> str:
        current = self.current_player(state)
        if current == TERMINAL:
            current_text = "TERMINAL"
        elif current == CHANCE:
            current_text = "CHANCE"
        else:
            current_text = self._player_name(current)

        tile_parts = []
        for label in TILE_LABELS:
            tile = TILE_DATA[label]
            number = tile.number if tile.number is not None else "?"
            robber = "R" if label == state.robber_tile else "-"
            tile_parts.append(f"{label}:{tile.landscape}/{number}/{robber}")

        settlement_parts = [f"{c}:{self._player_name(state.settlements[c])}" for c in CROSSINGS if c in state.settlements]
        city_parts = [f"{c}:{self._player_name(state.cities[c])}" for c in CROSSINGS if c in state.cities]
        road_parts = [f"{e}:{self._player_name(state.roads[e])}" for e in EDGE_LABELS if e in state.roads]

        player_parts = []
        for p in range(self.num_players):
            player_parts.append(
                f"{self._player_name(p)}:"
                f"vp={self._public_victory_points(state, p)}/{self._victory_points(state, p)},"
                f"hand={self._format_counts(RESOURCE_NAMES, state.resources[p])},"
                f"dev_old={self._format_counts(DEV_TYPES, state.dev_old[p])},"
                f"dev_new={self._format_counts(DEV_TYPES, state.dev_new[p])},"
                f"knights={state.played_knights[p]},"
                f"supply=S{self._settlements_left(state, p)}/C{self._cities_left(state, p)}/R{self._roads_left(state, p)}"
            )

        pending = ",".join(self._player_name(p) for p in state.pending_discard) if state.pending_discard else "-"
        winner = self._implicit_winner(state)
        return "\n".join([
            f"phase={state.phase} current={current_text} turn={self._player_name(state.turn_player)} last_dice={state.last_dice} winner={self._owner_text(winner)}",
            "tiles=" + ";".join(tile_parts),
            "settlements=" + (";".join(settlement_parts) if settlement_parts else "-"),
            "cities=" + (";".join(city_parts) if city_parts else "-"),
            "roads=" + (";".join(road_parts) if road_parts else "-"),
            "players=" + "|".join(player_parts),
            f"specials=Laengste:{self._owner_text(state.longest_road_owner)}:{state.longest_road_length},GroessteRittermacht:{self._owner_text(state.largest_army_owner)}",
            f"dev_deck={self._format_counts(DEV_TYPES, state.dev_deck)} pending_discard={pending} steal_victim={self._owner_text(state.steal_victim)}",
        ])

    def action_to_name(self, action: str) -> str:
        canonical = self.name_to_action(action)
        if canonical != action:
            raise ValueError(f"not canonical; canonical form is {canonical}")
        return canonical

    def name_to_action(self, name: str) -> str:
        if not isinstance(name, str):
            raise TypeError("actions are canonical strings")

        if name in {"roll", "finish_trade", "end_turn", "play:knight", "build:dev"}:
            return name

        if name.startswith("build:road:"):
            label = name[len("build:road:"):]
            if label not in EDGE_ENDPOINTS:
                raise ValueError("unknown road edge")
            return f"build:road:{label}"

        if name.startswith("build:settlement:"):
            label = name[len("build:settlement:"):]
            if label not in CROSSINGS:
                raise ValueError("unknown crossing")
            return f"build:settlement:{label}"

        if name.startswith("build:city:"):
            label = name[len("build:city:"):]
            if label not in CROSSINGS:
                raise ValueError("unknown crossing")
            return f"build:city:{label}"

        if name.startswith("robber:move:"):
            label = name[len("robber:move:"):]
            if label not in TILE_DATA:
                raise ValueError("unknown tile")
            return f"robber:move:{label}"

        if name.startswith("robber:steal:"):
            token = name[len("robber:steal:"):]
            p = self._parse_player_token(token)
            return f"robber:steal:{self._player_name(p)}"

        if name.startswith("chance:dice:"):
            value = int(name[len("chance:dice:"):])
            if value not in DICE_WEIGHTS:
                raise ValueError("bad dice sum")
            return f"chance:dice:{value}"

        if name.startswith("chance:dev:"):
            card = name[len("chance:dev:"):]
            if card not in DEV_INDEX:
                raise ValueError("bad development card type")
            return f"chance:dev:{card}"

        if name.startswith("chance:steal:"):
            resource = name[len("chance:steal:"):]
            if resource not in RESOURCE_INDEX:
                raise ValueError("bad resource")
            return f"chance:steal:{resource}"

        if name.startswith("discard:"):
            counts = _parse_multiset_payload(name[len("discard:"):])
            return "discard:" + _format_multiset(counts)

        if name.startswith("trade:maritime:"):
            parts = name.split(":")
            if len(parts) != 4:
                raise ValueError("bad maritime trade action")
            ratio = int(parts[2])
            if ratio not in (2, 3, 4):
                raise ValueError("bad maritime ratio")
            if "->" not in parts[3]:
                raise ValueError("bad maritime trade resources")
            give, get = parts[3].split("->", 1)
            if give not in RESOURCE_INDEX or get not in RESOURCE_INDEX:
                raise ValueError("bad maritime resource")
            return f"trade:maritime:{ratio}:{give}->{get}"

        raise ValueError("unknown action name")

    def chance_outcomes(self, state: GameState) -> List[Tuple[str, float]]:
        if self.is_terminal(state):
            return []
        if state.phase == "chance_dice":
            return [(f"chance:dice:{v}", DICE_WEIGHTS[v] / 36.0) for v in sorted(DICE_WEIGHTS)]
        if state.phase == "chance_dev":
            total = sum(state.dev_deck)
            return [(f"chance:dev:{DEV_TYPES[i]}", c / total) for i, c in enumerate(state.dev_deck) if c > 0] if total else []
        if state.phase == "chance_steal" and state.steal_victim is not None:
            hand = state.resources[state.steal_victim]
            total = sum(hand)
            return [(f"chance:steal:{RESOURCE_NAMES[i]}", c / total) for i, c in enumerate(hand) if c > 0] if total else []
        return []

    def information_state(self, state: GameState, player: int) -> str:
        if not 0 <= player < self.num_players:
            raise ValueError("bad player")

        current = self.current_player(state)
        if current == TERMINAL:
            current_text = "TERMINAL"
        elif current == CHANCE:
            current_text = "CHANCE"
        else:
            current_text = self._player_name(current)

        settlement_parts = [f"{c}:{self._player_name(state.settlements[c])}" for c in CROSSINGS if c in state.settlements]
        city_parts = [f"{c}:{self._player_name(state.cities[c])}" for c in CROSSINGS if c in state.cities]
        road_parts = [f"{e}:{self._player_name(state.roads[e])}" for e in EDGE_LABELS if e in state.roads]

        player_parts = []
        for p in range(self.num_players):
            if p == player:
                private = (
                    f"hand={self._format_counts(RESOURCE_NAMES, state.resources[p])},"
                    f"dev_old={self._format_counts(DEV_TYPES, state.dev_old[p])},"
                    f"dev_new={self._format_counts(DEV_TYPES, state.dev_new[p])},"
                    f"vp_total={self._victory_points(state, p)}"
                )
            else:
                private = "hand=hidden,dev=hidden"
            player_parts.append(
                f"{self._player_name(p)}:"
                f"vp_public={self._public_victory_points(state, p)},"
                f"knights={state.played_knights[p]},"
                f"{private}"
            )

        return "\n".join([
            f"viewer={self._player_name(player)} phase={state.phase} current={current_text} turn={self._player_name(state.turn_player)} last_dice={state.last_dice} robber={state.robber_tile}",
            "settlements=" + (";".join(settlement_parts) if settlement_parts else "-"),
            "cities=" + (";".join(city_parts) if city_parts else "-"),
            "roads=" + (";".join(road_parts) if road_parts else "-"),
            "players=" + "|".join(player_parts),
            f"specials=Laengste:{self._owner_text(state.longest_road_owner)}:{state.longest_road_length},GroessteRittermacht:{self._owner_text(state.largest_army_owner)}",
            f"dev_deck_size={sum(state.dev_deck)}",
        ])

    # ----- helpers -----

    def _player_name(self, player: int) -> str:
        return f"p{player}-{self.player_labels[player]}"

    def _owner_text(self, owner: Optional[int]) -> str:
        return "None" if owner is None else self._player_name(owner)

    def _parse_player_token(self, token: str) -> int:
        if not token.startswith("p") or "-" not in token:
            raise ValueError("bad player token")
        number_text, label = token[1:].split("-", 1)
        if not number_text.isdigit():
            raise ValueError("bad player token")
        player = int(number_text)
        if not 0 <= player < self.num_players:
            raise ValueError("bad player")
        if label != self.player_labels[player]:
            raise ValueError("bad player label")
        return player

    def _format_counts(self, names: Sequence[str], counts: Sequence[int]) -> str:
        return "{" + ",".join(f"{names[i]}:{counts[i]}" for i in range(len(names))) + "}"

    def _hand_total(self, state: GameState, player: int) -> int:
        return sum(state.resources[player])

    def _change_resources(self, state: GameState, player: int, deltas: Sequence[int]) -> None:
        rows = [list(row) for row in state.resources]
        for i, delta in enumerate(deltas):
            rows[player][i] += delta
            if rows[player][i] < 0:
                raise ValueError("resource count below zero")
        state.resources = tuple(tuple(row) for row in rows)

    def _pay(self, state: GameState, player: int, cost: Sequence[int]) -> None:
        self._change_resources(state, player, tuple(-x for x in cost))

    def _has_resources(self, state: GameState, player: int, cost: Sequence[int]) -> bool:
        return all(state.resources[player][i] >= cost[i] for i in range(len(RESOURCE_NAMES)))

    def _discard_combinations(self, hand: Sequence[int], needed: int) -> List[Tuple[int, ...]]:
        result: List[Tuple[int, ...]] = []

        def rec(index: int, remaining: int, current: List[int]) -> None:
            if index == len(RESOURCE_NAMES) - 1:
                if 0 <= remaining <= hand[index]:
                    result.append(tuple(current + [remaining]))
                return
            for amount in range(min(hand[index], remaining) + 1):
                rec(index + 1, remaining - amount, current + [amount])

        rec(0, needed, [])
        return result

    def _playable_dev_actions(self, state: GameState) -> List[str]:
        player = state.turn_player
        if state.dev_played:
            return []
        if state.dev_old[player][DEV_INDEX["Ritter"]] > 0:
            return ["play:knight"]
        return []

    def _start_knight_robber(self, state: GameState, resume_phase: str) -> None:
        player = state.turn_player
        old = [list(row) for row in state.dev_old]
        old[player][DEV_INDEX["Ritter"]] -= 1
        state.dev_old = tuple(tuple(row) for row in old)
        knights = list(state.played_knights)
        knights[player] += 1
        state.played_knights = tuple(knights)
        state.dev_played = True
        self._update_largest_army(state, player)
        state.resume_phase = resume_phase
        state.phase = "robber_move"
        state.steal_victim = None

    def _update_largest_army(self, state: GameState, active: int) -> None:
        current = state.largest_army_owner
        if current is None:
            if state.played_knights[active] >= 3:
                state.largest_army_owner = active
        elif active != current and state.played_knights[active] > state.played_knights[current]:
            state.largest_army_owner = active

    def _maritime_trade_actions(self, state: GameState) -> List[str]:
        player = state.turn_player
        rights: List[Tuple[int, Optional[str]]] = [(4, None)]

        for crossing, harbor in HARBORS.items():
            if self._building_owner(state, crossing) == player:
                kind, resource = harbor
                if kind == "3:1":
                    rights.append((3, None))
                elif kind == "2:1" and resource in RESOURCE_INDEX:
                    rights.append((2, resource))

        ordered_rights: List[Tuple[int, Optional[str]]] = []
        seen: Set[Tuple[int, Optional[str]]] = set()
        for right in rights:
            if right not in seen:
                ordered_rights.append(right)
                seen.add(right)

        actions: List[str] = []
        hand = state.resources[player]
        for ratio, specific in ordered_rights:
            give_options = [specific] if specific is not None else list(RESOURCE_NAMES)
            for give in give_options:
                if give is None:
                    continue
                if hand[RESOURCE_INDEX[give]] >= ratio:
                    for get in RESOURCE_NAMES:
                        if get != give:
                            actions.append(f"trade:maritime:{ratio}:{give}->{get}")
        return actions

    def _apply_maritime_trade(self, state: GameState, name: str) -> None:
        parts = name.split(":")
        ratio = int(parts[2])
        give, get = parts[3].split("->", 1)
        deltas = [0 for _ in RESOURCE_NAMES]
        deltas[RESOURCE_INDEX[give]] -= ratio
        deltas[RESOURCE_INDEX[get]] += 1
        self._change_resources(state, state.turn_player, deltas)

    def _build_actions(self, state: GameState) -> List[str]:
        player = state.turn_player
        actions: List[str] = []

        if self._has_resources(state, player, COST_ROAD):
            for edge in EDGE_LABELS:
                if self._can_build_road(state, player, edge):
                    actions.append(f"build:road:{edge}")

        if self._has_resources(state, player, COST_SETTLEMENT):
            for crossing in CROSSINGS:
                if self._can_build_settlement(state, player, crossing):
                    actions.append(f"build:settlement:{crossing}")

        if self._has_resources(state, player, COST_CITY):
            for crossing in CROSSINGS:
                if self._can_build_city(state, player, crossing):
                    actions.append(f"build:city:{crossing}")

        if sum(state.dev_deck) > 0 and self._has_resources(state, player, COST_DEV):
            actions.append("build:dev")

        return actions

    def _building_owner(self, state: GameState, crossing: str) -> Optional[int]:
        if crossing in state.settlements:
            return state.settlements[crossing]
        if crossing in state.cities:
            return state.cities[crossing]
        return None

    def _can_build_road(self, state: GameState, player: int, edge: str) -> bool:
        if edge in state.roads or self._roads_left(state, player) <= 0:
            return False
        a, b = EDGE_ENDPOINTS[edge]
        return self._road_connects_at(state, player, a) or self._road_connects_at(state, player, b)

    def _road_connects_at(self, state: GameState, player: int, crossing: str) -> bool:
        owner = self._building_owner(state, crossing)
        if owner is not None:
            return owner == player
        return any(state.roads.get(edge) == player for edge in INCIDENT_EDGES[crossing])

    def _can_build_settlement(self, state: GameState, player: int, crossing: str) -> bool:
        if self._building_owner(state, crossing) is not None:
            return False
        if self._settlements_left(state, player) <= 0:
            return False
        if not any(state.roads.get(edge) == player for edge in INCIDENT_EDGES[crossing]):
            return False
        for neighbor in CROSSING_NEIGHBORS[crossing]:
            if self._building_owner(state, neighbor) is not None:
                return False
        return True

    def _can_build_city(self, state: GameState, player: int, crossing: str) -> bool:
        return state.settlements.get(crossing) == player and self._cities_left(state, player) > 0

    def _settlements_left(self, state: GameState, player: int) -> int:
        return 5 - sum(1 for owner in state.settlements.values() if owner == player)

    def _cities_left(self, state: GameState, player: int) -> int:
        return 4 - sum(1 for owner in state.cities.values() if owner == player)

    def _roads_left(self, state: GameState, player: int) -> int:
        return 15 - sum(1 for owner in state.roads.values() if owner == player)

    def _distribute_yields(self, state: GameState, dice_value: int) -> None:
        for label, tile in TILE_DATA.items():
            if label == state.robber_tile:
                continue
            if tile.number != dice_value or tile.resource is None:
                continue
            idx = RESOURCE_INDEX[tile.resource]
            for crossing in tile.crossings:
                if crossing in state.cities:
                    owner = state.cities[crossing]
                    if owner < self.num_players:
                        self._change_resources(state, owner, tuple(2 if i == idx else 0 for i in range(len(RESOURCE_NAMES))))
                elif crossing in state.settlements:
                    owner = state.settlements[crossing]
                    if owner < self.num_players:
                        self._change_resources(state, owner, tuple(1 if i == idx else 0 for i in range(len(RESOURCE_NAMES))))

    def _robber_victims(self, state: GameState) -> Tuple[int, ...]:
        tile = TILE_DATA.get(state.robber_tile)
        if tile is None:
            return ()
        possible: Set[int] = set()
        for crossing in tile.crossings:
            owner = self._building_owner(state, crossing)
            if owner is not None and owner != state.turn_player and owner < self.num_players and self._hand_total(state, owner) > 0:
                possible.add(owner)
        return tuple(p for p in range(self.num_players) if p in possible)

    def _end_turn(self, state: GameState) -> None:
        player = state.turn_player
        old = [list(row) for row in state.dev_old]
        new = [list(row) for row in state.dev_new]
        for i in range(len(DEV_TYPES)):
            old[player][i] += new[player][i]
            new[player][i] = 0
        state.dev_old = tuple(tuple(row) for row in old)
        state.dev_new = tuple(tuple(row) for row in new)
        state.dev_played = False
        state.pending_discard = ()
        state.steal_victim = None
        state.last_dice = None
        state.turn_player = (state.turn_player + 1) % self.num_players
        state.phase = "pre_roll"

    def _longest_road_length(self, state: GameState, player: int) -> int:
        player_edges = [edge for edge in EDGE_LABELS if state.roads.get(edge) == player]
        if not player_edges:
            return 0

        adj: Dict[str, List[Tuple[str, str]]] = {c: [] for c in CROSSINGS}
        for edge in player_edges:
            a, b = EDGE_ENDPOINTS[edge]
            adj[a].append((edge, b))
            adj[b].append((edge, a))

        blocked = {
            c for c, owner in state.settlements.items() if owner != player
        } | {
            c for c, owner in state.cities.items() if owner != player
        }

        best = 0

        def dfs(vertex: str, used_edges: Set[str], length: int) -> None:
            nonlocal best
            best = max(best, length)
            if vertex in blocked:
                return
            for edge, nxt in adj.get(vertex, ()):
                if edge not in used_edges:
                    used_edges.add(edge)
                    dfs(nxt, used_edges, length + 1)
                    used_edges.remove(edge)

        for edge in player_edges:
            a, b = EDGE_ENDPOINTS[edge]
            dfs(a, {edge}, 1)
            dfs(b, {edge}, 1)
        return best

    def _recompute_longest_road(self, state: GameState) -> None:
        lengths = [self._longest_road_length(state, p) for p in range(self.num_players)]
        current = state.longest_road_owner
        active = state.turn_player

        if current is None or not (0 <= current < self.num_players):
            if lengths[active] >= 5:
                state.longest_road_owner = active
                state.longest_road_length = lengths[active]
                return
            max_len = max(lengths) if lengths else 0
            if max_len >= 5 and lengths.count(max_len) == 1:
                owner = lengths.index(max_len)
                state.longest_road_owner = owner
                state.longest_road_length = max_len
            else:
                state.longest_road_owner = None
                state.longest_road_length = 0
            return

        current_len = lengths[current]
        challengers = [p for p in range(self.num_players) if p != current and lengths[p] >= 5 and lengths[p] > current_len]
        if active in challengers:
            state.longest_road_owner = active
        elif challengers:
            state.longest_road_owner = max(challengers, key=lambda p: (lengths[p], -p))
        # Assumption for unclear drop/tie rules: current holder keeps the card unless
        # another player is strictly longer than the holder's current road length.
        state.longest_road_length = lengths[state.longest_road_owner]

    def _public_victory_points(self, state: GameState, player: int) -> int:
        vp = sum(1 for owner in state.settlements.values() if owner == player)
        vp += 2 * sum(1 for owner in state.cities.values() if owner == player)
        if state.longest_road_owner == player:
            vp += 2
        if state.largest_army_owner == player:
            vp += 2
        return vp

    def _victory_points(self, state: GameState, player: int) -> int:
        # Assumption: each "Siegpunkte" development card is worth 1 VP.
        idx = DEV_INDEX["Siegpunkte"]
        return self._public_victory_points(state, player) + state.dev_old[player][idx] + state.dev_new[player][idx]

    def _implicit_winner(self, state: GameState) -> Optional[int]:
        if state.winner is not None:
            return state.winner
        if state.phase in ("pre_roll", "trade", "build") and 0 <= state.turn_player < self.num_players:
            if self._victory_points(state, state.turn_player) >= 10:
                return state.turn_player
        return None

    def _maybe_finish(self, state: GameState) -> None:
        winner = self._implicit_winner(state)
        if winner is not None:
            state.winner = winner
            state.phase = "terminal"
