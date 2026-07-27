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
                supplement=paths["clarification.json"], supplement_source_id="CLARIFICATION",
                supplement_role="experimenter_clarification", model="model", effort="medium",
            )
            with patch.object(judges, "render_pdf_pages", return_value=[]), patch.object(judges, "run_codex", side_effect=fake_run_codex):
                judges.judge(1, args)

            source = captured["manifest"]["sources"][-1]
            self.assertEqual((source["source_id"], source["role"], source["packet_name"]),
                             ("CLARIFICATION", "experimenter_clarification", "canonical_supplement.json"))
            self.assertIn("canonical_supplement.json", captured["prompt"])


if __name__ == "__main__":
    unittest.main()
