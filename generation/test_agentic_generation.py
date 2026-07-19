from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from generation.run_expl import PROTOCOL, SOURCES, _agentic_gate, _event_commands, _validate_assumptions, implementation_prompt


VALID_IMPLEMENTATION = '''
from dataclasses import dataclass

@dataclass
class GameState:
    terminal: bool = False

class Game:
    def initial_state(self): return GameState()
    def current_player(self, state): return -1 if state.terminal else 0
    def legal_actions(self, state): return [] if state.terminal else ["finish"]
    def apply_action(self, state, action):
        if action != "finish": raise ValueError(action)
        state.terminal = True
        return state
    def is_terminal(self, state): return state.terminal
    def returns(self, state): return [1, -1] if state.terminal else [0, 0]
    def render(self, state): return str(state)
    def action_to_name(self, action): return action
    def name_to_action(self, name): return name
    def state_to_data(self, state):
        return {"schema": "boardbench/test/state/1", "data": {"terminal": state.terminal}}
    def state_from_data(self, payload):
        if set(payload) != {"schema", "data"} or payload["schema"] != "boardbench/test/state/1": raise ValueError(payload)
        return GameState(bool(payload["data"]["terminal"]))
    def action_to_data(self, action):
        return {"schema": "boardbench/test/action/1", "data": {"type": action}}
    def action_from_data(self, payload):
        if set(payload) != {"schema", "data"} or payload["schema"] != "boardbench/test/action/1": raise ValueError(payload)
        return payload["data"]["type"]
    def observation_to_data(self, state, player):
        return {"schema": "boardbench/test/observation/1", "data": {"player": player, "terminal": state.terminal}}
'''


class AgenticGenerationTests(unittest.TestCase):
    def test_current_conditions_are_explicit(self):
        clarified = SOURCES["clarified"].read_text(encoding="utf-8")
        self.assertIn("schuldet danach genau zwei", clarified)
        self.assertIn("frühere Vorschau", clarified)
        self.assertIn("vollständige beabsichtigte Aktion", clarified)
        self.assertTrue(SOURCES["pdf"].is_file())
        prompt = implementation_prompt("rulebook.txt", PROTOCOL)
        self.assertIn("assumptions.json", prompt)
        self.assertIn("state_to_data", prompt)

    def workspace(self, implementation: str):
        temporary = tempfile.TemporaryDirectory()
        path = Path(temporary.name)
        (path / "implementation.py").write_text(implementation, encoding="utf-8")
        (path / "rule_coverage.md").write_text("# Source coverage\n\nAll supplied sections mapped.\n", encoding="utf-8")
        (path / "assumptions.json").write_text('{"version": 1, "assumptions": []}\n', encoding="utf-8")
        shutil.copy2(Path(__file__).with_name("agentic_self_check.py"), path / "agentic_self_check.py")
        return temporary, path

    def test_independent_gate_runs_actual_implementation(self):
        temporary, path = self.workspace(VALID_IMPLEMENTATION)
        with temporary:
            passed, output = _agentic_gate(path, require_coverage=True)
        self.assertTrue(passed, output)
        self.assertIn("agentic-self-check OK", output)

    def test_independent_gate_requires_source_coverage_audit(self):
        temporary, path = self.workspace(VALID_IMPLEMENTATION)
        with temporary:
            (path / "rule_coverage.md").unlink()
            passed, output = _agentic_gate(path, require_coverage=True)
        self.assertFalse(passed)
        self.assertIn("rule_coverage.md", output)

    def test_agentic_v2_gate_does_not_require_later_coverage_artifact(self):
        temporary, path = self.workspace(VALID_IMPLEMENTATION)
        with temporary:
            (path / "rule_coverage.md").unlink()
            passed, output = _agentic_gate(path, require_coverage=False)
        self.assertTrue(passed, output)

    def test_agentic_v2_2_requires_valid_material_assumptions(self):
        temporary, path = self.workspace(VALID_IMPLEMENTATION)
        with temporary:
            passed, output = _agentic_gate(path, require_coverage=True, require_assumptions=True)
            self.assertTrue(passed, output)
            (path / "assumptions.json").write_text('{"version": 1, "assumptions": [{}]}', encoding="utf-8")
            self.assertIn("missing required fields", _validate_assumptions(path / "assumptions.json") or "")

    def test_independent_gate_rejects_legal_action_that_crashes(self):
        broken = VALID_IMPLEMENTATION.replace(
            'if action != "finish": raise ValueError(action)',
            'raise ValueError("legal action crashed")',
        )
        temporary, path = self.workspace(broken)
        with temporary:
            passed, output = _agentic_gate(path, require_coverage=True)
        self.assertFalse(passed)
        self.assertIn("legal action crashed", output)

    def test_event_commands_extracts_real_command_executions(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "events.jsonl"
            path.write_text(
                json.dumps({"type": "item.completed", "item": {"type": "command_execution", "command": "python agentic_self_check.py"}}) + "\n",
                encoding="utf-8",
            )
            self.assertEqual(_event_commands(path), ["python agentic_self_check.py"])


if __name__ == "__main__":
    unittest.main()
