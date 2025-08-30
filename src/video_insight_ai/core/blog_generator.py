#!/usr/bin/env python3
"""
Blog post generator from video analysis reports
"""
import os
import json
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

try:
    from openai import OpenAI
except ImportError:
    raise ImportError("OpenAI package not installed. Run: pip install -r requirements.txt")


class BlogGenerator:
    """Generate blog posts from video analysis reports"""
    
    def __init__(self, openai_api_key: str = None):
        self.client = OpenAI(api_key=openai_api_key or os.environ.get("OPENAI_API_KEY"))
        
    def generate_blog_post(
        self, 
        report_path: Path, 
        frames_dir: Path, 
        output_dir: Path,
        style: str = "medium",
        title: str = None,
        author: str = None
    ) -> Dict[str, Path]:
        """Generate a blog post from video analysis report"""
        
        logging.info(f"Generating blog post from report: {report_path}")
        
        # Read the existing report
        with open(report_path, 'r', encoding='utf-8') as f:
            report_content = f.read()
            
        # Read JSON report for structured data
        json_path = report_path.with_suffix('.json')
        if json_path.exists():
            with open(json_path, 'r', encoding='utf-8') as f:
                report_data = json.load(f)
        else:
            report_data = {}
            
        # Get available frames
        frame_files = list(frames_dir.glob("*.jpg")) if frames_dir.exists() else []
        
        logging.info(f"Found {len(frame_files)} frame images")
        
        # Generate blog post content using AI
        blog_content = self._generate_content(report_content, report_data, frame_files, style, title, author)
        
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy frame images to output directory
        images_dir = output_dir / "images"
        images_dir.mkdir(exist_ok=True)
        
        copied_images = []
        for frame in frame_files:
            dest = images_dir / frame.name
            shutil.copy2(frame, dest)
            copied_images.append(dest)
            
        logging.info(f"Copied {len(copied_images)} images to {images_dir}")
        
        # Write different format outputs
        outputs = {}
        
        # Medium-style markdown
        medium_path = output_dir / "blog_post_medium.md"
        with open(medium_path, 'w', encoding='utf-8') as f:
            f.write(blog_content['medium'])
        outputs['medium'] = medium_path
        
        # Newsletter HTML
        newsletter_path = output_dir / "newsletter.html"
        with open(newsletter_path, 'w', encoding='utf-8') as f:
            f.write(blog_content['newsletter'])
        outputs['newsletter'] = newsletter_path
        
        # WordPress/Ghost compatible markdown
        wordpress_path = output_dir / "blog_post_wordpress.md"
        with open(wordpress_path, 'w', encoding='utf-8') as f:
            f.write(blog_content['wordpress'])
        outputs['wordpress'] = wordpress_path
        
        # Create a package with images and content
        self._create_blog_package(output_dir, outputs, copied_images)
        
        logging.info(f"Blog post generated successfully in {output_dir}")
        
        return outputs
        
    def _generate_content(
        self, 
        report_content: str, 
        report_data: dict, 
        frame_files: List[Path],
        style: str,
        title: str,
        author: str
    ) -> Dict[str, str]:
        """Generate blog post content using AI"""
        
        # Extract video metadata
        video_source = report_data.get('source', 'Unknown video')
        video_filename = report_data.get('filename', '')
        
        # Create frame descriptions for context
        frame_descriptions = []
        if 'frames' in report_data:
            for i, frame_data in enumerate(report_data['frames'][:5]):  # Limit to first 5 frames
                timestamp = frame_data.get('timestamp_s', 0)
                analysis = frame_data.get('analysis', '')
                frame_descriptions.append(f"Frame at {timestamp//60:02d}:{timestamp%60:02d}: {analysis}")
        
        # Generate title if not provided
        if not title:
            title = self._generate_title(video_source, report_data.get('transcript_text', ''))
            
        if not author:
            author = "AI Video Analyst"
            
        logging.info(f"Generating blog post with title: '{title}'")
        
        prompt = f"""
        Create an engaging blog post based on this video analysis report. 
        
        VIDEO SOURCE: {video_source}
        TITLE: {title}
        AUTHOR: {author}
        
        ORIGINAL REPORT:
        {report_content}
        
        FRAME DESCRIPTIONS:
        {chr(10).join(frame_descriptions)}
        
        Create three versions:
        1. MEDIUM: A Medium.com style article with engaging headings, subheadings, and image placeholders
        2. NEWSLETTER: An HTML newsletter format with inline styles
        3. WORDPRESS: A WordPress/Ghost compatible markdown with proper image embedding
        
        Guidelines:
        - Make it engaging and readable
        - Include key insights from the video
        - Add relevant quotes from the transcript
        - Use the frame analyses to create compelling visual descriptions
        - Include image placeholders: ![Image Description](images/frame_XXXXXX.jpg)
        - Add call-to-action at the end
        - Keep paragraphs short for readability
        - Use bullet points and numbered lists where appropriate
        
        Format your response as JSON with keys: "medium", "newsletter", "wordpress"
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert content creator who writes engaging blog posts and newsletters. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=4000
            )
            
            content = response.choices[0].message.content.strip()
            
            # Try to parse JSON response
            try:
                if content.startswith('```json'):
                    content = content.split('```json')[1].split('```')[0]
                elif content.startswith('```'):
                    content = content.split('```')[1].split('```')[0]
                    
                blog_content = json.loads(content)
                
                # Ensure all required keys exist
                for key in ['medium', 'newsletter', 'wordpress']:
                    if key not in blog_content:
                        blog_content[key] = f"# {title}\n\nContent generation failed for {key} format."
                        
                return blog_content
                
            except json.JSONDecodeError:
                # Fallback: create basic content if JSON parsing fails
                return self._create_fallback_content(title, author, report_content, frame_descriptions)
                
        except Exception as e:
            logging.error(f"Error generating blog content: {e}")
            return self._create_fallback_content(title, author, report_content, frame_descriptions)
            
    def _generate_title(self, video_source: str, transcript: str) -> str:
        """Generate a compelling title from video content"""
        try:
            prompt = f"""
            Generate a compelling, clickable blog post title based on this video content.
            
            VIDEO SOURCE: {video_source}
            TRANSCRIPT EXCERPT: {transcript[:500]}...
            
            Make it:
            - Engaging and clickable
            - 50-70 characters
            - Descriptive of the main topic
            - Include keywords that would perform well
            
            Return only the title, nothing else.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert copywriter who creates compelling headlines."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=100
            )
            
            title = response.choices[0].message.content.strip().strip('"')
            return title
            
        except Exception as e:
            logging.error(f"Error generating title: {e}")
            return "Video Analysis: Key Insights and Takeaways"
            
    def _create_fallback_content(self, title: str, author: str, report_content: str, frame_descriptions: List[str]) -> Dict[str, str]:
        """Create basic fallback content if AI generation fails"""
        
        date = datetime.now().strftime("%B %d, %Y")
        
        medium_content = f"""# {title}

*By {author} • {date}*

## Overview

This article provides insights from an AI-powered video analysis, breaking down key moments and extracting valuable information from the content.

## Key Insights

{chr(10).join([f"• {desc}" for desc in frame_descriptions[:5]])}

## Full Analysis

{report_content}

## Conclusion

This analysis demonstrates the power of AI in extracting meaningful insights from video content, providing structured summaries and key takeaways.

---

*Generated using AI Video Analysis Tools*
"""

        newsletter_content = f"""<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; }}
        .header {{ background: #f8f9fa; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; }}
        .footer {{ background: #e9ecef; padding: 15px; text-align: center; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{title}</h1>
        <p>By {author} • {date}</p>
    </div>
    <div class="content">
        <h2>Key Insights</h2>
        <ul>
        {''.join([f"<li>{desc}</li>" for desc in frame_descriptions[:5]])}
        </ul>
        <h2>Full Analysis</h2>
        <div>{report_content.replace(chr(10), '<br>')}</div>
    </div>
    <div class="footer">
        Generated using AI Video Analysis Tools
    </div>
</body>
</html>"""

        wordpress_content = medium_content  # Same as medium for fallback
        
        return {
            "medium": medium_content,
            "newsletter": newsletter_content,
            "wordpress": wordpress_content
        }
        
    def _create_blog_package(self, output_dir: Path, outputs: Dict[str, Path], images: List[Path]):
        """Create a complete blog package with images and instructions"""
        
        # Create README with instructions
        readme_content = f"""# Blog Post Package

Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Contents

- `blog_post_medium.md` - Medium.com compatible markdown
- `newsletter.html` - HTML newsletter format
- `blog_post_wordpress.md` - WordPress/Ghost compatible markdown
- `images/` - Frame images from video analysis

## Publishing Instructions

### Medium.com
1. Copy content from `blog_post_medium.md`
2. Upload images from `images/` folder
3. Replace image placeholders with uploaded images

### Newsletter (Mailchimp, ConvertKit, etc.)
1. Use `newsletter.html` as template
2. Upload images to your newsletter platform
3. Update image URLs in the HTML

### WordPress/Ghost
1. Copy content from `blog_post_wordpress.md`
2. Upload images to media library
3. Update image URLs in the markdown

## Image Files
{chr(10).join([f"- {img.name}" for img in images])}

## Tips
- Optimize images for web (compress if needed)
- Add alt text for accessibility
- Customize content to match your brand voice
- Add your own CTAs and links
"""
        
        readme_path = output_dir / "README.md"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
            
        logging.info(f"Created package README at {readme_path}")
