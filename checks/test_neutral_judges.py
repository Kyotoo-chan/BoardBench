import argparse
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from checks import run_neutral_judges as judges


class NeutralJudgePacketTests(unittest.TestCase):
    def test_optional_clarification_is_copied_and_attributed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = {name: root / name for name in ("rules.pdf", "facts.md", "claims.json", "code.py", "clarification.json")}
            for path in paths.values():
                path.write_text(path.name, encoding="utf-8")
            captured = {}

            def fake_run_codex(**kwargs):
                captured["manifest"] = json.loads((kwargs["cwd"] / "SOURCE_MANIFEST.json").read_text(encoding="utf-8"))
                captured["prompt"] = kwargs["prompt"]

            args = argparse.Namespace(
                stem="game", condition="clarified", scope="base", output_dir=root, raw_dir=root,
                rulebook=paths["rules.pdf"], rulefacts=paths["facts.md"], claims=paths["claims.json"], code=paths["code.py"],
                rulebook_source_id="RULES", rulefacts_source_id="FACTS", claims_source_id="CLAIMS",
                companion=None, companion_source_id=None, companion_role="publisher_companion",
                supplement=paths["clarification.json"], supplement_source_id="CLARIFICATION",
                supplement_role="experimenter_clarification", model="model", effort="medium",
            )
            with patch.object(judges, "render_pdf_pages", return_value=[]), patch.object(judges, "run_codex", side_effect=fake_run_codex):
                judges.judge(1, args)

            source = captured["manifest"]["sources"][-1]
            self.assertEqual((source["source_id"], source["role"], source["packet_name"]),
                             ("CLARIFICATION", "experimenter_clarification", "canonical_supplement.json"))
            self.assertIn("canonical_supplement.json", captured["prompt"])

    def test_companion_and_rulebook_pdfs_are_both_rendered(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = {name: root / name for name in ("rules.pdf", "almanac.pdf", "facts.md", "claims.json", "code.py")}
            for path in paths.values():
                path.write_text(path.name, encoding="utf-8")
            args = argparse.Namespace(
                stem="game", condition="original", scope="base", output_dir=root, raw_dir=root,
                rulebook=paths["rules.pdf"], rulefacts=paths["facts.md"], claims=paths["claims.json"], code=paths["code.py"],
                rulebook_source_id="RULES", rulefacts_source_id="FACTS", claims_source_id="CLAIMS",
                companion=paths["almanac.pdf"], companion_source_id="ALMANAC", companion_role="publisher_companion",
                supplement=None, supplement_source_id=None, supplement_role="experimenter_clarification",
                model="model", effort="medium",
            )
            rendered = []

            def fake_render(path, output, dpi):
                rendered.append((path.name, dpi))
                return []

            with patch.object(judges, "render_pdf_pages", side_effect=fake_render), patch.object(judges, "run_codex"):
                judges.judge(1, args)

            self.assertEqual(rendered, [("canonical_rulebook.pdf", 150), ("canonical_companion.pdf", 150)])


if __name__ == "__main__":
    unittest.main()
