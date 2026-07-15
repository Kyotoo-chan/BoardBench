"""Small, source-faithful Exploding Kittens (NSFW edition) rules engine."""
from dataclasses import dataclass, field
import copy, json, random

EK = "Exploding Kitten"
DEFUSE = "Entschärfung"
ATTACK = "Angriff"
SKIP = "Hops!"
FAVOR = "Wunsch"
SHUFFLE = "Mischen"
SEE = "Blick in die Zukunft"
NOPE = "NÖ!"
CATS = ("Katze-1", "Katze-2", "Katze-3", "Katze-4", "Katze-5")
PLAYABLE = (ATTACK, SKIP, FAVOR, SHUFFLE, SEE)


@dataclass
class GameState:
    num_players: int
    deck: list[str]
    hands: list[list[str]]
    discard: list[str] = field(default_factory=list)
    alive: list[bool] = field(default_factory=list)
    player: int = 0
    turns_left: int = 1
    phase: str = "turn"              # turn, insert, favor, triple, reaction, terminal
    actor: int | None = None
    target: int | None = None
    requested: str | None = None
    pending: tuple | None = None
    cancelled: bool = False
    reaction_player: int | None = None
    reaction_passes: int = 0
    seen: dict[int, tuple[str, ...]] = field(default_factory=dict)
    winner: int | None = None
    rng_state: object | None = None


class Game:
    def __init__(self, num_players: int = 2, seed: int | None = 0):
        if not 2 <= num_players <= 5:
            raise ValueError("num_players must be 2..5 (the supplied material is for 2..5)")
        self.num_players, self.seed = num_players, seed

    def initial_state(self):
        r = random.Random(self.seed)
        # Four of every named action/cat except the source's stated 5 NÖ!, 5 Blick, 6 Entschärfung.
        pool = ([ATTACK]*4 + [SKIP]*4 + [FAVOR]*4 + [SHUFFLE]*4 + [SEE]*5 +
                [NOPE]*5 + sum(([c]*4 for c in CATS), []))
        r.shuffle(pool)
        hands = [[pool.pop() for _ in range(7)] + [DEFUSE] for _ in range(self.num_players)]
        # Two-player variant: only two further Entschärfung; otherwise all unused ones.
        extra = 2 if self.num_players == 2 else 6 - self.num_players
        pool += [DEFUSE] * extra + [EK] * (self.num_players - 1)
        r.shuffle(pool)
        return GameState(self.num_players, pool, hands, alive=[True]*self.num_players,
                         rng_state=r.getstate())

    def current_player(self, s):
        return s.reaction_player if s.phase == "reaction" else (s.target if s.phase == "favor" else s.player)

    def _others(self, s, p):
        return [i for i in range(s.num_players) if i != p and s.alive[i]]

    def legal_actions(self, s):
        if self.is_terminal(s): return []
        p = self.current_player(s)
        if s.phase == "insert": return [("Entschärfung: Exploding Kitten zurücklegen", i) for i in range(len(s.deck)+1)]
        if s.phase == "favor":
            return [("Wunsch: Karte geben", c) for c in sorted(set(s.hands[p]))]
        if s.phase == "triple":
            return [("Drilling: Karte wünschen", c) for c in sorted(set(s.hands[s.target]))] + [("Drilling: Karte nicht vorhanden",)]
        if s.phase == "reaction":
            a = [("NÖ!: passen",)]
            if NOPE in s.hands[p]: a.append(("NÖ!: spielen",))
            return a
        h, out = s.hands[p], [("Ziehen",)]
        for c in PLAYABLE:
            if c in h:
                if c == FAVOR:
                    out += [("Wunsch spielen", t) for t in self._others(s, p) if s.hands[t]]
                else: out.append((c + " spielen",))
        # Any two equal titles; any three equal titles; five distinct titles.
        for c in sorted(set(h)):
            if c not in (EK, DEFUSE) and h.count(c) >= 2:
                out += [("Pärchen spielen", c, t) for t in self._others(s, p) if s.hands[t]]
            if c not in (EK, DEFUSE) and h.count(c) >= 3:
                out += [("Drilling spielen", c, t) for t in self._others(s, p)]
        distinct = sorted(set(h) - {EK, DEFUSE})
        if len(distinct) >= 5:
            import itertools
            for cards in itertools.combinations(distinct, 5):
                for take in sorted(set(s.discard)):
                    out.append(("Fünfling spielen", cards, take))
        return out

    def _next(self, s, p):
        q = (p + 1) % s.num_players
        while not s.alive[q]: q = (q + 1) % s.num_players
        return q

    def _reaction(self, s, pending):
        others = self._others(s, s.player)
        if not others:
            return self._resolve(s, pending)
        s.phase, s.pending, s.cancelled = "reaction", pending, False
        s.reaction_player, s.reaction_passes = others[0], 0
        return s

    def _resolve(self, s, a):
        kind = a[0]; p = s.player
        s.phase = "turn"; s.pending = None; s.reaction_player = None
        if kind == "play":
            card = a[1]
            if card == ATTACK:
                s.player = self._next(s, p); s.turns_left = 2
            elif card == SKIP:
                s.turns_left -= 1
                if s.turns_left <= 0: s.player, s.turns_left = self._next(s, p), 1
            elif card == SHUFFLE:
                r=random.Random(); r.setstate(s.rng_state); r.shuffle(s.deck); s.rng_state=r.getstate()
            elif card == SEE: s.seen[p] = tuple(s.deck[-3:][::-1])
            elif card == FAVOR: s.phase, s.actor, s.target = "favor", p, a[2]
        elif kind == "pair":
            target=a[2]; r=random.Random(); r.setstate(s.rng_state)
            card=r.choice(s.hands[target]); s.hands[target].remove(card); s.hands[p].append(card); s.rng_state=r.getstate()
        elif kind == "triple": s.phase, s.actor, s.target = "triple", p, a[2]
        elif kind == "five":
            take=a[3]; s.discard.remove(take); s.hands[p].append(take)
        return s

    def apply_action(self, state, action):
        s=copy.deepcopy(state)
        if action not in self.legal_actions(s): raise ValueError("illegal action")
        p=self.current_player(s); tag=action[0]
        if s.phase == "insert":
            s.deck.insert(action[1], EK); s.phase="turn"; s.player=self._next(s,p); s.turns_left=1
        elif s.phase == "favor":
            c=action[1]; s.hands[p].remove(c); s.hands[s.actor].append(c); s.phase="turn"; s.player=s.actor
        elif s.phase == "triple":
            if tag.endswith("wünschen"):
                c=action[1]; s.hands[s.target].remove(c); s.hands[s.actor].append(c)
            s.phase="turn"; s.player=s.actor
        elif s.phase == "reaction":
            alive_others=len(self._others(s,s.player))
            if tag == "NÖ!: spielen":
                s.hands[p].remove(NOPE); s.discard.append(NOPE); s.cancelled=not s.cancelled; s.reaction_passes=0
            else: s.reaction_passes += 1
            if s.reaction_passes >= alive_others:
                pending=s.pending
                if s.cancelled: s.phase="turn"; s.pending=None; s.reaction_player=None
                else: self._resolve(s,pending)
            else: s.reaction_player=self._next(s,p)
        elif tag == "Ziehen":
            c=s.deck.pop(); s.seen.pop(p,None)
            if c == EK:
                if DEFUSE in s.hands[p]:
                    s.hands[p].remove(DEFUSE); s.discard.append(DEFUSE); s.phase="insert"
                else:
                    s.discard.append(EK); s.alive[p]=False
                    if sum(s.alive)==1: s.winner=s.alive.index(True); s.phase="terminal"
                    else: s.player=self._next(s,p); s.turns_left=1
            else:
                s.hands[p].append(c); s.turns_left-=1
                if s.turns_left<=0: s.player,self_turn=self._next(s,p),1; s.turns_left=self_turn
        else:
            if tag.endswith(" spielen") and tag.split(" spielen")[0] in PLAYABLE:
                card=tag[:-8]; s.hands[p].remove(card); s.discard.append(card); self._reaction(s,("play",card,*action[1:]))
            elif tag.startswith("Pärchen"):
                c=action[1]; s.hands[p].remove(c); s.hands[p].remove(c); s.discard += [c,c]; self._reaction(s,("pair",c,action[2]))
            elif tag.startswith("Drilling"):
                c=action[1]
                for _ in range(3): s.hands[p].remove(c)
                s.discard += [c]*3; self._reaction(s,("triple",c,action[2]))
            elif tag.startswith("Fünfling"):
                for c in action[1]: s.hands[p].remove(c); s.discard.append(c)
                self._reaction(s,("five",action[1],None,action[2]))
        return s

    def is_terminal(self,s): return s.winner is not None
    def returns(self,s): return [1 if i==s.winner else -1 for i in range(s.num_players)] if self.is_terminal(s) else [0]*s.num_players
    def render(self,s):
        return f"phase={s.phase} player={self.current_player(s)} deck={len(s.deck)} hands={[len(h) for h in s.hands]} alive={s.alive} discard={s.discard}"
    def action_to_name(self,a): return json.dumps(a,ensure_ascii=False,separators=(",",":"))
    def name_to_action(self,n):
        def tup(x): return tuple(tup(v) for v in x) if isinstance(x,list) else x
        return tup(json.loads(n))
