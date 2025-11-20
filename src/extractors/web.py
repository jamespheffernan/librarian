"""Web content extractor for URLs."""

import logging
from typing import Dict, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def extract_from_url(url: str, timeout: int = 10) -> Dict[str, str]:
    """
    Extract content from a web page URL.
    
    Args:
        url: Web page URL to extract content from
        timeout: Request timeout in seconds (default: 10)
        
    Returns:
        Dictionary with keys:
            - 'content': Main text content
            - 'title': Page title
            - 'url': Original URL
            - 'raw_html': Raw HTML content (optional)
            
    Raises:
        ValueError: If URL is invalid or content extraction fails
        requests.RequestException: If network request fails
    """
    if not url or not isinstance(url, str):
        raise ValueError("URL must be a non-empty string")
    
    # Validate URL format
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f"Invalid URL format: {url}")
    
    # Ensure URL has a scheme
    if not parsed.scheme.startswith("http"):
        url = f"https://{url}"
        parsed = urlparse(url)
    
    try:
        logger.info(f"Fetching content from URL: {url}")
        
        # Set headers to mimic a browser
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                         "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Extract title
        title_tag = soup.find("title")
        title = title_tag.get_text().strip() if title_tag else ""
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
            script.decompose()
        
        # Try to find main content area
        main_content = None
        
        # Common content selectors
        content_selectors = [
            "main",
            "article",
            "[role='main']",
            ".content",
            ".post",
            ".entry-content",
            "#content",
            "#main-content",
        ]
        
        for selector in content_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        # If no main content found, use body
        if not main_content:
            main_content = soup.find("body")
        
        if not main_content:
            # Fallback to entire document
            main_content = soup
        
        # Extract text
        text_content = main_content.get_text(separator="\n", strip=True)
        
        # Clean up text
        lines = [line.strip() for line in text_content.split("\n")]
        lines = [line for line in lines if line]  # Remove empty lines
        cleaned_content = "\n".join(lines)
        
        # Limit content length (prevent extremely long pages)
        max_content_length = 100000
        if len(cleaned_content) > max_content_length:
            logger.warning(f"Content truncated from {len(cleaned_content)} to {max_content_length} characters")
            cleaned_content = cleaned_content[:max_content_length] + "\n\n[Content truncated...]"
        
        if not cleaned_content.strip():
            raise ValueError(f"No extractable content found from URL: {url}")
        
        return {
            "content": cleaned_content,
            "title": title,
            "url": url,
            "raw_html": response.text[:5000] if len(response.text) < 5000 else None,  # Store first 5KB for debugging
        }
        
    except requests.exceptions.Timeout:
        raise ValueError(f"Request timeout while fetching URL: {url}")
    except requests.exceptions.ConnectionError:
        raise ValueError(f"Connection error while fetching URL: {url}")
    except requests.exceptions.HTTPError as e:
        raise ValueError(f"HTTP error {e.response.status_code} while fetching URL: {url}")
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Error fetching URL {url}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error extracting content from {url}: {e}")
        raise ValueError(f"Error extracting content from URL {url}: {e}")

