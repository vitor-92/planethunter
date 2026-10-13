"""Network access with timeout, retry with exponential backoff and atomic disk writes.

Only ingest, mirror sync and deep vetting may import this module.
"""

from __future__ import annotations

import random
import time
from pathlib import Path

import requests

USER_AGENT = "planethunter/0.1 (exoplanet candidate search; contact via repo)"
_session: requests.Session | None = None


def session() -> requests.Session:
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers["User-Agent"] = USER_AGENT
    return _session


def get_with_retry(
    url: str, *, timeout: float = 60.0, retries: int = 5, stream: bool = False
) -> requests.Response:
    """GET with exponential backoff (1, 2, 4, 8... s + jitter). Raises after `retries` failures."""
    last: Exception | None = None
    for attempt in range(retries):
        try:
            resp = session().get(url, timeout=timeout, stream=stream)
            if resp.status_code in (429, 500, 502, 503, 504):
                raise requests.HTTPError(f"HTTP {resp.status_code}", response=resp)
            resp.raise_for_status()
            return resp
        except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as exc:
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if status is not None and 400 <= status < 500 and status != 429:
                raise
            last = exc
            time.sleep(min(60.0, 2**attempt) + random.uniform(0, 1))
    raise RuntimeError(f"failed after {retries} attempts: {url}") from last


def download_file(url: str, dest: Path, *, timeout: float = 120.0, retries: int = 5) -> Path:
    """Download `url` to `dest` (atomic write via .part). Skips if `dest` already exists."""
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    resp = get_with_retry(url, timeout=timeout, retries=retries, stream=True)
    with tmp.open("wb") as fh:
        for chunk in resp.iter_content(chunk_size=1 << 20):
            fh.write(chunk)
    tmp.replace(dest)
    return dest
