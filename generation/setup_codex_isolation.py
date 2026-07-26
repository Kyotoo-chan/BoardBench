#!/usr/bin/env python3
"""One-time Windows setup for BoardBench's native Codex sandbox."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from codex_native import REPO_ROOT, _isolated_codex_home, verify_codex_isolation


def sandbox_group_sid() -> str:
    command = (
        "$account = New-Object System.Security.Principal.NTAccount($env:COMPUTERNAME, 'CodexSandboxUsers'); "
        "$account.Translate([System.Security.Principal.SecurityIdentifier]).Value"
    )
    return subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command", command],
        check=True, capture_output=True, text=True,
    ).stdout.strip()


def main() -> int:
    if os.name != "nt":
        raise SystemExit("setup is only required on Windows")
    sid = sandbox_group_sid()
    subprocess.run(
        ["icacls.exe", str(REPO_ROOT), "/deny", f"*{sid}:(OI)(CI)(F)"],
        check=True,
    )
    npx = Path(os.environ.get("NPX_PATH", r"C:\Program Files\nodejs\npx.cmd"))
    with _isolated_codex_home() as codex_home:
        verify_codex_isolation(npx, codex_home)
    print("BoardBench Codex isolation configured and verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
