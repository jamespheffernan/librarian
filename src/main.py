"""Main CLI entry point for Notion Note Creator."""

import logging
import sys
from pathlib import Path

import click

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
    click.echo("Note creation functionality will be implemented in subsequent phases.")


if __name__ == "__main__":
    cli()

