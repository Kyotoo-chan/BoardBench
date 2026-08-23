import hashlib
import json
import unittest
from pathlib import Path

from checks.run_scenarios_v4 import load_suite, run_suite

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "inputs/games/abalone"
V2 = ROOT / "results/scores/abalone/v2"
V3 = ROOT / "results/scores/abalone/v3"
SUITE_V2 = ROOT / "checks/scenarios/abalone_v2.json"
SUITE_V3 = ROOT / "checks/scenarios/abalone_v3.json"
DROPPED = "ABAL-R19-forced-pass-only-with-no-move"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class AbaloneV3ReplayTests(unittest.TestCase):
    def test_v3_drops_only_the_forced_pass_scenario(self):
        old = load_suite(SUITE_V2, ROOT)
        new = load_suite(SUITE_V3, ROOT)
        self.assertEqual(len(old["scenarios"]), 38)
        self.assertEqual(len(new["scenarios"]), 37)
        self.assertIn(DROPPED, [item["id"] for item in old["scenarios"]])
        self.assertNotIn(DROPPED, [item["id"] for item in new["scenarios"]])
        self.assertEqual(new["claim_coverage"]["mapping_coverage"], 1.0)
        self.assertEqual(len(new["claim_coverage"]["required"]), 33)

    def test_v2_scores_are_not_rewritten(self):
        original = load(V2 / "original_result.json")
        emphasis = load(V2 / "setup_emphasis_2_result.json")
        self.assertEqual(original["implementation_evidence"]["human_decision_basis_scenarios"]["mean"], 1.0)
        self.assertEqual(emphasis["implementation_evidence"]["human_decision_basis_scenarios"]["mean"], 0.8)
        self.assertEqual(original["runs"][0]["scenario"]["human_decision"]["evaluated"], 5)
        failures = [item["id"] for item in load(V2 / "setup_emphasis_2_scenarios.json")["results"] if item["status"] != "PASS"]
        self.assertEqual(failures, [DROPPED])

    def test_replay_scores_match_the_v3_cards(self):
        original = run_suite(V3 / "original.py", SUITE_V3)
        emphasis = run_suite(V3 / "setup_emphasis.py", SUITE_V3)
        replicate = run_suite(V3 / "setup_emphasis_2.py", SUITE_V3)
        self.assertEqual(original["basis_scores"]["clear"]["passed"], 32)
        self.assertEqual(original["basis_scores"]["human_decision"], {"passed": 4, "evaluated": 4, "score": 1.0})
        self.assertEqual([item["id"] for item in original["results"] if item["status"] != "PASS"], ["ABAL-R01-exact-initial-setup"])
        for result in (emphasis, replicate):
            self.assertEqual(result["basis_scores"]["clear"]["passed"], 33)
            self.assertEqual(result["basis_scores"]["human_decision"]["passed"], 4)
            self.assertEqual(result["counts"]["FAIL"], 0)

    def test_revision_hashes_and_code_identity(self):
        revision = load(GAME / "evaluator_revision_v3.json")
        self.assertEqual(revision["evaluation"]["unscored_scenario"], DROPPED)
        self.assertEqual(sha(SUITE_V3), revision["artifacts"]["scenario_suite"]["sha256"])
        self.assertEqual(sha(V3 / "original.py"), "4098c2dfc360915fd2760393907fe107e878c7b9a4ac3d2c4fcebab71b7e4ccd")
        self.assertEqual(sha(V3 / "original.py"), load(V2 / "original_result.json")["runs"][0]["hashes"]["code"])
        claims = {item["id"]: item for item in load(GAME / "claims_v3.json")["claims"]}
        self.assertFalse(claims["ABAL-G-PASS"]["testable"])


if __name__ == "__main__":
    unittest.main()
