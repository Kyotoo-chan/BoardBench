import json
import tempfile
import unittest
from pathlib import Path

from checks.check_player_counts import check_player_counts


IMPLEMENTATION = '''
class Game:
    def __init__(self, num_players=None, seed=None):
        self.num_players = 2 if num_players is None else num_players
        if self.num_players not in (2, 3):
            raise ValueError("unsupported")
    def initial_state(self): return {"done": False}
    def legal_actions(self, state): return [] if state["done"] else ["finish"]
    def apply_action(self, state, action): return {"done": True}
    def is_terminal(self, state): return state["done"]
    def returns(self, state): return [0] * self.num_players
    def render(self, state): return str(state)
    def action_to_name(self, action): return action
    def name_to_action(self, name): return name
'''


class PlayerCountTests(unittest.TestCase):
    def test_supported_and_outside_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            code = root / "game.py"
            profile = root / "profile.json"
            code.write_text(IMPLEMENTATION, encoding="utf-8")
            profile.write_text(json.dumps({"player_counts": {"supported": [2, 3], "unsupported": [1, 4]}}), encoding="utf-8")
            result = check_player_counts(code, profile, max_steps=5)
            self.assertEqual(result["passed"], 4)
            self.assertEqual(result["total"], 4)

    def test_profile_must_declare_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            code = root / "game.py"
            profile = root / "profile.json"
            code.write_text(IMPLEMENTATION, encoding="utf-8")
            profile.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "player_counts.supported"):
                check_player_counts(code, profile)


if __name__ == "__main__":
    unittest.main()
