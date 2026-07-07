## Open questions / assumptions

- The page-1 board figure is not fully available in text, so the built-in board is a small documented example board, not the official full Catan layout.
- Free player-to-player negotiation is omitted; only finite bank/maritime trade actions are implemented.
- Development-card counts are not specified; default deck uses one card of each named type. `Fortschritt` effects are not implemented because their card text is absent.
- Resource bank depletion is ignored.
- Longest-road loss/tie behavior is underspecified; holder keeps it unless another player strictly exceeds them.
- A `max_turns` draw guard is included for rollouts, although the rule text gives no draw rule.

```python
from dataclasses import dataclass, field
from copy import deepcopy
from typing import Dict, List, Optional, Tuple, Set


TERMINAL = -1
CHANCE = -2

RESOURCES = ("Holz", "Lehm", "Wolle", "Getreide", "Erz")
DEV_CARDS = ("Ritter", "Fortschritt", "Siegpunkte")
PLAYER_COLORS = ("Weiss", "Blau", "Orange", "Rot")

ROAD_COST = {"Lehm": 1, "Holz": 1}
SETTLEMENT_COST = {"Lehm": 1, "Holz": 1, "Wolle": 1, "Getreide": 1}
CITY_COST = {"Erz": 3, "Getreide": 2}
DEV_COST = {"Erz": 1, "Wolle": 1, "Getreide": 1}

LANDSCAPE_RESOURCE = {
    "Wald": "Holz",
    "Ackerland": "Getreide",
    "Huegelland": "Lehm",
    "Weideland": "Wolle",
    "Gebirge": "Erz",
    "Wueste": None,
}

DICE_WEIGHTS = {2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1}


@dataclass(frozen=True)
class Tile:
    id: str
    landscape: str
    number: Optional[int]
    crossings: Tuple[str, ...]


@dataclass(frozen=True)
class Edge:
    id: str
    a: str
    b: str


@dataclass(frozen=True)
class BoardData:
    tiles: Dict[str, Tile]
    edges: Dict[str, Edge]
    harbors: Dict[str, Tuple[int, Optional[str]]] = field(default_factory=dict)
    initial_settlements: Dict[str, Tuple[int, str]] = field(default_factory=dict)
    initial_roads: Dict[str, int] = field(default_factory=dict)
    initial_hands: Tuple[Dict[str, int], ...] = field(default_factory=tuple)
    robber_tile: str = "t_wueste"


@dataclass
class GameState:
    num_players: int
    phase: str
    active_player: int
    turn_count: int
    hands: List[Dict[str, int]]
    dev_old: List[Dict[str, int]]
    dev_new: List[Dict[str, int]]
    dev_deck: Dict[str, int]
    roads: Dict[str, Optional[int]]
    settlements: Dict[str, Optional[Tuple[int, str]]]
    supplies: List[Dict[str, int]]
    robber_tile: str
    played_knights: List[int]
    longest_road_owner: Optional[int] = None
    longest_road_length: int = 0
    largest_army_owner: Optional[int] = None
    last_roll: Optional[int] = None
    dev_card_played_this_turn: bool = False
    discard_queue: List[int] = field(default_factory=list)
    pending_steal_victim: Optional[int] = None
    after_robber_phase: str = "main"
    terminal_winner: Optional[int] = None
    history: List[str] = field(default_factory=list)

    def clone(self):
        return deepcopy(self)


def _empty_resource_counts() -> Dict[str, int]:
    return {r: 0 for r in RESOURCES}


def _empty_dev_counts() -> Dict[str, int]:
    return {c: 0 for c in DEV_CARDS}


def _total(counts: Dict[str, int]) -> int:
    return sum(int(v) for v in counts.values())


def make_text_example_board(num_players: int = 4) -> BoardData:
    """Small text-derived example board, not the missing official page-1 layout."""
    if num_players not in (3, 4):
        raise ValueError("rule text only supports the beginner setup for 3 or 4 players")

    tiles = {
        "t3_wald": Tile("t3_wald", "Wald", 3, ("D", "B", "X1", "X3")),
        "t3_gebirge": Tile("t3_gebirge", "Gebirge", 3, ("B", "C", "X3", "X5")),
        "t_blau_huegelland": Tile("t_blau_huegelland", "Huegelland", None, ("B",)),
        "t_orange_acker_1": Tile("t_orange_acker_1", "Ackerland", None, ("C",)),
        "t_orange_acker_2": Tile("t_orange_acker_2", "Ackerland", None, ("C",)),
        "t8_gebirge": Tile("t8_gebirge", "Gebirge", 8, ("R1", "R2", "W8", "X2", "X7", "X8")),
        "t10_weideland": Tile("t10_weideland", "Weideland", 10, ("W8", "X2")),
        "t_wueste": Tile("t_wueste", "Wueste", None, ()),
    }

    edge_pairs = [
        ("e_D_X1", "D", "X1"), ("e_X1_Y1", "X1", "Y1"),
        ("e_W8_X2", "W8", "X2"), ("e_X2_Y2", "X2", "Y2"),
        ("e_B_X3", "B", "X3"), ("e_X3_Y3", "X3", "Y3"),
        ("e_B2_X4", "B2", "X4"), ("e_X4_Y4", "X4", "Y4"),
        ("e_C_X5", "C", "X5"), ("e_X5_Y5", "X5", "Y5"),
        ("e_C2_X6", "C2", "X6"), ("e_X6_Y6", "X6", "Y6"),
        ("e_R1_X7", "R1", "X7"), ("e_X7_Y7", "X7", "Y7"),
        ("e_R2_X8", "R2", "X8"), ("e_X8_Y8", "X8", "Y8"),
    ]
    edges = {eid: Edge(eid, a, b) for eid, a, b in edge_pairs}

    settlements = {
        "D": (0, "Siedlung"), "W8": (0, "Siedlung"),
        "B": (1, "Siedlung"), "B2": (1, "Siedlung"),
        "C": (2, "Siedlung"), "C2": (2, "Siedlung"),
    }
    roads = {
        "e_D_X1": 0, "e_W8_X2": 0,
        "e_B_X3": 1, "e_B2_X4": 1,
        "e_C_X5": 2, "e_C2_X6": 2,
    }
    if num_players == 4:
        settlements.update({"R1": (3, "Siedlung"), "R2": (3, "Siedlung")})
        roads.update({"e_R1_X7": 3, "e_R2_X8": 3})

    hands = [_empty_resource_counts() for _ in range(num_players)]
    if num_players > 1:
        hands[1].update({"Holz": 1, "Erz": 1, "Lehm": 1})
    if num_players > 2:
        hands[2].update({"Erz": 1, "Getreide": 2})

    return BoardData(
        tiles=tiles,
        edges=edges,
        harbors={},
        initial_settlements=settlements,
        initial_roads=roads,
        initial_hands=tuple(hands),
        robber_tile="t_wueste",
    )


class Game:
    def __init__(
        self,
        num_players: int = 4,
        board: Optional[BoardData] = None,
        dev_deck: Optional[Dict[str, int]] = None,
        max_turns: Optional[int] = 200,
    ):
        if num_players not in (3, 4):
            raise ValueError("the supplied text describes 3 or 4 players")
        self.num_players = num_players
        self.players = PLAYER_COLORS[:num_players]
        self.board = board if board is not None else make_text_example_board(num_players)
        self.max_turns = max_turns
        self.initial_dev_deck = {c: 0 for c in DEV_CARDS}
        if dev_deck is None:
            self.initial_dev_deck.update({"Ritter": 1, "Fortschritt": 1, "Siegpunkte": 1})
        else:
            for card, count in dev_deck.items():
                if card in self.initial_dev_deck:
                    self.initial_dev_deck[card] = int(count)

        crossings: Set[str] = set()
        for edge in self.board.edges.values():
            crossings.add(edge.a)
            crossings.add(edge.b)
        for tile in self.board.tiles.values():
            crossings.update(tile.crossings)
        crossings.update(self.board.initial_settlements.keys())
        crossings.update(self.board.harbors.keys())
        self.crossings = tuple(sorted(crossings))

        self.crossing_edges = {c: [] for c in self.crossings}
        self.crossing_neighbors = {c: set() for c in self.crossings}
        for eid, edge in self.board.edges.items():
            self.crossing_edges.setdefault(edge.a, []).append(eid)
            self.crossing_edges.setdefault(edge.b, []).append(eid)
            self.crossing_neighbors.setdefault(edge.a, set()).add(edge.b)
            self.crossing_neighbors.setdefault(edge.b, set()).add(edge.a)

        self.tiles_by_crossing = {c: [] for c in self.crossings}
        for tid, tile in self.board.tiles.items():
            for c in tile.crossings:
                self.tiles_by_crossing.setdefault(c, []).append(tid)

    def initial_state(self) -> GameState:
        hands = [_empty_resource_counts() for _ in range(self.num_players)]
        for p, counts in enumerate(self.board.initial_hands[: self.num_players]):
            for r in RESOURCES:
                hands[p][r] = int(counts.get(r, 0))

        roads = {eid: None for eid in self.board.edges}
        for eid, owner in self.board.initial_roads.items():
            if eid in roads and 0 <= owner < self.num_players:
                roads[eid] = owner

        settlements = {c: None for c in self.crossings}
        for c, occ in self.board.initial_settlements.items():
            owner, kind = occ
            if c in settlements and 0 <= owner < self.num_players:
                settlements[c] = (owner, kind)

        supplies = []
        for p in range(self.num_players):
            used_roads = sum(1 for owner in roads.values() if owner == p)
            used_settlements = sum(1 for occ in settlements.values() if occ == (p, "Siedlung"))
            used_cities = sum(1 for occ in settlements.values() if occ == (p, "Stadt"))
            supplies.append({
                "roads": 15 - used_roads,
                "settlements": 5 - used_settlements,
                "cities": 4 - used_cities,
            })

        state = GameState(
            num_players=self.num_players,
            phase="roll",
            active_player=0,
            turn_count=0,
            hands=hands,
            dev_old=[_empty_dev_counts() for _ in range(self.num_players)],
            dev_new=[_empty_dev_counts() for _ in range(self.num_players)],
            dev_deck=dict(self.initial_dev_deck),
            roads=roads,
            settlements=settlements,
            supplies=supplies,
            robber_tile=self.board.robber_tile,
            played_knights=[0 for _ in range(self.num_players)],
        )
        self._update_longest_road(state)
        return state

    def current_player(self, state: GameState) -> int:
        if self.is_terminal(state):
            return TERMINAL
        if state.phase in ("dice_chance", "dev_chance", "steal_chance"):
            return CHANCE
        if state.phase == "discard":
            return state.discard_queue[0]
        return state.active_player

    def legal_actions(self, state: GameState) -> List[str]:
        if self.is_terminal(state):
            return []
        if state.phase in ("dice_chance", "dev_chance", "steal_chance"):
            return [a for a, _ in self.chance_outcomes(state)]

        p = self.current_player(state)
        if state.phase == "roll":
            return ["roll"] + self._dev_play_actions(state, p)

        if state.phase == "discard":
            return self._discard_actions(state, p)

        if state.phase == "move_robber":
            return [
                "robber:move:" + tid
                for tid in sorted(self.board.tiles)
                if tid != state.robber_tile and LANDSCAPE_RESOURCE.get(self.board.tiles[tid].landscape) is not None
            ]

        if state.phase == "choose_steal":
            victims = self._robber_victims(state, state.active_player)
            if not victims:
                return ["robber:no_steal"]
            return ["robber:steal:p" + str(v) for v in victims]

        if state.phase == "main":
            actions = []
            actions.extend(self._dev_play_actions(state, state.active_player))
            actions.extend(self._trade_actions(state, state.active_player))
            actions.extend(self._build_actions(state, state.active_player))
            actions.append("end_turn")
            return actions

        return []

    def apply_action(self, state: GameState, action: str) -> GameState:
        name = self.action_to_name(action)
        legal = self.legal_actions(state)
        if name not in legal:
            raise ValueError("illegal action: " + name)

        s = state.clone()
        s.history.append(name)

        if name == "roll":
            s.phase = "dice_chance"

        elif name.startswith("chance:dice:"):
            self._apply_dice(s, int(name.rsplit(":", 1)[1]))

        elif name.startswith("discard:"):
            counts = self._parse_multiset(name.split(":", 1)[1])
            p = s.discard_queue.pop(0)
            self._subtract(s.hands[p], counts)
            if s.discard_queue:
                s.phase = "discard"
            else:
                s.phase = "move_robber"
                s.after_robber_phase = "main"

        elif name.startswith("robber:move:"):
            s.robber_tile = name.split(":", 2)[2]
            victims = self._robber_victims(s, s.active_player)
            if victims:
                s.phase = "choose_steal"
            else:
                self._finish_robber(s)

        elif name == "robber:no_steal":
            self._finish_robber(s)

        elif name.startswith("robber:steal:p"):
            s.pending_steal_victim = int(name.rsplit("p", 1)[1])
            if _total(s.hands[s.pending_steal_victim]) == 0:
                self._finish_robber(s)
            else:
                s.phase = "steal_chance"

        elif name.startswith("chance:steal:"):
            resource = name.rsplit(":", 1)[1]
            victim = s.pending_steal_victim
            if victim is not None:
                s.hands[victim][resource] -= 1
                s.hands[s.active_player][resource] += 1
            self._finish_robber(s)

        elif name.startswith("trade:maritime:"):
            _, _, ratio_text, exchange = name.split(":", 3)
            ratio = int(ratio_text)
            give, get = exchange.split("->")
            self._subtract(s.hands[s.active_player], {give: ratio})
            s.hands[s.active_player][get] += 1

        elif name.startswith("build:road:"):
            eid = name.split(":", 2)[2]
            self._subtract(s.hands[s.active_player], ROAD_COST)
            s.roads[eid] = s.active_player
            s.supplies[s.active_player]["roads"] -= 1
            self._update_longest_road(s)

        elif name.startswith("build:settlement:"):
            crossing = name.split(":", 2)[2]
            self._subtract(s.hands[s.active_player], SETTLEMENT_COST)
            s.settlements[crossing] = (s.active_player, "Siedlung")
            s.supplies[s.active_player]["settlements"] -= 1
            self._update_longest_road(s)

        elif name.startswith("build:city:"):
            crossing = name.split(":", 2)[2]
            self._subtract(s.hands[s.active_player], CITY_COST)
            s.settlements[crossing] = (s.active_player, "Stadt")
            s.supplies[s.active_player]["cities"] -= 1
            s.supplies[s.active_player]["settlements"] += 1

        elif name == "build:dev":
            self._subtract(s.hands[s.active_player], DEV_COST)
            s.phase = "dev_chance"

        elif name.startswith("chance:dev:"):
            card = name.rsplit(":", 1)[1]
            s.dev_deck[card] -= 1
            s.dev_new[s.active_player][card] += 1
            s.phase = "main"

        elif name == "play:knight":
            p = s.active_player
            s.dev_old[p]["Ritter"] -= 1
            s.played_knights[p] += 1
            s.dev_card_played_this_turn = True
            self._update_largest_army(s, p)
            s.after_robber_phase = s.phase
            s.phase = "move_robber"

        elif name == "end_turn":
            if self._victory_points(s, s.active_player, include_hidden=True) >= 10:
                self._set_winner(s, s.active_player)
            else:
                self._advance_turn(s)

        if not self.is_terminal(s):
            self._maybe_set_winner(s)
        return s

    def is_terminal(self, state: GameState) -> bool:
        return state.terminal_winner is not None or state.phase == "terminal"

    def returns(self, state: GameState) -> List[float]:
        if not self.is_terminal(state) or state.terminal_winner == -1:
            return [0.0 for _ in range(self.num_players)]
        winner = state.terminal_winner
        loser_value = -1.0 / (self.num_players - 1)
        return [1.0 if p == winner else loser_value for p in range(self.num_players)]

    def chance_outcomes(self, state: GameState) -> List[Tuple[str, float]]:
        if state.phase == "dice_chance":
            return [("chance:dice:" + str(v), w / 36.0) for v, w in sorted(DICE_WEIGHTS.items())]

        if state.phase == "dev_chance":
            total = sum(max(0, state.dev_deck.get(c, 0)) for c in DEV_CARDS)
            if total <= 0:
                return []
            return [
                ("chance:dev:" + c, state.dev_deck[c] / float(total))
                for c in DEV_CARDS
                if state.dev_deck.get(c, 0) > 0
            ]

        if state.phase == "steal_chance":
            victim = state.pending_steal_victim
            if victim is None:
                return []
            total = _total(state.hands[victim])
            if total <= 0:
                return []
            return [
                ("chance:steal:" + r, state.hands[victim][r] / float(total))
                for r in RESOURCES
                if state.hands[victim].get(r, 0) > 0
            ]

        return []

    def action_to_name(self, action: str) -> str:
        if not isinstance(action, str):
            raise TypeError("actions are represented by their canonical string names")
        return action

    def name_to_action(self, name: str) -> str:
        if not isinstance(name, str):
            raise TypeError("action names must be strings")
        return name

    def render(self, state: GameState) -> str:
        current = self.current_player(state)
        current_text = "terminal" if current == TERMINAL else "chance" if current == CHANCE else "p" + str(current)
        lines = [
            "phase={} active=p{} current={} turn={} last_roll={} robber={}".format(
                state.phase, state.active_player, current_text, state.turn_count, state.last_roll, state.robber_tile
            ),
            "longest_road_owner={} longest_road_length={} largest_army_owner={} dev_deck={}".format(
                self._player_label(state.longest_road_owner),
                state.longest_road_length,
                self._player_label(state.largest_army_owner),
                sum(state.dev_deck.values()),
            ),
        ]
        for p in range(self.num_players):
            supply = state.supplies[p]
            lines.append(
                "p{} {} public_vp={} hand_cards={} dev_cards={} knights={} supply=roads:{},settlements:{},cities:{}".format(
                    p,
                    self.players[p],
                    self._victory_points(state, p, include_hidden=False),
                    _total(state.hands[p]),
                    _total(state.dev_old[p]) + _total(state.dev_new[p]),
                    state.played_knights[p],
                    supply["roads"],
                    supply["settlements"],
                    supply["cities"],
                )
            )

        tile_parts = []
        for tid in sorted(self.board.tiles):
            tile = self.board.tiles[tid]
            robber = "R" if state.robber_tile == tid else "-"
            tile_parts.append("{}={}/{}:{}".format(tid, tile.landscape, tile.number, robber))
        lines.append("tiles " + " ".join(tile_parts))

        crossing_parts = []
        for c in self.crossings:
            occ = state.settlements.get(c)
            text = "empty" if occ is None else "p{}:{}".format(occ[0], occ[1])
            crossing_parts.append("{}={}".format(c, text))
        lines.append("crossings " + " ".join(crossing_parts))

        road_parts = []
        for eid in sorted(self.board.edges):
            owner = state.roads.get(eid)
            road_parts.append("{}={}".format(eid, "empty" if owner is None else "p" + str(owner)))
        lines.append("roads " + " ".join(road_parts))
        return "\n".join(lines)

    def information_state(self, state: GameState, player: int) -> str:
        if not (0 <= player < self.num_players):
            raise ValueError("unknown player")
        return (
            self.render(state)
            + "\nself=p{} hand={} dev_old={} dev_new={}".format(
                player,
                self._format_counts(state.hands[player], RESOURCES),
                self._format_counts(state.dev_old[player], DEV_CARDS),
                self._format_counts(state.dev_new[player], DEV_CARDS),
            )
        )

    def _apply_dice(self, state: GameState, roll: int) -> None:
        state.last_roll = roll
        if roll == 7:
            state.discard_queue = [p for p in range(self.num_players) if _total(state.hands[p]) > 7]
            state.after_robber_phase = "main"
            state.phase = "discard" if state.discard_queue else "move_robber"
            return

        for tile in self.board.tiles.values():
            if tile.number != roll or tile.id == state.robber_tile:
                continue
            resource = LANDSCAPE_RESOURCE.get(tile.landscape)
            if resource is None:
                continue
            for crossing in tile.crossings:
                occ = state.settlements.get(crossing)
                if occ is None:
                    continue
                owner, kind = occ
                state.hands[owner][resource] += 2 if kind == "Stadt" else 1
        state.phase = "main"

    def _build_actions(self, state: GameState, player: int) -> List[str]:
        actions = []
        if self._has_resources(state.hands[player], ROAD_COST) and state.supplies[player]["roads"] > 0:
            for eid in sorted(self.board.edges):
                if self._can_build_road(state, player, eid):
                    actions.append("build:road:" + eid)

        if self._has_resources(state.hands[player], SETTLEMENT_COST) and state.supplies[player]["settlements"] > 0:
            for crossing in self.crossings:
                if self._can_build_settlement(state, player, crossing):
                    actions.append("build:settlement:" + crossing)

        if self._has_resources(state.hands[player], CITY_COST) and state.supplies[player]["cities"] > 0:
            for crossing in self.crossings:
                if self._can_build_city(state, player, crossing):
                    actions.append("build:city:" + crossing)

        if self._has_resources(state.hands[player], DEV_COST) and sum(state.dev_deck.values()) > 0:
            actions.append("build:dev")
        return actions

    def _trade_actions(self, state: GameState, player: int) -> List[str]:
        hand = state.hands[player]
        ratios_by_resource = {r: {4} for r in RESOURCES}

        for crossing, harbor in self.board.harbors.items():
            occ = state.settlements.get(crossing)
            if occ is None or occ[0] != player:
                continue
            ratio, harbor_resource = harbor
            if ratio == 3 and harbor_resource is None:
                for r in RESOURCES:
                    ratios_by_resource[r].add(3)
            elif ratio == 2 and harbor_resource in RESOURCES:
                ratios_by_resource[harbor_resource].add(2)

        actions = set()
        for give in RESOURCES:
            for ratio in ratios_by_resource[give]:
                if hand.get(give, 0) >= ratio:
                    for get in RESOURCES:
                        if get != give:
                            actions.add("trade:maritime:{}:{}->{}".format(ratio, give, get))
        return sorted(actions)

    def _dev_play_actions(self, state: GameState, player: int) -> List[str]:
        if state.dev_card_played_this_turn:
            return []
        actions = []
        if state.dev_old[player].get("Ritter", 0) > 0:
            actions.append("play:knight")
        # Fortschritt card text is not included in the supplied rule text, so no effect is invented.
        return actions

    def _discard_actions(self, state: GameState, player: int) -> List[str]:
        needed = _total(state.hands[player]) // 2
        combos = []
        self._generate_discards(state.hands[player], 0, needed, {}, combos)
        return ["discard:" + self._format_multiset(c) for c in combos]

    def _generate_discards(self, hand, idx, remaining, current, out):
        if idx == len(RESOURCES):
            if remaining == 0:
                out.append({r: current.get(r, 0) for r in RESOURCES})
            return
        resource = RESOURCES[idx]
        for n in range(min(hand.get(resource, 0), remaining) + 1):
            current[resource] = n
            self._generate_discards(hand, idx + 1, remaining - n, current, out)
        current[resource] = 0

    def _can_build_road(self, state: GameState, player: int, eid: str) -> bool:
        if state.roads.get(eid) is not None:
            return False
        edge = self.board.edges[eid]
        return self._road_attach_ok(state, player, eid, edge.a) or self._road_attach_ok(state, player, eid, edge.b)

    def _road_attach_ok(self, state: GameState, player: int, eid: str, crossing: str) -> bool:
        occ = state.settlements.get(crossing)
        if occ is not None and occ[0] != player:
            return False
        if occ is not None and occ[0] == player:
            return True
        return any(other != eid and state.roads.get(other) == player for other in self.crossing_edges.get(crossing, []))

    def _can_build_settlement(self, state: GameState, player: int, crossing: str) -> bool:
        if state.settlements.get(crossing) is not None:
            return False
        if not any(state.roads.get(eid) == player for eid in self.crossing_edges.get(crossing, [])):
            return False
        for neighbor in self.crossing_neighbors.get(crossing, set()):
            if state.settlements.get(neighbor) is not None:
                return False
        return True

    def _can_build_city(self, state: GameState, player: int, crossing: str) -> bool:
        return state.settlements.get(crossing) == (player, "Siedlung")

    def _robber_victims(self, state: GameState, player: int) -> List[int]:
        tile = self.board.tiles[state.robber_tile]
        victims = set()
        for crossing in tile.crossings:
            occ = state.settlements.get(crossing)
            if occ is not None and occ[0] != player and _total(state.hands[occ[0]]) > 0:
                victims.add(occ[0])
        return sorted(victims)

    def _finish_robber(self, state: GameState) -> None:
        state.pending_steal_victim = None
        state.phase = state.after_robber_phase or "main"
        state.after_robber_phase = "main"

    def _advance_turn(self, state: GameState) -> None:
        for p in range(self.num_players):
            for card in DEV_CARDS:
                state.dev_old[p][card] += state.dev_new[p][card]
                state.dev_new[p][card] = 0
        state.dev_card_played_this_turn = False
        state.last_roll = None
        state.turn_count += 1
        if self.max_turns is not None and state.turn_count >= self.max_turns:
            state.terminal_winner = -1
            state.phase = "terminal"
            return
        state.active_player = (state.active_player + 1) % self.num_players
        state.phase = "roll"

    def _has_resources(self, hand: Dict[str, int], cost: Dict[str, int]) -> bool:
        return all(hand.get(r, 0) >= n for r, n in cost.items())

    def _subtract(self, hand: Dict[str, int], cost: Dict[str, int]) -> None:
        for r, n in cost.items():
            hand[r] -= n

    def _update_largest_army(self, state: GameState, player: int) -> None:
        owner = state.largest_army_owner
        if owner is None:
            if state.played_knights[player] >= 3:
                state.largest_army_owner = player
        elif player != owner and state.played_knights[player] > state.played_knights[owner]:
            state.largest_army_owner = player

    def _update_longest_road(self, state: GameState) -> None:
        lengths = [self._longest_road_for_player(state, p) for p in range(self.num_players)]
        owner = state.longest_road_owner
        if owner is None:
            best = max(lengths) if lengths else 0
            if best >= 5 and lengths.count(best) == 1:
                state.longest_road_owner = lengths.index(best)
                state.longest_road_length = best
            else:
                state.longest_road_length = best
            return

        state.longest_road_length = lengths[owner]
        for p, length in enumerate(lengths):
            if p != owner and length >= 5 and length > lengths[owner]:
                state.longest_road_owner = p
                state.longest_road_length = length
                return

    def _longest_road_for_player(self, state: GameState, player: int) -> int:
        owned = [eid for eid, owner in state.roads.items() if owner == player]
        if not owned:
            return 0

        adjacency = {eid: set() for eid in owned}
        for crossing, eids in self.crossing_edges.items():
            occ = state.settlements.get(crossing)
            if occ is not None and occ[0] != player:
                continue
            player_edges = [eid for eid in eids if state.roads.get(eid) == player]
            for a in player_edges:
                for b in player_edges:
                    if a != b:
                        adjacency[a].add(b)

        def dfs(eid: str, visited: Set[str]) -> int:
            best = 1
            for nxt in adjacency[eid]:
                if nxt not in visited:
                    best = max(best, 1 + dfs(nxt, visited | {nxt}))
            return best

        return max(dfs(eid, {eid}) for eid in owned)

    def _victory_points(self, state: GameState, player: int, include_hidden: bool) -> int:
        vp = 0
        for occ in state.settlements.values():
            if occ is None or occ[0] != player:
                continue
            vp += 2 if occ[1] == "Stadt" else 1
        if state.longest_road_owner == player:
            vp += 2
        if state.largest_army_owner == player:
            vp += 2
        if include_hidden:
            vp += state.dev_old[player].get("Siegpunkte", 0)
            vp += state.dev_new[player].get("Siegpunkte", 0)
        return vp

    def _maybe_set_winner(self, state: GameState) -> None:
        if self._victory_points(state, state.active_player, include_hidden=True) >= 10:
            self._set_winner(state, state.active_player)

    def _set_winner(self, state: GameState, player: int) -> None:
        state.terminal_winner = player
        state.phase = "terminal"

    def _format_multiset(self, counts: Dict[str, int]) -> str:
        parts = []
        for r in RESOURCES:
            n = counts.get(r, 0)
            if n:
                parts.append(str(n) + r)
        return "+".join(parts) if parts else "none"

    def _parse_multiset(self, text: str) -> Dict[str, int]:
        counts = _empty_resource_counts()
        if text == "none":
            return counts
        for part in text.split("+"):
            i = 0
            while i < len(part) and part[i].isdigit():
                i += 1
            amount = int(part[:i])
            resource = part[i:]
            if resource not in RESOURCES:
                raise ValueError("unknown resource in multiset: " + resource)
            counts[resource] += amount
        return counts

    def _format_counts(self, counts: Dict[str, int], order) -> str:
        parts = [str(counts.get(k, 0)) + k for k in order if counts.get(k, 0)]
        return "+".join(parts) if parts else "none"

    def _player_label(self, player: Optional[int]) -> str:
        return "none" if player is None else "p" + str(player)
```