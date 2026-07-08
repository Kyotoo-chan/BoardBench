#!/usr/bin/env python3
"""Download rulebook PDFs from a plain URL list (one URL per line).

Example::

  python generation/rulebook_fetch/fetch_direct.py \\
    --urls generation/rulebook_fetch/examples/direct_urls.txt \\
    --out inputs/games/_bulk
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from generation.rulebook_fetch._common import download_file, sanitize_filename  # noqa: E402


def filename_from_url(url: str) -> str:
    path = unquote(urlparse(url).path)
    name = Path(path).name
    if not name.lower().endswith(".pdf"):
        name = f"{name or 'rulebook'}.pdf"
    return sanitize_filename(name)


def load_urls(path: Path) -> list[str]:
    urls: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        token = line.strip()
        if not token or token.startswith("#"):
            continue
        urls.append(token)
    return urls


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--urls", type=Path, required=True, help="Text file with one PDF URL per line")
    parser.add_argument("--out", type=Path, required=True, help="Output directory for PDFs")
    parser.add_argument("--prefix", default="", help="Optional filename prefix")
    args = parser.parse_args()

    urls = load_urls(args.urls)
    if not urls:
        raise SystemExit(f"No URLs in {args.urls.as_posix()}")

    for url in urls:
        name = f"{args.prefix}{filename_from_url(url)}"
        dest = args.out / name
        print(f"GET {url} -> {dest.as_posix()}")
        download_file(url, dest)
    print(f"OK {len(urls)} file(s) -> {args.out.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
