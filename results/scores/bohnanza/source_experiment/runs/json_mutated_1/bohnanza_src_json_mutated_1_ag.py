"""Source-bounded Bohnanza Ackerbohnen variant for four players.

The module uses immutable-looking (deep-copied) state transitions and a fixed,
reproducible shuffle.  Hands are ordered lists: index zero is always the only
plantable hand card.  Coins are cards turned to their reverse side.
"""
from dataclasses import dataclass, field
from typing import Optional
import copy
import random
from collections import Counter


BEANS = {
    "Blaue Bohne": (20, ((4, 1), (6, 2), (8, 3), (10, 4))),
    "Feuerbohne": (18, ((3, 1), (6, 2), (8, 3), (9, 4))),
    "Saubohne": (16, ((3, 1), (5, 2), (7, 3), (8, 4))),
    "Brechbohne": (14, ((3, 1), (5, 2), (6, 3), (7, 4))),
    "Sojabohne": (12, ((2, 1), (4, 2), (6, 3), (7, 4))),
    "Augenbohne": (10, ((2, 1), (4, 2), (5, 3), (6, 4))),
    "Rote Bohne": (8, ((2, 1), (3, 2), (4, 3), (5, 4))),
    "Gartenbohne": (6, ((2, 2), (3, 3))),
    "Weinbrandbohne": (22, ((2, 1), (4, 2), (6, 3), (8, 4))),
    "Ackerbohne": (3, ((2, 2), (3, 3))),
}


@dataclass(frozen=True)
class Action:
    kind: str
    arg: str = ""
    index: int = -1


@dataclass
class Player:
    hand: list[str] = field(default_factory=list)
    fields: list[list[str]] = field(default_factory=lambda: [[], []])
    coins: int = 0
    incoming: list[str] = field(default_factory=list)


@dataclass
class Offer:
    target: int
    give_hand: list[int] = field(default_factory=list)
    give_market: list[int] = field(default_factory=list)
    request_hand: list[tuple] = field(default_factory=list)
    submitted: bool = False


@dataclass
class GameState:
    players: list[Player]
    deck: list[str]
    discard: list[str]
    active: int = 0
    phase: str = "plant_first"
    market: list[str] = field(default_factory=list)
    offer: Optional[Offer] = None
    empty_count: int = 0
    terminal: bool = False
    terminal_pending: bool = False
    turn: int = 0


class Game:
    """Complete four-player realization; the rulebook permits four or five.

    ``player_count`` may be 4 or 5.  ``seed`` only selects the reproducible
    hidden deal; it does not alter rules.
    """
    def __init__(self, player_count: int = 4, seed: int = 1):
        if player_count not in (4, 5):
            raise ValueError("Ackerbohnen variant requires 4 or 5 players")
        self.player_count, self.seed = player_count, seed

    def initial_state(self) -> GameState:
        deck = [name for name, (n, _) in BEANS.items() for _ in range(n)]
        random.Random(self.seed).shuffle(deck)
        ps = [Player() for _ in range(self.player_count)]
        # Deal singly, preserving the order received; top of deck is list end.
        for _ in range(5):
            for p in ps:
                p.hand.append(deck.pop())
        return GameState(ps, deck, [])

    def current_player(self, s: GameState) -> int:
        if s.offer and s.offer.submitted:
            return s.offer.target
        if s.phase == "draw_each":
            return (s.active + len(s.market)) % len(s.players)
        return s.active

    def is_terminal(self, s: GameState) -> bool:
        return s.terminal

    def _harvest_actions(self, s: GameState, who: int) -> list[Action]:
        p = s.players[who]
        out = []
        for i, f in enumerate(p.fields):
            if not f:
                continue
            # Bean protection: a singleton cannot be harvested while another
            # field contains more than one card.
            if len(f) == 1 and any(len(x) > 1 for x in p.fields):
                continue
            out.append(Action("harvest", str(who), i))
        return out

    def legal_actions(self, s: GameState) -> list[Action]:
        if s.terminal:
            return []
        who = self.current_player(s)
        a = self._harvest_actions(s, who)
        p = s.players[who]
        if s.offer and s.offer.submitted:
            wanted = Counter(bean for _, bean in s.offer.request_hand)
            available = Counter(s.players[s.offer.target].hand)
            choices = [Action("reject_offer")]
            if all(available[bean] >= count for bean, count in wanted.items()):
                choices.insert(0, Action("accept_offer"))
            return a + choices
        if s.phase == "plant_first":
            if not p.hand:
                return a + [Action("skip_empty_hand")]
            return a + self._plant_options(p, "plant_hand")
        if s.phase == "plant_second":
            return a + [Action("finish_planting")] + (self._plant_options(p, "plant_hand") if p.hand else [])
        if s.phase == "reveal":
            return a + [Action("reveal_two")]
        if s.phase == "trade":
            out = a + [Action("finish_trading")]
            if s.offer is None:
                out += [Action("start_offer", str(i)) for i in range(len(s.players)) if i != s.active]
            else:
                o = s.offer
                used_h, used_m = set(o.give_hand), set(o.give_market)
                used_r = {i for i, _ in o.request_hand}
                out += [Action("offer_hand", p.hand[i], i) for i in range(len(p.hand)) if i not in used_h]
                out += [Action("offer_market", s.market[i], i) for i in range(len(s.market)) if i not in used_m]
                tp = s.players[o.target]
                out += [Action("request_hand", tp.hand[i], i) for i in range(len(tp.hand)) if i not in used_r]
                if o.give_hand or o.give_market:
                    out.append(Action("submit_offer"))
                out.append(Action("cancel_offer"))
            return out
        if s.phase == "plant_incoming":
            if not p.incoming:
                return a + [Action("finish_incoming")]
            return a + self._incoming_options(p)
        if s.phase == "draw_each":
            return a + [Action("draw_one")]
        raise ValueError(s.phase)

    @staticmethod
    def _plant_options(p: Player, kind: str) -> list[Action]:
        bean = p.hand[0] if kind == "plant_hand" else p.incoming[0]
        out = []
        for i, f in enumerate(p.fields):
            if not f or f[0] == bean:
                out.append(Action(kind, bean, i))
        return out

    @staticmethod
    def _incoming_options(p: Player) -> list[Action]:
        out = []
        for source, bean in enumerate(p.incoming):
            for destination, f in enumerate(p.fields):
                if not f or f[0] == bean:
                    out.append(Action("plant_incoming", f"{source}:{bean}", destination))
        return out

    def _draw(self, s: GameState) -> Optional[str]:
        if not s.deck:
            s.empty_count += 1
            if s.empty_count >= 3:
                if s.phase == "reveal": s.terminal_pending = True
                else: s.terminal = True
                return None
            s.deck = s.discard
            s.discard = []
            random.Random(self.seed + s.empty_count).shuffle(s.deck)
        return s.deck.pop() if s.deck else None

    def _harvest(self, s: GameState, who: int, fi: int) -> None:
        p, cards = s.players[who], s.players[who].fields[fi]
        bean, n = cards[0], len(cards)
        if bean == "Ackerbohne":
            value = 3 if n >= 3 else (2 if n == 2 and len(p.fields) == 2 else 0)
            if n == 2 and len(p.fields) == 2:
                p.fields.append([])
        else:
            value = 0
            for threshold, coins in BEANS[bean][1]:
                if n >= threshold:
                    value = coins
        p.coins += value
        # Coin cards come from the harvested cards; all others are discarded.
        s.discard.extend(cards[value:])
        p.fields[fi] = []

    def apply_action(self, state: GameState, action: Action) -> GameState:
        s = copy.deepcopy(state)
        if action not in self.legal_actions(s):
            raise ValueError("illegal action: " + self.action_to_name(action))
        who, p = self.current_player(s), s.players[self.current_player(s)]
        k = action.kind
        if k == "harvest":
            self._harvest(s, int(action.arg), action.index); return s
        if k == "skip_empty_hand": s.phase = "reveal"
        elif k in ("plant_hand", "plant_incoming"):
            if k == "plant_hand": bean = p.hand.pop(0)
            else:
                source_text, bean = action.arg.split(":", 1)
                p.incoming.pop(int(source_text))
            p.fields[action.index].append(bean)
            if k == "plant_hand": s.phase = "plant_second" if s.phase == "plant_first" else "reveal"
        elif k == "finish_planting": s.phase = "reveal"
        elif k == "reveal_two":
            for _ in range(2):
                card = self._draw(s)
                if card is not None: s.market.append(card)
            if not s.terminal: s.phase = "trade"
        elif k == "start_offer": s.offer = Offer(int(action.arg))
        elif k == "offer_hand": s.offer.give_hand.append(action.index)
        elif k == "offer_market": s.offer.give_market.append(action.index)
        elif k == "request_hand": s.offer.request_hand.append((action.index, action.arg))
        elif k == "cancel_offer": s.offer = None
        elif k == "submit_offer": s.offer.submitted = True
        elif k == "reject_offer": s.offer = None
        elif k == "accept_offer":
            o, ap, tp = s.offer, s.players[s.active], s.players[s.offer.target]
            given = [ap.hand[i] for i in o.give_hand] + [s.market[i] for i in o.give_market]
            requested = []
            remove_requested = set()
            for original_index, bean in o.request_hand:
                candidates = [i for i, card in enumerate(tp.hand) if card == bean and i not in remove_requested]
                if not candidates:
                    raise ValueError("offered card is no longer available")
                chosen = original_index if original_index in candidates else candidates[0]
                remove_requested.add(chosen); requested.append(bean)
            ap.hand = [x for i, x in enumerate(ap.hand) if i not in set(o.give_hand)]
            s.market = [x for i, x in enumerate(s.market) if i not in set(o.give_market)]
            tp.hand = [x for i, x in enumerate(tp.hand) if i not in remove_requested]
            tp.incoming.extend(given); ap.incoming.extend(requested); s.offer = None
        elif k == "finish_trading":
            p.incoming.extend(s.market); s.market = []; s.phase = "plant_incoming"
        elif k == "finish_incoming":
            s.market = []
            if s.terminal_pending: s.terminal = True
            else: s.phase = "draw_each"
        elif k == "draw_one":
            card = self._draw(s)
            if card is not None: s.players[who].hand.append(card)
            s.market.append("drawn")
            if len(s.market) == len(s.players) and not s.terminal:
                s.market = []; s.active = (s.active + 1) % len(s.players); s.turn += 1; s.phase = "plant_first"
        return s

    def returns(self, s: GameState) -> list[float]:
        if not s.terminal:
            return [0.0] * len(s.players)
        scored = copy.deepcopy(s)
        for i, p in enumerate(scored.players):
            for fi in range(len(p.fields)):
                if p.fields[fi]: self._harvest(scored, i, fi)
        scores = [p.coins for p in scored.players]
        best = max(scores)
        winners = [i for i, x in enumerate(scores) if x == best]
        # Tie: furthest clockwise from start player (highest seat number).
        winner = max(winners)
        return [1.0 if i == winner else -1.0 for i in range(len(scores))]

    def render(self, s: GameState) -> str:
        lines = [f"turn={s.turn} active={s.active} phase={s.phase} deck={len(s.deck)} empties={s.empty_count}"]
        for i, p in enumerate(s.players):
            hand = p.hand if i == self.current_player(s) else ["?"] * len(p.hand)
            lines.append(f"P{i}: coins={p.coins} hand={hand} fields={p.fields} incoming={p.incoming}")
        return "\n".join(lines)

    def action_to_name(self, a: Action) -> str:
        bits = [a.kind]
        if a.arg != "": bits.append(a.arg)
        if a.index >= 0: bits.append(str(a.index))
        return " | ".join(bits)

    def name_to_action(self, name: str) -> Action:
        bits = name.split(" | ")
        kind = bits[0]
        if len(bits) == 1: return Action(kind)
        if len(bits) == 2:
            return Action(kind, bits[1])
        return Action(kind, bits[1], int(bits[2]))
