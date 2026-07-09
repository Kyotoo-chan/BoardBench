"""Multi-turn GLM agentic generation with workspace read/write tools."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from generation.llm_cli import extract_code_block

ZAI_CHAT_URL = "https://api.z.ai/api/paas/v4/chat/completions"
MAX_READ_CHARS = 120_000
MAX_TURNS = 40
MAX_TOOL_OUTPUT_CHARS = 24_000

ActionKind = Literal["list", "read", "write", "run", "done"]

AGENT_BLOCK_RE = re.compile(r"```agent\s*(.*?)```", re.DOTALL | re.IGNORECASE)

SYSTEM_PROMPT = """\
BoardBench GLM agentic generation.

You work inside an isolated temporary workspace. Source material lives under inputs/.
Write generated code only under outputs/.

Use one ```agent block per turn until you submit the final answer:

```agent
action: list
path: inputs
```

```agent
action: read
path: inputs/game_rules_extracted.txt
```

```agent
action: write
path: outputs/game.py
---
<file content here>
```

```agent
action: run
command: python -c "import ast; ast.parse(open('outputs/game.py', encoding='utf-8').read())"
```

```agent
action: done
```

Allowed actions:
- list — list files in a directory (path optional, default ".")
- read — read a text file under inputs/ or outputs/
- write — write a text file under outputs/ only (content after a --- line)
- run — run a short python smoke command (python -c ... or python outputs/<file>.py)
- done — finish; your message must also include open questions/assumptions and one fenced ```python block

Rules:
- Use only files in inputs/ as rule sources. Do not use outside game knowledge.
- Do not access paths outside the workspace.
- Implement the BoardBench game API from inputs/rulebook_to_python.txt.
- Prefer reading inputs/rulebook_to_python.txt, inputs/open_spiel_backbone.md,
  inputs/implementation_brief.md, and inputs/game_rules_extracted.txt (or game_rules.txt).
- Image-only PDF pages cannot be read with the read tool; use extracted text files instead.
- Before done, read back your outputs file and run at least one syntax smoke check.
"""


@dataclass
class AgentAction:
    kind: ActionKind
    path: str = ""
    content: str = ""
    command: str = ""


@dataclass
class TurnRecord:
    turn: int
    assistant: str
    action: str
    tool_result: str


@dataclass
class AgentRunResult:
    final_text: str
    transcript: list[TurnRecord]
    usage_total: dict[str, int]
    raw_turns: list[dict[str, Any]] = field(default_factory=list)


def _parse_agent_block(block: str) -> AgentAction:
    lines = [line.strip() for line in block.strip().splitlines() if line.strip()]
    fields: dict[str, str] = {}
    content_lines: list[str] = []
    past_sep = False
    for line in block.strip().splitlines():
        if not past_sep and line.strip() == "---":
            past_sep = True
            continue
        if past_sep:
            content_lines.append(line)
            continue
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip().lower()] = value.strip()
    kind = fields.get("action", "").lower()
    if kind not in {"list", "read", "write", "run", "done"}:
        raise ValueError(f"unknown or missing action in agent block: {fields!r}")
    return AgentAction(
        kind=kind,  # type: ignore[arg-type]
        path=fields.get("path", ""),
        content="\n".join(content_lines).strip("\n"),
        command=fields.get("command", ""),
    )


def parse_agent_action(text: str) -> AgentAction | None:
    match = AGENT_BLOCK_RE.search(text)
    if not match:
        return None
    return _parse_agent_block(match.group(1))


def _resolve_workspace_path(workspace: Path, raw_path: str) -> Path:
    rel = raw_path.strip().replace("\\", "/")
    if not rel or rel == ".":
        target = workspace
    else:
        target = (workspace / rel).resolve()
    root = workspace.resolve()
    if target != root and root not in target.parents:
        raise ValueError(f"path escapes workspace: {raw_path}")
    return target


def _list_tree(path: Path, *, prefix: str = "") -> str:
    if not path.exists():
        return f"(missing) {path.as_posix()}"
    if path.is_file():
        return f"{prefix}{path.name}  ({path.stat().st_size} bytes)"
    lines = [f"{prefix}{path.name}/"]
    for child in sorted(path.iterdir(), key=lambda p: p.name.lower()):
        lines.append(_list_tree(child, prefix=prefix + "  "))
    return "\n".join(lines)


def execute_action(workspace: Path, action: AgentAction) -> str:
    if action.kind == "list":
        target = _resolve_workspace_path(workspace, action.path or ".")
        if not target.exists():
            return f"ERROR: path not found: {target.relative_to(workspace).as_posix()}"
        if target.is_file():
            return f"FILE {target.relative_to(workspace).as_posix()} ({target.stat().st_size} bytes)"
        entries = []
        for child in sorted(target.iterdir(), key=lambda p: p.name.lower()):
            kind = "dir" if child.is_dir() else "file"
            size = "" if child.is_dir() else f" ({child.stat().st_size} bytes)"
            entries.append(f"{kind:4} {child.relative_to(workspace).as_posix()}{size}")
        return "OK\n" + ("\n".join(entries) if entries else "(empty)")

    if action.kind == "read":
        target = _resolve_workspace_path(workspace, action.path)
        if not target.exists():
            return f"ERROR: file not found: {action.path}"
        if target.is_dir():
            return "ERROR: path is a directory; use action: list"
        allowed_roots = [(workspace / "inputs").resolve(), (workspace / "outputs").resolve()]
        if not any(root == target or root in target.parents for root in allowed_roots):
            return "ERROR: read allowed only under inputs/ or outputs/"
        text = target.read_text(encoding="utf-8", errors="replace")
        if len(text) > MAX_READ_CHARS:
            text = text[:MAX_READ_CHARS] + f"\n\n...[truncated at {MAX_READ_CHARS} chars]"
        return f"OK {target.relative_to(workspace).as_posix()}\n\n{text}"

    if action.kind == "write":
        target = _resolve_workspace_path(workspace, action.path)
        outputs_root = (workspace / "outputs").resolve()
        if outputs_root != target and outputs_root not in target.parents:
            return "ERROR: write allowed only under outputs/"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(action.content, encoding="utf-8")
        return f"OK wrote {target.relative_to(workspace).as_posix()} ({len(action.content)} chars)"

    if action.kind == "run":
        cmd = action.command.strip()
        if not cmd.startswith("python "):
            return "ERROR: only python commands are allowed"
        if ".." in cmd or "inputs/" in cmd:
            return "ERROR: run only against outputs/ artifacts"
        completed = subprocess.run(
            cmd,
            shell=True,
            cwd=workspace,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
        stdout = (completed.stdout or "").strip()
        stderr = (completed.stderr or "").strip()
        detail = stdout or stderr or "(no output)"
        if len(detail) > MAX_TOOL_OUTPUT_CHARS:
            detail = detail[:MAX_TOOL_OUTPUT_CHARS] + "\n...[truncated]"
        status = "OK" if completed.returncode == 0 else f"FAIL exit={completed.returncode}"
        return f"{status}\n{detail}"

    if action.kind == "done":
        return "OK done"

    raise ValueError(f"unsupported action: {action.kind}")


def workspace_bootstrap(workspace: Path) -> str:
    lines = ["Workspace root:", _list_tree(workspace)]
    return "\n".join(lines)


def _merge_usage(total: dict[str, int], usage: dict[str, Any]) -> None:
    for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
        total[key] = total.get(key, 0) + int(usage.get(key, 0) or 0)
    details = usage.get("completion_tokens_details")
    if isinstance(details, dict):
        total["reasoning_tokens"] = total.get("reasoning_tokens", 0) + int(
            details.get("reasoning_tokens", 0) or 0
        )


def call_glm(
    *,
    api_key: str,
    model: str,
    effort: str,
    messages: list[dict[str, str]],
    timeout: int,
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    payload = {
        "model": model,
        "messages": messages,
        "thinking": {"type": "enabled"},
        "reasoning_effort": effort,
    }
    req = urllib.request.Request(
        ZAI_CHAT_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw_bytes = resp.read()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Z.ai HTTP {exc.code}: {body}") from exc

    data = json.loads(raw_bytes.decode("utf-8", errors="replace"))
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise RuntimeError("GLM response missing choices")
    message = choices[0].get("message", {})
    content = message.get("content", "")
    if isinstance(content, list):
        text = "\n".join(
            str(part.get("text", ""))
            for part in content
            if isinstance(part, dict) and part.get("type") == "text"
        ).strip()
    else:
        text = str(content or "").strip()
    if not text:
        raise RuntimeError("GLM returned empty message content")
    usage = data.get("usage", {}) if isinstance(data.get("usage"), dict) else {}
    return text, usage, data


def run_glm_agentic_loop(
    *,
    api_key: str,
    workspace: Path,
    user_prompt: str,
    model: str,
    effort: str,
    timeout: int,
    code_path: Path,
) -> AgentRunResult:
    workspace_code = workspace / "outputs" / code_path.name
    prompt = user_prompt.replace(code_path.as_posix(), workspace_code.as_posix())

    messages: list[dict[str, str]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": prompt + "\n\n" + workspace_bootstrap(workspace),
        },
    ]

    transcript: list[TurnRecord] = []
    raw_turns: list[dict[str, Any]] = []
    usage_total: dict[str, int] = {}
    final_text = ""

    for turn in range(1, MAX_TURNS + 1):
        text, usage, raw = call_glm(
            api_key=api_key,
            model=model,
            effort=effort,
            messages=messages,
            timeout=timeout,
        )
        _merge_usage(usage_total, usage)
        raw_turns.append(raw)

        action = parse_agent_action(text)
        action_name = action.kind if action else "(none)"
        tool_result = ""

        if action is None:
            if extract_code_block(text) is not None:
                final_text = text
                transcript.append(TurnRecord(turn, text, "final_python", "accepted"))
                break
            tool_result = (
                "ERROR: expected exactly one ```agent block, or a final ```python block. "
                "Use list/read/write/run until ready, then action: done with assumptions + python."
            )
        elif action.kind == "done":
            if extract_code_block(text) is None and not workspace_code.exists():
                tool_result = "ERROR: done requires a fenced ```python block or an outputs code file."
            else:
                final_text = text
                tool_result = execute_action(workspace, action)
                transcript.append(TurnRecord(turn, text, "done", tool_result))
                break
        else:
            try:
                tool_result = execute_action(workspace, action)
            except Exception as exc:  # ponytail: surface tool errors back to the model
                tool_result = f"ERROR: {exc}"

        transcript.append(TurnRecord(turn, text, action_name, tool_result))
        messages.append({"role": "assistant", "content": text})
        messages.append(
            {
                "role": "user",
                "content": f"Tool result (turn {turn}):\n\n{tool_result}",
            }
        )
    else:
        raise RuntimeError(f"GLM agentic loop exceeded {MAX_TURNS} turns without final code")

    return AgentRunResult(
        final_text=final_text,
        transcript=transcript,
        usage_total=usage_total,
        raw_turns=raw_turns,
    )


def ingest_workspace_code(workspace: Path, code_path: Path) -> bool:
    workspace_code = workspace / "outputs" / code_path.name
    if not workspace_code.exists():
        return False
    code_path.parent.mkdir(parents=True, exist_ok=True)
    code_path.write_text(workspace_code.read_text(encoding="utf-8"), encoding="utf-8")
    return True


def format_transcript_markdown(result: AgentRunResult) -> str:
    parts = ["# GLM agentic transcript", ""]
    for record in result.transcript:
        parts.extend(
            [
                f"## Turn {record.turn} ({record.action})",
                "",
                record.assistant,
                "",
                "### Tool result",
                "",
                record.tool_result,
                "",
            ]
        )
    parts.append("## Final response")
    parts.append("")
    parts.append(result.final_text)
    return "\n".join(parts).strip() + "\n"
