import hashlib
import json
import math
import tarfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V2 = ROOT / "results/scores/abalone/v2"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class AbaloneV2ReplicationTests(unittest.TestCase):
    def test_generation_is_exact_preregistered_replicate(self):
        evidence = load(ROOT / "outputs/abalone_codex_ag_agentic.json")
        self.assertEqual(evidence["run_id"], "v2_setup_emphasis_2")
        self.assertEqual(evidence["adapted_from_run_id"], "v2_setup_emphasis_1")
        self.assertTrue(evidence["success"])
        self.assertEqual((len(evidence["calls"]), evidence["repair_count"]), (1, 0))
        result = load(V2 / "setup_emphasis_replication_v2_result.json")
        self.assertTrue(result["model_packet_sha256_equal"])
        first_packet = result["model_packets"]["replicate_1"]
        second_packet = result["model_packets"]["replicate_2"]
        self.assertEqual(first_packet["aggregate_sha256"], second_packet["aggregate_sha256"])
        self.assertEqual(first_packet["file_sha256"], second_packet["file_sha256"])
        self.assertEqual(sha(ROOT / second_packet["evidence"]["path"]), second_packet["evidence"]["sha256"])
        self.assertEqual(sha(ROOT / first_packet["evidence_archive"]["path"]), first_packet["evidence_archive"]["archive_sha256"])
        self.assertFalse(result["selection_policy"]["best_of_selection"])
        self.assertTrue(result["selection_policy"]["replicate_1_retained"])

    def test_deterministic_results_recur(self):
        scenarios = load(V2 / "setup_emphasis_2_scenarios.json")
        self.assertEqual(scenarios["counts"], {"PASS": 37, "FAIL": 1, "CRASH": 0, "UNREACHED": 0, "UNTESTABLE": 0})
        self.assertEqual(scenarios["basis_scores"]["clear"]["passed"], 33)
        self.assertEqual(scenarios["basis_scores"]["human_decision"]["passed"], 4)
        failures = [item["id"] for item in scenarios["results"] if item["status"] != "PASS"]
        self.assertEqual(failures, ["ABAL-R19-forced-pass-only-with-no-move"])
        self.assertEqual(len(scenarios["claim_coverage"]["evaluated"]), 33)

    def test_result_profile_and_judges(self):
        result = load(V2 / "setup_emphasis_2_result.json")
        evidence = result["implementation_evidence"]
        self.assertEqual(evidence["technical_gate_pass_rate"], 1.0)
        self.assertEqual(evidence["robustness"]["mean"], 1.0)
        self.assertEqual(evidence["clear_basis_scenarios"]["mean"], 1.0)
        self.assertEqual(evidence["human_decision_basis_scenarios"]["mean"], 0.8)
        judges = result["review_evidence"]["neutral_judges"]
        self.assertEqual(judges["values"], [0.9, 0.87, 0.84])
        self.assertTrue(math.isclose(judges["mean"], 0.87))
        self.assertTrue(math.isclose(judges["sample_sd"], 0.03))
        usage = load(V2 / "setup_emphasis_2_usage.json")
        self.assertEqual((usage["call_count"], usage["generation_calls"], usage["neutral_judge_calls"]), (4, 1, 3))
        for call in usage["calls"]:
            self.assertEqual(call["exit_code"], 0)
            self.assertTrue(call["isolation_canary_passed"])
        for call in usage["calls"][1:]:
            self.assertEqual((call["model"], call["reasoning_effort"], len(call["image_paths"])), ("gpt-5.6-sol", "medium", 4))

    def test_evaluation_and_iteration_hashes(self):
        manifest = load(V2 / "setup_emphasis_2_evaluation_manifest.json")
        self.assertEqual(manifest["status"], "complete")
        self.assertFalse(manifest["implementation_changed_after_evaluation_started"])
        self.assertTrue(manifest["model_packet_sha256_equal_to_replicate_1"])
        self.assertEqual(sha(ROOT / "outputs/abalone_codex_ag.py"), manifest["implementation_sha256"])
        for item in manifest["source_condition"]:
            self.assertEqual(sha(ROOT / item["path"]), item["sha256"])
        for item in manifest["evaluator"].values():
            self.assertEqual(sha(ROOT / item["path"]), item["sha256"])
        for item in manifest["artifacts"].values():
            self.assertEqual(sha(ROOT / item["path"]), item["sha256"])
        iteration = load(V2 / "iteration_manifest.json")
        for relative, digest in iteration["conditions"]["setup_emphasis_2"].items():
            self.assertEqual(sha(V2 / relative), digest)

    def test_judge_candidate_is_confirmed_but_unscored(self):
        candidate = load(V2 / "raw/setup_emphasis_2_judge_candidate_replays.json")["candidates"][0]
        self.assertTrue(candidate["confirmed"])
        self.assertFalse(candidate["scored"])
        self.assertTrue(candidate["serialized_actions_differ"])
        self.assertTrue(candidate["successor_states_equal"])

    def test_raw_archive_retains_canonical_outputs(self):
        with tarfile.open(V2 / "raw/setup_emphasis_2_artifacts.tar.gz", "r:gz") as archive:
            names = set(archive.getnames())
        self.assertIn("abalone_codex_ag.py", names)
        self.assertIn("abalone_codex_ag_agentic.json", names)
        self.assertIn("abalone_codex_ag_judge_1.md", names)
        self.assertIn("abalone_codex_ag_judge_2.md", names)
        self.assertIn("abalone_codex_ag_judge_3.md", names)


if __name__ == "__main__":
    unittest.main()
