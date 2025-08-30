"""
Video Insight AI - AI-powered video analysis and blog generation tools
"""

__version__ = "1.0.0"
__author__ = "Video Analysis Team"

from .core import VideoAnalyzer, BlogGenerator
from .utils import setup_logging

__all__ = ["VideoAnalyzer", "BlogGenerator", "setup_logging"]
