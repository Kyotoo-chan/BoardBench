from __future__ import annotations

import unittest

from checks.run_scenarios import _contains, _resolve_action, _settle


class DummyGame:
    def action_to_name(self, action):
        return action

    def legal_actions(self, state):
        return state["actions"]

    def apply_action(self, state, action):
        if action == "react:pass":
            state["actions"] = ["play:preview", "draw"]
        return state


class ScenarioRunnerTests(unittest.TestCase):
    def test_semantic_matching_handles_case_separators_and_umlauts(self):
        self.assertTrue(_contains("play:Blick_in_die_Zukunft", "blick in die zukunft"))
        self.assertTrue(_contains("play:Doppel-Zug", "doppel zug"))
        self.assertTrue(_contains("play:FÜNF", "funf"))

    def test_semantic_selector_can_prefer_a_specific_combination_result(self):
        game = DummyGame()
        actions = ["five:a+b+c+d+e:take:attack", "five:a+b+c+d+e:take:exploding_kitten"]
        selected = _resolve_action(
            game,
            actions,
            {
                "contains_any": ["five"],
                "prefer_contains_all_groups": [["five"], ["kitten"]],
            },
        )
        self.assertEqual(selected, actions[1])

    def test_settle_stops_after_reaction_phase(self):
        game = DummyGame()
        state = {"actions": ["react:pass"]}
        result = _settle(
            game,
            state,
            [{
                "while_all_contains_any": ["pass", "nope"],
                "choose_contains_any": ["pass"],
                "max_steps": 5,
            }],
        )
        self.assertEqual(result["actions"], ["play:preview", "draw"])


if __name__ == "__main__":
    unittest.main()
