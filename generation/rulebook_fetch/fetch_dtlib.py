#!/usr/bin/env python3
"""Bulk-download rulebooks from the Dice Tower Library mirror.

Parses ``dtlibrary.html`` or ``dtlist.txt`` and fetches PDFs from
``https://cs.uwaterloo.ca/~dtompkin/archive/dtlib/``.

Example::

  python generation/rulebook_fetch/fetch_dtlib.py --query havannah --out inputs/games/_bulk
  python generation/rulebook_fetch/fetch_dtlib.py --all --out inputs/games/_bulk --limit 20
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urljoin

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from generation.rulebook_fetch._common import download_file, sanitize_filename  # noqa: E402

DTLIB_INDEX = "https://cs.uwaterloo.ca/~dtompkin/dtlib/dtlibrary.html"
DTLIB_PAGE_BASE = "https://cs.uwaterloo.ca/~dtompkin/dtlib/"


def fetch_index(url: str) -> str:
    from urllib.request import Request, urlopen

    request = Request(url, headers={"User-Agent": "BoardBench-rulebook-fetch/1.0"})
    with urlopen(request, timeout=120) as response:
        return response.read().decode("utf-8", errors="replace")


def parse_dtlib_entries(html: str) -> list[tuple[str, str]]:
    """Return (game_title, absolute_pdf_url) pairs."""
    entries: list[tuple[str, str]] = []
    pattern = re.compile(
        r'<span class="gtitle">([^<]+)</span>.*?<a class="glink" href="([^"]+\.pdf)">',
        flags=re.DOTALL | re.IGNORECASE,
    )
    for title, href in pattern.findall(html):
        entries.append((title.strip(), urljoin(DTLIB_PAGE_BASE, href.strip())))
    return entries


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", action="append", default=[], help="Case-insensitive substring filter on game title")
    parser.add_argument("--all", action="store_true", help="Download every indexed PDF (use with care)")
    parser.add_argument("--limit", type=int, default=0, help="Max downloads after filtering (0 = no limit)")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--index-url", default=DTLIB_INDEX)
    args = parser.parse_args()

    if not args.all and not args.query:
        raise SystemExit("Provide --query <substring> or --all")

    html = fetch_index(args.index_url)
    entries = parse_dtlib_entries(html)
    selected = entries
    if args.query:
        needles = [q.lower() for q in args.query]
        selected = [
            item for item in entries if any(needle in item[0].lower() for needle in needles)
        ]
    if args.limit > 0:
        selected = selected[: args.limit]

    if not selected:
        raise SystemExit("No matching rulebooks found")

    for title, url in selected:
        safe = sanitize_filename(f"{title}__{Path(url).name}")
        dest = args.out / safe
        print(f"GET {title} -> {dest.name}")
        download_file(url, dest)

    print(f"OK {len(selected)} file(s) -> {args.out.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
