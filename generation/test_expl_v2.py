import json
import py_compile
import shutil
import unittest
from collections import Counter
from pathlib import Path

from checks.run_scenarios_v4 import load_suite
from checks.scenario_adapters import expl_v2 as adapter
from generation.run_hardened import build_workspace, load_config

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "inputs/games/expl"
CONFIG = GAME / "run_v2_original.json"
SUITE = ROOT / "checks/scenarios/expl_v2.json"
MATRIX = GAME / "scenario_matrix_v2.json"


class ExplodingKittensV2Tests(unittest.TestCase):
    def test_claims_matrix_and_executable_suite_are_in_sync(self):
        suite = load_suite(SUITE, ROOT)
        matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
        coverage = suite["claim_coverage"]
        self.assertEqual(matrix["status"], "approved-for-v2-original-packet")
        self.assertEqual(len(suite["scenarios"]), 38)
        self.assertEqual(sum(item["basis"] == "clear" for item in suite["scenarios"]), 34)
        self.assertEqual(sum(item["basis"] == "human_decision" for item in suite["scenarios"]), 4)
        self.assertEqual(len(coverage["required"]), 65)
        self.assertEqual(coverage["mapping_coverage"], 1.0)
        self.assertEqual(
            [(x["id"], x["basis"], x["fact_ids"]) for x in matrix["scenarios"]],
            [(x["id"], x["basis"], x["fact_ids"]) for x in suite["scenarios"]],
        )
        markdown = (GAME / "scenario_matrix_v2.md").read_text(encoding="utf-8")
        for item in matrix["scenarios"]:
            self.assertEqual(markdown.count(f"`{item['id']}`"), 1)
            self.assertIn(item["expectation"], markdown)
        py_compile.compile(str(ROOT / suite["adapter"]), doraise=True)

    def test_cat_single_and_nope_gaps_are_not_hard_scored(self):
        claims = {item["id"]: item for item in json.loads((GAME / "claims_v2.json").read_text(encoding="utf-8"))["claims"]}
        scenarios = json.loads(SUITE.read_text(encoding="utf-8"))["scenarios"]
        mapped = {claim_id for item in scenarios for claim_id in item["fact_ids"]}
        cat = claims["EXPL-C-CAT-SINGLE"]
        self.assertEqual(cat["classification"], "clear")
        self.assertFalse(cat["testable"])
        for claim_id in (
            "EXPL-M-NOPE-PRIORITY",
            "EXPL-M-NOPE-ANNOUNCEMENT",
            "EXPL-M-NOPE-EMPTY-RESTORE",
            "EXPL-A-FIVE-SELF-RETRIEVE",
            "EXPL-A-FIVE-KITTEN-SAFE",
            "EXPL-A-DEFUSE-OPTIONAL",
        ):
            self.assertNotIn(claim_id, mapped)

    def test_every_approved_human_scenario_has_an_exact_decision(self):
        decisions = json.loads((GAME / "decisions_v2.json").read_text(encoding="utf-8"))["decisions"]
        approved = {claim_id for item in decisions if item["status"] == "approved" for claim_id in item["claim_ids"]}
        suite = json.loads(SUITE.read_text(encoding="utf-8"))
        human = {claim_id for item in suite["scenarios"] if item["basis"] == "human_decision" for claim_id in item["fact_ids"]}
        self.assertEqual(human, approved)

    def test_adapter_fixture_conserves_pending_kitten(self):
        class FakeGame:
            @staticmethod
            def state_from_data(payload):
                return payload

            @staticmethod
            def state_to_data(state):
                return state

        state = adapter.setup(None, FakeGame(), {
            "hands": {"0": [], "1": ["nope"]},
            "deck": ["attack"],
            "discard": ["defuse"],
            "phase": "defuse_reinsert",
            "pending": {"type": "defuse", "actor": 0, "kitten": "exploding_kitten"},
        })
        self.assertEqual(Counter(adapter._cards(state["data"])), Counter(adapter.CARD_COUNTS))

    def test_original_packet_contains_only_pdf_profile_contract_and_fresh_renders(self):
        workspace, images, allowed, _immutable, renders = build_workspace(load_config(CONFIG))
        try:
            files = {path.relative_to(workspace).as_posix() for path in workspace.rglob("*") if path.is_file()}
            self.assertEqual(files, allowed)
            self.assertEqual(len(images), 2)
            self.assertEqual(set(renders), {"game_rules_pages/render_manifest.json"})
            self.assertIn("game_rules.pdf", allowed)
            self.assertIn("GAME_PROFILE.json", allowed)
            for excluded in (
                "claims_v2.json", "decisions_v2.json", "rulefacts_v2.md", "expl_v2.json",
                "expl_clarified.txt", "scenario_matrix_v2.json",
            ):
                self.assertNotIn(excluded, allowed)
        finally:
            shutil.rmtree(workspace, ignore_errors=True)

    def test_profile_and_manifest_are_frozen(self):
        profile = json.loads((GAME / "environment_profile_v2.json").read_text(encoding="utf-8"))
        manifest = json.loads((GAME / "game_rules_render_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(profile["player_counts"], {"supported": [2, 3, 4, 5], "unsupported": [1, 6]})
        self.assertEqual(profile["state_schema"], "boardbench/exploding-kittens/state/1")
        self.assertEqual(len(profile["card_ids"]), 13)
        self.assertEqual(manifest["source_sha256"], "f15c85be6345ff0101d01059509bc07e4989896f4f1927ace4248bba4ce1e853")
        self.assertEqual(manifest["dpi"], 150)
        self.assertEqual(len(manifest["pages"]), 2)


if __name__ == "__main__":
    unittest.main()
