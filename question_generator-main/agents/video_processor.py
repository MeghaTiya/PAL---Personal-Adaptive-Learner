#!/usr/bin/env python3
"""
Video Frame Extractor
Utilities for extracting and processing video frames
"""

import cv2
import os
import logging
import tempfile
import subprocess
from typing import List, Tuple, Optional
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)

class VideoProcessor:
    """
    Process video files for frame-based analysis
    """
    
    def __init__(self):
        self.supported_formats = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv']
        self.temp_dir = tempfile.mkdtemp(prefix='video_frames_')
        
    def __del__(self):
        """Cleanup temporary files"""
        try:
            import shutil
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        except:
            pass
    
    def extract_video_info(self, video_path: str) -> dict:
        """
        Extract basic video information
        """
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return {}
            
            info = {
                'fps': cap.get(cv2.CAP_PROP_FPS),
                'total_frames': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                'duration_seconds': 0,
                'codec': '',
                'file_size': 0
            }
            
            # Calculate duration
            if info['fps'] > 0:
                info['duration_seconds'] = info['total_frames'] / info['fps']
            
            # Get file size
            if os.path.exists(video_path):
                info['file_size'] = os.path.getsize(video_path)
            
            cap.release()
            return info
            
        except Exception as e:
            logger.error(f"Error extracting video info: {str(e)}")
            return {}
    
    def is_supported_format(self, video_path: str) -> bool:
        """Check if video format is supported"""
        return any(video_path.lower().endswith(ext) for ext in self.supported_formats)
    
    def extract_frames_at_intervals(self, video_path: str, interval_seconds: int = 2) -> List[Tuple[np.ndarray, float]]:
        """
        Extract frames at regular intervals
        
        Args:
            video_path: Path to video file
            interval_seconds: Interval between frames in seconds
            
        Returns:
            List of (frame, timestamp) tuples
        """
        try:
            if not self.is_supported_format(video_path):
                logger.error(f"Unsupported video format: {video_path}")
                return []
            
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                logger.error(f"Could not open video: {video_path}")
                return []
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            if fps <= 0:
                logger.error("Invalid FPS in video")
                cap.release()
                return []
            
            frames = []
            frame_interval = int(fps * interval_seconds)
            
            logger.info(f"Extracting frames every {interval_seconds} seconds ({frame_interval} frames)")
            
            frame_number = 0
            while frame_number < total_frames:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                ret, frame = cap.read()
                
                if not ret:
                    break
                
                timestamp = frame_number / fps
                frames.append((frame.copy(), timestamp))
                
                frame_number += frame_interval
                
                # Progress logging
                if len(frames) % 50 == 0:
                    logger.info(f"Extracted {len(frames)} frames...")
            
            cap.release()
            logger.info(f"Successfully extracted {len(frames)} frames from video")
            return frames
            
        except Exception as e:
            logger.error(f"Error extracting frames: {str(e)}")
            return []
    
    def detect_scene_changes(self, video_path: str, threshold: float = 0.3) -> List[Tuple[np.ndarray, float]]:
        """
        Detect scene changes and extract key frames
        
        Args:
            video_path: Path to video file
            threshold: Threshold for scene change detection
            
        Returns:
            List of (frame, timestamp) tuples at scene changes
        """
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return []
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            scene_frames = []
            prev_frame = None
            frame_number = 0
            
            logger.info("Detecting scene changes...")
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Convert to grayscale for comparison
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # Check for scene change
                if prev_frame is not None:
                    # Calculate histogram difference
                    hist1 = cv2.calcHist([prev_frame], [0], None, [256], [0, 256])
                    hist2 = cv2.calcHist([gray], [0], None, [256], [0, 256])
                    
                    # Calculate correlation coefficient
                    correlation = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
                    
                    # Scene change detected if correlation is below threshold
                    if correlation < (1.0 - threshold):
                        timestamp = frame_number / fps
                        scene_frames.append((frame.copy(), timestamp))
                        logger.debug(f"Scene change detected at {timestamp:.2f}s (correlation: {correlation:.3f})")
                
                prev_frame = gray
                frame_number += 1
                
                # Progress logging
                if frame_number % 1000 == 0:
                    logger.debug(f"Processed {frame_number} frames...")
            
            cap.release()
            logger.info(f"Detected {len(scene_frames)} scene changes")
            return scene_frames
            
        except Exception as e:
            logger.error(f"Error detecting scene changes: {str(e)}")
            return []
    
    def extract_text_rich_frames(self, video_path: str, min_text_confidence: float = 0.5) -> List[Tuple[np.ndarray, float]]:
        """
        Extract frames that likely contain text (slides, captions, etc.)
        Uses simple edge detection as proxy for text content
        """
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return []
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            text_frames = []
            frame_number = 0
            
            logger.info("Extracting text-rich frames...")
            
            # Sample every 2 seconds initially
            sample_interval = int(fps * 2)
            
            while True:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Check if frame likely contains text
                text_score = self._assess_text_content(frame)
                
                if text_score >= min_text_confidence:
                    timestamp = frame_number / fps
                    text_frames.append((frame.copy(), timestamp))
                    logger.debug(f"Text-rich frame found at {timestamp:.2f}s (score: {text_score:.3f})")
                
                frame_number += sample_interval
            
            cap.release()
            logger.info(f"Found {len(text_frames)} text-rich frames")
            return text_frames
            
        except Exception as e:
            logger.error(f"Error extracting text-rich frames: {str(e)}")
            return []
    
    def _assess_text_content(self, frame: np.ndarray) -> float:
        """
        Assess likelihood that frame contains text content
        Simple heuristic based on edge density and contrast
        """
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Edge detection
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.count_nonzero(edges) / edges.size
            
            # Contrast analysis
            contrast = np.std(gray)
            
            # Simple scoring
            text_score = 0.0
            
            # Edge density (text has many edges)
            if edge_density > 0.02:
                text_score += 0.4
            elif edge_density > 0.01:
                text_score += 0.2
            
            # Contrast (text usually has good contrast)
            if contrast > 40:
                text_score += 0.3
            elif contrast > 20:
                text_score += 0.1
            
            # Histogram analysis (text often has bimodal distribution)
            hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
            hist = hist.flatten()
            
            # Look for peaks (black text on white background or vice versa)
            if hist[0] > frame.size * 0.1 or hist[255] > frame.size * 0.1:
                text_score += 0.3
            
            return min(text_score, 1.0)
            
        except:
            return 0.0
    
    def create_frame_montage(self, frames: List[Tuple[np.ndarray, float]], output_path: str, 
                           cols: int = 4, frame_width: int = 200) -> bool:
        """
        Create a montage image showing multiple frames
        Useful for debugging and visualization
        """
        try:
            if not frames:
                return False
            
            rows = (len(frames) + cols - 1) // cols
            frame_height = int(frame_width * frames[0][0].shape[0] / frames[0][0].shape[1])
            
            # Create montage image
            montage = np.zeros((rows * frame_height, cols * frame_width, 3), dtype=np.uint8)
            
            for i, (frame, timestamp) in enumerate(frames):
                row = i // cols
                col = i % cols
                
                # Resize frame
                resized = cv2.resize(frame, (frame_width, frame_height))
                
                # Add timestamp text
                cv2.putText(resized, f"{timestamp:.1f}s", (5, 20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
                # Place in montage
                y_start = row * frame_height
                y_end = y_start + frame_height
                x_start = col * frame_width
                x_end = x_start + frame_width
                
                montage[y_start:y_end, x_start:x_end] = resized
            
            # Save montage
            cv2.imwrite(output_path, montage)
            logger.info(f"Frame montage saved to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating frame montage: {str(e)}")
            return False
    
    def convert_to_supported_format(self, input_path: str, output_path: str = None) -> Optional[str]:
        """
        Convert video to supported format using ffmpeg
        """
        try:
            if self.is_supported_format(input_path):
                return input_path
            
            if output_path is None:
                base_name = os.path.splitext(os.path.basename(input_path))[0]
                output_path = os.path.join(self.temp_dir, f"{base_name}_converted.mp4")
            
            # Use ffmpeg to convert
            cmd = [
                'ffmpeg', '-i', input_path,
                '-c:v', 'libx264',
                '-crf', '23',
                '-c:a', 'aac',
                '-b:a', '128k',
                '-y',  # Overwrite output file
                output_path
            ]
            
            logger.info(f"Converting video format: {input_path} -> {output_path}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logger.info("Video conversion successful")
                return output_path
            else:
                logger.error(f"Video conversion failed: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error("Video conversion timed out")
            return None
        except Exception as e:
            logger.error(f"Error converting video: {str(e)}")
            return None
    
    def get_frame_at_timestamp(self, video_path: str, timestamp_seconds: float) -> Optional[np.ndarray]:
        """
        Get a specific frame at given timestamp
        """
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return None
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_number = int(timestamp_seconds * fps)
            
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = cap.read()
            
            cap.release()
            
            if ret:
                return frame
            return None
            
        except Exception as e:
            logger.error(f"Error getting frame at timestamp {timestamp_seconds}: {str(e)}")
            return None
