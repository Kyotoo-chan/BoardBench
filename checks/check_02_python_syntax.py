from __future__ import annotations

import ast

from common import CheckContext


def run(ctx: CheckContext) -> str | None:
    if ctx.code_path.suffix.lower() != ".py":
        return f"generated result is not a .py file: {ctx.code_path.name}"

    try:
        source = ctx.code_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        return f"generated result is not UTF-8 text: {exc}"

    try:
        ast.parse(source, filename=str(ctx.code_path))
    except SyntaxError as exc:
        return f"invalid Python syntax at line {exc.lineno}: {exc.msg}"

    return None
