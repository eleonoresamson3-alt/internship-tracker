"""Polite HTTP client: honest user-agent, per-host rate limit, robots.txt."""

from __future__ import annotations

import logging
import time
import urllib.robotparser
from urllib.parse import urlsplit

import requests

from . import config

log = logging.getLogger(__name__)


class RobotsDisallowed(Exception):
    """Raised when robots.txt forbids fetching a URL."""


class PoliteClient:
    def __init__(
        self,
        user_agent: str = config.USER_AGENT,
        min_delay: float = config.MIN_DELAY_PER_HOST,
        timeout: float = config.REQUEST_TIMEOUT,
    ):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": user_agent,
                "Accept-Language": "en-GB,en;q=0.9,fr;q=0.8",
            }
        )
        self.user_agent = user_agent
        self.min_delay = min_delay
        self.timeout = timeout
        self._last_request: dict[str, float] = {}
        self._robots: dict[str, urllib.robotparser.RobotFileParser | None] = {}

    # -- robots.txt -------------------------------------------------------

    def _robots_for(self, scheme: str, host: str):
        key = f"{scheme}://{host}"
        if key not in self._robots:
            parser = urllib.robotparser.RobotFileParser()
            try:
                self._wait(host)
                resp = self.session.get(f"{key}/robots.txt", timeout=self.timeout)
                if resp.status_code >= 400:
                    # No robots.txt (or not readable): nothing is disallowed.
                    parser = None
                else:
                    parser.parse(resp.text.splitlines())
            except requests.RequestException:
                parser = None
            self._robots[key] = parser
        return self._robots[key]

    def allowed(self, url: str) -> bool:
        parts = urlsplit(url)
        parser = self._robots_for(parts.scheme, parts.netloc)
        return parser is None or parser.can_fetch(self.user_agent, url)

    # -- rate limiting ----------------------------------------------------

    def _wait(self, host: str) -> None:
        last = self._last_request.get(host)
        if last is not None:
            delay = self.min_delay - (time.monotonic() - last)
            if delay > 0:
                time.sleep(delay)
        self._last_request[host] = time.monotonic()

    # -- requests ---------------------------------------------------------

    def request(self, method: str, url: str, retries: int = 2, **kwargs) -> requests.Response:
        if not self.allowed(url):
            raise RobotsDisallowed(f"robots.txt disallows {url}")
        host = urlsplit(url).netloc
        kwargs.setdefault("timeout", self.timeout)
        for attempt in range(retries + 1):
            self._wait(host)
            try:
                resp = self.session.request(method, url, **kwargs)
            except requests.RequestException:
                if attempt == retries:
                    raise
                time.sleep(2 ** attempt * 2)
                continue
            if resp.status_code in (429, 502, 503, 504) and attempt < retries:
                retry_after = resp.headers.get("Retry-After", "")
                time.sleep(int(retry_after) if retry_after.isdigit() else 2 ** attempt * 5)
                continue
            resp.raise_for_status()
            return resp
        raise RuntimeError("unreachable")

    def get(self, url: str, **kwargs) -> requests.Response:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> requests.Response:
        return self.request("POST", url, **kwargs)

    def get_json(self, url: str, **kwargs):
        kwargs.setdefault("headers", {"Accept": "application/json"})
        return self.get(url, **kwargs).json()

    def post_json(self, url: str, payload: dict, **kwargs):
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        headers.update(kwargs.pop("headers", {}))
        return self.post(url, json=payload, headers=headers, **kwargs).json()
