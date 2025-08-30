# Video Insight AI 🎬

AI-powered video analysis and blog post generation tools. Transform YouTube videos or local video files into detailed reports and publication-ready blog posts.

## Features

- 🎥 **Video Analysis**: Download from YouTube or analyze local files
- 🖼️ **Frame Analysis**: AI vision analysis of key video frames  
- 🎵 **Audio Transcription**: Accurate speech-to-text with chunking
- 📝 **Blog Generation**: Create Medium, newsletter, and WordPress-ready content
- 📊 **Structured Reports**: JSON and Markdown outputs
- 🔧 **CLI Interface**: Easy-to-use command-line tools

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/video-insight-ai.git
cd video-insight-ai

# Install dependencies
pip install -r requirements.txt

# Or install as package
pip install -e .
```

### Setup

1. Copy `.env.example` to `.env` and add your OpenAI API key:
```bash
cp .env.example .env
```

2. Edit `.env` file:
```env
OPENAI_API_KEY=sk-your-openai-api-key-here
```

3. Ensure `ffmpeg` is installed and in your PATH:
```bash
# Windows (with Chocolatey)
choco install ffmpeg

# macOS (with Homebrew)  
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg
```

### Basic Usage

#### Analyze a Video
```bash
# YouTube video
video-insight analyze "https://www.youtube.com/watch?v=VIDEO_ID"

# Local video file
video-insight analyze "/path/to/video.mp4"

# With custom options
video-insight analyze "https://youtube.com/watch?v=ID" \
  --interval 30 \
  --max-frames 20 \
  --output my_analysis
```

#### Generate Blog Post
```bash
# From analysis results
video-insight generate-blog "runs/20240830-110429" \
  --title "My Video Analysis" \
  --author "Your Name"
```

#### Full Pipeline
```bash
# Analyze + generate blog in one command
video-insight full-pipeline "https://youtube.com/watch?v=ID" \
  --blog-title "Amazing Video Insights" \
  --blog-author "Your Name"
```

## Output Structure

### Video Analysis
```
runs/YYYYMMDD-HHMMSS/
├── report.json          # Structured data
├── report.md            # Human-readable report
├── video/              # Downloaded video
├── audio/              # Extracted audio
└── frames/             # Sampled frames
    ├── frame_000001.jpg
    ├── frame_000002.jpg
    └── ...
```

### Blog Post Generation
```
blog_output/
├── blog_post_medium.md      # Medium.com format
├── newsletter.html          # HTML newsletter
├── blog_post_wordpress.md   # WordPress/Ghost format  
├── images/                  # Frame images
│   ├── frame_000001.jpg
│   └── ...
└── README.md               # Publishing instructions
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key | Required |
| `OPENAI_VISION_MODEL` | Vision model to use | `gpt-4o` |
| `OPENAI_TRANSCRIPTION_MODEL` | Transcription model | `gpt-4o-mini-transcribe` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `MAX_FRAMES_DEFAULT` | Default max frames | `120` |

### Command Options

#### `video-insight analyze`

| Option | Description | Default |
|--------|-------------|---------|
| `--interval` | Frame sampling interval (seconds) | `30` |
| `--max-frames` | Maximum frames to analyze | `120` |  
| `--audio-chunk-seconds` | Audio chunk size for transcription | `300` |
| `--vision-model` | OpenAI vision model | `gpt-4o` |
| `--transcribe-model` | Transcription model | `gpt-4o-mini-transcribe` |
| `--keep-media` | Keep temporary files | `false` |
| `--output` | Output directory | `runs` |

## API Usage

### Python API

```python
from video_insight_ai import VideoAnalyzer, BlogGenerator

# Analyze video
analyzer = VideoAnalyzer()
json_path, md_path = analyzer.analyze_video(
    input_source="https://youtube.com/watch?v=ID",
    frame_interval=30,
    max_frames=20
)

# Generate blog post
generator = BlogGenerator()
blog_outputs = generator.generate_blog_post(
    report_path=md_path,
    frames_dir=json_path.parent / "frames",
    output_dir="my_blog",
    title="Custom Title"
)
```

## Examples

### Quick Analysis
```bash
# Minimal analysis for testing
video-insight analyze "https://youtube.com/watch?v=ID" \
  --max-frames 5 \
  --interval 60
```

### High-Quality Analysis  
```bash
# Detailed analysis with many frames
video-insight analyze "video.mp4" \
  --interval 15 \
  --max-frames 200 \
  --audio-chunk-seconds 180 \
  --keep-media
```

### Blog Post Formats

The tool generates three blog post formats:

1. **Medium.com**: Clean markdown with image placeholders
2. **Newsletter**: HTML with inline styles for email platforms  
3. **WordPress**: Compatible markdown with image embedding

Each includes publishing instructions and optimized formatting.

## Requirements

- Python 3.8+
- OpenAI API key
- ffmpeg (for video processing)
- yt-dlp (auto-installed)

### Supported Video Sources

- YouTube videos (any URL format)
- Local video files (.mp4, .mkv, .webm, .avi, .mov, .wmv, .flv, .m4v)

## Development

### Setup Development Environment

```bash
# Clone and setup
git clone https://github.com/yourusername/video-insight-ai.git
cd video-insight-ai

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Code formatting
black src/
flake8 src/
```

### Project Structure

```
video-insight-ai/
├── src/video_insight_ai/
│   ├── core/               # Core functionality
│   │   ├── video_analyzer.py
│   │   └── blog_generator.py
│   ├── utils/              # Utilities  
│   │   ├── logging_config.py
│   │   └── validators.py
│   └── cli.py              # Command-line interface
├── requirements.txt
├── setup.py
└── README.md
```

## Troubleshooting

### Common Issues

**API Key Error**
```
Error: OPENAI_API_KEY environment variable is required
```
- Ensure `.env` file exists with valid OpenAI API key
- API key must start with `sk-`

**FFmpeg Not Found**
```
Error: ffmpeg not found in PATH
```
- Install ffmpeg and ensure it's in your system PATH
- Test with `ffmpeg -version`

**Memory/Performance Issues**
- Reduce `--max-frames` for large videos
- Increase `--audio-chunk-seconds` for long audio
- Use `--interval` to skip frames

**Model Compatibility**
- Use `gpt-4o` for vision (not `gpt-4o-mini`)
- Use `whisper-1` if transcription model issues occur

## Cost Optimization

- **Vision API**: ~$0.01-0.02 per frame analyzed
- **Transcription**: ~$0.006 per minute of audio
- **Text Generation**: ~$0.01-0.03 per blog post

**Tips to reduce costs:**
- Use larger `--interval` values (60+ seconds)
- Limit `--max-frames` (5-20 for testing)
- Use shorter `--audio-chunk-seconds` for better parallelization

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI for GPT-4 Vision and Whisper APIs
- yt-dlp for video downloading capabilities  
- FFmpeg for video processing

## Support

- 📧 Email: support@example.com
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/video-insight-ai/issues)
- 📖 Documentation: [Wiki](https://github.com/yourusername/video-insight-ai/wiki)
