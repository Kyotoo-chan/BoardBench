#!/usr/bin/env python3
"""Run one isolated Codex call and preserve its response, events, and usage."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

DEFAULT_VERBOSITY = "low"

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
) -> dict[str, object]:
    cwd = cwd.resolve()
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
        "-s",
        "danger-full-access" if mode == "agentic" else "read-only",
        "-C",
        cwd.as_posix(),
    ]
    for image_path in image_paths or []:
        command += ["--image", image_path.resolve().as_posix()]
    command += [
        "--ignore-user-config",
        "--ignore-rules",
        "--json",
        "--output-last-message",
        response_path.resolve().as_posix(),
        "-",
    ]

    quota_before = fetch_codex_quota()
    started_at = datetime.now(timezone.utc)
    started = time.perf_counter()
    result = subprocess.run(
        command,
        input=prompt.encode("utf-8"),
        capture_output=True,
        cwd=cwd,
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
        "image_paths": [path.as_posix() for path in image_paths or []],
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
    parser.add_argument("--timeout", type=int, default=4000)
    parser.add_argument("--image", type=Path, action="append", default=[])
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
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
