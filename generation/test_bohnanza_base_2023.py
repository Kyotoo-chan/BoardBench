from __future__ import annotations

import shutil
import unittest
from unittest.mock import patch

import generation.run_bohnanza_base_2023 as study


class BohnanzaBase2023StudyTests(unittest.TestCase):
    def test_frozen_manifest_hashes_match(self):
        manifest = study.load_manifest()
        self.assertEqual(manifest["runs"], ["base_pdf"])
        self.assertEqual(manifest["generation"]["runs"], 1)
        self.assertEqual(manifest["judging"]["judges_per_run"], 3)

    def test_generation_packet_has_only_source_and_neutral_contract_files(self):
        manifest = study.load_manifest()
        workspace, _ = study.make_workspace(manifest["conditions"]["base_pdf"])
        try:
            names = {path.name for path in workspace.iterdir() if path.is_file()}
            for required in ("game_rules.pdf", "ENVIRONMENT_CONTRACT.md", "GAME_PROFILE.json", "agentic_self_check.py", "profile_fixture_self_check.py", "TASK.txt", "SOURCE_MANIFEST.md"):
                self.assertIn(required, names)
            for hidden in ("rulefacts.md", "approved_rulefacts.md", "bohnanza_base_2023.json", "bohnanza_base_2023.py"):
                self.assertNotIn(hidden, names)
            self.assertNotIn("game_components.json", names)
            task = (workspace / "TASK.txt").read_text(encoding="utf-8")
            self.assertIn('"material": true', task)
            self.assertIn("profile_fixture_self_check.py", task)
            self.assertNotIn("IMPLEMENTATION_TASK.txt", task)
        finally:
            shutil.rmtree(workspace, ignore_errors=True)

    def test_single_run_is_sequential_and_resumable(self):
        manifest = study.load_manifest()
        progress = {"schema_version": 1, "completed": [], "judged": [], "failed": [], "updated_at": None}
        generated = []
        with patch.object(study, "load_manifest", return_value=manifest), patch.object(study, "state", return_value=progress), patch.object(study, "save"), patch.object(study, "generate_one", side_effect=lambda *args: generated.append(args[0])):
            self.assertEqual(study.run_phase("generate", None), 0)
        self.assertEqual(generated, ["base_pdf"])
        self.assertEqual(progress["completed"], ["base_pdf"])
        with patch.object(study, "load_manifest", return_value=manifest), patch.object(study, "state", return_value=progress), patch.object(study, "save"), patch.object(study, "generate_one") as generate:
            self.assertEqual(study.run_phase("generate", None), 0)
            generate.assert_not_called()

    def test_three_judges_are_sequential_and_resumable(self):
        manifest = study.load_manifest()
        progress = {"schema_version": 1, "completed": ["base_pdf"], "judged": [], "failed": [], "updated_at": None}
        judged = []
        with patch.object(study, "load_manifest", return_value=manifest), patch.object(study, "state", return_value=progress), patch.object(study, "save"), patch.object(study, "judge_one", side_effect=lambda condition, index: judged.append((condition, index))):
            self.assertEqual(study.run_phase("judge", None), 0)
        self.assertEqual(judged, [("base_pdf", 1), ("base_pdf", 2), ("base_pdf", 3)])
        self.assertEqual(progress["judged"], ["base_pdf_judge_1", "base_pdf_judge_2", "base_pdf_judge_3"])
        with patch.object(study, "load_manifest", return_value=manifest), patch.object(study, "state", return_value=progress), patch.object(study, "save"), patch.object(study, "judge_one") as judge:
            self.assertEqual(study.run_phase("judge", None), 0)
            judge.assert_not_called()


if __name__ == "__main__":
    unittest.main()
