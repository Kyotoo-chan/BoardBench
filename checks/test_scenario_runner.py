from __future__ import annotations

import json
import unittest
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

from checks.run_scenarios import _contains, _resolve_action, _settle
from checks.scenario_adapters import abalone, expl


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
    def test_expl_mutations_target_current_scenarios(self):
        root = Path(__file__).resolve().parents[1]
        suite = json.loads((root / "checks/scenarios/expl.json").read_text(encoding="utf-8"))
        manifest = json.loads((root / "checks/mutations/expl.json").read_text(encoding="utf-8"))
        scenario_ids = {item["id"] for item in suite["scenarios"]}
        self.assertEqual(manifest["rubric_version"], suite["rubric_version"])
        self.assertTrue(all(set(item["scenarios"]) <= scenario_ids for item in manifest["mutations"]))
        self.assertEqual(len({item["id"] for item in manifest["mutations"]}), len(manifest["mutations"]))

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

    def test_adapter_can_resolve_a_semantic_action(self):
        actions = ["left", "right"]
        adapter = SimpleNamespace(resolve_action=lambda module, game, state, legal, spec: legal[spec["index"]])
        selected = _resolve_action(
            DummyGame(),
            actions,
            {"adapter": {"index": 1}},
            state={},
            adapter=adapter,
        )
        self.assertEqual(selected, "right")

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

    def test_settle_does_not_play_a_normal_draw_named_pass(self):
        game = DummyGame()
        state = {"actions": ["Passen:draw"]}
        result = _settle(
            game,
            state,
            [{"while_all_contains_any": ["pass", "nope"], "choose_contains_any": ["pass"]}],
        )
        self.assertEqual(result["actions"], ["Passen:draw"])

    def test_abalone_adapter_sets_and_observes_axial_board(self):
        cells = {
            (q, r): None
            for r in range(-4, 5)
            for q in range(max(-4, -r - 4), min(4, -r + 4) + 1)
        }
        cells[(0, -4)], cells[(-4, 4)] = "B", "W"
        initial = SimpleNamespace(board=cells, current_player=0, captures=[0, 0], winner=None)
        game = SimpleNamespace(initial_state=lambda: initial)
        state = abalone.setup(None, game, {"black": ["0,0"], "white": ["4,0"]})
        abalone.check(None, game, state, {"marble_counts": {"black": 1, "white": 1}, "occupancy": {"0,0": "black"}})

    def test_abalone_adapter_resolves_move_by_transition(self):
        cells = {
            (q, r): None
            for r in range(-4, 5)
            for q in range(max(-4, -r - 4), min(4, -r + 4) + 1)
        }
        cells[(0, -4)], cells[(-4, 4)] = "B", "W"
        initial = SimpleNamespace(board=cells, current_player=0, captures=[0, 0], winner=None)

        def apply_action(state, action):
            result = SimpleNamespace(**vars(state))
            result.board = state.board.copy()
            source, target = action
            result.board[target] = result.board[source]
            result.board[source] = None
            return result

        game = SimpleNamespace(initial_state=lambda: initial, apply_action=apply_action)
        state = abalone.setup(None, game, {"black": ["0,0"], "white": ["4,0"]})
        actions = [((0, 0), (-1, 0)), ((0, 0), (1, 0))]
        selected = abalone.resolve_action(None, game, state, actions, {"group": ["0,0"], "direction": "E"})
        self.assertEqual(selected, actions[1])

    def test_abalone_adapter_supports_mutating_apply_action(self):
        cells = {
            (q, r): None
            for r in range(-4, 5)
            for q in range(max(-4, -r - 4), min(4, -r + 4) + 1)
        }
        cells[(0, -4)], cells[(-4, 4)] = "B", "W"
        initial = SimpleNamespace(board=cells, current_player=0, captures=[0, 0], winner=None)

        def apply_action(state, action):
            source, target = action
            state.board[target] = state.board[source]
            state.board[source] = None

        game = SimpleNamespace(initial_state=lambda: initial, apply_action=apply_action)
        state = abalone.setup(None, game, {"black": ["0,0"], "white": ["4,0"]})
        actions = [((0, 0), (-1, 0)), ((0, 0), (1, 0))]
        selected = abalone.resolve_action(None, game, state, actions, {"group": ["0,0"], "direction": "E"})
        self.assertEqual(selected, actions[1])

    def test_abalone_adapter_marks_sparse_fixture_rejection_untestable(self):
        cells = {
            (q, r): None
            for r in range(-4, 5)
            for q in range(max(-4, -r - 4), min(4, -r + 4) + 1)
        }
        cells[(0, -4)], cells[(-4, 4)] = "B", "W"
        initial = SimpleNamespace(board=cells, current_player=0, winner=None)

        def reject(state):
            raise RuntimeError("invalid inventory invariant")

        game = SimpleNamespace(initial_state=lambda: initial, legal_actions=reject)
        with self.assertRaisesRegex(NotImplementedError, "rejects sparse evaluator fixture"):
            abalone.setup(None, game, {"black": ["0,0"], "white": ["4,0"]})

    def test_abalone_adapter_does_not_hide_action_probe_crash(self):
        cells = {
            (q, r): None
            for r in range(-4, 5)
            for q in range(max(-4, -r - 4), min(4, -r + 4) + 1)
        }
        cells[(0, -4)], cells[(-4, 4)] = "B", "W"
        initial = SimpleNamespace(board=cells, current_player=0, winner=None)
        game = SimpleNamespace(
            initial_state=lambda: initial,
            legal_actions=lambda state: ["broken"],
            apply_action=lambda state, action: (_ for _ in ()).throw(RuntimeError("broken legal action")),
        )
        state = abalone.setup(None, game, {"black": ["0,0"], "white": ["4,0"]})
        with self.assertRaisesRegex(RuntimeError, "broken legal action"):
            abalone.check(
                None,
                game,
                state,
                {"move_legal": {"group": ["0,0"], "direction": "E", "expected": False}},
            )

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

    def test_expl_adapter_supports_active_player_field(self):
        module = SimpleNamespace(ATTACK="attack", SHUFFLE="shuffle")
        state = SimpleNamespace(
            hands=[[], []], deck=[], discard=[], alive=[True, True],
            active=0, turns_owed=1, pending=None, winner=None,
        )
        game = SimpleNamespace(initial_state=lambda: state)
        configured = expl.setup(module, game, {"active_player": 1, "deck": ["shuffle"]})
        self.assertEqual(configured.active, 1)

    def test_expl_adapter_checks_deck_and_stale_preview(self):
        module = SimpleNamespace(ATTACK="attack", EXPLODING="kitten", SHUFFLE="shuffle")
        state = SimpleNamespace(deck=["attack", "kitten"], viewed_top=(), hands=[[], []], discard=[])
        expl.check(module, None, state, {"deck": ["attack", "kitten"], "deck_count": {"kitten": 1}, "preview_empty": True})
        state.viewed_top = ("attack",)
        with self.assertRaisesRegex(AssertionError, "stale preview"):
            expl.check(module, None, state, {"preview_empty": True})

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
