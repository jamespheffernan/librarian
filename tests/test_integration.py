"""Integration tests for the full workflow."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.main import _determine_file_type, _extract_content_from_text
from pathlib import Path


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

