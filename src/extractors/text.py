"""Text content extractor for plain text input."""

import re


def extract_from_text(text: str) -> str:
    """
    Extract and clean text content from plain text input.
    
    Args:
        text: Raw text input
        
    Returns:
        Cleaned text with normalized whitespace and line breaks
        
    Raises:
        ValueError: If text is empty or None
    """
    if text is None:
        raise ValueError("Text input cannot be None")
    
    if not isinstance(text, str):
        raise ValueError(f"Text input must be a string, got {type(text)}")
    
    if not text.strip():
        raise ValueError("Text input cannot be empty")
    
    # Normalize line breaks (Windows, Mac, Unix)
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
    
    # Remove excessive whitespace (more than 2 consecutive spaces)
    cleaned = re.sub(r" {3,}", "  ", cleaned)
    
    # Remove excessive blank lines (more than 2 consecutive newlines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    
    # Strip leading/trailing whitespace
    cleaned = cleaned.strip()
    
    return cleaned

