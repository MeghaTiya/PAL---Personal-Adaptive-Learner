#!/usr/bin/env python3
"""
Video Transcript Ge# Show warnings only once
if not WHISPER_AVAILABLE:
    print("Warning: For best results, install whisper: pip install openai-whisper")
if not PYDUB_AVAILABLE:
    print("Warning: Install pydub for audio processing: pip install pydub")
if not MOVIEPY_AVAILABLE:
    print("Warning: Install moviepy for video processing: pip install moviepy (will use ffmpeg fallback)")
if not SPEECH_RECOGNITION_AVAILABLE:
    print("Warning: Install SpeechRecognition for Google Speech: pip install SpeechRecognition")========================

Generates transcripts from video files using speech-to-text technology.
Supports multiple speech recognition engines and output formats.
"""

import os
import subprocess
import tempfile
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    sr = None
    SPEECH_RECOGNITION_AVAILABLE = False

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    AudioSegment = None
    PYDUB_AVAILABLE = False

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    whisper = None
    WHISPER_AVAILABLE = False

try:
    import moviepy.editor as mp
    MOVIEPY_AVAILABLE = True
except ImportError:
    mp = None
    MOVIEPY_AVAILABLE = False

# Show warnings only once
if not WHISPER_AVAILABLE:
    print("Warning: For best results, install whisper: pip install openai-whisper")
if not PYDUB_AVAILABLE:
    print("Warning: Install pydub for audio processing: pip install pydub")
if not MOVIEPY_AVAILABLE:
    print("Warning: Install moviepy for video processing: pip install moviepy")
if not SPEECH_RECOGNITION_AVAILABLE:
    print("Warning: Install speech recognition: pip install SpeechRecognition")

logger = logging.getLogger(__name__)

class VideoTranscriptGenerator:
    """Generate transcripts from video files"""
    
    def __init__(self, method: str = "whisper"):
        """
        Initialize transcript generator
        
        Args:
            method: Transcription method ("whisper", "google", "sphinx")
        """
        self.method = method
        self.whisper_model = None
        self.recognizer = sr.Recognizer() if SPEECH_RECOGNITION_AVAILABLE else None
        
        # Initialize Whisper if available and requested
        if method == "whisper" and WHISPER_AVAILABLE:
            try:
                print("Loading Whisper model...")
                self.whisper_model = whisper.load_model("base")
                print("Whisper ready for transcription")
            except Exception as e:
                print(f"Warning: Whisper loading failed: {e}")
                self.method = "google"
        
        self.supported_formats = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv']
    
    def extract_audio(self, video_path: str, output_path: str = None) -> str:
        """
        Extract audio from video file
        
        Args:
            video_path: Path to video file
            output_path: Optional output audio path
            
        Returns:
            Path to extracted audio file
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        # Create output path if not provided
        if output_path is None:
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            output_path = f"{base_name}_audio.wav"
        
        try:
            if MOVIEPY_AVAILABLE:
                # Use MoviePy for audio extraction
                print(f"Extracting audio from {os.path.basename(video_path)}...")
                video = mp.VideoFileClip(video_path)
                audio = video.audio
                audio.write_audiofile(output_path, verbose=False, logger=None)
                audio.close()
                video.close()
                
            else:
                # Fallback to ffmpeg
                cmd = [
                    'ffmpeg', '-i', video_path, '-vn', '-acodec', 'pcm_s16le',
                    '-ar', '16000', '-ac', '1', '-y', output_path
                ]
                subprocess.run(cmd, check=True, capture_output=True)
            
            print(f"Audio extracted to: {os.path.basename(output_path)}")
            return output_path
            
        except Exception as e:
            raise Exception(f"Audio extraction failed: {str(e)}")
    
    def transcribe_with_whisper(self, video_path: str, model_name: str = "base") -> List[Dict]:
        """
        Transcribe video using OpenAI Whisper
        
        Args:
            video_path: Path to video file
            model_name: Whisper model to use
            
        Returns:
            List of transcript segments with timestamps
        """
        if not WHISPER_AVAILABLE:
            raise ImportError("Whisper not available. Install with: pip install openai-whisper")
        
        try:
            logger.info(f"Starting Whisper transcription of {video_path}")
            
            # Load Whisper model if not already loaded
            if self.whisper_model is None or hasattr(self.whisper_model, 'name') and self.whisper_model.name != model_name:
                logger.info(f"Loading Whisper model: {model_name}")
                self.whisper_model = whisper.load_model(model_name)
            
            # Create temporary audio file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
                temp_audio_path = temp_audio.name
            
            try:
                # Extract audio using ffmpeg directly (fallback if MoviePy not available)
                if MOVIEPY_AVAILABLE:
                    logger.info("Extracting audio from video using MoviePy")
                    video = mp.VideoFileClip(video_path)
                    audio = video.audio
                    if audio is None:
                        raise ValueError("No audio track found in video")
                    
                    audio.write_audiofile(temp_audio_path, verbose=False, logger=None)
                    audio.close()
                    video.close()
                else:
                    # Fallback: use ffmpeg directly
                    logger.info("Extracting audio from video using ffmpeg")
                    ffmpeg_cmd = [
                        "ffmpeg", "-i", video_path, "-acodec", "pcm_s16le", 
                        "-ar", "16000", "-ac", "1", "-y", temp_audio_path
                    ]
                    
                    result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
                    if result.returncode != 0:
                        raise RuntimeError(f"FFmpeg failed: {result.stderr}")
                
                # Transcribe with Whisper
                logger.info("Running Whisper transcription")
                result = self.whisper_model.transcribe(temp_audio_path, word_timestamps=True)
                
                # Format results
                transcript_segments = []
                for segment in result.get("segments", []):
                    transcript_segments.append({
                        "start": segment["start"],
                        "end": segment["end"],
                        "text": segment["text"].strip(),
                        "confidence": 1.0  # Whisper doesn't provide confidence scores
                    })
                
                logger.info(f"Whisper transcription complete: {len(transcript_segments)} segments")
                return transcript_segments
                
            finally:
                # Cleanup temporary file
                if os.path.exists(temp_audio_path):
                    os.unlink(temp_audio_path)
                
        except Exception as e:
            logger.error(f"Whisper transcription failed: {str(e)}")
            raise
    
    def transcribe_with_speech_recognition(self, audio_path: str, chunk_duration: int = 30) -> List[Dict]:
        """
        Transcribe audio using SpeechRecognition library
        
        Args:
            audio_path: Path to audio file
            chunk_duration: Duration of each chunk in seconds
            
        Returns:
            List of transcript segments
        """
        if not SPEECH_RECOGNITION_AVAILABLE or not self.recognizer:
            raise Exception("SpeechRecognition not available. Install with: pip install SpeechRecognition")
        
        if not PYDUB_AVAILABLE:
            raise Exception("pydub not available. Install with: pip install pydub")
        
        print(f"Transcribing with {self.method.title()}...")
        
        # Load audio and split into chunks
        audio = AudioSegment.from_wav(audio_path)
        chunks = self._split_audio_into_chunks(audio, chunk_duration * 1000)  # Convert to ms
        
        segments = []
        total_chunks = len(chunks)
        
        for i, (chunk, start_time) in enumerate(chunks):
            print(f"   Processing chunk {i+1}/{total_chunks}...", end='\r')
            
            try:
                # Save chunk to temporary file
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                    chunk.export(temp_file.name, format='wav')
                    
                    # Transcribe chunk
                    with sr.AudioFile(temp_file.name) as source:
                        audio_data = self.recognizer.record(source)
                        
                        if self.method == "google":
                            text = self.recognizer.recognize_google(audio_data)
                        elif self.method == "sphinx":
                            text = self.recognizer.recognize_sphinx(audio_data)
                        else:
                            text = self.recognizer.recognize_google(audio_data)  # Default
                    
                    if text.strip():
                        segments.append({
                            'start': self._seconds_to_timestamp(start_time / 1000),
                            'end': self._seconds_to_timestamp((start_time + len(chunk)) / 1000),
                            'text': text.strip(),
                            'confidence': 0.8  # Estimate
                        })
                
                # Clean up temp file
                os.unlink(temp_file.name)
                
            except sr.UnknownValueError:
                # No speech detected in this chunk
                continue
            except sr.RequestError as e:
                print(f"\nRecognition error: {e}")
                continue
            except Exception as e:
                print(f"\nChunk processing error: {e}")
                continue
        
        print(f"\nTranscription complete: {len(segments)} segments")
        return segments
    
    def _split_audio_into_chunks(self, audio, chunk_length_ms: int) -> List[Tuple]:
        """Split audio into smaller chunks for processing"""
        if not PYDUB_AVAILABLE:
            raise ImportError("pydub not available. Install with: pip install pydub")
            
        chunks = []
        duration_ms = len(audio)
        
        for start_ms in range(0, duration_ms, chunk_length_ms):
            end_ms = min(start_ms + chunk_length_ms, duration_ms)
            chunk = audio[start_ms:end_ms]
            chunks.append((chunk, start_ms / 1000.0, end_ms / 1000.0))
        
        return chunks
    
    def _seconds_to_timestamp(self, seconds: float) -> str:
        """Convert seconds to VTT timestamp format"""
        td = timedelta(seconds=seconds)
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        milliseconds = int((seconds - int(seconds)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{milliseconds:03d}"
    
    def save_as_vtt(self, segments: List[Dict], output_path: str):
        """Save transcript as WebVTT file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("WEBVTT\n\n")
            
            for i, segment in enumerate(segments):
                f.write(f"{i+1}\n")
                f.write(f"{segment['start']} --> {segment['end']}\n")
                f.write(f"{segment['text']}\n\n")
        
        print(f"VTT transcript saved: {os.path.basename(output_path)}")
    
    def save_as_srt(self, segments: List[Dict], output_path: str):
        """Save transcript as SRT file"""
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, segment in enumerate(segments):
                # Convert VTT timestamp to SRT format
                start_srt = segment['start'].replace('.', ',')
                end_srt = segment['end'].replace('.', ',')
                
                f.write(f"{i+1}\n")
                f.write(f"{start_srt} --> {end_srt}\n")
                f.write(f"{segment['text']}\n\n")
        
        print(f"SRT transcript saved: {os.path.basename(output_path)}")
    
    def save_as_json(self, segments: List[Dict], output_path: str):
        """Save transcript as JSON file"""
        transcript_data = {
            "generated_at": datetime.now().isoformat(),
            "method": self.method,
            "total_segments": len(segments),
            "segments": segments
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(transcript_data, f, indent=2, ensure_ascii=False)
        
        print(f"JSON transcript saved: {os.path.basename(output_path)}")
    
    def generate_transcript(self, video_path: str, output_dir: str = None, formats: List[str] = None) -> Dict:
        """
        Generate transcript from video file
        
        Args:
            video_path: Path to video file
            output_dir: Output directory (defaults to video directory)
            formats: List of output formats ['vtt', 'srt', 'json']
            
        Returns:
            Dictionary with transcript info and file paths
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        if formats is None:
            formats = ['vtt', 'json']
        
        if output_dir is None:
            output_dir = os.path.dirname(video_path) or '.'
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate base filename
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        audio_path = os.path.join(output_dir, f"{base_name}_temp_audio.wav")
        
        try:
            # Extract audio
            self.extract_audio(video_path, audio_path)
            
            # Generate transcript
            if self.method == "whisper" and self.whisper_model:
                segments = self.transcribe_with_whisper(audio_path)
            else:
                segments = self.transcribe_with_speech_recognition(audio_path)
            
            # Save in requested formats
            output_files = {}
            for fmt in formats:
                output_path = os.path.join(output_dir, f"{base_name}.{fmt}")
                
                if fmt == 'vtt':
                    self.save_as_vtt(segments, output_path)
                elif fmt == 'srt':
                    self.save_as_srt(segments, output_path)
                elif fmt == 'json':
                    self.save_as_json(segments, output_path)
                
                output_files[fmt] = output_path
            
            return {
                "success": True,
                "video_file": video_path,
                "segments_count": len(segments),
                "method": self.method,
                "output_files": output_files,
                "generated_at": datetime.now().isoformat()
            }
            
        finally:
            # Clean up temporary audio file
            if os.path.exists(audio_path):
                os.unlink(audio_path)

def main():
    """Command line interface for transcript generation"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate transcripts from video files")
    parser.add_argument("video_path", help="Path to video file")
    parser.add_argument("--method", choices=["whisper", "google", "sphinx"], 
                       default="whisper", help="Transcription method")
    parser.add_argument("--output-dir", help="Output directory")
    parser.add_argument("--formats", nargs="+", choices=["vtt", "srt", "json"],
                       default=["vtt", "json"], help="Output formats")
    
    args = parser.parse_args()
    
    print("🎬 Video Transcript Generator")
    print("=" * 40)
    
    # Check dependencies
    missing_deps = []
    if args.method == "whisper" and not WHISPER_AVAILABLE:
        missing_deps.append("openai-whisper")
    if not MOVIEPY_AVAILABLE:
        missing_deps.append("moviepy")
    
    if missing_deps:
        print(f"Missing dependencies: {', '.join(missing_deps)}")
        print("Install with: pip install " + " ".join(missing_deps))
        return
    
    try:
        generator = VideoTranscriptGenerator(method=args.method)
        result = generator.generate_transcript(
            args.video_path,
            output_dir=args.output_dir,
            formats=args.formats
        )
        
        if result["success"]:
            print("\nTranscript generation successful!")
            print(f"Generated {result['segments_count']} segments")
            print("Output files:")
            for fmt, path in result["output_files"].items():
                print(f"   {fmt.upper()}: {path}")
        else:
            print("Transcript generation failed")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
