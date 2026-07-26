from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from checks.run_scenarios import run_suite

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "inputs/games/bohnanza_base_2023/game_rules.pdf"
FACTS = ROOT / "inputs/games/bohnanza_base_2023/rulefacts.md"
PROFILE = ROOT / "inputs/games/bohnanza_base_2023/environment_profile.json"
SUITE = ROOT / "checks/scenarios/bohnanza_base_2023.json"
ADAPTER = ROOT / "checks/scenario_adapters/bohnanza_base_2023.py"
PROBE = ROOT / "checks/fixtures/bohnanza_base_2023_contract_probe.py"
POSTHOC_SUITE = ROOT / "checks/scenarios/bohnanza_base_2023_posthoc_v2.json"
POSTHOC_ADAPTER = ROOT / "checks/scenario_adapters/bohnanza_base_2023_posthoc_v2.py"
COMPARISON_SUITE = ROOT / "checks/scenarios/bohnanza_base_2023_comparison_v4.json"
ORIGINAL_IMPLEMENTATION = ROOT / "results/scores/bohnanza_base_2023/base_pdf_1/runs/base_pdf/bohnanza_base_2023_codex_ag.py"


class BohnanzaBase2023Tests(unittest.TestCase):
    def test_frozen_source_and_base_inventory(self):
        self.assertEqual(hashlib.sha256(RULES.read_bytes()).hexdigest(), "e59f7a7d77ed2f052cdf46403b797a1d418996664dc1e3ae9baf7e498b727655")
        profile = json.loads(PROFILE.read_text(encoding="utf-8"))
        self.assertEqual(profile["bean_ids"], ["gartenbohne", "rote_bohne", "augenbohne", "sojabohne", "brechbohne", "saubohne", "feuerbohne", "blaue_bohne"])

    def test_approved_facts_and_citations(self):
        self.assertIn("status:** approved", FACTS.read_text(encoding="utf-8"))
        suite = json.loads(SUITE.read_text(encoding="utf-8"))
        self.assertEqual(len(suite["scenarios"]), 31)
        for scenario in suite["scenarios"]:
            self.assertIn(scenario["basis"], ("clear", "human_decision"))
            self.assertEqual(scenario["source"]["source_id"], "BOHN-BASE-RULES")
            self.assertGreater(scenario["source"]["page"], 0)
            self.assertTrue(scenario["source"]["quote"])
        text = SUITE.read_text(encoding="utf-8").lower()
        for obsolete in ("acker", "weinbrand", "kaffee", "kakao", "157"):
            self.assertNotIn(obsolete, text)

    def test_adapter_uses_only_contract_and_public_api(self):
        source = ADAPTER.read_text(encoding="utf-8")
        for forbidden in ("vars(module)", "is_dataclass", "hasattr(state", "getattr(state", "action[0]", "action[-1]"):
            self.assertNotIn(forbidden, source)

    def test_every_scenario_is_representable(self):
        for suite in (SUITE, POSTHOC_SUITE, COMPARISON_SUITE):
            result = run_suite(PROBE, suite)
            self.assertEqual(result["counts"]["CRASH"], 0)
            self.assertEqual(result["counts"]["UNTESTABLE"], 0)

    def test_expanded_comparison_baseline_is_frozen(self):
        suite = json.loads(COMPARISON_SUITE.read_text(encoding="utf-8"))
        self.assertEqual(len(suite["scenarios"]), 41)
        self.assertIn("comparison-v4", suite["rubric_version"])
        result = run_suite(ORIGINAL_IMPLEMENTATION, COMPARISON_SUITE)
        self.assertEqual(result["counts"], {"PASS": 34, "FAIL": 7, "CRASH": 0, "UNREACHED": 0, "UNTESTABLE": 0})

    def test_posthoc_corrections_are_separately_labelled(self):
        suite = json.loads(POSTHOC_SUITE.read_text(encoding="utf-8"))
        self.assertIn("posthoc-v2", suite["rubric_version"])
        self.assertEqual(Path(suite["adapter"]).resolve(), POSTHOC_ADAPTER.resolve())


if __name__ == "__main__":
    unittest.main()
