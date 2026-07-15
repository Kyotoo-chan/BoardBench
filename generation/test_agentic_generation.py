from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from generation.run_expl_variants import _agentic_gate, _event_commands


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
'''


class AgenticGenerationTests(unittest.TestCase):
    def workspace(self, implementation: str):
        temporary = tempfile.TemporaryDirectory()
        path = Path(temporary.name)
        (path / "implementation.py").write_text(implementation, encoding="utf-8")
        shutil.copy2(Path(__file__).with_name("agentic_self_check.py"), path / "agentic_self_check.py")
        return temporary, path

    def test_independent_gate_runs_actual_implementation(self):
        temporary, path = self.workspace(VALID_IMPLEMENTATION)
        with temporary:
            passed, output = _agentic_gate(path)
        self.assertTrue(passed, output)
        self.assertIn("agentic-self-check OK", output)

    def test_independent_gate_rejects_legal_action_that_crashes(self):
        broken = VALID_IMPLEMENTATION.replace(
            'if action != "finish": raise ValueError(action)',
            'raise ValueError("legal action crashed")',
        )
        temporary, path = self.workspace(broken)
        with temporary:
            passed, output = _agentic_gate(path)
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
