import unittest

from generation.agentic_self_check_v2 import validate_envelope


class AgenticSelfCheckTests(unittest.TestCase):
    def test_accepts_profile_schema_versions_beyond_one(self):
        value = {"schema": "boardbench/example/state/2", "data": {}}
        validate_envelope(value, "state", "boardbench/example/state/2")
        with self.assertRaises(AssertionError):
            validate_envelope(value, "state", "boardbench/example/state/1")

    def test_rejects_wrong_kind_and_invalid_version(self):
        for schema in ("boardbench/example/action/2", "boardbench/example/state/0", "example/state/2"):
            with self.subTest(schema=schema), self.assertRaises(AssertionError):
                validate_envelope({"schema": schema, "data": {}}, "state")


if __name__ == "__main__":
    unittest.main()
