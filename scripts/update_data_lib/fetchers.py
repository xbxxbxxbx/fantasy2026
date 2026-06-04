from __future__ import annotations

import json
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


def fetch_html(url: str) -> str:
    parts = urlsplit(url)
    referer = f"{parts.scheme}://{parts.netloc}/" if parts.scheme and parts.netloc else url
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Referer": referer,
    }
    retry_delays = [0, 2, 5]

    last_error: Exception | None = None
    for delay in retry_delays:
        if delay:
            time.sleep(delay)

        request = Request(url, headers=headers)
        try:
            with urlopen(request, timeout=30) as response:
                return response.read().decode("utf-8", errors="replace")
        except HTTPError as exc:
            last_error = exc
            if exc.code not in {403, 429}:
                raise
        except URLError as exc:
            last_error = exc

    if last_error:
        raise last_error
    raise RuntimeError(f"Failed to fetch {url}")


def fetch_json(url: str, payload: dict, headers: dict[str, str] | None = None) -> dict:
    parts = urlsplit(url)
    referer = f"{parts.scheme}://{parts.netloc}/" if parts.scheme and parts.netloc else url
    request_headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0 Safari/537.36"
        ),
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": referer,
    }
    if headers:
        request_headers.update(headers)

    body = json.dumps(payload).encode("utf-8")
    request = Request(url, data=body, headers=request_headers, method="POST")
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))
