import hashlib
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from generation import codex_native
from generation.codex_native import DEFAULT_VERBOSITY, default_effort, parse_event_usage


class CodexNativeTest(unittest.TestCase):
    def test_mode_defaults(self) -> None:
        self.assertEqual(default_effort("agentic"), "low")
        self.assertEqual(default_effort("judge"), "medium")
        self.assertEqual(DEFAULT_VERBOSITY, "low")

    def test_process_tree_timeout_returns(self) -> None:
        child = "import time; time.sleep(60)"
        parent = (
            "import subprocess,sys,time; "
            "subprocess.Popen([sys.executable,'-c'," + repr(child) + "]); time.sleep(60)"
        )
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(subprocess.TimeoutExpired):
                codex_native._run_with_tree_timeout(
                    [sys.executable, "-c", parent],
                    input_bytes=b"",
                    cwd=Path(directory),
                    environment=os.environ.copy(),
                    timeout=1,
                )

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

    def test_isolation_profile_denies_filesystem_root(self) -> None:
        config = codex_native._isolation_config()
        self.assertIn('default_permissions = "boardbench-workspace-only"', config)
        self.assertIn('":root" = "deny"', config)
        self.assertIn('":minimal" = "read"', config)
        self.assertIn(f'"{codex_native.REPO_ROOT.as_posix()}" = "deny"', config)

    def test_repository_workspace_is_rejected(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "outside the BoardBench repository"):
            codex_native._assert_isolated_workspace(codex_native.REPO_ROOT, [])

    def test_isolated_home_removes_copied_auth(self) -> None:
        with tempfile.TemporaryDirectory() as source_dir, tempfile.TemporaryDirectory() as home_dir:
            source = Path(source_dir)
            home = Path(home_dir)
            (source / "auth.json").write_text("secret", encoding="utf-8")
            with mock.patch.dict(os.environ, {"CODEX_HOME": str(source), "BOARDBENCH_CODEX_HOME": str(home)}):
                with codex_native._isolated_codex_home() as active:
                    self.assertEqual((active / "auth.json").read_text(encoding="utf-8"), "secret")
                self.assertFalse((home / "auth.json").exists())
                self.assertTrue((home / "config.toml").is_file())

    def test_agentic_call_requires_declared_packet(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(ValueError, "exact packet_files allowlist"):
                codex_native.run_codex(
                    prompt="test", cwd=root, response_path=root / "response.md",
                    events_path=root / "events.jsonl", usage_path=root / "usage.json",
                )

    def test_agentic_call_requires_validated_source_condition(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "rules.pdf").write_bytes(b"rules")
            with self.assertRaisesRegex(ValueError, "validated source condition"):
                codex_native.run_codex(
                    prompt="test", cwd=root, response_path=root / "response.md",
                    events_path=root / "events.jsonl", usage_path=root / "usage.json",
                    packet_files={"rules.pdf"},
                )

    def test_agentic_call_rejects_extra_packet_file_before_launch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "rules.pdf").write_bytes(b"rules")
            (root / "evaluator.json").write_text("leak", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "extra=.*evaluator.json"):
                codex_native.run_codex(
                    prompt="test", cwd=root, response_path=root / "response.md",
                    events_path=root / "events.jsonl", usage_path=root / "usage.json",
                    packet_files={"rules.pdf"}, source_kind="original",
                    sources=[{
                        "path": "rules.pdf", "packet_name": "rules.pdf",
                        "role": "publisher_rulebook",
                        "sha256": hashlib.sha256(b"rules").hexdigest(),
                    }],
                    source_base_dir=root,
                )

    def test_isolation_canary_requires_outside_read_to_fail(self) -> None:
        def sandbox_pass(*args, **kwargs):
            (Path(kwargs["cwd"]) / "write.txt").write_text("ok", encoding="utf-8")
            return subprocess.CompletedProcess(args[0], 0, b"", b"")

        with tempfile.TemporaryDirectory() as home, mock.patch.object(
            codex_native, "_ISOLATION_VERIFIED", False
        ), mock.patch("generation.codex_native.subprocess.run", side_effect=sandbox_pass):
            codex_native.verify_codex_isolation("npx", Path(home))

        leak = subprocess.CompletedProcess([], 20, b"", b"")
        with tempfile.TemporaryDirectory() as home, mock.patch.object(
            codex_native, "_ISOLATION_VERIFIED", False
        ), mock.patch("generation.codex_native.subprocess.run", return_value=leak):
            with self.assertRaisesRegex(RuntimeError, "read outside"):
                codex_native.verify_codex_isolation("npx", Path(home))

        write = subprocess.CompletedProcess([], 40, b"", b"")
        with tempfile.TemporaryDirectory() as home, mock.patch.object(
            codex_native, "_ISOLATION_VERIFIED", False
        ), mock.patch("generation.codex_native.subprocess.run", return_value=write):
            with self.assertRaisesRegex(RuntimeError, "wrote outside"):
                codex_native.verify_codex_isolation("npx", Path(home))


if __name__ == "__main__":
    unittest.main()
