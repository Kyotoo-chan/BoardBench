from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from generation.plot_result import plot
from generation.result_card import aggregate, estimate_call_cost, markdown


class ResultCardTests(unittest.TestCase):
    def write_json(self, path: Path, value: object) -> None:
        path.write_text(json.dumps(value), encoding="utf-8")

    def make_run(self, root: Path, index: int, score: float) -> dict[str, object]:
        stem = f"run{index}"
        evidence = root / f"{stem}_evidence.json"
        checks = root / f"{stem}_checks.txt"
        scenarios = root / f"{stem}_scenarios.json"
        usage = root / f"{stem}_usage.json"
        code = root / f"{stem}.py"
        assumptions = root / f"{stem}_assumptions.json"
        self.write_json(evidence, {"protocol": "agentic-v2.2", "model": "m", "reasoning_effort": "medium", "independent_gate_passed": True, "agent_ran_self_check": True, "repair_count": 0})
        checks.write_text(f"summary 4/4 score=1.000\n05_random_rollouts 100/100 score={score:.3f}\n06_action_language 10/10 score=1.000\n", encoding="utf-8")
        self.write_json(scenarios, {"rubric_version": "g-v1", "suite_sha256": "a" * 64, "adapter_sha256": "b" * 64, "counts": {"PASS": 2}, "coverage": 1.0, "basis_scores": {"clear": {"score": score}, "human_decision": {"score": 0.5}}, "results": []})
        self.write_json(usage, {"call_count": 4, "elapsed_seconds_total": 10 * index, "token_totals": {"input_tokens": 100 * index, "cached_input_tokens": 50, "output_tokens": 20, "reasoning_output_tokens": 10}, "actual_subscription_cost": None})
        code.write_text("x = 1\ny = 2\n", encoding="utf-8")
        self.write_json(assumptions, {"version": 1, "assumptions": [] if index > 1 else [{"source_location": "p1", "selected": "A"}]})
        reviews = []
        for judge in range(3):
            path = root / f"{stem}_judge{judge}.md"
            path.write_text(f"score: {score}\n", encoding="utf-8")
            reviews.append(path.name)
        return {"stem": stem, "agentic_evidence": evidence.name, "checks": checks.name, "scenarios": scenarios.name, "usage": usage.name, "code": code.name, "assumptions": assumptions.name, "neutral_reviews": reviews}

    def test_three_run_profile_keeps_groups_separate(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "rules.txt"
            source.write_text("rules", encoding="utf-8")
            spec = {
                "identity": {"game": "demo", "source_path": source.name, "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest()},
                "runs": [self.make_run(root, 1, 0.5), self.make_run(root, 2, 0.75), self.make_run(root, 3, 1.0)],
                "headline": "Separated evidence.",
            }
            result = aggregate(spec, root)
            self.assertEqual(result["implementation_evidence"]["clear_rules"]["mean"], 0.75)
            self.assertEqual(result["implementation_evidence"]["clear_rules"]["sample_sd"], 0.25)
            self.assertEqual(result["efficiency"]["input_tokens"]["mean"], 200)
            self.assertEqual(result["review_evidence"]["neutral_judges"]["mean"], 0.75)
            self.assertIsNone(result["monetary_cost"]["exact_total"])
            self.assertNotIn("overall_correctness_score", result)
            self.assertIn("Clear rules", markdown(result))

    def test_public_price_estimate_separates_cached_tokens(self):
        cost = estimate_call_cost({
            "model": "gpt-5.6-sol",
            "token_summary": {"input_tokens": 1_000_000, "cached_input_tokens": 800_000, "output_tokens": 10_000},
        })
        self.assertAlmostEqual(cost, 1.7)

    def test_spec_cannot_override_raw_model_settings(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "rules.txt"
            source.write_text("rules", encoding="utf-8")
            run = self.make_run(root, 1, 1.0)
            run["model"] = "spoofed-model"
            with self.assertRaisesRegex(ValueError, "settings belong in raw artifacts"):
                aggregate({"identity": {"source_path": source.name}, "runs": [run]}, root)

    def test_plot_rejects_more_than_two_conditions(self):
        with self.assertRaisesRegex(ValueError, "one or two"):
            plot([{}, {}, {}], Path("unused.png"))

    def test_mismatched_evaluators_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "rules.txt"
            source.write_text("rules", encoding="utf-8")
            runs = [self.make_run(root, 1, 1.0), self.make_run(root, 2, 1.0)]
            scenario = root / "run2_scenarios.json"
            payload = json.loads(scenario.read_text(encoding="utf-8"))
            payload["suite_sha256"] = "c" * 64
            self.write_json(scenario, payload)
            with self.assertRaisesRegex(ValueError, "mismatched"):
                aggregate({"identity": {"source_path": source.name}, "runs": runs}, root)


if __name__ == "__main__":
    unittest.main()
