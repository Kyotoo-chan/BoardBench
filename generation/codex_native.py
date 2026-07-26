#!/usr/bin/env python3
"""Run one isolated Codex call and preserve its response, events, and usage."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import urllib.request
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from generation.source_condition import (
    validate_packet_files,
    validate_packet_sources,
    validate_pair,
    validate_pdf_renders,
    validate_sources,
)

DEFAULT_VERBOSITY = "low"
ISOLATION_PROFILE = "boardbench-workspace-only"
_ISOLATION_VERIFIED = False

TOKEN_KEYS = {
    "input_tokens",
    "cached_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
    "reasoning_tokens",
    "total_tokens",
}


def _usage_records(value: object, path: str = "$") -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    if isinstance(value, dict):
        token_data = {
            key: item
            for key, item in value.items()
            if key in TOKEN_KEYS and isinstance(item, (int, float))
        }
        if token_data:
            records.append({"path": path, **token_data})
        for key, item in value.items():
            records.extend(_usage_records(item, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            records.extend(_usage_records(item, f"{path}[{index}]"))
    return records


def parse_event_usage(raw_jsonl: str) -> tuple[list[dict[str, object]], dict[str, int]]:
    records: list[dict[str, object]] = []
    for line_number, line in enumerate(raw_jsonl.splitlines(), start=1):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        for record in _usage_records(event):
            records.append({"line": line_number, **record})

    # Codex currently emits cumulative usage in its final completion event. Keep
    # every raw record above and use the last reported value for the convenience summary.
    summary: dict[str, int] = {}
    for record in records:
        for key in TOKEN_KEYS:
            value = record.get(key)
            if isinstance(value, (int, float)):
                summary[key] = int(value)
    return records, summary


def fetch_codex_quota() -> dict[str, object] | None:
    auth_path = Path.home() / ".pi" / "agent" / "auth.json"
    try:
        access = json.loads(auth_path.read_text(encoding="utf-8"))["openai-codex"]["access"]
        request = urllib.request.Request(
            "https://chatgpt.com/backend-api/wham/usage",
            headers={"Authorization": f"Bearer {access}"},
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            payload = json.load(response)
    except Exception:
        return None

    rate_limit = payload.get("rate_limit", {})
    result: dict[str, object] = {}
    for source, label in (("primary_window", "5h"), ("secondary_window", "7d")):
        window = rate_limit.get(source)
        if isinstance(window, dict):
            result[label] = {
                key: window[key]
                for key in ("used_percent", "reset_at", "reset_after_seconds", "limit_window_seconds")
                if key in window
            }
    return result or None


def default_effort(mode: str) -> str:
    return "low" if mode == "agentic" else "medium"


def _isolation_config() -> str:
    windows = '\n[windows]\nsandbox = "elevated"\n' if os.name == "nt" else ""
    repository = REPO_ROOT.as_posix().replace('"', '\\"')
    return f'''default_permissions = "{ISOLATION_PROFILE}"
sandbox_mode = "workspace-write"
approval_policy = "never"

[permissions.{ISOLATION_PROFILE}]
extends = ":workspace"

[permissions.{ISOLATION_PROFILE}.filesystem]
":root" = "deny"
":minimal" = "read"
":tmpdir" = "deny"
":slash_tmp" = "deny"
"{repository}" = "deny"
{windows}'''


@contextmanager
def _isolated_codex_home():
    source = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    home = Path(os.environ.get("BOARDBENCH_CODEX_HOME", Path.home() / ".codex-boardbench"))
    home.mkdir(parents=True, exist_ok=True)
    copied_auth = home / "auth.json"
    copied_auth.unlink(missing_ok=True)
    auth = source / "auth.json"
    if auth.exists():
        shutil.copy2(auth, copied_auth)
    elif not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError(f"Codex authentication not found at {auth}")
    (home / "config.toml").write_text(_isolation_config(), encoding="utf-8")
    try:
        yield home
    finally:
        copied_auth.unlink(missing_ok=True)


def _assert_isolated_workspace(cwd: Path, image_paths: list[Path]) -> None:
    if not cwd.is_dir():
        raise FileNotFoundError(f"Codex workspace does not exist: {cwd}")
    try:
        cwd.relative_to(REPO_ROOT)
    except ValueError:
        pass
    else:
        raise RuntimeError("Codex workspace must be outside the BoardBench repository")
    if any((parent / ".git").exists() for parent in (cwd, *cwd.parents)):
        raise RuntimeError("Codex workspace must not be inside a Git worktree")
    for path in image_paths:
        try:
            path.resolve().relative_to(cwd)
        except ValueError as exc:
            raise RuntimeError(f"Model-facing image is outside the isolated workspace: {path}") from exc


def verify_codex_isolation(npx: str, codex_home: Path) -> None:
    """Fail closed unless Codex can write only inside a non-repository workspace."""
    global _ISOLATION_VERIFIED
    if _ISOLATION_VERIFIED:
        return
    with tempfile.TemporaryDirectory(prefix="boardbench-isolation-canary-") as directory:
        parent = Path(directory)
        workspace = parent / "workspace"
        workspace.mkdir()
        (workspace / "inside.txt").write_text("inside", encoding="utf-8")
        outside = parent / "outside.txt"
        outside.write_text("secret", encoding="utf-8")
        if os.name == "nt":
            inside = str(workspace / "inside.txt").replace("'", "''")
            written = str(workspace / "write.txt").replace("'", "''")
            forbidden = [outside, codex_home / "config.toml", REPO_ROOT / "checks/run_scenarios.py"]
            forbidden_array = ",".join(
                f"'{str(path).replace(chr(39), chr(39) * 2)}'" for path in forbidden
            )
            probe = (
                f"$value = Get-Content -Raw -LiteralPath '{inside}'; "
                "if ($value -ne 'inside') { exit 11 }; "
                f"Set-Content -LiteralPath '{written}' -Value ok; "
                f"$forbidden = @({forbidden_array}); for ($i = 0; $i -lt $forbidden.Count; $i++) {{ "
                "try { Get-Content -Raw -LiteralPath $forbidden[$i] -ErrorAction Stop | Out-Null; exit (20 + $i) } catch {} }; "
                f"try {{ Set-Content -LiteralPath '{str(outside).replace(chr(39), chr(39) * 2)}' -Value changed -ErrorAction Stop; exit 40 }} catch {{}}; "
                "exit 0"
            )
            shell = ["powershell.exe", "-NoProfile", "-Command", probe]
        else:
            checks = "; ".join(
                f"if cat {shlex.quote(str(path))} >/dev/null 2>&1; then exit 12; fi"
                for path in (outside, codex_home / "config.toml", REPO_ROOT / "checks/run_scenarios.py")
            )
            shell = [
                "sh", "-c",
                f"test \"$(cat inside.txt)\" = inside && echo ok > write.txt; {checks}; "
                f"if echo changed > {shlex.quote(str(outside))}; then exit 40; fi; exit 0",
            ]
        command = [
            npx, "--yes", "@openai/codex", "sandbox", "-C", str(workspace),
            "-P", ISOLATION_PROFILE, "--", *shell,
        ]
        environment = os.environ.copy()
        environment["CODEX_HOME"] = str(codex_home)
        result = subprocess.run(command, capture_output=True, cwd=workspace, env=environment, timeout=120)
        if 20 <= result.returncode < 20 + len(forbidden):
            leaked = forbidden[result.returncode - 20]
            raise RuntimeError(f"Codex isolation canary read outside its workspace: {leaked}")
        if result.returncode == 40:
            raise RuntimeError("Codex isolation canary wrote outside its workspace")
        if result.returncode != 0 or not (workspace / "write.txt").exists():
            detail = (result.stderr or result.stdout).decode("utf-8", errors="replace").strip()
            raise RuntimeError(
                "Codex workspace isolation is unavailable; configure the elevated Windows sandbox "
                f"before generation. {detail}"
            )
        if not outside.exists() or outside.read_text(encoding="utf-8") != "secret":
            raise RuntimeError("Codex isolation canary modified a file outside its workspace")
    _ISOLATION_VERIFIED = True


def _run_with_tree_timeout(
    command: list[str], *, input_bytes: bytes, cwd: Path, environment: dict[str, str], timeout: int
) -> subprocess.CompletedProcess[bytes]:
    windows = os.name == "nt"
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd,
        env=environment,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if windows else 0,
        start_new_session=not windows,
    )
    try:
        stdout, stderr = process.communicate(input=input_bytes, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        if windows:
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                capture_output=True,
                timeout=30,
            )
        else:
            os.killpg(process.pid, signal.SIGKILL)
        stdout, stderr = process.communicate(timeout=30)
        raise subprocess.TimeoutExpired(command, timeout, output=stdout, stderr=stderr) from exc
    return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)


def run_codex(
    *,
    prompt: str,
    cwd: Path,
    response_path: Path,
    events_path: Path,
    usage_path: Path,
    model: str = "gpt-5.6-sol",
    effort: str | None = None,
    verbosity: str = DEFAULT_VERBOSITY,
    mode: str = "agentic",
    timeout: int = 4000,
    image_paths: list[Path] | None = None,
    sandbox: str | None = None,
    packet_files: set[str] | None = None,
    source_kind: str | None = None,
    sources: list[dict] | None = None,
    source_base_dir: Path | None = None,
    original_sources: list[dict] | None = None,
    original_source_base_dir: Path | None = None,
) -> dict[str, object]:
    cwd = cwd.resolve()
    images = [path.resolve() for path in image_paths or []]
    if sandbox not in {None, "workspace-write"}:
        raise ValueError("BoardBench Codex calls require workspace-write isolation")
    _assert_isolated_workspace(cwd, images)
    if mode == "agentic":
        if packet_files is None:
            raise ValueError("agentic Codex calls require an exact packet_files allowlist")
        if source_kind is None or sources is None or source_base_dir is None:
            raise ValueError("agentic Codex calls require a validated source condition")
        if source_kind == "clarified":
            if original_sources is None or original_source_base_dir is None:
                raise ValueError("clarified Codex calls require the original source condition")
            validate_pair(
                original_sources, sources, original_source_base_dir, source_base_dir
            )
        else:
            validate_sources(source_kind, sources, source_base_dir)
    packet_manifest = validate_packet_files(cwd, packet_files) if packet_files is not None else None
    if mode == "agentic":
        validate_packet_sources(packet_manifest, sources)
        validate_pdf_renders(cwd, sources, images)
    response_path.parent.mkdir(parents=True, exist_ok=True)
    events_path.parent.mkdir(parents=True, exist_ok=True)
    usage_path.parent.mkdir(parents=True, exist_ok=True)

    effort = effort or default_effort(mode)
    npx = shutil.which("npx") or shutil.which("npx.cmd")
    if not npx:
        raise FileNotFoundError("npx is required to run native Codex")
    command = [
        npx,
        "--yes",
        "@openai/codex",
        "exec",
        "--ephemeral",
        "--skip-git-repo-check",
        "-m",
        model,
        "-c",
        f'model_reasoning_effort="{effort}"',
        "-c",
        f'model_verbosity="{verbosity}"',
        "-c",
        f'default_permissions="{ISOLATION_PROFILE}"',
        "-C",
        cwd.as_posix(),
    ]
    for image_path in images:
        command += ["--image", image_path.resolve().as_posix()]
    command += [
        "--ignore-rules",
        "--json",
        "--output-last-message",
        response_path.resolve().as_posix(),
        "-",
    ]

    quota_before = fetch_codex_quota()
    started_at = datetime.now(timezone.utc)
    started = time.perf_counter()
    with _isolated_codex_home() as codex_home:
        verify_codex_isolation(npx, codex_home)
        environment = os.environ.copy()
        environment["CODEX_HOME"] = str(codex_home)
        result = _run_with_tree_timeout(
            command,
            input_bytes=prompt.encode("utf-8"),
            cwd=cwd,
            environment=environment,
            timeout=timeout,
        )
    elapsed = time.perf_counter() - started
    ended_at = datetime.now(timezone.utc)
    quota_after = fetch_codex_quota()
    stdout = result.stdout.decode("utf-8", errors="replace")
    stderr = result.stderr.decode("utf-8", errors="replace")
    events_path.write_text(stdout, encoding="utf-8")

    records, tokens = parse_event_usage(stdout)
    metadata: dict[str, object] = {
        "model": model,
        "reasoning_effort": effort,
        "verbosity": verbosity,
        "mode": mode,
        "sandbox": "workspace-write",
        "permission_profile": ISOLATION_PROFILE,
        "isolation_canary_passed": True,
        "source_condition_kind": source_kind,
        "model_packet_sha256": packet_manifest,
        "started_at": started_at.isoformat(),
        "ended_at": ended_at.isoformat(),
        "elapsed_seconds": round(elapsed, 3),
        "exit_code": result.returncode,
        "quota_before": quota_before,
        "quota_after": quota_after,
        "token_summary": tokens,
        "provider_usage_records": records,
        "events_path": events_path.as_posix(),
        "response_path": response_path.as_posix(),
        "image_paths": [path.as_posix() for path in images],
        "stderr": stderr,
    }
    usage_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if result.returncode != 0:
        raise RuntimeError(stderr.strip() or stdout.strip() or "Codex call failed")
    if not response_path.exists() or not response_path.read_text(encoding="utf-8").strip():
        raise RuntimeError("Codex produced no final response")
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt", type=Path, required=True)
    parser.add_argument("--cwd", type=Path, required=True)
    parser.add_argument("--response", type=Path, required=True)
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--usage", type=Path, required=True)
    parser.add_argument("--model", default="gpt-5.6-sol")
    parser.add_argument("--effort", help="default: low for generation, medium for judging")
    parser.add_argument("--verbosity", choices=("low", "medium", "high"), default=DEFAULT_VERBOSITY)
    parser.add_argument("--mode", choices=("agentic", "judge"), default="agentic")
    parser.add_argument("--sandbox", choices=("workspace-write",))
    parser.add_argument("--timeout", type=int, default=4000)
    parser.add_argument("--image", type=Path, action="append", default=[])
    parser.add_argument("--packet-file", action="append", default=[])
    args = parser.parse_args()
    run_codex(
        prompt=args.prompt.read_text(encoding="utf-8"),
        cwd=args.cwd,
        response_path=args.response,
        events_path=args.events,
        usage_path=args.usage,
        model=args.model,
        effort=args.effort,
        verbosity=args.verbosity,
        mode=args.mode,
        timeout=args.timeout,
        image_paths=args.image,
        sandbox=args.sandbox,
        packet_files=set(args.packet_file) if args.packet_file else None,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
