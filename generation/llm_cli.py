"""Run BoardBench LLM steps through Claude Code CLI, Codex CLI, or legacy pi."""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Literal

LLMMode = Literal["agentic", "oneshot", "judge", "align"]

NONINTERACTIVE_SYSTEM_APPEND = (
    "BoardBench non-interactive step. Answer directly in your response text only. "
    "Do not use tools, shell commands, or repository exploration. "
    "All required context is already in the user message."
)

DISALLOWED_NONINTERACTIVE_TOOLS = (
    "Bash,Edit,Write,Read,Grep,Glob,WebFetch,WebSearch,Task,TodoWrite,NotebookEdit"
)

_TOOL_USE_LINE = re.compile(
    r"(?m)^name:\s*(Bash|Edit|Write|Read|Grep|Glob|WebFetch|WebSearch|Task|TodoWrite|NotebookEdit)\s*$"
)


def get_claude_path() -> str:
    claude_path = shutil.which("claude") or shutil.which("claude.cmd")
    if claude_path is not None:
        return claude_path
    raise FileNotFoundError(
        "Could not find the claude CLI. Install Claude Code and run `claude auth login`."
    )


def get_pi_path() -> str:
    pi_path = shutil.which("pi") or shutil.which("pi.cmd")
    if pi_path is not None:
        return pi_path

    windows_fallback = Path.home() / "AppData/Roaming/npm/pi.cmd"
    if windows_fallback.exists():
        return str(windows_fallback)

    raise FileNotFoundError("Could not find pi or pi.cmd")


def get_npx_path() -> str:
    npx_path = shutil.which("npx") or shutil.which("npx.cmd")
    if npx_path is not None:
        return npx_path
    raise FileNotFoundError("Could not find npx on PATH")


def get_codex_exec_prefix() -> list[str]:
    return [get_npx_path(), "--yes", "@openai/codex", "exec"]


def unique_dirs(paths: list[Path]) -> list[Path]:
    seen: set[str] = set()
    ordered: list[Path] = []
    for path in paths:
        resolved = path.resolve()
        key = resolved.as_posix()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(resolved)
    return ordered


def attachment_add_dirs(file_args: list[Path] | None) -> list[Path]:
    if not file_args:
        return []
    return unique_dirs([path.parent for path in file_args if path.exists()])


def extract_code_block(text: str) -> str | None:
    match = re.search(r"```python\s*(.*?)```", text, re.IGNORECASE | re.DOTALL)
    if match is None:
        return None
    return match.group(1).strip() + "\n"


def extract_code_blocks(text: str) -> list[str]:
    blocks = re.findall(r"```python\s*(.*?)```", text, re.IGNORECASE | re.DOTALL)
    return [block.strip() + "\n" for block in blocks]


def raise_if_bad_llm_text(text: str, *, step: str) -> None:
    lowered = text.lower()
    if "session limit" in lowered or "hit your session limit" in lowered:
        raise RuntimeError(text.strip())

    if _TOOL_USE_LINE.search(text):
        raise RuntimeError(
            f"{step} used tools instead of a direct answer; all context is already in the prompt"
        )

    if re.search(r"(?m)^name:\s*\w+\s*$", text) and "input:" in text and "command:" in text:
        raise RuntimeError(f"{step} returned tool-call output instead of a direct answer")


def ensure_direct_llm_response(result: subprocess.CompletedProcess[str], *, step: str) -> str:
    if result.returncode != 0:
        raise RuntimeError(llm_failure_message(result, step=step))
    text = result.stdout or ""
    raise_if_bad_llm_text(text, step=step)
    return text


def require_code_block_response(result: subprocess.CompletedProcess[str], *, step: str) -> str:
    text = ensure_direct_llm_response(result, step=step)
    code = extract_code_block(text)
    if code is None:
        raise RuntimeError(f"No fenced python block in {step} response")
    return code


def require_code_blocks(result: subprocess.CompletedProcess[str], *, step: str, count: int) -> list[str]:
    text = ensure_direct_llm_response(result, step=step)
    blocks = extract_code_blocks(text)
    if len(blocks) < count:
        raise RuntimeError(
            f"{step} response must contain {count} fenced python blocks; found {len(blocks)}"
        )
    return blocks


def build_llm_command(
    backend: str,
    model: str,
    effort: str | None,
    *,
    mode: LLMMode,
    add_dirs: list[Path] | None = None,
    file_args: list[Path] | None = None,
) -> list[str]:
    """Build a subprocess command for one BoardBench LLM step."""

    if backend == "pi":
        return _build_pi_command(model, mode=mode, file_args=file_args)

    if backend == "codex":
        return _build_codex_command(
            model,
            mode=mode,
            cwd=add_dirs[0] if add_dirs else None,
            file_args=file_args,
            effort=effort,
        )

    command = [
        get_claude_path(),
        "-p",
        "--model",
        model,
        "--no-session-persistence",
        "--disable-slash-commands",
    ]
    if effort:
        command += ["--effort", effort]

    extra_dirs = attachment_add_dirs(file_args)
    for directory in unique_dirs(list(add_dirs or []) + extra_dirs):
        command += ["--add-dir", directory.as_posix()]

    if mode == "agentic":
        command += ["--permission-mode", "bypassPermissions"]
    elif mode in {"oneshot", "judge", "align"}:
        command += [
            "--permission-mode",
            "default",
            "--append-system-prompt",
            NONINTERACTIVE_SYSTEM_APPEND,
        ]
        if file_args and mode in {"oneshot", "judge"}:
            command += ["--tools", "Read"]
        else:
            command += ["--tools", ""]
            command += ["--disallowedTools", DISALLOWED_NONINTERACTIVE_TOOLS]

    return command


def _build_pi_command(
    model: str,
    *,
    mode: LLMMode,
    file_args: list[Path] | None,
) -> list[str]:
    command = [
        get_pi_path(),
        "-p",
        "--no-session",
        "--model",
        model,
        "--no-extensions",
        "--no-skills",
        "--no-prompt-templates",
        "--no-context-files",
    ]
    if mode in {"oneshot", "judge", "align"}:
        command.append("--no-tools")
    else:
        command += ["--tools", "read,write,edit,bash,grep,find,ls"]

    for path in file_args or []:
        command.append("@" + path.as_posix())
    return command


def _build_codex_command(
    model: str,
    *,
    mode: LLMMode,
    cwd: Path | None,
    file_args: list[Path] | None,
    effort: str | None,
) -> list[str]:
    command = get_codex_exec_prefix() + [
        "--ephemeral",
        "--skip-git-repo-check",
    ]
    if model and model not in {"default", "auto"}:
        command += ["-m", model]
    if effort:
        command += ["-c", f'model_reasoning_effort="{effort}"']

    if mode == "agentic":
        command += ["-s", "workspace-write"]
    else:
        command += ["-s", "read-only"]

    if cwd is not None:
        command += ["-C", Path(cwd).resolve().as_posix()]

    for directory in attachment_add_dirs(file_args):
        command += ["--add-dir", directory.as_posix()]

    return command


def run_codex_subprocess(
    command: list[str],
    *,
    prompt_text: str,
    output_message_path: Path,
    timeout: int,
    cwd: str | Path | None = None,
) -> subprocess.CompletedProcess[str]:
    prompt_bytes = prompt_text.encode("utf-8", errors="replace")
    full_command = command + ["--output-last-message", output_message_path.as_posix(), "-"]
    run_cwd = str(Path(cwd).resolve()) if cwd is not None else str(output_message_path.parent.resolve())
    completed = subprocess.run(
        full_command,
        input=prompt_bytes,
        capture_output=True,
        timeout=timeout,
        cwd=run_cwd,
    )
    stdout = completed.stdout.decode("utf-8", errors="replace") if completed.stdout else ""
    stderr = completed.stderr.decode("utf-8", errors="replace") if completed.stderr else ""
    return subprocess.CompletedProcess(
        full_command,
        completed.returncode,
        stdout,
        stderr,
    )


def _command_uses_codex(command: list[str]) -> bool:
    joined = " ".join(command)
    return "@openai/codex" in joined or joined.rstrip().endswith("codex exec")


def run_llm_subprocess(
    command: list[str],
    *,
    prompt_text: str,
    cwd: str | Path | None = None,
    timeout: int,
    output_dir: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    if _command_uses_codex(command):
        scratch_dir = output_dir or Path.cwd() / "outputs"
        scratch_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            prefix="boardbench_llm_",
            suffix=".md",
            delete=False,
            dir=scratch_dir,
        ) as tmp:
            message_path = Path(tmp.name)
        try:
            repo_cwd = Path(output_dir).resolve().parent if output_dir is not None else Path.cwd()
            result = run_codex_subprocess(
                command,
                prompt_text=prompt_text,
                output_message_path=message_path,
                timeout=timeout,
                cwd=repo_cwd,
            )
            response_text = message_path.read_text(encoding="utf-8") if message_path.exists() else ""
            if result.returncode == 0 and not response_text.strip():
                response_text = result.stdout or ""
            return subprocess.CompletedProcess(
                command,
                result.returncode,
                response_text,
                result.stderr or "",
            )
        finally:
            message_path.unlink(missing_ok=True)

    return subprocess.run(
        command,
        input=prompt_text,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=str(cwd) if cwd is not None else None,
    )


def llm_failure_message(result: subprocess.CompletedProcess[str], *, step: str) -> str:
    stderr = (result.stderr or "").strip()
    stdout = (result.stdout or "").strip()
    detail = stderr or stdout or f"{step} call failed"
    return detail
