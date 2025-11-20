"\"\"\"Lightweight helpers for Twitter/X thread detection.\"\""

from __future__ import annotations

import re

TWITTER_STATUS_PATTERN = re.compile(
    r"https?://(?:www\.)?(?:mobile\.)?(?:x|twitter)\.com/[^/]+/status(?:es)?/(?P<id>\d+)",
    re.IGNORECASE,
)


def looks_like_twitter_status(url: str) -> bool:
    """Return True if the URL points to a Twitter/X status page."""
    return bool(TWITTER_STATUS_PATTERN.search(url))

