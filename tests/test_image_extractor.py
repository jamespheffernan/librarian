"""Tests for image extractor."""

import base64
import io
import os
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open

from PIL import Image

from src.extractors.image import extract_from_image, _encode_image_to_base64


def test_encode_image_to_base64_success(tmp_path):
    """Test successful image encoding."""
    # Create a test image
    img = Image.new("RGB", (100, 100), color="red")
    img_path = tmp_path / "test.jpg"
    img.save(img_path)
    
    encoded = _encode_image_to_base64(img_path)
    assert isinstance(encoded, str)
    assert len(encoded) > 0
    
    # Verify it's valid base64
    decoded = base64.b64decode(encoded)
    assert len(decoded) > 0


def test_encode_image_to_base64_png_with_transparency(tmp_path):
    """Test encoding PNG with transparency."""
    # Create a test PNG with transparency
    img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
    img_path = tmp_path / "test.png"
    img.save(img_path)
    
    encoded = _encode_image_to_base64(img_path)
    assert isinstance(encoded, str)
    assert len(encoded) > 0


def test_extract_from_image_file_not_found():
    """Test that non-existent file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        extract_from_image("nonexistent.jpg")


def test_extract_from_image_unsupported_format(tmp_path):
    """Test that unsupported format raises ValueError."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("not an image")
    
    with pytest.raises(ValueError, match="Unsupported image format"):
        extract_from_image(str(test_file))


def test_extract_from_image_no_api_key(tmp_path):
    """Test that missing API key raises ValueError."""
    img = Image.new("RGB", (100, 100), color="red")
    img_path = tmp_path / "test.jpg"
    img.save(img_path)
    
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY not found"):
            extract_from_image(str(img_path))


@patch("src.extractors.image.Anthropic")
def test_extract_from_image_success(mock_anthropic, tmp_path):
    """Test successful image extraction."""
    # Create a test image
    img = Image.new("RGB", (100, 100), color="red")
    img_path = tmp_path / "test.jpg"
    img.save(img_path)
    
    # Mock Anthropic client
    mock_client = MagicMock()
    mock_message = MagicMock()
    mock_content = MagicMock()
    mock_content.type = "text"
    mock_content.text = "Extracted text from image"
    mock_message.content = [mock_content]
    mock_client.messages.create.return_value = mock_message
    mock_anthropic.return_value = mock_client
    
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        result = extract_from_image(str(img_path))
        assert result == "Extracted text from image"
        mock_client.messages.create.assert_called_once()


@patch("src.extractors.image.Anthropic")
def test_extract_from_image_no_text_extracted(mock_anthropic, tmp_path):
    """Test that image with no text raises ValueError."""
    img = Image.new("RGB", (100, 100), color="red")
    img_path = tmp_path / "test.jpg"
    img.save(img_path)
    
    # Mock Anthropic client with empty response
    mock_client = MagicMock()
    mock_message = MagicMock()
    mock_message.content = []  # No content
    mock_client.messages.create.return_value = mock_message
    mock_anthropic.return_value = mock_client
    
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
        with pytest.raises(ValueError, match="No text could be extracted"):
            extract_from_image(str(img_path))


@patch("src.extractors.image.Anthropic")
def test_extract_from_image_api_key_parameter(mock_anthropic, tmp_path):
    """Test that API key can be passed as parameter."""
    img = Image.new("RGB", (100, 100), color="red")
    img_path = tmp_path / "test.jpg"
    img.save(img_path)
    
    mock_client = MagicMock()
    mock_message = MagicMock()
    mock_content = MagicMock()
    mock_content.type = "text"
    mock_content.text = "Extracted text"
    mock_message.content = [mock_content]
    mock_client.messages.create.return_value = mock_message
    mock_anthropic.return_value = mock_client
    
    with patch.dict(os.environ, {}, clear=True):
        result = extract_from_image(str(img_path), api_key="custom-key")
        assert result == "Extracted text"
        mock_anthropic.assert_called_once_with(api_key="custom-key")


def test_extract_from_image_anthropic_not_installed(tmp_path):
    """Test that missing anthropic library raises ImportError."""
    img = Image.new("RGB", (100, 100), color="red")
    img_path = tmp_path / "test.jpg"
    img.save(img_path)
    
    with patch("src.extractors.image.Anthropic", None):
        with pytest.raises(ImportError, match="anthropic library is required"):
            extract_from_image(str(img_path))

