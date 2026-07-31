import hashlib
import json
import unittest
from pathlib import Path

from checks.run_scenarios_v4_r2 import load_suite

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "inputs/games/6_nimmt"
BASE = ROOT / "checks/scenarios/six_nimmt_v2.json"
REVISED = ROOT / "checks/scenarios/six_nimmt_v2_r2.json"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SixNimmtEvaluatorR2Tests(unittest.TestCase):
    def test_revision_preserves_approved_matrix(self):
        suite = load_suite(REVISED, ROOT)
        matrix = load(GAME / "scenario_matrix_v2.json")
        self.assertEqual(suite["game_kwargs"], {"num_players": 4})
        self.assertEqual(len(suite["scenarios"]), 33)
        self.assertEqual(sum(len(s["cases"]) for s in suite["scenarios"]), 74)
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
        self.assertEqual(len(suite["claim_coverage"]["required"]), 30)
        self.assertEqual(suite["claim_coverage"]["mapping_coverage"], 1.0)

    def test_revision_manifest_hashes_and_invalid_replays(self):
        revision = load(GAME / "evaluator_revision_v2_r2.json")
        self.assertEqual(revision["status"], "frozen-before-valid-scoring")
        for group in ("base_frozen", "revision"):
            for item in revision[group].values():
                self.assertEqual(sha(ROOT / item["path"]), item["sha256"])
        self.assertEqual(
            sha(BASE),
            load(GAME / "experiment_manifest_v2.json")["artifacts"]["scenario_suite"]["sha256"],
        )
        for item in revision["invalid_replays"]:
            self.assertEqual(sha(ROOT / item["path"]), item["sha256"])
        self.assertEqual(load(ROOT / revision["invalid_replays"][0]["path"])["counts"]["CRASH"], 19)
        self.assertEqual(load(ROOT / revision["invalid_replays"][1]["path"])["counts"]["FAIL"], 1)

    def test_only_joint_visibility_case_payload_changed(self):
        base = load(BASE)
        revised = load(REVISED)
        self.assertEqual(base["sources"], revised["sources"])
        self.assertEqual(base["claim_inventory"], revised["claim_inventory"])
        base_scenarios = json.loads(json.dumps(base["scenarios"]))
        revised_scenarios = json.loads(json.dumps(revised["scenarios"]))
        base_step = base_scenarios[13]["cases"][1]["steps"][3]["expect"]["adapter"]["observations"]["0"]
        revised_step = revised_scenarios[13]["cases"][1]["steps"][3]["expect"]["adapter"]["observations"]["0"]
        self.assertEqual(base_step.pop("revealed_cards"), revised_step.pop("visible_cards"))
        self.assertEqual(base_scenarios, revised_scenarios)


if __name__ == "__main__":
    unittest.main()
