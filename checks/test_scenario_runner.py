from __future__ import annotations

import unittest
from dataclasses import dataclass
from types import SimpleNamespace

from checks.run_scenarios import _contains, _resolve_action, _settle
from checks.scenario_adapters import expl


class DummyGame:
    def action_to_name(self, action):
        return action

    def legal_actions(self, state):
        return state["actions"]

    def apply_action(self, state, action):
        if action == "react:pass":
            state["actions"] = ["play:preview", "draw"]
        return state


@dataclass(frozen=True)
class ImmutableState:
    hands: tuple[tuple[str, ...], ...] = ((), ())
    deck: tuple[str, ...] = ()
    discard: tuple[str, ...] = ()
    alive: tuple[bool, ...] = (True, True)
    player: int = 0
    turns_left: int = 1
    pending: tuple[str, ...] = ()
    winner: int | None = None


class ScenarioRunnerTests(unittest.TestCase):
    def test_semantic_matching_handles_case_separators_and_umlauts(self):
        self.assertTrue(_contains("play:Blick_in_die_Zukunft", "blick in die zukunft"))
        self.assertTrue(_contains("play:Doppel-Zug", "doppel zug"))
        self.assertTrue(_contains("play:FÜNF", "funf"))
        self.assertTrue(_contains("play:Schutzkarte", "protection"))
        self.assertTrue(_contains("request:Gefahrenkarte", "danger"))

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

    def test_expl_adapter_resolves_anonymized_card_catalog(self):
        module = SimpleNamespace(CARDS=("Gefahrenkarte", "Schutzkarte", "Doppelzug", "Neuordnen"))
        game = SimpleNamespace(initial_state=lambda: ImmutableState())
        state = expl.setup(
            module,
            game,
            {"hands": {"0": ["attack"], "1": []}, "deck": ["shuffle"]},
        )
        self.assertEqual(state.hands[0], ("Doppelzug",))
        self.assertEqual(state.deck, ("Neuordnen",))

    def test_expl_adapter_supports_immutable_tuple_states(self):
        module = SimpleNamespace(ATTACK="attack", SHUFFLE="shuffle")
        game = SimpleNamespace(initial_state=lambda: ImmutableState())
        state = expl.setup(
            module,
            game,
            {"hands": {"0": ["attack"], "1": []}, "deck": ["shuffle"], "active_player": 1, "turns_owed": 2},
        )
        self.assertEqual(state.hands, (("attack",), ()))
        self.assertEqual(state.deck, ("shuffle",))
        self.assertEqual((state.player, state.turns_left), (1, 2))


if __name__ == "__main__":
    unittest.main()
