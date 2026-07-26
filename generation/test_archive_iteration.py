import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from generation import archive_iteration


class ArchiveIterationTests(unittest.TestCase):
    def test_compact_condition_prefix_and_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outputs = root / "outputs"
            results = root / "results"
            outputs.mkdir()
            (outputs / "game_codex_ag.py").write_text("code", encoding="utf-8")
            (outputs / "game_codex_ag_events.jsonl").write_text("{}\n", encoding="utf-8")
            with mock.patch.object(archive_iteration, "OUTPUTS", outputs), mock.patch.object(
                archive_iteration, "RESULTS", results
            ):
                destination = archive_iteration.archive("game", "v2", "original", "game_codex_ag")
            self.assertTrue((destination / "original.py").is_file())
            self.assertTrue((destination / "raw/original_events.jsonl").is_file())
            manifest = json.loads((destination / "iteration_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(set(manifest["conditions"]), {"original"})
            (outputs / "game_codex_ag_checks.txt").write_text("late", encoding="utf-8")
            with mock.patch.object(archive_iteration, "OUTPUTS", outputs), mock.patch.object(
                archive_iteration, "RESULTS", results
            ):
                with self.assertRaisesRegex(FileExistsError, "different artifact set"):
                    archive_iteration.archive("game", "v2", "original", "game_codex_ag")
            self.assertFalse((destination / "original_checks.txt").exists())


if __name__ == "__main__":
    unittest.main()
