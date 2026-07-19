from __future__ import annotations

import importlib.util
import unittest
from dataclasses import dataclass
from pathlib import Path


PATH = Path(__file__).with_name("scenario_adapters") / "bohnanza_posthoc_v2.py"
SPEC = importlib.util.spec_from_file_location("bohnanza_posthoc_v2", PATH)
assert SPEC and SPEC.loader
ADAPTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ADAPTER)


@dataclass
class State:
    deck: list[str]
    discard: list[str]
    hands: list[list[str]]
    fields: list[list[list[str]]]
    traded: list[list[str]]


class BohnanzaPosthocV2Tests(unittest.TestCase):
    def test_nested_player_zones_are_flattened_as_cards(self):
        state = State(
            deck=["Blaue Bohne"],
            discard=["Feuerbohne"],
            hands=[["Saubohne"], []],
            fields=[[["Sojabohne"], []], [[], []]],
            traded=[["Ackerbohne"], []],
        )
        self.assertEqual(
            ADAPTER._all_cards(state),
            ["Blaue Bohne", "Feuerbohne", "Saubohne", "Sojabohne", "Ackerbohne"],
        )

    def test_unhashable_candidates_do_not_crash_card_lookup(self):
        class Module:
            BEANS = {"Blaue Bohne": (20, [[4, 1]])}

        class Game:
            def initial_state(self):
                return State([], [], [["Blaue Bohne"]], [[[], []]], [[]])

        self.assertEqual(ADAPTER._card(Module, Game(), "blau"), "Blaue Bohne")

    def test_adapter_marks_unsupported_representation_untestable(self):
        error = ADAPTER.AdapterUntestable("unsupported")
        self.assertTrue(ADAPTER.is_untestable(error))
        self.assertFalse(ADAPTER.is_untestable(ValueError("implementation crash")))


if __name__ == "__main__":
    unittest.main()
