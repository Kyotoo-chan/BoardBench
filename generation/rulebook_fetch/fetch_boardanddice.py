#!/usr/bin/env python3
"""Download rulebook PDFs linked from boardanddice.com/download/."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from generation.rulebook_fetch._common import download_file, sanitize_filename  # noqa: E402

DOWNLOAD_PAGE = "https://boardanddice.com/download/"


def discover_pdf_links(page_url: str) -> list[tuple[str, str]]:
    request = Request(page_url, headers={"User-Agent": "BoardBench-rulebook-fetch/1.0"})
    with urlopen(request, timeout=120) as response:
        html = response.read().decode("utf-8", errors="replace")

    links: list[tuple[str, str]] = []
    for match in re.finditer(r'href="([^"]+\.pdf[^"]*)"', html, flags=re.IGNORECASE):
        href = match.group(1)
        url = urljoin(page_url, href)
        label = Path(url).stem.replace("-", " ").replace("_", " ")
        links.append((label, url))
    # dedupe by URL
    seen: set[str] = set()
    unique: list[tuple[str, str]] = []
    for label, url in links:
        if url in seen:
            continue
        seen.add(url)
        unique.append((label, url))
    return unique


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", action="append", default=[], help="Substring filter on link label or URL")
    parser.add_argument("--all", action="store_true", help="Download every PDF on the page")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--page", default=DOWNLOAD_PAGE)
    args = parser.parse_args()

    links = discover_pdf_links(args.page)
    if args.query:
        needles = [q.lower() for q in args.query]
        links = [
            item
            for item in links
            if any(needle in item[0].lower() or needle in item[1].lower() for needle in needles)
        ]
    elif not args.all:
        raise SystemExit("Provide --query <substring> or --all")

    if not links:
        raise SystemExit("No PDF links matched")

    args.out.mkdir(parents=True, exist_ok=True)
    for label, url in links:
        dest = args.out / sanitize_filename(f"{label}.pdf")
        print(f"GET {label} -> {dest.name}")
        download_file(url, dest)

    print(f"OK {len(links)} file(s) -> {args.out.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
