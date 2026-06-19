from __future__ import annotations

from common import CheckContext


def run(ctx: CheckContext) -> str | None:
    if not ctx.code_path.exists():
        return f"missing generated result: {ctx.code_path}"
    if not ctx.code_path.is_file():
        return f"generated result is not a file: {ctx.code_path}"
    if ctx.code_path.stat().st_size == 0:
        return f"generated result is empty: {ctx.code_path}"
    return None
