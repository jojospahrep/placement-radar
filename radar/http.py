"""Polite JSON HTTP client: identifies itself, retries transient errors, throttles per host."""
import json
import random
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

USER_AGENT = "PlacementRadar/1.0 (+https://github.com/jojospahrep/placement-radar; UK engineering placements board)"
MIN_INTERVAL = 0.35  # seconds between requests to the same host

_last_hit: dict[str, float] = {}
_lock = threading.Lock()


def _throttle(url: str) -> None:
    host = urllib.parse.urlsplit(url).netloc
    while True:
        with _lock:
            wait = _last_hit.get(host, 0) + MIN_INTERVAL - time.monotonic()
            if wait <= 0:
                _last_hit[host] = time.monotonic()
                return
        time.sleep(wait)


def request_json(url: str, body: dict | None = None, retries: int = 3, timeout: int = 30):
    data = json.dumps(body).encode() if body is not None else None
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    for attempt in range(retries):
        _throttle(url)
        try:
            req = urllib.request.Request(url, data=data, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504) or attempt == retries - 1:
                raise
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if attempt == retries - 1:
                raise
        time.sleep(2 ** attempt + random.random())


get_json = request_json


def post_json(url: str, body: dict, **kw):
    return request_json(url, body=body, **kw)
