"""Tests for PDF extractor."""

import io
import pytest
from unittest.mock import Mock, patch, mock_open, MagicMock

from src.extractors.pdf import extract_from_pdf


def test_extract_from_pdf_file_not_found():
    """Test that non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        extract_from_pdf("nonexistent.pdf")


def test_extract_from_pdf_not_pdf_file():
    """Test that non-PDF file raises ValueError."""
    with patch("pathlib.Path.exists", return_value=True):
        with pytest.raises(ValueError, match="not a PDF"):
            extract_from_pdf("file.txt")


def test_extract_from_pdf_pypdf2_not_installed():
    """Test that missing PyPDF2 raises ImportError."""
    with patch("src.extractors.pdf.PyPDF2", None):
        with patch("pathlib.Path.exists", return_value=True):
            with patch("pathlib.Path.suffix", ".pdf"):
                with pytest.raises(ImportError, match="PyPDF2 is required"):
                    extract_from_pdf("test.pdf")


@patch("builtins.open", new_callable=mock_open)
@patch("pathlib.Path.exists", return_value=True)
@patch("pathlib.Path.suffix", ".pdf")
def test_extract_from_pdf_success(mock_exists, mock_file):
    """Test successful PDF extraction."""
    # Mock PyPDF2
    mock_pdf_reader = MagicMock()
    mock_page1 = MagicMock()
    mock_page1.extract_text.return_value = "Page 1 content"
    mock_page2 = MagicMock()
    mock_page2.extract_text.return_value = "Page 2 content"
    mock_pdf_reader.pages = [mock_page1, mock_page2]
    
    with patch("src.extractors.pdf.PyPDF2.PdfReader", return_value=mock_pdf_reader):
        result = extract_from_pdf("test.pdf")
        assert "Page 1 content" in result
        assert "Page 2 content" in result


@patch("builtins.open", new_callable=mock_open)
@patch("pathlib.Path.exists", return_value=True)
@patch("pathlib.Path.suffix", ".pdf")
def test_extract_from_pdf_empty_pages(mock_exists, mock_file):
    """Test PDF with empty pages raises ValueError."""
    mock_pdf_reader = MagicMock()
    mock_pdf_reader.pages = []
    
    with patch("src.extractors.pdf.PyPDF2.PdfReader", return_value=mock_pdf_reader):
        with pytest.raises(ValueError, match="no pages"):
            extract_from_pdf("test.pdf")


@patch("builtins.open", new_callable=mock_open)
@patch("pathlib.Path.exists", return_value=True)
@patch("pathlib.Path.suffix", ".pdf")
def test_extract_from_pdf_no_text_extracted(mock_exists, mock_file):
    """Test PDF with no extractable text raises ValueError."""
    mock_pdf_reader = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = ""  # Empty text
    mock_pdf_reader.pages = [mock_page]
    
    with patch("src.extractors.pdf.PyPDF2.PdfReader", return_value=mock_pdf_reader):
        with pytest.raises(ValueError, match="Could not extract any text"):
            extract_from_pdf("test.pdf")


@patch("builtins.open", new_callable=mock_open)
@patch("pathlib.Path.exists", return_value=True)
@patch("pathlib.Path.suffix", ".pdf")
def test_extract_from_pdf_too_short_text(mock_exists, mock_file):
    """Test PDF with too short extracted text raises ValueError."""
    mock_pdf_reader = MagicMock()
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "abc"  # Too short
    mock_pdf_reader.pages = [mock_page]
    
    with patch("src.extractors.pdf.PyPDF2.PdfReader", return_value=mock_pdf_reader):
        with pytest.raises(ValueError, match="too short"):
            extract_from_pdf("test.pdf")


@patch("builtins.open", new_callable=mock_open)
@patch("pathlib.Path.exists", return_value=True)
@patch("pathlib.Path.suffix", ".pdf")
def test_extract_from_pdf_corrupted_file(mock_exists, mock_file):
    """Test corrupted PDF raises ValueError."""
    import PyPDF2
    
    with patch("src.extractors.pdf.PyPDF2.PdfReader", side_effect=PyPDF2.errors.PdfReadError("Corrupted")):
        with pytest.raises(ValueError, match="Invalid or corrupted"):
            extract_from_pdf("test.pdf")

