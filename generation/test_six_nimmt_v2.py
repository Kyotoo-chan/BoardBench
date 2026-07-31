import hashlib
import json
import py_compile
import re
import shutil
import unittest
from pathlib import Path

from checks.run_scenarios_v4 import load_suite
from generation.run_hardened import build_workspace, load_config

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "inputs/games/6_nimmt"
CONFIG = GAME / "run_v2_original.json"
SUITE = ROOT / "checks/scenarios/six_nimmt_v2.json"
MATRIX = GAME / "scenario_matrix_v2.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SixNimmtV2PacketTests(unittest.TestCase):
    def test_profile_is_finite_representation_only(self):
        profile = load(GAME / "environment_profile_v2.json")
        self.assertEqual(
            (profile["state_schema"], profile["action_schema"], profile["observation_schema"]),
            ("boardbench/six-nimmt/state/2", "boardbench/six-nimmt/action/2", "boardbench/six-nimmt/observation/2"),
        )
        self.assertEqual(profile["player_counts"]["supported"], list(range(2, 11)))
        self.assertEqual(set(profile["action_data"]["types"]), {"commit_card", "choose_row"})
        self.assertEqual(set(profile["action_data"]["types"]["commit_card"]), {"card"})
        self.assertEqual(set(profile["action_data"]["types"]["choose_row"]), {"row"})
        text = json.dumps(profile).lower()
        for hidden_behavior in ("strictly_greater", "all zeros", "copies_each", "multiples_of_10", '"55": 7'):
            self.assertNotIn(hidden_behavior, text)
        self.assertIn("card_bullheads", profile["state_data"]["required"])
        self.assertIn("card_bullheads", profile["observation_data"]["required"])

    def test_suite_exactly_matches_approved_matrix(self):
        suite = load_suite(SUITE, ROOT)
        matrix = load(MATRIX)
        self.assertEqual(matrix["status"], "approved")
        self.assertEqual(len(suite["scenarios"]), 33)
        self.assertEqual(sum(len(s["cases"]) for s in suite["scenarios"]), 74)
        self.assertEqual(len(suite["claim_coverage"]["required"]), 30)
        self.assertEqual(suite["claim_coverage"]["mapping_coverage"], 1.0)
        self.assertEqual(suite["claim_coverage"]["coverage_exceptions"], [])
        fields = ("id", "basis", "fact_ids", "title", "expectation", "source")
        self.assertEqual(
            [tuple(s[field] for field in fields) for s in suite["scenarios"]],
            [tuple(s[field] for field in fields) for s in matrix["scenarios"]],
        )
        self.assertEqual(
            [s.get("supporting_sources", []) for s in suite["scenarios"]],
            [s.get("supporting_sources", []) for s in matrix["scenarios"]],
        )
        self.assertEqual(
            [len(s["cases"]) for s in suite["scenarios"]],
            [s["planned_named_cases"] for s in matrix["scenarios"]],
        )

    def test_component_facts_never_enter_clear_basis(self):
        suite = load(SUITE)
        for scenario in suite["scenarios"]:
            sources = [scenario["source"], *scenario.get("supporting_sources", [])]
            if scenario["basis"] == "clear":
                self.assertFalse(any(source["source_id"] == "6NIMMT-V2-COMPONENTS" for source in sources), scenario["id"])
                self.assertFalse(any(fact.startswith("6N-M-") for fact in scenario["fact_ids"]), scenario["id"])
        inventory = next(s for s in suite["scenarios"] if s["id"] == "6N-R11-card-inventory")
        self.assertEqual(inventory["basis"], "human_decision")
        self.assertEqual(inventory["fact_ids"], ["6N-M-CARD-IDENTITIES", "6N-M-BULL-INVENTORY"])

    def test_decisions_link_every_material_testable_gap(self):
        claims = load(GAME / "claims_v2.json")["claims"]
        decisions = load(GAME / "decisions_v2.json")["decisions"]
        linked = {claim for decision in decisions for claim in decision["claim_ids"]}
        known = {claim["id"] for claim in claims}
        gaps = {
            claim["id"]
            for claim in claims
            if claim["classification"] in {"ambiguous", "missing", "conflicting"} and claim["material"] and claim["testable"]
        }
        self.assertTrue(all(decision["claim_ids"] for decision in decisions))
        self.assertLessEqual(linked, known)
        self.assertLessEqual(gaps, linked)

    def test_markdown_fact_ids_are_synchronized(self):
        matrix = load(MATRIX)
        rows = {}
        for line in (GAME / "scenario_matrix_v2.md").read_text(encoding="utf-8").splitlines():
            if line.startswith("| `6N-"):
                parts = [part.strip() for part in line.split("|")]
                rows[parts[1].strip("`")] = re.findall(r"`(6N-[^`]+)`", parts[4])
        self.assertEqual(len(rows), len(matrix["scenarios"]))
        for scenario in matrix["scenarios"]:
            self.assertEqual(rows[scenario["id"]], scenario["fact_ids"], scenario["id"])

    def test_adapter_is_contract_v2_only_and_files_compile(self):
        adapter = ROOT / "checks/scenario_adapters/six_nimmt_v2.py"
        fixture = GAME / "profile_fixture_self_check_v2.py"
        py_compile.compile(str(adapter), doraise=True)
        py_compile.compile(str(fixture), doraise=True)
        text = adapter.read_text(encoding="utf-8")
        self.assertIn("boardbench/six-nimmt/state/2", text)
        self.assertIn("game.state_to_data", text)
        self.assertIn("game.state_from_data", text)
        self.assertNotIn("state.data", text)
        self.assertNotIn("state.__dict__", text)
        self.assertNotIn("all_remaining_values", text)

    def test_original_augmented_packet_exact_allowlist(self):
        config = load_config(CONFIG)
        workspace, images, allowed, _immutable, renders = build_workspace(config)
        try:
            self.assertEqual(len(images), 2)
            self.assertEqual(set(renders), {"game_rules_pages/render_manifest.json"})
            self.assertEqual({source["role"] for source in config["sources"]}, {"publisher_rulebook", "user_observation"})
            for present in (
                "game_rules.pdf",
                "game_components.json",
                "GAME_PROFILE.json",
                "agentic_self_check.py",
                "profile_fixture_self_check.py",
                "TASK.txt",
                "SOURCE_MANIFEST.json",
            ):
                self.assertIn(present, allowed)
            for hidden in ("claims_v2.json", "decisions_v2.json", "scenario_matrix_v2.json", "six_nimmt_v2.json"):
                self.assertNotIn(hidden, allowed)
        finally:
            shutil.rmtree(workspace, ignore_errors=True)

    def test_frozen_manifest_hashes_match(self):
        manifest = load(GAME / "experiment_manifest_v2.json")
        self.assertEqual(manifest["status"], "frozen-pre-generation")
        self.assertEqual(manifest["evaluation"]["status"], "not_run")
        self.assertEqual(
            (manifest["evaluation"]["scenarios"], manifest["evaluation"]["named_cases"], manifest["evaluation"]["required_clear_claims"]),
            (33, 74, 30),
        )
        for item in manifest["condition"]["sources"]:
            self.assertEqual(sha(ROOT / item["path"]), item["sha256"], item["source_id"])
        for name, item in manifest["artifacts"].items():
            if name != "packet_test":
                self.assertEqual(sha(ROOT / item["path"]), item["sha256"], name)


if __name__ == "__main__":
    unittest.main()
