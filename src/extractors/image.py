"""Image content extractor using Claude vision API."""

import base64
import logging
import os
from pathlib import Path
from typing import Optional

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

from dotenv import load_dotenv
from PIL import Image

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


def _encode_image_to_base64(image_path: Path) -> str:
    """
    Encode an image file to base64 string.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Base64-encoded string of the image
        
    Raises:
        ValueError: If image cannot be opened or encoded
    """
    try:
        # Open and validate image
        with Image.open(image_path) as img:
            # Convert to RGB if necessary (for formats like PNG with transparency)
            if img.mode in ("RGBA", "LA", "P"):
                # Create a white background
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                background.paste(img, mask=img.split()[-1] if img.mode in ("RGBA", "LA") else None)
                img = background
            elif img.mode != "RGB":
                img = img.convert("RGB")
            
            # Save to bytes
            import io
            img_bytes = io.BytesIO()
            img.save(img_bytes, format="JPEG", quality=95)
            img_bytes.seek(0)
            
            # Encode to base64
            encoded = base64.b64encode(img_bytes.read()).decode("utf-8")
            return encoded
            
    except Exception as e:
        raise ValueError(f"Error encoding image {image_path}: {e}")


def extract_from_image(image_path: str, api_key: Optional[str] = None) -> str:
    """
    Extract text content from an image using Claude vision API.
    
    Args:
        image_path: Path to the image file
        api_key: Anthropic API key (if not provided, uses ANTHROPIC_API_KEY env var)
        
    Returns:
        Extracted text content from the image
        
    Raises:
        FileNotFoundError: If image file doesn't exist
        ValueError: If image format is not supported or extraction fails
        ImportError: If required libraries are not installed
    """
    if Anthropic is None:
        raise ImportError(
            "anthropic library is required for image extraction. "
            "Install it with: pip install anthropic"
        )
    image_file = Path(image_path)
    
    if not image_file.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    # Validate image format
    valid_extensions = {".png", ".jpg", ".jpeg", ".webp"}
    if image_file.suffix.lower() not in valid_extensions:
        raise ValueError(
            f"Unsupported image format: {image_file.suffix}. "
            f"Supported formats: {', '.join(valid_extensions)}"
        )
    
    # Get API key
    if api_key is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found in environment variables. "
                "Set it in .env file or pass as parameter."
            )
    
    try:
        # Encode image to base64
        logger.info(f"Encoding image: {image_path}")
        base64_image = _encode_image_to_base64(image_file)
        
        # Initialize Anthropic client
        client = Anthropic(api_key=api_key)
        
        # Get model from config (default to Haiku)
        from pathlib import Path as PathLib
        import yaml
        
        config_path = PathLib(__file__).parent.parent.parent / "config" / "config.yaml"
        model = "claude-3-5-haiku-20241022"  # Default
        
        if config_path.exists():
            try:
                with open(config_path) as f:
                    config = yaml.safe_load(f)
                    if config and "anthropic" in config and "model" in config["anthropic"]:
                        model = config["anthropic"]["model"]
            except Exception as e:
                logger.warning(f"Could not load config, using default model: {e}")
        
        # Call Claude vision API
        logger.info(f"Extracting text from image using {model}")
        
        message = client.messages.create(
            model=model,
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": base64_image,
                            },
                        },
                        {
                            "type": "text",
                            "text": "Extract all text content from this image. Return only the extracted text without any commentary or explanation. Preserve the structure and formatting as much as possible.",
                        },
                    ],
                }
            ],
        )
        
        # Extract text from response
        extracted_text = ""
        for content_block in message.content:
            if content_block.type == "text":
                extracted_text += content_block.text
        
        if not extracted_text.strip():
            raise ValueError(f"No text could be extracted from image: {image_path}")
        
        return extracted_text.strip()
        
    except Exception as e:
        if isinstance(e, (ValueError, FileNotFoundError)):
            raise
        logger.error(f"Error extracting text from image {image_path}: {e}")
        raise ValueError(f"Error extracting text from image {image_path}: {e}")

