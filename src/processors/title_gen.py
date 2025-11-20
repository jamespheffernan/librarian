"""Title generation using Claude AI."""

import logging
import os
import time
from pathlib import Path
from typing import Optional

import yaml
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


def _load_config() -> dict:
    """Load configuration from config.yaml."""
    config_path = Path(__file__).parent.parent.parent / "config" / "config.yaml"
    default_config = {
        "anthropic": {
            "model": "claude-3-5-haiku-20241022",
            "max_tokens": 1000,
        },
        "processing": {
            "title_max_length": 60,
            "content_preview_length": 2000,
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
            merged.update(config)
            return merged
    except Exception as e:
        logger.warning(f"Error loading config, using defaults: {e}")
        return default_config


def generate_title(
    content: str,
    source_type: str = "unknown",
    api_key: Optional[str] = None,
    max_retries: int = 3,
) -> str:
    """
    Generate an intelligent title from content using Claude AI.
    
    Args:
        content: Content to generate title from
        source_type: Type of source (e.g., "pdf", "url", "image", "text")
        api_key: Anthropic API key (if not provided, uses ANTHROPIC_API_KEY env var)
        max_retries: Maximum number of retry attempts for API calls
        
    Returns:
        Generated title (max 60 characters by default)
        
    Raises:
        ValueError: If content is empty or API key is missing
        RuntimeError: If title generation fails after retries
    """
    if not content or not content.strip():
        raise ValueError("Content cannot be empty for title generation")
    
    # Get API key
    if api_key is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found in environment variables. "
                "Set it in .env file or pass as parameter."
            )
    
    # Load config
    config = _load_config()
    model = config["anthropic"]["model"]
    max_tokens = config["anthropic"]["max_tokens"]
    title_max_length = config["processing"]["title_max_length"]
    preview_length = config["processing"]["content_preview_length"]
    
    # Truncate content for title generation (use first N characters)
    content_preview = content[:preview_length]
    if len(content) > preview_length:
        content_preview += "..."
    
    # Initialize Anthropic client
    client = Anthropic(api_key=api_key)
    
    # Retry logic with exponential backoff
    last_error = None
    for attempt in range(max_retries):
        try:
            logger.info(f"Generating title (attempt {attempt + 1}/{max_retries})")
            
            prompt = f"""Analyze this content and generate a concise, descriptive title (max {title_max_length} characters).
The title should capture the main topic or purpose of the content.
Return ONLY the title, nothing else. No quotes, no explanation, just the title.

Source type: {source_type}
Content:
{content_preview}"""

            message = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )
            
            # Extract title from response
            title = ""
            for content_block in message.content:
                if content_block.type == "text":
                    title += content_block.text
            
            # Clean up title
            title = title.strip()
            
            # Remove quotes if present
            if title.startswith('"') and title.endswith('"'):
                title = title[1:-1]
            elif title.startswith("'") and title.endswith("'"):
                title = title[1:-1]
            
            # Truncate to max length
            if len(title) > title_max_length:
                title = title[:title_max_length - 3] + "..."
            
            if not title:
                raise ValueError("Generated title is empty")
            
            logger.info(f"Generated title: {title}")
            return title
            
        except Exception as e:
            last_error = e
            logger.warning(f"Title generation attempt {attempt + 1} failed: {e}")
            
            if attempt < max_retries - 1:
                # Exponential backoff: wait 2^attempt seconds
                wait_time = 2 ** attempt
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error(f"Title generation failed after {max_retries} attempts")
    
    # If all retries failed, raise error
    raise RuntimeError(
        f"Failed to generate title after {max_retries} attempts: {last_error}"
    )

