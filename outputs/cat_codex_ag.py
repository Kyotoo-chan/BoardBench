"""Conservative CATAN engine generated from the supplied rule text.

The rule text gives the core CATAN rules, but the extracted text does not
include the page-1 board graph, exact harbor positions, number-chip set, or
development-card deck composition.  This module therefore implements the rules
as a deterministic engine over a small documented abstract board that preserves
the explicit examples in the text.  Callers may still edit the returned
GameState if they want to supply a more faithful board/deck from an allowed
source.
"""

from __future__ import annotations

import copy
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


TERMINAL = -1
CHANCE = -2
SIMULTANEOUS = -3

RESOURCES = ("Holz", "Lehm", "Wolle", "Getreide", "Erz")
LANDSCAPE_TO_RESOURCE = {
    "Wald": "Holz",
    "Huegelland": "Lehm",
    "Weideland": "Wolle",
    "Ackerland": "Getreide",
    "Gebirge": "Erz",
}

ROAD_COST = {"Lehm": 1, "Holz": 1}
SETTLEMENT_COST = {"Lehm": 1, "Holz": 1, "Wolle": 1, "Getreide": 1}
CITY_COST = {"Erz": 3, "Getreide": 2}
DEV_COST = {"Erz": 1, "Wolle": 1, "Getreide": 1}

DICE_WEIGHTS = {
    2: 1,
    3: 2,
    4: 3,
    5: 4,
    6: 5,
    7: 6,
    8: 5,
    9: 4,
    10: 3,
    11: 2,
    12: 1,
}

COLORS = ("Weiss", "Blau", "Orange", "Rot")


@dataclass(frozen=True)
class Tile:
    id: str
    landscape: str
    number: Optional[int]
    crossings: Tuple[str, ...]


@dataclass(frozen=True)
class Crossing:
    id: str
    harbor: Optional[str] = None


@dataclass(frozen=True)
class Edge:
    id: str
    a: str
    b: str


@dataclass
class DevCard:
    kind: str
    bought_turn: bool = False


@dataclass
class GameState:
    num_players: int
    phase: str
    current: int
    tiles: Dict[str, Tile]
    crossings: Dict[str, Crossing]
    edges: Dict[str, Edge]
    settlements: Dict[str, Tuple[int, str]]
    roads: Dict[str, int]
    hands: List[Dict[str, int]]
    dev_hands: List[List[DevCard]]
    dev_deck: List[str]
    settlement_supply: List[int]
    city_supply: List[int]
    road_supply: List[int]
    played_knights: List[int]
    dev_card_played: List[bool]
    robber_tile: str
    last_roll: Optional[int] = None
    longest_road_owner: Optional[int] = None
    largest_army_owner: Optional[int] = None
    pending_discards: List[int] = field(default_factory=list)
    pending_robber_return_phase: str = "trade"
    pending_steal_victims: List[int] = field(default_factory=list)
    pending_steal_victim: Optional[int] = None
    pending_dev_player: Optional[int] = None
    terminal_winner: Optional[int] = None
    history: List[str] = field(default_factory=list)


class Game:
    """Self-contained CATAN rules engine with explicit chance nodes."""

    def __init__(self, num_players: int = 4, dev_deck: Optional[Sequence[str]] = None):
        if num_players not in (3, 4):
            raise ValueError("The supplied text supports 3 players by removing red, and otherwise shows 4 colors.")
        self.num_players = num_players
        self.initial_dev_deck = list(dev_deck or [])
        for card in self.initial_dev_deck:
            if card not in ("Ritter", "Fortschritt", "Siegpunkte"):
                raise ValueError(f"Unknown development card kind: {card}")

    def initial_state(self) -> GameState:
        tiles, crossings, edges, settlements, roads, lettered = self._abstract_board(self.num_players)
        hands = [{resource: 0 for resource in RESOURCES} for _ in range(self.num_players)]
        dev_hands = [[] for _ in range(self.num_players)]

        for player, crossing_id in lettered.items():
            if player >= self.num_players:
                continue
            for tile in tiles.values():
                if crossing_id in tile.crossings:
                    resource = LANDSCAPE_TO_RESOURCE.get(tile.landscape)
                    if resource:
                        hands[player][resource] += 1

        preplaced_settlements = [0 for _ in range(self.num_players)]
        preplaced_roads = [0 for _ in range(self.num_players)]
        for player, _kind in settlements.values():
            if player < self.num_players:
                preplaced_settlements[player] += 1
        for player in roads.values():
            if player < self.num_players:
                preplaced_roads[player] += 1

        desert = next((tile.id for tile in tiles.values() if tile.landscape == "Wueste"), "t8")
        return GameState(
            num_players=self.num_players,
            phase="pre_roll",
            current=0,
            tiles=tiles,
            crossings=crossings,
            edges=edges,
            settlements=settlements,
            roads=roads,
            hands=hands,
            dev_hands=dev_hands,
            dev_deck=list(self.initial_dev_deck),
            settlement_supply=[5 - preplaced_settlements[p] for p in range(self.num_players)],
            city_supply=[4 for _ in range(self.num_players)],
            road_supply=[15 - preplaced_roads[p] for p in range(self.num_players)],
            played_knights=[0 for _ in range(self.num_players)],
            dev_card_played=[False for _ in range(self.num_players)],
            robber_tile=desert,
        )

    def current_player(self, state: GameState) -> int:
        if self.is_terminal(state):
            return TERMINAL
        if state.phase in ("dice_chance", "dev_chance", "steal_chance"):
            return CHANCE
        if state.phase == "discard" and state.pending_discards:
            return state.pending_discards[0]
        return state.current

    def legal_actions(self, state: GameState) -> List[str]:
        if self.is_terminal(state):
            return []

        phase = state.phase
        player = self.current_player(state)

        if phase == "pre_roll":
            return self._playable_dev_actions(state, state.current) + ["roll"]
        if phase == "dice_chance":
            return [f"chance:dice:{value}" for value in sorted(DICE_WEIGHTS)]
        if phase == "discard":
            return self._discard_actions(state.hands[player], self._discard_count(state.hands[player]))
        if phase == "robber_move":
            return [
                f"robber:move:{tile_id}"
                for tile_id in sorted(state.tiles)
                if tile_id != state.robber_tile and state.tiles[tile_id].landscape != "Meer"
            ]
        if phase == "robber_steal":
            if not state.pending_steal_victims:
                return ["robber:steal:none"]
            return [f"robber:steal:p{victim}" for victim in state.pending_steal_victims]
        if phase == "steal_chance":
            victim = state.pending_steal_victim
            if victim is None:
                return []
            return [f"chance:steal:{r}" for r in RESOURCES if state.hands[victim].get(r, 0) > 0]
        if phase == "trade":
            actions = []
            actions.extend(self._playable_dev_actions(state, state.current))
            actions.extend(self._maritime_trade_actions(state, state.current))
            actions.append("pass")
            return actions
        if phase == "build":
            actions = []
            actions.extend(self._playable_dev_actions(state, state.current))
            actions.extend(self._build_actions(state, state.current))
            actions.append("pass")
            return actions
        if phase == "dev_chance":
            counts = Counter(state.dev_deck)
            return [f"chance:dev:{kind}" for kind in sorted(counts)]
        return []

    def apply_action(self, state: GameState, action: str) -> GameState:
        action = self.action_to_name(action)
        legal = self.legal_actions(state)
        if action not in legal:
            raise ValueError(f"Illegal action {action!r} in phase {state.phase}; legal actions are {legal!r}")

        next_state = copy.deepcopy(state)
        next_state.history.append(action)
        phase = next_state.phase

        if phase == "pre_roll":
            if action == "roll":
                next_state.phase = "dice_chance"
            elif action == "play:knight":
                self._play_knight(next_state, "pre_roll")

        elif phase == "dice_chance":
            roll = int(action.rsplit(":", 1)[1])
            next_state.last_roll = roll
            if roll == 7:
                next_state.pending_discards = [
                    p for p in range(next_state.num_players) if self._hand_total(next_state.hands[p]) > 7
                ]
                next_state.pending_robber_return_phase = "trade"
                next_state.phase = "discard" if next_state.pending_discards else "robber_move"
            else:
                self._distribute_yield(next_state, roll)
                next_state.phase = "trade"

        elif phase == "discard":
            player = next_state.pending_discards[0]
            cards = self._parse_multiset(action[len("discard:") :])
            self._subtract_cards(next_state.hands[player], cards)
            next_state.pending_discards.pop(0)
            next_state.phase = "discard" if next_state.pending_discards else "robber_move"

        elif phase == "robber_move":
            tile_id = action.rsplit(":", 1)[1]
            next_state.robber_tile = tile_id
            victims = self._robber_victims(next_state, tile_id, next_state.current)
            next_state.pending_steal_victims = victims
            next_state.pending_steal_victim = None
            next_state.phase = "robber_steal" if victims else next_state.pending_robber_return_phase

        elif phase == "robber_steal":
            if action == "robber:steal:none":
                next_state.pending_steal_victim = None
                next_state.pending_steal_victims = []
                next_state.phase = next_state.pending_robber_return_phase
            else:
                victim = int(action.rsplit("p", 1)[1])
                next_state.pending_steal_victim = victim
                next_state.phase = "steal_chance"

        elif phase == "steal_chance":
            resource = action.rsplit(":", 1)[1]
            victim = next_state.pending_steal_victim
            if victim is None:
                raise ValueError("Missing robber steal victim")
            self._subtract_cards(next_state.hands[victim], {resource: 1})
            next_state.hands[next_state.current][resource] += 1
            next_state.pending_steal_victim = None
            next_state.pending_steal_victims = []
            next_state.phase = next_state.pending_robber_return_phase

        elif phase == "trade":
            if action == "pass":
                next_state.phase = "build"
            elif action == "play:knight":
                self._play_knight(next_state, "trade")
            elif action.startswith("trade:maritime:"):
                _trade, _kind, ratio_text, exchange = action.split(":")
                ratio = int(ratio_text)
                give, get = exchange.split("->")
                self._subtract_cards(next_state.hands[next_state.current], {give: ratio})
                next_state.hands[next_state.current][get] += 1

        elif phase == "build":
            if action == "pass":
                if self._victory_points(next_state, next_state.current) >= 10:
                    self._make_terminal(next_state, next_state.current)
                else:
                    self._end_turn(next_state)
            elif action == "play:knight":
                self._play_knight(next_state, "build")
            elif action.startswith("build:road:"):
                edge_id = action.rsplit(":", 1)[1]
                self._pay(next_state, next_state.current, ROAD_COST)
                next_state.roads[edge_id] = next_state.current
                next_state.road_supply[next_state.current] -= 1
                self._update_longest_road(next_state, next_state.current)
                self._maybe_terminal(next_state)
            elif action.startswith("build:settlement:"):
                crossing_id = action.rsplit(":", 1)[1]
                self._pay(next_state, next_state.current, SETTLEMENT_COST)
                next_state.settlements[crossing_id] = (next_state.current, "settlement")
                next_state.settlement_supply[next_state.current] -= 1
                self._update_longest_road(next_state, next_state.current)
                self._maybe_terminal(next_state)
            elif action.startswith("build:city:"):
                crossing_id = action.rsplit(":", 1)[1]
                self._pay(next_state, next_state.current, CITY_COST)
                next_state.settlements[crossing_id] = (next_state.current, "city")
                next_state.city_supply[next_state.current] -= 1
                next_state.settlement_supply[next_state.current] += 1
                self._maybe_terminal(next_state)
            elif action == "build:dev":
                self._pay(next_state, next_state.current, DEV_COST)
                next_state.pending_dev_player = next_state.current
                next_state.phase = "dev_chance"

        elif phase == "dev_chance":
            card = action.rsplit(":", 1)[1]
            next_state.dev_deck.remove(card)
            player = next_state.pending_dev_player
            if player is None:
                raise ValueError("Missing development-card buyer")
            next_state.dev_hands[player].append(DevCard(card, bought_turn=True))
            next_state.pending_dev_player = None
            next_state.phase = "build"
            self._maybe_terminal(next_state)

        return next_state

    def is_terminal(self, state: GameState) -> bool:
        return state.phase == "terminal" or state.terminal_winner is not None

    def returns(self, state: GameState) -> List[float]:
        if not self.is_terminal(state):
            return [0.0 for _ in range(state.num_players)]
        winner = state.terminal_winner
        if winner is None:
            return [0.0 for _ in range(state.num_players)]
        if state.num_players == 1:
            return [1.0]
        loss = -1.0 / float(state.num_players - 1)
        return [1.0 if p == winner else loss for p in range(state.num_players)]

    def render(self, state: GameState) -> str:
        lines = [
            f"phase={state.phase} current=p{state.current}:{COLORS[state.current]} last_roll={state.last_roll}",
            f"robber={state.robber_tile} longest_owner={self._owner_name(state.longest_road_owner)} "
            f"largest_army_owner={self._owner_name(state.largest_army_owner)}",
        ]
        tile_parts = []
        for tile_id in sorted(state.tiles):
            tile = state.tiles[tile_id]
            number = "-" if tile.number is None else str(tile.number)
            robber = "R" if tile.id == state.robber_tile else "-"
            tile_parts.append(f"{tile.id}:{tile.landscape}:{number}:{robber}")
        lines.append("tiles=" + ",".join(tile_parts))

        building_parts = []
        for crossing_id in sorted(state.settlements):
            player, kind = state.settlements[crossing_id]
            label = "C" if kind == "city" else "S"
            building_parts.append(f"{crossing_id}=p{player}{label}")
        lines.append("buildings=" + ",".join(building_parts))

        road_parts = [f"{edge_id}=p{state.roads[edge_id]}" for edge_id in sorted(state.roads)]
        lines.append("roads=" + ",".join(road_parts))

        for player in range(state.num_players):
            hand_count = self._hand_total(state.hands[player])
            dev_count = len(state.dev_hands[player])
            public_vp = self._public_victory_points(state, player)
            longest = self._longest_road_length(state, player)
            supply = (
                f"S{state.settlement_supply[player]}/"
                f"C{state.city_supply[player]}/"
                f"R{state.road_supply[player]}"
            )
            lines.append(
                f"p{player}:{COLORS[player]} public_vp={public_vp} hand_count={hand_count} "
                f"dev_count={dev_count} knights={state.played_knights[player]} "
                f"longest={longest} supply={supply}"
            )
        if state.terminal_winner is not None:
            lines.append(f"winner=p{state.terminal_winner}:{COLORS[state.terminal_winner]}")
        return "\n".join(lines)

    def action_to_name(self, action: str) -> str:
        if not isinstance(action, str):
            raise TypeError("This implementation uses canonical string actions.")
        return action

    def name_to_action(self, name: str) -> str:
        if not isinstance(name, str) or not name:
            raise ValueError("Action names must be non-empty strings.")
        return name

    def chance_outcomes(self, state: GameState) -> List[Tuple[str, float]]:
        if state.phase == "dice_chance":
            return [(f"chance:dice:{value}", weight / 36.0) for value, weight in sorted(DICE_WEIGHTS.items())]
        if state.phase == "dev_chance":
            total = len(state.dev_deck)
            counts = Counter(state.dev_deck)
            return [(f"chance:dev:{kind}", count / float(total)) for kind, count in sorted(counts.items())]
        if state.phase == "steal_chance":
            victim = state.pending_steal_victim
            if victim is None:
                return []
            total = self._hand_total(state.hands[victim])
            return [
                (f"chance:steal:{resource}", state.hands[victim][resource] / float(total))
                for resource in RESOURCES
                if state.hands[victim].get(resource, 0) > 0
            ]
        return []

    def information_state(self, state: GameState, player: int) -> str:
        if player < 0 or player >= state.num_players:
            raise ValueError("Unknown player")
        lines = [self.render(state)]
        lines.append(f"viewer=p{player}:{COLORS[player]}")
        lines.append("viewer_hand=" + self._format_multiset(state.hands[player]))
        own_dev = Counter(card.kind for card in state.dev_hands[player])
        lines.append("viewer_dev=" + self._format_multiset(own_dev, resource_order=("Ritter", "Fortschritt", "Siegpunkte")))
        for other in range(state.num_players):
            if other == player:
                continue
            lines.append(
                f"p{other}_hidden=hand_count:{self._hand_total(state.hands[other])},"
                f"dev_count:{len(state.dev_hands[other])}"
            )
        return "\n".join(lines)

    def _abstract_board(
        self, num_players: int
    ) -> Tuple[Dict[str, Tile], Dict[str, Crossing], Dict[str, Edge], Dict[str, Tuple[int, str]], Dict[str, int], Dict[int, str]]:
        # This board is not the missing official figure. It is a small stable
        # graph whose production adjacencies preserve the explicit examples.
        player_crossings = {
            0: ("xD", "xW2"),
            1: ("xB", "xB2"),
            2: ("xC", "xO2"),
            3: ("xA", "xR2"),
        }
        lettered = {0: "xD", 1: "xB", 2: "xC", 3: "xA"}

        crossing_ids = set()
        edge_specs = []
        for bases in player_crossings.values():
            for base in bases:
                crossing_ids.update({base, f"{base}_r1", f"{base}_r2", f"{base}_r3"})
                edge_specs.append((f"e_{base}_0", base, f"{base}_r1"))
                edge_specs.append((f"e_{base}_1", f"{base}_r1", f"{base}_r2"))
                edge_specs.append((f"e_{base}_2", f"{base}_r2", f"{base}_r3"))

        tile_specs = [
            ("t0", "Wald", 3, ("xD", "xD_r2")),
            ("t1", "Gebirge", 3, ("xB", "xC", "xB_r2")),
            ("t2", "Wald", 5, ("xB", "xB2_r2")),
            ("t3", "Huegelland", 11, ("xB", "xO2_r2")),
            ("t4", "Ackerland", 4, ("xC", "xC_r2")),
            ("t5", "Ackerland", 9, ("xC", "xO2_r2")),
            ("t6", "Gebirge", 8, ("xA", "xR2", "xW2")),
            ("t7", "Weideland", 10, ("xW2", "xW2_r2")),
            ("t8", "Wueste", None, ("xA_r2",)),
            ("t9", "Weideland", 6, ("xD_r2", "xB2")),
            ("t10", "Wald", 4, ("xB2", "xB2_r2")),
            ("t11", "Huegelland", 5, ("xO2", "xO2_r2")),
            ("t12", "Ackerland", 6, ("xR2_r2", "xC_r2")),
            ("t13", "Gebirge", 9, ("xA_r2",)),
            ("t14", "Weideland", 11, ("xD_r3",)),
            ("t15", "Wald", 10, ("xB_r3",)),
            ("t16", "Ackerland", 2, ("xC_r3",)),
            ("t17", "Gebirge", 12, ("xR2_r3",)),
            ("t18", "Huegelland", 6, ("xW2_r3",)),
        ]
        for _tile_id, _landscape, _number, tile_crossings in tile_specs:
            crossing_ids.update(tile_crossings)

        crossings = {crossing_id: Crossing(crossing_id) for crossing_id in sorted(crossing_ids)}
        edges = {edge_id: Edge(edge_id, a, b) for edge_id, a, b in edge_specs}
        tiles = {
            tile_id: Tile(tile_id, landscape, number, tuple(tile_crossings))
            for tile_id, landscape, number, tile_crossings in tile_specs
        }

        settlements: Dict[str, Tuple[int, str]] = {}
        roads: Dict[str, int] = {}
        for player in range(num_players):
            for base in player_crossings[player]:
                settlements[base] = (player, "settlement")
                roads[f"e_{base}_0"] = player
        return tiles, crossings, edges, settlements, roads, lettered

    def _playable_dev_actions(self, state: GameState, player: int) -> List[str]:
        if state.dev_card_played[player]:
            return []
        if any(card.kind == "Ritter" and not card.bought_turn for card in state.dev_hands[player]):
            return ["play:knight"]
        return []

    def _build_actions(self, state: GameState, player: int) -> List[str]:
        actions: List[str] = []
        if state.road_supply[player] > 0 and self._has_cards(state.hands[player], ROAD_COST):
            for edge_id in sorted(state.edges):
                if edge_id not in state.roads and self._can_build_road(state, player, edge_id):
                    actions.append(f"build:road:{edge_id}")
        if state.settlement_supply[player] > 0 and self._has_cards(state.hands[player], SETTLEMENT_COST):
            for crossing_id in sorted(state.crossings):
                if self._can_build_settlement(state, player, crossing_id):
                    actions.append(f"build:settlement:{crossing_id}")
        if state.city_supply[player] > 0 and self._has_cards(state.hands[player], CITY_COST):
            for crossing_id in sorted(state.settlements):
                owner, kind = state.settlements[crossing_id]
                if owner == player and kind == "settlement":
                    actions.append(f"build:city:{crossing_id}")
        if state.dev_deck and self._has_cards(state.hands[player], DEV_COST):
            actions.append("build:dev")
        return actions

    def _maritime_trade_actions(self, state: GameState, player: int) -> List[str]:
        actions: List[str] = []
        for give in RESOURCES:
            for ratio in self._available_maritime_ratios(state, player, give):
                if state.hands[player].get(give, 0) < ratio:
                    continue
                for get in RESOURCES:
                    if get != give:
                        actions.append(f"trade:maritime:{ratio}:{give}->{get}")
        return actions

    def _available_maritime_ratios(self, state: GameState, player: int, give: str) -> List[int]:
        ratios = {4}
        for crossing_id, (owner, _kind) in state.settlements.items():
            if owner != player:
                continue
            harbor = state.crossings[crossing_id].harbor
            if harbor == "3:1":
                ratios.add(3)
            if harbor == f"2:1:{give}":
                ratios.add(2)
        return sorted(ratios)

    def _can_build_road(self, state: GameState, player: int, edge_id: str) -> bool:
        if edge_id in state.roads:
            return False
        edge = state.edges[edge_id]
        for node in (edge.a, edge.b):
            occupant = state.settlements.get(node)
            if occupant is not None and occupant[0] != player:
                continue
            if occupant is not None and occupant[0] == player:
                return True
            for adjacent_edge in self._incident_edges(state, node):
                if state.roads.get(adjacent_edge.id) == player:
                    return True
        return False

    def _can_build_settlement(self, state: GameState, player: int, crossing_id: str) -> bool:
        if crossing_id in state.settlements:
            return False
        for neighbor in self._neighbor_crossings(state, crossing_id):
            if neighbor in state.settlements:
                return False
        return any(state.roads.get(edge.id) == player for edge in self._incident_edges(state, crossing_id))

    def _incident_edges(self, state: GameState, crossing_id: str) -> List[Edge]:
        return [edge for edge in state.edges.values() if edge.a == crossing_id or edge.b == crossing_id]

    def _neighbor_crossings(self, state: GameState, crossing_id: str) -> List[str]:
        neighbors = []
        for edge in self._incident_edges(state, crossing_id):
            neighbors.append(edge.b if edge.a == crossing_id else edge.a)
        return neighbors

    def _distribute_yield(self, state: GameState, roll: int) -> None:
        for tile in state.tiles.values():
            if tile.number != roll or tile.id == state.robber_tile:
                continue
            resource = LANDSCAPE_TO_RESOURCE.get(tile.landscape)
            if resource is None:
                continue
            for crossing_id in tile.crossings:
                occupant = state.settlements.get(crossing_id)
                if occupant is None:
                    continue
                player, kind = occupant
                amount = 2 if kind == "city" else 1
                state.hands[player][resource] += amount

    def _play_knight(self, state: GameState, return_phase: str) -> None:
        player = state.current
        for index, card in enumerate(state.dev_hands[player]):
            if card.kind == "Ritter" and not card.bought_turn:
                del state.dev_hands[player][index]
                break
        state.dev_card_played[player] = True
        state.played_knights[player] += 1
        self._update_largest_army(state, player)
        state.pending_robber_return_phase = return_phase
        state.pending_steal_victims = []
        state.pending_steal_victim = None
        state.phase = "robber_move"
        self._maybe_terminal(state)

    def _robber_victims(self, state: GameState, tile_id: str, active: int) -> List[int]:
        victims = set()
        for crossing_id in state.tiles[tile_id].crossings:
            occupant = state.settlements.get(crossing_id)
            if occupant is None:
                continue
            player, _kind = occupant
            if player != active and self._hand_total(state.hands[player]) > 0:
                victims.add(player)
        return sorted(victims)

    def _update_largest_army(self, state: GameState, player: int) -> None:
        if state.played_knights[player] < 3:
            return
        owner = state.largest_army_owner
        if owner is None or (owner != player and state.played_knights[player] > state.played_knights[owner]):
            state.largest_army_owner = player

    def _update_longest_road(self, state: GameState, actor: int) -> None:
        actor_length = self._longest_road_length(state, actor)
        owner = state.longest_road_owner
        if owner is None:
            if actor_length >= 5:
                state.longest_road_owner = actor
            return
        owner_length = self._longest_road_length(state, owner)
        if actor != owner and actor_length >= 5 and actor_length > owner_length:
            state.longest_road_owner = actor

    def _longest_road_length(self, state: GameState, player: int) -> int:
        owned_edges = {edge_id: state.edges[edge_id] for edge_id, owner in state.roads.items() if owner == player}
        if not owned_edges:
            return 0
        adjacency: Dict[str, List[Tuple[str, str]]] = {}
        for edge_id, edge in owned_edges.items():
            adjacency.setdefault(edge.a, []).append((edge_id, edge.b))
            adjacency.setdefault(edge.b, []).append((edge_id, edge.a))

        def blocked(crossing_id: str) -> bool:
            occupant = state.settlements.get(crossing_id)
            return occupant is not None and occupant[0] != player

        def extend(crossing_id: str, used: frozenset) -> int:
            if blocked(crossing_id):
                return 0
            best = 0
            for edge_id, neighbor in adjacency.get(crossing_id, []):
                if edge_id in used:
                    continue
                best = max(best, 1 + extend(neighbor, used | frozenset([edge_id])))
            return best

        best = 0
        for edge_id, edge in owned_edges.items():
            used = frozenset([edge_id])
            best = max(best, 1 + extend(edge.a, used), 1 + extend(edge.b, used))
        return best

    def _maybe_terminal(self, state: GameState) -> None:
        if state.terminal_winner is not None:
            return
        player = state.current
        if 0 <= player < state.num_players and self._victory_points(state, player) >= 10:
            self._make_terminal(state, player)

    def _make_terminal(self, state: GameState, winner: int) -> None:
        state.terminal_winner = winner
        state.phase = "terminal"
        state.pending_discards = []
        state.pending_steal_victims = []
        state.pending_steal_victim = None
        state.pending_dev_player = None

    def _end_turn(self, state: GameState) -> None:
        player = state.current
        for card in state.dev_hands[player]:
            card.bought_turn = False
        state.dev_card_played[player] = False
        state.pending_discards = []
        state.pending_steal_victims = []
        state.pending_steal_victim = None
        state.pending_dev_player = None
        state.current = (state.current + 1) % state.num_players
        state.phase = "pre_roll"
        state.last_roll = None

    def _public_victory_points(self, state: GameState, player: int) -> int:
        points = 0
        for owner, kind in state.settlements.values():
            if owner == player:
                points += 2 if kind == "city" else 1
        if state.longest_road_owner == player:
            points += 2
        if state.largest_army_owner == player:
            points += 2
        return points

    def _victory_points(self, state: GameState, player: int) -> int:
        hidden = sum(1 for card in state.dev_hands[player] if card.kind == "Siegpunkte")
        return self._public_victory_points(state, player) + hidden

    def _pay(self, state: GameState, player: int, cost: Dict[str, int]) -> None:
        self._subtract_cards(state.hands[player], cost)

    def _has_cards(self, hand: Dict[str, int], cost: Dict[str, int]) -> bool:
        return all(hand.get(resource, 0) >= amount for resource, amount in cost.items())

    def _subtract_cards(self, hand: Dict[str, int], cards: Dict[str, int]) -> None:
        if not self._has_cards(hand, cards):
            raise ValueError("Cannot remove cards that are not in hand")
        for resource, amount in cards.items():
            hand[resource] -= amount

    def _hand_total(self, hand: Dict[str, int]) -> int:
        return sum(hand.get(resource, 0) for resource in RESOURCES)

    def _discard_count(self, hand: Dict[str, int]) -> int:
        return self._hand_total(hand) // 2

    def _discard_actions(self, hand: Dict[str, int], count: int) -> List[str]:
        combos: List[Dict[str, int]] = []

        def rec(index: int, remaining: int, current: Dict[str, int]) -> None:
            if index == len(RESOURCES):
                if remaining == 0:
                    combos.append(dict(current))
                return
            resource = RESOURCES[index]
            max_take = min(hand.get(resource, 0), remaining)
            for amount in range(max_take + 1):
                if amount:
                    current[resource] = amount
                elif resource in current:
                    del current[resource]
                rec(index + 1, remaining - amount, current)
            current.pop(resource, None)

        rec(0, count, {})
        return ["discard:" + self._format_multiset(combo) for combo in combos]

    def _format_multiset(
        self,
        cards: Dict[str, int] | Counter,
        resource_order: Iterable[str] = RESOURCES,
    ) -> str:
        parts = []
        for resource in resource_order:
            amount = int(cards.get(resource, 0))
            if amount > 0:
                parts.append(f"{amount}{resource}")
        return "+".join(parts) if parts else "none"

    def _parse_multiset(self, text: str) -> Dict[str, int]:
        if text == "none":
            return {}
        cards = {resource: 0 for resource in RESOURCES}
        for part in text.split("+"):
            if not part:
                raise ValueError(f"Bad multiset part in {text!r}")
            digits = ""
            name = ""
            for char in part:
                if char.isdigit() and not name:
                    digits += char
                else:
                    name += char
            if not digits or name not in RESOURCES:
                raise ValueError(f"Bad card multiset part {part!r}")
            amount = int(digits)
            if amount <= 0:
                raise ValueError(f"Bad non-positive card count in {part!r}")
            cards[name] += amount
        return {resource: amount for resource, amount in cards.items() if amount > 0}

    def _owner_name(self, owner: Optional[int]) -> str:
        if owner is None:
            return "none"
        return f"p{owner}:{COLORS[owner]}"
