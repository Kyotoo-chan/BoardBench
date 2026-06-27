"""Render PDF rulebook pages when pdftoppm is unavailable."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def get_pdftoppm_path() -> str | None:
    for candidate in (
        shutil.which("pdftoppm"),
        shutil.which("pdftoppm.exe"),
        Path.home() / "AppData/Local/Programs/MiKTeX/miktex/bin/x64/pdftoppm.exe",
    ):
        if candidate and Path(candidate).exists():
            return str(candidate)
    return None


def render_pdf_pages_pymupdf(rules_path: Path, page_dir: Path, *, dpi: int = 180) -> list[Path]:
    import fitz  # pymupdf

    page_dir.mkdir(parents=True, exist_ok=True)
    for old_page in page_dir.glob("page-*.png"):
        old_page.unlink()

    doc = fitz.open(rules_path)
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    pages: list[Path] = []
    for index in range(len(doc)):
        out_path = page_dir / f"page-{index + 1:03d}.png"
        pix = doc.load_page(index).get_pixmap(matrix=matrix, alpha=False)
        pix.save(out_path.as_posix())
        pages.append(out_path)
    doc.close()
    if not pages:
        raise RuntimeError(f"No PDF pages rendered from {rules_path}")
    return pages


def render_pdf_pages(rules_path: Path, page_dir: Path, *, dpi: int = 180) -> list[Path]:
    pdftoppm = get_pdftoppm_path()
    if pdftoppm is not None:
        page_dir.mkdir(parents=True, exist_ok=True)
        for old_page in page_dir.glob("page-*.png"):
            old_page.unlink()
        prefix = page_dir / "page"
        subprocess.run(
            [pdftoppm, "-png", "-r", str(dpi), str(rules_path), str(prefix)],
            check=True,
            capture_output=True,
            text=True,
        )
        pages = sorted(page_dir.glob("page-*.png"))
        if pages:
            return pages
    return render_pdf_pages_pymupdf(rules_path, page_dir, dpi=dpi)
