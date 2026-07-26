import json
import tempfile
import unittest
from pathlib import Path

from checks.claim_coverage import validate_claim_coverage


class ClaimCoverageTests(unittest.TestCase):
    def inventory(self, root: Path, claims: list[dict]) -> Path:
        path = root / "claims.json"
        path.write_text(json.dumps({"version": 1, "claims": claims}), encoding="utf-8")
        return path

    def test_requires_scenario_for_material_clear_claim(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inventory = self.inventory(root, [{
                "id": "TURN-01", "classification": "clear", "material": True, "testable": True,
            }])
            with self.assertRaisesRegex(ValueError, "TURN-01"):
                validate_claim_coverage(inventory, [])
            with self.assertRaisesRegex(ValueError, "no checkable"):
                validate_claim_coverage(inventory, [{
                    "id": "EMPTY", "basis": "clear", "fact_ids": ["TURN-01"],
                }])
            result = validate_claim_coverage(inventory, [{
                "id": "GAME-R01", "basis": "clear", "fact_ids": ["TURN-01"], "initial": {"terminal": False},
            }])
            self.assertEqual(result["mapping_coverage"], 1.0)

    def test_ambiguity_uses_human_decision_basis_and_exceptions_do_not_inflate_coverage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inventory = self.inventory(root, [
                {"id": "CLEAR-01", "classification": "clear", "material": True, "testable": True, "coverage_exception": "physical dexterity"},
                {"id": "GAP-01", "classification": "missing", "material": True, "testable": True},
            ])
            result = validate_claim_coverage(inventory, [{
                "id": "GAME-R02", "basis": "human_decision", "fact_ids": ["GAP-01"], "initial": {"legal_action_count_min": 1},
            }])
            self.assertEqual(result["mapping_coverage"], 0.0)
            self.assertEqual(result["coverage_exceptions"], ["CLEAR-01"])


if __name__ == "__main__":
    unittest.main()
