# Intelligent Notion Note Creator - Project Specification

## Project Overview

Build a system that accepts any input type (images, PDFs, URLs, text), extracts content, generates intelligent titles using AI, and creates well-formatted notes in Notion via API.

## Core Requirements

### Input Types Supported
- **Images**: PNG, JPG, JPEG, WebP (OCR extraction)
- **PDFs**: Extract text content
- **URLs**: Fetch and parse web page content
- **Plain text**: Direct input
- **Files**: Accept file paths

### Output
- Create pages in specified Notion database
- Intelligent title generation based on content
- Clean, formatted content in Notion blocks
- Preserve source metadata (URL, file name, date)

## Technical Architecture

### Tech Stack
- **Language**: Python 3.10+
- **AI**: Anthropic Claude API (vision + text analysis)
- **Notion Integration**: Official Notion API SDK
- **PDF Processing**: pypdf2 or pdfplumber
- **Image Processing**: PIL/Pillow for image handling
- **Web Fetching**: requests + beautifulsoup4
- **CLI Framework**: click or argparse

### Project Structure
```
notion-note-creator/
├── src/
│   ├── __init__.py
│   ├── main.py              # Entry point and CLI
│   ├── extractors/
│   │   ├── __init__.py
│   │   ├── image.py         # Image OCR via Claude vision
│   │   ├── pdf.py           # PDF text extraction
│   │   ├── web.py           # URL content fetching
│   │   └── text.py          # Plain text handling
│   ├── processors/
│   │   ├── __init__.py
│   │   ├── title_gen.py     # Claude-powered title generation
│   │   └── content_clean.py # Content cleaning and formatting
│   └── notion/
│       ├── __init__.py
│       └── client.py        # Notion API wrapper
├── config/
│   └── config.yaml          # Configuration file
├── .env.example             # Environment variables template
├── requirements.txt
└── README.md
```

## Implementation Plan

### Phase 1: Core Infrastructure (Day 1)

**Files to create:**
1. `requirements.txt` with dependencies
2. `.env.example` with required API keys
3. `config/config.yaml` for Notion database ID and settings
4. `src/main.py` with basic CLI structure

**Dependencies needed:**
```
anthropic>=0.18.0
notion-client>=2.2.1
pypdf2>=3.0.0
pillow>=10.0.0
requests>=2.31.0
beautifulsoup4>=4.12.0
python-dotenv>=1.0.0
pyyaml>=6.0.1
click>=8.1.7
```

### Phase 2: Extractors (Day 1-2)

**src/extractors/image.py**
- Function: `extract_from_image(image_path: str) -> str`
- Use Claude's vision API to extract text from images
- Convert image to base64
- Send to Claude with prompt: "Extract all text content from this image. Return only the extracted text without any commentary."

**src/extractors/pdf.py**
- Function: `extract_from_pdf(pdf_path: str) -> str`
- Use pypdf2 to extract text from all pages
- Handle multi-page PDFs
- Fallback to Claude vision for image-based PDFs

**src/extractors/web.py**
- Function: `extract_from_url(url: str) -> dict`
- Fetch URL content with requests
- Parse with BeautifulSoup
- Extract main content, title, metadata
- Return both raw HTML and cleaned text

**src/extractors/text.py**
- Function: `extract_from_text(text: str) -> str`
- Simple passthrough with basic cleaning
- Remove excessive whitespace
- Normalize line breaks

### Phase 3: AI Processing (Day 2)

**src/processors/title_gen.py**
- Function: `generate_title(content: str, source_type: str) -> str`
- Send content to Claude with prompt:
  ```
  Analyze this content and generate a concise, descriptive title (max 60 chars).
  The title should capture the main topic or purpose.
  Return ONLY the title, nothing else.
  
  Content:
  {content[:2000]}  # First 2000 chars for context
  ```

**src/processors/content_clean.py**
- Function: `clean_content(content: str, source_type: str) -> str`
- Remove excessive whitespace
- Format for Notion blocks
- Add source attribution footer

### Phase 4: Notion Integration (Day 2-3)

**src/notion/client.py**

Key functions:
- `initialize_client() -> Client`: Set up Notion client with API key
- `create_page(database_id: str, title: str, content: str, metadata: dict) -> str`: Create Notion page
- `format_blocks(content: str) -> list`: Convert text to Notion block format

Block formatting logic:
- Split content into paragraphs
- Detect headings (lines ending with : or starting with #)
- Detect bullet lists (lines starting with -, *, •)
- Create appropriate Notion block types

### Phase 5: CLI Interface (Day 3)

**src/main.py**

Commands:
```bash
# Single file
python -m src.main add-note --file path/to/file.pdf

# URL
python -m src.main add-note --url https://example.com

# Text input
python -m src.main add-note --text "Direct text content"

# With custom title (override AI)
python -m src.main add-note --file file.pdf --title "Custom Title"

# Specify database
python -m src.main add-note --file file.pdf --database "Research Notes"
```

CLI arguments:
- `--file PATH`: Path to file (image, PDF, or text)
- `--url URL`: Web page URL
- `--text TEXT`: Direct text input
- `--title TITLE`: Override AI-generated title
- `--database NAME`: Notion database name (from config)
- `--tags TAGS`: Comma-separated tags to add

## Configuration

**config/config.yaml structure:**
```yaml
notion:
  databases:
    default: "database_id_here"
    research: "research_db_id"
    articles: "articles_db_id"
    
anthropic:
  model: "claude-sonnet-4-20250514"
  max_tokens: 1000

processing:
  title_max_length: 60
  content_preview_length: 2000
  add_source_metadata: true
```

**.env structure:**
```
ANTHROPIC_API_KEY=sk-ant-...
NOTION_API_KEY=secret_...
NOTION_DEFAULT_DATABASE_ID=...
```

## Key Implementation Details

### Image Processing Flow
1. Load image with PIL
2. Convert to base64
3. Send to Claude vision API with extraction prompt
4. Receive extracted text
5. Generate title from extracted text
6. Create Notion page

### PDF Processing Flow
1. Try pypdf2 extraction first
2. If text extraction fails (image-based PDF), convert pages to images
3. Use Claude vision on images
4. Combine extracted text
5. Generate title
6. Create Notion page

### URL Processing Flow
1. Fetch URL with requests
2. Parse with BeautifulSoup
3. Extract article content (main text, title)
4. Clean HTML/markdown
5. Generate title (or use page title if good)
6. Create Notion page with URL in metadata

### Error Handling
- Validate input types before processing
- Handle API rate limits (implement exponential backoff)
- Catch and log extraction failures
- Provide meaningful error messages
- Implement retry logic for API calls

### Content Length Handling
- If content > 100,000 chars, truncate for title generation (use first 2000 chars)
- Split very long content into multiple Notion blocks (max 2000 chars per block)
- Add "..." indicator for truncated previews

## Testing Checklist

- [ ] Test PDF extraction with text-based PDF
- [ ] Test PDF extraction with scanned/image-based PDF
- [ ] Test image OCR with screenshot
- [ ] Test image OCR with photo of document
- [ ] Test URL fetching with article
- [ ] Test URL fetching with Wikipedia page
- [ ] Test plain text input
- [ ] Test title generation quality (10+ examples)
- [ ] Test Notion page creation
- [ ] Test with very long content (>10k words)
- [ ] Test error handling for invalid inputs
- [ ] Test rate limiting behavior

## Development Steps for Cursor

1. **Initialize project**
   - Create directory structure
   - Create `requirements.txt`
   - Create `.env.example`
   - Create `config/config.yaml`

2. **Build extractors** (in order)
   - Start with `src/extractors/text.py` (simplest)
   - Build `src/extractors/pdf.py`
   - Build `src/extractors/web.py`
   - Build `src/extractors/image.py` (most complex)

3. **Build processors**
   - `src/processors/content_clean.py`
   - `src/processors/title_gen.py`

4. **Build Notion client**
   - `src/notion/client.py`
   - Test with manual page creation first

5. **Build CLI**
   - `src/main.py` with basic structure
   - Add argument parsing
   - Wire up all components
   - Add error handling

6. **Test and refine**
   - Test each input type
   - Refine prompts for better titles
   - Optimize Notion block formatting

## Usage Examples

**After implementation:**

```bash
# Setup
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys

# Add a research paper PDF
python -m src.main add-note --file ~/Downloads/paper.pdf --database research

# Save an article
python -m src.main add-note --url https://example.com/article

# Save a screenshot with notes
python -m src.main add-note --file screenshot.png

# Quick text note
python -m src.main add-note --text "Meeting notes from today's discussion about Q1 goals"
```

## Future Enhancements (V2)

- Batch processing (multiple files at once)
- Watch folder for automatic processing
- Email integration (forward emails to create notes)
- Smart tagging based on content analysis
- Duplicate detection
- MCP server implementation for Claude Desktop integration
- Support for audio transcription
- Support for video subtitle extraction

## Success Criteria

- Successfully extracts text from all supported input types
- Generates meaningful, concise titles 90%+ of the time
- Creates properly formatted Notion pages
- Handles errors gracefully
- Processes typical inputs in < 10 seconds
- Easy to use from command line

## Notes for Cursor

- Use type hints throughout
- Add docstrings to all functions
- Implement logging with Python's logging module
- Use environment variables for all secrets
- Make configuration flexible (allow overrides)
- Keep functions small and focused
- Error messages should be actionable
- Test with real-world examples as you build
