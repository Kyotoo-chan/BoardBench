import importlib.util
import unittest
from pathlib import Path


PATH = Path(__file__).with_name("versioned") / "04_required_api_v2.py"
SPEC = importlib.util.spec_from_file_location("required_api_check", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class RequiredApiEnvelopeTests(unittest.TestCase):
    def test_positive_schema_versions_are_supported(self):
        self.assertTrue(MODULE._canonical_envelope({"schema": "boardbench/game/state/2", "data": {}}, "state"))
        self.assertTrue(MODULE._canonical_envelope({"schema": "boardbench/game/state/1", "data": {}}, "state"))
        self.assertFalse(MODULE._canonical_envelope({"schema": "boardbench/game/action/2", "data": {}}, "state"))
        self.assertFalse(MODULE._canonical_envelope({"schema": "boardbench/game/state/0", "data": {}}, "state"))


if __name__ == "__main__":
    unittest.main()
