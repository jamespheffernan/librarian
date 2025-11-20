"""Tests for Notion client."""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock

from src.notion.client import (
    initialize_client,
    format_blocks,
    get_database_id,
    create_page,
    _is_heading,
    _is_bullet_list,
    _get_heading_level,
    _split_long_content,
)


def test_initialize_client_no_api_key():
    """Test that missing API key raises ValueError."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="NOTION_API_KEY not found"):
            initialize_client()


def test_initialize_client_with_api_key():
    """Test client initialization with API key."""
    with patch("src.notion.client.Client") as mock_client:
        initialize_client(api_key="test-key")
        mock_client.assert_called_once_with(auth="test-key")


def test_is_heading_markdown():
    """Test heading detection with markdown syntax."""
    assert _is_heading("# Heading")
    assert _is_heading("## Heading")
    assert _is_heading("### Heading")
    assert not _is_heading("Regular text")


def test_is_heading_colon():
    """Test heading detection with colon."""
    assert _is_heading("Heading:")
    assert not _is_heading("Heading")


def test_is_bullet_list():
    """Test bullet list detection."""
    assert _is_bullet_list("- Item")
    assert _is_bullet_list("* Item")
    assert _is_bullet_list("• Item")
    assert not _is_bullet_list("Regular text")


def test_get_heading_level():
    """Test heading level extraction."""
    assert _get_heading_level("# Heading") == 1
    assert _get_heading_level("## Heading") == 2
    assert _get_heading_level("### Heading") == 3
    assert _get_heading_level("#### Heading") == 3  # Capped at 3
    assert _get_heading_level("Heading:") == 1


def test_split_long_content_short():
    """Test splitting short content."""
    content = "Short content"
    result = _split_long_content(content, max_length=100)
    assert len(result) == 1
    assert result[0] == content


def test_split_long_content_long():
    """Test splitting long content."""
    content = "A" * 5000
    result = _split_long_content(content, max_length=1000)
    assert len(result) > 1
    assert all(len(chunk) <= 1000 for chunk in result)


def test_split_long_content_paragraph_breaking():
    """Ensure paragraphs longer than the limit are force-split."""
    sentence = "word " * 250
    content = sentence.strip()
    result = _split_long_content(content, max_length=200)
    assert len(result) > 1
    assert all(len(chunk) <= 200 for chunk in result)
    # ensure split respects word boundaries when possible
    assert all(chunk.endswith("word") or content.endswith(chunk) for chunk in result)


def test_format_blocks_paragraph():
    """Test formatting simple paragraph."""
    content = "This is a paragraph."
    blocks = format_blocks(content)
    
    assert len(blocks) == 1
    assert blocks[0]["type"] == "paragraph"
    assert blocks[0]["paragraph"]["rich_text"][0]["text"]["content"] == "This is a paragraph."


def test_format_blocks_heading():
    """Test formatting heading."""
    content = "# Heading 1"
    blocks = format_blocks(content)
    
    assert len(blocks) == 1
    assert blocks[0]["type"] == "heading_1"
    assert blocks[0]["heading_1"]["rich_text"][0]["text"]["content"] == "Heading 1"


def test_format_blocks_bullet_list():
    """Test formatting bullet list."""
    content = "- Item 1\n- Item 2"
    blocks = format_blocks(content)
    
    assert len(blocks) == 2
    assert blocks[0]["type"] == "bulleted_list_item"
    assert blocks[1]["type"] == "bulleted_list_item"


def test_format_blocks_mixed():
    """Test formatting mixed content."""
    content = "# Title\n\nParagraph text.\n\n- List item"
    blocks = format_blocks(content)
    
    assert len(blocks) >= 3
    assert blocks[0]["type"] == "heading_1"
    assert any(b["type"] == "paragraph" for b in blocks)
    assert any(b["type"] == "bulleted_list_item" for b in blocks)


def test_format_blocks_empty():
    """Test formatting empty content."""
    blocks = format_blocks("")
    assert blocks == []


def test_get_database_id_from_config(tmp_path):
    """Test getting database ID from config."""
    import yaml
    
    config = {
        "notion": {
            "databases": {
                "default": "default-db-id",
                "research": "research-db-id",
            }
        }
    }
    
    with patch("src.notion.client._load_config", return_value=config):
        assert get_database_id() == "default-db-id"
        assert get_database_id("research") == "research-db-id"


def test_get_database_id_from_env():
    """Test getting database ID from environment."""
    with patch("src.notion.client._load_config", return_value={"notion": {"databases": {}}}):
        with patch.dict(os.environ, {"NOTION_DEFAULT_DATABASE_ID": "env-db-id"}):
            assert get_database_id() == "env-db-id"


def test_get_database_id_not_found():
    """Test that missing database ID raises ValueError."""
    with patch("src.notion.client._load_config", return_value={"notion": {"databases": {}}}):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Database ID not found"):
                get_database_id()


@patch("src.notion.client.initialize_client")
def test_create_page_success(mock_init_client):
    """Test successful page creation."""
    mock_client = MagicMock()
    mock_response = {"id": "page-123"}
    mock_client.pages.create.return_value = mock_response
    mock_init_client.return_value = mock_client
    
    with patch.dict(os.environ, {"NOTION_API_KEY": "test-key"}):
        page_id = create_page(
            database_id="db-123",
            title="Test Page",
            content="Test content",
        )
        
        assert page_id == "page-123"
        mock_client.pages.create.assert_called_once()


@patch("src.notion.client.initialize_client")
def test_create_page_no_database_id(mock_init_client):
    """Test that missing database ID raises ValueError."""
    with pytest.raises(ValueError, match="Database ID is required"):
        create_page(database_id="", title="Test", content="Content")


@patch("src.notion.client.initialize_client")
def test_create_page_no_title(mock_init_client):
    """Test that missing title raises ValueError."""
    with pytest.raises(ValueError, match="Title is required"):
        create_page(database_id="db-123", title="", content="Content")


@patch("src.notion.client.initialize_client")
@patch("src.notion.client.time.sleep")
def test_create_page_retries_on_failure(mock_sleep, mock_init_client):
    """Test that page creation retries on failure."""
    mock_client = MagicMock()
    mock_client.pages.create.side_effect = [
        Exception("API Error"),
        {"id": "page-123"},
    ]
    mock_init_client.return_value = mock_client
    
    with patch.dict(os.environ, {"NOTION_API_KEY": "test-key"}):
        page_id = create_page(
            database_id="db-123",
            title="Test Page",
            content="Test content",
            max_retries=3,
        )
        
        assert page_id == "page-123"
        assert mock_client.pages.create.call_count == 2
        mock_sleep.assert_called_once()

