"""Input validation utilities"""

import os
import logging
from pathlib import Path
from urllib.parse import urlparse


def validate_api_key() -> bool:
    """Validate OpenAI API key is present"""
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        logging.error("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
        return False
    
    if not api_key.startswith('sk-'):
        logging.error("Invalid OpenAI API key format. Must start with 'sk-'")
        return False
        
    logging.info("✓ OpenAI API key validated")
    return True


def validate_video_input(input_source: str) -> bool:
    """Validate video input (URL or local file)"""
    if is_url(input_source):
        logging.info(f"✓ URL input validated: {input_source}")
        return True
    
    # Check if local file exists
    file_path = Path(input_source)
    if file_path.exists() and file_path.is_file():
        # Check file extension
        valid_extensions = {'.mp4', '.mkv', '.webm', '.avi', '.mov', '.wmv', '.flv', '.m4v'}
        if file_path.suffix.lower() in valid_extensions:
            logging.info(f"✓ Local video file validated: {file_path}")
            return True
        else:
            logging.error(f"Unsupported video format: {file_path.suffix}")
            return False
    else:
        logging.error(f"Local file not found: {file_path}")
        return False


def is_url(s: str) -> bool:
    """Check if string is a valid URL"""
    try:
        result = urlparse(s)
        return all([result.scheme, result.netloc])
    except Exception:
        return False
