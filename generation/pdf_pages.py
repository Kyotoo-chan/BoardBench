"""Render complete PDF rulebooks and record the derived model inputs."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_manifest(
    rules_path: Path,
    page_dir: Path,
    pages: list[Path],
    *,
    dpi: int,
    renderer: str,
    renderer_version: str,
) -> None:
    manifest = {
        "version": 1,
        "source_file": rules_path.name,
        "source_sha256": _sha256(rules_path),
        "dpi": dpi,
        "renderer": renderer,
        "renderer_version": renderer_version,
        "pages": [
            {"page": index, "file": page.name, "sha256": _sha256(page)}
            for index, page in enumerate(pages, start=1)
        ],
    }
    (page_dir / "render_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _pdftoppm_version(pdftoppm: str) -> str:
    result = subprocess.run(
        [pdftoppm, "-v"],
        capture_output=True,
        text=True,
        check=False,
    )
    lines = (result.stderr or result.stdout).strip().splitlines()
    return lines[0] if lines else "unknown"


def _page_number(path: Path) -> int:
    return int(path.stem.rsplit("-", 1)[1])


def get_pdftoppm_path() -> str | None:
    for candidate in (
        shutil.which("pdftoppm"),
        shutil.which("pdftoppm.exe"),
        Path.home() / "AppData/Local/Programs/MiKTeX/miktex/bin/x64/pdftoppm.exe",
    ):
        if candidate and Path(candidate).exists():
            return str(candidate)
    return None


def render_pdf_pages_pymupdf(rules_path: Path, page_dir: Path, *, dpi: int = 150) -> list[Path]:
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
    _write_manifest(
        rules_path,
        page_dir,
        pages,
        dpi=dpi,
        renderer="PyMuPDF",
        renderer_version=str(getattr(fitz, "VersionBind", "unknown")),
    )
    return pages


def render_pdf_pages(rules_path: Path, page_dir: Path, *, dpi: int = 150) -> list[Path]:
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
        pages = sorted(page_dir.glob("page-*.png"), key=_page_number)
        if pages:
            _write_manifest(
                rules_path,
                page_dir,
                pages,
                dpi=dpi,
                renderer="pdftoppm",
                renderer_version=_pdftoppm_version(pdftoppm),
            )
            return pages
    return render_pdf_pages_pymupdf(rules_path, page_dir, dpi=dpi)
