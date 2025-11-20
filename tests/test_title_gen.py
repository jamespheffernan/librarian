"""Tests for title generator."""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock

from src.processors.title_gen import generate_title


def test_generate_title_empty_content():
    """Test that empty content raises ValueError."""
    with pytest.raises(ValueError, match="cannot be empty"):
        generate_title("")


def test_generate_title_no_api_key():
    """Test that missing API key raises ValueError."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY not found"):
            generate_title("Some content")


@patch("src.processors.title_gen.Anthropic")
def test_generate_title_success(mock_anthropic):
    """Test successful title generation."""
    # Mock Anthropic client
    mock_client = MagicMock()
    mock_message = MagicMock()
    mock_content = MagicMock()
    mock_content.type = "text"
    mock_content.text = "Generated Title"
    mock_message.content = [mock_content]
    mock_client.messages.create.return_value = mock_message
    mock_anthropic.return_value = mock_client
    
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        result = generate_title("Some content here", source_type="text")
        assert result == "Generated Title"
        mock_client.messages.create.assert_called_once()


@patch("src.processors.title_gen.Anthropic")
def test_generate_title_removes_quotes(mock_anthropic):
    """Test that quotes are removed from generated title."""
    mock_client = MagicMock()
    mock_message = MagicMock()
    mock_content = MagicMock()
    mock_content.type = "text"
    mock_content.text = '"Title in Quotes"'
    mock_message.content = [mock_content]
    mock_client.messages.create.return_value = mock_message
    mock_anthropic.return_value = mock_client
    
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        result = generate_title("Some content", source_type="text")
        assert result == "Title in Quotes"
        assert not result.startswith('"')


@patch("src.processors.title_gen.Anthropic")
def test_generate_title_truncates_long_title(mock_anthropic):
    """Test that long titles are truncated."""
    mock_client = MagicMock()
    mock_message = MagicMock()
    mock_content = MagicMock()
    mock_content.type = "text"
    # Create a title longer than 60 chars
    mock_content.text = "A" * 100
    mock_message.content = [mock_content]
    mock_client.messages.create.return_value = mock_message
    mock_anthropic.return_value = mock_client
    
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        result = generate_title("Some content", source_type="text")
        assert len(result) <= 60
        assert result.endswith("...")


@patch("src.processors.title_gen.Anthropic")
def test_generate_title_truncates_content_preview(mock_anthropic):
    """Test that content is truncated for title generation."""
    mock_client = MagicMock()
    mock_message = MagicMock()
    mock_content = MagicMock()
    mock_content.type = "text"
    mock_content.text = "Title"
    mock_message.content = [mock_content]
    mock_client.messages.create.return_value = mock_message
    mock_anthropic.return_value = mock_client
    
    # Create very long content
    long_content = "A" * 5000
    
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        generate_title(long_content, source_type="text")
        
        # Check that the prompt sent to API contains truncated content
        call_args = mock_client.messages.create.call_args
        prompt = call_args[1]["messages"][0]["content"]
        assert len(prompt) < len(long_content)


@patch("src.processors.title_gen.Anthropic")
@patch("src.processors.title_gen.time.sleep")
def test_generate_title_retries_on_failure(mock_sleep, mock_anthropic):
    """Test that title generation retries on failure."""
    mock_client = MagicMock()
    
    # First call fails, second succeeds
    mock_client.messages.create.side_effect = [
        Exception("API Error"),
        MagicMock(content=[MagicMock(type="text", text="Retry Title")]),
    ]
    mock_anthropic.return_value = mock_client
    
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        result = generate_title("Some content", source_type="text", max_retries=3)
        assert result == "Retry Title"
        assert mock_client.messages.create.call_count == 2
        mock_sleep.assert_called_once()  # Should have slept once before retry


@patch("src.processors.title_gen.Anthropic")
@patch("src.processors.title_gen.time.sleep")
def test_generate_title_fails_after_max_retries(mock_sleep, mock_anthropic):
    """Test that title generation raises error after max retries."""
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = Exception("API Error")
    mock_anthropic.return_value = mock_client
    
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        with pytest.raises(RuntimeError, match="Failed to generate title"):
            generate_title("Some content", source_type="text", max_retries=2)
        
        assert mock_client.messages.create.call_count == 2

