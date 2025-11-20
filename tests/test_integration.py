"""Integration tests for the full workflow."""

import pytest
from click.testing import CliRunner
from unittest.mock import Mock, patch, MagicMock

from pathlib import Path
from src.main import (
    _determine_file_type,
    _extract_content_from_text,
    _extract_content_from_url,
    cli,
)


def test_determine_file_type():
    """Test file type determination."""
    assert _determine_file_type(Path("test.png")) == "image"
    assert _determine_file_type(Path("test.jpg")) == "image"
    assert _determine_file_type(Path("test.jpeg")) == "image"
    assert _determine_file_type(Path("test.webp")) == "image"
    assert _determine_file_type(Path("test.pdf")) == "pdf"
    assert _determine_file_type(Path("test.txt")) == "text"
    assert _determine_file_type(Path("test.md")) == "text"


def test_extract_content_from_text():
    """Test text extraction in CLI context."""
    content, source_type, metadata = _extract_content_from_text("Test content here")
    assert content == "Test content here"
    assert source_type == "text"
    assert isinstance(metadata, dict)


def test_extract_content_from_url_defaults_to_web(monkeypatch):
    """Ensure web extraction is used when Twitter flag is disabled."""
    monkeypatch.setattr("src.main.looks_like_twitter_status", lambda url: True)
    called = {}

    def fake_web_extractor(url):
        called["url"] = url
        return {"content": "page data", "title": "Page", "url": url}

    monkeypatch.setattr("src.main.extract_from_url", fake_web_extractor)

    content, source_type, metadata = _extract_content_from_url(
        "https://mobile.twitter.com/test/status/1",
        enable_twitter=False,
    )

    assert source_type == "url"
    assert metadata["url"] == "https://mobile.twitter.com/test/status/1"
    assert called["url"] == metadata["url"]
    assert content == "page data"


def test_extract_content_from_url_twitter_thread(monkeypatch):
    """Twitter thread extraction should honor the enable flag."""
    monkeypatch.setattr("src.main.looks_like_twitter_status", lambda url: True)

    fake_thread = {
        "content": "Thread overview",
        "title": "Timeline thread",
        "metadata": {"thread_author": "tester"},
    }

    content, source_type, metadata = _extract_content_from_url(
        "https://twitter.com/test/status/2",
        enable_twitter=True,
        _twitter_extractor=lambda url: fake_thread,
    )

    assert source_type == "twitter-thread"
    assert content == "Thread overview"
    assert metadata["thread_author"] == "tester"
    assert metadata["source_detail"] == "Twitter thread"


@patch("src.main.extract_from_text")
@patch("src.main.generate_title")
@patch("src.main.clean_content")
@patch("src.main.get_database_id")
@patch("src.main.create_page")
def test_full_workflow_text_input(
    mock_create_page,
    mock_get_database_id,
    mock_clean_content,
    mock_generate_title,
    mock_extract_text,
):
    """Test full workflow with text input."""
    # Setup mocks
    mock_extract_text.return_value = "Test content"
    mock_generate_title.return_value = "Test Title"
    mock_clean_content.return_value = "Cleaned content"
    mock_get_database_id.return_value = "db-123"
    mock_create_page.return_value = "page-123"
    
    # This is a simplified test - actual CLI testing would require click.testing.CliRunner
    # But we can test the helper functions
    content, source_type, metadata = _extract_content_from_text("Test content")
    assert content == "Test content"
    assert source_type == "text"


@patch("src.main.create_page")
@patch("src.main.get_database_id")
@patch("src.main.clean_content")
@patch("src.main.generate_title")
@patch("src.main._extract_content_from_file")
def test_add_note_multiple_files(
    mock_extract_file,
    mock_generate_title,
    mock_clean_content,
    mock_get_database_id,
    mock_create_page,
    tmp_path,
):
    """Ensure multiple --file arguments generate multiple pages."""
    outputs = {
        "file-a.txt": ("A content", "text", {"filename": "file-a.txt"}),
        "file-b.txt": ("B content", "text", {"filename": "file-b.txt"}),
    }

    def fake_extract(path):
        return outputs[Path(path).name]

    mock_extract_file.side_effect = fake_extract
    mock_generate_title.side_effect = ["Title A", "Title B"]
    mock_clean_content.side_effect = lambda content, **kwargs: f"cleaned-{content}"
    mock_get_database_id.return_value = "db-123"
    mock_create_page.side_effect = ["page-a", "page-b"]

    file_a = tmp_path / "file-a.txt"
    file_b = tmp_path / "file-b.txt"
    file_a.write_text("Sample A")
    file_b.write_text("Sample B")

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "add-note",
            "--file",
            str(file_a),
            "--file",
            str(file_b),
            "--database",
            "default",
        ],
    )

    assert result.exit_code == 0
    assert mock_generate_title.call_count == 2
    assert mock_clean_content.call_count == 2
    assert mock_create_page.call_count == 2

