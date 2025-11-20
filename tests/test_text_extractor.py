"""Tests for text extractor."""

import pytest

from src.extractors.text import extract_from_text


def test_extract_from_text_basic():
    """Test basic text extraction."""
    text = "This is a simple text."
    result = extract_from_text(text)
    assert result == "This is a simple text."


def test_extract_from_text_normalizes_line_breaks():
    """Test that line breaks are normalized."""
    text = "Line 1\r\nLine 2\rLine 3\nLine 4"
    result = extract_from_text(text)
    assert "\r" not in result
    assert "\r\n" not in result
    assert result == "Line 1\nLine 2\nLine 3\nLine 4"


def test_extract_from_text_removes_excessive_whitespace():
    """Test that excessive whitespace is removed."""
    text = "Word1    Word2     Word3"
    result = extract_from_text(text)
    assert "   " not in result
    assert "    " not in result


def test_extract_from_text_removes_excessive_blank_lines():
    """Test that excessive blank lines are removed."""
    text = "Line 1\n\n\n\nLine 2"
    result = extract_from_text(text)
    assert "\n\n\n" not in result
    assert result.count("\n\n") <= 1


def test_extract_from_text_strips_whitespace():
    """Test that leading/trailing whitespace is stripped."""
    text = "   \n  Text content  \n   "
    result = extract_from_text(text)
    assert result == "Text content"


def test_extract_from_text_empty_string():
    """Test that empty string raises ValueError."""
    with pytest.raises(ValueError, match="cannot be empty"):
        extract_from_text("")


def test_extract_from_text_whitespace_only():
    """Test that whitespace-only string raises ValueError."""
    with pytest.raises(ValueError, match="cannot be empty"):
        extract_from_text("   \n\n   ")


def test_extract_from_text_none():
    """Test that None raises ValueError."""
    with pytest.raises(ValueError, match="cannot be None"):
        extract_from_text(None)


def test_extract_from_text_non_string():
    """Test that non-string input raises ValueError."""
    with pytest.raises(ValueError, match="must be a string"):
        extract_from_text(123)


def test_extract_from_text_preserves_double_spaces():
    """Test that double spaces are preserved (for intentional formatting)."""
    text = "Word1  Word2"
    result = extract_from_text(text)
    assert "  " in result


def test_extract_from_text_preserves_double_newlines():
    """Test that double newlines are preserved (for paragraph breaks)."""
    text = "Paragraph 1\n\nParagraph 2"
    result = extract_from_text(text)
    assert "\n\n" in result

