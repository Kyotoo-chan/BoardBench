from __future__ import annotations

import shutil
import unittest
from unittest.mock import patch

import generation.run_bohnanza_base_2023_clarified as study


class BohnanzaBase2023ClarifiedStudyTests(unittest.TestCase):
    def test_frozen_manifest_and_original_baseline(self):
        manifest = study.load_manifest()
        self.assertEqual(manifest["runs"], ["clarified"])
        self.assertEqual(manifest["generation"]["runs"], 1)
        self.assertEqual(manifest["judging"]["judges_per_run"], 3)
        self.assertNotIn("original_frozen_baseline", manifest["comparison"])

    def test_packet_contains_only_assigned_sources_and_neutral_contract(self):
        manifest = study.load_manifest()
        workspace, _ = study.make_workspace(manifest["conditions"]["clarified"])
        try:
            names = {path.name for path in workspace.iterdir() if path.is_file()}
            self.assertEqual(names, {
                "game_rules.pdf", "clarifications.json", "ENVIRONMENT_CONTRACT.md",
                "GAME_PROFILE.json", "agentic_self_check.py", "profile_fixture_self_check.py",
                "TASK.txt", "SOURCE_MANIFEST.md",
            })
            task = (workspace / "TASK.txt").read_text(encoding="utf-8")
            self.assertIn('"material": true', task)
            self.assertIn("profile_fixture_self_check.py", task)
            source_manifest = (workspace / "SOURCE_MANIFEST.md").read_text(encoding="utf-8")
            self.assertIn("experimenter_clarification", source_manifest)
            self.assertIn("four explicitly identified", source_manifest)
        finally:
            shutil.rmtree(workspace, ignore_errors=True)

    def test_single_run_is_sequential_and_resumable(self):
        manifest = study.load_manifest()
        progress = {"schema_version": 1, "completed": [], "judged": [], "failed": [], "updated_at": None}
        generated = []
        with patch.object(study, "load_manifest", return_value=manifest), patch.object(study, "state", return_value=progress), patch.object(study, "save"), patch.object(study, "generate_one", side_effect=lambda *args: generated.append(args[0])):
            self.assertEqual(study.run_phase("generate", None), 0)
        self.assertEqual(generated, ["clarified"])
        self.assertEqual(progress["completed"], ["clarified"])
        with patch.object(study, "load_manifest", return_value=manifest), patch.object(study, "state", return_value=progress), patch.object(study, "save"), patch.object(study, "generate_one") as generate:
            self.assertEqual(study.run_phase("generate", None), 0)
            generate.assert_not_called()

    def test_three_judges_are_sequential_and_resumable(self):
        manifest = study.load_manifest()
        progress = {"schema_version": 1, "completed": ["clarified"], "judged": [], "failed": [], "updated_at": None}
        judged = []
        with patch.object(study, "load_manifest", return_value=manifest), patch.object(study, "state", return_value=progress), patch.object(study, "save"), patch.object(study, "judge_one", side_effect=lambda condition, index: judged.append((condition, index))):
            self.assertEqual(study.run_phase("judge", None), 0)
        self.assertEqual(judged, [("clarified", 1), ("clarified", 2), ("clarified", 3)])
        self.assertEqual(progress["judged"], ["clarified_judge_1", "clarified_judge_2", "clarified_judge_3"])
        with patch.object(study, "load_manifest", return_value=manifest), patch.object(study, "state", return_value=progress), patch.object(study, "save"), patch.object(study, "judge_one") as judge:
            self.assertEqual(study.run_phase("judge", None), 0)
            judge.assert_not_called()


if __name__ == "__main__":
    unittest.main()
