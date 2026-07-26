import json
import shutil
import unittest
from pathlib import Path

from checks.run_scenarios_v4 import load_suite
from generation.run_hardened import build_workspace, load_config

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "inputs/games/abalone"
CONFIG = GAME / "run_v2_original.json"
EMPHASIS_CONFIG = GAME / "run_v2_setup_emphasis.json"
SUITE = ROOT / "checks/scenarios/abalone_v2.json"


class AbaloneV2Tests(unittest.TestCase):
    def test_claim_and_scenario_matrix_is_complete(self):
        suite = load_suite(SUITE, ROOT)
        coverage = suite["claim_coverage"]
        self.assertEqual(len(suite["scenarios"]), 38)
        self.assertEqual(len(coverage["required"]), 33)
        self.assertEqual(coverage["mapping_coverage"], 1.0)
        profile = json.loads((GAME / "environment_profile_v2.json").read_text(encoding="utf-8"))
        self.assertEqual(profile["player_counts"], {"supported": [2], "unsupported": [1, 3]})
        player_probe = next(item for item in suite["scenarios"] if item["id"] == "ABAL-R24-player-count-and-bounded-playability")
        self.assertEqual(player_probe["initial"]["adapter"]["player_count_probe"]["exception"], "ValueError")

    def test_original_packet_excludes_evaluator_and_clarification(self):
        workspace, images, allowed, _immutable, renders = build_workspace(load_config(CONFIG))
        try:
            self.assertEqual(len(images), 4)
            self.assertEqual(set(renders), {"game_rules_pages/render_manifest.json"})
            self.assertEqual({path.relative_to(workspace).as_posix() for path in workspace.rglob("*") if path.is_file()}, allowed)
            self.assertNotIn("claims_v2.json", allowed)
            self.assertNotIn("abalone_v2.json", allowed)
            self.assertNotIn("rulefacts_v2.md", allowed)
            self.assertNotIn("decisions_v2.json", allowed)
        finally:
            shutil.rmtree(workspace, ignore_errors=True)

    def test_setup_emphasis_is_paired_but_not_mislabelled_as_gap_clarification(self):
        config = load_config(EMPHASIS_CONFIG)
        self.assertEqual(config["intervention_kind"], "clear_rule_emphasis")
        workspace, _images, allowed, _immutable, _renders = build_workspace(config)
        try:
            self.assertIn("setup_emphasis_v2.json", allowed)
            self.assertNotIn("decisions_v2.json", allowed)
            self.assertNotIn("claims_v2.json", allowed)
            emphasis = json.loads((workspace / "setup_emphasis_v2.json").read_text(encoding="utf-8"))
            self.assertEqual(emphasis["intervention_kind"], "clear_rule_emphasis")
            self.assertIn("not a source-gap clarification", emphasis["authorship"])
        finally:
            shutil.rmtree(workspace, ignore_errors=True)

    def test_every_evaluator_decision_resolves_a_gap_claim(self):
        claims = {item["id"]: item for item in json.loads((GAME / "claims_v2.json").read_text(encoding="utf-8"))["claims"]}
        decisions = json.loads((GAME / "decisions_v2.json").read_text(encoding="utf-8"))["decisions"]
        self.assertEqual(len(decisions), 7)
        for item in decisions:
            self.assertTrue(item["claim_ids"])
            self.assertTrue(all(claims[claim_id]["classification"] != "clear" for claim_id in item["claim_ids"]))


if __name__ == "__main__":
    unittest.main()
