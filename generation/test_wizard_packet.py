from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path

from checks.run_scenarios import load_suite

ROOT = Path(__file__).resolve().parents[1]
GAME_DIR = ROOT / "inputs/games/wizard"
RULES = GAME_DIR / "game_rules.pdf"
FACTS = GAME_DIR / "rulefacts.md"
PROFILE = GAME_DIR / "environment_profile.json"
RENDER_MANIFEST = GAME_DIR / "game_rules_render_manifest.json"
SUITE_PATH = ROOT / "checks/scenarios/wizard.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class WizardPacketTest(unittest.TestCase):
    def setUp(self) -> None:
        self.facts = FACTS.read_text(encoding="utf-8")
        self.profile = json.loads(PROFILE.read_text(encoding="utf-8"))
        self.suite = load_suite(SUITE_PATH, ROOT)

    def test_source_and_render_provenance(self) -> None:
        digest = "167254a64b0866266746833c0b98836db51c08171b5b96e25f7461d5bf3dee79"
        self.assertEqual(sha256(RULES), digest)
        manifest = json.loads(RENDER_MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(manifest["source_sha256"], digest)
        self.assertEqual(manifest["dpi"], 150)
        self.assertEqual([entry["page"] for entry in manifest["pages"]], [1, 2])
        self.assertTrue(all(re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]) for entry in manifest["pages"]))

    def test_facts_are_approved_and_scenarios_are_cited(self) -> None:
        self.assertIn("**status:** approved (2026-07-25)", self.facts)
        fact_ids = set(re.findall(r"\*\*(WIZ-[A-Z0-9-]+)", self.facts))
        scenario_ids = [scenario["id"] for scenario in self.suite["scenarios"]]
        self.assertEqual(len(scenario_ids), len(set(scenario_ids)))
        for scenario in self.suite["scenarios"]:
            self.assertTrue(set(scenario["fact_ids"]) <= fact_ids, scenario["id"])
            self.assertNotIn("WIZ-X-HOUSE-WIZARD", scenario["fact_ids"])
            self.assertNotIn("WIZ-X-HOUSE-BIDS", scenario["fact_ids"])

    def test_profile_freezes_base_contract(self) -> None:
        self.assertEqual(self.profile["default_num_players"], 4)
        self.assertEqual(self.profile["phase_ids"], ["choose_trump", "predict", "play", "terminal"])
        self.assertEqual(self.profile["action_data"]["type_ids"], ["choose_trump", "predict", "play_card"])
        self.assertEqual(len(self.profile["suit_ids"]), 4)
        self.assertEqual(self.profile["rank_ids"], list(range(1, 14)))

    def test_matrix_covers_first_wizard_and_keeps_variants_out(self) -> None:
        scenarios = {scenario["id"]: scenario for scenario in self.suite["scenarios"]}
        self.assertEqual(len(scenarios), 21)
        self.assertIn("WIZ-R10-first-wizard-wins-midgame", scenarios)
        self.assertIn("WIZ-R11-first-wizard-also-wins-final-round", scenarios)
        self.assertEqual(sum(item["basis"] == "clear" for item in scenarios.values()), 11)
        self.assertEqual(sum(item["basis"] == "human_decision" for item in scenarios.values()), 10)
        self.assertNotIn("plus_minus", self.profile["action_data"]["type_ids"])


if __name__ == "__main__":
    unittest.main()
