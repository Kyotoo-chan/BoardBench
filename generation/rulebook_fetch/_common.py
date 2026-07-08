"""Shared helpers for rulebook PDF bulk download scripts."""

from __future__ import annotations

import re
import time
import urllib.error
import urllib.request
from pathlib import Path

USER_AGENT = "BoardBench-rulebook-fetch/1.0 (+local thesis repo)"


def sanitize_filename(name: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*]+', "_", name.strip())
    return cleaned or "rulebook.pdf"


def download_file(
    url: str,
    dest: Path,
    *,
    cookie_header: str | None = None,
    timeout: int = 120,
    retries: int = 3,
) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    headers = {"User-Agent": USER_AGENT}
    if cookie_header:
        headers["Cookie"] = cookie_header

    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                data = response.read()
            if not data:
                raise RuntimeError(f"empty response from {url}")
            dest.write_bytes(data)
            return dest
        except (urllib.error.URLError, TimeoutError, RuntimeError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(attempt)
    raise RuntimeError(f"download failed for {url}: {last_error}") from last_error
