"""Tests for web extractor."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.extractors.web import extract_from_url


def test_extract_from_url_invalid_url():
    """Test that invalid URL raises ValueError."""
    with pytest.raises(ValueError, match="Invalid URL format"):
        extract_from_url("not-a-url")


def test_extract_from_url_empty_string():
    """Test that empty URL raises ValueError."""
    with pytest.raises(ValueError, match="non-empty string"):
        extract_from_url("")


def test_extract_from_url_none():
    """Test that None URL raises ValueError."""
    with pytest.raises(ValueError, match="non-empty string"):
        extract_from_url(None)


@patch("src.extractors.web.requests.get")
def test_extract_from_url_success(mock_get):
    """Test successful URL extraction."""
    # Mock response
    mock_response = Mock()
    mock_response.content = b"<html><head><title>Test Page</title></head><body><p>Test content</p></body></html>"
    mock_response.text = "<html><head><title>Test Page</title></head><body><p>Test content</p></body></html>"
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response
    
    result = extract_from_url("https://example.com")
    
    assert "content" in result
    assert "title" in result
    assert "url" in result
    assert result["title"] == "Test Page"
    assert "Test content" in result["content"]
    assert result["url"] == "https://example.com"


@patch("src.extractors.web.requests.get")
def test_extract_from_url_adds_https_scheme(mock_get):
    """Test that URL without scheme gets https:// added."""
    mock_response = Mock()
    mock_response.content = b"<html><body><p>Content</p></body></html>"
    mock_response.text = "<html><body><p>Content</p></body></html>"
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response
    
    result = extract_from_url("example.com")
    
    # Should have added https://
    assert result["url"].startswith("https://")
    mock_get.assert_called_once()
    call_args = mock_get.call_args
    assert call_args[0][0].startswith("https://")


@patch("src.extractors.web.requests.get")
def test_extract_from_url_timeout(mock_get):
    """Test that timeout raises ValueError."""
    import requests
    mock_get.side_effect = requests.exceptions.Timeout("Timeout")
    
    with pytest.raises(ValueError, match="timeout"):
        extract_from_url("https://example.com")


@patch("src.extractors.web.requests.get")
def test_extract_from_url_connection_error(mock_get):
    """Test that connection error raises ValueError."""
    import requests
    mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
    
    with pytest.raises(ValueError, match="Connection error"):
        extract_from_url("https://example.com")


@patch("src.extractors.web.requests.get")
def test_extract_from_url_http_error(mock_get):
    """Test that HTTP error raises ValueError."""
    import requests
    mock_response = Mock()
    mock_response.status_code = 404
    mock_get.side_effect = requests.exceptions.HTTPError(response=mock_response)
    
    with pytest.raises(ValueError, match="HTTP error"):
        extract_from_url("https://example.com")


@patch("src.extractors.web.requests.get")
def test_extract_from_url_no_content(mock_get):
    """Test that page with no extractable content raises ValueError."""
    mock_response = Mock()
    mock_response.content = b"<html><head><title>Empty</title></head><body></body></html>"
    mock_response.text = "<html><head><title>Empty</title></head><body></body></html>"
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response
    
    with pytest.raises(ValueError, match="No extractable content"):
        extract_from_url("https://example.com")


@patch("src.extractors.web.requests.get")
def test_extract_from_url_removes_scripts(mock_get):
    """Test that scripts and styles are removed."""
    html = """
    <html>
    <head><title>Test</title></head>
    <body>
        <script>alert('test');</script>
        <style>.test { color: red; }</style>
        <p>Real content</p>
    </body>
    </html>
    """
    mock_response = Mock()
    mock_response.content = html.encode()
    mock_response.text = html
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response
    
    result = extract_from_url("https://example.com")
    
    assert "alert" not in result["content"]
    assert "color: red" not in result["content"]
    assert "Real content" in result["content"]

