"""
Transcript Loader
Handles loading and parsing transcript files in various formats
"""

import json
import logging
from typing import List, Dict
import re
import os

logger = logging.getLogger(__name__)

class TranscriptLoader:
    """
    Loads transcript files in various formats and converts to standard format
    """
    
    def __init__(self):
        self.supported_formats = ['.json', '.srt', '.vtt', '.txt']
    
    def load_transcript(self, file_path: str) -> List[Dict[str, str]]:
        """
        Alias for load method to maintain compatibility
        
        Args:
            file_path: Path to transcript file
            
        Returns:
            List of transcript segments
        """
        return self.load(file_path)
    
    def load(self, file_path: str) -> List[Dict[str, str]]:
        """
        Load transcript from file
        
        Args:
            file_path: Path to transcript file
            
        Returns:
            List of transcript segments with 'time' and 'text' keys
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Transcript file not found: {file_path}")
        
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == '.json':
            return self._load_json(file_path)
        elif file_extension == '.srt':
            return self._load_srt(file_path)
        elif file_extension == '.vtt':
            return self._load_vtt(file_path)
        elif file_extension == '.txt':
            return self._load_txt(file_path)
        else:
            raise ValueError(f"Unsupported transcript format: {file_extension}")
    
    def _load_json(self, file_path: str) -> List[Dict[str, str]]:
        """Load JSON format transcript"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different JSON structures
            if isinstance(data, list):
                # Direct list format: [{"time": "00:12:30", "text": "..."}]
                segments = []
                for item in data:
                    if isinstance(item, dict) and 'time' in item and 'text' in item:
                        segments.append({
                            'time': str(item['time']),
                            'text': str(item['text'])
                        })
                return segments
            
            elif isinstance(data, dict):
                # Object format with segments
                if 'segments' in data:
                    segments = []
                    for item in data['segments']:
                        if 'time' in item and 'text' in item:
                            segments.append({
                                'time': str(item['time']),
                                'text': str(item['text'])
                            })
                    return segments
                
                # Whisper API format
                elif 'results' in data:
                    segments = []
                    for item in data['results']:
                        if 'start_time' in item and 'transcript' in item:
                            segments.append({
                                'time': self._seconds_to_timestamp(item['start_time']),
                                'text': str(item['transcript'])
                            })
                    return segments
            
            raise ValueError("Unsupported JSON transcript structure")
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error loading JSON transcript: {str(e)}")
    
    def _load_srt(self, file_path: str) -> List[Dict[str, str]]:
        """Load SRT subtitle format"""
        try:
            segments = []
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse SRT format
            srt_pattern = r'(\d+)\s*\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\s*\n(.*?)(?=\n\d+\s*\n|\n*$)'
            matches = re.findall(srt_pattern, content, re.DOTALL)
            
            for match in matches:
                sequence, start_time, end_time, text = match
                
                # Convert SRT timestamp to standard format
                start_timestamp = self._srt_to_timestamp(start_time)
                
                # Clean text (remove HTML tags, extra whitespace)
                clean_text = re.sub(r'<[^>]+>', '', text)
                clean_text = re.sub(r'\s+', ' ', clean_text).strip()
                
                if clean_text:  # Skip empty segments
                    segments.append({
                        'time': start_timestamp,
                        'text': clean_text
                    })
            
            return segments
            
        except Exception as e:
            raise ValueError(f"Error loading SRT transcript: {str(e)}")
    
    def _load_vtt(self, file_path: str) -> List[Dict[str, str]]:
        """Load WebVTT format"""
        try:
            segments = []
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            current_segment = None
            i = 0
            
            while i < len(lines):
                line = lines[i].strip()
                
                # Skip WEBVTT header and empty lines
                if line == 'WEBVTT' or line == '' or line.isdigit():
                    i += 1
                    continue
                
                # Look for timestamp line (handles both formats)
                # Format 1: HH:MM:SS.mmm --> HH:MM:SS.mmm  
                # Format 2: seconds.decimal --> seconds.decimal
                timestamp_match = re.match(r'([\d:.]+)\s*-->\s*([\d:.]+)', line)
                
                if timestamp_match:
                    start_time, end_time = timestamp_match.groups()
                    
                    # Convert to standard timestamp format
                    start_timestamp = self._normalize_timestamp(start_time)
                    
                    # Get text from next lines until we hit another timestamp or segment number
                    text_lines = []
                    i += 1
                    
                    while i < len(lines):
                        next_line = lines[i].strip()
                        
                        # Stop if we hit another timestamp, segment number, or empty line before text
                        if (re.match(r'([\d:.]+)\s*-->\s*([\d:.]+)', next_line) or 
                            next_line.isdigit() or 
                            (next_line == '' and text_lines)):
                            break
                            
                        if next_line:  # Non-empty line
                            text_lines.append(next_line)
                        
                        i += 1
                    
                    # Combine text lines
                    if text_lines:
                        combined_text = ' '.join(text_lines)
                        # Clean HTML tags and normalize whitespace
                        clean_text = re.sub(r'<[^>]+>', '', combined_text)
                        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
                        
                        if clean_text:
                            segments.append({
                                'time': start_timestamp,
                                'text': clean_text,
                                'start': float(start_time) if '.' in start_time and ':' not in start_time else None
                            })
                else:
                    i += 1
            
            logger.info(f"Loaded {len(segments)} segments from VTT file")
            return segments
            
        except Exception as e:
            logger.error(f"Error loading VTT transcript: {str(e)}")
            raise ValueError(f"Error loading VTT transcript: {str(e)}")
    
    def _normalize_timestamp(self, timestamp: str) -> str:
        """Convert various timestamp formats to HH:MM:SS"""
        try:
            # If it's already in HH:MM:SS format, clean it up
            if ':' in timestamp:
                # Handle HH:MM:SS.mmm format
                if '.' in timestamp:
                    timestamp = timestamp.split('.')[0]  # Remove milliseconds
                return timestamp
            else:
                # Handle seconds.decimal format
                seconds = float(timestamp)
                hours = int(seconds // 3600)
                minutes = int((seconds % 3600) // 60)
                secs = int(seconds % 60)
                return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        except:
            return "00:00:00"
    
    def _load_txt(self, file_path: str) -> List[Dict[str, str]]:
        """Load plain text format with timestamps"""
        try:
            segments = []
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            current_time = "00:00:00"
            current_text = ""
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Look for timestamp patterns
                timestamp_match = re.match(r'(\d{1,2}:\d{2}:\d{2})', line)
                if timestamp_match:
                    # Save previous segment if exists
                    if current_text.strip():
                        segments.append({
                            'time': current_time,
                            'text': current_text.strip()
                        })
                    
                    # Start new segment
                    current_time = timestamp_match.group(1)
                    current_text = line[len(timestamp_match.group(0)):].strip()
                else:
                    # Continue current segment
                    current_text += " " + line
            
            # Add final segment
            if current_text.strip():
                segments.append({
                    'time': current_time,
                    'text': current_text.strip()
                })
            
            # If no timestamps found, create artificial segments
            if not segments and lines:
                full_text = " ".join(line.strip() for line in lines if line.strip())
                
                # Split into chunks (approximately 30 seconds each)
                words = full_text.split()
                chunk_size = 50  # words per chunk
                
                for i in range(0, len(words), chunk_size):
                    chunk_text = " ".join(words[i:i + chunk_size])
                    timestamp = self._seconds_to_timestamp(i * 0.6)  # Estimate 0.6 sec per word
                    
                    segments.append({
                        'time': timestamp,
                        'text': chunk_text
                    })
            
            return segments
            
        except Exception as e:
            raise ValueError(f"Error loading TXT transcript: {str(e)}")
    
    def _srt_to_timestamp(self, srt_time: str) -> str:
        """Convert SRT timestamp (00:12:30,123) to standard format (00:12:30)"""
        return srt_time.split(',')[0]
    
    def _vtt_to_timestamp(self, vtt_time: str) -> str:
        """Convert VTT timestamp (00:12:30.123) to standard format (00:12:30)"""
        return vtt_time.split('.')[0]
    
    def _seconds_to_timestamp(self, seconds: float) -> str:
        """Convert seconds to HH:MM:SS format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
