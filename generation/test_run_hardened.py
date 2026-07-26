import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from generation import run_hardened


class HardenedRunnerTests(unittest.TestCase):
    def test_model_prompt_matches_assumptions_validator_vocabulary(self):
        prompt = (run_hardened.ROOT / "inputs/prompts/rulebook_to_python_v2.txt").read_text(encoding="utf-8")
        self.assertIn("`ambiguous`, `missing`, and `conflicting`", prompt)
        self.assertIn("`selected` value must exactly equal", prompt)
        self.assertNotIn("`contradictory`", prompt)

    def config(self, root: Path) -> dict:
        source = root / "source"
        source.mkdir()
        (source / "rules.txt").write_text("rules", encoding="utf-8")
        (root / "profile.json").write_text("{}", encoding="utf-8")
        (root / "fixture.py").write_text("raise SystemExit(0)\n", encoding="utf-8")
        return {
            "schema_version": 1,
            "game": "test_game",
            "run_id": "v2_original_1",
            "condition_kind": "original",
            "scope": "test base game only",
            "source_base_dir": str(source),
            "sources": [{
                "path": "rules.txt",
                "packet_name": "game_rules.txt",
                "role": "publisher_rulebook",
                "sha256": hashlib.sha256(b"rules").hexdigest(),
            }],
            "profile": str(root / "profile.json"),
            "profile_fixture_self_check": str(root / "fixture.py"),
            "max_repairs": 1,
            "output_stem": "test_game_codex_ag",
        }

    def test_assumptions_entries_are_schema_validated(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "assumptions.json"
            path.write_text(json.dumps({"version": 1, "assumptions": [{"id": "A"}]}), encoding="utf-8")
            self.assertIn("missing required fields", run_hardened.validate_assumptions(path))
            path.write_text(json.dumps({"version": 1, "assumptions": []}), encoding="utf-8")
            self.assertIsNone(run_hardened.validate_assumptions(path))

    def test_clarified_config_must_keep_paired_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = self.config(root)
            original_path = root / "original.json"
            original_path.write_text(json.dumps(original), encoding="utf-8")
            clarified_source = root / "clarified_source"
            clarified_source.mkdir()
            (clarified_source / "rules.txt").write_text("rules", encoding="utf-8")
            (clarified_source / "clarifications.json").write_text("{}", encoding="utf-8")
            evidence_path = root / "original_agentic.json"
            evidence_path.write_text(json.dumps({
                "success": True,
                "condition_kind": "original",
                "game": original["game"],
                "run_config_sha256": run_hardened.config_digest(original),
                "calls": [{"model_packet_sha256": {
                    "TASK.txt": run_hardened.sha256(run_hardened.ROOT / "inputs/prompts/rulebook_to_python.txt")
                }}],
            }), encoding="utf-8")
            clarified = {
                **original,
                "run_id": "v2_clarified_1",
                "condition_kind": "clarified",
                "source_base_dir": str(clarified_source),
                "original_run_config": str(original_path),
                "original_evidence": str(evidence_path),
                "sources": [
                    original["sources"][0],
                    {
                        "path": "clarifications.json", "packet_name": "clarifications.json",
                        "role": "experimenter_clarification",
                        "sha256": hashlib.sha256(b"{}").hexdigest(),
                    },
                ],
            }
            paired, evidence = run_hardened.original_pair(clarified, require_frozen=False)
            self.assertEqual(paired["run_id"], "v2_original_1")
            self.assertTrue(evidence["success"])
            clarified["effort"] = "medium"
            with self.assertRaisesRegex(ValueError, "paired setting"):
                run_hardened.original_pair(clarified, require_frozen=False)

    def test_runner_uses_exact_repair_allowlists_and_preserves_one_run(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outputs = root / "outputs"
            outputs.mkdir()
            config = self.config(root)
            calls = []

            def fake_codex(**kwargs):
                calls.append(set(kwargs["packet_files"]))
                workspace = kwargs["cwd"]
                (workspace / "implementation.py").write_text("# implementation\n", encoding="utf-8")
                if len(calls) == 1:
                    (workspace / ".git").mkdir()
                    (workspace / ".git/config").write_text("internal", encoding="utf-8")
                    (workspace / "__pycache__").mkdir()
                    (workspace / "__pycache__/implementation.pyc").write_bytes(b"cache")
                if len(calls) == 2:
                    self.assertFalse((workspace / ".git").exists())
                    self.assertFalse((workspace / "__pycache__").exists())
                    (workspace / "rule_coverage.md").write_text("covered\n", encoding="utf-8")
                    (workspace / "assumptions.json").write_text(json.dumps({"version": 1, "assumptions": []}), encoding="utf-8")
                kwargs["response_path"].write_text("response", encoding="utf-8")
                kwargs["events_path"].write_text('{"type":"done"}\n', encoding="utf-8")
                return {"model_packet_sha256": {name: "hash" for name in kwargs["packet_files"]}}

            gate_results = iter([(False, "missing artifacts"), (True, "all checks pass")])

            def fake_gate(workspace):
                result = next(gate_results)
                if not result[0]:
                    (workspace / "__pycache__").mkdir(exist_ok=True)
                    (workspace / "__pycache__/host.pyc").write_bytes(b"cache")
                return result

            with mock.patch.object(run_hardened, "OUTPUTS", outputs), mock.patch.object(
                run_hardened, "run_codex", side_effect=fake_codex
            ), mock.patch.object(run_hardened, "gate", side_effect=fake_gate):
                self.assertTrue(run_hardened.run(config))

            self.assertNotIn("implementation.py", calls[0])
            self.assertIn("implementation.py", calls[1])
            self.assertNotIn("rule_coverage.md", calls[1])
            self.assertTrue((outputs / "test_game_codex_ag.py").is_file())
            evidence = json.loads((outputs / "test_game_codex_ag_agentic.json").read_text(encoding="utf-8"))
            self.assertEqual(evidence["run_id"], "v2_original_1")
            self.assertEqual(evidence["repair_count"], 1)
            checks = (outputs / "test_game_codex_ag_checks.txt").read_text(encoding="utf-8")
            self.assertIn("removed runtime metadata", checks)
            self.assertIn(".git, __pycache__", checks)

    def test_launch_failure_preserves_prior_attempt_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outputs = root / "outputs"
            outputs.mkdir()
            config = self.config(root)
            count = 0

            def fake_codex(**kwargs):
                nonlocal count
                count += 1
                if count == 2:
                    raise ValueError("unexpected model file")
                workspace = kwargs["cwd"]
                (workspace / "implementation.py").write_text("# partial\n", encoding="utf-8")
                kwargs["response_path"].write_text("first response", encoding="utf-8")
                kwargs["events_path"].write_text('{"type":"first"}\n', encoding="utf-8")
                return {"model_packet_sha256": {}}

            with mock.patch.object(run_hardened, "OUTPUTS", outputs), mock.patch.object(
                run_hardened, "run_codex", side_effect=fake_codex
            ), mock.patch.object(run_hardened, "gate", return_value=(False, "repair needed")):
                with self.assertRaisesRegex(ValueError, "unexpected model file"):
                    run_hardened.run(config)

            evidence = json.loads((outputs / "test_game_codex_ag_agentic.json").read_text(encoding="utf-8"))
            self.assertFalse(evidence["success"])
            self.assertIn("first response", (outputs / "test_game_codex_ag.md").read_text(encoding="utf-8"))
            self.assertIn("launch failure", (outputs / "test_game_codex_ag_checks.txt").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
