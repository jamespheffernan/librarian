"""Tests for content cleaner."""

from src.processors.content_clean import clean_content


def test_clean_content_basic():
    """Test basic content cleaning."""
    content = "  Line 1  \n  Line 2  \n  Line 3  "
    result = clean_content(content)
    assert result == "Line 1\nLine 2\nLine 3"


def test_clean_content_removes_excessive_blank_lines():
    """Test that excessive blank lines are removed."""
    content = "Line 1\n\n\n\nLine 2"
    result = clean_content(content)
    # Should have at most one blank line between lines
    assert "\n\n\n" not in result


def test_clean_content_empty():
    """Test that empty content returns empty string."""
    result = clean_content("")
    assert result == ""


def test_clean_content_with_source_metadata():
    """Test content cleaning with source metadata."""
    content = "Some content"
    metadata = {
        "url": "https://example.com",
        "filename": "test.pdf",
    }
    result = clean_content(content, source_type="pdf", source_metadata=metadata)
    
    assert "Some content" in result
    assert "Source: pdf" in result
    assert "https://example.com" in result
    assert "test.pdf" in result
    assert "Date:" in result


def test_clean_content_without_source_metadata():
    """Test content cleaning without adding source metadata."""
    content = "Some content"
    metadata = {"url": "https://example.com"}
    result = clean_content(
        content, source_type="url", source_metadata=metadata, add_source_metadata=False
    )
    
    assert result == "Some content"
    assert "Source:" not in result
    assert "https://example.com" not in result


def test_clean_content_preserves_structure():
    """Test that content structure is preserved."""
    content = "Paragraph 1\n\nParagraph 2\n\nParagraph 3"
    result = clean_content(content)
    assert "Paragraph 1" in result
    assert "Paragraph 2" in result
    assert "Paragraph 3" in result


def test_clean_content_strips_trailing_whitespace():
    """Test that trailing whitespace is removed."""
    content = "Line 1\nLine 2\n   \n  "
    result = clean_content(content)
    assert not result.endswith(" ")
    assert not result.endswith("\n")


def test_clean_content_with_partial_metadata():
    """Test content cleaning with partial metadata."""
    content = "Some content"
    metadata = {"url": "https://example.com"}  # No filename
    result = clean_content(content, source_type="url", source_metadata=metadata)
    
    assert "Source: url" in result
    assert "https://example.com" in result
    assert "File:" not in result  # Should not include file if not provided

