#!/usr/bin/env python3
"""
Command-line interface for Video Insight AI
"""
import os
import sys
import click
from pathlib import Path
from typing import Optional

from .core import VideoAnalyzer, BlogGenerator
from .utils import setup_logging


@click.group()
@click.option('--debug', is_flag=True, help='Enable debug logging')
@click.pass_context
def cli(ctx, debug):
    """Video Insight AI - Analyze videos and generate blog posts"""
    ctx.ensure_object(dict)
    setup_logging(debug=debug)


@cli.command()
@click.argument('video_input')
@click.option('--output', '-o', default='runs', help='Output directory')
@click.option('--interval', default=30, help='Frame sample interval in seconds')
@click.option('--max-frames', default=120, help='Maximum number of frames to analyze')
@click.option('--audio-chunk-seconds', default=300, help='Audio chunk length for transcription')
@click.option('--vision-model', default='gpt-4o', help='Vision model to use')
@click.option('--transcribe-model', default='gpt-4o-mini-transcribe', help='Transcription model to use')
@click.option('--skip-download', is_flag=True, help='Treat input as local file only')
@click.option('--keep-media', is_flag=True, help='Keep temporary media files')
def analyze(video_input, output, interval, max_frames, audio_chunk_seconds, 
           vision_model, transcribe_model, skip_download, keep_media):
    """Analyze a video with AI vision and transcription"""
    
    # Check for API key
    if not os.environ.get('OPENAI_API_KEY'):
        click.echo(click.style('Error: OPENAI_API_KEY environment variable is required', fg='red'))
        click.echo('Please set your OpenAI API key in .env file or environment variables')
        sys.exit(1)
    
    try:
        analyzer = VideoAnalyzer()
        
        output_dir = Path(output)
        if output == 'runs':
            # Use timestamped directory for runs
            from datetime import datetime
            output_dir = Path('runs') / datetime.now().strftime("%Y%m%d-%H%M%S")
        
        click.echo(f"🎬 Starting video analysis...")
        click.echo(f"📹 Input: {video_input}")
        click.echo(f"📁 Output: {output_dir}")
        
        json_path, md_path = analyzer.analyze_video(
            input_source=video_input,
            output_dir=output_dir,
            frame_interval=interval,
            max_frames=max_frames,
            audio_chunk_seconds=audio_chunk_seconds,
            vision_model=vision_model,
            transcribe_model=transcribe_model,
            skip_download=skip_download,
            keep_media=keep_media
        )
        
        click.echo(click.style('✅ Analysis complete!', fg='green'))
        click.echo(f"📄 JSON Report: {json_path}")
        click.echo(f"📝 Markdown Report: {md_path}")
        
    except Exception as e:
        click.echo(click.style(f'❌ Error: {str(e)}', fg='red'))
        sys.exit(1)


@cli.command('generate-blog')
@click.argument('report_path')
@click.option('--output', '-o', default='blog_output', help='Output directory for blog post')
@click.option('--title', help='Custom blog post title')
@click.option('--author', help='Author name')
@click.option('--style', default='medium', type=click.Choice(['medium', 'newsletter', 'wordpress']), 
              help='Blog post style/platform')
def generate_blog(report_path, output, title, author, style):
    """Generate blog post from video analysis report"""
    
    # Check for API key
    if not os.environ.get('OPENAI_API_KEY'):
        click.echo(click.style('Error: OPENAI_API_KEY environment variable is required', fg='red'))
        sys.exit(1)
    
    try:
        generator = BlogGenerator()
        
        # Determine paths
        report_path = Path(report_path)
        
        if report_path.is_dir():
            # If directory provided, look for report.md
            report_file = report_path / "report.md"
            frames_dir = report_path / "frames"
        else:
            # If file provided, assume frames are in same directory
            report_file = report_path
            frames_dir = report_path.parent / "frames"
            
        if not report_file.exists():
            click.echo(click.style(f'Error: Report file not found at {report_file}', fg='red'))
            sys.exit(1)
            
        output_dir = Path(output)
        
        click.echo(f"📝 Generating blog post from: {report_file}")
        click.echo(f"📁 Output directory: {output_dir}")
        
        outputs = generator.generate_blog_post(
            report_path=report_file,
            frames_dir=frames_dir,
            output_dir=output_dir,
            style=style,
            title=title,
            author=author
        )
        
        click.echo(click.style('✅ Blog post generation complete!', fg='green'))
        click.echo('\n📄 Generated files:')
        for format_name, path in outputs.items():
            click.echo(f"  • {format_name}: {path}")
            
    except Exception as e:
        click.echo(click.style(f'❌ Error: {str(e)}', fg='red'))
        sys.exit(1)


@cli.command()
@click.argument('video_input')
@click.option('--blog-title', help='Blog post title')
@click.option('--blog-author', help='Blog post author')
@click.option('--interval', default=30, help='Frame sample interval in seconds')
@click.option('--max-frames', default=20, help='Maximum number of frames to analyze')
def full_pipeline(video_input, blog_title, blog_author, interval, max_frames):
    """Run complete pipeline: analyze video + generate blog post"""
    
    # Check for API key
    if not os.environ.get('OPENAI_API_KEY'):
        click.echo(click.style('Error: OPENAI_API_KEY environment variable is required', fg='red'))
        sys.exit(1)
    
    try:
        from datetime import datetime
        
        # Step 1: Analyze video
        analyzer = VideoAnalyzer()
        output_dir = Path('runs') / datetime.now().strftime("%Y%m%d-%H%M%S")
        
        click.echo(f"🎬 Step 1: Analyzing video...")
        json_path, md_path = analyzer.analyze_video(
            input_source=video_input,
            output_dir=output_dir,
            frame_interval=interval,
            max_frames=max_frames,
            keep_media=True  # Keep for blog generation
        )
        
        click.echo(click.style('✅ Video analysis complete!', fg='green'))
        
        # Step 2: Generate blog post
        generator = BlogGenerator()
        blog_output_dir = output_dir.parent / f"{output_dir.name}_blog"
        
        click.echo(f"📝 Step 2: Generating blog post...")
        blog_outputs = generator.generate_blog_post(
            report_path=md_path,
            frames_dir=output_dir / "frames",
            output_dir=blog_output_dir,
            title=blog_title,
            author=blog_author
        )
        
        click.echo(click.style('✅ Full pipeline complete!', fg='green'))
        click.echo(f"\n📊 Analysis Results: {output_dir}")
        click.echo(f"📝 Blog Post: {blog_output_dir}")
        
    except Exception as e:
        click.echo(click.style(f'❌ Error: {str(e)}', fg='red'))
        sys.exit(1)


def main():
    """Entry point for the CLI"""
    cli()


if __name__ == '__main__':
    main()
