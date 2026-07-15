import unittest

from generation.codex_native import default_effort, parse_event_usage


class CodexNativeTest(unittest.TestCase):
    def test_mode_defaults(self) -> None:
        self.assertEqual(default_effort("agentic"), "low")
        self.assertEqual(default_effort("judge"), "medium")

    def test_parse_event_usage_uses_final_cumulative_record(self) -> None:
        raw = "\n".join(
            [
                '{"type":"turn.completed","usage":{"input_tokens":10,"output_tokens":2}}',
                '{"type":"turn.completed","usage":{"input_tokens":25,"cached_input_tokens":5,"output_tokens":7}}',
            ]
        )
        records, summary = parse_event_usage(raw)
        self.assertEqual(len(records), 2)
        self.assertEqual(
            summary,
            {"input_tokens": 25, "cached_input_tokens": 5, "output_tokens": 7},
        )


if __name__ == "__main__":
    unittest.main()
