#!/usr/bin/env python3
"""Verify that native Codex cannot read outside its temporary workspace."""

import shutil

try:
    from generation.codex_native import _isolated_codex_home, verify_codex_isolation
except ModuleNotFoundError:  # Direct script execution.
    from codex_native import _isolated_codex_home, verify_codex_isolation


npx = shutil.which("npx") or shutil.which("npx.cmd")
if not npx:
    raise SystemExit("npx is required")
with _isolated_codex_home() as codex_home:
    verify_codex_isolation(npx, codex_home)
print("Codex workspace isolation PASS")
