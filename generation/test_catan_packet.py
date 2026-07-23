from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import unittest
from pathlib import Path

from checks.run_scenarios import load_suite

ROOT = Path(__file__).resolve().parents[1]
GAME_DIR = ROOT / "inputs/games/catan"
PROFILE_PATH = GAME_DIR / "environment_profile.json"
SUITE_PATH = ROOT / "checks/scenarios/catan.json"
ADAPTER_PATH = ROOT / "checks/scenario_adapters/catan.py"
MANIFEST_PATH = GAME_DIR / "experiment_manifest.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_evidence(source: object) -> None:
    if not isinstance(source, dict):
        raise AssertionError("evidence must be an object")
    page = source.get("page")
    pointer = source.get("json_pointer")
    if (isinstance(page, int) and page > 0) == (isinstance(pointer, str) and pointer.startswith("/")):
        raise AssertionError("evidence needs exactly one page or JSON Pointer")
    if not isinstance(source.get("source_id"), str) or not isinstance(source.get("quote"), str) or len(source["quote"].strip()) < 10:
        raise AssertionError("evidence needs source_id and direct quote")


class CatanPacketTests(unittest.TestCase):
    def setUp(self):
        self.profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        self.suite = load_suite(SUITE_PATH, ROOT)

    def test_assigned_sources_and_active_slots_match(self):
        expected = {
            "game_rules.pdf": "e0673fa93040f5b43908b215f52573878f586d26827d3a4f07c2ef8f8a947cf3",
            "game_almanac.pdf": "8fe89cc65308c08104a2b2afd2f8edae24e8c608383420b044a6f35cd2c611bc",
        }
        for name, digest in expected.items():
            self.assertEqual(sha256(GAME_DIR / name), digest)
            self.assertEqual((ROOT / "inputs" / name).read_bytes(), (GAME_DIR / name).read_bytes())

    def test_profile_topology_inventory_and_starting_resources(self):
        topology = self.profile["topology"]
        self.assertEqual(sum(map(len, topology["hex_rows"])), 19)
        self.assertEqual(len(topology["vertex_ids"]), 54)
        self.assertEqual(len(topology["edge_ids"]), 72)
        self.assertEqual(sum(self.profile["development_inventory"].values()), 25)
        starts = self.profile["fixed_beginner_setup"]["starting_resources"]
        self.assertEqual(starts[3], {"wood": 1, "brick": 0, "wool": 1, "grain": 0, "ore": 1})
        bank = {resource: 19 - sum(hand[resource] for hand in starts) for resource in self.profile["resource_ids"]}
        self.assertEqual(bank, {"wood": 15, "brick": 18, "wool": 18, "grain": 16, "ore": 16})

    def test_scenarios_are_cited_unique_and_resolved(self):
        facts = set(re.findall(r"\*\*(CAT-[A-Z0-9-]+)", (GAME_DIR / "rulefacts.md").read_text(encoding="utf-8")))
        ids = [scenario["id"] for scenario in self.suite["scenarios"]]
        self.assertEqual(len(ids), len(set(ids)))
        for scenario in self.suite["scenarios"]:
            validate_evidence(scenario["source"])
            for support in scenario.get("supporting_sources", []):
                validate_evidence(support)
            self.assertTrue(set(scenario["fact_ids"]) <= facts, scenario["id"])
        scored_facts = {fact for scenario in self.suite["scenarios"] for fact in scenario["fact_ids"]}
        self.assertNotIn("CAT-GAP-SHORTAGE", scored_facts)
        self.assertNotIn("CAT-GAP-RANDOM", scored_facts)

    def test_adapter_matches_profile_and_fixture_references(self):
        spec = importlib.util.spec_from_file_location("catan_adapter_test", ADAPTER_PATH)
        adapter = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(adapter)
        self.assertEqual(set(self.profile["action_data"]["type_ids"]), set(adapter.ACTION_ARGS))
        for action_type, args in adapter.ACTION_ARGS.items():
            self.assertEqual(set(self.profile["action_data"]["types"][action_type]), args)
        vertices = set(self.profile["topology"]["vertex_ids"])
        edges = set(self.profile["topology"]["edge_ids"])
        hexes = {entry["id"] for entry in self.profile["fixed_beginner_setup"]["hexes"]}
        for scenario in self.suite["scenarios"]:
            fixture = scenario.get("fixture", {})
            self.assertTrue(set(fixture.get("buildings", {})) <= vertices, scenario["id"])
            self.assertTrue(set(fixture.get("roads", {})) <= edges, scenario["id"])
            if "robber_hex" in fixture:
                self.assertIn(fixture["robber_hex"], hexes, scenario["id"])

    def test_manifest_hashes_current_packet(self):
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        entries = manifest["condition"]["sources"] + manifest["condition"]["excluded_candidates"] + list(manifest["infrastructure"].values())
        for entry in entries:
            self.assertEqual(sha256(ROOT / entry["path"]), entry["sha256"], entry["path"])


if __name__ == "__main__":
    unittest.main()
