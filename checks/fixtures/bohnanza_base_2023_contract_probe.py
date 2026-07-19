"""Contract/adapter infrastructure probe; intentionally not a rule implementation."""

from copy import deepcopy
import json

COUNTS = {"gartenbohne": 6, "rote_bohne": 8, "augenbohne": 10, "sojabohne": 12, "brechbohne": 14, "saubohne": 16, "feuerbohne": 18, "blaue_bohne": 20}
STATE = "boardbench/bohnanza-base-2023/state/1"
ACTION = "boardbench/bohnanza-base-2023/action/1"
OBSERVATION = "boardbench/bohnanza-base-2023/observation/1"


class GameState:
    def __init__(self, payload): self.payload = deepcopy(payload)


class Game:
    def __init__(self, num_players=None, seed=None):
        self.num_players = 4 if num_players is None else int(num_players); self.seed = seed

    def initial_state(self):
        cards = [bean for bean, count in COUNTS.items() for _ in range(count)]
        players = []
        fields = 3 if self.num_players == 3 else 2
        for player in range(self.num_players):
            hand, cards = cards[:5], cards[5:]
            players.append({"id": player, "hand": hand, "fields": [[] for _ in range(fields)], "coins": 0})
        return GameState({"schema": STATE, "data": {
            "configuration": {"players": self.num_players, "seed": self.seed}, "current_player": 0, "active_player": 0,
            "start_player": 0, "phase": "plant_first", "terminal": False, "players": players,
            "zones": {"deck": cards, "discard": [], "revealed": [], "pending_received": [[] for _ in players], "reserve": []},
            "depletions": 0, "pending": None, "chance": {"seed": self.seed, "draw_index": 0},
        }})

    def current_player(self, state): return state.payload["data"]["current_player"]
    def is_terminal(self, state): return state.payload["data"]["terminal"]
    def returns(self, state):
        players = state.payload["data"]["players"]
        if not self.is_terminal(state): return [0 for _ in players]
        best = max(player["coins"] for player in players)
        winner = max(player["id"] for player in players if player["coins"] == best)
        return [1 if player["id"] == winner else -1 for player in players]

    def legal_actions(self, state):
        if self.is_terminal(state): return []
        data = state.payload["data"]; actor = data["current_player"]; result = []
        def add(kind, args=None, who=None): result.append({"type": kind, "actor": actor if who is None else who, "args": args or {}})
        hand = data["players"][actor]["hand"]
        bean = hand[0] if hand else "gartenbohne"
        for field in range(len(data["players"][actor]["fields"])): add("plant", {"field": field, "source": "hand", "index": 0, "bean": bean})
        for player in data["players"]:
            for field in range(len(player["fields"])): add("harvest", {"player": player["id"], "field": field}, player["id"])
        for kind in ("reveal", "trade_accept", "trade_reject", "end_trade", "draw", "pass"): add(kind)
        if len(data["players"]) > 1:
            partner = 1 if actor == 0 else 0
            offered = [{"owner": actor, "zone": "hand", "index": i, "bean": card} for i, card in enumerate(hand)]
            requested = [{"owner": partner, "zone": "hand", "index": i, "bean": card} for i, card in enumerate(data["players"][partner]["hand"])]
            for offer in (offered[:1], [item for item in offered if item["index"] in (0, 2)]):
                add("trade_propose", {"partner": partner, "offered": offer, "requested": requested[:1], "gift": False})
        return result

    def apply_action(self, state, action): return GameState(state.payload)
    def render(self, state): return json.dumps(self.observation_to_data(state, self.current_player(state)), ensure_ascii=False)
    def action_to_name(self, action): return json.dumps(action, ensure_ascii=False, sort_keys=True)
    def name_to_action(self, name): return json.loads(name)
    def state_to_data(self, state): return deepcopy(state.payload)
    def state_from_data(self, payload): return GameState(payload)
    def action_to_data(self, action): return {"schema": ACTION, "data": deepcopy(action)}
    def action_from_data(self, payload): return deepcopy(payload["data"])
    def observation_to_data(self, state, player):
        data = state.payload["data"]
        return {"schema": OBSERVATION, "data": {
            "player": player, "current_player": data["current_player"], "active_player": data["active_player"], "phase": data["phase"],
            "terminal": data["terminal"], "own_hand": list(data["players"][player]["hand"]),
            "opponents": [{"id": entry["id"], "hand_size": len(entry["hand"])} for entry in data["players"] if entry["id"] != player],
            "fields": [deepcopy(entry["fields"]) for entry in data["players"]], "coins": [entry["coins"] for entry in data["players"]],
            "revealed": list(data["zones"]["revealed"]), "deck_size": len(data["zones"]["deck"]),
            "discard_size": len(data["zones"]["discard"]), "pending": deepcopy(data["pending"]),
        }}
