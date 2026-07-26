import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from generation.source_condition import (
    validate_packet_files,
    validate_packet_sources,
    validate_pair,
    validate_pdf_renders,
    validate_sources,
)


def source(name, role, content=b"rules"):
    return {"path": name, "packet_name": name, "role": role, "sha256": hashlib.sha256(content).hexdigest()}


class SourceConditionTests(unittest.TestCase):
    def test_original_rejects_clarification_leak(self):
        values = [source("game_rules.pdf", "publisher_rulebook"), source("clarifications.json", "experimenter_clarification")]
        with self.assertRaisesRegex(ValueError, "clarification count"):
            validate_sources("original", values)

    def test_clarified_pair_keeps_original_sources_byte_identical(self):
        original = [source("game_rules.pdf", "publisher_rulebook")]
        clarified = original + [source("clarifications.json", "experimenter_clarification", b"clarify")]
        validate_pair(original, clarified)
        changed = [source("game_rules.pdf", "publisher_rulebook", b"rewritten"), clarified[1]]
        with self.assertRaisesRegex(ValueError, "changed a non-clarification source"):
            validate_pair(original, changed)

    def test_hashes_and_exact_packet_files_are_checked(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "game_rules.pdf").write_bytes(b"rules")
            values = [source("game_rules.pdf", "publisher_rulebook")]
            validate_sources("original", values, root)
            validate_packet_files(root, {"game_rules.pdf"})
            outside = root.parent / "outside-rules.pdf"
            outside.write_bytes(b"rules")
            escaped = [{**values[0], "path": "../outside-rules.pdf"}]
            with self.assertRaisesRegex(ValueError, "escapes base directory"):
                validate_sources("original", escaped, root)
            outside.unlink()
            (root / "checks.json").write_text("leak", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "extra=.*checks.json"):
                validate_packet_files(root, {"game_rules.pdf"})

    def test_packet_source_bytes_and_pdf_renders_are_coupled(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rules = root / "game_rules.pdf"
            rules.write_bytes(b"rules")
            values = [source("game_rules.pdf", "publisher_rulebook")]
            hashes = validate_packet_files(root, {"game_rules.pdf"})
            validate_packet_sources(hashes, values)
            with self.assertRaisesRegex(ValueError, "source mismatch"):
                validate_packet_sources({"game_rules.pdf": "0" * 64}, values)

            pages = root / "game_rules_pages"
            pages.mkdir()
            image = pages / "page-001.png"
            image.write_bytes(b"image")
            manifest = {
                "source_file": "game_rules.pdf",
                "source_sha256": values[0]["sha256"],
                "dpi": 150,
                "renderer": "test",
                "renderer_version": "1",
                "pages": [{"page": 1, "file": image.name, "sha256": hashlib.sha256(b"image").hexdigest()}],
            }
            (pages / "render_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            validate_pdf_renders(root, values, [image])
            manifest["dpi"] = 149
            (pages / "render_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "source or DPI"):
                validate_pdf_renders(root, values, [image])


if __name__ == "__main__":
    unittest.main()
