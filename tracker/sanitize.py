"""Cleaning of every text and URL that comes from an external source.

Scraped job offers, RSS entries and generated analyses are displayed on the
site. The site never interprets them as HTML (textContent only) and checks
URLs again before using them, but data is also cleaned here, at collection
time, so that what is stored in data/*.json is plain text and safe links:
defence in depth.
"""

from __future__ import annotations

import html
import re
from urllib.parse import urlsplit

MAX_URL_LENGTH = 2048

# Content of these elements is never text worth keeping.
_DROP_BLOCKS = re.compile(r"<(script|style|noscript|iframe|object|embed|svg|math|template)\b.*?</\1\s*>",
                          re.IGNORECASE | re.DOTALL)
_TAG = re.compile(r"<[a-zA-Z/!?][^>]*>|<[a-zA-Z/!?][^>]*$")   # tags (and a tag cut by truncation), not "a < b"
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f​-‏‪-‮⁦-⁩]")


def clean_text(value, limit: int = 500) -> str:
    """Plain text: HTML entities decoded, tags and their dangerous content removed,
    control and bidi-override characters removed, whitespace collapsed, length capped."""
    if value is None:
        return ""
    text = str(value)
    # Decode twice so that "&lt;script&gt;" (escaped markup inside RSS) is removed too.
    for _ in range(2):
        text = _DROP_BLOCKS.sub(" ", text)
        text = _TAG.sub(" ", text)
        text = html.unescape(text)
    text = _DROP_BLOCKS.sub(" ", text)
    text = _TAG.sub(" ", text)
    text = _CONTROL.sub("", text)
    text = " ".join(text.split())
    if len(text) > limit:
        text = text[: limit - 1].rstrip() + "…"
    return text


def safe_url(value) -> str:
    """The URL if it is an absolute http(s) URL with a host, otherwise "".

    Rejects javascript:, data:, vbscript:, file:, protocol-relative URLs,
    URLs containing whitespace or control characters, and overlong URLs."""
    if not value:
        return ""
    url = html.unescape(str(value)).strip()
    if len(url) > MAX_URL_LENGTH or re.search(r"[\s\x00-\x1f\x7f<>\"'`]", url):
        return ""
    try:
        parts = urlsplit(url)
    except ValueError:
        return ""
    if parts.scheme.lower() not in ("http", "https") or not parts.netloc or parts.username or parts.password:
        return ""
    return url
