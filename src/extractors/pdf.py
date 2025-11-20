"""PDF content extractor."""

import logging
from pathlib import Path
from typing import Optional

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

logger = logging.getLogger(__name__)


def extract_from_pdf(pdf_path: str) -> str:
    """
    Extract text content from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text content from all pages
        
    Raises:
        FileNotFoundError: If PDF file doesn't exist
        ValueError: If PDF extraction fails or file is not a PDF
        ImportError: If PyPDF2 is not installed
    """
    if PyPDF2 is None:
        raise ImportError(
            "PyPDF2 is required for PDF extraction. Install it with: pip install pypdf2"
        )
    
    pdf_file = Path(pdf_path)
    
    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    if not pdf_file.suffix.lower() == ".pdf":
        raise ValueError(f"File is not a PDF: {pdf_path}")
    
    try:
        text_content = []
        
        with open(pdf_file, "rb") as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            if len(pdf_reader.pages) == 0:
                raise ValueError(f"PDF file has no pages: {pdf_path}")
            
            logger.info(f"Extracting text from {len(pdf_reader.pages)} page(s)")
            
            for page_num, page in enumerate(pdf_reader.pages, start=1):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():
                        text_content.append(page_text)
                    else:
                        logger.warning(f"Page {page_num} appears to be empty or image-based")
                except Exception as e:
                    logger.warning(f"Error extracting text from page {page_num}: {e}")
                    continue
        
        if not text_content:
            raise ValueError(
                f"Could not extract any text from PDF: {pdf_path}. "
                "This may be an image-based PDF. Consider using image extraction instead."
            )
        
        extracted_text = "\n\n".join(text_content)
        
        # Check if we got meaningful text (not just whitespace or minimal content)
        if len(extracted_text.strip()) < 10:
            raise ValueError(
                f"Extracted text from PDF is too short: {pdf_path}. "
                "This may be an image-based PDF. Consider using image extraction instead."
            )
        
        return extracted_text.strip()
        
    except PyPDF2.errors.PdfReadError as e:
        raise ValueError(f"Invalid or corrupted PDF file: {pdf_path}. Error: {e}")
    except Exception as e:
        raise ValueError(f"Error extracting text from PDF {pdf_path}: {e}")

