import hashlib
import json
import math
import py_compile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V2 = ROOT / "results/scores/6_nimmt/v2"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SixNimmtV2ResultTests(unittest.TestCase):
    def test_result_keeps_evidence_groups_separate(self):
        result = load(V2 / "result.json")
        evidence = result["implementation_evidence"]
        self.assertEqual(result["schema_version"], 2)
        self.assertEqual(evidence["agentic_gate_pass_rate"], 1.0)
        self.assertEqual(evidence["technical_gate_pass_rate"], 1.0)
        self.assertEqual(evidence["robustness"]["mean"], 1.0)
        self.assertEqual(evidence["interface"]["mean"], 1.0)
        self.assertEqual(evidence["clear_basis_scenarios"]["mean"], 1.0)
        self.assertEqual(evidence["human_decision_basis_scenarios"]["mean"], 1.0)
        self.assertEqual(evidence["scenario_evaluated_coverage"]["mean"], 1.0)
        review = result["review_evidence"]["neutral_judges"]
        self.assertEqual(review["values"], [0.84, 0.88, 0.82])
        self.assertTrue(math.isclose(review["mean"], 0.8466666666666667))
        self.assertTrue(math.isclose(review["sample_sd"], 0.03055050463303896))

    def test_valid_scenario_result_and_claim_coverage(self):
        scenarios = load(V2 / "original_scenarios.json")
        self.assertEqual(scenarios["counts"], {"PASS": 33, "FAIL": 0, "CRASH": 0, "UNREACHED": 0, "UNTESTABLE": 0})
        self.assertEqual(scenarios["basis_scores"]["clear"]["passed"], 24)
        self.assertEqual(scenarios["basis_scores"]["human_decision"]["passed"], 9)
        self.assertEqual(len(scenarios["claim_coverage"]["scenario_covered"]), 30)
        self.assertEqual(len(scenarios["claim_coverage"]["evaluated"]), 30)

    def test_evaluation_manifest_hashes(self):
        manifest = load(V2 / "original_evaluation_manifest.json")
        self.assertEqual(manifest["status"], "complete")
        self.assertFalse(manifest["implementation_changed_after_evaluation_started"])
        self.assertEqual(sha(ROOT / "outputs/six_nimmt_codex_ag.py"), manifest["implementation_sha256"])
        for item in manifest["source_condition"]:
            self.assertEqual(sha(ROOT / item["path"]), item["sha256"])
        for item in manifest["evaluator"].values():
            self.assertEqual(sha(ROOT / item["path"]), item["sha256"])
        for item in manifest["artifacts"].values():
            self.assertEqual(sha(ROOT / item["path"]), item["sha256"])
        for item in manifest["invalid_evaluator_replays"]:
            self.assertEqual(sha(ROOT / item["path"]), item["sha256"])

    def test_judge_packet_and_usage(self):
        packet = load(V2 / "judge_packet_manifest.json")
        for item in packet["sources"]:
            self.assertEqual(sha(ROOT / item["path"]), item["sha256"])
        self.assertEqual(packet["pdf_render"]["dpi"], 150)
        self.assertEqual(packet["pdf_render"]["page_count"], 2)
        self.assertEqual(len(packet["neutral"]["reviews"]), 3)
        self.assertEqual(len(packet["personas"]["reviews"]), 3)
        usage = load(V2 / "original_usage.json")
        self.assertEqual((usage["call_count"], usage["generation_calls"], usage["neutral_judge_calls"], usage["persona_calls"]), (9, 3, 3, 3))
        for call in usage["calls"]:
            self.assertEqual(call["exit_code"], 0)
            self.assertTrue(call["isolation_canary_passed"])
        for call in usage["calls"][3:]:
            self.assertEqual((call["model"], call["reasoning_effort"], call["verbosity"]), ("gpt-5.6-sol", "medium", "low"))
            self.assertEqual(len(call["image_paths"]), 2)

    def test_post_judge_candidate_is_confirmed_but_unscored(self):
        candidate = load(V2 / "raw/judge_candidate_replays.json")["candidates"][0]
        self.assertTrue(candidate["confirmed"])
        self.assertFalse(candidate["scored"])
        self.assertEqual(candidate["fact_ids"], ["6N-C-JOINT-REVEAL"])
        self.assertEqual(candidate["actual"]["0"]["missing_played_cards"], [20])
        self.assertEqual(load(V2 / "raw/invalid_evaluator_replay_1.json")["counts"]["CRASH"], 19)
        self.assertEqual(load(V2 / "raw/invalid_evaluator_replay_2.json")["counts"]["FAIL"], 1)

    def test_persona_runner_compiles(self):
        py_compile.compile(str(ROOT / "checks/run_judge_personas_v2.py"), doraise=True)


if __name__ == "__main__":
    unittest.main()
