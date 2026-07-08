#!/usr/bin/env python3
"""Download rulebook PDFs from BoardGameGeek file pages.

BGG requires a logged-in session. Export your browser cookies for
``boardgamegeek.com`` into a Netscape cookie file and pass ``--cookies``.

Example::

  python generation/rulebook_fetch/fetch_bgg.py \\
    --filepage 303599 \\
    --out inputs/games/umami/game_rules.pdf \\
    --cookies %USERPROFILE%\\.boardbench_bgg_cookies.txt
"""

from __future__ import annotations

import argparse
import http.cookiejar
import re
import sys
from pathlib import Path
from urllib.request import HTTPCookieProcessor, Request, build_opener

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from generation.rulebook_fetch._common import download_file  # noqa: E402


def load_cookie_header(cookie_file: Path) -> str:
    jar = http.cookiejar.MozillaCookieJar(cookie_file)
    jar.load(ignore_discard=True, ignore_expires=True)
    parts = [f"{cookie.name}={cookie.value}" for cookie in jar]
    if not parts:
        raise RuntimeError(f"No cookies loaded from {cookie_file.as_posix()}")
    return "; ".join(parts)


def resolve_filepage_pdf(filepage_id: int, cookie_header: str) -> tuple[str, str]:
    page_url = f"https://boardgamegeek.com/filepage/{filepage_id}"
    request = Request(page_url, headers={"User-Agent": "BoardBench-rulebook-fetch/1.0", "Cookie": cookie_header})
    opener = build_opener(HTTPCookieProcessor())
    with opener.open(request, timeout=120) as response:
        html = response.read().decode("utf-8", errors="replace")

    match = re.search(r'href="(/filepage/download/[^"]+\.pdf[^"]*)"', html, flags=re.IGNORECASE)
    if not match:
        match = re.search(r'href="(/filepage/download/[^"]+)"', html, flags=re.IGNORECASE)
    if not match:
        raise RuntimeError(f"No download link on filepage {filepage_id}; check login cookies")

    href = match.group(1)
    pdf_url = f"https://boardgamegeek.com{href}"
    title_match = re.search(r"<title>([^<]+)</title>", html, flags=re.IGNORECASE)
    title = title_match.group(1).strip() if title_match else f"bgg_{filepage_id}"
    return pdf_url, title


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--filepage", type=int, action="append", required=True)
    parser.add_argument("--out", type=Path, required=True, help="Output file or directory")
    parser.add_argument("--cookies", type=Path, required=True, help="Netscape-format cookie jar")
    args = parser.parse_args()

    cookie_header = load_cookie_header(args.cookies)
    out_is_dir = args.out.suffix.lower() != ".pdf" or len(args.filepage) > 1
    if out_is_dir:
        args.out.mkdir(parents=True, exist_ok=True)

    for filepage_id in args.filepage:
        pdf_url, title = resolve_filepage_pdf(filepage_id, cookie_header)
        if out_is_dir:
            dest = args.out / f"bgg_{filepage_id}.pdf"
        else:
            dest = args.out
        print(f"GET filepage/{filepage_id} ({title}) -> {dest.as_posix()}")
        download_file(pdf_url, dest, cookie_header=cookie_header)

    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
