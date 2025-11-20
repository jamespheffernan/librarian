"""Tests for the Twitter thread extractor."""

from datetime import datetime
from types import SimpleNamespace

import pytest

from src.extractors.twitter import (
    extract_twitter_thread,
    looks_like_twitter_thread,
)


class _FakeTweet:
    def __init__(
        self,
        tweet_id: int,
        username: str,
        text: str,
        date: datetime,
        conversation_id: int | None = None,
        media_urls: list[str] | None = None,
    ) -> None:
        self.id = tweet_id
        self.user = SimpleNamespace(username=username)
        self.renderedContent = text
        self.date = date
        self.conversationId = conversation_id or tweet_id
        self.media = [
            SimpleNamespace(fullUrl=url) for url in (media_urls or [])
        ]


def test_looks_like_twitter_thread():
    assert looks_like_twitter_thread("https://twitter.com/john/status/1234567890")
    assert looks_like_twitter_thread("https://x.com/alice/statuses/987654321")
    assert not looks_like_twitter_thread("https://example.com/article")


def test_extract_twitter_thread_invalid_url():
    with pytest.raises(ValueError, match="Twitter status"):
        extract_twitter_thread("https://example.com/not-a-tweet")


def test_extract_twitter_thread_success(monkeypatch):
    root_tweet = _FakeTweet(
        tweet_id=1,
        username="threader",
        text="First tweet in thread.",
        date=datetime(2025, 1, 1, 12, 0),
        media_urls=["https://pbs.twimg.com/media/1.jpg"],
    )

    reply_tweet = _FakeTweet(
        tweet_id=2,
        username="threader",
        text="Second tweet with image.",
        date=datetime(2025, 1, 1, 12, 5),
        conversation_id=1,
        media_urls=["https://pbs.twimg.com/media/2.jpg"],
    )

    mock_tweet_scraper = SimpleNamespace()
    mock_tweet_scraper.get_items = lambda: iter([root_tweet])

    mock_search_scraper = SimpleNamespace()
    mock_search_scraper.get_items = lambda: iter([reply_tweet])

    fake_snscrape = SimpleNamespace(
        TwitterTweetScraper=lambda *_: mock_tweet_scraper,
        TwitterSearchScraper=lambda *_: mock_search_scraper,
    )

    monkeypatch.setattr("src.extractors.twitter.sntwitter", fake_snscrape)

    result = extract_twitter_thread("https://twitter.com/threader/status/1")

    assert "Tweet 1/2" in result["content"]
    assert "Tweet 2/2" in result["content"]
    assert "- https://pbs.twimg.com/media/2.jpg" in result["content"]
    assert result["metadata"]["tweet_count"] == 2
    assert result["metadata"]["thread_author"] == "threader"
    assert result["metadata"]["images"] == [
        "https://pbs.twimg.com/media/1.jpg",
        "https://pbs.twimg.com/media/2.jpg",
    ]

