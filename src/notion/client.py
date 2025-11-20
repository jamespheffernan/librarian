"""Notion API client for creating pages and formatting content."""

import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Optional

import yaml
from dotenv import load_dotenv
from notion_client import Client

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Notion block content limit (2000 characters per block)
NOTION_BLOCK_CONTENT_LIMIT = 2000


def _load_config() -> dict:
    """Load configuration from config.yaml."""
    config_path = Path(__file__).parent.parent.parent / "config" / "config.yaml"
    default_config = {
        "notion": {
            "databases": {
                "default": "",
            }
        },
        "processing": {
            "add_source_metadata": True,
        },
    }
    
    if not config_path.exists():
        logger.warning("Config file not found, using defaults")
        return default_config
    
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f) or {}
            # Merge with defaults
            merged = default_config.copy()
            if config:
                for key, value in config.items():
                    if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                        merged[key].update(value)
                    else:
                        merged[key] = value
            return merged
    except Exception as e:
        logger.warning(f"Error loading config, using defaults: {e}")
        return default_config


def initialize_client(api_key: Optional[str] = None) -> Client:
    """
    Initialize Notion API client.
    
    Args:
        api_key: Notion API key (if not provided, uses NOTION_API_KEY env var)
        
    Returns:
        Initialized Notion Client
        
    Raises:
        ValueError: If API key is not found
    """
    if api_key is None:
        api_key = os.getenv("NOTION_API_KEY")
        if not api_key:
            raise ValueError(
                "NOTION_API_KEY not found in environment variables. "
                "Set it in .env file or pass as parameter."
            )
    
    return Client(auth=api_key)


def _is_heading(line: str) -> bool:
    """Check if a line is a heading (starts with # or ends with :)."""
    stripped = line.strip()
    return stripped.startswith("#") or (stripped.endswith(":") and len(stripped) > 1)


def _is_bullet_list(line: str) -> bool:
    """Check if a line is a bullet list item."""
    stripped = line.strip()
    return stripped.startswith("- ") or stripped.startswith("* ") or stripped.startswith("• ")


def _get_heading_level(line: str) -> int:
    """Get heading level from markdown-style heading."""
    stripped = line.strip()
    if stripped.startswith("#"):
        level = 0
        for char in stripped:
            if char == "#":
                level += 1
            else:
                break
        return min(level, 3)  # Notion supports levels 1-3
    return 1  # Default to level 1 for lines ending with :


def _split_long_content(content: str, max_length: int = NOTION_BLOCK_CONTENT_LIMIT) -> List[str]:
    """
    Split long content into chunks that fit within Notion's block limit.
    
    Args:
        content: Content to split
        max_length: Maximum length per chunk
        
    Returns:
        List of content chunks
    """
    if len(content) <= max_length:
        return [content]
    
    chunks = []
    current_chunk = ""
    
    # Try to split at paragraph boundaries
    paragraphs = content.split("\n\n")
    
    for para in paragraphs:
        # If adding this paragraph would exceed limit, save current chunk and start new one
        if current_chunk and len(current_chunk) + len(para) + 2 > max_length:
            chunks.append(current_chunk.strip())
            current_chunk = para
        else:
            if current_chunk:
                current_chunk += "\n\n" + para
            else:
                current_chunk = para
    
    # Add remaining chunk
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks


def format_blocks(content: str) -> List[Dict]:
    """
    Convert text content to Notion block format.
    
    Args:
        content: Text content to format
        
    Returns:
        List of Notion block dictionaries
    """
    if not content:
        return []
    
    blocks = []
    lines = content.split("\n")
    current_paragraph = []
    in_list = False
    
    for line in lines:
        stripped = line.strip()
        
        # Handle headings
        if _is_heading(line):
            # Save any pending paragraph
            if current_paragraph:
                para_text = "\n".join(current_paragraph).strip()
                if para_text:
                    # Split if too long
                    for chunk in _split_long_content(para_text):
                        blocks.append({
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [{"type": "text", "text": {"content": chunk}}]
                            },
                        })
                current_paragraph = []
            
            # Create heading block
            heading_text = stripped.lstrip("#").strip()
            if heading_text.endswith(":"):
                heading_text = heading_text[:-1].strip()
            
            level = _get_heading_level(line)
            heading_type = f"heading_{level}"
            
            # Split if too long
            for chunk in _split_long_content(heading_text):
                blocks.append({
                    "object": "block",
                    "type": heading_type,
                    heading_type: {
                        "rich_text": [{"type": "text", "text": {"content": chunk}}]
                    },
                })
            
            in_list = False
            continue
        
        # Handle bullet lists
        if _is_bullet_list(line):
            # Save any pending paragraph
            if current_paragraph:
                para_text = "\n".join(current_paragraph).strip()
                if para_text:
                    for chunk in _split_long_content(para_text):
                        blocks.append({
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [{"type": "text", "text": {"content": chunk}}]
                            },
                        })
                current_paragraph = []
            
            # Extract list item text
            list_text = stripped[2:].strip()  # Remove "- " or "* " or "• "
            
            # Split if too long
            for chunk in _split_long_content(list_text):
                blocks.append({
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"type": "text", "text": {"content": chunk}}]
                    },
                })
            
            in_list = True
            continue
        
        # Regular paragraph line
        if stripped:
            current_paragraph.append(line)
        else:
            # Empty line - end current paragraph if we have one
            if current_paragraph:
                para_text = "\n".join(current_paragraph).strip()
                if para_text:
                    for chunk in _split_long_content(para_text):
                        blocks.append({
                            "object": "block",
                            "type": "paragraph",
                            "paragraph": {
                                "rich_text": [{"type": "text", "text": {"content": chunk}}]
                            },
                        })
                current_paragraph = []
            in_list = False
    
    # Handle remaining paragraph
    if current_paragraph:
        para_text = "\n".join(current_paragraph).strip()
        if para_text:
            for chunk in _split_long_content(para_text):
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": chunk}}]
                    },
                })
    
    return blocks


def get_database_id(database_name: Optional[str] = None, api_key: Optional[str] = None) -> str:
    """
    Get database ID by name from config or environment.
    
    Args:
        database_name: Name of database from config (e.g., "default", "research")
        api_key: Notion API key (optional)
        
    Returns:
        Database ID
        
    Raises:
        ValueError: If database ID is not found
    """
    config = _load_config()
    
    # Try to get from config by name
    if database_name:
        databases = config.get("notion", {}).get("databases", {})
        if database_name in databases and databases[database_name]:
            return databases[database_name]
    
    # Try default database from config
    default_db = config.get("notion", {}).get("databases", {}).get("default", "")
    if default_db:
        return default_db
    
    # Try environment variable
    env_db = os.getenv("NOTION_DEFAULT_DATABASE_ID")
    if env_db:
        return env_db
    
    raise ValueError(
        f"Database ID not found. "
        f"Set it in config/config.yaml or NOTION_DEFAULT_DATABASE_ID environment variable."
    )


def create_page(
    database_id: str,
    title: str,
    content: str,
    metadata: Optional[Dict] = None,
    api_key: Optional[str] = None,
    max_retries: int = 3,
) -> str:
    """
    Create a page in a Notion database.
    
    Args:
        database_id: Notion database ID
        title: Page title
        content: Page content (will be formatted into blocks)
        metadata: Optional metadata dict (currently unused, reserved for future properties)
        api_key: Notion API key (optional)
        max_retries: Maximum number of retry attempts
        
    Returns:
        Created page ID
        
    Raises:
        ValueError: If required parameters are missing
        RuntimeError: If page creation fails after retries
    """
    if not database_id:
        raise ValueError("Database ID is required")
    
    if not title:
        raise ValueError("Title is required")
    
    client = initialize_client(api_key)
    
    # Format content into blocks
    blocks = format_blocks(content) if content else []
    
    # Prepare page properties
    properties = {
        "title": {
            "title": [{"type": "text", "text": {"content": title}}]
        }
    }
    
    # Add metadata as properties if provided (future enhancement)
    # For now, metadata is included in content footer
    
    # Retry logic with exponential backoff
    last_error = None
    for attempt in range(max_retries):
        try:
            logger.info(f"Creating Notion page: {title} (attempt {attempt + 1}/{max_retries})")
            
            # Create page
            response = client.pages.create(
                parent={"database_id": database_id},
                properties=properties,
                children=blocks,
            )
            
            page_id = response.get("id", "")
            logger.info(f"Successfully created Notion page: {page_id}")
            return page_id
            
        except Exception as e:
            last_error = e
            logger.warning(f"Page creation attempt {attempt + 1} failed: {e}")
            
            if attempt < max_retries - 1:
                # Exponential backoff
                wait_time = 2 ** attempt
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error(f"Page creation failed after {max_retries} attempts")
    
    raise RuntimeError(
        f"Failed to create Notion page after {max_retries} attempts: {last_error}"
    )

