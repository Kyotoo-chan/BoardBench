import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from generation.pdf_pages import render_pdf_pages


ROOT = Path(__file__).resolve().parents[1]


class PdfPagesTest(unittest.TestCase):
    def test_complete_render_has_reproducibility_manifest(self) -> None:
        source = ROOT / "inputs/games/catan/game_almanac.pdf"
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            pages = render_pdf_pages(source, output, dpi=24)
            manifest = json.loads((output / "render_manifest.json").read_text(encoding="utf-8"))

            self.assertEqual(len(pages), 24)
            self.assertEqual([int(path.stem.rsplit("-", 1)[1]) for path in pages], list(range(1, 25)))
            self.assertEqual(manifest["source_sha256"], hashlib.sha256(source.read_bytes()).hexdigest())
            self.assertEqual(manifest["dpi"], 24)
            self.assertEqual(len(manifest["pages"]), len(pages))
            for number, (page, entry) in enumerate(zip(pages, manifest["pages"]), start=1):
                self.assertEqual(entry["page"], number)
                self.assertEqual(entry["file"], page.name)
                self.assertEqual(entry["sha256"], hashlib.sha256(page.read_bytes()).hexdigest())
            self.assertTrue(manifest["renderer_version"])


if __name__ == "__main__":
    unittest.main()
