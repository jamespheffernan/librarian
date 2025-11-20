"""Twitter thread extractor using snscrape."""

from __future__ import annotations

import importlib.util
import logging
import sys
from datetime import datetime
from importlib.machinery import PathFinder
from types import ModuleType
from typing import Any, Dict, Iterable, List, Optional

imp_module = sys.modules.get("imp")
if imp_module is None:
    imp_module = ModuleType("imp")
    sys.modules["imp"] = imp_module

from src.extractors.twitter_utils import TWITTER_STATUS_PATTERN


def _ensure_imp_find_module() -> None:
    """Patch imp.find_module to use importlib on Python 3.13+."""
    if hasattr(imp_module, "find_module"):
        return

    def _find_module(name: str, path: Optional[list[str]] = None):
        spec = PathFinder().find_spec(name, path)
        if spec is None:
            raise ModuleNotFoundError(name)
        origin = spec.origin or ""
        return None, origin, ("", "", 0)

    setattr(imp_module, "find_module", _find_module)


_ensure_imp_find_module()

try:
    import snscrape.modules.twitter as sntwitter
except ImportError:  # pragma: no cover
    sntwitter = None

logger = logging.getLogger(__name__)


def _ensure_snscrape_available() -> None:
    if sntwitter is None:
        raise ImportError(
            "snscrape is required for Twitter thread extraction. "
            "Install it with: pip install snscrape"
        )


def _extract_status_id(url: str) -> str:
    match = TWITTER_STATUS_PATTERN.search(url)
    if not match:
        raise ValueError(f"URL does not look like a Twitter status: {url}")
    return match.group("id")


def _format_tweet_text(tweet: Any) -> str:
    candidate_attrs = ["renderedContent", "content", "rawContent", "text"]
    for attr in candidate_attrs:
        text = getattr(tweet, attr, None)
        if text and isinstance(text, str):
            return text.strip()
    return ""


def _gather_media_urls(tweet: Any) -> List[str]:
    urls: List[str] = []
    for media in getattr(tweet, "media", []) or []:
        url = getattr(media, "fullUrl", None) or getattr(media, "previewUrl", None)
        if url:
            urls.append(url)
    return urls


def extract_twitter_thread(
    url: str,
    max_tweets: int = 50,
) -> Dict[str, Any]:
    """
    Extract a Twitter/X thread from a public status URL.

    Args:
        url: Link to the first tweet in the thread.
        max_tweets: Maximum number of tweets to follow in the thread.

    Returns:
        Dictionary containing text content, metadata, and a friendly title.
    """
    status_id = _extract_status_id(url)
    _ensure_snscrape_available()

    try:
        tweet_scraper = sntwitter.TwitterTweetScraper(status_id)
    except AttributeError as exc:
        raise RuntimeError(f"snscrape TwitterTweetScraper is unavailable: {exc}")

    tweet_iter = tweet_scraper.get_items()
    try:
        root_tweet = next(tweet_iter)
    except StopIteration:
        raise ValueError(f"Twitter status not found: {url}")

    author = getattr(root_tweet.user, "username", "unknown")
    conversation_id = getattr(root_tweet, "conversationId", status_id)
    tweets: List[Any] = [root_tweet]

    search_query = f"conversation_id:{conversation_id} from:{author}"
    search_scraper = sntwitter.TwitterSearchScraper(search_query)

    for tweet in search_scraper.get_items():
        if len(tweets) >= max_tweets:
            break
        if tweet.id == root_tweet.id:
            continue
        username = getattr(tweet.user, "username", "")
        if username.lower() != author.lower():
            continue
        tweets.append(tweet)

    tweets_sorted = sorted(tweets, key=lambda t: getattr(t, "date", datetime.min))
    if not tweets_sorted:
        raise ValueError(f"No tweets found for thread: {url}")

    all_media_urls: List[str] = []
    lines: List[str] = []
    for index, tweet in enumerate(tweets_sorted, start=1):
        tweet_date = getattr(tweet, "date", None)
        timestamp = (
            tweet_date.strftime("%Y-%m-%d %H:%M:%S")
            if isinstance(tweet_date, datetime)
            else "Unknown time"
        )
        lines.append(f"Tweet {index}/{len(tweets_sorted)} ({timestamp} UTC)")
        text = _format_tweet_text(tweet)
        if text:
            lines.append(text)

        media_urls = _gather_media_urls(tweet)
        if media_urls:
            lines.append("Images:")
            for media_url in media_urls:
                lines.append(f"- {media_url}")
            all_media_urls.extend(media_urls)

        lines.append("")  # Spacer between tweets

    content = "\n".join(lines).strip()
    if not content:
        raise ValueError("Twitter thread did not contain any textual content")

    metadata = {
        "url": url,
        "thread_author": author,
        "tweet_count": len(tweets_sorted),
        "tweet_ids": [str(getattr(tweet, "id", "")) for tweet in tweets_sorted],
        "images": all_media_urls,
        "page_title": f"Twitter thread by {author}",
    }

    return {
        "content": content,
        "title": f"Twitter thread by {author}",
        "metadata": metadata,
    }



