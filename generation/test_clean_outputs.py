import tempfile
import unittest
from pathlib import Path

from generation.clean_outputs import clean_outputs, entries


class CleanOutputsTest(unittest.TestCase):
    def test_keeps_only_current_stem_and_gitkeep(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output_dir = Path(temporary)
            for name in (".gitkeep", "old.py", "wizard_codex_ag.py", "wizard_codex_ag.md"):
                (output_dir / name).write_text("", encoding="utf-8")
            (output_dir / "__pycache__").mkdir()

            removed = clean_outputs(output_dir, keep_stem="wizard_codex_ag", require_tracked=False)

            self.assertEqual(removed, ["__pycache__", "old.py"])
            self.assertEqual([path.name for path in entries(output_dir)], ["wizard_codex_ag.md", "wizard_codex_ag.py"])


if __name__ == "__main__":
    unittest.main()
