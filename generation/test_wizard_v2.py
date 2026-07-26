import json
import shutil
import unittest
from pathlib import Path

from checks.run_scenarios_v4 import load_suite
from generation.run_hardened import build_workspace, load_config
from generation.source_condition import validate_pair

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "inputs/games/wizard"
CONFIG = GAME / "run_v2_original.json"
CLARIFIED_CONFIG = GAME / "run_v2_clarified.json"
SUITE = ROOT / "checks/scenarios/wizard_v2.json"


class WizardV2Tests(unittest.TestCase):
    def test_atomic_claim_and_player_count_coverage_is_frozen(self):
        suite = load_suite(SUITE, ROOT)
        claims = suite["claim_coverage"]
        self.assertEqual(len(suite["scenarios"]), 34)
        self.assertEqual(len(claims["required"]), 50)
        self.assertEqual(claims["mapping_coverage"], 1.0)
        key = next(item for item in suite["scenarios"] if item["id"] == "WIZ-R28-wizard-lead-keeps-all-cards-legal")
        self.assertEqual(key["basis"], "clear")
        self.assertEqual(key["fact_ids"], ["WIZ-C-WIZARD-LEAD-FREE"])
        profile = json.loads((GAME / "environment_profile_v2.json").read_text(encoding="utf-8"))
        self.assertEqual(profile["player_counts"], {"supported": [3, 4, 5, 6], "unsupported": [2, 7]})

    def test_clarification_is_separate_and_does_not_change_publisher_source(self):
        original = load_config(CONFIG)["sources"]
        clarification_path = GAME / "clarifications_v2.json"
        clarification = json.loads(clarification_path.read_text(encoding="utf-8"))
        self.assertEqual(len(clarification["clarifications"]), 7)
        self.assertTrue(all(item["claim_ids"] for item in clarification["clarifications"]))
        clarified = original + [{
            "source_id": "WIZARD-V2-CLARIFICATIONS",
            "path": clarification_path.name,
            "packet_name": clarification_path.name,
            "role": "experimenter_clarification",
            "sha256": "aabb56f76253b565063e325fcf83debbcce0c8037a8a6ea26814bb3924fdff83",
        }]
        validate_pair(original, clarified, GAME, GAME)

    def test_clarified_packet_adds_only_attributed_clarification(self):
        workspace, _images, allowed, _immutable, _renders = build_workspace(load_config(CLARIFIED_CONFIG))
        try:
            self.assertIn("clarifications_v2.json", allowed)
            self.assertNotIn("claims_v2.json", allowed)
            self.assertNotIn("wizard_v2.json", allowed)
            self.assertNotIn("rulefacts_v2.md", allowed)
        finally:
            shutil.rmtree(workspace, ignore_errors=True)

    def test_original_model_packet_is_exact_and_rendered(self):
        config = load_config(CONFIG)
        workspace, images, allowed, _immutable, renders = build_workspace(config)
        try:
            self.assertEqual(len(images), 2)
            self.assertEqual(set(renders), {"game_rules_pages/render_manifest.json"})
            self.assertEqual({path.relative_to(workspace).as_posix() for path in workspace.rglob("*") if path.is_file()}, allowed)
            self.assertNotIn("claims_v2.json", allowed)
            self.assertNotIn("wizard_v2.json", allowed)
            self.assertNotIn("rulefacts_v2.md", allowed)
        finally:
            shutil.rmtree(workspace, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
