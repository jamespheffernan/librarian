# Notion Note Creator

A Python CLI tool that extracts content from images, PDFs, URLs, and text; generates intelligent titles using AI; and creates well-formatted notes in Notion.

## Features

- **Multiple Input Types**: Support for images (PNG, JPG, JPEG, WebP), PDFs, URLs, and plain text
- **Intelligent Content Extraction**: OCR for images, text extraction for PDFs, web scraping for URLs
- **AI-Powered Titles**: Automatically generates concise, descriptive titles using Claude Haiku 4.5
- **Notion Integration**: Creates properly formatted pages with block structure (paragraphs, headings, lists)
- **Error Handling**: Robust retry logic and rate limiting for API calls

## Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. Configure Notion (see [Notion Setup](#notion-setup) below)

## Notion Setup

### Step 1: Create a Notion Integration

1. Go to [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Click **"+ New integration"**
3. Give it a name (e.g., "Note Creator")
4. Select your workspace
5. Under **Capabilities**, enable:
   - **Read content**
   - **Insert content**
   - **Update content**
6. Click **"Submit"** to create the integration
7. Copy the **Internal Integration Token** (starts with `secret_`) - this is your `NOTION_API_KEY`

### Step 2: Create a Database

1. In Notion, create a new page or open an existing page
2. Type `/database` and select **"Table - Inline"** or **"Table - Full page"**
3. Name your database (e.g., "Research Notes", "Articles")
4. Add any properties you want (Title, Tags, Date, etc.)

### Step 3: Share Database with Integration

1. Open your database page
2. Click the **"..."** menu in the top right
3. Click **"Add connections"**
4. Search for and select your integration (e.g., "Note Creator")
5. Click **"Confirm"**

### Step 4: Get Database ID

1. Open your database in Notion
2. Look at the URL - it will look like:
   ```
   https://www.notion.so/workspace/DATABASE_ID?v=...
   ```
3. The Database ID is the long string of characters between the last `/` and the `?`
4. Copy this ID and add it to your `config/config.yaml` or `.env` file

Example:
- URL: `https://www.notion.so/abc123def456?v=...`
- Database ID: `abc123def456`

**Note:** You may need to remove any hyphens from the ID. The actual ID format is a 32-character hex string, often displayed with hyphens in the URL.

### Step 5: Configure in Project

Add your database ID to `config/config.yaml`:

```yaml
notion:
  databases:
    default: "your-database-id-here"
    research: "another-database-id"  # Optional: named databases
```

Or set `NOTION_DEFAULT_DATABASE_ID` in your `.env` file.

## Usage

### Add a Note from a File

```bash
python -m src.main add-note --file path/to/file.pdf
python -m src.main add-note --file screenshot.png
```

### Add a Note from a URL

```bash
python -m src.main add-note --url https://example.com/article
```

### Add a Note from Text

```bash
python -m src.main add-note --text "Meeting notes from today's discussion"
```

### Options

- `--file PATH`: Path to file (image, PDF, or text file)
- `--url URL`: Web page URL to extract content from
- `--text TEXT`: Direct text input
- `--title TITLE`: Override AI-generated title with custom title
- `--database NAME`: Specify database by name (from config.yaml)
- `--tags TAGS`: Comma-separated tags to add (future feature)

### Examples

```bash
# Add a research paper PDF to research database
python -m src.main add-note --file ~/Downloads/paper.pdf --database research

# Save an article with custom title
python -m src.main add-note --url https://example.com/article --title "My Custom Title"

# Quick text note
python -m src.main add-note --text "Remember to check the quarterly report"
```

## Configuration

Edit `config/config.yaml` to customize:

- Notion database IDs
- Claude model settings
- Content processing options (title length, preview length, etc.)

## Development

### Running Tests

```bash
pytest
```

### Project Structure

```
notion-note-creator/
├── src/
│   ├── main.py              # CLI entry point
│   ├── extractors/          # Content extraction modules
│   ├── processors/          # AI processing (title generation, cleaning)
│   └── notion/              # Notion API integration
├── config/
│   └── config.yaml          # Configuration file
├── tests/                   # Test suite
└── docs/                    # Documentation
```

## Requirements

- Python 3.10+
- Anthropic Claude API key
- Notion API key and database access

## License

MIT

