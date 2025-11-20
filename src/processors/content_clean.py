"""Content cleaning and formatting."""

import logging
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def clean_content(
    content: str,
    source_type: str = "unknown",
    source_metadata: Optional[Dict[str, str]] = None,
    add_source_metadata: bool = True,
) -> str:
    """
    Clean and format content for Notion.
    
    Args:
        content: Raw content to clean
        source_type: Type of source (e.g., "pdf", "url", "image", "text")
        source_metadata: Optional metadata dict with keys like "url", "filename", etc.
        add_source_metadata: Whether to add source attribution footer
        
    Returns:
        Cleaned and formatted content
    """
    if not content:
        return ""
    
    # Remove excessive whitespace
    lines = content.split("\n")
    cleaned_lines = []
    
    for line in lines:
        # Strip each line
        line = line.strip()
        
        # Skip completely empty lines if previous line was also empty
        if not line and cleaned_lines and not cleaned_lines[-1]:
            continue
        
        cleaned_lines.append(line)
    
    # Join lines back
    cleaned = "\n".join(cleaned_lines)
    
    # Remove trailing whitespace
    cleaned = cleaned.rstrip()
    
    # Add source metadata footer if requested
    if add_source_metadata and source_metadata:
        footer_parts = []
        
        # Add source type
        if source_type:
            footer_parts.append(f"Source: {source_type}")
        
        # Add URL if available
        if "url" in source_metadata and source_metadata["url"]:
            footer_parts.append(f"URL: {source_metadata['url']}")
        
        # Add filename if available
        if "filename" in source_metadata and source_metadata["filename"]:
            footer_parts.append(f"File: {source_metadata['filename']}")
        
        # Add date
        footer_parts.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if footer_parts:
            footer = "\n\n---\n" + " | ".join(footer_parts)
            cleaned += footer
    
    return cleaned

