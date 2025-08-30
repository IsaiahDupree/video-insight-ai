#!/usr/bin/env python3
"""Setup script for Video Insight AI CLI tools"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

setup(
    name="video-insight-ai",
    version="1.0.0",
    author="Video Analysis Team",
    author_email="team@example.com",
    description="AI-powered video analysis and blog post generation tools",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/video-insight-ai",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Video",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "openai>=1.40.0",
        "yt-dlp>=2023.1.1",
        "tqdm>=4.66.4",
        "python-dotenv>=1.0.1",
        "rich>=13.7.1",
        "click>=8.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
        ],
    },
    entry_points={
        "console_scripts": [
            "video-insight=video_insight_ai.cli:main",
            "generate-blog=video_insight_ai.blog_generator:main",
        ],
    },
    include_package_data=True,
    package_data={
        "video_insight_ai": ["prompts/*.txt"],
    },
)
