"""Main CLI entry point for Notion Note Creator."""

import logging
import sys
from pathlib import Path
from typing import Optional

import click

from src.extractors import (
    extract_from_image,
    extract_from_pdf,
    extract_from_text,
    extract_from_url,
)
from src.notion import create_page, get_database_id
from src.processors import clean_content, generate_title

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


@click.group()
def cli():
    """Notion Note Creator - Create notes in Notion from various sources."""
    pass


def _determine_file_type(file_path: Path) -> str:
    """Determine the type of file based on extension."""
    ext = file_path.suffix.lower()
    
    image_extensions = {".png", ".jpg", ".jpeg", ".webp"}
    pdf_extensions = {".pdf"}
    
    if ext in image_extensions:
        return "image"
    elif ext in pdf_extensions:
        return "pdf"
    else:
        return "text"


def _extract_content_from_file(file_path: str) -> tuple[str, str, dict]:
    """
    Extract content from a file.
    
    Returns:
        Tuple of (content, source_type, metadata)
    """
    path = Path(file_path)
    source_type = _determine_file_type(path)
    metadata = {"filename": path.name}
    
    click.echo(f"Extracting content from {source_type} file: {path.name}")
    
    try:
        if source_type == "image":
            content = extract_from_image(str(path))
        elif source_type == "pdf":
            content = extract_from_pdf(str(path))
        else:
            # Text file
            with open(path, "r", encoding="utf-8") as f:
                raw_content = f.read()
            content = extract_from_text(raw_content)
        
        return content, source_type, metadata
        
    except Exception as e:
        logger.error(f"Error extracting content from file: {e}")
        click.echo(f"Error: Failed to extract content from file: {e}", err=True)
        sys.exit(1)


def _extract_content_from_url(url: str) -> tuple[str, str, dict]:
    """
    Extract content from a URL.
    
    Returns:
        Tuple of (content, source_type, metadata)
    """
    click.echo(f"Fetching content from URL: {url}")
    
    try:
        result = extract_from_url(url)
        content = result["content"]
        metadata = {
            "url": result["url"],
            "title": result.get("title", ""),
        }
        
        # Use page title if available and good
        if result.get("title") and len(result["title"]) < 100:
            metadata["page_title"] = result["title"]
        
        return content, "url", metadata
        
    except Exception as e:
        logger.error(f"Error extracting content from URL: {e}")
        click.echo(f"Error: Failed to extract content from URL: {e}", err=True)
        sys.exit(1)


def _extract_content_from_text(text: str) -> tuple[str, str, dict]:
    """
    Extract content from direct text input.
    
    Returns:
        Tuple of (content, source_type, metadata)
    """
    try:
        content = extract_from_text(text)
        return content, "text", {}
    except Exception as e:
        logger.error(f"Error processing text: {e}")
        click.echo(f"Error: Failed to process text: {e}", err=True)
        sys.exit(1)


@cli.command("add-note")
@click.option("--file", type=click.Path(exists=True), help="Path to file (image, PDF, or text)")
@click.option("--url", type=str, help="Web page URL to extract content from")
@click.option("--text", type=str, help="Direct text input")
@click.option("--title", type=str, help="Override AI-generated title with custom title")
@click.option("--database", type=str, help="Specify database by name (from config.yaml)")
@click.option("--tags", type=str, help="Comma-separated tags to add (future feature)")
def add_note(file, url, text, title, database, tags):
    """Add a note to Notion from file, URL, or text."""
    # Validate that exactly one input type is provided
    input_count = sum([bool(file), bool(url), bool(text)])
    
    if input_count == 0:
        click.echo("Error: Must provide one of --file, --url, or --text", err=True)
        sys.exit(1)
    
    if input_count > 1:
        click.echo("Error: Can only provide one of --file, --url, or --text", err=True)
        sys.exit(1)
    
    logger.info("Note creation requested")
    
    try:
        # Extract content based on input type
        if file:
            content, source_type, metadata = _extract_content_from_file(file)
        elif url:
            content, source_type, metadata = _extract_content_from_url(url)
        else:  # text
            content, source_type, metadata = _extract_content_from_text(text)
        
        if not content or not content.strip():
            click.echo("Error: No content could be extracted", err=True)
            sys.exit(1)
        
        click.echo(f"Extracted {len(content)} characters from {source_type} source")
        
        # Generate title if not provided
        if not title:
            click.echo("Generating title using AI...")
            try:
                title = generate_title(content, source_type=source_type)
                click.echo(f"Generated title: {title}")
            except Exception as e:
                logger.error(f"Error generating title: {e}")
                click.echo(f"Warning: Failed to generate title: {e}", err=True)
                # Use fallback title
                if "page_title" in metadata:
                    title = metadata["page_title"]
                elif "filename" in metadata:
                    title = Path(metadata["filename"]).stem
                else:
                    title = f"Note from {source_type}"
                click.echo(f"Using fallback title: {title}")
        else:
            click.echo(f"Using provided title: {title}")
        
        # Clean content
        click.echo("Cleaning and formatting content...")
        cleaned_content = clean_content(
            content,
            source_type=source_type,
            source_metadata=metadata,
        )
        
        # Get database ID
        try:
            database_id = get_database_id(database_name=database)
            click.echo(f"Using database: {database_id[:8]}...")
        except Exception as e:
            logger.error(f"Error getting database ID: {e}")
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)
        
        # Create page in Notion
        click.echo("Creating page in Notion...")
        try:
            page_id = create_page(
                database_id=database_id,
                title=title,
                content=cleaned_content,
                metadata=metadata,
            )
            click.echo(f"✓ Successfully created Notion page: {page_id}")
            click.echo(f"  Title: {title}")
            click.echo(f"  Database: {database_id[:8]}...")
        except Exception as e:
            logger.error(f"Error creating Notion page: {e}")
            click.echo(f"Error: Failed to create Notion page: {e}", err=True)
            sys.exit(1)
        
    except KeyboardInterrupt:
        click.echo("\nOperation cancelled by user", err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()

