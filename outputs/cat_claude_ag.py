"""CATAN (Siedler von Catan base game) — BoardBench OpenSpiel-style module."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any

TERMINAL = -1
CHANCE = -2

NUM_PLAYERS = 4
RES = ("B", "G", "L", "O", "W")
RES_NAME = {r: n for r, n in zip(RES, ("brick", "grain", "lumber", "ore", "wool"))}
NAME_RES = {v: k for k, v in RES_NAME.items()}
BUILD_ROAD = Counter(B=1, L=1)
BUILD_SETTLE = Counter(B=1, G=1, L=1, W=1)
BUILD_CITY = Counter(G=2, O=3)
BUY_DEV = Counter(G=1, O=1, W=1)
VP_WIN = 10
ROLL_PROBS = {2: 1/36, 3: 2/36, 4: 3/36, 5: 4/36, 6: 5/36, 7: 6/36,
              8: 5/36, 9: 4/36, 10: 3/36, 11: 2/36, 12: 1/36}

HEXES = [('G', 9), ('L', 8), ('G', 12), ('B', 5), ('L', 11), ('O', 10), ('O', 3), ('B', 6), ('G', 6), ('D', -1), ('W', 2), ('G', 4), ('W', 4), ('W', 11), ('L', 3), ('L', 9), ('W', 5), ('B', 10), ('O', 8)]
V_HEX = [[0], [0], [1], [0, 1], [0, 2], [2], [3], [1, 3], [0, 1, 4], [0, 2, 4], [2, 5], [5], [3], [1, 3, 6], [1, 4, 6], [2, 4, 7], [2, 5, 7], [5], [3, 8], [3, 6, 8], [4, 6, 9], [4, 7, 9], [5, 7, 10], [5, 10], [8], [6, 8, 11], [6, 9, 11], [7, 9, 12], [7, 10, 12], [10], [8, 13], [8, 11, 13], [9, 11, 14], [9, 12, 14], [10, 12, 15], [10, 15], [13], [11, 13, 16], [11, 14, 16], [12, 14, 17], [12, 15, 17], [15], [13], [13, 16], [14, 16, 18], [14, 17, 18], [15, 17], [15], [16], [16, 18], [17, 18], [17], [18], [18]]
V_EDGE = [[44, 52], [52, 60], [27, 35], [35, 43, 44], [54, 60, 61], [61, 67], [10, 18], [18, 26, 27], [37, 43, 45], [45, 53, 54], [63, 67, 68], [68, 71], [9, 10], [20, 26, 28], [28, 36, 37], [47, 53, 55], [55, 62, 63], [70, 71], [4, 9, 11], [11, 19, 20], [30, 36, 38], [38, 46, 47], [57, 62, 64], [64, 69, 70], [3, 4], [13, 19, 21], [21, 29, 30], [40, 46, 48], [48, 56, 57], [66, 69], [1, 3, 5], [5, 12, 13], [23, 29, 31], [31, 39, 40], [50, 56, 58], [58, 65, 66], [0, 1], [7, 12, 14], [14, 22, 23], [33, 39, 41], [41, 49, 50], [59, 65], [0, 2], [2, 6, 7], [16, 22, 24], [24, 32, 33], [42, 49, 51], [51, 59], [6, 8], [8, 15, 16], [25, 32, 34], [34, 42], [15, 17], [17, 25]]
V_VERT = [[1, 3], [0, 4], [3, 7], [0, 2, 8], [1, 5, 9], [4, 10], [7, 12], [2, 6, 13], [3, 9, 14], [4, 8, 15], [5, 11, 16], [10, 17], [6, 18], [7, 14, 19], [8, 13, 20], [9, 16, 21], [10, 15, 22], [11, 23], [12, 19, 24], [13, 18, 25], [14, 21, 26], [15, 20, 27], [16, 23, 28], [17, 22, 29], [18, 30], [19, 26, 31], [20, 25, 32], [21, 28, 33], [22, 27, 34], [23, 35], [24, 31, 36], [25, 30, 37], [26, 33, 38], [27, 32, 39], [28, 35, 40], [29, 34, 41], [30, 42], [31, 38, 43], [32, 37, 44], [33, 40, 45], [34, 39, 46], [35, 47], [36, 43], [37, 42, 48], [38, 45, 49], [39, 44, 50], [40, 47, 51], [41, 46], [43, 49], [44, 48, 52], [45, 51, 53], [46, 50], [49, 53], [50, 52]]
E_VERT = [[36, 42], [30, 36], [42, 43], [24, 30], [18, 24], [30, 31], [43, 48], [37, 43], [48, 49], [12, 18], [6, 12], [18, 19], [31, 37], [25, 31], [37, 38], [49, 52], [44, 49], [52, 53], [6, 7], [19, 25], [13, 19], [25, 26], [38, 44], [32, 38], [44, 45], [50, 53], [7, 13], [2, 7], [13, 14], [26, 32], [20, 26], [32, 33], [45, 50], [39, 45], [50, 51], [2, 3], [14, 20], [8, 14], [20, 21], [33, 39], [27, 33], [39, 40], [46, 51], [3, 8], [0, 3], [8, 9], [21, 27], [15, 21], [27, 28], [40, 46], [34, 40], [46, 47], [0, 1], [9, 15], [4, 9], [15, 16], [28, 34], [22, 28], [34, 35], [41, 47], [1, 4], [4, 5], [16, 22], [10, 16], [22, 23], [35, 41], [29, 35], [5, 10], [10, 11], [23, 29], [17, 23], [11, 17]]
HARBORS = [(29, 35, 'G'), (46, 51, 'O'), (52, 53, '3'), (43, 48, 'W'), (24, 30, '3'), (6, 12, '3'), (0, 3, 'B'), (4, 5, 'L'), (11, 17, '3')]
SETUP = [(0, 0, 44), (1, 2, 27), (2, 4, 54), (3, 6, 10), (3, 20, 30), (2, 15, 47), (1, 13, 20), (0, 8, 37)]

DEV_DECK = (
    ["knight"] * 14 + ["monopoly"] * 2 + ["road"] * 2 + ["year"] * 2 + ["vp"] * 5
)


def _c(**kw):
    return Counter(kw)


def _hand_total(h: Counter) -> int:
    return sum(h.values())


def _can_pay(h: Counter, cost: Counter) -> bool:
    return all(h.get(r, 0) >= cost.get(r, 0) for r in cost)


def _pay(h: Counter, cost: Counter) -> Counter:
    out = h.copy()
    for r, n in cost.items():
        out[r] -= n
        if out[r] == 0:
            del out[r]
    return out


def _add(h: Counter, gains: Counter) -> Counter:
    out = h.copy()
    for r, n in gains.items():
        out[r] += n
    return out


def _discard_auto(h: Counter) -> Counter:
    total = _hand_total(h)
    if total <= 7:
        return h.copy()
    drop = total // 2
    out = h.copy()
    order = sorted(RES, key=lambda r: (-out.get(r, 0), r))
    while drop > 0:
        for r in order:
            if out.get(r, 0) > 0 and drop > 0:
                out[r] -= 1
                if out[r] == 0:
                    del out[r]
                drop -= 1
                if drop == 0:
                    break
    return out


def _hex_produces(hi: int, roll: int, robber: int) -> str | None:
    res, num = HEXES[hi]
    if res == "D" or hi == robber or num != roll:
        return None
    return res


def _harbor_rates(state, player: int) -> list[tuple[int, str | None]]:
    rates = [(4, None)]
    seen = set()
    for v in range(54):
        occ = state.vertices[v]
        if occ is None or occ[0] != player:
            continue
        for e in V_EDGE[v]:
            a, b = E_VERT[e]
            other = b if a == v else a
            for va, vb, kind in HARBORS:
                if {v, other} == {va, vb}:
                    key = (va, vb)
                    if key in seen:
                        continue
                    seen.add(key)
                    if kind == "3":
                        rates.append((3, None))
                    else:
                        rates.append((2, kind))
    best: dict[tuple[int, str | None], tuple[int, str | None]] = {}
    for rate in rates:
        if rate[0] == 4:
            best[(4, None)] = rate
        elif rate[1] is None:
            if (3, None) not in best or best[(3, None)][0] > 3:
                best[(3, None)] = rate
        else:
            best[(2, rate[1])] = rate
    out = list(best.values())
    out.sort(key=lambda x: (x[0], x[1] or ""))
    return out


def _longest_road(state, player: int) -> int:
    edges = [e for e, o in enumerate(state.edges) if o == player]
    if not edges:
        return 0
    adj: dict[int, list[int]] = {}
    for e in edges:
        a, b = E_VERT[e]
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    blocked = {v for v, occ in enumerate(state.vertices) if occ is not None and occ[0] != player}

    best = 0
    for start in adj:
        stack = [(start, None, 0, {start})]
        while stack:
            node, prev, length, visited = stack.pop()
            if node in blocked and node != start:
                continue
            best = max(best, length)
            for nxt in adj.get(node, []):
                if nxt == prev:
                    continue
                if nxt in blocked:
                    continue
                if nxt in visited:
                    continue
                stack.append((nxt, node, length + 1, visited | {nxt}))
    return best


def _update_longest_road(state):
    scores = [( _longest_road(state, p), p) for p in range(NUM_PLAYERS)]
    best_len = max(s for s, _ in scores)
    if best_len < 5:
        return None
    leaders = [p for s, p in scores if s == best_len]
    if len(leaders) != 1:
        return state.longest_road if state.longest_road in leaders else None
    return leaders[0]


def _update_largest_army(state):
    best = max(state.dev_played)
    if best < 3:
        return None
    leaders = [p for p, n in enumerate(state.dev_played) if n == best]
    if len(leaders) != 1:
        return state.largest_army if state.largest_army in leaders else None
    return leaders[0]


def _public_vp(state, player: int) -> int:
    vp = 0
    for occ in state.vertices:
        if occ is not None and occ[0] == player:
            vp += 2 if occ[1] == "C" else 1
    if state.longest_road == player:
        vp += 2
    if state.largest_army == player:
        vp += 2
    return vp


def _total_vp(state, player: int) -> int:
    return _public_vp(state, player) + state.vp_dev[player]


def _check_winner(state, player: int):
    if _total_vp(state, player) >= VP_WIN:
        return player
    return None


@dataclass(frozen=True)
class GameState:
    phase: str
    setup_step: int
    current_player: int
    hands: tuple[Counter, ...]
    vertices: tuple[tuple[int | None, str] | None, ...]
    edges: tuple[int | None, ...]
    roads_left: tuple[int, ...]
    settles_left: tuple[int, ...]
    cities_left: tuple[int, ...]
    dev_deck: tuple[str, ...]
    dev_hands: tuple[tuple[str, ...], ...]
    dev_played: tuple[int, ...]
    vp_dev: tuple[int, ...]
    longest_road: int | None
    largest_army: int | None
    robber_hex: int
    last_roll: int | None
    bought_dev_this_turn: bool
    winner: int | None
    robber_stage: str


class Game:
    def __init__(self, num_players: int = NUM_PLAYERS):
        if num_players != 4:
            raise ValueError("beginner board supports 4 players")
        self.num_players = num_players

    def initial_state(self) -> GameState:
        desert = next(i for i, (r, n) in enumerate(HEXES) if r == "D")
        return GameState(
            phase="setup",
            setup_step=0,
            current_player=0,
            hands=tuple(Counter() for _ in range(NUM_PLAYERS)),
            vertices=tuple(None for _ in range(54)),
            edges=tuple(None for _ in range(72)),
            roads_left=tuple(15 for _ in range(NUM_PLAYERS)),
            settles_left=tuple(5 for _ in range(NUM_PLAYERS)),
            cities_left=tuple(4 for _ in range(NUM_PLAYERS)),
            dev_deck=DEV_DECK,
            dev_hands=tuple(() for _ in range(NUM_PLAYERS)),
            dev_played=tuple(0 for _ in range(NUM_PLAYERS)),
            vp_dev=tuple(0 for _ in range(NUM_PLAYERS)),
            longest_road=None,
            largest_army=None,
            robber_hex=desert,
            last_roll=None,
            bought_dev_this_turn=False,
            winner=None,
            robber_stage="",
        )

    def current_player(self, state: GameState) -> int:
        if state.winner is not None or state.phase == "terminal":
            return TERMINAL
        if state.phase == "roll":
            return CHANCE
        return state.current_player

    def is_terminal(self, state: GameState) -> bool:
        return state.winner is not None or state.phase == "terminal"

    def returns(self, state: GameState) -> list[float]:
        if state.winner is None:
            return [0.0] * NUM_PLAYERS
        out = [0.0] * NUM_PLAYERS
        out[state.winner] = 1.0
        return out

    def chance_outcomes(self, state: GameState) -> list[tuple[Any, float]]:
        if state.phase != "roll":
            return []
        return [(("roll", s), ROLL_PROBS[s]) for s in range(2, 13)]

    def _distance_ok(self, state: GameState, v: int) -> bool:
        if state.vertices[v] is not None:
            return False
        for n in V_VERT[v]:
            if state.vertices[n] is not None:
                return False
        return True

    def _can_build_road(self, state: GameState, player: int, e: int) -> bool:
        if state.edges[e] is not None or state.roads_left[player] <= 0:
            return False
        if not _can_pay(state.hands[player], BUILD_ROAD):
            return False
        a, b = E_VERT[e]
        if state.vertices[a] is not None and state.vertices[a][0] == player:
            return True
        if state.vertices[b] is not None and state.vertices[b][0] == player:
            return True
        for end in (a, b):
            for ne in V_EDGE[end]:
                if ne == e:
                    continue
                if state.edges[ne] == player:
                    if state.vertices[end] is None or state.vertices[end][0] == player:
                        return True
        return False

    def _can_build_settle(self, state: GameState, player: int, v: int) -> bool:
        if not self._distance_ok(state, v) or state.settles_left[player] <= 0:
            return False
        if not _can_pay(state.hands[player], BUILD_SETTLE):
            return False
        connected = False
        for e in V_EDGE[v]:
            if state.edges[e] == player:
                connected = True
                break
        return connected

    def _can_build_city(self, state: GameState, player: int, v: int) -> bool:
        cur = state.vertices[v]
        if cur is None or cur[0] != player or cur[1] != "S":
            return False
        if state.cities_left[player] <= 0:
            return False
        return _can_pay(state.hands[player], BUILD_CITY)

    def _players_on_hex(self, state: GameState, hi: int) -> list[int]:
        ps = set()
        for v in range(54):
            occ = state.vertices[v]
            if occ is None:
                continue
            for h in V_HEX[v]:
                if h == hi:
                    ps.add(occ[0])
                    break
        return sorted(ps)

    def legal_actions(self, state: GameState) -> list[Any]:
        if self.is_terminal(state):
            return []
        if state.phase == "setup":
            if state.setup_step >= len(SETUP):
                return []
            return [("setup", state.setup_step)]
        if state.phase == "roll":
            return [("roll", s) for s in range(2, 13)]
        if state.phase == "robber":
            p = state.current_player
            if state.robber_stage == "move":
                acts = []
                for hi, (res, _n) in enumerate(HEXES):
                    if hi != state.robber_hex:
                        acts.append(("move_robber", hi))
                return acts
            victims = self._players_on_hex(state, state.robber_hex)
            victims = [x for x in victims if x != p and _hand_total(state.hands[x]) > 0]
            if not victims:
                return [("steal", None)]
            return [("steal", v) for v in victims]
        if state.phase != "main":
            return []
        p = state.current_player
        acts: list[Any] = [("pass",)]
        hand = state.hands[p]
        seen_bank: set[tuple[Any, ...]] = set()
        for r in RES:
            if hand.get(r, 0) >= 4:
                for g in RES:
                    act = ("bank", 4, None, r, g)
                    if act not in seen_bank:
                        seen_bank.add(act)
                        acts.append(act)
        for rate, spec in _harbor_rates(state, p):
            if rate == 4:
                continue
            if spec is None:
                for r in RES:
                    if hand.get(r, 0) >= 3:
                        for g in RES:
                            act = ("bank", 3, None, r, g)
                            if act not in seen_bank:
                                seen_bank.add(act)
                                acts.append(act)
            else:
                if hand.get(spec, 0) >= 2:
                    for g in RES:
                        act = ("bank", 2, spec, spec, g)
                        if act not in seen_bank:
                            seen_bank.add(act)
                            acts.append(act)
        # agentic variant: simplified 1:1 player trades (active player proposes)
        for partner in range(NUM_PLAYERS):
            if partner == p:
                continue
            ph = state.hands[partner]
            for give in RES:
                if hand.get(give, 0) < 1:
                    continue
                for take in RES:
                    if give != take and ph.get(take, 0) >= 1:
                        acts.append(("ptrade", partner, give, take))
        for e in range(72):
            if self._can_build_road(state, p, e):
                acts.append(("build", "road", e))
        for v in range(54):
            if self._can_build_settle(state, p, v):
                acts.append(("build", "settlement", v))
            if self._can_build_city(state, p, v):
                acts.append(("build", "city", v))
        if _can_pay(hand, BUY_DEV) and state.dev_deck:
            acts.append(("buy_dev",))
        if not state.bought_dev_this_turn:
            for i, card in enumerate(state.dev_hands[p]):
                if card == "knight":
                    acts.append(("play", i, "knight"))
                elif card == "monopoly":
                    for r in RES:
                        acts.append(("play", i, "monopoly", r))
                elif card in ("road", "year"):
                    acts.append(("play", i, card))
        return acts

    def apply_action(self, state: GameState, action: Any) -> GameState:
        if self.is_terminal(state):
            raise ValueError("terminal state")
        kind = action[0]
        if kind == "setup":
            step = action[1]
            if step != state.setup_step:
                raise ValueError("bad setup step")
            player, v, e = SETUP[step]
            verts = list(state.vertices)
            edges = list(state.edges)
            roads = list(state.roads_left)
            settles = list(state.settles_left)
            if verts[v] is not None or edges[e] is not None:
                raise ValueError("setup occupied")
            verts[v] = (player, "S")
            edges[e] = player
            roads[player] -= 1
            settles[player] -= 1
            ns = state.setup_step + 1
            hands = state.hands
            phase = "setup"
            current = 0
            if ns >= len(SETUP):
                new_hands = []
                for pl in range(NUM_PLAYERS):
                    h = Counter()
                    star_v = SETUP[4 + (3 - pl)][1]
                    for hi in V_HEX[star_v]:
                        res, _ = HEXES[hi]
                        if res != "D":
                            h[res] += 1
                    new_hands.append(h)
                hands = tuple(new_hands)
                phase = "roll"
                current = 0
            return GameState(
                phase=phase,
                setup_step=ns,
                current_player=current,
                hands=hands,
                vertices=tuple(verts),
                edges=tuple(edges),
                roads_left=tuple(roads),
                settles_left=tuple(settles),
                cities_left=state.cities_left,
                dev_deck=state.dev_deck,
                dev_hands=state.dev_hands,
                dev_played=state.dev_played,
                vp_dev=state.vp_dev,
                longest_road=state.longest_road,
                largest_army=state.largest_army,
                robber_hex=state.robber_hex,
                last_roll=state.last_roll,
                bought_dev_this_turn=False,
                winner=None,
                robber_stage="",
            )
        if kind == "roll":
            roll = action[1]
            p = state.current_player
            hands = list(state.hands)
            if roll == 7:
                hands = [_discard_auto(Counter(h)) for h in hands]
                return GameState(
                    **{**state.__dict__,
                       "hands": tuple(hands),
                       "phase": "robber",
                       "robber_stage": "move",
                       "last_roll": roll,
                       "bought_dev_this_turn": False,
                    }
                )
            for pl in range(NUM_PLAYERS):
                h = Counter(hands[pl])
                for v in range(54):
                    occ = state.vertices[v]
                    if occ is None or occ[0] != pl:
                        continue
                    mult = 2 if occ[1] == "C" else 1
                    for hi in V_HEX[v]:
                        res = _hex_produces(hi, roll, state.robber_hex)
                        if res:
                            h[res] += mult
                hands[pl] = h
            return GameState(
                **{**state.__dict__,
                   "hands": tuple(hands),
                   "phase": "main",
                   "last_roll": roll,
                   "bought_dev_this_turn": False,
                   "robber_stage": "",
                }
            )
        if kind == "move_robber":
            hi = action[1]
            return GameState(
                **{**state.__dict__,
                   "robber_hex": hi,
                   "robber_stage": "steal",
                }
            )
        if kind == "steal":
            p = state.current_player
            hands = list(state.hands)
            victim = action[1]
            if victim is not None:
                vh = Counter(hands[victim])
                if vh:
                    take = sorted(vh.items(), key=lambda x: (x[0]))[0][0]
                    vh[take] -= 1
                    if vh[take] == 0:
                        del vh[take]
                    hands[victim] = vh
                    hands[p] = _add(Counter(hands[p]), Counter({take: 1}))
            return GameState(
                **{**state.__dict__,
                   "hands": tuple(hands),
                   "phase": "main",
                   "robber_stage": "",
                }
            )
        if kind == "bank":
            _, rate, spec, give, get = action
            p = state.current_player
            h = Counter(state.hands[p])
            if rate == 4:
                h[give] -= 4
            elif rate == 3:
                h[give] -= 3
            else:
                h[give] -= 2
            if h[give] == 0:
                del h[give]
            h[get] += 1
            hands = list(state.hands)
            hands[p] = h
            return GameState(**{**state.__dict__, "hands": tuple(hands)})
        if kind == "ptrade":
            _, partner, give, take = action
            p = state.current_player
            hands = [Counter(h) for h in state.hands]
            if partner == p or hands[p].get(give, 0) < 1 or hands[partner].get(take, 0) < 1:
                raise ValueError("illegal ptrade")
            hands[p][give] -= 1
            if hands[p][give] == 0:
                del hands[p][give]
            hands[p][take] += 1
            hands[partner][take] -= 1
            if hands[partner][take] == 0:
                del hands[partner][take]
            hands[partner][give] += 1
            return GameState(**{**state.__dict__, "hands": tuple(hands)})
        if kind == "build":
            _, btype, target = action
            p = state.current_player
            hands = list(state.hands)
            verts = list(state.vertices)
            edges = list(state.edges)
            roads = list(state.roads_left)
            settles = list(state.settles_left)
            cities = list(state.cities_left)
            if btype == "road":
                hands[p] = _pay(Counter(hands[p]), BUILD_ROAD)
                edges[target] = p
                roads[p] -= 1
            elif btype == "settlement":
                hands[p] = _pay(Counter(hands[p]), BUILD_SETTLE)
                verts[target] = (p, "S")
                settles[p] -= 1
            elif btype == "city":
                hands[p] = _pay(Counter(hands[p]), BUILD_CITY)
                verts[target] = (p, "C")
                cities[p] -= 1
                settles[p] += 1
            st = GameState(
                **{**state.__dict__,
                   "hands": tuple(hands),
                   "vertices": tuple(verts),
                   "edges": tuple(edges),
                   "roads_left": tuple(roads),
                   "settles_left": tuple(settles),
                   "cities_left": tuple(cities),
                }
            )
            lr = _update_longest_road(st)
            st = GameState(**{**st.__dict__, "longest_road": lr})
            w = _check_winner(st, p)
            if w is not None:
                st = GameState(**{**st.__dict__, "winner": w, "phase": "terminal"})
            return st
        if kind == "buy_dev":
            p = state.current_player
            if not state.dev_deck:
                raise ValueError("empty deck")
            card = state.dev_deck[0]
            deck = state.dev_deck[1:]
            hands = list(state.hands)
            hands[p] = _pay(Counter(hands[p]), BUY_DEV)
            dh = list(state.dev_hands)
            dh[p] = tuple(list(dh[p]) + [card])
            vp = list(state.vp_dev)
            if card == "vp":
                vp[p] += 1
            st = GameState(
                **{**state.__dict__,
                   "hands": tuple(hands),
                   "dev_deck": deck,
                   "dev_hands": tuple(dh),
                   "vp_dev": tuple(vp),
                   "bought_dev_this_turn": True,
                }
            )
            w = _check_winner(st, p)
            if w is not None:
                st = GameState(**{**st.__dict__, "winner": w, "phase": "terminal"})
            return st
        if kind == "play":
            p = state.current_player
            idx = action[1]
            dh = list(state.dev_hands[p])
            if idx < 0 or idx >= len(dh):
                raise ValueError("bad dev card index")
            card = dh[idx]
            expected = action[2]
            if card != expected:
                raise ValueError("dev card mismatch")
            del dh[idx]
            if card == "knight":
                dp = list(state.dev_played)
                dp[p] += 1
                st = GameState(
                    **{**state.__dict__,
                       "dev_hands": tuple(tuple(d if i != p else tuple(dh) for i, d in enumerate(state.dev_hands))),
                       "dev_played": tuple(dp),
                       "phase": "robber",
                       "robber_stage": "move",
                    }
                )
                la = _update_largest_army(st)
                st = GameState(**{**st.__dict__, "largest_army": la})
                w = _check_winner(st, p)
                if w is not None:
                    st = GameState(**{**st.__dict__, "winner": w, "phase": "terminal"})
                return st
            if card == "monopoly":
                r = action[3]
                new_dh = list(state.dev_hands)
                new_dh[p] = tuple(dh)
                hands = list(state.hands)
                gain = 0
                for i in range(NUM_PLAYERS):
                    if i == p:
                        continue
                    h = Counter(hands[i])
                    gain += h.get(r, 0)
                    if r in h:
                        del h[r]
                    hands[i] = h
                hands[p] = _add(Counter(hands[p]), Counter({r: gain}))
                return GameState(**{**state.__dict__, "hands": tuple(hands), "dev_hands": tuple(new_dh)})
            new_dh = list(state.dev_hands)
            new_dh[p] = tuple(dh)
            return GameState(**{**state.__dict__, "dev_hands": tuple(new_dh)})
        if kind == "pass":
            p = state.current_player
            nxt = (p + 1) % NUM_PLAYERS
            return GameState(
                **{**state.__dict__,
                   "current_player": nxt,
                   "phase": "roll",
                   "bought_dev_this_turn": False,
                   "robber_stage": "",
                   "last_roll": None,
                }
            )
        raise ValueError(f"unknown action {action!r}")

    def action_to_name(self, action: Any) -> str:
        k = action[0]
        if k == "setup":
            pl, v, e = SETUP[action[1]]
            return f"setup:place:p{pl}:v{v}:e{e}"
        if k == "roll":
            return f"chance:roll:{action[1]}"
        if k == "move_robber":
            res, num = HEXES[action[1]]
            label = f"h{action[1]}"
            if num >= 0:
                label += f":{RES_NAME[res] if res in RES_NAME else res}{num}"
            return f"move:robber:{label}"
        if k == "steal":
            return "steal:none" if action[1] is None else f"steal:p{action[1]}"
        if k == "bank":
            _, rate, _spec, give, get = action
            return f"bank:{rate}:1:{RES_NAME[give]}->{RES_NAME[get]}"
        if k == "ptrade":
            _, partner, give, take = action
            return f"trade:p{partner}:1:{RES_NAME[give]}->{RES_NAME[take]}"
        if k == "build":
            _, btype, t = action
            return f"build:{btype}:{'e' if btype == 'road' else 'v'}{t}"
        if k == "buy_dev":
            return "buy:dev"
        if k == "play":
            idx = action[1]
            card = action[2]
            if card == "monopoly":
                return f"play:dev:{idx}:monopoly:{RES_NAME[action[3]]}"
            return f"play:dev:{idx}:{card}"
        if k == "pass":
            return "pass"
        raise ValueError(action)

    def name_to_action(self, name: str) -> Any:
        if name == "pass":
            return ("pass",)
        if name == "buy:dev":
            return ("buy_dev",)
        if name.startswith("setup:place:"):
            parts = name.split(":")
            step = None
            for i, part in enumerate(SETUP):
                pl, v, e = part
                if f"p{pl}" in name and f"v{v}" in name and f"e{e}" in name:
                    step = i
                    break
            if step is None:
                raise ValueError(name)
            return ("setup", step)
        if name.startswith("chance:roll:"):
            return ("roll", int(name.rsplit(":", 1)[1]))
        if name.startswith("move:robber:h"):
            body = name.split(":", 2)[2]
            hi = int(body.split(":")[0][1:])
            return ("move_robber", hi)
        if name == "steal:none":
            return ("steal", None)
        if name.startswith("steal:p"):
            return ("steal", int(name[7:]))
        if name.startswith("bank:"):
            # bank:4:1:brick->grain
            chunks = name.split(":")
            rate = int(chunks[1])
            give, get = chunks[3].split("->")
            g = NAME_RES[give]
            t = NAME_RES[get]
            spec = g if rate == 2 else None
            return ("bank", rate, spec, g, t)
        if name.startswith("trade:p"):
            # trade:p2:1:brick->grain
            parts = name.split(":")
            partner = int(parts[1][1:])
            give, take = parts[3].split("->")
            return ("ptrade", partner, NAME_RES[give], NAME_RES[take])
        if name.startswith("build:road:e"):
            return ("build", "road", int(name[12:]))
        if name.startswith("build:settlement:v"):
            return ("build", "settlement", int(name[18:]))
        if name.startswith("build:city:v"):
            return ("build", "city", int(name[12:]))
        if name.startswith("play:dev:"):
            parts = name.split(":")
            idx = int(parts[2])
            if parts[3] == "monopoly":
                return ("play", idx, "monopoly", NAME_RES[parts[4]])
            return ("play", idx, parts[3])
        raise ValueError(name)

    def render(self, state: GameState) -> str:
        lines = [
            f"phase={state.phase} cp=p{state.current_player} robber=h{state.robber_hex}",
            f"roll={state.last_roll} setup={state.setup_step}/{len(SETUP)}",
        ]
        if state.robber_stage:
            lines[0] += f" robber_stage={state.robber_stage}"
        for p in range(NUM_PLAYERS):
            h = state.hands[p]
            parts = [f"{RES_NAME[r]}:{h.get(r,0)}" for r in RES if h.get(r, 0)]
            vp = _total_vp(state, p)
            lines.append(
                f"p{p} vp={vp} pub={_public_vp(state,p)} road={state.roads_left[p]} "
                f"set={state.settles_left[p]} city={state.cities_left[p]} hand=[{','.join(parts)}] "
                f"knights={state.dev_played[p]} vpdev={state.vp_dev[p]}"
            )
        if state.longest_road is not None:
            lines.append(f"longest_road=p{state.longest_road}")
        if state.largest_army is not None:
            lines.append(f"largest_army=p{state.largest_army}")
        if state.winner is not None:
            lines.append(f"winner=p{state.winner}")
        return "\n".join(lines)
