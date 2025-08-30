#!/usr/bin/env python3
"""
Core video analysis functionality
"""
import os
import sys
import time
import logging
import shutil
import subprocess
import base64
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
from typing import Dict, List, Optional, Tuple

try:
    from openai import OpenAI
    from tqdm import tqdm
except ImportError:
    raise ImportError("Required packages not installed. Run: pip install -r requirements.txt")


class VideoAnalyzer:
    """Main video analysis class that handles video processing and AI analysis"""
    
    def __init__(self, openai_api_key: str = None):
        """Initialize with OpenAI API key"""
        self.client = OpenAI(api_key=openai_api_key or os.environ.get("OPENAI_API_KEY"))
        self.ffmpeg_bin = shutil.which("ffmpeg")
        self.ytdlp_bin = shutil.which("yt-dlp")
        
        if not self.ffmpeg_bin:
            raise RuntimeError("ffmpeg not found in PATH. Please install ffmpeg.")
        if not self.ytdlp_bin:
            logging.warning("yt-dlp not found in PATH. Installing...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"])
            self.ytdlp_bin = shutil.which("yt-dlp")
            
        logging.info(f"VideoAnalyzer initialized with ffmpeg: {self.ffmpeg_bin}")
        logging.info(f"yt-dlp: {self.ytdlp_bin}")

    @staticmethod
    def is_url(s: str) -> bool:
        """Check if string is a URL"""
        u = urlparse(s)
        return bool(u.scheme and u.netloc)

    @staticmethod
    def b64_image(path: Path) -> str:
        """Convert image to base64 string"""
        return base64.b64encode(path.read_bytes()).decode("utf-8")

    def fetch_video(self, input_arg: str, run_dir: Path, skip_download: bool = False) -> Tuple[Path, Dict]:
        """Download video if URL, copy if local file"""
        videos_dir = run_dir / "video"
        videos_dir.mkdir(parents=True, exist_ok=True)
        
        logging.info(f"Fetching video from: {input_arg}")
        logging.info(f"Output directory: {videos_dir}")

        if self.is_url(input_arg) and not skip_download:
            logging.info(f"Starting download with yt-dlp: {input_arg}")
            outtmpl = str(videos_dir / "%(id)s_%(title).200B.%(ext)s")
            cmd = [
                self.ytdlp_bin,
                "-S", "res,ext:mp4:m4a",
                "-f", "bv*+ba/b",
                "-o", outtmpl,
                input_arg
            ]
            try:
                logging.info(f"Running command: {' '.join(cmd)}")
                subprocess.run(cmd, check=True)
                logging.info("Download completed successfully")
            except subprocess.CalledProcessError as e:
                logging.error(f"Download failed with exit code {e.returncode}")
                raise
                
            files = sorted(videos_dir.glob("*.mp4")) + sorted(videos_dir.glob("*.mkv")) + sorted(videos_dir.glob("*.webm"))
            if not files:
                logging.error("Download succeeded but no media file found")
                raise RuntimeError("Download succeeded but no media file found.")
                
            video_path = files[0]
            logging.info(f"Using downloaded video: {video_path} ({video_path.stat().st_size} bytes)")
            meta = {"source": input_arg, "filename": video_path.name}
            return video_path, meta
        else:
            logging.info(f"Using local file: {input_arg}")
            p = Path(input_arg).expanduser().resolve()
            if not p.exists():
                logging.error(f"Local file not found: {p}")
                raise FileNotFoundError(f"Local file not found: {p}")
            dest = videos_dir / p.name
            if str(p) != str(dest):
                logging.info(f"Copying {p} to {dest}")
                shutil.copy2(p, dest)
            logging.info(f"Using local video: {dest} ({dest.stat().st_size} bytes)")
            meta = {"source": "local", "filename": dest.name}
            return dest, meta

    def extract_audio(self, video_path: Path, run_dir: Path) -> Path:
        """Extract audio from video file"""
        audio_dir = run_dir / "audio"
        audio_dir.mkdir(exist_ok=True)
        out = audio_dir / (video_path.stem + ".m4a")
        logging.info(f"Extracting audio from {video_path} to {out}")
        
        cmd = [
            self.ffmpeg_bin, "-y",
            "-i", str(video_path),
            "-vn", "-acodec", "aac", "-b:a", "192k",
            str(out)
        ]
        
        logging.info(f"Running ffmpeg command: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            logging.info(f"Audio extraction completed successfully: {out}")
        except subprocess.CalledProcessError as e:
            logging.error(f"Audio extraction failed with exit code {e.returncode}")
            logging.error(f"Error output: {e.stderr if e.stderr else 'None'}")
            raise
        
        if not out.exists() or out.stat().st_size == 0:
            logging.error(f"Audio extraction failed - output file is missing or empty")
            raise RuntimeError("Audio extraction failed - output file is missing or empty")
            
        logging.info(f"Audio file size: {out.stat().st_size} bytes")
        return out

    def sample_frames(self, video_path: Path, run_dir: Path, interval_s: int) -> Tuple[Path, List[Path]]:
        """Extract frames at regular intervals"""
        frames_dir = run_dir / "frames"
        frames_dir.mkdir(exist_ok=True)
        logging.info(f"Sampling frames every {interval_s} seconds from {video_path}")
        logging.info(f"Output directory for frames: {frames_dir}")

        # fps=1/interval extracts one frame per `interval_s`
        pattern = frames_dir / "frame_%06d.jpg"
        cmd = [
            self.ffmpeg_bin, "-y",
            "-i", str(video_path),
            "-vf", f"fps=1/{interval_s}",
            "-q:v", "2",
            str(pattern)
        ]
        
        logging.info(f"Running ffmpeg command: {' '.join(cmd)}")
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            logging.info("Frame extraction completed successfully")
        except subprocess.CalledProcessError as e:
            logging.error(f"Frame extraction failed with exit code {e.returncode}")
            logging.error(f"Error output: {e.stderr if e.stderr else 'None'}")
            raise

        frames = sorted(frames_dir.glob("frame_*.jpg"))
        logging.info(f"Extracted {len(frames)} frames")
        
        if not frames:
            logging.error("No frames were extracted")
            raise RuntimeError("No frames were extracted.")
            
        # Log some details about the frames
        if frames:
            logging.info(f"First frame: {frames[0]}, size: {frames[0].stat().st_size} bytes")
            logging.info(f"Last frame: {frames[-1]}, size: {frames[-1].stat().st_size} bytes")
            
        return frames_dir, frames

    def analyze_frames(self, frames: List[Path], prompt_text: str, interval_s: int, model: str = "gpt-4o") -> List[Dict]:
        """Analyze frames with Vision API"""
        results = []
        logging.info(f"Starting frame analysis using model: {model}")
        logging.info(f"Number of frames to analyze: {len(frames)}")
        
        for idx, frame in enumerate(tqdm(frames, desc="Vision frames")):
            ts = idx * interval_s
            frame_time = f"{ts//60:02d}:{ts%60:02d}"
            logging.info(f"Analyzing frame {idx+1}/{len(frames)} at timestamp {frame_time}")
            logging.info(f"Frame path: {frame}, size: {frame.stat().st_size} bytes")
            
            try:
                start_time = time.time()
                data_uri = f"data:image/jpeg;base64,{self.b64_image(frame)}"
                logging.info(f"Base64 encoding completed for frame {idx+1}")
                
                # Chat Completions with multimodal payload
                resp = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role":"system","content":"You are a precise video scene analyst. Be specific, concise, and avoid hallucinations."},
                        {"role":"user","content":[
                            {"type":"text","text": f"{prompt_text}\n\nTIMESTAMP (sec): {ts}"},
                            {"type":"image_url","image_url":{"url": data_uri}}
                        ]}
                    ],
                    temperature=0.2,
                )
                elapsed = time.time() - start_time
                text = resp.choices[0].message.content.strip()
                logging.info(f"Frame {idx+1} analysis completed in {elapsed:.2f}s")
                logging.info(f"Analysis result: {text[:100]}...")
                results.append({"timestamp_s": ts, "frame_path": str(frame), "analysis": text})
            except Exception as e:
                logging.error(f"Error analyzing frame {idx+1}: {str(e)}")
                # Continue with other frames rather than failing completely
                results.append({"timestamp_s": ts, "frame_path": str(frame), "analysis": f"ERROR: {str(e)}"})    
        
        logging.info(f"Completed analysis of {len(results)} frames")
        return results

    def segment_audio(self, audio_path: Path, chunk_seconds: int, workdir: Path) -> List[Path]:
        """Split audio into chunks"""
        outdir = workdir / "split"
        outdir.mkdir(parents=True, exist_ok=True)
        logging.info(f"Segmenting audio into {chunk_seconds}-second chunks")
        logging.info(f"Output directory for chunks: {outdir}")
        
        # ffmpeg -f segment split
        pattern = outdir / "part_%05d.m4a"
        cmd = [
            self.ffmpeg_bin, "-y", "-i", str(audio_path),
            "-f", "segment",
            "-segment_time", str(chunk_seconds),
            "-c", "copy",
            str(pattern)
        ]
        
        logging.info(f"Running ffmpeg command: {' '.join(cmd)}")
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            logging.info("Audio segmentation completed successfully")
        except subprocess.CalledProcessError as e:
            logging.error(f"Audio segmentation failed with exit code {e.returncode}")
            logging.error(f"Error output: {e.stderr if e.stderr else 'None'}")
            raise
            
        parts = sorted(outdir.glob("part_*.m4a"))
        logging.info(f"Created {len(parts)} audio chunks")
        
        if not parts:
            logging.warning("No chunks were created, using the original audio file as a single chunk")
            # fallback: single chunk (no split)
            parts = [audio_path]
            
        # Log some details about the chunks
        if parts:
            total_size = sum(p.stat().st_size for p in parts)
            logging.info(f"Total size of all chunks: {total_size} bytes")
            logging.info(f"First chunk: {parts[0]}, size: {parts[0].stat().st_size} bytes")
            logging.info(f"Last chunk: {parts[-1]}, size: {parts[-1].stat().st_size} bytes")
            
        return parts

    def transcribe_audio(self, audio_path: Path, chunk_seconds: int, prompt: str = None, model: str = "gpt-4o-mini-transcribe") -> Dict:
        """Transcribe audio with chunking"""
        workdir = audio_path.parent
        logging.info(f"Starting audio transcription using model: {model}")
        logging.info(f"Audio path: {audio_path}, chunk size: {chunk_seconds} seconds")
        
        chunks = self.segment_audio(audio_path, chunk_seconds, workdir)
        logging.info(f"Audio segmented into {len(chunks)} chunks")
        
        full_text = []
        segments_meta = []
        
        for i, c in enumerate(tqdm(chunks, desc="Transcribe chunks")):
            logging.info(f"Transcribing chunk {i+1}/{len(chunks)}: {c}")
            logging.info(f"Chunk file size: {c.stat().st_size} bytes")
            
            try:
                start_time = time.time()
                with c.open("rb") as f:
                    # Using 'text' response format for compatibility with all models
                    resp = self.client.audio.transcriptions.create(
                        model=model,
                        file=f,
                        # The prompt can bias vocabulary / names:
                        **({"prompt": prompt} if prompt else {}),
                        response_format="text"  # Compatible with all transcription models
                    )
                elapsed = time.time() - start_time
                logging.info(f"Chunk {i+1} transcription completed in {elapsed:.2f}s")
                
                # With response_format='text', we get the text directly
                text = resp if isinstance(resp, str) else ""
                if not text:
                    text = ""
                    logging.warning(f"Empty transcription result for chunk {i+1}")
                else:
                    logging.info(f"Transcribed {len(text)} characters")
                    logging.info(f"Sample: {text[:100]}...")
                
                full_text.append(text)
                segments_meta.append({
                    "chunk_index": i,
                    "file": str(c),
                    "text": text
                })
            except Exception as e:
                logging.error(f"Error transcribing chunk {i+1}: {str(e)}")
                # Continue with other chunks rather than failing completely
                error_msg = f"[Error transcribing chunk {i+1}: {str(e)}]"
                full_text.append(error_msg)
                segments_meta.append({
                    "chunk_index": i,
                    "file": str(c),
                    "text": error_msg
                })
        
        combined_text = "\n".join(full_text).strip()
        logging.info(f"Total transcription length: {len(combined_text)} characters")
        return {
            "text": combined_text,
            "chunks": segments_meta
        }

    def analyze_video(
        self,
        input_source: str,
        output_dir: Path = None,
        frame_interval: int = 30,
        max_frames: int = 120,
        audio_chunk_seconds: int = 300,
        vision_model: str = "gpt-4o",
        transcribe_model: str = "gpt-4o-mini-transcribe",
        skip_download: bool = False,
        keep_media: bool = False,
        frame_prompt: str = None,
        audio_prompt: str = None
    ) -> Tuple[Path, Path]:
        """Complete video analysis pipeline"""
        
        # Setup output directory
        if not output_dir:
            output_dir = Path("runs") / datetime.now().strftime("%Y%m%d-%H%M%S")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Default prompts
        if not frame_prompt:
            frame_prompt = """You are analyzing a single still frame from a video.
Return 3 concise bullets:
- What's happening (speaker/scene/action)?
- Any on-screen text, charts, or key visual cues?
- The likely "topic or claim" being made at this moment.

Avoid speculation beyond the image. Keep each bullet to ~20 words."""

        if not audio_prompt:
            audio_prompt = """Use these hints to bias names/terms that may appear: YouTube, creator, product names, tech jargon.
Prefer correct casing. If audio is unclear, mark [inaudible]."""

        logging.info(f"Starting video analysis for: {input_source}")
        logging.info(f"Output directory: {output_dir}")
        
        # 1) Acquire video
        video_path, meta = self.fetch_video(input_source, output_dir, skip_download)

        # 2) Extract audio
        audio_path = self.extract_audio(video_path, output_dir)

        # 3) Sample frames
        frames_dir, frame_index = self.sample_frames(video_path, output_dir, frame_interval)
        if max_frames and len(frame_index) > max_frames:
            frame_index = frame_index[:max_frames]
            logging.info(f"Capped frames to {max_frames}")

        # 4) Analyze frames (Vision)
        frame_analyses = self.analyze_frames(
            frames=frame_index, 
            prompt_text=frame_prompt,
            interval_s=frame_interval,
            model=vision_model
        )

        # 5) Transcribe audio (chunks)
        transcript = self.transcribe_audio(
            audio_path=audio_path, 
            chunk_seconds=audio_chunk_seconds,
            prompt=audio_prompt,
            model=transcribe_model
        )

        # 6) Build + write report
        json_path, md_path = self._write_report(
            video_meta=meta,
            frame_analyses=frame_analyses,
            transcript=transcript,
            frame_interval_s=frame_interval,
            run_dir=output_dir
        )

        # 7) Cleanup (optional)
        if not keep_media:
            shutil.rmtree(frames_dir, ignore_errors=True)
            audio_dir = output_dir / "audio"
            audio_split_dir = audio_dir / "split"
            if audio_split_dir.exists():
                shutil.rmtree(audio_split_dir, ignore_errors=True)
            try: 
                audio_path.unlink(missing_ok=True)
            except Exception:
                pass

        logging.info(f"Analysis complete! Results in: {output_dir}")
        return json_path, md_path

    def _write_report(self, video_meta: Dict, frame_analyses: List[Dict], transcript: Dict, frame_interval_s: int, run_dir: Path) -> Tuple[Path, Path]:
        """Write JSON and Markdown reports"""
        import json
        
        # Prepare report data
        report_data = {
            "source": video_meta.get("source",""),
            "filename": video_meta.get("filename",""),
            "frame_interval_s": frame_interval_s,
            "frames": frame_analyses,
            "transcript_text": transcript.get("text","").strip()
        }
        
        # JSON report
        json_path = run_dir / "report.json"
        with json_path.open("w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        # Markdown report
        md_path = run_dir / "report.md"
        with md_path.open("w", encoding="utf-8") as f:
            f.write(f"# Video Insight Report\n\n")
            f.write(f"- **Source:** {report_data['source']}\n")
            f.write(f"- **File:** {report_data['filename']}\n")
            f.write(f"- **Frame interval:** {report_data['frame_interval_s']}s\n\n")
            f.write("## Timeline (frame analyses)\n")
            for fr in frame_analyses:
                mm = fr["timestamp_s"] // 60
                ss = fr["timestamp_s"] % 60
                f.write(f"**[{mm:02d}:{ss:02d}]** — {fr['analysis']}\n\n")
            f.write("## Transcript (raw)\n\n")
            f.write(report_data["transcript_text"] or "_(empty)_")
        
        logging.info(f"📄 Wrote {json_path.name} and {md_path.name}")
        return json_path, md_path
